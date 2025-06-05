from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import date, datetime, timedelta
import MySQLdb
from MySQLdb.cursors import DictCursor
import connect
import re # Regex used for email and phone validations

app = Flask(__name__)
app.secret_key = 'raghav_secret_key' # Setting secret key for session management and flash message


app = Flask(__name__)

connection = None
cursor = None

# definig cursor for the database setup and returning database cursor
def getCursor():
    global connection
    global cursor

    # checking if the connection is not previously established
    if connection is None:
        try:
            connection = MySQLdb.connect(
                user=connect.dbuser,
                password=connect.dbpass,
                host=connect.dbhost,
                database=connect.dbname,
                port=int(connect.dbport),
                autocommit=True
            )       
        except MySQLdb.Error as e:
            
            #displaying error messages if the connection gets failed
            flash(f"Database connection error: {e}", "error")
            raise
    cursor = connection.cursor(DictCursor)
    return cursor


# Homepage route
@app.route("/")
def home():
    return render_template("home.html") #Rendering the homepage template

#Events Route
@app.route("/events", methods=["GET"])
def events():
    cursor = getCursor()
    qstr = "SELECT event_id, event_name FROM events ORDER BY event_name ASC;" # Added query to fetch all event data sorted by event name
    cursor.execute(qstr)
    events = cursor.fetchall()
    return render_template("events.html", events=events) #Rending events template


# Route for displaying data of event tickets purchased by the customer
@app.route("/events/customerlist", methods=["POST"])
def eventcustomerlist():
    cursor = getCursor()
    event_id = request.form.get('event_id')

    if not event_id or not event_id.isdigit(): #Validating if the event ID is provided
        flash("Invalid event selected.", 'error')
        return redirect(url_for('events'))

    qstr_event = "SELECT event_name, event_date FROM events WHERE event_id = %s;" #Selecting event data based on event ID selected by the user
    cursor.execute(qstr_event, (event_id,))
    event_details = cursor.fetchone()

    if not event_details: #Displaying error message if event is not in the database
        flash("Event not found.", 'danger')
        return redirect(url_for('events'))

    # Sorting the customer name alphabetical by family name, then again by date of birth (youngest first)
    qstr_customers = """
        SELECT c.customer_id, CONCAT(c.first_name, ' ', c.family_name) AS full_name, c.date_of_birth, ts.tickets_purchased AS ticket_quantity
        FROM customers c
        JOIN ticket_sales ts ON c.customer_id = ts.customer_id
        WHERE ts.event_id = %s
        ORDER BY c.family_name ASC, c.date_of_birth DESC;
    """
    cursor.execute(qstr_customers, (event_id,))
    customerlist = cursor.fetchall()

    return render_template("eventcustomerlist.html", event=event_details, customers=customerlist) # Rendering eventcustomerlist template


@app.route("/customers")
def customers():
    #List customer details.
    return render_template("customers.html")  


@app.route("/futureevents")
def futureevents():
    #Future Events which still have tickets available.
    return render_template("futureevents.html")  


@app.route("/tickets/buy")
def buytickets():
    #Buy tickets
    return render_template()