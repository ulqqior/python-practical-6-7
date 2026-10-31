"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 1.1: Маршрутизація для GET та POST запитів з динамічними параметрами.
"""

from flask import Flask, request, render_template_string, redirect, url_for, abort

app = Flask(__name__)

# Шаблон HTML для демонстрації
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        nav a { margin-right: 12px; color: #0284c7; text-decoration: none; font-weight: 600; }
        nav a:hover { text-decoration: underline; }
        .post-card { border-bottom: 1px solid #e2e8f0; padding: 12px 0; }
        .badge { background: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; }
        input[type=text], textarea { width: 100%; padding: 8px; margin: 6px 0 14px; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 9px 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0369a1; }
        .pagination a { margin: 0 5px; color: #0284c7; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <nav>
            <a href="{{ url_for('index') }}">Головна</a> |
            <a href="{{ url_for('post_list') }}">Публікації</a> |
            <a href="{{ url_for('post_create') }}">+ Створити пост</a> |
            <a href="{{ url_for('search') }}">Пошук</a> |
            <a href="{{ url_for('archive', year=2026, month=10) }}">Архів (10/2026)</a> |
            <a href="{{ url_for('user_profile', username='Denys') }}">Профіль</a>
        </nav>
        <hr>
        {{ content | safe }}
    </div>
</body>
</html>
"""

# Тимчасове сховище даних
posts_db = [
    {"id": 1, "title": "Вступ до Python", "content": "Python — потужна та гнучка мова програмування для бекенду і науки про дані.", "author": "Іван", "year": 2026, "month": 10},
    {"id": 2, "title": "Flask для початківців", "content": "Flask — мікрофреймворк з мінімалістичним ядром та великими можливостями розширення.", "author": "Марія", "year": 2026, "month": 10},
    {"id": 3, "title": "REST API принципи", "content": "REST — архітектурний стиль передачі стану представлення з використанням стандартних HTTP-методів.", "author": "Петро", "year": 2026, "month": 9},
]
next_id = 4

# 1. Головна сторінка (GET /)
@app.route("/")
def index():
    content = f"""
    <h2>Вітаємо на навчальному порталі Flask!</h2>
    <p>Цей сервіс демонструє систему маршрутизації, обробку статичних та динамічних параметрів, обробку POST-форм та роботу з URL-генератором <code>url_for()</code>.</p>
    <p>У системі зареєстровано публікацій: <strong>{len(posts_db)}</strong>.</p>
    """
    return render_template_string(BASE_TEMPLATE, title="Головна сторінка", content=content)

# 2. Список публікацій з пагінацією (GET /posts?page=1&per_page=2)
@app.route("/posts")
def post_list():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=2, type=int)

    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = posts_db[start:end]
    total_pages = (len(posts_db) + per_page - 1) // per_page

    posts_html = ""
    for p in paginated_posts:
        posts_html += f"""
        <div class="post-card">
            <h3><a href="{url_for('post_detail', post_id=p['id'])}">{p['title']}</a></h3>
            <p>{p['content']}</p>
            <span class="badge">Автор: {p['author']}</span>
        </div>
        """

    pagination_html = "<div class='pagination'><p>Сторінки: "
    for i in range(1, total_pages + 1):
        if i == page:
            pagination_html += f"<strong>[{i}]</strong> "
        else:
            pagination_html += f"<a href='{url_for('post_list', page=i, per_page=per_page)}'>{i}</a> "
    pagination_html += "</p></div>"

    content = posts_html + pagination_html
    return render_template_string(BASE_TEMPLATE, title="Список публікацій", content=content)

# 3. Деталі публікації (GET /posts/<int:post_id>)
@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        abort(404)

    content = f"""
    <h2>{post['title']}</h2>
    <p>{post['content']}</p>
    <p><span class="badge">Автор: {post['author']}</span> | Дата: {post['month']:02d}/{post['year']}</p>
    <hr>
    <p><a href="{url_for('post_list')}">&larr; Назад до списку</a></p>
    """
    return render_template_string(BASE_TEMPLATE, title=f"Публікація #{post_id}", content=content)

