from flask import Flask, render_template, url_for, request, redirect, session
import pymysql
import re
import random
from flask_bootstrap import Bootstrap
from flaskext.mysql import MySQL
from flask_googlemaps import GoogleMaps, Map
import base64
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.permanent_session_lifetime = timedelta(minutes=15)
Bootstrap(app)
mapsKey = 'AIzaSyDWt399XO3bPkDtZsE3zQbA9iIdlQg1xLk'
GoogleMaps(app, key=mapsKey)

# Connecting to database
conn = pymysql.connect(
    host='production.cvikcdpdf7om.us-west-1.rds.amazonaws.com',
    port=3306,
    user='root',
    password='cscteam02',
    db='gatorgrub',

)


mysql = MySQL()
mysql.init_app(app)

# # small class for image uploads
# class MyForm(FlaskForm):
#     image = FileField('image')

cursor = conn.cursor()

cursor.execute("SELECT type, foodTypeIcon FROM FoodTypes")
foodTypes = cursor.fetchall()

cursor.execute(
    "SELECT restaurantName, restaurantFoodType, restaurantPrice, restaurantID, restaurantImage from Restaurant")
allData = cursor.fetchall()

def restaurantPageQuery(input):
    beginning = "SELECT restaurantID, restaurantName, restaurantFoodType, restaurantPrice, restaurantAddress, restaurantImage FROM Restaurant WHERE restaurantName = "
    formatInput = "\"" + input + "\""
    query = beginning + formatInput
    return query


# Reviewed by Patricia Sarno
# on 05/15/2021

# COMMENT #1
# SUGGESTION TO PUT A MORE DETAILED DESCRIPTION OF THE SEARCH QUERY RIGHT HERE.

# COMMENT #2
# EXPLAIN WHAT THE DROP DOWN AND SEARCH BAR IS SUPPOSED TO DO LIKE WHAT PARAMETERS IT NEEDS, ETC.

# COMMENT #3
# CAN EXPLAIN WHAT DATA WE ARE GETTING/WHAT IS NEEDED AND WHAT IS BEING RETURNED WHEN
# CURSOR.EXECUTE IS EXECUTED.

# Takes a string input and searches through the Restaurant and
# FoodType tables in the database to find matches
def searchQuery(input):

    # check to see if valid entry
    if len(input) > 40:
        return "error"

    # get the data
    input = "%" + input + "%"
    cursor.execute("SELECT restaurantName, restaurantFoodType, restaurantPrice, restaurantImage from Restaurant WHERE restaurantName LIKE %s OR restaurantFoodType LIKE %s", (input, input))
    data = cursor.fetchall()

    # if search was empty
    if input == 'all' or len(data) == 0:
        return "error"
    # convert photos to base64
    else:
        # convert BLOB (image) to base64
        outer = list(data)
        convertPhoto(outer)
        data = tuple(outer)
    # return query results
    return data


# takes a tuple returned from a query and converts the
# images to base64 (so they appear in browser)
def convertPhoto(listOfData):
    img = len(listOfData[0]) - 1
    for i in range(len(listOfData)):
        inner = list(listOfData[i])
        inner[img] = base64.b64encode(inner[img])  # convert image BLOB to base64
        inner[img] = inner[img].decode("UTF-8")  # decode base64 to UTF-8
        listOfData[i] = tuple(inner)


# Google Map Function to Render Maps through view
def mapView():
    restaurantMap = Map(
        identifier='restaurantMap',
        varname='restaurantMap',
        style='height:600px;width:100%;margin:0;',
        zoom='15',
        lat=37.7281281,
        lng=-122.479742,
        markers=[
            {
                'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                'lat': 37.7281281,
                'lng': -122.479742,
                'labelbox': '<img src="static/image/background.jpg" />'
            }
        ]
    )
    return restaurantMap


# Generates a random number with a specified number of digits
def randomNumGenerator(numOfDigits):
    start = 10 ** (numOfDigits - 1)
    end = (10 ** numOfDigits) - 1
    return random.randint(start, end)


# converts photos for all restaurants for global use
outer = list(allData)
convertPhoto(outer)
allData = tuple(outer)

# converts photos for food types for global use
outer = list(foodTypes)
convertPhoto(outer)
foodTypes = tuple(outer)


# class ResultsForm(FlaskForm):
#     result = StringField('result', validators=[InputRequired(), Length(min=1, max=80)])


