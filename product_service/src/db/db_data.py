import uuid
from random import randint

TABLES_DATA = {"Products": [], "Stocks": []}

products = [
    {"title": "The Last of Us Part II", "description": "Action-adventure game by Naughty Dog", "price": 49.99},
    {"title": "God of War", "description": "Action-adventure game by Santa Monica Studio", "price": 39.99},
    {"title": "Red Dead Redemption 2", "description": "Open-world game by Rockstar Games", "price": 59.99},
    {"title": "Spider-Man (PS4)", "description": "Action-adventure game by Insomniac Games", "price": 29.99},
    {"title": "The Witcher 3: Wild Hunt", "description": "Action role-playing game by CD Projekt", "price": 39.99},
    {"title": "Final Fantasy VII Remake", "description": "Role-playing game by Square Enix", "price": 49.99},
]


for product in products:
    product_id = uuid.uuid4().hex

    product_item = {
        "PutRequest": {
            "Item": {
                "id": {"S": product_id},
                "title": {"S": product["title"]},
                "description": {"S": product["description"]},
                "price": {"N": str(product["price"])},
            }
        }
    }

    stock_item = {
        "PutRequest": {
            "Item": {
                "product_id": {"S": product_id},
                "count": {"N": f"{randint(1, 10)}"},
            }
        }
    }

    TABLES_DATA["Products"].append(product_item)
    TABLES_DATA["Stocks"].append(stock_item)
