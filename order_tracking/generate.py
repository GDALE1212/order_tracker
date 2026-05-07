from main import app, db
from faker import Faker
from random import choice, randint
import random
from datetime import datetime, timedelta
from main import db, User, BuyerInfo, Order, DelicacyType, ContainerSize, OrderStatus

fake = Faker()

# Function to generate fake buyers
def generate_fake_buyers():
    for _ in range(1000): 
        name = fake.name()
        contact_number = f"09{randint(100000000, 999999999)}"  # Generate a realistic 11-digit contact number
        address = fake.address()
        buyer = BuyerInfo(name=name, contact_number=contact_number, address=address)
        db.session.add(buyer)
    db.session.commit()

# Function to generate fake orders
def generate_fake_orders():
    buyers = BuyerInfo.query.all()
    for buyer in buyers:
        for _ in range(random.randint(1, 5)):  
            user_id = 1 
            delicacy = random.choice(list(DelicacyType))
            quantity = random.randint(1, 10)
            container = random.choice(list(ContainerSize))
            # Make special requests more food-related and realistic
            special_request = random.choice([
                "Add extra cheese.",
                "Please include extra sauce.",
                "Less sugar, please.",
                "Include extra toppings.",
                "Keep the food warm during delivery",
                "Make sure the food is freshly made"
            ])
            pickup_place = fake.city()
            pickup_date = fake.date_this_year()
            status = random.choice(list(OrderStatus))

            order = Order(
                user_id=user_id,
                buyer_id=buyer.id,
                delicacy=delicacy,
                quantity=quantity,
                container_size=container,
                special_request=special_request,
                pickup_place=pickup_place,
                pickup_date=pickup_date,
                status=status,
            )
            db.session.add(order)
    db.session.commit()

# Main function to generate fake data
def generate_fake_data():
    with app.app_context():  
        generate_fake_buyers()
        generate_fake_orders()

if __name__ == '__main__':
    generate_fake_data()
    print("Fake data generation completed!")
