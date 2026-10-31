"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 3.1: Повний REST API для ресурсу "Студент" з фільтрацією, пагінацією та статистикою.
"""

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# "База даних" студентів
students_db = {}
next_id = 1

# --- REST API ендпоінти ---

@app.route("/api/students", methods=["GET"])
def get_students():
    """GET /api/students — список усіх студентів з фільтрацією, сортуванням та пагінацією."""
    group_filter = request.args.get("group")
    min_gpa = request.args.get("min_gpa", type=float)
    sort_by = request.args.get("sort_by", default="id")
    order = request.args.get("order", default="asc").lower()
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    result = list(students_db.values())

    # 1. Фільтрація
    if group_filter:
        result = [s for s in result if s["group"].lower() == group_filter.lower()]
    if min_gpa is not None:
        result = [s for s in result if s["gpa"] >= min_gpa]

    # 2. Сортування
    if sort_by in ["id", "name", "gpa", "group"]:
        reverse = (order == "desc")
        result.sort(key=lambda s: s[sort_by], reverse=reverse)

    # 3. Пагінація
    total_count = len(result)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_students = result[start:end]

    return jsonify({
        "total": total_count,
        "count": len(paginated_students),
        "page": page,
        "per_page": per_page,
        "students": paginated_students
    }), 200

@app.route("/api/students", methods=["POST"])
def create_student():
    """POST /api/students — створити нового студента."""
    global next_id
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Очікується JSON-об'єкт у тілі запиту", "status": 400}), 400

    name = str(data.get("name", "")).strip()
    group = str(data.get("group", "")).strip()
    email = str(data.get("email", "")).strip()
    gpa = data.get("gpa")

    # Валідація обов'язкових полів
    if not name or not group or not email or gpa is None:
        return jsonify({
            "error": "Поля name, group, email та gpa є обов'язковими",
            "status": 422
        }), 422

    try:
        gpa = float(gpa)
    except (ValueError, TypeError):
        return jsonify({"error": "Поле gpa має бути числом", "status": 422}), 422

    if not (0.0 <= gpa <= 100.0):
        return jsonify({"error": "Значення gpa повинно бути в межах від 0 до 100", "status": 422}), 422

    # Перевірка унікальності email
    if any(s["email"].lower() == email.lower() for s in students_db.values()):
        return jsonify({"error": f"Студент з email '{email}' вже зареєстрований", "status": 400}), 400

    new_student = {
        "id": next_id,
        "name": name,
        "group": group,
        "email": email,
        "gpa": gpa,
        "created_at": datetime.now().isoformat()
    }
    students_db[next_id] = new_student
    next_id += 1

    return jsonify(new_student), 201

@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    """GET /api/students/:id — отримати дані конкретного студента."""
    student = students_db.get(student_id)
    if not student:
        return jsonify({"error": f"Студента з ID {student_id} не знайдено", "status": 404}), 404
    return jsonify(student), 200

@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """PUT /api/students/:id — повне оновлення запису студента."""
    if student_id not in students_db:
        return jsonify({"error": f"Студента з ID {student_id} не знайдено", "status": 404}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Очікується JSON-тіло запиту", "status": 400}), 400

    name = str(data.get("name", "")).strip()
    group = str(data.get("group", "")).strip()
    email = str(data.get("email", "")).strip()
    gpa = data.get("gpa")

    if not name or not group or not email or gpa is None:
        return jsonify({"error": "При повному PUT-оновленні обов'язкові всі поля (name, group, email, gpa)", "status": 422}), 422

    try:
        gpa = float(gpa)
    except (ValueError, TypeError):
        return jsonify({"error": "gpa має бути числом", "status": 422}), 422

    if not (0.0 <= gpa <= 100.0):
        return jsonify({"error": "gpa має бути в діапазоні 0..100", "status": 422}), 422

    # Перевірка унікальності email
    for s_id, s_data in students_db.items():
        if s_id != student_id and s_data["email"].lower() == email.lower():
            return jsonify({"error": f"Email '{email}' вже використовується іншим студентом", "status": 400}), 400

    students_db[student_id].update({
        "name": name,
        "group": group,
        "email": email,
        "gpa": gpa,
        "updated_at": datetime.now().isoformat()
    })
    return jsonify(students_db[student_id]), 200

@app.route("/api/students/<int:student_id>", methods=["PATCH"])
def patch_student(student_id):
    """PATCH /api/students/:id — часткове оновлення студента."""
    if student_id not in students_db:
        return jsonify({"error": f"Студента з ID {student_id} не знайдено", "status": 404}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Очікується JSON", "status": 400}), 400

    student = students_db[student_id]

    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify({"error": "name не може бути порожнім", "status": 422}), 422
        student["name"] = name

    if "group" in data:
        group = str(data["group"]).strip()
        if not group:
            return jsonify({"error": "group не може бути порожнім", "status": 422}), 422
        student["group"] = group

    if "email" in data:
        email = str(data["email"]).strip()
        if not email:
            return jsonify({"error": "email не може бути порожнім", "status": 422}), 422
        for s_id, s_data in students_db.items():
            if s_id != student_id and s_data["email"].lower() == email.lower():
                return jsonify({"error": f"Email '{email}' вже зайнято", "status": 400}), 400
        student["email"] = email

    if "gpa" in data:
        try:
            gpa = float(data["gpa"])
            if not (0.0 <= gpa <= 100.0):
                return jsonify({"error": "gpa має бути в межах 0..100", "status": 422}), 422
            student["gpa"] = gpa
        except (ValueError, TypeError):
            return jsonify({"error": "gpa має бути числом", "status": 422}), 422

    student["updated_at"] = datetime.now().isoformat()
    return jsonify(student), 200

@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """DELETE /api/students/:id — видалити студента."""
    if student_id not in students_db:
        return jsonify({"error": f"Студента з ID {student_id} не знайдено", "status": 404}), 404

    del students_db[student_id]
    return "", 204

@app.route("/api/students/stats", methods=["GET"])
def students_stats():
    """GET /api/students/stats — аналітична статистика по базі студентів."""
    students = list(students_db.values())
    total = len(students)
    if total == 0:
        return jsonify({
            "total": 0,
            "avg_gpa": 0.0,
            "groups": {},
            "top_students": []
        }), 200

    avg_gpa = round(sum(s["gpa"] for s in students) / total, 2)
    groups = {}
    for s in students:
        grp = s["group"]
        groups[grp] = groups.get(grp, 0) + 1

    top_students = sorted(students, key=lambda s: s["gpa"], reverse=True)[:3]
    top_clean = [{"id": s["id"], "name": s["name"], "gpa": s["gpa"], "group": s["group"]} for s in top_students]

    return jsonify({
        "total": total,
        "avg_gpa": avg_gpa,
        "groups": groups,
        "top_students": top_clean
    }), 200

# --- Обробники помилок ---

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Ресурс не знайдено", "status": 404}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Некоректний запит", "status": 400}), 400

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"error": "Помилка валідації сутності", "status": 422}), 422

if __name__ == "__main__":
    # Заповнюємо початковими тестовими даними
    test_students = [
        {"name": "Іваненко О.", "group": "БІКС-21", "email": "ivan@kubg.edu.ua", "gpa": 85.5},
        {"name": "Петренко М.", "group": "БІКС-21", "email": "petro@kubg.edu.ua", "gpa": 92.0},
        {"name": "Сидоренко А.", "group": "БІКС-22", "email": "syd@kubg.edu.ua", "gpa": 78.3},
        {"name": "Коваль Л.", "group": "БІКС-22", "email": "koval@kubg.edu.ua", "gpa": 95.1},
    ]
    for s in test_students:
        students_db[next_id] = {**s, "id": next_id, "created_at": datetime.now().isoformat()}
        next_id += 1

    app.run(debug=True, port=5005)