@app.route('/', methods=['GET', 'POST'])
def index2():
    if request.method == "POST":
        # reset input string to clear data from multiple searches
        input = ""
        # If going to restaurant page
        if 'restaurant_page' in request.form:
            # redirect to restaurant
            input = request.form['restaurant_page']
            print(input)
            return redirect(url_for('restaurantPage', restaurant=input))

        # if searching by category button
        if 'category' in request.form:
            # get food type
            input = request.form.get('category')

        # if using drop down or search bar
        # get the user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"
        # redirect to results page
        return redirect(url_for('results', srch=input))


    # return home page
    return render_template('index2.html', data=allData, food=foodTypes)


# return results page
@app.route('/results-<srch>', methods=['GET', 'POST'])
def results(srch):
    msg = ''
    if request.method == "POST":
        # reset string input in case of multiple searches
        input = ""
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"
        return redirect(url_for('results', srch=input, msg=msg))

    # query the database for results of search bar search
    data = searchQuery(srch)
    if data == "error":
        msg = "We couldn't find anything like that. Here are some suggestions!"
        return render_template('results.html', data=allData, food=foodTypes, results=len(allData), photo=4, msg=msg)
    results = len(data)

    return render_template('results.html', data=data, food=foodTypes, results=results, photo=3, msg=msg)


@app.route('/customerlogin', methods=['GET', 'POST'])
def customerlogin():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Creating variables to access easily
        username = request.form['username']
        password = request.form['password']

        # Authenticating account in MySQL database
        cursor.execute('SELECT * FROM RegisteredCustomer WHERE customerUsername = %s AND customerPassword = sha1(%s)',
                       (username, password))
        data = cursor.fetchall()

        # if wrong login
        if len(data) != 1:
            message = 'Username/Password incorrect'
            return render_template("customerlogin.html", food=foodTypes, message=message)
        # correct login
        else:
            # Create session for when customer is logged in
            session['loggedin'] = True
            session['id'] = str(data[0][0])
            session['username'] = username

            # return render_template("index2.html", food=foodTypes, message=message)
            return redirect(url_for("index2"))

    # else if using search bar to search
    elif request.method == "POST":
        input = ""
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"
        return redirect(url_for('results', srch=input))

    return render_template("customerlogin.html", food=foodTypes)


@app.route('/schedule')
def schedule():
    return render_template("schedule.html")

@app.route('/add-item-<restID>', methods=['GET', 'POST'])
def menu(restID):
    msg = ''

    #Gets the menu of of restaurant.
    cursor.execute("SELECT * from RestaurantMenuItem WHERE restaurantID = %s", restID)
    menu = cursor.fetchall()
    print(menu)
    if request.method == 'POST':

        if 'remove-item' in request.form:
            # get item id
            item = request.form['remove-item']
            print(item)
            # delete from session
            cursor.execute("DELETE from RestaurantMenuItem WHERE itemID = %s", item)
            conn.commit()
            return redirect(url_for('menu', restID=restID))

        # if 'name' in request.form and 'description' in request.form and 'price' in request.form:

        itemID = randomNumGenerator(7)
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        if len(name) == 0 or len(description) == 0 or len(price) ==0:
            msg = "All forms are required to add item."

            return render_template("menu.html", menu=menu, msg=msg)
        else:
            try:
                price = float(price)
            except ValueError:
                msg = "Please Enter A Valid Number"

                return render_template("menu.html", menu=menu, msg=msg)

            cursor.execute("INSERT INTO RestaurantMenuItem (itemID, restaurantID, itemName, itemDescription, itemPrice) VALUES (%s, %s, %s, %s, %s)",(itemID, restID, name, description, price))
            conn.commit()
            return redirect(url_for('menu', restID=restID))


    return render_template("menu.html", menu=menu, msg=msg, restID=restID)


@app.route('/restaurant-orders-<restID>', methods=['GET', 'POST'])
def restaurantOrders(restID):

    cursor.execute("SELECT restaurantName FROM Restaurant WHERE restaurantID = %s", restID)
    restaurantName = cursor.fetchall()

    cursor.execute("SELECT * FROM Orders WHERE restaurantID = %s", restID)
    orders = cursor.fetchall()
    print(orders)

    if 'remove-order' in request.form:
        # get order id
        orderID = request.form['remove-order']
        # delete from session
        cursor.execute("DELETE from Orders WHERE orderID = %s", orderID)
        conn.commit()
        return redirect(url_for('restaurantOrders', restID=restID))

    return render_template("restaurant-orders.html", restaurantName=restaurantName, orders=orders, restID=restID)


