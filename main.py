from flask import Flask
from api.views import codificar_rosto, comparar_rosto, index
from settings import configure_logger

def create_app():
    """Construct the core application."""
    application = Flask(__name__)
    if not application.config["DEBUG"]:
        application.config.from_object("settings.ProductionConfig")
        # LOGs
        log = configure_logger(log_path='logs/')
        application.logger.addHandler(log)
        print('---> Modo Produção!!!', flush=True)
        
    else:
        application.config.from_object("settings.DevelopmentConfig")
        print('---> Modo Development!!!', flush=True)

    with application.app_context():
        # URLS
        # Codificar Rosto
        application.add_url_rule('/foto/codificar', methods=['POST', 'GET'], view_func=codificar_rosto)
        # Comparação entre fotos
        application.add_url_rule('/foto/comparar', methods=['POST', 'GET'], view_func=comparar_rosto)
        # Teste Estado da api
        application.add_url_rule('/', methods=['POST', 'GET'], view_func=index)

    return application

if __name__ == '__main__':
    app = create_app()
    app.run()
