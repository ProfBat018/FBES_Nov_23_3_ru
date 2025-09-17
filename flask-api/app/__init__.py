from flask import Flask, Response
from flask_smorest import Api
from .ext import db, migrate, jwt
from .api.v1 import bp as api_v1  

SCALAR_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>API Reference</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>html,body{height:100%;margin:0}</style>

    <!-- Конфиг как JSON в script#api-reference -->
    <script id="api-reference" type="application/json">
      {
        "spec": { "url": "/openapi.json" },
        "layout": "modern",
        "theme": "kepler",
        "hideDownloadButton": false,
        "hideSearch": false
      }
    </script>

    <!-- Подключаем UI ПОСЛЕ конфига -->
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </head>
  <body></body>
</html>"""

def create_app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://postgres:postgres@db:5432/appdb",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY="change-me",
        API_TITLE="My Flask API",
        API_VERSION="v1",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openapi.json",
        OPENAPI_REDOC_PATH=None,
        OPENAPI_SWAGGER_UI_PATH=None,
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    api = Api(app)          
    api.register_blueprint(api_v1)

    @app.get("/readyz")
    def readyz():
        return {"status": "ready"}, 200


    @app.get("/docs")
    def scalar_docs():
        return Response(SCALAR_HTML, mimetype="text/html")

    return app