# takes a driver to their active orders page
@app.route('/<driver>-orders', methods=['GET', 'POST'])
def orders(driver):
    # get restaurant id and driver id
    cursor.execute(
        'SELECT restaurantID, driverID FROM DeliveryDriver WHERE driverUsername = %s',
        (driver))
    driverInfo = cursor.fetchall()
    restID = driverInfo[0][0]
    driverID = driverInfo[0][1]

    # get orders for driver
    cursor.execute("SELECT * FROM Orders WHERE restaurantID = %s AND Status = 'In Progress'", restID)
    orders = cursor.fetchall()
    cursor.execute("SELECT restaurantName FROM Restaurant WHERE restaurantID = %s", restID)
    restaurantName = cursor.fetchall()

    if request.method == 'POST':
        input = ""
        search = False
        # if accepting an order
        if 'order-id' in request.form:
            # update order status in database
            orderNumber = request.form['order-id']
            cursor.execute("UPDATE Orders SET Status = %s, driverAccount = %s WHERE orderId = %s", ('Delivered', driverID, orderNumber))
            conn.commit()
            return redirect(url_for('orders', driver=driver))

        # if using drop down or search bar
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
            search = True
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
            search = True
        if len(input) == 0:
            input = "all"
        if search:
            return redirect(url_for('results', srch=input))

    return render_template("orders.html", food=foodTypes, orders=orders, restaurantName=restaurantName)


@app.route('/driverlogin', methods=['GET', 'POST'])
def driverlogin():
    msg = ''
    # if trying to log in
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # validate username/password
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            'SELECT driverID, restaurantID FROM DeliveryDriver WHERE driverUsername = %s AND driverPassword = sha1(%s)',
            (username, password))
        data = cursor.fetchall()

        # if incorrect entry
        if len(data) != 1:
            msg = 'Username/Password incorrect'
            return render_template("driverlogin.html", food=foodTypes, message=msg)
        else:
            # create session for user login
            session['loggedin'] = True
            session['id'] = str(data[0][0])
            print(type(session['id']))
            session['username'] = username

            return redirect(url_for('orders', driver=username))
    # using search bar
    elif request.method == "POST":
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"

        return redirect(url_for('results', srch=input))

    return render_template("driverlogin.html", food=foodTypes, message=msg)


@app.route('/driver-register', methods=['GET', 'POST'])
def driverregister():
    message = ''
    if request.method == "POST" and 'full-name' in request.form and 'password' in request.form:
        # Creating variables for easy access
        full_name = request.form['full-name']
        sfsu_email = request.form['sfsu-email']
        username = request.form['username']
        phone_number = request.form['phone-number']
        password = request.form['password']
        password_verify = request.form['password-verify']
        restaurant = request.form['restaurants']

        # Check if driver account already exists
        cursor.execute('SELECT * FROM DeliveryDriver WHERE driverEmail = %s', (sfsu_email))
        data = cursor.fetchall()

        # If account does exist
        if data:
            message = 'Account already exists!'
            print("Account already exists!")
            return render_template("driver-register.html", food=foodTypes, data=allData, message=message)
        elif not re.match(r'[^@]+@([a-z]{3,15}\.)?sfsu\.edu$', sfsu_email):
            # Check if it is a valid sfsu email
            message = "Invalid email address"
            print("Invalid email address")
            return render_template("driver-register.html", food=foodTypes, data=allData, message=message)
        else:
            # Check to see if passwords match for confirmation
            if password_verify == password:
                driver_id = randomNumGenerator(6)
                cursor.execute('INSERT INTO DeliveryDriver VALUES(%s, %s, %s, %s, %s, sha1(%s), %s)',
                               (driver_id, full_name, sfsu_email, phone_number, username, password, restaurant))
                conn.commit()
                message = 'Successfully registered!'
                print("Delivery Driver successfully registered")
            else:
                message = "Passwords did not match"
                return render_template("driver-register.html", food=foodTypes, data=allData, message=message)

            return redirect(url_for("driverlogin"))

    elif request.method == "POST":
        input = ""
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"
        return redirect(url_for('results', srch=input))

    return render_template("driver-register.html", food=foodTypes, data=allData, message=message)


