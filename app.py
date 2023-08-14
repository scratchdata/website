from urllib.parse import urlparse
from flask import Flask, request, render_template, session, redirect, url_for, jsonify, send_from_directory
from jinja2.exceptions import TemplateNotFound
from blog import blog_blueprint
import functools
import random
import datetime
from pprint import pprint
# from jinja_components import JinjaComponents

app = Flask(__name__)
# app.jinja_env.add_extension(JinjaComponents)
# app.secret_key = "21f11080-57be-451e-b01d-04dbe02e2336"
app.register_blueprint(blog_blueprint)

# @app.before_request
# def redirect_root_to_www():
#     return redirect('https://www.journalize.io', 301)

#     u = urlparse(request.url)
#     if u.netloc in ('hotswap.app', 'usehotswap.com'):
#         www_url = request.url.replace(u.netloc, 'www.' + u.netloc, 1)
#         www_url = www_url.replace('http://', 'https://', 1)
#         return redirect(www_url, 301)


# # add the date util to jinja2
# @app.context_processor
# def inject_date():
#     return { 'date': datetime.date }


@app.get("/")
def index():
    # sources = get_sources()
    # random.shuffle(sources)
    return render_template("index.html")


# @app.get("/about")
# def about():
#     return render_template("about.html")


# @app.get("/contact")
# def contact():
#     return render_template("contact.html")


# @app.get("/migration_asset/<migration>/<path:asset>")
# def migration_asset(migration, asset):
#     dirname = f"local_modules/{migration}"
#     return send_from_directory(dirname, asset)


# @functools.lru_cache(maxsize=None)
# def get_sources():
#     sources = [
#         migrations.get_product_details(m) for m in migrations.get_migration_map()
#     ]
#     return sources


# @app.get("/migrations")
# def migrations_list():
#     return render_template("migrations.html", sources=get_sources())


# @app.get("/migrations/<source>")
# def migrations_source(source):
#     source_details = migrations.get_product_details(source)
#     destinations = [
#         migrations.get_product_details(m)
#         for m in migrations.get_migration_map().get(source)
#     ]

#     return render_template(
#         "migrations_source.html",
#         source=source_details,
#         destinations=destinations,
#     )


# @app.get("/migrations/<source>/<destination>")
# def migrations_source_destination(source, destination):
#     source = migrations.get_product_details(source)
#     dest = migrations.get_product_details(destination)

#     migration = migrations.get_migration_data(source, destination)    
#     migration['supported'] = migrations.is_supported(source, destination)

#     return render_template(
#         "migrations_source_destination.html",
#         source=source,
#         destination=dest,
#         migration=migration,
#     )


# @app.post("/migrations/<source>/<destination>/start")
# def migrations_start(source, destination):
#     hs_session = client.create_session(source, destination)
#     return render_template("components/widget.html", session_id=hs_session.session_id)


# @app.route("/migrations/<source>/<destination>/join_waitlist", methods=["POST"])
# def join_waitlist(source, destination):
#     email = request.form["email"]
#     tag_name = f'{source}_to_{destination}'
#     mailchimp.add_tag_to_email(email, tag_name)
#     return jsonify({"status": "success"})

# @app.route("/health")
# def health_check():
#     # https://tools.ietf.org/id/draft-inadarei-api-health-check-05.html#name-example-output
#     client.health()
#     return jsonify({"status": "pass"})


if __name__ == "__main__":
    app.run(debug=True, threaded=True)