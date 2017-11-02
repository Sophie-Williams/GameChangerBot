#!/usr/bin/python

from __future__ import absolute_import, print_function
from sqlalchemy.exc import ProgrammingError
from tweepy.streaming import StreamListener
from slacker import Slacker
from tweepy import OAuthHandler
from tweepy import Stream
from threading import Thread
from time import sleep
import dataset
import re
import praw
from config import definitions as define
from config import botconfig as cfg
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import OrderedDict


class StdOutListener(StreamListener):
    def on_status(self, status):
        if status.retweeted:
            return

        if status.user.screen_name == "EAMaddenMobile":
            slack_chan = "#maddengeneral"
        elif status.user.screen_name == "EAFIFAMOBILE":
            slack_chan = "#fifageneral"
        elif status.user.screen_name == "EASPORTSNBA":
            if tweet_is_relevant(status.text):
                slack_chan = "#nbageneral"
        else:
            slack_chan = "#easports-tweets"
            add_history = True

        t_buf = "*[New tweet from %s]*\n %s" % (status.user.screen_name, status.text)
        print(t_buf)

        post_slack(slack_chan, t_buf, add_history)

    def on_error(self, status_code):
        if status_code == 420:
            return False


def start_stream(t_id):
    listen = StdOutListener()
    auth = OAuthHandler(cfg.twitter_creds['consumer_key'], cfg.twitter_creds['consumer_secret'])
    auth.set_access_token(cfg.twitter_creds['access_token'], cfg.twitter_creds['access_token_secret'])

    try:
        stream = Stream(auth, listen)
        stream.filter(follow=[t_id])
    except Exception as e:
        print(e)


def tweet_is_relevant(t_content):
    tweet_text = re.sub("[^\w]", " ", t_content).split()

    if set(tweet_text) & set(define.nba_keywords):
        return True
    else:
        return False


def post_slack(slack_chan, slack_msg, add_history=False):

        obj = slack.chat.post_message(
            channel=slack_chan,
            text=slack_msg,
            as_user=True,
            link_names=True,
            attachments=[])

        o_ts = obj.__dict__['body']['ts']
        o_chan = obj.__dict__['body']['channel']

        if add_history:
            slack_history[o_ts] = o_chan

            if len(slack_history) > 200:
                while True:
                    trim_channel(slack_history.values()[0], slack_history.keys()[0])
                    del slack_history[slack_history.keys()[0]]
                    if len(slack_history) <= 200:
                        break


def trim_channel(slack_chan, slack_timestamp):
    slack.chat.delete(slack_chan, slack_timestamp, False)

if __name__ == '__main__':
    mm_id = "1691502835"
    nbalm_id = "46172768"
    fifa_id = "3009573404"
    slack_history = OrderedDict()

    try:
        token = cfg.slack_creds['api_token']
        slack = Slacker(token)
    except Exception as e:
        print(e)

    print("[Twitter] Starting Madden Twitter stream monitor ...")
    madden_tweet = Thread(target=start_stream, args = [mm_id])
    madden_tweet.start()

    print("[Twitter] Starting NBA Live Twitter stream monitor ...")
    nbalm_tweet = Thread(target=start_stream, args=[nbalm_id])
    nbalm_tweet.start()

    print("[Twitter] Starting FIFA Twitter stream monitor ...")
    fifa_tweet = Thread(target=start_stream, args=[fifa_id])
    fifa_tweet.start()

