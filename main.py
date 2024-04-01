from flask import Flask, render_template, request, redirect, url_for
import MySQLdb

app = Flask(__name__)

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'u28'
DB_NAME = 'u28'
DB_PASSWORD = 'schoolCLOTHESdeep691'

# App config
PORT = 15097 #provide a unique integer value instead of XXXX, e.g., PORT = 15657


def get_db_connection():
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

#show specific table
@app.route('/show-table', methods=['GET', 'POST'])
def tables():
    conn = get_db_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        table_name = request.form['name']
    return render_template('show_table.html')