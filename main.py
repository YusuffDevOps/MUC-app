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
    return render_template('index.html', name="Yusuff")

#show specific table
@app.route('/show-table', methods=['GET', 'POST'])
def tables():
    conn = get_db_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        #Get the submitted table name from our form
        table_name = request.form['name']
        print(table_name)
        # execute query to get table elements
        cur.execute(f"SELECT * FROM {table_name}")
        data = cur.fetchall()
        #Get name of columns in our corresponding table
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        columns = cur.fetchall()
        arr =[]
        for c in columns:
            arr.append(c['COLUMN_NAME'])
        print(arr)
        cur.close()
        conn.close()
        # return to frontend the data in table_name and the corresponding columns in table_name
        return render_template('show_table.html', data=data, columns=arr)
    else:
        return render_template('show_table.html', data=[], columns=[])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)