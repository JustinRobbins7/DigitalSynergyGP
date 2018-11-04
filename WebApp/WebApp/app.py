

from flask import Flask, render_template, abort
from jinja2 import TemplateNotFound
from WebApp.WebApp.forms import LoginForm, AddMenuItem, CreateAccount
app = Flask(__name__)

# secret key to allow for CSRF forms
app.config['SECRET_KEY'] = 'any secret string'


# application will load html based on URL route given in the browser
@app.route('/', defaults={'page': 'home'})
@app.route('/<page>')
def html_lookup(page):
    renderpage = page + '.html'
    print(page)
    # has to load page differently with forms, check for myaccount before the general render
    if page == 'myaccount':
        try:
            form_login = LoginForm()
            form_menu = AddMenuItem()
            form_create = CreateAccount()
            return render_template('myaccount.html', formLogin=form_login, formMenu=form_menu, formCreate=form_create)
        except TemplateNotFound:
            abort(404)
    else:
        try:
            return render_template('{}'.format(renderpage))
        except TemplateNotFound:
            abort(404)


# runs application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
