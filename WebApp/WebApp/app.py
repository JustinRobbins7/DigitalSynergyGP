from flask import Flask, render_template, abort, redirect, request, flash
from jinja2 import TemplateNotFound
from WebApp.WebApp.forms import AddMenuItem, CreateAccount, FormLogin
from flask_sqlalchemy import SQLAlchemy
import pymysql

app = Flask(__name__)

# secret key to allow for CSRF forms
app.config['SECRET_KEY'] = 'any secret string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:DigitalSynergy@localhost/restaurant'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class users(db.Model):
    users_id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(40))
    accountbalance = db.Column(db.DECIMAL(10, 2))
    typeaccount = db.Column(db.Integer)


db.create_all()

if db.session.query(users).filter(users.username == 'admin').count() == 0:
    admin_user = users(username='admin', password='password', accountbalance=0.0, typeaccount=1)
    db.session.add(admin_user)
    db.session.commit()


# application will load html based on URL route given in the browser
@app.route('/', defaults={'page': 'home'}, methods=['GET', 'POST'])
@app.route('/<page>', methods=['GET', 'POST'])
def html_lookup(page):
    renderpage = page + '.html'
    print(page)
    # has to load page differently with forms, check for myaccount before the general render
    if page == 'myaccount':
        try:

            error = None

            form_menu = AddMenuItem()
            form_login = FormLogin()
            form_create = CreateAccount()

            if form_create.createaccount.data:
                form_create = CreateAccount(request.form)
                if form_create.validate_on_submit():
                    temp_username = form_create.createusername.data
                    temp_password = form_create.createpassword.data

                    if db.session.query(users).filter(users.username == temp_username).count() == 0:
                        temp_user = users(username=temp_username.lower(), password=temp_password, accountbalance=0.0,
                                          typeaccount=0)
                        db.session.add(temp_user)
                        db.session.commit()
                        return render_template('myaccount.html', formMenu=form_menu, formCreate=form_create,
                                               formLogin=form_login)
                    else:
                        error = 'Account Already Exists: Choose Another Username or Login'
                        return render_template('myaccount.html', formMenu=form_menu, formCreate=form_create,
                                               formLogin=form_login, createError=error)

            if form_login.loginsubmit.data:
                form_login = FormLogin(request.form)
                if form_login.validate_on_submit():
                    temp_username = form_login.loginusername.data
                    temp_password = form_login.loginpassword.data
                    if users.query.filter_by(username=temp_username, password=temp_password).count() != 0:
                        return render_template('myaccount.html', formMenu=form_menu, formCreate=form_create,
                                               formLogin=form_login)
                    else:
                        error = 'Account Does Not Exist: Create Account to Continue'
                        return render_template('myaccount.html', formMenu=form_menu, formCreate=form_create,
                                               formLogin=form_login, loginError=error)

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


# def delete_account():
    # delete from database
    # redirect to homepage

# runs application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
