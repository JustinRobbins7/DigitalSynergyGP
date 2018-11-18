# imort  flask_wtf to use forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, SelectField, validators

# choices for drop down menu on the add menu item form
menu_choices = [('appetizer', 'Appetizer'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('dessert', 'Dessert'), ('beverage', 'Beverage')]


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
