from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import date, datetime, timedelta
import MySQLdb
from MySQLdb.cursors import DictCursor
import connect
import re # Regex used for email and phone validations

app = Flask(__name__)
app.secret_key = 'raghav_secret_key_very_secure_key' # Setting secret key for session management and flash message


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
            flash(f"Database connection error: {e}", "danger")
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
    cursor = getCursor() #Getting database cursor for specifoc route
    qstr = "SELECT event_id, event_name FROM events ORDER BY event_name ASC;" # Added query to fetch all event data sorted by event name
    cursor.execute(qstr)
    events = cursor.fetchall()
    return render_template("events.html", events=events) #Rending events template


# Route for displaying data of event tickets purchased by the customer
@app.route("/events/customerlist", methods=["POST"])
def eventcustomerlist():
    cursor = getCursor() #Getting database cursor for specifoc route
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

#Route for all customers data 
@app.route("/customers")
def customers_list(): 
    cursor = getCursor() #Getting database cursor for specifoc route
    
    # Retrieving customers data sorted by family name and for the same last names, they are sorted by their age(yougest first)
    qstr = "SELECT customer_id, CONCAT(first_name, ' ', family_name) AS full_name, email FROM customers ORDER BY family_name ASC, date_of_birth DESC;"
    cursor.execute(qstr)
    all_customers = cursor.fetchall()
    return render_template("customers.html", all_customers=all_customers)


@app.route("/customersearch", methods=["GET", "POST"])
def customersearch():
    cursor = getCursor() #Getting database cursor for specifoc route
    search_results = [] #intialized an empty list to store the search results
    search_term = ""

    if request.method == "POST":
        search_term = request.form.get('search_term', '').strip()
        if search_term:
            # Retrieving the data from database based on search requested by the user. This data will provide the customer data of customer searched by the user
            qstr = """
                SELECT customer_id, CONCAT(first_name, ' ', family_name) AS full_name, email, first_name, family_name, date_of_birth
                FROM customers
                WHERE first_name LIKE %s OR family_name LIKE %s
                ORDER BY family_name ASC, first_name ASC;
            """ 
            search_param = f"%{search_term}%"
            cursor.execute(qstr, (search_param, search_param))
            search_results = cursor.fetchall() #Retrieved data into search_results
            return render_template("customersearchresults.html", search_results=search_results, search_term=search_term) #Rendering the customersearch result template and passing search_result data
        else:
            flash("Please enter a search term.", "danger")
            # If no search term, redirect back to the search form page
            return redirect(url_for('customersearch'))
    
    return render_template("customersearch.html") #Rendering form by using GEt request for just rendering template

#Add Customer Route
@app.route("/addcustomer", methods=["GET", "POST"])
def addcustomer():
    cursor = getCursor() #Getting database cursor for specifoc route
    if request.method == "POST":
        #Retrieving form data 
        first_name = request.form.get('first_name', '').strip()
        family_name = request.form.get('family_name', '').strip() #
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        email = request.form.get('email', '').strip()
        errors = [] #Initialized error list to store errors

        # Validation used for required fields
        if not first_name:
            errors.append("First Name is required.")
        if not family_name:
            errors.append("Family Name is required.")
        if not date_of_birth_str:
            errors.append("Date of Birth is required.")
        if not email:
            errors.append("Email Address is required.")

        # Validating for email formating
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Invalid Email Address format.")

        # Validateing date of birth as per New Zealand Format and checking for the past date
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                if date_of_birth >= date.today():
                    errors.append("Date of Birth has to be in the past.")
            except ValueError:
                errors.append("Invalid Date of Birth format. Please use YYYY-MM-DD.")

        # Check for unique email address
        if email and not errors: 
            qstr_check_email = "SELECT COUNT(*) AS count FROM customers WHERE email = %s;"
            cursor.execute(qstr_check_email, (email,))
            email_count = cursor.fetchone()['count']
            if email_count > 0:
                errors.append("An account with this email address already exists.") #Appending error to errors list

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("addcustomer.html",
                                   first_name=first_name, family_name=family_name,
                                   date_of_birth=date_of_birth_str, email=email) #Redering template if error occured
        else:
            # Finding the next available customer_id
            qstr_next_id = "SELECT COALESCE(MAX(customer_id), 0) + 1 AS next_id FROM customers;"
            cursor.execute(qstr_next_id)
            next_customer_id = cursor.fetchone()['next_id']
            
            #inserting new customer to the database 
            qstr_insert = """
                INSERT INTO customers (customer_id, first_name, family_name, date_of_birth, email)
                VALUES (%s, %s, %s, %s, %s); 
            """ 
            try:
                cursor.execute(qstr_insert, (next_customer_id, first_name, family_name, date_of_birth, email))
                flash("Customer added successfully!", "success")
                return redirect(url_for('customers_list')) # Redirecting to customers list after adding
            except MySQLdb.Error as e:
                flash(f"Database error: Could not add customer. {e}", "danger") #error handling
                return render_template("addcustomer.html",
                                       first_name=first_name, family_name=family_name,
                                       date_of_birth=date_of_birth_str, email=email)

    return render_template("addcustomer.html") 

