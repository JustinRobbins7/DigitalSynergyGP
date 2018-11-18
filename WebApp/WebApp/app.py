from flask import Flask, render_template, abort, redirect, request
from jinja2 import TemplateNotFound
from WebApp.WebApp.forms import AddMenuItem, CreateAccount, FormLogin, UsernameReturnDelete, UsernameReturnAdmin, GiftCardAddition, AddBalance
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
import pymysql

app = Flask(__name__)

# secret key to allow for CSRF forms
app.config['SECRET_KEY'] = 'any secret string'
# configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:DigitalSynergy@localhost/restaurant'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# configuration to start the Flask-Login manager
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


# DB model for a user (admin or regular)
# type account will allow distinguishing between regular/admin user in the .hmtl to display different elements
class Users(UserMixin, db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(40))
    accountbalance = db.Column(db.DECIMAL(10, 2))
    typeaccount = db.Column(db.Integer)


# DB model for a giftcard
# giftcards will be added to a database, and normal users can add a balance to their account using
# these cards
class Giftcards(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    number = db.Column(db.String(15))
    balance = db.Column(db.DECIMAL(10, 2))


db.create_all()

# if there is no admin user in the database, this will create one. There should always be an admin account
if db.session.query(Users).filter(Users.username == 'admin').count() == 0:
    admin_user = Users(username='admin', password='password', accountbalance=0.0, typeaccount=1)
    db.session.add(admin_user)
    db.session.commit()


# what to do on logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect('home')


# what to do on create account
@app.route('/createaccount')
def createaccount_function():
    try:

        error = None

        # initialize forms needed
        form_create = CreateAccount()

        # if create button is pressed
        if form_create.createaccount.data:
            # pull form data into form_create
            form_create = CreateAccount(request.form)
            # if data is all valid
            if form_create.validate_on_submit():
                temp_username = form_create.createusername.data
                temp_password = form_create.createpassword.data

                # if user don't exist, create a temp user with all the data and add it to the users table in the DB,
                # and then redirect to the myaccount page
                if db.session.query(Users).filter(Users.username == temp_username).count() == 0:
                    temp_user = Users(username=temp_username.lower(), password=temp_password, accountbalance=0.0,
                                            typeaccount=0)
                    db.session.add(temp_user)
                    db.session.commit()
                    return redirect('myaccount')
                # if user already exists, prompt user to either change username or login
                else:
                    error = 'Account Already Exists: Choose Another Username or Login'
                    return render_template('createaccount.html', formCreate=form_create, createError=error)

        # what to return on no button press
        return render_template('createaccount.html', formCreate=form_create, loginError=error)

    except TemplateNotFound:
        abort(404)


# what to do on my account
@app.route('/myaccount')
def myaccount_function():
    try:

        # messages that are passed to the html
        error = None
        dmessagegood = None
        dmessagebad = None
        amessagegood = None
        amessagebad = None
        gcmessagegood = None
        gcmessagebad = None
        addmessagegood = None
        addmessagebad = None

        # initialized forms needed
        form_menu = AddMenuItem()
        form_login = FormLogin()
        form_create = CreateAccount()
        form_delete = UsernameReturnDelete()
        form_makeadmin = UsernameReturnAdmin()
        form_addgiftcard = GiftCardAddition()
        form_addbalance = AddBalance()

        # if login button is pressed ------------------------------------------------------------------------------
        if form_login.loginsubmit.data:
            # pull data from form
            form_login = FormLogin(request.form)
            # if all data is valid
            if form_login.validate_on_submit():
                temp_username = form_login.loginusername.data
                temp_password = form_login.loginpassword.data

                # if the username and password combo is in the DB, then login the user using Flask-Login and then
                # redirect to myaccount, which will now show a different page because user is logged in
                if Users.query.filter_by(username=temp_username, password=temp_password).count() != 0:
                    user = Users.query.filter_by(username=temp_username, password=temp_password).first()
                    login_user(user, remember=True)
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance)
                # if the combo doesn't exist in the DB, prompt user to create account if they don't have one
                else:
                    error = 'Username or Password Incorrect: Create Account if you Don\'t Have One'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           loginError=error)

        # logic for adding a menu item to the website -------------------------------------------------------------
        if form_menu.addsubmit.data:
            form_menu = AddMenuItem(request.form)
            if form_menu.validate_on_submit():
                print(form_menu.title.data)
                print(form_menu.description.data)
                print(form_menu.price.data)
                print(form_menu.choice.data)
                return redirect('myaccount')

        # logic for a user to add a balance to their account via a giftcard ---------------------------------------
        if form_addbalance.addBalanceButton.data:
            form_addbalance = AddBalance(request.form)
            if form_addbalance.validate_on_submit():
                temp_addnumber = form_addbalance.balanceNumber.data
                # if gc number is not in database
                if db.session.query(Giftcards).filter(Giftcards.number == temp_addnumber).count() == 0:
                    gcmessagebad = "Gift Card does not exist. Check the numbers and try again."
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           BalanceMessageB=gcmessagebad)
                # gc number is in database
                else:
                    gift_card = Giftcards.query.filter_by(number=temp_addnumber).first()
                    current_user.accountbalance += gift_card.balance
                    Giftcards.query.filter_by(number=temp_addnumber).delete()
                    db.session.commit()
                    gcmessagegood = 'Balance has been added to your account.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           BalanceMessageG=gcmessagegood)

        # logic for adding a giftcard to the database -------------------------------------------------------------
        if form_addgiftcard.addGiftCard.data:
            form_addgiftcard = GiftCardAddition(request.form)
            if form_addgiftcard.validate_on_submit():
                temp_gcnumber = form_addgiftcard.giftCardNumber.data
                temp_gcamount = form_addgiftcard.giftCardAmount.data
                if db.session.query(Giftcards).filter(Giftcards.number == temp_gcnumber).count() == 0:
                    temp_gc = Giftcards(number=temp_gcnumber, balance=temp_gcamount)
                    db.session.add(temp_gc)
                    db.session.commit()
                    gcmessagegood = 'Giftcard Has Been Added'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           AddMessageG=gcmessagegood)
                else:
                    gcmessagebad = 'Giftcard Has Already Been Added'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           AddMessageB=gcmessagebad)

        # logic for deleting a user from the website --------------------------------------------------------------
        if form_delete.returnButtonDelete.data:
            form_delete = UsernameReturnDelete(request.form)
            if form_delete.validate_on_submit():
                temp_user = form_delete.returnUsernameDelete.data
                if db.session.query(Users).filter(Users.username == temp_user).count() == 0:
                    dmessagebad = 'User Does Not Exists. Check Username and Enter Again'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           DeleteMessageB=dmessagebad)
                else:
                    Users.query.filter_by(username=temp_user).delete()
                    db.session.commit()
                    dmessagegood = 'User Has Been Deleted'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           DeleteMessageG=dmessagegood)

        # logic for making a user and admin -----------------------------------------------------------------------
        if form_makeadmin.returnButtonAdmin.data:
            form_makeadmin = UsernameReturnAdmin(request.form)
            if form_makeadmin.validate_on_submit():
                temp_user = form_makeadmin.returnUsernameAdmin.data
                if db.session.query(Users).filter(Users.username == temp_user).count() == 0:
                    amessagebad = 'User Does Not Exists. Check Username and Enter Again'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           AdminMessageB=amessagebad)
                else:
                    temp = Users.query.filter_by(username=temp_user).first()
                    temp.typeaccount = 1
                    db.session.commit()
                    amessagegood = 'Account Has Been Made an Admin'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           AdminMessageG=amessagegood)

        # on no special cases return myaccount page ---------------------------------------------------------------
        return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                               formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                               formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance)

    except TemplateNotFound:
        abort(404)


# application will load html based on URL route given in the browser
@app.route('/', defaults={'page': 'home'}, methods=['GET', 'POST'])
@app.route('/<page>', methods=['GET', 'POST'])
def html_lookup(page):
    renderpage = page + '.html'
    print(page)

    # call myaccount functionality from function
    if page == 'myaccount':
        print('hi')
        return myaccount_function()

    # call myaccount functionality from function
    if page == 'createaccount':
        print('hello')
        return createaccount_function()

    # render all other pages that don't require extra procession in the form of a function
    try:
        return render_template('{}'.format(renderpage))
    except TemplateNotFound:
        abort(404)


# handler for the Flask-Login package
@login_manager.user_loader
def login_handler(user_id):
    return Users.query.get(int(user_id))

# def delete_account():
    # delete from database
    # redirect to homepage


# runs application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
