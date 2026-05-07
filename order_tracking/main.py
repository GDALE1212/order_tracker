from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
import time
import sys
import tracemalloc
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)

# Set configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

app.permanent_session_lifetime = timedelta(minutes=30)  


# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Enum classes for order status, delicacies, and container sizes
class DelicacyType(PyEnum):
    SINUKMANI = "SINUKMANI"
    SAPIN_SAPIN = "SAPIN_SAPIN"
    PUTO = "PUTO"
    PUTO_ALSA = "PUTO_ALSA"
    KUTSINTA = "KUTSINTA"
    PUTO_KUTSINTA = "PUTO_KUTSINTA"
    MAJA = "MAJA"
    PICHI_PICHI = "PICHI_PICHI"
    PALITAW = "PALITAW"
    KARIOKA = "KARIOKA"
    SUMAN_MALAGKIT = "SUMAN_MALAGKIT"
    SUMAN_CASSAVA = "SUMAN_CASSAVA"
    SUMAN_LIHIA = "SUMAN_LIHIA"

class ContainerSize(PyEnum):
    BILAO_10 = "BILAO_10"
    BILAO_12 = "BILAO_12"
    BILAO_14 = "BILAO_14"
    BILAO_16 = "BILAO_16"
    BILAO_18 = "BILAO_18"
    TAB = "TAB"
    SLICE = "SLICE"

