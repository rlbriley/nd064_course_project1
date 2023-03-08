import logging
import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_connection_cnt = 0
post_cnt = 0
db_error = False

# Stream logs to a file, and set the default log level to DEBUG
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_cnt
    connection = sqlite3.connect('techtrends/database.db')
    connection.row_factory = sqlite3.Row
    db_connection_cnt += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global db_error
    connection = get_db_connection()
    if db_error is False:
        try:
            post = connection.execute('SELECT * FROM posts WHERE id = ?',
                                     (post_id,)).fetchone()
            db_error = False
        except sqlite3.Error as er:
            log.exception(er)
            db_error = True
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application
@app.route('/')
def index():
    global post_cnt
    global db_error
    connection = get_db_connection()
    if db_error is False:
        try:
            posts = connection.execute('SELECT * FROM posts').fetchall()
            connection.close()
            post_cnt = len(posts)
            db_error = False
            log.debug("Database contains %i posts", post_cnt)
        except sqlite3.Error as er:
            log.exception(er)
            db_error = True
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        log.error("404, Post %i not found.", post_id)
        return render_template('404.html'), 404
    else:
        log.info("Displaying post %-4i with title '%s'",
                 post_id, post['title'])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log.debug("about endpoint accessed, rendering 'about.html'")
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    global db_error
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            log.error("Title not set!")
            flash('Title is required!')
        else:
            connection = get_db_connection()
            if db_error is False:
                try:
                    cursor = connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                                                (title, content))
                    connection.commit()
                    connection.close()
                    db_error = False

                    log.info("Created post %-4i with title '%s'",
                            cursor.lastrowid, title)

                except sqlite3.Error as er:
                    log.exception(er)
                    db_error = True

    return render_template('create.html')

# healthz REST route.
# Will return "OK - healthy" if the application is running
@app.route("/healthz")
def healthz():
    '''
    healthz REST route.
    Will return "OK - healthy" if the application is running
    '''
    global db_error
    if db_error is False:
        response = app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )
    log.info('healthz request successful response=%s',
             json.dumps(response.json))
    return response

# metrics REST route.
# will return the number of times each endpoint has been accessed. Plus the uptime for the
# application.
@app.route("/metrics")
def metrics():
    '''
    metrics REST route.
    will return the number of database connections that have been made, and the number
    of post in the database.
    '''
    global post_cnt
    global db_connection_cnt
    response = app.response_class(
        response=json.dumps(
            {"db_connection_count": db_connection_cnt, "post_count": post_cnt}),
        status=200,
        mimetype='application/json'
    )
    log.debug('metrics request successful response=%s',
              json.dumps(response.json))
    return response


# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
