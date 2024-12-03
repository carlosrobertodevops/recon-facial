import gc
import imghdr
import json
import time
from datetime import datetime, timedelta
import numpy as np
from flask import jsonify, request
from .autenticate import jwt_required
from .recface import RecFace
from settings import configure_logger

def index():
    '''ROTA DE TESTE DA API'''
    return jsonify({'status': 'OK'})



@jwt_required
def codificar_rosto(current_user='', _jsontoken={}):
    '''ENDEPOINT: /foto/codificar
        PARAMETROS LIDOS NO CABEÇALHO (Todos Opcionais):
        
        metodo: hog ou cnn (cnn é mais preciso e mais lento)
        repeticao: 1 a 3 (N vezes que avalia a imagem em busca de um rosto)
        forma_processamento: auto <--- Irá usar o método do Mais Rápido ao mais Lento até encontrar um
                             Rosto, ou passar por todas as Opções re retornar [[]]
        .
    '''
    # Para Gerar Log no Arquivo
    #log = configure_logger(log_path='logs/')
    #log.info(f'Utilização do Método: U:{current_user} Tk: {_jsontoken}')
    
    retorno = []
    rf = RecFace()
    npimg = ''
    img = ''
    files = ''

    if request.method == 'POST':
        # Parâmetros de Codificação
        metodo = request.headers.get('metodo', 'hog')
        repeticao = request.headers.get('repeticao', 1)
        forma_processamento = request.headers.get(
            'forma_processamento', 'auto')

        # Fixa em 1 passagem para metodo cnn pois usa muito recurso Fisico do PC
        if metodo == 'cnn' and repeticao != 1:
            repeticao = 1

        # Arquivos
        files = request.files.getlist("upload_image")
        print(f'---> U:{current_user} Tk: {_jsontoken}', files, flush=True)
        if files:
            for f in files:
                rosto = {}

                # Pula os arquivos != imagens
                # https://docs.python.org/3/library/imghdr.html
                # f.content_type Retorna formato, mas se nao tiver a extensão não e reconhecido como imagem
                formato = imghdr.what(f)

                if not formato:
                    print('Formato Não reconhecido', f, flush=True)
                    continue

                inicio = time.time()

                npimg = np.fromfile(f, np.uint8)

                rosto['file'] = f.filename
                rosto['mensagem'] = ''
                rosto['status'] = 'OK'
                try:
                    try:
                        if forma_processamento == 'auto':
                            img = rf.codificar_auto(
                                img=npimg, num_passagens=int(repeticao))
                            rosto['metodo'] = 'Automático!'
                        else:
                            # Codificação com modelo de aprendizado
                            # Se Falhar, tenta no método Simples
                            img = rf.codificar_mod_aprendizado(
                                img=npimg, num_passagens=int(repeticao), model=metodo)
                            rosto['metodo'] = f'Aprendizado de Máquina, pixel a pixel ({metodo}, {repeticao})'
                    except Exception as erro:
                        print('----> Falha: ', erro, flush=True)
                        # Codificação Simples
                        img = rf.codificar(npimg)
                        rosto['metodo'] = 'Simples'
                except Exception as erro:
                    print('----> Falha ao Codificar a Imagem: ', erro, flush=True)
                    rosto['metodo'] = 'Ambos as Tentativas Falharam!'
                    rosto['status'] = 'Falha'
                    rosto['mensagem'] = 'Todos os Métodos  de Detecção falharam! Experimente Outra foto com melhor qualidade!!!'
                    img = []

                rosto['encoding'] = img
                rosto['totalrosto'] = len(img)
                fim = time.time()
                rosto['tempogasto'] = str(fim - inicio) + 's'

                retorno.append(rosto)

            # Delera da memoria o Ultimo arquivo lido ao final do loop
            del f
        else:
            rosto = {}
            rosto['mensagem'] = 'Não Foi recebido Nenhuma Imagem Válida!!!'
            retorno.append(rosto)

    else:
        rosto = {}
        rosto['encoding'] = []
        rosto['mensagem'] = 'Método Não Permitido!!!'
        rosto['file'] = ''
        rosto['totalrosto'] = 0
        rosto['status'] = 'Falha'
        rosto['tempogasto'] = ''
        retorno.append(rosto)

    # Limpezas
    del rf, rosto, img, npimg, files
    gc.collect()

    return json.dumps(retorno)  # render_template('index.html')


@jwt_required
def comparar_rosto(current_user, _jsontoken):
    '''RECEBE UMA LISTA DE OBJETOS E REALIZA A COMPARAÇÃO ENTRE OS ROSTOS:
         [{'img': [[1,2,3, ..., 128]], 'nome_foto': 'fotoxxx.png'}]
    '''
    try:
        img = request.get_json()
    except:
        img = []
    rf = RecFace()
    retorno = rf.compara_rostos(img)

    return {'retorno': retorno}