@app.route('/restaurant-register', methods=['GET', 'POST'])
def restaurantregister():
    message = ''
    if request.method == "POST" and 'full-name' in request.form and 'password' in request.form:
        # Create variables for easy access
        full_name = request.form['full-name']
        restaurant_name = request.form['sfsu-restaurant-name']
        # address = request.form['restaurant-address']
        sfsu_email = request.form['sfsu-email']
        phone_number = request.form['phone-number']
        username = request.form['username']
        password = request.form['password']
        password_verify = request.form['password-verify']

        # Check if the owner account already exists in the database
        cursor.execute('SELECT * FROM RestaurantOwner WHERE ownerEmail = %s', (sfsu_email))
        data = cursor.fetchall()
        regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        # Check if account with email address already exists
        if data:
            message = 'Account already exists!'
            print("Account already exists!")
            return render_template("restaurant-register.html", food=foodTypes, msg=message)
        elif not re.search(regex, sfsu_email):
            # Check if email is a valid sfsu email
            message = 'Invalid email address'
            print('Invalid email address')
            return render_template("restaurant-register.html", food=foodTypes, msg=message)
        else:
            # If account doesn't exist yet
            # Confirm password by checking verify_password and password
            if password == password_verify:
                owner_id = randomNumGenerator(7)
                restaurant_id = randomNumGenerator(7)
                cursor.execute('INSERT INTO RestaurantOwner VALUES(%s, %s, %s, %s, %s, sha1(%s), %s)',
                               (owner_id, full_name, sfsu_email, phone_number, username, password, restaurant_id))
                conn.commit()
                cursor.execute('INSERT INTO Restaurant VALUES(%s, %s, "", 0.000, 0.000, %s, "", "", "pending", "")',
                               (restaurant_id, restaurant_name, phone_number))
                conn.commit()
                print("Successfully registered")
            else:
                message = "Passwords did not match"
                # Go back to the restaurant register page
                return render_template("restaurant-register.html", food=foodTypes, msg=message)

            # After successful registration, redirect to home page
            return redirect(url_for("restaurantowners"))

    elif request.method == "POST":
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"

        return redirect(url_for('results', srch=input))
    return render_template("restaurant-register.html", food=foodTypes, msg=message)


@app.route('/restaurantowners', methods=['GET', 'POST'])
def restaurantowners():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:

        # Creating variables to access easily
        username = request.form['username']
        password = request.form['password']

        # Authenticating account in MySQL database
        cursor.execute('SELECT * FROM RestaurantOwner WHERE ownerUsername = %s AND ownerPassword = sha1(%s)',
                       (username, password))
        data = cursor.fetchall()

        # if entry is wrong
        if len(data) != 1:
            message = 'Username/Password incorrect'
            return render_template("restaurantowners.html", food=foodTypes, message=message)
        else:
            # Create session for when customer is logged in
            session['loggedin'] = True
            session['id'] = str(data[0][0])
            session['username'] = username

            return redirect(url_for("restaurantinfo", usr=username))

    elif request.method == "POST":
        # get user input and redirect to login page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"

        return redirect(url_for('results', srch=input))
    return render_template("restaurantowners.html", food=foodTypes, message=message)

