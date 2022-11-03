from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from packages.adminOop import Operations
from packages.database import CursorFromConnectionPool


class Login(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')

	def validate_login(self, email, password):
		chk_user = Operations(email=email, password=password).checkuser()
		if not chk_user:
			raise ValidationError('Sorry! Login Details not found')



class Newuser(FlaskForm):
	firstname = StringField('Firstname', validators=[DataRequired(), Length(min=2, max=15)])
	lastname = StringField('Lastname', validators=[DataRequired(), Length(min=2, max=15)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	role = SelectField('Role', choices=['Administrator', 'Managing Director', 'Observer'])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Add User')

	
	def validate_email(self, email):
	    email = Operations(str(email)).existing_user()
	    if email:
	        return True


class UserLogin:
	def __init__(self, email, password):
		self.email = email
		self.password = password

	def userlogin(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute('SELECT * FROM employees WHERE email=%s and password=%s LIMIT 1', (self.email, self.password))
			result = cursor.fetchone()
			if result is not None:
				return result


class New_staff(FlaskForm):
	name = StringField('Full Name', validators=[DataRequired()])
	state = StringField('State', validators=[DataRequired()])
	address = StringField('Address', validators=[DataRequired()])
	city = StringField('City', validators=[DataRequired()])
	mobile = IntegerField('Mobile', validators=[DataRequired()])
	bank_name = StringField('Bank name', validators=[DataRequired()])
	acct_num = IntegerField('Account Number', validators=[DataRequired()])
	tax = StringField('Tax Number')
	pension = StringField('Pension company')
	pension_num = StringField('Pension Number')
	submit = SubmitField('Save Information')



