from urllib.parse import urlparse
from flask import (
    Flask,
    request,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    send_from_directory,
)
from jinja2.exceptions import TemplateNotFound
from blog import blog_blueprint
import functools
import random
import datetime
from pprint import pprint
import requests
import os
import logging
import sys
import stripe

stripe.api_key = os.environ.get("STRIPE_API_KEY")

app = Flask(__name__)
app.register_blueprint(blog_blueprint)


@app.get("/payment/<stripe_customer_id>")
def stripe_payment(stripe_customer_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="setup",
        customer=stripe_customer_id,
        success_url="https://www.scratchdb.com",
        cancel_url="https://www.scratchdb.com"
    )

    return redirect(session.url)


@app.get("/")
def index():
    return render_template("index.html")

@app.get("/docs")
def docs():
    return render_template("docs.html")

@app.get("/customers")
def customers():
    return render_template("customers.html")

@app.get("/demo")
def demo():
    return render_template("demo.html")

@app.post("/signup")
def signup():
    email = request.form.get("email", "")
    payload = {"email": email}
    requests.post(
        "https://api.scratchdb.com/data?table=email_signup",
        headers={"X-API-KEY": os.environ.get("SCRATCHDB_API_KEY")},
        json=payload,
    )

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