@app.route('/restaurantinfo-<usr>', methods=['GET', 'POST'])
def restaurantinfo(usr):
    print(usr)
    cursor.execute("SELECT restaurantID, ownerPhoneNumber FROM RestaurantOwner WHERE ownerUsername = %s", usr)
    ownerInfo = cursor.fetchall()
    print(ownerInfo[0][0])
    cursor.execute("SELECT restaurantName, restaurantAddress, restaurantPhoneNumber, restaurantFoodType, restaurantPrice, restaurantApprovalStatus FROM Restaurant WHERE restaurantID = %s", ownerInfo[0][0])
    restInfo = cursor.fetchall()[0]
    print(restInfo)

    if request.method == "POST":

        name = request.form['rest-name']
        print("Name: ", name)
        street = request.form['street']
        print(street)
        city = request.form['city']
        print(city)
        zip = request.form['zip']
        print(zip)
        state = request.form['state']
        print(state)
        addr = street + ", " + city + ", " + state + " " + zip
        price = request.form['price']
        if len(price) > 3:
            price = "$"
        if price != "$" and price != "$$" and price != "$$$":
            price = "$"
        print(price)
        type = request.form['dropdown']
        print(type)

        cursor.execute("INSERT INTO Restaurant (restaurantID, restaurantName, restaurantAddress, latitude, longitude, restaurantPhoneNumber, restaurantFoodType, restaurantPrice, restaurantApprovalStatus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (ownerInfo[0][0], name, addr, 0.000, 0.000, ownerInfo[0][1], type, price, "pending"))
        conn.commit()


    return render_template("RestaurantInfo.html", food=foodTypes, restID=ownerInfo[0][0], restInfo=restInfo)

@app.route('/edit-restaurant-<restID>', methods=['GET', 'POST'])
def editRestaurant(restID):

    if request.method == "POST":

        name = request.form['rest-name']
        print("Name: ", name)
        street = request.form['street']
        print(street)
        city = request.form['city']
        print(city)
        zip = request.form['zip']
        print(zip)
        state = request.form['state']
        print(state)
        addr = street + ", " + city + ", " + state + " " + zip
        price = request.form['price']
        if len(price) > 3:
            price = "$"
        if price != "$" and price != "$$" and price != "$$$":
            price = "$"
        print(price)
        phone = request.form['phone']
        type = request.form['dropdown']
        print(type)

        cursor.execute("UPDATE Restaurant SET restaurantName = %s, restaurantAddress = %s, latitude = %s, longitude = %s, restaurantPhoneNumber = %s, restaurantFoodType = %s, restaurantPrice = %s, restaurantApprovalStatus = %s WHERE restaurantID = %s", (name, addr, 0.000, 0.000, phone, type, price, "Pending", restID))
        conn.commit()


    return render_template("edit-restaurant.html", food=foodTypes, restID=restID)

@app.route('/customer-register', methods=['GET', 'POST'])
def customerregister():
    message = ''
    if request.method == 'POST' and 'full-name' in request.form and 'password' in request.form:
        # Creating variables to access easily
        full_name = request.form['full-name']
        username = request.form['username']
        password = request.form['password']
        password_verify = request.form['password-verify']
        address = request.form['address']
        phone_number = request.form['phone-number']
        sfsu_email = request.form['sfsu-email']

        # Checking if username or email (account) already exists in MySQL DB
        cursor.execute('SELECT * FROM RegisteredCustomer WHERE customerEmail = %s or customerUsername = %s',
                       (sfsu_email, username))
        data = cursor.fetchall()

        if data:
            message = 'Account already exists!'
            print("Account already exists!")
            return render_template("customer-register.html", message=message)
        elif not re.match(r'[^@]+@([a-z]{3,15}\.)?sfsu\.edu$', sfsu_email):
            # Checking for valid sfsu.edu email
            message = 'Invalid email address'
            print("invalid email")
            return render_template("customer-register.html", message=message)
        else:
            # If account doesn't exist, insert new account to RegisteredCustomer table
            # Check to see if password and verify password matches
            if password == password_verify:
                customer_id = randomNumGenerator(5)
                cursor.execute(
                    'INSERT INTO RegisteredCustomer VALUES (%s, %s, %s, %s, %s, "", "", %s , sha1(%s))',
                    (customer_id, full_name, sfsu_email, phone_number, address, username, password))
                conn.commit()
                print("Successfully registered")
            else:
                message = "Passwords did not match"
                # Go back to the customer registration page
                return render_template("customer-register.html", message=message)
            # After registration, redirect to customer Login page
            return redirect(url_for("customerlogin"))

    elif request.method == "POST":
        # get user input and return to results page
        if 'food' in request.form:
            input = request.form['food']
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
        if len(input) == 0:
            input = "all"

        return redirect(url_for('results', srch=input))

    return render_template("customer-register.html", food=foodTypes, message=message)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    # clear tip and msg
    tip = 0
    msg = ""

    if request.method == "POST":
        input = ""
        search = False
        # if using drop down or search bar
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
            search = True
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
            search = True
        if len(input) == 0:
            input = "all"
        if search:
            return redirect(url_for('results', srch=input))

        # if logged in, grant acces to the below functionality
        if session.get('loggedin') == True:

            # if removing item
            if 'remove-item' in request.form:
                # get item id
                item = request.form['remove-item']
                # delete from session
                for i in session['cart']:
                    if i == item:
                        session['cart'].remove(item)

            # if adding a tip
            if 'options' in request.form:
                tip = float(request.form['options'])

            # if placing order
            if 'order' in request.form:
                if 'cart' not in session:
                    return redirect(url_for('cart'))

                # get all data for an order and commit to DB
                orderID = randomNumGenerator(6)

                cursor.execute('SELECT restaurantID FROM RestaurantMenuItem WHERE itemID = %s', session['cart'][0])
                restID = cursor.fetchall()[0][0]

                name = session['username']
                status = "In Progress"
                total = session['total']

                # cursor.execute('SELECT customerAddr1 FROM RegisteredCustomer WHERE customerUsername = %s', session['username'])
                # address = cursor.fetchall()[0][0]
                address = request.form['addr']
                print("ADDRESS SELECTED ", address)

                if 'reqs' in request.form:
                    reqs = request.form['reqs']
                else:
                    reqs = ""
                cursor.execute('INSERT INTO Orders (orderID, restaurantID, customerName, date, time, Status, priceTotal, destinationAddress, specialRequest, Items)VALUES (%s, %s, %s, CURDATE(), CURTIME(), %s, %s, %s, %s, %s)', (orderID, restID, name, status, total, address, reqs, session['items']))
                conn.commit()

                session.pop('cart', None)
                session.pop('items', None)
                msg = "Your order is confirmed!"
        # if not logged in, redirect to login page
        else:
            return redirect(url_for('customerlogin'))

    # create empty list to carry our items
    cartlist = []
    total = 0
    address = ""
    session['items'] = ""

    # if item in cart
    if 'cart' in session:
        # for every item, grab name and price
        for item in session['cart']:
            cursor.execute('SELECT itemName, itemPrice, itemID FROM RestaurantMenuItem WHERE itemID = %s', item)
            items = cursor.fetchall()
            # add item to list and add price to total
            cartlist.append(items[0])
            session['items'] = session['items'] + items[0][0] + ", "
            total += items[0][1]
        if len(session['id']) == 7:
            # get address of customer
            cursor.execute('SELECT restaurantID FROM RestaurantOwner WHERE ownerID = %s',
                           int(session['id']))
            restID = cursor.fetchall()[0][0]
            cursor.execute('SELECT restaurantAddress FROM Restaurant WHERE restaurantID = %s', restID)
            address = cursor.fetchall()[0][0]
            print(address)
        else:
            address = ""

    # calculate subtotal, tip, tax and total
    subtotal = total
    tip = round(tip * total, 2)
    # calculate tax (round to 2 decimal places) and add to total
    tax = round(total * 0.07, 2)
    total = round(total + tax + tip, 2)
    session['total'] = total

    return render_template('cart.html', food=foodTypes, items=cartlist, subtotal=subtotal, total=total, tax=tax, tip=tip, address=address, msg=msg)


# goes to a restaurant page
@app.route('/menu-<restaurant>', methods=['GET', 'POST'])
def restaurantPage(restaurant):
    # get all data associated with restaurant
    query = restaurantPageQuery(restaurant)
    cursor.execute(query)
    data = cursor.fetchall()
    # gets menu of restuarant
    cursor.execute("SELECT * from RestaurantMenuItem WHERE restaurantID = %s", data[0][0])
    menu = cursor.fetchall()
    # if using search bar or adding to cart
    if request.method == "POST":
        input = ''
        search = False
        # adding to cart
        if 'item-info' in request.form:
            if 'loggedin' in session and session['loggedin']:
                session.permanent = True
                # get item ID
                item = request.form['item-info']
                # append item to cart list
                if session.get('cart') is None:
                    cartItems = []
                else:
                    cartItems = session.get('cart')
                cartItems.append(item)
                # add item to cart
                session['cart'] = cartItems
            else:
                msg = "You need to be logged in to order from restaurants."
                return render_template('restaurantpage.html', data=data, food=foodTypes, menu=menu, msg=msg)

        # if using drop down or search bar
        # get user input and redirect to results page
        if 'food' in request.form:
            input = request.form['food']
            search = True
        if 'dropdown' in request.form and request.form['dropdown'] != 'Choose Cuisine':
            input = request.form['dropdown']
            search = True
        if len(input) == 0:
            input = "all"
        if search:
            return redirect(url_for('results', srch=input))
    # return complete restaurant page
    return render_template('restaurantpage.html', data=data, food=foodTypes, menu=menu)


@app.route('/patricia')
def patricia():
    return render_template("patricia.html")


@app.route('/erik')
def erik():
    return render_template("erik.html")


@app.route("/danny")
def danny():
    return render_template("danny.html")


@app.route("/saloni")
def saloni():
    return render_template("saloni.html")


@app.route("/affaan")
def affaan():
    return render_template("affaan.html")


@app.route("/edmund")
def edmund():
    return render_template("edmund.html")

@app.route("/about")
def about():
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("id", None)
    session.pop("cart", None)
    session['loggedin'] = False

    return redirect(url_for("index2"))


if __name__ == '__main__':
    app.run(debug=True)
