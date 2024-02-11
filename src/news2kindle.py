#!/usr/bin/env python
# encoding: utf-8

# idea and original code from from from https://gist.github.com/alexwlchan/01cec115a6f51d35ab26

# PYTHON boilerplate
from email.utils import COMMASPACE, formatdate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import morss
import sys
import pypandoc
import pytz
from tzlocal import get_localzone
import time
import logging
import threading
import subprocess
from datetime import datetime, timedelta
import os
import feedparser
from FeedparserThread import FeedparserThread

logging.basicConfig(level=logging.INFO)

EMAIL_SMTP = os.getenv("EMAIL_SMTP")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")
PANDOC = os.getenv("PANDOC_PATH", "/usr/bin/pandoc")
PERIOD = int(os.getenv("UPDATE_PERIOD", 24))  # hours between RSS pulls
FETCH_PERIOD=int(os.getenv("FETCH_PERIOD",24))
HOUR=int(os.getenv("HOUR",0))
MINUTE=int(os.getenv("MINUTES",0))

CONFIG_PATH = '/config'
FEED_FILE = os.path.join(CONFIG_PATH, 'feeds.txt')
COVER_FILE = os.path.join(CONFIG_PATH, 'cover.png')


feed_file = os.path.expanduser(FEED_FILE)

def load_feeds():
    """Return a list of the feeds for download.
        At the moment, it reads it from `feed_file`.
    """
    with open(feed_file, 'r') as f:
        return list(f)


def update_start(now):
    """
    Update the timestamp of the feed file. The time stamp is used
    as the starting point to download articles.
    """
    new_now = time.mktime(now.timetuple())
    with open(feed_file, 'a'):
        os.utime(feed_file, (new_now, new_now))


def get_start(fname):
    """
    Get the starting time to read posts since. This is currently saved as 
    the timestamp of the feeds file.
    """
    return pytz.utc.localize(datetime.fromtimestamp(os.path.getmtime(fname))) - timedelta(hours=FETCH_PERIOD)


def get_posts_list(feed_list, START):
    """
    Spawn a worker thread for each feed.
    """
    posts = []
    ths = []
    lock = threading.Lock()

    def append_posts(new_posts):
        lock.acquire()
        posts.extend(new_posts)
        lock.release()

    for link in feed_list:
        url = str(link)
        options = morss.Options(format='rss')
        url, rss = morss.FeedFetch(url, options)
        rss = morss.FeedGather(rss, url, options)
        output = morss.FeedFormat(rss, options, 'unicode')
        feed = feedparser.parse(output)
        th = FeedparserThread(feed, START, append_posts)
        ths.append(th)
        th.start()

    for th in ths:
        th.join()

    # When all is said and done,
    return posts


def nicedate(dt):
    return dt.strftime('%d %B %Y').strip('0')


def nicehour(dt):
    return dt.strftime('%I:%M&thinsp;%p').strip('0').lower()


def nicepost(post):
    thispost = post._asdict()
    thispost['nicedate'] = nicedate(thispost['time'])
    thispost['nicetime'] = nicehour(thispost['time'])
    return thispost


# <link rel="stylesheet" type="text/css" href="style.css">
html_head = u"""<html>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width" />
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta name="apple-mobile-web-app-capable" content="yes" />
<style>
</style>
<title>THE DAILY NEWS</title>
</head>
<body>

"""

html_tail = u"""
</body>
</html>
"""

html_perpost = u"""
    <article>
        <h1><a href="{link}">{title}</a></h1>
        <p><small>By {author} for <i>{blog}</i>, on {nicedate} at {nicetime}.</small></p>
         {body}
    </article>
"""


