from flask import Flask, redirect, render_template, request, url_for

import helpers
from analyzer import Analyzer
import os
import sys
from termcolor import colored
from nltk.tokenize import TweetTokenizer

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():

    # validate screen_name
    screen_name = request.args.get("screen_name", "").lstrip("@")
    if not screen_name:
        return redirect(url_for("index"))

    # get screen_name's tweets
    tweets = helpers.get_user_timeline(screen_name, count=100)

    positive, negative, neutral = 0.0, 0.0, 100.0
    
    #########added part starts here
    
    tknzr = TweetTokenizer()
    
    temp_list = []
    for e in tweets:
        temp_list.append(e)
    
    # absolute paths to lists
    positives = os.path.join(sys.path[0], "positive-words.txt")
    negatives = os.path.join(sys.path[0], "negative-words.txt")

    # instantiate analyzer
    analyzer = Analyzer(positives, negatives)
    score = 0
    total_tweets = 0
    # analyze word
    for y in temp_list:
        y = tknzr.tokenize(y)
        for xy in y:
            ##include capital letters
            for i in range(ord('a'),ord('z')+1):
                if xy.startswith(chr(i)):
                    total_tweets+=1
                    score = analyzer.analyze(xy)
                    if score == 1:
                        positive+=1
                    elif score == -1:
                        negative+=1
                    else:
                        neutral+=1
                    
                    break
           
    ############################### added part ends here

    # generate chart
    chart = helpers.chart(positive, negative, neutral)

    # render results
    return render_template("search.html", chart=chart, screen_name=screen_name)
