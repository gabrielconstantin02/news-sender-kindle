# news-sender-kindle
# Send your RSS news to your Kindle

- Python script that will read a list of RSS news, package them as a MOBI/EPUB file, and then send it to your kindle via kindle mail address and Amazon's whispersync at the same time everyday.

## Features

1.  Fetch full articles from rss feeds instead of summaries
2.  Convert them into an EPUB/MOBI book
3.  Automatically send it to your kindle at the same time everyday
4.  Extremely easy to setup and use. Virtually everything is easily customisable by changing just a few environment variables. Some of the important ones are - <br>
    - Number of articles to fetch
    - Time range of posted articles (For instance: only fetching articles posted in last 24hrs)
    - Time at which to send the book to kindle

## Under the hood

This is a simple Python script that will download all your RSS news, package them as an EPUB first using `pandoc`, and then generate a Kindle file from that. This is a very roundabout way to do things, but it turned out to give the best results.

Then, it will sleep until specified time (adjustable) and do it all over again. The idea is to leave the script running in some server, and comfortably have your news delivered to your Kindle, at the same time, at your leisure, so you can get the news and go back to the more pressing matters of your daily life without feeling like you're compulsed to chase the cycle of Ad riddled news.

# Installation

### Docker CLI

If you want to use the provided docker image, just run:

```sh
docker run -d \
  --name news-sender-kindle \
  --restart unless-stopped \
   -e EMAIL_SMTP="smtp.gmail.com" \
   -e EMAIL_SMTP_PORT="465" \
   -e EMAIL_USER="USER" \
   -e EMAIL_PASSWORD="PWD" \
   -e EMAIL_FROM="USER" \
   -e KINDLE_EMAIL="KINDLE_USER" \
   -e UPDATE_PERIOD="24" \
   -e FETCH_PERIOD="24" \
   -e ITEM="30" \
   -e HOUR="2" \
   -e MINUTE="45" \
  ghcr.io/gabrielconstantin02/news-sender-kindle:latest
```

### Python

First, Change into the **cloned github repo**

### 1. Install docker

`sudo apt install docker`

### 2. Setting up docker permissions

    sudo usermod -aG docker $USER
    newgrp docker

### 3. Setting up environment file

    nano ./config/news2kindle.env

If you're using Gmail, you'd need to setup [Google App Password](https://support.google.com/accounts/answer/185833?hl=en) and use them for `username, password` fields in the file.<br>
If you're using other service providers, then their process would vary.<br>

    EMAIL_SMTP=smtp.gmail.com
    EMAIL_SMTP_PORT=465
    EMAIL_USER=username@gmail.com
    EMAIL_PASSWORD=password
    EMAIL_FROM=username@gmail.com
    KINDLE_EMAIL=username@kindle.com
    UPDATE_PERIOD=24
    FETCH_PERIOD=24
    ITEM=20
    HOUR=5
    MINUTES=0

`mv ./config/news2kindle.env` to where you store your environment variables.
For instance, I store mine at `/etc/environment.d/`

### 4. Setting up feed

    nano ./config/feeds.txt

The RSS feeds are listed in a file called `feeds.txt`, one per line. The modification date of `feeds.txt` will be the starting date from which news are downloaded.

### 5. Change into the **cloned github repo** and execute following docker commands:

    docker build -t news-sender-kindle .
    docker run --env-file </path/to/env/file/> news-sender-kindle

where the `.env` file contains all the environment variables defined in [news2kindle.py](src/news2kindle.py).

# Custom configurations

There are a couple custom change to the script as per your own liking. These would however require changes to the script.

It is advisable to use a text editor like vs-code. But for the purpose of this documentation the commands will be using `nano`.

### 1. Getting all posts posted within an X-hour period

        nano ./config/news2kindle.env

change `FETCH_PERIOD=24` to set up a time range.
<br>This will fetch all the posts from the rss feed posted within now and the last X-hours.

### 2. Setting a maximum number of posts to fetch

    nano ./config/news2kindle.env

change `ITEM=20` to set up a max-number of posts to fetch.

### 3. Changing the send period

    nano ./config/news2kindle.env

3.1. If you'd like to change the send time edit `HOUR=5` and `MINUTE=0` to your preferred time in 24hr format.

**Note: Remember to rebuild the docker again.**

# Contribution

You can contribute in many ways!

1. You can test the script in your own system and add steps.
2. You can report bugs and issues.
3. Better yet, you can **SOLVE** and document the bugs you come across.
4. You can help optimising the code.

# Acknowledgements

This script was originally developed by model-map to whom I am very thankful. Since he no longer has the repo, I published my version where I fixed his bug regarding epub files.

This author would like to thank anteprandium.

This script is based on code from
<br>
`https://github.com/anteprandium/news2kindle` and aims to solve some of the problems faced when using anteprandium's script:

1. The original script only downloaded summaries of provided rss feeds. This made the entire process redundant since to read an interesting article you'd need to redirect yourself to the host website in the end. The entire point of such a utility, in my opinion, is to provide a complete newspaper experience on your kindle.

2. Anteprandium writes in their bio that this script is meant for people with know-how. This author disagrees with such Gatekeeping, believing that everyone who owns a kindle should be able to enrich their reading experience regardless of their prior programming experience.
   <br>In that effort I have tried to write an exhaustive setup guide and have also addressed the MANY bugs and changes I had to make to get this project up and running.
   <br>However, the author acknowledges that setting it up for individuals with NO prior experience may take a bit of effort. One that will certainly pay off. Keep at it!

_Caveat_: If your MOBI file gets bigger than 25MB (easy if you have a lot of RSS sources), amazon will refuse to whispersync to your device. Can't do anything about it.
