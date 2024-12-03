import logging
import logging.config
from datetime import datetime

def configure_logger(log_path='logs/', name='default'):
    '''CONFIGURAÇÃO DA GERAÇÃO DE LOGS DA API NO CONSOLE/ARQUIVO .log'''
    
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            # 'default': {'format': '%(asctime)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'},
            'full': {
                'format': '---->[{asctime}] {levelname} {module} Func:{funcName} Func:{process:d} Th:{thread:d} [Nome/Linha:{name}:{lineno}] {message}',
                'datefmt': '%d/%b/%Y %H:%M:%S',
                'style': '{',
            },
            'simple': {
                'format': '[{asctime}] {levelname} {message}',
                'datefmt': '%d/%b/%Y %H:%M:%S',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                # 'stream': 'ext://flask.logging.wsgi_errors_stream',
                'stream': 'ext://sys.stdout'
            },
            'file_geral': {
                # DEBUG/WARNING/INFO/ERROR <--- Definindo aqui os Niveis do log q sera enviado ao arquivo
                'level': 'INFO',
                'encoding': 'utf-8',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'full',
                'filename': f'{log_path}/Log_{datetime.strftime(datetime.now(), "%d-%m-%Y")}.log',
                'maxBytes': 5 * 1024 * 1024,  # Tamanho máximo de 5MB por arquivo
                'backupCount': 50,  # Manter no Máximo 50 arquivos
            },
        },
        'loggers': {
            'default': {
                'level': 'DEBUG',
                'handlers': ['console', 'file_geral']
            },
            # Necessário para pegar all logs do Flask
            '': {
                'handlers': ['console', 'file_geral'],
                'propagate': True,
                'formatter': 'full',
            },
            # Log do Gunicorn para qnd em produção mostrar os erros. Nao mostra com flask run
            'gunicorn': {
                'level': 'WARNING',  # DEBUG para printar as requests...
                'handlers': ['file_geral', 'console'],
                'propagate': True,
                'formatter': 'full',
            },

        },
    })
    retorno = logging.getLogger(name)
    return retorno


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "f(98z+*o_dw-3c8jz0scfxNxo&fa*gR=kX@-g^m99@s2d7AX*rhTf0xab"

    # Tamanho máximo de arquivo aceitavel é de 10MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    SESSION_COOKIE_SECURE = True

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = '--->KeySecretaByDevelopment;)'
    # print('=====> Chamou Metodo Development....')

class TestingConfig(Config):
    TESTING = True
