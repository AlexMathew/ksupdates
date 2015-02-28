from flask import Flask, render_template, redirect, url_for, request, session
import os
import psycopg2
from functools import wraps
import urlparse

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = conn.cursor()


def login_required(f):
    @wraps(f)
    def function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return function


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('update'))
    session['type'] = 'unknown'
    return render_template('home.html')


@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
	return render_template('update.html')


if __name__ == '__main__':
	app.run(host="127.0.0.1", port=6666, debug=True)	
	