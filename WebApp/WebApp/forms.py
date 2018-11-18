from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, DecimalField, SelectField, validators

# choices for drop down menu on the add menu item form
menu_choices = [('appetizer', 'Appetizer'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('dessert', 'Dessert'), ('beverage', 'Beverage')]
# choices for dollar amounts of gift cards being added by admins
gc_choices = [('5', 5), ('10', 10), ('15', 15), ('25', 25), ('50', 50), ('100', 100)]
# choices for where to put the image on the gallery page
gallery_choices = [('appetizer', 'Appetizer'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('dessert', 'Dessert'), ('beverage', 'Beverage')]


# form for creating account
class CreateAccount(FlaskForm):
    createusername = StringField('Please Enter a Username', [validators.DataRequired()])
    createpassword = PasswordField('Please Enter a Password', [validators.DataRequired()])
    # validate for same password as above
    createpasswordverify = PasswordField('Please Re-Enter Your Password', [validators.DataRequired(), validators.equal_to('createpassword', message='Passwords Must Match')])
    createaccount = SubmitField('Create Account')


# form for logging into the system
class FormLogin(FlaskForm):
    loginusername = StringField('Username', [validators.DataRequired()])
    loginpassword = PasswordField('Password', [validators.DataRequired()])
    loginsubmit = SubmitField('Sign In')


# form for adding a menu item
class AddMenuItem(FlaskForm):
    title = StringField('Menu Item', [validators.DataRequired()])
    description = StringField('Description', [validators.DataRequired()])
    price = DecimalField('Price', [validators.DataRequired()], places=2, rounding=None)
    choice = SelectField(label='Type of Item', choices=menu_choices)
    addsubmit = SubmitField('Add Item')


# form for returning username for delete account
class UsernameReturnDelete(FlaskForm):
    returnUsernameDelete = StringField('Username', [validators.DataRequired()])
    returnButtonDelete = SubmitField('Delete User')


# form for returning username for make admin
class UsernameReturnAdmin(FlaskForm):
    returnUsernameAdmin = StringField('Username', [validators.DataRequired()])
    returnButtonAdmin = SubmitField('Submit')


# form for admins to add giftcards to the database to be used by users of the website
class GiftCardAddition(FlaskForm):
    giftCardNumber = StringField('Gift Card Number', [validators.DataRequired(), validators.Length(min=15, max=15, message='Gift Card Number should be 15 characters long.')])
    giftCardAmount = SelectField(label='Gift Card Amount', choices=gc_choices)
    addGiftCard = SubmitField('Add Gift Card')


# form for users to add a giftcard from the database to their balance
class AddBalance(FlaskForm):
    balanceNumber = StringField('Gift Card Number', [validators.DataRequired(), validators.Length(min=15, max=15, message='Gift Card Number should be 15 characters long.')])
    addBalanceButton = SubmitField('Redeem Gift Card')


# form to allow admins to remove items from the menu by a title
class RemoveMenuItem(FlaskForm):
    removeItemTitle = StringField('Item to Remove', [validators.DataRequired()])
    removeItemButton = SubmitField('Remove Menu Item')


# form to add image to the gallery
class AddImage(FlaskForm):
    galleryImage = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp'], 'Only Image Uploads Allowed.')])
    galleryLocation = SelectField(label='Location', choices=gallery_choices)
    galleryButton = SubmitField('Add Image')


# form for an admin to remove an image from the database
class RemoveImage(FlaskForm):
    imageName = StringField('Filename to Delete', [validators.DataRequired()])
    removeImageButton = SubmitField('Remove Image')
