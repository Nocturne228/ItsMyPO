from pathlib import Path

from flask import Flask


def create_app():
    app = Flask(__name__)

    from pixelforge_web.routes import main_bp, api_bp
    from pixelforge_web.pdf_routes import pdf_api_bp
    from pixelforge_web.image_routes import image_api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(pdf_api_bp, url_prefix="/api")
    app.register_blueprint(image_api_bp, url_prefix="/api")

    return app