def send_mail(send_from, send_to, subject, text, files):
    # assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text, 'text', 'utf-8'))

    for f in files or []:
        with open(f, "rb") as fil:
            # print("Original message:")
            # print(fil.read())
            msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition=f'attachment; filename="{os.path.basename(f)}"',
                Name=os.path.basename(f)
            ))
    # print("Message before sending: ")
    # print(msg.as_string())
    smtp = smtplib.SMTP_SSL(EMAIL_SMTP, EMAIL_SMTP_PORT)
    smtp.login(EMAIL_USER, EMAIL_PASSWD)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


# def send_ebook(url, filename, email, send_to, subject):
#     epubfile = BytesIO()
#     print(url)
#     try:
#         with urlopen(url, timeout=10) as connection:
#             epubfile.write(connection.read())
#     except urllib.error.HTTPError as e:
#         print(e.read().decode())
#     from_email = "joe@compellingsciencefiction.com"
#     to_email = send_to
#     msg = MIMEMultipart()
#     msg['From'] = send_from
#     msg['To'] = COMMASPACE.join(send_to)
#     msg['Date'] = formatdate(localtime=True)
#     msg['Subject'] = subject
#
#     # Set message body
#     body = MIMEText("This is your daily news.\n\n--\n\n", "plain")
#     msg.attach(body)
#
#     epubfile.seek(0)
#     part = MIMEApplication(epubfile.read())
#     part.add_header("Content-Disposition",
#                     "attachment",
#                     filename=filename)
#     msg.attach(part)
#
#     # Convert message to string and send
#     ses_client = boto3.client("ses", region_name="us-west-2")
#     response = ses_client.send_raw_email(
#         Source=from_email,
#         Destinations=[to_email],
#         RawMessage={"Data": msg.as_string()}
#     )
#     print(response)

def convert_to_mobi(input_file, output_file):
    cmd = ['ebook-convert', input_file, output_file]
    process = subprocess.Popen(cmd)
    process.wait()


def do_one_round():
    # get all posts from starting point to now
    now = pytz.utc.localize(datetime.now())
    #midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = get_start(feed_file)

    logging.info(f"Collecting posts since {start}")

    posts = get_posts_list(load_feeds(), start)
    posts.sort()

    logging.info(f"Downloaded {len(posts)} posts")

    if posts:
        logging.info("Compiling newspaper")

        result = html_head + \
            u"\n".join([html_perpost.format(**nicepost(post))
                        for post in posts]) + html_tail

        logging.info("Creating epub")
        today_date = datetime.today().date()
        epubFile = str(today_date)+'.epub'
        mobiFile = str(today_date)+'.mobi'
        os.environ['PYPANDOC_PANDOC'] = PANDOC
        # print("Body:")
        # print(result)
        pypandoc.convert_text(result,
                              to='epub3',
                              format="html",
                              outputfile=epubFile,
                              extra_args=["--standalone",
                                          f"--epub-cover-image={COVER_FILE}",
                                          ])
        convert_to_mobi(epubFile, mobiFile)
        epubFile_2 = str(today_date)+'_converted.epub'
        convert_to_mobi(mobiFile, epubFile_2)

        logging.info("Sending to kindle email")
        send_mail(send_from=EMAIL_FROM,
                  send_to=[KINDLE_EMAIL],
                  subject="Daily news - "+str(today_date),
                  text="This is your daily news.\n\n--\n\n",
                  files=[epubFile_2])
        logging.info("Cleaning up...")
        os.remove(epubFile)
        os.remove(mobiFile)

    logging.info("Finished.")
    update_start(now)

def get_next_x_am():
    tz = get_localzone()
    timezone=pytz.timezone(tz.key)
    now = datetime.now(tz=timezone)
    next_x_am = now.replace(hour=HOUR, minute=MINUTE, second=0, microsecond=0)
    if now >= next_x_am:
        next_x_am += timedelta(days=1)
    return (next_x_am - now).total_seconds()

if __name__ == '__main__':
    while True:
        do_one_round()
        seconds = get_next_x_am()
        # seconds = PERIOD*3600
        time.sleep(seconds)
