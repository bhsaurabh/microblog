from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField
from wtforms.validators import Required, Length
from models import User

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

  def __init__(self, original_nickname, *args, **kwargs):
    """
    Constructor

    Args:
      original_nickname: the original nickname which is to be shown
    """
    Form.__init__(self, *args, **kwargs)
    self.original_nickname = original_nickname

  def validate(self):
    """
    Check if the nickname entered is unique
    """
    if not Form.validate(self):
      return False
    if self.nickname.data == self.original_nickname:
      return True
    user = User.query.filter_by(nickname=self.nickname.data).first()
    if user != None:
      self.nickname.errors.append('This nickname is already in use. Please choose another one.')
      return False
    return True


class PostForm(Form):
  """
  Form for submitting new posts
  """
  post = TextField('post', validators=[Required()])
