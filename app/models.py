from app import db
from hashlib import md5

ROLE_USER = 0
ROLE_ADMIN = 1

# make a association table for many-many relation
# between followers and followed
followers = db.Table('followers',
            db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
            db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


class User(db.Model):
  """
  Model for a User in the microblog application
  """
  id = db.Column(db.Integer, primary_key=True)
  nickname = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(120), index=True, unique=True)
  role = db.Column(db.SmallInteger, default=ROLE_USER)
  posts = db.relationship('Post', backref='author', lazy='dynamic')
  about_me = db.Column(db.String(140))
  last_seen = db.Column(db.DateTime)
  followed = db.relationship('User',
              secondary=followers,
              primaryjoin=(followers.c.follower_id==id),
              secondaryjoin=(followers.c.followed_id==id),
              backref=db.backref('followers', lazy='dynamic'),
              lazy='dynamic')

  def __repr__(self):
    """
    String representation of the user. Useful in printing

    Returns:
      A string representation of the user
    """
    return '<User %r>' % (self.nickname)

  def avatar(self, size):
    """
    Returns a link to the Avatar of the user (uses Gravatar)

    Args:
      size: the size of the gravatar needed

    Returns:
      link: a link to the user's Gravatar avatar of required size
    """
    return 'http://www.gravatar.com/avatar/' + md5(self.email).hexdigest() + '?d=mm&s=' + str(size)

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

  @staticmethod
  def make_unique_nickname(nickname):
    """
    Check for users with same nickname and append numbers to make unique

    Args:
      nickname: nickname to be verified

    Returns:
      nickname: a unique nickname
    """
    if User.query.filter_by(nickname=nickname).first() == None:
      # already unique
      return nickname
    version = 2
    while True:
      new_nickname = nickname + str(version)
      if User.query.filter_by(nickname=new_nickname).first() == None:
        break
      version += 1
    return new_nickname


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
