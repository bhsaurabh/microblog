from app import db, app
from hashlib import md5
import flask.ext.whooshalchemy as whooshalchemy

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

  # methods to deal with follow/unfollow
  def follow(self, user):
    """
    Follow a user, if not following already

    Args:
      user: The user to follow

    Returns:
      A reference to itself, if the operation is successful
    """
    if not self.is_following(user):
      self.followed.append(user)
      return self  # a good way to check if follow operation is successful

  def unfollow(self, user):
    """
    Unfollow a user, if following him

    Args:
      user: The user to unfollow

    Returns:
      A reference to itself, if the operation is successful
    """
    if self.is_following(user):
      self.followed.remove(user)
      return self

  def is_following(self, user):
    """
    Checks if a user is being followed or not

    Args:
      user: The user to check, if being followed or not

    Returns:
      True, if the user is followed; False otherwise
    """
    return self.followed.filter(followers.c.followed_id == user.id).count() > 0

  def followed_posts(self):
    """
    Use a single DB query to get posts followed by this user, sorted by time

    Returns:
      A list of all followed posts, sorted by time in descending order (recent 1st)
    """
    return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())

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
  __searchable__ = ['body']  # data that has to be indexed for full text search

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


whooshalchemy.whoosh_index(app, Post)  # initialise the full-text index
