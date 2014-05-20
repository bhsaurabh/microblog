# Handlers that respond to requests from browsers
from flask import render_template, flash, redirect, session, url_for, g, request
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from models import User, ROLE_USER, ROLE_ADMIN

@app.route('/')
@app.route('/index')
def index():
  """
  Index page/Landing page for app
  """
  user = g.user
  posts = [ # fake array of posts
        {
            'author': { 'nickname': 'John' },
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': { 'nickname': 'Susan' },
            'body': 'The Avengers movie was so cool!'
        }]
  return render_template('index.html', title='Home', user=user, posts=posts)


@app.before_request
def before_request():
  """
  Runs before the view function
  Sets the current user to the global user for better access
  """
  # current_user is set by login_user of flask-login
  g.user = current_user


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler  # tell Flask-OpenID that this is our login view function
def login():
  """
  Login form for signing into app
  """
  # Do not present login page if already signed in
  if g.user is not None and g.user.is_authenticated():
    return redirect(url_for('index'))
  # Present login form
  form = LoginForm()
  # process form fields upon submission
  if form.validate_on_submit():
    session['remember_me'] = form.remember_me.data
    # Try login with Open-ID
    # Query OpenID provider for user's nickname and email
    return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
  # render the form
  render_template('login.html', title='Sign In', form=form,
                  providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
  """
  Callback after authentication using Flask-OpenID

  Args:
    resp: response from OpenID provider
  """
  if resp.email is None or resp.email == '':
    flash('Invalid login. Please try again.')
    return redirect(url_for('login'))
  user = User.query.filter_by(email=resp.email).first()
  if user is None:
    # no such user, create a new user
    nickname = resp.nickname
    if nickname is None or nickname == '':
      # could not get nickname from OpenID provider
      # get a nickname from the email address
      nickname = resp.email.split('@')[0]
    # create a new user and add to database
    user = User(nickname=nickname, email=resp.email, role=ROLE_USER)
    db.session.add(user)
    db.session.commit()
  remember_me = False
  if 'remember_me' in session:
    remember_me = session['remember_me']
    session.pop('remember_me', False)
  login_user(user, remember_me=remember_me)  # register this is a valid login
  return redirect(request.args.get('next') or url_for('index'))


@lm.user_loader
def load_user(id):
  """
  Loads the user from the database

  Args:
    id: ID of required user (could be in unicode format)

  Returns:
    user: the user object
  """
  return User.query.get(int(id))
