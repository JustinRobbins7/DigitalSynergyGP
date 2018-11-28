from flask import Flask, render_template, abort, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import TemplateNotFound
from WebApp.WebApp.forms import AddMenuItem, CreateAccount, FormLogin, UsernameReturnDelete, UsernameReturnAdmin, \
                                GiftCardAddition, AddBalance, RemoveMenuItem, AddImage, RemoveImage, StatusChange
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_uploads import UploadSet, IMAGES, configure_uploads
import pymysql
import os

app = Flask(__name__)

app.config['UPLOADED_IMAGES_DEST'] = 'static/uploads/'

# Configuration for WebApp ----------------------------------------------------------------------------------------

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

# configuration for file uploads
imagesList = UploadSet('images', IMAGES)
configure_uploads(app, imagesList)


# Models for Database ---------------------------------------------------------------------------------------------

# DB model for a user (admin or regular)
# type account will allow distinguishing between regular/admin user in the .hmtl to display different elements
class Users(UserMixin, db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(128))
    accountbalance = db.Column(db.DECIMAL(10, 2))
    # type account will be 0 for regular users and 1 for admin users
    typeaccount = db.Column(db.Integer)


# DB model for a giftcard
# giftcards will be added to a database, and normal users can add a balance to their account using
# these cards
class Giftcards(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    number = db.Column(db.String(15))
    balance = db.Column(db.DECIMAL(10, 2))


# DB model for the items on the menu
# menu items will be added or removed from an admin account and displayed on the menu.html page
class MenuItems(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    itemtitle = db.Column(db.String(40))
    itemdescription = db.Column(db.String(250))
    itemprice = db.Column(db.DECIMAL(10, 2))
    itemtype = db.Column(db.String(10))


# DB model for images being added by an admin
# to be displayed on the gallery webpage of the website
class GalleryImages(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    imagefilename = db.Column(db.String(100))
    imageurl = db.Column(db.String(200))
    imagelocation = db.Column(db.String(10))


# DB model for orders that have been placed by users
# Will be displayed for admins to view
class OrderInformation(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    # username of user that have created the order
    orderauthor = db.Column(db.String(25))
    # items that are within the order
    orderinfo = db.Column(db.String(500))
    # restrictions that are given from the users allergy/diet restrictions
    orderrestrictions = db.Column(db.String(200))
    # 1 = created, 2 = started, 3 = completed, 4 = ready for pickup, 5 = picked up (remove from DB)
    orderstatus = db.Column(db.Integer)


# creates all the models within the database
db.create_all()

# if there is no admin user in the database, this will create one. There should always be an admin account
if db.session.query(Users).filter(Users.username == 'admin').count() == 0:
    # hashes admin password
    tempPassword = generate_password_hash('password')
    admin_user = Users(username='admin', password=tempPassword, accountbalance=0.0, typeaccount=1)
    db.session.add(admin_user)
    db.session.commit()


# Routes for WebApp -----------------------------------------------------------------------------------------------

# what to do on logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect('home')


# shopping cart variable to hold users cart information
shoppingcart = []
cartprice = 0


# app route for when a menu item gets added to the cart
@app.route('/add/<code>')
def add(code):
    flash(code + ' has been added to your cart.')
    addeditem = MenuItems.query.filter_by(itemtitle=code).first()
    shoppingcart.append(addeditem)
    global cartprice
    cartprice += addeditem.itemprice
    return redirect('menu')


@app.route('/placeorder')
def place_order():

    global shoppingcart
    global cartprice

    temporder = ''
    tempprice = cartprice

    for x in shoppingcart:
        if temporder == '':
            temporder += x.itemtitle
        else:
            temporder += ', ' + x.itemtitle

    print(tempprice)

    orderinfo = OrderInformation(orderauthor=current_user.username, orderinfo=temporder, orderstatus=1)
    db.session.add(orderinfo)
    current_user.accountbalance -= tempprice
    db.session.commit()

    shoppingcart = []
    cartprice = 0

    return redirect('myaccount')


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
                #hashes password when sending to db
                temp_password = generate_password_hash(form_create.createpassword.data)

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


# what to do on menu
# used to pass a list of all menu items from the database to the html to allow for a loop
# to place all the items
@app.route('/menu')
def menu_function():
    # command to retrieve all menu item entries from database
    test = db.engine.execute('SELECT * FROM restaurant.menu_items')
    menuitemlist = test.fetchall()
    return render_template('menu.html', MenuItemList=menuitemlist)


# what to do on gallery
# used to pass a list of all the images and their locations from the database to the html
# to allow for a loop and to place the images in their correct location
@app.route('/gallery')
def gallery_function():
    # command to retrieve all gallery images from database
    testimages = db.engine.execute('SELECT * FROM restaurant.gallery_images')
    testimageslist = testimages.fetchall()
    print(testimageslist)
    return render_template('gallery.html', ImagesItemList=testimageslist)


# what to do on my account
@app.route('/myaccount')
def myaccount_function():
    try:

        pullorders = db.engine.execute('SELECT * FROM restaurant.order_information')
        orderlist = pullorders.fetchall()

        # messages that are passed to the html (not needed here, for my reference)
        error = None
        dmessagegood = None
        dmessagebad = None
        amessagegood = None
        amessagebad = None
        gcmessagegood = None
        gcmessagebad = None
        addmessagegood = None
        addmessagebad = None
        menumessagegood = None
        menumessagebad = None
        rimessagegood = None
        rimessagebad = None
        aimessagegood = None
        aimessagebad = None
        rimgmessagegood = None
        rimgmessagebad = None
        scmessagebad = None

        # initialized forms needed
        form_menu = AddMenuItem()
        form_login = FormLogin()
        form_create = CreateAccount()
        form_delete = UsernameReturnDelete()
        form_makeadmin = UsernameReturnAdmin()
        form_addgiftcard = GiftCardAddition()
        form_addbalance = AddBalance()
        form_removeitem = RemoveMenuItem()
        form_addimage = AddImage()
        form_removeimage = RemoveImage()
        form_statuschange = StatusChange()

        # if login button is pressed ------------------------------------------------------------------------------
        if form_login.loginsubmit.data:
            # pull data from form
            form_login = FormLogin(request.form)
            # if all data is valid
            if form_login.validate_on_submit():
                temp_username = form_login.loginusername.data
                temp_password = form_login.loginpassword.data

                if Users.query.filter_by(username=temp_username).count() != 0:
                    tempuser = Users.query.filter_by(username=temp_username).first()
                    # checks password hash
                    tempbool = check_password_hash(tempuser.password, temp_password)

                # if the username and password combo is in the DB, then login the user using Flask-Login and then
                # redirect to myaccount, which will now show a different page because user is logged in
                if Users.query.filter_by(username=temp_username).count() != 0 and tempbool:
                    user = Users.query.filter_by(username=temp_username).first()
                    login_user(user, remember=True)
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, OrderList=orderlist,
                                           formStatus=form_statuschange, CartList=shoppingcart, CartPrice=cartprice)
                # if the combo doesn't exist in the DB, prompt user to create account if they don't have one
                else:
                    error = 'Username or Password Incorrect: Create Account if you Don\'t Have One'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, loginError=error, OrderList=orderlist,
                                           formStatus=form_statuschange, CartList=shoppingcart, CartPrice=cartprice)

        # logic for adding a menu item to the website -------------------------------------------------------------
        if form_menu.addsubmit.data:
            form_menu = AddMenuItem(request.form)
            if form_menu.validate_on_submit():
                temp_title = form_menu.title.data
                temp_description = form_menu.description.data
                temp_price = form_menu.price.data
                temp_itemtype = form_menu.choice.data
                # if an item with that title does not exist add it to the database
                if db.session.query(MenuItems).filter(MenuItems.itemtitle == temp_title).count() == 0:
                    temp_item = MenuItems(itemtitle=temp_title, itemdescription=temp_description, itemprice=temp_price,
                                          itemtype=temp_itemtype)
                    db.session.add(temp_item)
                    db.session.commit()
                    menumessagegood = 'Item has been added to the menu.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, MenuMessageG=menumessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                # if an item with that title already exists don't add it
                else:
                    menumessagebad = 'Item already exists in the menu. Check name and try again.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, MenuMessageB=menumessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # logic for changing the status of an order ---------------------------------------------------------------
        if form_statuschange.statusButton.data:
            form_statuschange = StatusChange(request.form)
            if form_statuschange.validate_on_submit():
                temp_ordernum = form_statuschange.orderNumber.data
                temp_newstatus = form_statuschange.orderStatus.data
                # if an order with that number doesn't exist throw error
                if db.session.query(OrderInformation).filter(OrderInformation.id == temp_ordernum).count() == 0:
                    scmessagebad = 'Order Doesn\'t Exist, Check Order Number Again'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, MenuMessageG=menumessagegood,
                                           OrderList=orderlist, StatusMessage=scmessagebad,
                                           formStatus=form_statuschange, CartList=shoppingcart, CartPrice=cartprice)
                # order does exist, change status
                else:
                    if temp_newstatus != '4':
                        temp_order = OrderInformation.query.filter_by(id=temp_ordernum).first()
                        temp_order.orderstatus = temp_newstatus
                        db.session.commit()
                    else:
                        OrderInformation.query.filter_by(id=temp_ordernum).delete()
                        db.session.commit()
                    return redirect('myaccount')

        # logic for removing a menu item from the website ---------------------------------------------------------
        if form_removeitem.removeItemButton.data:
            form_removeitem = RemoveMenuItem(request.form)
            if form_removeitem.validate_on_submit():
                temp_itemremove = form_removeitem.removeItemTitle.data
                # if item is not in database throw error message
                if db.session.query(MenuItems).filter(MenuItems.itemtitle == temp_itemremove).count() == 0:
                    rimessagebad = 'Item is not on the menu. Check title and try again.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, RemoveMessageB=rimessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                # item with the remove title is in the database for menu items
                else:
                    MenuItems.query.filter_by(itemtitle=temp_itemremove).delete()
                    db.session.commit()
                    rimessagegood = 'Item has been removed from the menu.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, RemoveMessageG=rimessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

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
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, BalanceMessageB=gcmessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
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
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, BalanceMessageG=gcmessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # logic for adding a giftcard to the database -------------------------------------------------------------
        if form_addgiftcard.addGiftCard.data:
            form_addgiftcard = GiftCardAddition(request.form)
            if form_addgiftcard.validate_on_submit():
                temp_gcnumber = form_addgiftcard.giftCardNumber.data
                temp_gcamount = form_addgiftcard.giftCardAmount.data
                # the gift card number doesn't already exist within the database
                if db.session.query(Giftcards).filter(Giftcards.number == temp_gcnumber).count() == 0:
                    temp_gc = Giftcards(number=temp_gcnumber, balance=temp_gcamount)
                    db.session.add(temp_gc)
                    db.session.commit()
                    gcmessagegood = 'Giftcard Has Been Added'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, AddMessageG=gcmessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                # the gift card number already exists in the database
                else:
                    gcmessagebad = 'Giftcard Has Already Been Added'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, AddMessageB=gcmessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # logic for deleting a user from the website --------------------------------------------------------------
        if form_delete.returnButtonDelete.data:
            form_delete = UsernameReturnDelete(request.form)
            if form_delete.validate_on_submit():
                temp_user = form_delete.returnUsernameDelete.data
                # user that is trying to be deleted doesn't exist
                if db.session.query(Users).filter(Users.username == temp_user).count() == 0:
                    dmessagebad = 'User Does Not Exists. Check Username and Enter Again'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, DeleteMessageB=dmessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                # delete account with the username that was given
                else:
                    Users.query.filter_by(username=temp_user).delete()
                    db.session.commit()
                    dmessagegood = 'User Has Been Deleted'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, DeleteMessageG=dmessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # logic for uploading a file for the gallery --------------------------------------------------------------
        if form_addimage.galleryButton.data:
            form_addimage = AddImage()
            if form_addimage.validate_on_submit():
                temp_filename = imagesList.save(request.files['galleryImage'])
                temp_url = imagesList.url(temp_filename)
                temp_imagelocation = form_addimage.galleryLocation.data
                # image does not already exists within database
                if db.session.query(GalleryImages).filter(GalleryImages.imagefilename == temp_filename).count() == 0:
                    aimessagegood = 'Image Has Been Added'
                    temp_galleryimages = GalleryImages(imagefilename=temp_filename, imageurl=temp_url,
                                                       imagelocation=temp_imagelocation)
                    db.session.add(temp_galleryimages)
                    db.session.commit()
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, ImageMessageG=aimessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                # image already exists within the database
                else:
                    aimessagebad = 'Image Already Exists. Check File and Try Again.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, ImageMessageB=aimessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # logic for removing a file for the gallery ---------------------------------------------------------------
        if form_removeimage.removeImageButton.data:
            form_removeimage = RemoveImage(request.form)
            if form_removeimage.validate_on_submit():
                temp_removeimage = form_removeimage.imageName.data
                # if image with name passed does not exist within the database
                if db.session.query(GalleryImages).filter(GalleryImages.imagefilename == temp_removeimage).count() == 0:
                    rimgmessagebad = 'Image Does Not Exist. Check Name and Try Again.'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, RImageMessageB=rimgmessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                else:
                    GalleryImages.query.filter_by(imagefilename=temp_removeimage).delete()
                    db.session.commit()
                    removepath = imagesList.path(temp_removeimage)
                    os.remove(removepath)
                    rimgmessagegood = 'Image Successfully Deleted'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, RImageMessageG=rimgmessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # logic for making a user and admin -----------------------------------------------------------------------
        if form_makeadmin.returnButtonAdmin.data:
            form_makeadmin = UsernameReturnAdmin(request.form)
            if form_makeadmin.validate_on_submit():
                temp_user = form_makeadmin.returnUsernameAdmin.data
                # user that is trying to become an admin does not exist in the database
                if db.session.query(Users).filter(Users.username == temp_user).count() == 0:
                    amessagebad = 'User Does Not Exists. Check Username and Enter Again'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, AdminMessageB=amessagebad,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)
                # make the user an admin based on the username given
                else:
                    temp = Users.query.filter_by(username=temp_user).first()
                    temp.typeaccount = 1
                    db.session.commit()
                    amessagegood = 'Account Has Been Made an Admin'
                    return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                                           formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                                           formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                                           formRemoveItem=form_removeitem, formAddImage=form_addimage,
                                           formRemoveImage=form_removeimage, AdminMessageG=amessagegood,
                                           OrderList=orderlist, formStatus=form_statuschange, CartList=shoppingcart,
                                           CartPrice=cartprice)

        # on no special cases return myaccount page ---------------------------------------------------------------
        return render_template('myaccount.html', formMenu=form_menu, formLogin=form_login,
                               formCreate=form_create, formDelete=form_delete, formAdmin=form_makeadmin,
                               formAddGiftcard=form_addgiftcard, formAddBalance=form_addbalance,
                               formRemoveItem=form_removeitem, formAddImage=form_addimage,
                               formRemoveImage=form_removeimage, OrderList=orderlist, formStatus=form_statuschange,
                               CartList=shoppingcart, CartPrice=cartprice)

    except TemplateNotFound:
        abort(404)


# application will load html based on URL route given in the browser
@app.route('/', defaults={'page': 'home'}, methods=['GET', 'POST'])
@app.route('/<page>', methods=['GET', 'POST'])
def html_lookup(page):
    renderpage = page + '.html'

    # call myaccount functionality from function
    if page == 'myaccount':
        return myaccount_function()

    # call myaccount functionality from function
    if page == 'createaccount':
        return createaccount_function()

    # call menu functionality from function
    if page == 'menu':
        return menu_function()

    # render all other pages that don't require extra procession in the form of a function
    try:
        return render_template('{}'.format(renderpage))
    except TemplateNotFound:
        abort(404)


# handler for the Flask-Login package
@login_manager.user_loader
def login_handler(user_id):
    return Users.query.get(int(user_id))


# runs application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
