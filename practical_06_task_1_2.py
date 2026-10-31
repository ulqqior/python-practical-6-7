"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 1.2: Контролери/views для обробки запитів з валідацією, фільтрацією та сортуванням.
"""

from flask import Flask, request, jsonify, abort
from functools import wraps

app = Flask(__name__)

def validate_json(required_fields):
    """Декоратор для валідації JSON-запитів."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"error": "Очікується JSON-тіло запиту (Content-Type: application/json)"}), 400
            
            missing = [field for field in required_fields if field not in data]
            if missing:
                return jsonify({
                    "error": f"Відсутні обов'язкові поля: {', '.join(missing)}"
                }), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Тимчасова "база даних"
items_db = {
    1: {"id": 1, "name": "Ноутбук", "price": 25000.0, "category": "електроніка"},
    2: {"id": 2, "name": "Книга Python", "price": 500.0, "category": "книги"},
    3: {"id": 3, "name": "Навушники", "price": 2000.0, "category": "електроніка"},
    4: {"id": 4, "name": "Мишка оптична", "price": 750.0, "category": "електроніка"},
}
next_id = 5

# --- View-функції ---

@app.route("/api/items", methods=["GET"])
def get_items():
    """GET /api/items — список елементів з фільтрацією та сортуванням."""
    category = request.args.get("category")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_field = request.args.get("sort", default="id")
    order = request.args.get("order", default="asc").lower()

    items = list(items_db.values())

    # 1. Фільтрація за категорією
    if category:
        items = [i for i in items if i["category"].lower() == category.lower()]

    # 2. Фільтрація за ціною
    if min_price is not None:
        items = [i for i in items if i["price"] >= min_price]
    if max_price is not None:
        items = [i for i in items if i["price"] <= max_price]

    # 3. Сортування
    if sort_field in ["id", "name", "price", "category"]:
        reverse = (order == "desc")
        items.sort(key=lambda x: x[sort_field], reverse=reverse)

    return jsonify({
        "total": len(items),
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort_field,
            "order": order
        },
        "items": items
    }), 200

@app.route("/api/items", methods=["POST"])
@validate_json(["name", "price", "category"])
def create_item():
    """POST /api/items — створити новий товар з валідацією."""
    global next_id
    data = request.get_json()

    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    try:
        price = float(data.get("price", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Поле price має бути числовим значенням"}), 400

    if not name:
        return jsonify({"error": "Назва товару (name) не може бути порожньою"}), 400
    if price <= 0:
        return jsonify({"error": "Ціна товару (price) має бути строго більшою за 0"}), 400

    new_item = {
        "id": next_id,
        "name": name,
        "price": price,
        "category": category
    }
    items_db[next_id] = new_item
    next_id += 1

    return jsonify(new_item), 201

@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """GET /api/items/:id — отримати деталі одного товару."""
    item = items_db.get(item_id)
    if not item:
        abort(404)
    return jsonify(item), 200

@app.route("/api/items/<int:item_id>", methods=["PUT"])
@validate_json(["name", "price", "category"])
def update_item(item_id):
    """PUT /api/items/:id — повне оновлення товару."""
    if item_id not in items_db:
        abort(404)

    data = request.get_json()
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    try:
        price = float(data.get("price", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Поле price має бути числовим"}), 400

    if not name or price <= 0:
        return jsonify({"error": "Некоректні параметри: name має бути непорожнім, price > 0"}), 400

    items_db[item_id] = {
        "id": item_id,
        "name": name,
        "price": price,
        "category": category
    }
    return jsonify(items_db[item_id]), 200

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """DELETE /api/items/:id — видалення товару."""
    if item_id not in items_db:
        abort(404)

    del items_db[item_id]
    # За стандартами REST статус 204 повертається без тіла відповіді
    return "", 204

# --- Обробка помилок ---

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Ресурс не знайдено", "status": 404}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Некоректний запит", "status": 400}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5001)
