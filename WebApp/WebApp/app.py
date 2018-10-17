# from flask import Flask
# import flask
#
# app = Flask(__name__)
#
#
# @app.route('/')
# def index():
#     return flask.render_template("index.html")
#
#
# @app.route('/about.html/')
# def about():
#     return flask.render_template("about.html")
#
#
# @app.route('/gallery.html/')
# def gallery():
#     return flask.render_template("gallery.html")
#
#
# @app.route('/menu.html/')
# def menu():
#     return flask.render_template("menu.html")
#
#
# @app.route('/myaccount.html/')
# def myaccount():
#     return flask.render_template("myaccount.html")

from flask import Flask, render_template, abort
from jinja2 import TemplateNotFound
app = Flask(__name__)


@app.route('/', defaults={'page': 'home.html'})
@app.route('/<page>')
def html_lookup(page):
    print(page)
    try:
        return render_template('{}'.format(page))
    except TemplateNotFound:
        abort(404)


if __name__ == '__main__':
    app.run()
