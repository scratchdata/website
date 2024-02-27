from flask import Blueprint, render_template, send_from_directory, send_file
import os
import os.path
import markdown
import datetime
from typing import List, Tuple
import json
from gradient import generate_social_hero
from io import BytesIO

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
    hero: str
    color1: Tuple[int]
    color2: Tuple[int]
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
    rc.hero = _g("hero")

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


@blog_blueprint.get("/<post>/hero.png")
def blog_hero(post):
    post = get_post(post)

    gradients = [
        (0xD4145A, 0xFBB03B),
        (0x2E3192, 0x1BFFFF),
        (0x662D8C, 0xED1E79),
        (0x614385, 0x516395),
        (0x000000, 0x0f9b0f),
        (0x000000, 0xEB5757),
    ]

    def _rgb(color_int):
        # Extract the Red component
        red = (color_int >> 16) & 0xFF
        # Extract the Green component
        green = (color_int >> 8) & 0xFF
        # Extract the Blue component
        blue = color_int & 0xFF
    
        return red, green, blue

    n = hash(post.title) % len(gradients)
    gradient = gradients[n]

    c1 = _rgb(gradient[0])
    c2 = _rgb(gradient[1])

    img = generate_social_hero(c1,c2,post.title)
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@blog_blueprint.get("/<post>/<path:asset>")
def blog_post_asset(post, asset):
    dirname = f"blog/posts/{post}"
    return send_from_directory(dirname, asset)