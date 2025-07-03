import threading
import time
import datetime
import requests
from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "I'm alive!"


