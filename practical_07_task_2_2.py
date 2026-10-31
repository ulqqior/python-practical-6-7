"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 2.2: CRUD: операції Update та Delete з підтвердженням та валідацією.
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
    <title>Блог — Повний CRUD</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 8px; }
        .flash { background: #dcfce7; border-left: 4px solid #22c55e; color: #15803d; padding: 10px 14px; margin-bottom: 18px; border-radius: 4px; }
        .btn-new { display: inline-block; background: #0284c7; color: white; padding: 8px 14px; text-decoration: none; border-radius: 4px; font-weight: bold; }
        article { border-bottom: 1px solid #e2e8f0; padding: 16px 0; }
        .actions a { margin-right: 12px; font-size: 0.9em; text-decoration: none; }
        .btn-edit { color: #d97706; font-weight: bold; }
        .btn-del { color: #dc2626; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Блог — Повний CRUD</h1>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}<div class="flash">✓ {{ msg }}</div>{% endfor %}
            {% endif %}
        {% endwith %}

        <div style="margin-bottom: 15px;">
            <a href="{{ url_for('post_create') }}" class="btn-new">+ Створити нову публікацію</a>
        </div>

        {% for post in posts %}
        <article>
            <h2><a href="{{ url_for('post_detail', post_id=post.id) }}" style="color:#0284c7; text-decoration:none;">{{ post.title }}</a></h2>
            <p>{{ post.content[:150] }}...</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <small style="color: #64748b;">👤 {{ post.author }} | 📅 {{ post.created_at }}</small>
                <div class="actions">
                    <a href="{{ url_for('post_detail', post_id=post.id) }}">Читати</a>
                    <a href="{{ url_for('post_edit', post_id=post.id) }}" class="btn-edit">✏️ Редагувати</a>
                    <a href="{{ url_for('post_delete', post_id=post.id) }}" class="btn-del">🗑️ Видалити</a>
                </div>
            </div>
        </article>
        {% else %}
        <p>Публікацій немає.</p>
        {% endfor %}
    </div>
</body>
</html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>{{ post.title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1 { margin-top: 0; }
        .content { font-size: 1.1em; line-height: 1.7; margin: 20px 0; }
        .actions { margin-top: 25px; padding-top: 15px; border-top: 1px solid #e2e8f0; }
        .actions a { margin-right: 15px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ post.title }}</h1>
        <p style="color: #64748b;">Автор: <strong>{{ post.author }}</strong> | Дата: {{ post.created_at }}</p>
        <div class="content">{{ post.content }}</div>
        <div class="actions">
            <a href="{{ url_for('post_list') }}" style="color: #64748b;">&larr; До списку</a>
            <a href="{{ url_for('post_edit', post_id=post.id) }}" style="color: #d97706;">✏️ Редагувати</a>
            <a href="{{ url_for('post_delete', post_id=post.id) }}" style="color: #dc2626;">🗑️ Видалити</a>
        </div>
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
        label { font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; }
        input[type=text], textarea { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ form_title }}</h1>
        {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
        <form method="POST">
            <label>Заголовок:</label>
            <input type="text" name="title" value="{{ post.title if post else '' }}" required>
            <label>Автор:</label>
            <input type="text" name="author" value="{{ post.author if post else '' }}" required>
            <label>Зміст:</label>
            <textarea name="content" rows="8" required>{{ post.content if post else '' }}</textarea>
            <div>
                <button type="submit">{{ button_text }}</button>
                <a href="{{ url_for('post_list') }}" style="margin-left: 15px; color: #64748b; text-decoration: none;">Скасувати</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

DELETE_CONFIRM_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Підтвердження видалення</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }
        .container { max-width: 550px; margin: 40px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }
        h1 { color: #dc2626; margin-top: 0; }
        .warning-box { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 15px; border-radius: 6px; margin: 20px 0; }
        button { background: #dc2626; color: white; border: none; padding: 10px 22px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #b91c1c; }
        .cancel { margin-left: 15px; color: #64748b; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Підтвердження видалення</h1>
        <div class="warning-box">
            Ви дійсно бажаєте безповоротно видалити публікацію <strong>"{{ post.title }}"</strong> (ID: #{{ post.id }})?
        </div>
        <form method="POST">
            <button type="submit">Так, видалити публікацію</button>
            <a href="{{ url_for('post_detail', post_id=post.id) }}" class="cancel">Скасувати</a>
        </form>
    </div>
</body>
</html>
"""

# Початкове сховище
posts_db = [
    {"id": 1, "title": "Перша публікація: знайомство з CRUD", "content": "CRUD описує базові операції взаємодії зі сховищем даних у будь-якому веб-додатку.", "author": "Іван", "created_at": "2026-10-31 09:30"},
    {"id": 2, "title": "Друга публікація: архітектура Flask", "content": "Завдяки декораторам та маршрутам Flask дозволяє швидко будувати гнучкі системи обробки контенту.", "author": "Марія", "created_at": "2026-10-31 10:15"},
]
next_id = 3

@app.route("/")
@app.route("/posts")
def post_list():
    return render_template_string(LIST_TEMPLATE, posts=posts_db)

@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, post=post)

@app.route("/posts/create", methods=["GET", "POST"])
def post_create():
    global next_id
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            return render_template_string(FORM_TEMPLATE, form_title="Створити публікацію", button_text="Опублікувати", post=request.form, error="Всі поля обов'язкові!"), 400

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

    return render_template_string(FORM_TEMPLATE, form_title="Створити публікацію", button_text="Опублікувати", post=None)

@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
def post_edit(post_id):
    """UPDATE: редагування існуючої публікації."""
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            return render_template_string(
                FORM_TEMPLATE,
                form_title=f"Редагування #{post_id}",
                button_text="Зберегти зміни",
                post=request.form,
                error="Помилка: поля не можуть бути порожніми!"
            ), 400

        # Оновлюємо дані
        post["title"] = title
        post["author"] = author
        post["content"] = content

        flash(f"Публікацію #{post_id} успішно оновлено!")
        return redirect(url_for("post_detail", post_id=post_id))

    return render_template_string(
        FORM_TEMPLATE,
        form_title=f"Редагування #{post_id}",
        button_text="Зберегти зміни",
        post=post
    )

@app.route("/posts/<int:post_id>/delete", methods=["GET", "POST"])
def post_delete(post_id):
    """DELETE: видалення публікації із захисним підтвердженням."""
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        abort(404)

    if request.method == "POST":
        posts_db.remove(post)
        flash(f"Публікацію '{post['title']}' було успішно видалено.")
        return redirect(url_for("post_list"))

    return render_template_string(DELETE_CONFIRM_TEMPLATE, post=post)

if __name__ == "__main__":
    app.run(debug=True, port=5004)
