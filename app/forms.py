from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField
from wtforms.validators import Required, Length

class LoginForm(Form):
  """
  Form for sign in page
  """
  openid = TextField('openid', validators=[Required()])
  remember_me = BooleanField('remember_me', default=False)


class EditForm(Form):
  """
  Form for editing profile information
  """
  nickname = TextField('nickname', validators=[Required()])
  about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])
