from flask import Flask, render_template, redirect, url_for, request, session,\
    flash, jsonify
from werkzeug.contrib.atom import AtomFeed
import os
import psycopg2
from functools import wraps
import urlparse
import datetime

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']


def connectDB(wrapped):
    @wraps(wrapped)
    def inner(*args, **kwargs):
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
        ret = wrapped(cur, *args, **kwargs)
        conn.commit()
        cur.close()
        conn.close()
        return ret
    return inner


def login_required(f):
    @wraps(f)
    def function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return function


@app.route('/', methods=['GET', 'POST'])
@connectDB
def home(cur):
	if request.method == 'GET':
	    if 'username' in session:
	        return redirect(url_for('update'))
	    session['type'] = 'unknown'
	    return render_template('home.html', logged_in=False)
	else:
		cur.execute("SELECT * FROM ROOT")
		auth = cur.fetchone()
		user_input = (request.form['username'], request.form['password'])
		if user_input == auth:
			session['username'] = request.form['username']
			return redirect(url_for('update'))
		else:
			return redirect(url_for('home'))


@app.route('/update', methods=['GET', 'POST'])
@login_required
@connectDB
def update(cur):
    if request.method == 'GET':
        return render_template('update.html', logged_in=True)
    else:
        cluster = request.form['cluster']
        announcement = request.form['announcement']
        timestamp = datetime.datetime.now()
        try:
            cur.execute("INSERT INTO ANNOUNCEMENTS (CLUSTER, ANNOUNCEMENT, TIME) VALUES \
                        (%s, %s, %s)", (cluster, announcement, timestamp))
            flash('The update has been posted.')
            error = " "
        except:
            flash('ERROR ! The update was NOT posted.')
            error = " alert-danger"
        finally:
            return render_template('update.html', logged_in=True, error=error)


@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session['type'] = 'unknown'
    return redirect(url_for('home'))


@app.route('/recent.atom')
@connectDB
def recent_feed(cur):
    feed = AtomFeed('Recent announcements', 
                    feed_url=request.url,
                    url=request.url_root)
    cur.execute("SELECT * FROM ANNOUNCEMENTS ORDER BY TIME DESC LIMIT 50")
    announcements = cur.fetchall()
    for i, announcement in enumerate(announcements):
        feed.add(
            "ANNOUNCEMENT " + str(i),
            unicode(announcement[0] + announcement[1]),
            author="KS",
            url=request.url,
            updated=announcement[2]
            )
    return feed.get_response()


@app.route('/api/count', methods=['GET'])
@connectDB
def count(cur):
    cur.execute("SELECT COUNT(*) FROM ANNOUNCEMENTS")
    count = cur.fetchone()[0]
    return jsonify({'count': count})


if __name__ == '__main__':
	app.run(host="127.0.0.1", port=6666, debug=True)	
