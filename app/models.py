from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User:
  """
  Model for a User in the microblog application
  """
  id = db.Column(db.Integer, primary_key=True)
  nickname = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(120), index=True, unique=True)
  role = db.Column(db.SmallInteger, default=ROLE_USER)

  def __repr__(self):
    """
    String representation of the user. Useful in printing

    Returns:
      A string representation of the user
    """
    return '<User %r>' % (self.nickname)
