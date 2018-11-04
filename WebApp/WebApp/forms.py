from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField
from wtforms.validators import DataRequired, equal_to


# form for creating account
class CreateAccount(FlaskForm):
    username = StringField('Please Enter a Username', validators=[DataRequired()])
    password = PasswordField('Please Enter a Password', validators=[DataRequired()])
    # validate for same password as above
    passwordverify = PasswordField('Please Re-Enter Your Password', validators=[equal_to(password), DataRequired()])
    createaccount = SubmitField('Create Account')


# form for logging into the system
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    loginsubmit = SubmitField('Sign In')


# form for adding a menu item
class AddMenuItem(FlaskForm):
    title = StringField('Menu Item', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    price = DecimalField('Price', places=2, rounding=None, validators=[DataRequired()])
    addsubmit = SubmitField('Add Item')
