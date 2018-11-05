

from flask import Flask, render_template, abort, redirect, request
from jinja2 import TemplateNotFound
from WebApp.WebApp.forms import AddMenuItem, CreateAccount, FormLogin
app = Flask(__name__)

# secret key to allow for CSRF forms
app.config['SECRET_KEY'] = 'any secret string'


# application will load html based on URL route given in the browser
@app.route('/', defaults={'page': 'home'}, methods=['GET', 'POST'])
@app.route('/<page>', methods=['GET', 'POST'])
def html_lookup(page):
    renderpage = page + '.html'
    print(page)
    # has to load page differently with forms, check for myaccount before the general render
    if page == 'myaccount':
        try:

            form_menu = AddMenuItem()
            form_login = FormLogin()
            form_create = CreateAccount()

            if form_create.createaccount.data:
                form_create = CreateAccount(request.form)
                if form_create.validate_on_submit():
                    print(form_create.createusername.data)
                    print(form_create.createpassword.data)
                    print(form_create.createpasswordverify.data)
                    return redirect('myaccount')

            if form_login.loginsubmit.data:
                form_login = FormLogin(request.form)
                if form_login.validate_on_submit():
                    print(form_login.loginusername.data)
                    print(form_login.loginpassword.data)
                    return redirect('myaccount')

            if form_menu.addsubmit.data:
                form_menu = AddMenuItem(request.form)
                if form_menu.validate_on_submit():
                    print(form_menu.title.data)
                    print(form_menu.description.data)
                    print(form_menu.price.data)
                    print(form_menu.choice.data)
                    return redirect('myaccount')

            return render_template('myaccount.html', formMenu=form_menu, formCreate=form_create, formLogin=form_login)

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