#Edit customer route 
@app.route("/editcustomer/<int:customer_id>", methods=["GET", "POST"])
def editcustomer(customer_id):
    cursor = getCursor() #Getting database cursor for specifoc route
    customer_data = None

    if request.method == "GET":
        #Retrieving form data 
        qstr_select = "SELECT customer_id, first_name, family_name, date_of_birth, email FROM customers WHERE customer_id = %s;" # Removed phone
        cursor.execute(qstr_select, (customer_id,))
        customer_data = cursor.fetchone()

        if not customer_data:
            flash("Customer not found.", "danger") #Error handling
            return redirect(url_for('customers_list')) # Redirecting to all customers list

        # Formatng the date for HTML input
        if customer_data['date_of_birth']:
            customer_data['date_of_birth'] = customer_data['date_of_birth'].strftime('%Y-%m-%d')

    elif request.method == "POST":
        first_name = request.form.get('first_name', '').strip()
        family_name = request.form.get('family_name', '').strip()
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        email = request.form.get('email', '').strip()

        errors = [] #Initialized error list

        # Validation used for required fields
        if not first_name:
            errors.append("First Name is required.")
        if not family_name:
            errors.append("Family Name is required.")
        if not date_of_birth_str:
            errors.append("Date of Birth is required.")
        if not email:
            errors.append("Email Address is required.")

        # Validating for email format
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Invalid Email Address format.")

        # Validating date of birth as per New Zealand Format and checking for the past date
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                if date_of_birth >= date.today():
                    errors.append("Date of Birth must be in the past.")
            except ValueError:
                errors.append("Invalid Date of Birth format. Please use YYYY-MM-DD.")

        # Checking for unique email address and current customer's email address is excluded
        if email and not errors:
            qstr_check_email = "SELECT COUNT(*) AS count FROM customers WHERE email = %s AND customer_id != %s;"
            cursor.execute(qstr_check_email, (email, customer_id))
            email_count = cursor.fetchone()['count']
            if email_count > 0:
                errors.append("An account with this email address already exists for another customer.")

        if errors:
            for error in errors:
                flash(error, "danger")
            # Prepopulating the form for good user experience
            customer_data = request.form.to_dict()
            customer_data['customer_id'] = customer_id 
            return render_template("editcustomer.html", customer_data=customer_data)
        else:
            # Updating customer data as per the user request
            qstr_update = """
                UPDATE customers
                SET first_name = %s, family_name = %s, date_of_birth = %s, email = %s
                WHERE customer_id = %s;
            """ 
            try:
                cursor.execute(qstr_update, (first_name, family_name, date_of_birth, email, customer_id))
                flash("Customer details updated successfully!", "success")
                return redirect(url_for('customerticketsummary', customer_id=customer_id))
            except MySQLdb.Error as e:
                flash(f"Database error: Could not update customer. {e}", "danger") #Flashing message if any error comes
                customer_data = request.form.to_dict()
                customer_data['customer_id'] = customer_id
                return render_template("editcustomer.html", customer_data=customer_data)

    return render_template("editcustomer.html", customer_data=customer_data) # Rending template editcustomer

