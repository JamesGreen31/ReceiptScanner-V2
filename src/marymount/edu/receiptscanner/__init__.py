from flask import Flask

from .config import Config
from .controllers.receipts import receipts_bp
from .services.storage_service import StorageService


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    StorageService.ensure_environment(app.config)

    app.register_blueprint(receipts_bp)

    @app.context_processor
    def inject_globals():
        return {"app_name": "Receipt Scanner (POC)"}

    return app
