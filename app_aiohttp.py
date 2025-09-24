from datetime import datetime
from aiohttp import web
import json

# --- простое "хранилище" в памяти процесса ---
ads: dict[int, dict] = {}
next_id: int = 1


def serialize_ad(ad_id: int, ad: dict) -> dict:
    return {
        "id": ad_id,
        "title": ad["title"],
        "description": ad["description"],
        "owner": ad["owner"],
        "created_at": ad["created_at"],
    }


# ---------- JSON ошибки единым форматом ----------
@web.middleware
async def json_error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except web.HTTPException as ex:
        # текст, который укажем в исключении, попадёт как message
        code = ex.status
        # маппинг кодов в краткие имена
        names = {400: "bad_request", 404: "not_found", 405: "method_not_allowed"}
        return web.json_response(
            {"error": names.get(code, "http_error"), "message": ex.text or ex.reason},
            status=code,
        )
    except Exception:
        # необработанные ошибки
        return web.json_response(
            {"error": "internal_error", "message": "Internal Server Error"}, status=500
        )


app = web.Application(middlewares=[json_error_middleware])


# ---------- маршруты ----------
async def alive(request: web.Request):
    return web.json_response({"status": "ok", "service": "Ads API (aiohttp)"})


async def create_ad(request: web.Request):
    if request.content_type != "application/json":
        raise web.HTTPBadRequest(text="Request body must be JSON")

    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise web.HTTPBadRequest(text="Malformed JSON")

    # валидация обязательных полей
    for field in ("title", "description", "owner"):
        val = data.get(field)
        if not isinstance(val, str) or not val.strip():
            raise web.HTTPBadRequest(
                text=f"Field '{field}' is required and must be a non-empty string"
            )

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

    return web.json_response(serialize_ad(ad_id, ad), status=201)  # 201 Created


async def get_ad(request: web.Request):
    ad_id = int(request.match_info["ad_id"])
    ad = ads.get(ad_id)
    if not ad:
        raise web.HTTPNotFound(text="Ad not found")
    return web.json_response(serialize_ad(ad_id, ad))


async def delete_ad(request: web.Request):
    ad_id = int(request.match_info["ad_id"])
    if ad_id not in ads:
        raise web.HTTPNotFound(text="Ad not found")
    del ads[ad_id]
    return web.Response(status=204)  # No Content


# регистрируем роуты
app.add_routes(
    [
        web.get("/", alive),
        web.post("/ads", create_ad),
        web.get(r"/ads/{ad_id:\d+}", get_ad),
        web.delete(r"/ads/{ad_id:\d+}", delete_ad),
    ]
)


if __name__ == "__main__":
    # локальный запуск (как у Flask)
    web.run_app(app, host="127.0.0.1", port=5000)