

from flask import Flask, render_template, abort
from jinja2 import TemplateNotFound
app = Flask(__name__)


# application will load html based on URL route given in the browser
@app.route('/', defaults={'page': 'home.html'})
@app.route('/<page>')
def html_lookup(page):
    print(page)
    try:
        return render_template('{}'.format(page))
    except TemplateNotFound:
        abort(404)


# runs application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
