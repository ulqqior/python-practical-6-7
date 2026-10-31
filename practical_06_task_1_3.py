"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 1.3: Робота з Cookies та Sessions для збереження стану клієнта.
"""

from flask import Flask, request, make_response, session, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = "super-secret-key-for-session-signing-kubg-2026"

# Тимчасова база товарів
products_db = {
    1: {"name": "Ноутбук", "price": 25000.0},
    2: {"name": "Смартфон", "price": 12000.0},
    3: {"name": "Навушники", "price": 2000.0},
    4: {"name": "Клавіатура", "price": 1500.0},
}

# ==========================================
# 1. Робота з Cookies (зберігаються на клієнті)
# ==========================================

@app.route("/set-theme/<theme>")
def set_theme(theme):
    """Встановити тему оформлення через безпечний Cookie."""
    if theme not in ["light", "dark", "system"]:
        return jsonify({"error": "Непідтримувана тема. Доступні: light, dark, system"}), 400

    resp = make_response(jsonify({
        "message": f"Тему успішно оновлено на '{theme}'",
        "theme": theme
    }))
    # Встановлюємо cookie з max_age (30 днів), httponly (захист від XSS) та samesite (захист від CSRF)
    resp.set_cookie(
        key="theme",
        value=theme,
        max_age=30 * 24 * 3600,
        httponly=True,
        samesite="Lax"
    )
    return resp

@app.route("/get-theme")
def get_theme():
    """Прочитати тему оформлення з Cookie запиту."""
    theme = request.cookies.get("theme", default="light")
    return jsonify({
        "theme": theme,
        "source": "client_cookie"
    })

@app.route("/set-language/<lang>")
def set_language(lang):
    """Встановити мову інтерфейсу через Cookie."""
    resp = make_response(jsonify({
        "message": f"Мову інтерфейсу збережено: '{lang}'",
        "language": lang
    }))
    resp.set_cookie(key="language", value=lang, max_age=365 * 24 * 3600, httponly=True, samesite="Lax")
    return resp

@app.route("/preferences")
def preferences():
    """Показати всі збережені уподобання користувача з Cookies."""
    return jsonify({
        "theme": request.cookies.get("theme", "light"),
        "language": request.cookies.get("language", "uk"),
        "all_cookies": dict(request.cookies)
    })

# ==========================================
# 2. Робота з Sessions (стан зберігається на сервері)
# ==========================================

@app.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    """Додати товар до сесійного кошика."""
    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": "Товар з таким ID не існує"}), 404

    if "cart" not in session:
        session["cart"] = []

    # Додаємо ID товару
    cart = session["cart"]
    cart.append(product_id)
    session["cart"] = cart  # Явне оновлення об'єкта для прапорця модифікації сесії

    return jsonify({
        "message": f"Товар '{product['name']}' додано до кошика",
        "cart_count": len(session["cart"])
    })

@app.route("/cart")
def view_cart():
    """Переглянути вміст сесійного кошика з розрахунком суми."""
    cart_ids = session.get("cart", [])
    cart_items = []
    total_amount = 0.0

    for pid in cart_ids:
        if pid in products_db:
            item = products_db[pid]
            cart_items.append({"id": pid, **item})
            total_amount += item["price"]

    return jsonify({
        "items_count": len(cart_items),
        "total_amount": total_amount,
        "items": cart_items
    })

@app.route("/cart/clear")
def clear_cart():
    """Очистити вміст кошика в поточній сесії."""
    session.pop("cart", None)
    return jsonify({"message": "Кошик успішно очищено"})

@app.route("/login", methods=["GET", "POST"])
def login():
    """Імітація авторизації — збереження облікового запису в сесії."""
    if request.method == "POST":
        # Підтримуємо і JSON, і звичайні веб-форми
        username = request.form.get("username")
        if not username and request.is_json:
            username = request.get_json().get("username")

        if not username:
            return jsonify({"error": "Поле username обов'язкове"}), 400

        session["username"] = username.strip()
        return jsonify({
            "message": f"Користувач '{session['username']}' успішно увійшов у систему",
            "status": "authenticated"
        })

    return """
    <form method="POST">
        <h3>Авторизація</h3>
        <label>Ім'я користувача:</label>
        <input type="text" name="username" required>
        <button type="submit">Увійти</button>
    </form>
    """

@app.route("/logout")
def logout():
    """Вихід із системи — інвалідація даних сесії."""
    user = session.pop("username", None)
    return jsonify({
        "message": f"Користувач '{user}' успішно вийшов із системи" if user else "Ви не були авторизовані"
    })

@app.route("/profile")
def profile():
    """Особистий кабінет — захищений маршрут на базі session."""
    username = session.get("username")
    if not username:
        return jsonify({
            "error": "Неавторизований доступ. Будь ласка, виконайте вхід через /login",
            "authenticated": False
        }), 401

    cart_count = len(session.get("cart", []))
    return jsonify({
        "username": username,
        "authenticated": True,
        "cart_items_count": cart_count,
        "preferences": {
            "theme": request.cookies.get("theme", "light"),
            "language": request.cookies.get("language", "uk")
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5002)
