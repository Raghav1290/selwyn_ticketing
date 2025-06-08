# Selwyn Ticketing Project Report 

## DESIGN DECISIONS

* **Flexible Templates And Routes:** Routes and HTML templates were designated  to each of the main functions (such as purchasing tickets, showing customers and events data, viewing customerEvent summary). With the help of this separation, we got improved maintainability,  Cleaner code and scalability.

* **Using POST Request Method For Data Modifications:** To avoid unintentional data changes via url, post request method is used by all forms to alter database such as adding or editing customer data or buying tickets for the events.   

* **GET Request Method For Data Retrieval:** In accordance with the REST(Representational State Transfer Application Programming) principle, GET request method is only used for read-only pages such as retrieving events and customers data from the database and showing it on the respective HTML pages.

* **Bootstrap Validation:** Built-in bootstrap validation is being used by all forms for a better user experience as well as to ensure that no incorrect data gets submitted to the database.

* **Flash Flash Messages:** Flask flash messages are used on form submissions to ensure that the user should get instant feedback on errors or successful submits while submitting the forms. 

* **Customer Data Display Optimized:** Customer names are shown as full names not as first name and last name using the Concat function of SQL which gives a good user experience. Along with that the customer data list is sorted by family names and if any customer has the same last name then they are sorted by their age(youngest first) to meet business requirements.

* **Design Of Data Model:** The ticket_sales table is a junction between events and customers which helps in supporting a many-to-many relationship and tickets_purchased help in tracking ticket quantity.

* **Age Restrictions For Buying Tickets:** Age restriction validations have been added to the buy tickets page so that only customers with valid age can buy or be permitted to buy a ticket. The validations have been done as per the age restrictions of event table data.
 
* **New Zealand Based Date Formatting:** Time and dates are consistently formatted as New Zealand based data format by using python’s strftime.

* **Avoided External Javascript and Style Sheets:** No external Javascript code and css have been used as per the instructions of the assignment. Only bootstrap cdn and classes are used for the styling and scripting work.

* **Considering Event Capacity:** It is being noted that the customer should not be able to make ticket purchases more than the available tickets. Proper validations have been added for smooth functioning of the application.

* **Proper Naming Conventions:** To reduce bugs and increase code understanding,  Database columns, form, fields and python variables have been given proper naming conventions.

* **Appropriate Comments:** Proper comments have been added to Python, HTML and SQL codes for better understanding.

## Image Source
RahulPandit. (2020, January 16). [Photograph of Concert]. https://pixabay.com/photos/concert-performance-music-festival-4768496/

## Database Questions
### Answer 1:
* ```sql
  CREATE TABLE events (
    event_id INT,
    event_name VARCHAR(100),
    age_restriction INT,
    capacity INT,
    event_date DATE,
    PRIMARY KEY (event_id));
  ```

### Answer 2:
* ```sql
  CREATE TABLE ticket_sales (
    ticket_sales_id INT NOT NULL AUTO_INCREMENT,
    customer_id INT,
    event_id INT,
    tickets_purchased INT,
    PRIMARY KEY (ticket_sales_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id));
  ```

### Answer 3: 
* ```sql
  CREATE TABLE event_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description TEXT);
  ```  

### Answer 4:
* ```sql
  INSERT INTO event_categories (category_name, description) VALUES ('Workshop', 'Educational and skill-based learning events');
  ```

### Answer 5
To the existing data model, we should do the following to fullly integrate **event categories**:
* A **add_category** field should be added to the events table so that each event could get associated with a category.
* We should define a foreign key relationship between **event_categories.category_id** and **events.category_id**.

By performing these steps, events would be allowed to be categorized and filtering could be enabled or organised by event type.