class OrderStatus(PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REMOVED = "REMOVED"

# User table definition
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    orders = relationship("Order", back_populates="user")

# Buyer information table
class BuyerInfo(db.Model):
    __tablename__ = 'buyer_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    orders = relationship("Order", back_populates="buyer")

# Orders table definition
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    buyer_id = db.Column(db.Integer, ForeignKey('buyer_info.id'), nullable=False)
    delicacy = db.Column(db.Enum(DelicacyType), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    container_size = db.Column(db.Enum(ContainerSize), nullable=False)
    special_request = db.Column(db.String(255))
    pickup_place = db.Column(db.String(255), nullable=False)
    pickup_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    user = relationship("User", back_populates="orders")
    buyer = relationship("BuyerInfo", back_populates="orders")


# Create tables before the first request
@app.before_request
def create_tables():
    db.create_all()
    # Check if a user exists, create one if not
    if not User.query.first():
        default_user = User(
            username="admin",
            password=bcrypt.generate_password_hash("password").decode('utf-8')
        )
        db.session.add(default_user)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']

        # Retrieve the first (and only) user from the database
        user = User.query.first()

        if user and bcrypt.check_password_hash(user.password, password) and user.username == username:
        
            return redirect(url_for('order_management'))  
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/order_form', methods=['GET', 'POST'])
def order_form():
    if request.method == 'POST':
        data = request.json  

    # Extract and validate data
    try:
        customer_name = data.get('customerName')
        contact_number = data.get('contactNumber')
        address = data.get('address')
        pickup_place = data.get('pickupPlace')
        pickup_date_str = data.get('pickupDate')
        delicacy = data.get('delicacy')
        quantity = int(data.get('quantity', 1))
        container = data.get('container')
        special_request = data.get('specialRequest', '')

        if not (customer_name and contact_number and address and pickup_place and pickup_date_str and delicacy and quantity and container):
            return jsonify({"success": False, "message": "All fields are required."}), 400

        # Parse pickup date
        pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d').date()
        if pickup_date < datetime.now().date():
            return jsonify({"success": False, "message": "Pickup date cannot be in the past."}), 400

    except Exception as e:
        return jsonify({"success": False, "message": "Invalid input data. Please check your entries."}), 400

    # Retrieve or create buyer
    buyer = BuyerInfo.query.filter_by(
        name=customer_name,
        contact_number=contact_number,
        address=address
    ).first()

    if not buyer:
        buyer = BuyerInfo(
            name=customer_name,
            contact_number=contact_number,
            address=address
        )
        db.session.add(buyer)
        db.session.commit()

    # Sanitize and validate Enum values
    try:
        delicacy_enum = DelicacyType[delicacy.upper().replace("-", "_")]
        container_enum = ContainerSize[container.upper().replace("-", "_")]
    except KeyError:
        return jsonify({"success": False, "message": "Invalid delicacy or container type."}), 400

    # Create a new order
    try:
        user_id = User.query.first().id  
        new_order = Order(
            user_id=user_id,
            buyer_id=buyer.id,
            delicacy=delicacy_enum,
            quantity=quantity,
            container_size=container_enum,
            special_request=special_request,
            pickup_place=pickup_place,
            pickup_date=pickup_date,
            status=OrderStatus.PENDING,
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"success": True, "message": "Order created successfully!"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"success": False, "message": "Failed to save the order. Please try again."}), 500



# Comb Sort implementation with reverse flag
def comb_sort(orders, key_func, reverse=False):
    gap = len(orders)
    shrink_factor = 1.3
    swapped = True

    while gap > 1 or swapped:
        gap = int(gap / shrink_factor)
        if gap < 1:
            gap = 1

        swapped = False
        for i in range(len(orders) - gap):
            if (key_func(orders[i]) > key_func(orders[i + gap])) if not reverse else (key_func(orders[i]) < key_func(orders[i + gap])):
                orders[i], orders[i + gap] = orders[i + gap], orders[i]
                swapped = True

    return orders

# Quick Sort implementation
def quick_sort(orders, key_func, reverse=False):
    if len(orders) <= 1:
        return orders
    pivot = key_func(orders[len(orders) // 2])
    left = [x for x in orders if key_func(x) < pivot] if not reverse else [x for x in orders if key_func(x) > pivot]
    middle = [x for x in orders if key_func(x) == pivot]
    right = [x for x in orders if key_func(x) > pivot] if not reverse else [x for x in orders if key_func(x) < pivot]
    return quick_sort(left, key_func, reverse) + middle + quick_sort(right, key_func, reverse)

# Cycle Sort implementation
def cycle_sort(orders, key_func, reverse=False):
    n = len(orders)
    for cycle_start in range(n - 1):
        item = orders[cycle_start]
        pos = cycle_start
        for i in range(cycle_start + 1, n):
            if (key_func(orders[i]) < key_func(item)) if not reverse else (key_func(orders[i]) > key_func(item)):
                pos += 1
        if pos == cycle_start:
            continue
        while key_func(orders[pos]) == key_func(item):
            pos += 1
        orders[pos], item = item, orders[pos]
        while pos != cycle_start:
            pos = cycle_start
            for i in range(cycle_start + 1, n):
                if (key_func(orders[i]) < key_func(item)) if not reverse else (key_func(orders[i]) > key_func(item)):
                    pos += 1
            while key_func(orders[pos]) == key_func(item):
                pos += 1
            orders[pos], item = item, orders[pos]
    return orders

def estimate_memory(obj, seen_ids=None):
    """Recursively estimate memory size of an object."""
    if seen_ids is None:
        seen_ids = set()

    obj_id = id(obj)
    if obj_id in seen_ids:  
        return 0
    seen_ids.add(obj_id)

    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(estimate_memory(k, seen_ids) + estimate_memory(v, seen_ids) for k, v in obj.items())
    elif hasattr(obj, '__dict__'):
        size += estimate_memory(vars(obj), seen_ids)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum(estimate_memory(i, seen_ids) for i in obj)

    return size

@app.route('/order_management')
def order_management():
    sort_by = request.args.get('sort_by', default='pickup_date', type=str)
    data_count = request.args.get('data_count', default=50, type=int)
    sort_algo = request.args.get('sort_algo', default='comb_sort', type=str)  # New parameter for algorithm choice

    valid_sort_fields = ['pickup_date', 'delicacy', 'status']
    if sort_by not in valid_sort_fields:
        return "Invalid sort option!", 400

    # Fetch orders excluding REMOVED status
    orders = Order.query.filter(Order.status != OrderStatus.REMOVED).limit(data_count).all()
    
    # Select sorting algorithm
    sort_func = {
        'comb_sort': comb_sort,
        'quick_sort': quick_sort,
        'cycle_sort': cycle_sort
    }.get(sort_algo, comb_sort)  # Default to comb_sort if invalid algorithm

    # Start tracking memory
    tracemalloc.start()
    start_memory = tracemalloc.get_traced_memory()[0]
    start_time = time.perf_counter()

    # Sort orders
    key_func = {
        'pickup_date': lambda order: order.pickup_date,
        'delicacy': lambda order: order.delicacy.name.lower() if order.delicacy else "",
        'status': lambda order: order.status.name if order.status else ""
    }.get(sort_by)
    orders = sort_func(orders, key_func)

    end_time = time.perf_counter()
    end_memory = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    execution_time_ns = (end_time - start_time) * 1e9
    memory_used_kb = (end_memory - start_memory) / 1024
    start_memory_kb = start_memory / 1024
    end_memory_kb = end_memory / 1024

    return render_template(
        'order_management.html',
        orders=orders,
        execution_time=f"{execution_time_ns:.0f} nanoseconds",
        memory_used=f"{memory_used_kb:.2f} KB",
        start_memory=f"{start_memory_kb:.2f} KB",
        end_memory=f"{end_memory_kb:.2f} KB",
        sort_algo=sort_algo
    )
    
@app.route('/remove_order/<int:order_id>', methods=['POST'])
def remove_order(order_id):
    order = Order.query.get_or_404(order_id)
   
    # Mark the order as removed but don't delete it
    order.status = OrderStatus.REMOVED
    db.session.commit()

    return jsonify({"success": True})  


@app.route('/update_order/<int:orderId>', methods=['POST'])
def update_order(orderId):
    data = request.json  
    order = Order.query.get(orderId)  

    if order:
        try:
            # Convert the pickup_date string into a datetime.date object
            pickup_date_str = data.get('pickup_date')
            if pickup_date_str:
                pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d').date()  
            else:
                pickup_date = None 

            # Update each field with the received data
            order.buyer.name = data.get('customer_name', order.buyer.name)
            order.buyer.contact_number = data.get('contact_number', order.buyer.contact_number)
            order.buyer.address = data.get('address', order.buyer.address)
            order.pickup_place = data.get('pickup_place', order.pickup_place)
            order.pickup_date = pickup_date 
            order.quantity = data.get('quantity', order.quantity)
            order.container_size = data.get('container', order.container_size)
            order.special_request = data.get('special_request', order.special_request)
            order.status = data.get('status', order.status)

            # Handle delicacy and status with validation using Enum
            try:
                if data.get('delicacy'):
                    order.delicacy = DelicacyType[data.get('delicacy').upper()]  
                if data.get('status'):
                    order.status = OrderStatus[data.get('status').upper()]  
            except KeyError as e:
                return jsonify(success=False, message=f"Invalid value for {e}")

            # Commit changes to the database
            db.session.commit()

            return jsonify(success=True, order=data)
        except Exception as e:
            print(f"Error while updating order: {e}")
            return jsonify(success=False, message="An error occurred while updating the order")
    else:
        return jsonify(success=False, message="Order not found")

# Permanent delete the order
@app.route('/delete_order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order) 
    db.session.commit()
    return '', 204  

@app.route('/order_history')
def order_history():
    
    orders = Order.query.all()  

    print(f"Orders fetched for history: {len(orders)} orders found.")
    for order in orders:
        print(f"Order ID: {order.id}, Status: {order.status.name}")

    return render_template('order_history.html', orders=orders)



if __name__ == '__main__':
    app.run(debug=True)