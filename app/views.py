# Handlers that respond to requests from browsers
from flask import render_template, flash, redirect, session, url_for, g, request
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, EditForm
from models import User, ROLE_USER, ROLE_ADMIN
from datetime import datetime

@app.route('/')
@app.route('/index')
@login_required  # cannot view this page without signing in
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
  if g.user.is_authenticated():
    # Add the current time to this user's last seen
    g.user.last_seen = datetime.utcnow()
    db.session.add(g.user)
    db.session.commit()


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
  return render_template('login.html', title='Sign In', form=form,
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
  login_user(user, remember=remember_me)  # register this is a valid login
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


@app.route('/logout')
def logout():
  """
  Logs a user out of the microblog application
  """
  logout_user()
  return redirect(url_for('index'))


@app.route('/user/<nickname>')
@login_required
def user(nickname):
  """
  Profile page for a user

  Args:
    nickname: nickname of the user whose profile page is needed
  """
  # verify if user exists
  user = User.query.filter_by(nickname=nickname).first()
  if user is None:
    flash('User ' + nickname + ' not found!')
    return redirect(url_for('index'))
  posts = [ # fake posts by user
        { 'author': user, 'body': 'Test post #1' },
        { 'author': user, 'body': 'Test post #2' }]
  return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
  """
  Page to edit profile
  """
  form = EditForm()
  if form.validate_on_submit():
    g.user.nickname = form.nickname.data
    g.user.about_me = form.about_me.data
    db.session.add(g.user)
    db.session.commit()
    flash('Your changes have been saved.')
    return redirect(url_for('edit'))
  else:
    # provide default values, else form will be very irritating
    form.nickname.data = g.user.nickname
    form.about_me.data = g.user.about_me
  return render_template('edit.html', title='Edit Profile', form=form)


@app.errorhandler(404)
def not_found_error(error):
  """
  404: Page not found
  """
  return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
  """
  404: Internal error
  """
  db.session.rollback()
  return render_template('500.html'), 500
