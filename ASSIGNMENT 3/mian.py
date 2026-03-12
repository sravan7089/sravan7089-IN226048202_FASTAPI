from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# ------------------ PYDANTIC MODELS ------------------

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

# ------------------ DATA ------------------

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
]

# ------------------ HELPER ------------------

def find_product(product_id: int):
    for p in products:
        if p['id'] == product_id:
            return p
    return None

# ------------------ HOME ------------------

@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API"}

# ------------------ GET ALL PRODUCTS ------------------

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

# ------------------ ADD PRODUCT ------------------

@app.post("/products")
def add_product(new_product: NewProduct, response: Response):

    for p in products:
        if p["name"].lower() == new_product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Product with this name already exists"}

    next_id = max(p["id"] for p in products) + 1

    product = {
        "id": next_id,
        "name": new_product.name,
        "price": new_product.price,
        "category": new_product.category,
        "in_stock": new_product.in_stock
    }

    products.append(product)

    response.status_code = status.HTTP_201_CREATED
    return {"message": "Product added", "product": product}

# ------------------ UPDATE PRODUCT ------------------



# ------------------ AUDIT ENDPOINT ------------------

@app.get("/products/audit")
def audit_products():

    total_products = len(products)

    in_stock_products = [p for p in products if p["in_stock"]]
    in_stock_count = len(in_stock_products)

    out_of_stock_names = [p["name"] for p in products if not p["in_stock"]]

    total_stock_value = sum(p["price"] * 10 for p in in_stock_products)

    most_expensive = max(products, key=lambda x: x["price"])

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_names": out_of_stock_names,
        "total_stock_value": total_stock_value,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        }
    }

# ------------------ DISCOUNT ------------------

@app.put("/products/discount")
def apply_discount(category: str = Query(...),
                   discount_percent: int = Query(..., ge=1, le=99)):

    updated = []

    for p in products:
        if p["category"].lower() == category.lower():

            new_price = int(p["price"] * (1 - discount_percent / 100))
            p["price"] = new_price

            updated.append({
                "name": p["name"],
                "new_price": new_price
            })

    if not updated:
        return {"message": "No products found in this category"}

    return {
        "updated_count": len(updated),
        "products": updated
    }




@app.put("/products/{product_id}")
def update_product(product_id: int,
                   response: Response,
                   in_stock: bool = Query(None),
                   price: int = Query(None)):

    product = find_product(product_id)

    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}

    if in_stock is not None:
        product["in_stock"] = in_stock

    if price is not None:
        product["price"] = price

    return {"message": "Product updated", "product": product}

# ------------------ DELETE PRODUCT ------------------

@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):

    product = find_product(product_id)

    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}

    products.remove(product)

    return {"message": f"Product '{product['name']}' deleted"}

# ------------------ GET SINGLE PRODUCT ------------------

@app.get("/products/{product_id}")
def get_product(product_id: int):

    product = find_product(product_id)

    if not product:
        return {"error": "Product not found"}

    return {"product": product}