#Customer ticket summary route
@app.route("/customerticketsummary/<int:customer_id>")
def customerticketsummary(customer_id):
    cursor = getCursor() #Getting database cursor for specifoc route

    # Fetching customer details from database 
    qstr_customer = """
        SELECT customer_id, 
               CONCAT(first_name, ' ', family_name) AS full_name, 
               first_name, 
               family_name,
               date_of_birth,
               email
        FROM customers 
        WHERE customer_id = %s;
    """
    cursor.execute(qstr_customer, (customer_id,))
    customer_details = cursor.fetchone()

    if not customer_details:
        flash("Customer not found.", "error")
        return redirect(url_for('customers_list')) # Redirecting to customerList

    # Formatting the date as per NZ way
    if customer_details['date_of_birth']:
        customer_details['date_of_birth'] = customer_details['date_of_birth'].strftime('%Y-%m-%d')

    # Fetching the details of tickets purchased by the customer 
    qstr_purchases = """
        SELECT e.event_name, e.event_date, ts.tickets_purchased
        FROM ticket_sales ts
        JOIN events e ON ts.event_id = e.event_id
        WHERE ts.customer_id = %s
        ORDER BY e.event_date DESC;
    """
    cursor.execute(qstr_purchases, (customer_id,))
    customer_ticket_purchases = cursor.fetchall()

    total_tickets_bought_by_customer = sum(purchase['tickets_purchased'] for purchase in customer_ticket_purchases)

    return render_template("customerticketsummary.html",
                           customer=customer_details,
                           tickets=customer_ticket_purchases,
                           total_tickets=total_tickets_bought_by_customer) # Rendering customerticketsummary template


#Future Events Route used to display all the tickets and events availability in future
@app.route("/futureevents")
def futureevents():
    cursor = getCursor() #Getting database cursor for specifoc route
    # Retrieving future events data from the databse
    qstr = """
        SELECT e.event_id, e.event_name, e.event_date, e.capacity,
               SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END) AS tickets_sold
        FROM events e
        LEFT JOIN ticket_sales ts ON e.event_id = ts.event_id
        WHERE e.event_date > CURDATE()
        GROUP BY e.event_id, e.event_name, e.event_date, e.capacity
        HAVING (e.capacity - SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END)) > 0
        ORDER BY e.event_date ASC;
    """
    cursor.execute(qstr)
    future_events_data = cursor.fetchall() #Storing fetched data to future_events_data
    return render_template("futureevents.html", future_events=future_events_data)