# 4. Створення публікації (GET+POST /posts/create)
@app.route("/posts/create", methods=["GET", "POST"])
def post_create():
    global next_id
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        author = request.form.get("author", "").strip()

        if not title or not content or not author:
            error_content = "<p style='color:red;'>Усі поля обов'язкові для заповнення!</p>"
            return render_template_string(BASE_TEMPLATE, title="Створити публікацію", content=error_content + get_create_form(title, content, author)), 400

        new_post = {
            "id": next_id,
            "title": title,
            "content": content,
            "author": author,
            "year": 2026,
            "month": 10
        }
        posts_db.append(new_post)
        created_id = next_id
        next_id += 1

        # Redirect після успішного POST запиту (Post/Redirect/Get патерн)
        return redirect(url_for("post_detail", post_id=created_id))

    return render_template_string(BASE_TEMPLATE, title="Створити публікацію", content=get_create_form())

def get_create_form(title="", content="", author=""):
    return f"""
    <form method="POST" action="{url_for('post_create')}">
        <label><strong>Заголовок публікації:</strong></label>
        <input type="text" name="title" value="{title}" placeholder="Введіть заголовок" required>

        <label><strong>Автор:</strong></label>
        <input type="text" name="author" value="{author}" placeholder="Ваше ім'я" required>

        <label><strong>Зміст:</strong></label>
        <textarea name="content" rows="6" placeholder="Текст публікації..." required>{content}</textarea>

        <button type="submit">Опублікувати</button>
    </form>
    """

# 5. Пошук (GET /search?q=query)
@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        q_lower = query.lower()
        results = [p for p in posts_db if q_lower in p["title"].lower() or q_lower in p["content"].lower()]

    content = f"""
    <form method="GET" action="{url_for('search')}">
        <input type="text" name="q" value="{query}" placeholder="Введіть запит для пошуку...">
        <button type="submit">Шукати</button>
    </form>
    """
    if query:
        content += f"<h3>Результати за запитом: <em>{query}</em> ({len(results)} знайдено)</h3>"
        for p in results:
            content += f"""
            <div class="post-card">
                <h4><a href="{url_for('post_detail', post_id=p['id'])}">{p['title']}</a></h4>
                <p>{p['content']}</p>
            </div>
            """
        if not results:
            content += "<p>За вашим запитом нічого не знайдено.</p>"

    return render_template_string(BASE_TEMPLATE, title="Пошук публікацій", content=content)

# 6. Архів за датою (GET /archive/<int:year>/<int:month>)
@app.route("/archive/<int:year>/<int:month>")
def archive(year, month):
    archived = [p for p in posts_db if p.get("year") == year and p.get("month") == month]
    content = f"<h3>Публікації за {month:02d}.{year} (знайдено: {len(archived)})</h3>"
    for p in archived:
        content += f"""
        <div class="post-card">
            <h4><a href="{url_for('post_detail', post_id=p['id'])}">{p['title']}</a></h4>
            <p>{p['content']}</p>
        </div>
        """
    return render_template_string(BASE_TEMPLATE, title=f"Архів за {month:02d}/{year}", content=content)

# 7. Профіль користувача (GET /user/<username>)
@app.route("/user/<username>")
def user_profile(username):
    user_posts = [p for p in posts_db if p["author"].lower() == username.lower()]
    content = f"""
    <h2>Користувач: {username}</h2>
    <p>Кількість публікацій автора: <strong>{len(user_posts)}</strong></p>
    <ul>
    """
    for p in user_posts:
        content += f"<li><a href='{url_for('post_detail', post_id=p['id'])}'>{p['title']}</a></li>"
    content += "</ul>"
    return render_template_string(BASE_TEMPLATE, title=f"Профіль: {username}", content=content)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
