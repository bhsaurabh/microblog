from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
  """
  Model for a User in the microblog application
  """
  id = db.Column(db.Integer, primary_key=True)
  nickname = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(120), index=True, unique=True)
  role = db.Column(db.SmallInteger, default=ROLE_USER)
  posts = db.relationship('Post', backref='author', lazy='dynamic')

  def __repr__(self):
    """
    String representation of the user. Useful in printing

    Returns:
      A string representation of the user
    """
    return '<User %r>' % (self.nickname)

  # methods needed by flask.ext.login
  def is_authenticated(self):
    """
    Is the user allowed to authenticate with the app?

    Returns:
      True, if user is allowed to authenticate with the app
    """
    return True

  def is_active(self):
    """
    Is the user active/not blocked?

    Returns:
      True, if user is not banned
    """
    return True

  def is_anonymous(self):
    """
    Is the user NOT allowed to login?

    Returns:
      False, if user is allowed to login
    """
    return False

  def get_id(self):
    """
    Get the user's ID in unicode format

    Returns:
      user's id in unicode format
    """
    return unicode(self.id)


class Post(db.Model):
  """
  Model for a Post in the microblog application
  """
  id = db.Column(db.Integer, primary_key=True)
  body = db.Column(db.String(140))
  timestamp = db.Column(db.DateTime)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

  def __repr__(self):
    """
    String representation of the post. Useful in printing

    Returns:
      A string representation of the post
    """
    return '<Post %r>' % (self.body)
