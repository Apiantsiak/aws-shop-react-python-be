import typing as tp
from random import randint


PRODUCTS: list[dict[str, tp.Union[str, int]]] = [
    {
        "id": num,
        "title": f"product_{num}",
        "description": f"description for product_{num}",
        "price": randint(100, 1000),
    } for num in range(1, 11)
]
