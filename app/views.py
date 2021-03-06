# Handlers that respond to requests from browsers
from flask import render_template, flash, redirect, session, url_for, g, request
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, EditForm, PostForm, SearchForm
from models import User, ROLE_USER, ROLE_ADMIN, Post
from datetime import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, WHOOSH_ENABLED

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required  # cannot view this page without signing in
def index(page=1):
  """
  Index page/Landing page for app
  """
  user = g.user
  form = PostForm()
  posts = user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
  if form.validate_on_submit():
    post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=user)
    db.session.add(post)
    db.session.commit()
    flash('SUCCESS: Your post is now live!')
    return redirect(url_for('index'))
  return render_template('index.html', title='Home', user=user, posts=posts,
                    form=form)


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
    g.search_form = SearchForm()
  g.search_enabled = WHOOSH_ENABLED

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
    flash('ERROR: Invalid login. Please try again.')
    return redirect(url_for('login'))
  user = User.query.filter_by(email=resp.email).first()
  if user is None:
    # no such user, create a new user
    nickname = resp.nickname
    if nickname is None or nickname == '':
      # could not get nickname from OpenID provider
      # get a nickname from the email address
      nickname = resp.email.split('@')[0]
    # make the nickname unique
    nickname = User.make_unique_nickname(nickname)
    # create a new user and add to database
    user = User(nickname=nickname, email=resp.email, role=ROLE_USER)
    db.session.add(user)
    db.session.commit()
    # make every new user follow himself
    # so that a user's posts appear on his feed
    user = user.follow(user)
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
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
  """
  Profile page for a user

  Args:
    nickname: nickname of the user whose profile page is needed
  """
  # verify if user exists
  user = User.query.filter_by(nickname=nickname).first()
  if user is None:
    flash('ERROR: User ' + nickname + ' not found!')
    return redirect(url_for('index'))
  posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
  return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
  """
  Page to edit profile
  """
  form = EditForm(g.user.nickname)
  if form.validate_on_submit():
    g.user.nickname = form.nickname.data
    g.user.about_me = form.about_me.data
    db.session.add(g.user)
    db.session.commit()
    flash('SUCCESS: Your changes have been saved.')
    return redirect(url_for('edit'))
  else:
    # provide default values, else form will be very irritating
    form.nickname.data = g.user.nickname
    form.about_me.data = g.user.about_me
  return render_template('edit.html', title='Edit Profile', form=form)


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
  """
  Follow a user
  """
  user = User.query.filter_by(nickname=nickname).first()
  if user is None:
    flash('ERROR: User ' + nickname + ' cannot be found.')
    return redirect(url_for('index'))
  if user == g.user:
    flash('ERROR: You cannot follow yourself.')
    return redirect(url_for('user', nickname=nickname))
  u = g.user.follow(user)
  if u is None:
    flash('ERROR: You cannot follow: ' + nickname)
    return redirect(url_for('user', nickname=nickname))
  db.session.add(u)
  db.session.commit()
  flash('SUCCESS: You are now following: ' + nickname)
  return redirect(url_for('user', nickname = nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
  """
  Unfollow a user
  """
  user = User.query.filter_by(nickname=nickname).first()
  if user is None:
    flash('ERROR: User ' + nickname + ' cannot be found.')
    return redirect(url_for('index'))
  if user == g.user:
    flash('ERROR: You cannot unfollow yourself.')
    return redirect(url_for('user', nickname=nickname))
  u = g.user.unfollow(user)
  if u is None:
    flash('ERROR: You cannot unfollow: ' + nickname)
    return redirect(url_for('user', nickname=nickname))
  db.session.add(u)
  db.session.commit()
  return redirect(url_for('user', nickname=nickname))


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


@app.route('/search', methods=['POST'])
@login_required
def search():
  """
  Collects data to search, and avoids re-searching on refreshing pages
  """
  if not g.search_form.validate_on_submit():
    return redirect(url_for('index'))
  return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route('/search_results/<query>')
@login_required
def search_results(query):
  """
  Uses Whooshalchemy to perform full-text search
  """
  results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
  return render_template('search_results.html', query=query, results=results)
