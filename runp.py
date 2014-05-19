#!flask/bin/python

# Starts production server with microblog app

from app import app  # import app from app package (init script useful)
app.run(port=3000, debug=False)
