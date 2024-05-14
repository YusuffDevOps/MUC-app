from flask import Flask, render_template, request, redirect, url_for
import MySQLdb
import locale

app = Flask(__name__)

# Database configuration
DB_HOST = 'bjm2ilghwdekljzhlply-mysql.services.clever-cloud.com'
DB_USER = 'uhxwhl1fwaww00tv'
DB_NAME = 'bjm2ilghwdekljzhlply'
DB_PASSWORD = 'gUEM5LAmUrB7RuwR6Ro4'

#Set locale for currency function 
locale.setlocale( locale.LC_ALL, 'en_CA.UTF-8' )

# App config
PORT = 50306 #provide a unique integer value instead of XXXX, e.g., PORT = 15657


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
        data = []
        arr =[]
        table_name = request.form['name']
        if table_name == "suppliers":
            cur.execute(f"""SELECT supplier._id, name, email, telephone.tel 
            FROM supplier, telephone WHERE supplier._id = telephone.sup_id;""")
            data = cur.fetchall()
            arr = ["_id", "name", "email", "tel"]
        elif table_name == "parts":
            cur.execute(f"SELECT * FROM {table_name}")
            data = cur.fetchall()
            arr = ["_id","price","description"]
        elif table_name == "orders":
            cur.execute("""SELECT orders.order_date, orders.sup_id, part_orders.part_id, part_orders.qty
            FROM part_orders, orders WHERE part_orders.order_id = orders._id;""")
            data = cur.fetchall()
            arr =["order_date","sup_id","part_id","qty"]
        cur.close()
        conn.close()
        # return to frontend the data in table_name and the corresponding columns in table_name
        return render_template('show_table.html', data=data, columns=arr)
    else:
        return render_template('show_table.html', data=[], columns=[])


#shows expenses page and redirects user to request
@app.route("/get-expenses/", methods=['GET', 'POST'])
def get_expenses():
    if request.method =='GET':
        return render_template('annual_expense.html', data=[])
    else:
        start = request.form["start"]
        end = request.form["end"]
        return redirect(f"/get-annual-expense/{start}/{end}")


# GET Annual Expenses for parts from start to end year
@app.route("/get-annual-expense/<string:start>/<string:end>", methods=['GET'])
def total_expense(start, end):
    conn = get_db_connection()
    cur = conn.cursor()
    #SQL query to get total expense for each YEAR
    cur.execute(f"""SELECT YEAR(order_date) as year,  sum(price*qty) FROM 
    part_orders, parts, orders WHERE 
    part_orders.part_id = parts._id AND orders._id = part_orders.order_id AND 
    YEAR(order_date)>={start} AND YEAR(order_date)<={end} GROUP BY YEAR(order_date);""")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('annual_expense.html', data=data, currency=locale.currency)

#Budget Projection
@app.route("/project-budget", methods=['GET', 'POST'])
def project_budget():
    if request.method == "GET":
        return render_template('project_budget.html', data=[])
    else:
        #Get number of years and inflation rate
        years = int(request.form["numYears"])
        rate = float(request.form["rate"])
        arr = []
        conn = get_db_connection()
        cur = conn.cursor()
        #SQL query to get the recent expense 
        cur.execute("""SELECT YEAR(order_date) as year, sum(price*qty) 
        FROM part_orders, parts, orders 
        WHERE part_orders.part_id = parts._id AND orders._id = part_orders.order_id AND YEAR(order_date)=2022
        GROUP BY YEAR(order_date);""")
        data = cur.fetchall()
        recent_year = data[0][0]
        recent_expense = data[0][1]
        total_rate = (100+rate)/100
        #Add tuple containg new year and projected expenses for the year
        for i in range (1, years+1):
            arr.append((recent_year+i, float("{:.2f}".format((recent_expense)*(total_rate)**(i)))))
        cur.close()
        conn.close()
        return render_template('project_budget.html', data=arr, currency=locale.currency)

@app.route("/add-supplier", methods=['GET', 'POST'])
def add_supplier():
    if request.method == "GET":
        return render_template('add_supplier.html', data=[])
    else:
        _id = request.form["id"]
        name = request.form["name"]
        email = request.form["email"]
        numbers = request.form["numbers"].split(",")
        conn = get_db_connection()
        cur = conn.cursor()
        #Check if supplier exists with _id
        cur.execute(f"SELECT * FROM supplier WHERE _id = {_id}")
        data = cur.fetchall()
        #If supplier Doesn't exist
        if data == ():
            #Insert  into supplier relation
            cur.execute(f"INSERT INTO supplier(_id, name, email) VALUES ({_id}, '{name}', '{email}')")
            #Insert numbers into telephone relation
            for number in numbers:
                cur.execute(f"INSERT INTO telephone(sup_id, tel ) VALUES ({_id}, '{number}')")
            conn.commit()
            cur.execute(f"""SELECT supplier._id, name, email, telephone.tel 
            FROM supplier, telephone WHERE supplier._id = telephone.sup_id AND supplier._id={_id} ;""")
            data = cur.fetchall()
            print(data)
            arr = ["_id", "name", "email", "tel"]
            cur.close()
            conn.close()
            return render_template('add_supplier.html', data=data, columns=arr)
        else:
            return render_template('add_supplier.html', data=[], error="Supplier already exists please try different _id")



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)