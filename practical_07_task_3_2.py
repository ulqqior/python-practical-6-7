"""
ПР №6-7: Імплементація маршрутизації, CRUD операцій та REST архітектури у Flask.
Завдання 3.2: Серіалізація, розширена фільтрація, авторизація через API-Key та обробка виключень.
"""

from flask import Flask, request, jsonify, g
from datetime import datetime
import time
from functools import wraps

app = Flask(__name__)

# --- Централізована обробка помилок ---

class APIError(Exception):
    """Базове кероване виключення API."""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

@app.errorhandler(APIError)
def handle_api_error(error: APIError):
    """Централізована обробка виключень API."""
    response = {
        "error": error.message,
        "status": error.status_code,
        "details": error.details,
        "timestamp": datetime.now().isoformat(),
    }
    return jsonify(response), error.status_code

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Ендпоінт або ресурс не знайдено", "status": 404}), 404

# --- Серіалізатор даних ---

class StudentSerializer:
    """Серіалізатор для безпечного та гнучкого перетворення даних студента."""

    @staticmethod
    def serialize(student: dict, fields: list[str] | None = None) -> dict:
        """Серіалізувати сутність студента (з вибором полів)."""
        # Обчислюємо додаткове поле академічного статусу
        gpa = student.get("gpa", 0.0)
        academic_status = "відмінник" if gpa >= 90.0 else ("хорошист" if gpa >= 75.0 else "задовільно")

        full_data = {
            "id": student.get("id"),
            "name": student.get("name"),
            "group": student.get("group"),
            "email": student.get("email"),
            "gpa": student.get("gpa"),
            "academic_status": academic_status,
            "created_at": student.get("created_at")
        }

        if fields:
            # Повертаємо лише запитані клієнтом поля (+ id завжди для ідентифікації)
            allowed = set(fields) | {"id"}
            return {k: v for k, v in full_data.items() if k in allowed}

        return full_data

    @staticmethod
    def deserialize(data: dict) -> dict:
        """Десеріалізувати та провалідувати вхідні дані запиту."""
        if not data or not isinstance(data, dict):
            raise APIError("Очікується коректний JSON-об'єкт у тілі запиту", status_code=400)

        errors = {}
        name = str(data.get("name", "")).strip()
        group = str(data.get("group", "")).strip()
        email = str(data.get("email", "")).strip()
        gpa_raw = data.get("gpa")

        if not name:
            errors["name"] = "Ім'я студента (name) є обов'язковим"
        if not group:
            errors["group"] = "Академічна група (group) є обов'язковою"
        if not email or "@" not in email:
            errors["email"] = "Некоректний або порожній email"

        try:
            gpa = float(gpa_raw)
            if not (0.0 <= gpa <= 100.0):
                errors["gpa"] = "Оцінка gpa повинна належати діапазону [0.0, 100.0]"
        except (ValueError, TypeError):
            errors["gpa"] = "Оцінка gpa має бути дійсним числом"

        if errors:
            raise APIError("Помилка валідації полів запиту", status_code=422, details=errors)

        return {
            "name": name,
            "group": group,
            "email": email,
            "gpa": gpa
        }

    @staticmethod
    def serialize_list(students: list[dict], fields: list[str] | None = None) -> list[dict]:
        """Серіалізувати масив студентів."""
        return [StudentSerializer.serialize(s, fields) for s in students]

# --- Middleware: логування та заголовки ---

@app.before_request
def log_request_start():
    """Логування вхідного запиту та фіксація часу старту."""
    g.start_time = time.perf_counter()

@app.after_request
def add_response_headers(response):
    """Додавання службових заголовків (час виконання та CORS)."""
    if hasattr(g, "start_time"):
        elapsed_ms = (time.perf_counter() - g.start_time) * 1000
        response.headers["X-Request-Time"] = f"{elapsed_ms:.2f}ms"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    return response

# --- Декоратор авторизації ---

def require_api_key(f):
    """Декоратор перевірки API-ключа в заголовку X-API-Key."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise APIError("Відсутній заголовок авторизації X-API-Key", status_code=401)
        if api_key != "secret-api-key-123":
            raise APIError("Недійсний токен авторизації API", status_code=403)
        return f(*args, **kwargs)
    return wrapper

# --- Сховище даних ---

students_db = {
    1: {"id": 1, "name": "Іваненко Олексій", "group": "БІКС-21", "email": "ivan@kubg.edu.ua", "gpa": 92.5, "created_at": "2026-10-31T09:00:00"},
    2: {"id": 2, "name": "Петренко Марія", "group": "БІКС-21", "email": "maria@kubg.edu.ua", "gpa": 88.0, "created_at": "2026-10-31T09:15:00"},
    3: {"id": 3, "name": "Сидоренко Денис", "group": "БІКС-22", "email": "denys@kubg.edu.ua", "gpa": 97.4, "created_at": "2026-10-31T09:30:00"},
    4: {"id": 4, "name": "Коваленко Іванна", "group": "БІКС-22", "email": "ivanna@kubg.edu.ua", "gpa": 74.2, "created_at": "2026-10-31T10:00:00"},
}
next_id = 5

# --- REST API v2 ендпоінти ---

@app.route("/api/v2/students", methods=["GET"])
def get_students_v2():
    """GET /api/v2/students — отримання списку студентів із серіалізацією, вибором полів, пошуком та сортуванням.
    Query:
        ?fields=name,group,gpa
        ?search=Денис
        ?sort=gpa
        ?order=desc
    """
    fields_arg = request.args.get("fields")
    fields = [f.strip() for f in fields_arg.split(",")] if fields_arg else None
    search_query = request.args.get("search", "").strip().lower()
    sort_by = request.args.get("sort", default="id")
    order = request.args.get("order", default="asc").lower()

    students = list(students_db.values())

    # Повнотекстовий пошук за ім'ям, групою або email
    if search_query:
        students = [
            s for s in students
            if search_query in s["name"].lower() or search_query in s["group"].lower() or search_query in s["email"].lower()
        ]

    # Сортування
    if sort_by in ["id", "name", "group", "gpa"]:
        students.sort(key=lambda s: s[sort_by], reverse=(order == "desc"))

    # Серіалізація списку через StudentSerializer
    serialized_list = StudentSerializer.serialize_list(students, fields=fields)

    return jsonify({
        "total": len(serialized_list),
        "fields_selected": fields if fields else "all",
        "students": serialized_list
    }), 200

@app.route("/api/v2/students", methods=["POST"])
@require_api_key
def create_student_v2():
    """POST /api/v2/students — захищене створення студента з десеріалізацією та валідацією."""
    global next_id
    raw_data = request.get_json(silent=True)
    clean_data = StudentSerializer.deserialize(raw_data)

    # Перевірка унікальності email
    if any(s["email"].lower() == clean_data["email"].lower() for s in students_db.values()):
        raise APIError(f"Студент з email '{clean_data['email']}' вже зареєстрований", status_code=400)

    new_student = {
        "id": next_id,
        **clean_data,
        "created_at": datetime.now().isoformat()
    }
    students_db[next_id] = new_student
    next_id += 1

    return jsonify(StudentSerializer.serialize(new_student)), 201

if __name__ == "__main__":
    app.run(debug=True, port=5006)
