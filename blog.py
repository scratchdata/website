from flask import Blueprint, render_template, send_from_directory
import os
import os.path
import markdown
import datetime
from typing import List
import json

blog_blueprint = Blueprint(
    "blog_blueprint", __name__, template_folder="templates", url_prefix="/blog"
)


POSTS_DIR = "blog/posts/"


class Post(object):
    date: datetime.date
    publishdate: datetime.date
    title: str
    html: str
    markdown: str
    summary: str
    slug: str
    tags: List[str]
    md_object: markdown.Markdown


def post_exists(post):
    return os.path.exists(f"{POSTS_DIR}/{post}/index.md")


def get_post(post):
    contents = open(f"{POSTS_DIR}/{post}/index.md", "r").read()

    # https://python-markdown.github.io/extensions/
    # https://facelessuser.github.io/pymdown-extensions/
    # md = markdown.Markdown(extensions=["meta", "tables", "pymdownx.magiclink", "pymdownx.highlight"])

    md = markdown.Markdown(extensions=["meta", "tables", "pymdownx.magiclink", "pymdownx.highlight", "pymdownx.superfences"],extension_configs={'pymdownx.highlight': {
			'noclasses': True,
			'use_pygments': False,
			# 'pygments_style': 'material'
		}})

    def _g(k):
        if k in md.Meta and len(md.Meta[k]) > 0:
            return md.Meta[k][0]

        return ""

    rc = Post()

    rc.markdown = contents
    rc.md_object = md
    rc.html = md.convert(contents)
    rc.date = _g("date")
    rc.publishdate = _g("publishdate")
    rc.title = _g("title")
    rc.summary = _g("summary")
    rc.slug = post
    rc.tags = json.loads(_g("tags"))

    return rc


@blog_blueprint.get("/")
def blog():
    posts = os.listdir(POSTS_DIR)
    post_details = []
    for p in posts:
        if post_exists(p):
            post = get_post(p)
            post_details.append(post)

    post_details.sort(key=lambda p: p.publishdate, reverse=True)

    print(post_details[0].tags)

    return render_template("blog.html", posts=post_details)


@blog_blueprint.get("/<post>/")
def blog_post(post):
    md = markdown.Markdown(extensions=["meta", "tables", "pymdownx.magiclink", "pymdownx.highlight", "pymdownx.superfences"],extension_configs={'pymdownx.highlight': {
			'noclasses': True,
			'use_pygments': False,
			# 'pygments_style': 'material'
		}})
    if not post_exists(post):
        return "", 404

    full_post = get_post(post)

    return render_template("blog_post.html", post=full_post)


@blog_blueprint.get("/<post>/<path:asset>")
def blog_post_asset(post, asset):
    dirname = f"blog/posts/{post}"
    return send_from_directory(dirname, asset)