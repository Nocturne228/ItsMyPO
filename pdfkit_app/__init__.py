from pathlib import Path

from flask import Flask


def create_app():
    app = Flask(__name__)

    from pdfkit_app.routes import api_bp, main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
