from urllib.parse import urlparse
from flask import Flask, request, render_template, session, redirect, url_for, jsonify, send_from_directory
from jinja2.exceptions import TemplateNotFound
from blog import blog_blueprint
import functools
import random
import datetime
from pprint import pprint
import requests
import os

app = Flask(__name__)
app.register_blueprint(blog_blueprint)


@app.get("/")
def index():
    return render_template("index.html")

@app.post("/signup")
def signup():
    email = request.form.get('email', '')
    payload = {'email': email}
    requests.post(
        'https://demo.scratchdb.com/data?table=email_signup', 
        headers={'X-API-KEY': os.environ.get('SCRATCHDB_API_KEY')}, 
        json=payload)

    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True, threaded=True)