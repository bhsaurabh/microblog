# Handlers that respond to requests from browsers
from flask import render_template, flash, redirect
from app import app
from forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
  """
  Index page/Landing page for app
  """
  user = {'nickname': 'Saurabh'}  # fake user
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


@app.route('/login', methods=['GET', 'POST'])
def login():
  """
  Login form for signing into app
  """
  form = LoginForm()
  # form processing upon submission
  # if any field fails validation, False is returned & form is re-rendered
  if form.validate_on_submit():
    msg = 'Login requested for OpenID: "' + form.openid.data + '", remember_me: ' +\
     str(form.remember_me.data)
    flash(msg)  # display logs
    return redirect('/index')  # redirect to index page after login
  # render the form page
  return render_template('login.html', title='Sign In', form=form,
          providers=app.config['OPENID_PROVIDERS'])
