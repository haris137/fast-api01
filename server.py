from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv('.env')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('FRONTEND_URL')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class Order(BaseModel):
    firstName: str
    lastName: str
    address: str
    city: str
    whatsappNumber: str
    email: str
    cart: list
    total: float

class Feedback(BaseModel):
    name: str
    phone: str
    feedback: str

# Initialize MongoDB connection from environment variables
client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('DB_NAME')]
orderCollection = db[os.getenv('COLLECTION_NAME')]
feedbackCollection = db[os.getenv('COLLECTION_NAME02')]

# Setup for sending email
app_pass =  os.getenv('APP_PASSWORD')
sender = os.getenv('SENDER_GMAIL')
owner = os.getenv('OWNER_GMAIL')


@app.get("/")
async def root():
    return {
        "message": "Welcome to the API",
        "config": {
            "frontend_url": os.getenv('FRONTEND_URL'),
            "mongodb_url": os.getenv('MONGODB_URL'),
            "database": os.getenv('DB_NAME'),
            "collection": os.getenv('COLLECTION_NAME'),
            "collection02": os.getenv('COLLECTION_NAME02'),
            "sender": os.getenv('SENDER_GMAIL'),
            "reciever": os.getenv('RECIEVER_GMAIL'),
            "app_pass": os.getenv('APP_PASSWORD')
        }
}

@app.get("/showOrders")
async def read_orders():
    orders = []
    async for order in orderCollection.find({}):
        order["_id"] = str(order["_id"])
        orders.append(order)
    return orders

@app.get("/showFeedbacks")
async def read_feedbacks():
    feedbacks = []
    async for feedback in feedbackCollection.find({}):
        feedback["_id"] = str(feedback["_id"])
        feedbacks.append(feedback)
    return feedbacks

@app.post("/order/")
async def  create_order(order: Order):
    # To customer 
    msg = MIMEMultipart()
    msg['from'] = sender
    msg['subject'] = "Order Confirmation"

    result = await orderCollection.insert_one(order.model_dump())
    
    name = order.lastName
    reciever_mail = order.email

    customerBody = f"Hello, {name} 👋 \n\nYour order has been placed successfully 🎉.\n\nOur team will contact you within 24 hours 🛃\n\nThanks,\nKohinoor Toppings"
    msg.attach(MIMEText(customerBody, 'plain'))
    
    if result.inserted_id:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, app_pass)
            server.sendmail(sender, reciever_mail, msg.as_string())
            print("Email sent successfully")
            
        return {"message" : "Order created successfully"}
    raise HTTPException(status_code=500, detail= "Failed to add data")

@app.post("/feedback/")
async def  create_feedback(feedback: Feedback):
    # To owner 
    msg02 = MIMEMultipart()
    msg02['from'] = sender
    msg02['to'] = owner
    msg02['subject'] = "New Order"

    result = await feedbackCollection.insert_one(feedback.model_dump())
        
    OwnerBody = f"Hey👋,\n\nNew order has been placed.\n\nGo and confirm it quickly.\n\nThanks,\nKohinoor Toppings"
    msg02.attach(MIMEText(OwnerBody, 'plain'))
    
    if result.inserted_id:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, app_pass)
            server.sendmail(sender, owner, msg02.as_string())
            print("Email sent successfully")
            
        return {"message" : "Order notification sent successfully"}
    raise HTTPException(status_code=500, detail= "Failed to add data")