#Buy Tickets Route
@app.route("/tickets/buy", methods=["GET", "POST"])
def buytickets():
    cursor = getCursor() #Getting database cursor for specifoc route
    if request.method == "GET":
        # Fetching available event tickets from database
        qstr_events = """
            SELECT e.event_id, e.event_name, e.event_date, e.capacity, e.age_restriction,
                   SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END) AS tickets_sold
            FROM events e
            LEFT JOIN ticket_sales ts ON e.event_id = ts.event_id
            WHERE e.event_date > CURDATE()
            GROUP BY e.event_id, e.event_name, e.event_date, e.capacity, e.age_restriction
            HAVING (e.capacity - SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END)) > 0
            ORDER BY e.event_date ASC;
        """
        cursor.execute(qstr_events)
        available_events = cursor.fetchall()

        # Calculating the event tickets remaining
        for event in available_events:
            event['remaining_tickets'] = event['capacity'] - event['tickets_sold']

        # Fetching the customer list from database
        qstr_customers = "SELECT customer_id, CONCAT(first_name, ' ', family_name) AS full_name, date_of_birth FROM customers ORDER BY family_name ASC, first_name ASC;"
        cursor.execute(qstr_customers)
        customers_data = cursor.fetchall()

        return render_template("buytickets.html", events=available_events, customers=customers_data) #Redering buytickets.html

    elif request.method == "POST":
        # Fetching user input
        customer_id = request.form.get('customer_id')
        event_id = request.form.get('event_id')
        quantity_str = request.form.get('quantity')

        errors = [] # List to store errors

        # Validating the fields that are required
        if not customer_id:
            errors.append("Please select a customer.")
        if not event_id:
            errors.append("Please select an event.")
        if not quantity_str:
            errors.append("Number of tickets is required.")
        
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                errors.append("Number of tickets must be at least 1.")
        except ValueError:
            errors.append("Invalid number of tickets.")
            quantity = 0 # Setting quantity to 0 so that further calculation issues could be prevented

        # Fetching event customer and details for validation ahead
        customer_dob = None
        event_age_restriction = None
        event_capacity = 0
        tickets_sold = 0

        if customer_id and customer_id.isdigit():
            qstr_customer_dob = "SELECT date_of_birth FROM customers WHERE customer_id = %s;"
            cursor.execute(qstr_customer_dob, (customer_id,))
            customer_data = cursor.fetchone()
            if customer_data:
                customer_dob = customer_data['date_of_birth']
            else:
                errors.append("Selected customer not found.")
        
        if event_id and event_id.isdigit():
            qstr_event_details = """
                SELECT e.age_restriction, e.capacity,
                       SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END) AS tickets_sold
                FROM events e
                LEFT JOIN ticket_sales ts ON e.event_id = ts.event_id
                WHERE e.event_id = %s
                GROUP BY e.event_id, e.age_restriction, e.capacity;
            """
            cursor.execute(qstr_event_details, (event_id,))
            event_details = cursor.fetchone()
            if event_details:
                event_age_restriction = event_details['age_restriction']
                event_capacity = event_details['capacity']
                tickets_sold = event_details['tickets_sold']
            else:
                errors.append("Selected event not found or has no available tickets.")

        # Applying validations for age restriction
        if customer_dob and event_age_restriction is not None:
            today = date.today()
            age = today.year - customer_dob.year - ((today.month, today.day) < (customer_dob.month, customer_dob.day))
            if age < event_age_restriction:
                errors.append(f"Customer is too young for this event. Minimum age required: {event_age_restriction}.")

        # Validation for tickets which are available
        tickets_remaining = event_capacity - tickets_sold
        if quantity > tickets_remaining:
            errors.append(f"Not enough tickets available. Only {tickets_remaining} tickets left.")


        if errors:
            for error in errors:
                flash(error, "danger") #Flashing error messages if error ouccur

            qstr_events_get = """
                SELECT e.event_id, e.event_name, e.event_date, e.capacity, e.age_restriction,
                       SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END) AS tickets_sold
                FROM events e
                LEFT JOIN ticket_sales ts ON e.event_id = ts.event_id
                WHERE e.event_date > CURDATE()
                GROUP BY e.event_id, e.event_name, e.event_date, e.capacity, e.age_restriction
                HAVING (e.capacity - SUM(CASE WHEN ts.tickets_purchased IS NULL THEN 0 ELSE ts.tickets_purchased END)) > 0
                ORDER BY e.event_date ASC;
            """
            cursor.execute(qstr_events_get)
            available_events = cursor.fetchall()

            for event in available_events:
                event['remaining_tickets'] = event['capacity'] - event['tickets_sold']

            qstr_customers_get = "SELECT customer_id, CONCAT(first_name, ' ', family_name) AS full_name, date_of_birth FROM customers ORDER BY family_name ASC, first_name ASC;"
            cursor.execute(qstr_customers_get)
            customers_data = cursor.fetchall()
            
            return render_template("buytickets.html", events=available_events, customers=customers_data, 
                                   selected_customer_id=customer_id, selected_event_id=event_id, selected_quantity=quantity_str)
        else:
            # If all validations gets paased then continue with ticket purchase
            try:
                #updating tickets data in the database
                qstr_insert_ticket = """
                    INSERT INTO ticket_sales (customer_id, event_id, tickets_purchased)
                    VALUES (%s, %s, %s);
                """
                cursor.execute(qstr_insert_ticket, (customer_id, event_id, quantity))
                flash("Tickets purchased successfully!", "success")
                return redirect(url_for('customerticketsummary', customer_id=customer_id)) #Reirecting to customersummary route
            except MySQLdb.Error as e:
                flash(f"Database error: Could not purchase tickets. {e}", "error") #Flashing error messages
                return redirect(url_for('buytickets')) #Redirecting to buytickets route

