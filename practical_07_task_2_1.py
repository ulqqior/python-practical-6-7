"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 2.1: CRUD: операції Create та Read для блогу через веб-інтерфейс.
"""

from flask import Flask, request, render_template_string, redirect, url_for, flash, abort
from datetime import datetime

app = Flask(__name__)
app.secret_key = "blog-secret-key-security-kubg-2026"

# HTML-шаблони
LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Блог — Публікації</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 8px; }
        .flash { background: #dcfce7; border-left: 4px solid #22c55e; color: #15803d; padding: 10px 14px; margin-bottom: 18px; border-radius: 4px; }
        .btn-new { display: inline-block; background: #0284c7; color: white; padding: 8px 14px; text-decoration: none; border-radius: 4px; font-weight: bold; }
        .btn-new:hover { background: #0369a1; }
        article { border-bottom: 1px solid #e2e8f0; padding: 16px 0; }
        article h2 { margin: 0 0 8px; }
        article h2 a { color: #0284c7; text-decoration: none; }
        article h2 a:hover { text-decoration: underline; }
        .meta { color: #64748b; font-size: 0.85em; }
        .pagination { margin-top: 20px; }
        .pagination a, .pagination strong { margin-right: 8px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Блог новин та публікацій</h1>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                    <div class="flash">✓ {{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div style="margin-bottom: 15px;">
            <a href="{{ url_for('post_create') }}" class="btn-new">+ Нова публікація</a>
        </div>

        {% for post in posts %}
        <article>
            <h2><a href="{{ url_for('post_detail', post_id=post.id) }}">{{ post.title }}</a></h2>
            <p>{{ post.content[:140] }}{% if post.content|length > 140 %}...{% endif %}</p>
            <div class="meta">
                👤 Автор: <strong>{{ post.author }}</strong> | 📅 Створено: {{ post.created_at }}
            </div>
        </article>
        {% else %}
        <p>Публікацій поки немає. Створіть першу!</p>
        {% endfor %}

        {% if total_pages > 1 %}
        <div class="pagination">
            <span>Сторінка: </span>
            {% for p in range(1, total_pages + 1) %}
                {% if p == current_page %}
                    <strong>[{{ p }}]</strong>
                {% else %}
                    <a href="{{ url_for('post_list', page=p) }}">{{ p }}</a>
                {% endif %}
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>{{ post.title }} | Блог</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { color: #0f172a; margin-top: 0; }
        .meta { background: #f1f5f9; padding: 10px 14px; border-radius: 6px; color: #475569; font-size: 0.9em; margin-bottom: 20px; }
        .content { font-size: 1.1em; line-height: 1.7; white-space: pre-wrap; }
        .back-link { display: inline-block; margin-top: 25px; color: #0284c7; text-decoration: none; font-weight: bold; }
        .flash { background: #dcfce7; border-left: 4px solid #22c55e; color: #15803d; padding: 10px 14px; margin-bottom: 18px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                    <div class="flash">✓ {{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <h1>{{ post.title }}</h1>
        <div class="meta">
            👤 Автор: <strong>{{ post.author }}</strong> | 📅 Дата: {{ post.created_at }} | ID: #{{ post.id }}
        </div>
        <div class="content">{{ post.content }}</div>
        <hr>
        <a href="{{ url_for('post_list') }}" class="back-link">&larr; Повернутися до списку публікацій</a>
    </div>
</body>
</html>
"""

FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 650px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 8px; }
        label { font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; }
        input[type=text], textarea { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 1em; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-size: 1em; cursor: pointer; margin-top: 20px; }
        button:hover { background: #0369a1; }
        .cancel-btn { margin-left: 12px; color: #64748b; text-decoration: none; }
        .error { color: #dc2626; font-size: 0.9em; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ form_title }}</h1>
        {% if error %}<div style="color:red; margin-bottom: 12px;">{{ error }}</div>{% endif %}
        <form method="POST">
            <label>Заголовок публікації:</label>
            <input type="text" name="title" value="{{ post.title if post else '' }}" required placeholder="Введіть інформативний заголовок">

            <label>Автор:</label>
            <input type="text" name="author" value="{{ post.author if post else '' }}" required placeholder="Ваше ім'я або псевдонім">

            <label>Зміст матеріалу:</label>
            <textarea name="content" rows="8" required placeholder="Детальний опис публікації...">{{ post.content if post else '' }}</textarea>

            <div>
                <button type="submit">{{ button_text }}</button>
                <a href="{{ url_for('post_list') }}" class="cancel-btn">Скасувати</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

# Тимчасове сховище публікацій
posts_db = [
    {
        "id": 1,
        "title": "Принципи побудови RESTful веб-сервісів",
        "content": "Архітектурний стиль REST базується на принципах клієнт-серверної архітектури, відсутності збереження стану (stateless) та стандартизованих HTTP методах (GET, POST, PUT, DELETE).",
        "author": "Ліпунов Д.О.",
        "created_at": "2026-10-31 10:15"
    },
    {
        "id": 2,
        "title": "Робота з сесіями та куками у Python",
        "content": "Cookies зберігаються на стороні клієнта у браузері, тоді як сесії забезпечують захищене збереження стану на сервері або через криптографічно підписаний JWT/cookie механізм.",
        "author": "Марія Шевченко",
        "created_at": "2026-10-31 10:45"
    }
]
next_id = 3

@app.route("/")
def home():
    return redirect(url_for("post_list"))

@app.route("/posts")
def post_list():
    """READ: відображення списку всіх публікацій із пагінацією."""
    page = request.args.get("page", default=1, type=int)
    per_page = 2
    total_posts = len(posts_db)
    total_pages = (total_posts + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated = posts_db[start:end]

    return render_template_string(
        LIST_TEMPLATE,
        posts=paginated,
        current_page=page,
        total_pages=total_pages
    )

@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    """READ: детальне відображення окремої публікації."""
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, post=post)

@app.route("/posts/create", methods=["GET", "POST"])
def post_create():
    """CREATE: створення нової публікації з валідацією."""
    global next_id
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            return render_template_string(
                FORM_TEMPLATE,
                form_title="Нова публікація",
                button_text="Опублікувати",
                post=request.form,
                error="Помилка валідації: усі поля є обов'язковими до заповнення!"
            ), 400

        new_post = {
            "id": next_id,
            "title": title,
            "author": author,
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        posts_db.append(new_post)
        created_id = next_id
        next_id += 1

        flash(f"Публікацію '{title}' успішно створено!")
        return redirect(url_for("post_detail", post_id=created_id))

    return render_template_string(
        FORM_TEMPLATE,
        form_title="Нова публікація",
        button_text="Опублікувати",
        post=None
    )

if __name__ == "__main__":
    app.run(debug=True, port=5003)
