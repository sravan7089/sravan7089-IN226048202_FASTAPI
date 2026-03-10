from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# ================= DATA =================

products = [
    {'id':1,'name':'Wireless Mouse','price':499,'category':'Electronics','in_stock':True},
    {'id':2,'name':'Notebook','price':99,'category':'Stationery','in_stock':True},
    {'id':3,'name':'USB Hub','price':799,'category':'Electronics','in_stock':False},
    {'id':4,'name':'Pen Set','price':49,'category':'Stationery','in_stock':True},
]

orders = []
order_counter = 1
feedback_list = []

# ================= MODELS =================

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

# ================= HELPER FUNCTIONS =================

def find_product(product_id:int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None

def calculate_total(product, qty):
    return product["price"] * qty

# ================= BASIC ENDPOINTS =================

@app.get("/")
def home():
    return {"message":"Welcome to our E-commerce API"}

@app.get("/products")
def get_products():
    return {"products":products,"total":len(products)}

# ================= Q1 =================
# FILTER WITH min_price

@app.get("/products/filter")
def filter_products(
        category:str = Query(None),
        min_price:int = Query(None),
        max_price:int = Query(None),
        in_stock:bool = Query(None)
):
    result = products

    if category:
        result = [p for p in result if p["category"] == category]

    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"filtered_products":result,"count":len(result)}

# ================= Q2 =================
# PRICE ONLY ENDPOINT

@app.get("/products/{product_id}/price")
def get_product_price(product_id:int):

    product = find_product(product_id)

    if not product:
        return {"error":"Product not found"}

    return {
        "name":product["name"],
        "price":product["price"]
    }

# ================= Q3 =================
# CUSTOMER FEEDBACK

@app.post("/feedback")
def submit_feedback(data:CustomerFeedback):

    feedback_list.append(data.dict())

    return {
        "message":"Feedback submitted successfully",
        "feedback":data,
        "total_feedback":len(feedback_list)
    }

# ================= Q4 =================
# PRODUCT SUMMARY DASHBOARD

@app.get("/products/summary")
def product_summary():

    total_products = len(products)

    in_stock_count = len([p for p in products if p["in_stock"]])
    out_of_stock_count = total_products - in_stock_count

    cheapest = min(products, key=lambda x: x["price"])
    expensive = max(products, key=lambda x: x["price"])

    categories = list(set([p["category"] for p in products]))

    return {
        "total_products":total_products,
        "in_stock_count":in_stock_count,
        "out_of_stock_count":out_of_stock_count,
        "most_expensive":{
            "name":expensive["name"],
            "price":expensive["price"]
        },
        "cheapest":{
            "name":cheapest["name"],
            "price":cheapest["price"]
        },
        "categories":categories
    }

# ================= Q5 =================
# BULK ORDER

@app.post("/orders/bulk")
def bulk_order(data:BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in data.items:

        product = find_product(item.product_id)

        if not product:
            failed.append({
                "product_id":item.product_id,
                "reason":"Product not found"
            })
            continue

        if not product["in_stock"]:
            failed.append({
                "product_id":item.product_id,
                "reason":f"{product['name']} is out of stock"
            })
            continue

        subtotal = calculate_total(product,item.quantity)
        grand_total += subtotal

        confirmed.append({
            "product":product["name"],
            "qty":item.quantity,
            "subtotal":subtotal
        })

    return {
        "company":data.company_name,
        "confirmed":confirmed,
        "failed":failed,
        "grand_total":grand_total
    }

# ================= BONUS =================
# ORDER TRACKING

@app.post("/orders")
def place_order(order:OrderRequest):

    global order_counter

    product = find_product(order.product_id)

    if not product:
        return {"error":"Product not found"}

    total = calculate_total(product,order.quantity)

    new_order = {
        "order_id":order_counter,
        "customer_name":order.customer_name,
        "product":product["name"],
        "quantity":order.quantity,
        "total_price":total,
        "status":"pending"
    }

    orders.append(new_order)
    order_counter += 1

    return {"message":"Order placed","order":new_order}

@app.get("/orders/{order_id}")
def get_order(order_id:int):

    for order in orders:
        if order["order_id"] == order_id:
            return order

    return {"error":"Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id:int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message":"Order confirmed","order":order}

    return {"error":"Order not found"}
