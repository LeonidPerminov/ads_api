from datetime import datetime
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Простое "хранилище" в памяти процесса
ads = {}          # { id: {...} }
next_id = 1       # счётчик id


def serialize_ad(ad_id: int, ad: dict) -> dict:
    """Возвращаем объявление в виде JSON-словаря с id."""
    return {
        "id": ad_id,
        "title": ad["title"],
        "description": ad["description"],
        "owner": ad["owner"],
        "created_at": ad["created_at"],
    }


@app.route("/", methods=["GET"])
def alive():
    return jsonify({"status": "ok", "service": "Ads API"}), 200


@app.route("/ads", methods=["POST"])
def create_ad():
    """
    Создать объявление.
    Ожидаем JSON с полями: title, description, owner
    """
    if not request.is_json:
        abort(400, description="Request body must be JSON")

    data = request.get_json(silent=True) or {}

    # Простая валидация обязательных полей
    for field in ("title", "description", "owner"):
        if field not in data or not isinstance(data[field], str) or not data[field].strip():
            abort(400, description=f"Field '{field}' is required and must be a non-empty string")

    global next_id
    ad_id = next_id
    next_id += 1

    ad = {
        "title": data["title"].strip(),
        "description": data["description"].strip(),
        "owner": data["owner"].strip(),
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    ads[ad_id] = ad

    return jsonify(serialize_ad(ad_id, ad)), 201  # 201 Created


@app.route("/ads/<int:ad_id>", methods=["GET"])
def get_ad(ad_id: int):
    """Получить объявление по id."""
    ad = ads.get(ad_id)
    if not ad:
        abort(404, description="Ad not found")
    return jsonify(serialize_ad(ad_id, ad)), 200


@app.route("/ads/<int:ad_id>", methods=["DELETE"])
def delete_ad(ad_id: int):
    """Удалить объявление по id."""
    if ad_id not in ads:
        abort(404, description="Ad not found")
    del ads[ad_id]
    return "", 204  # No Content


# Красивые JSON-ошибки вместо HTML
@app.errorhandler(400)
def bad_request(err):
    return jsonify({"error": "bad_request", "message": err.description}), 400


@app.errorhandler(404)
def not_found(err):
    return jsonify({"error": "not_found", "message": err.description}), 404


if __name__ == "__main__":
    # debug=True — авто-перезапуск при изменениях и подробные ошибки
    app.run(debug=True)