from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms.validators import DataRequired, Email, EqualTo

class QuickResume(FlaskForm):
    resume = FileField('Resume File:')
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    