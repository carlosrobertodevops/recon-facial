from functools import wraps

import jwt
#from app.models import User
from flask import jsonify, request
from jwt.algorithms import RSAAlgorithm
from datetime import datetime

jwt.unregister_algorithm('RS256')
jwt.register_algorithm('RS256', RSAAlgorithm(RSAAlgorithm.SHA256))

# GERANDO A CHAVE PUBLICA/PRIVADA
#ssh-keygen -t rsa -b 4096 -m PEM -f jwtRS256.key
#### Don't add passphrase
#openssl rsa -in jwtRS256.key -pubout -outform PEM -out jwtRS256.key.pub
#cat jwtRS256.key        <--- Essa usa para Gerar o Token
#cat jwtRS256.key.pub    <--- Essa usa na API para Decodificar o Token

def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        origem = request.headers.get('origem', None)
        algorithm = request.headers.get('algorithm', 'RS256')
        
        if origem:
            origem = origem.lower()
            try:
                chave = open(f"chave/{origem}.pub", "rb").read()
            except:
                return jsonify({"ERRO 00": f"Erro ao Carregar a Chave Pública para a Origem {origem}!!!"}), 403
            algorithms = algorithm
        else:
            algorithms = 'RS256'
            chave = open("chave/default.pub", "rb").read()
        
        if 'authorization' in request.headers:
            token = request.headers['authorization']
        
        if not token:
            return jsonify({"ERRO A0": "Você não tem Permissão para Está Aqui!!!"}), 403
        
        if not "Bearer" in token:
            return jsonify({"ERRO A1": "Chave de Acesso Inválida ou mau formatada!!!"}), 401
        
        try:
            token_pure = token.replace("Bearer ", "")
            decoded = jwt.decode(jwt=token_pure, key=chave, algorithms=algorithms,
                                 options={'require': ['iat', 'exp']})
            
            # Validações Adicionais:
            try:
                dt_geracao = datetime.fromtimestamp(decoded['iat'])
                dt_exp = datetime.fromtimestamp(decoded['exp'])
                
                if dt_geracao > datetime.now():
                    return jsonify({"ERRO D1": "Tokem Gerado no Futuro?!;)"}), 401
                if int((dt_exp - dt_geracao).seconds / 3600) > 6:
                    return jsonify({"ERRO D2": "Tokem com Validade Muito Longa!!!"}), 401
            
            except:
                return jsonify({"ERRO D0": f"As datas de Geração {decoded['iat']}/Expiração {decoded['exp']} do Tokem foram mau formatadas!!!"}), 401
                
            if 'cpf' in decoded.keys():
                current_user = decoded['cpf']
            else:
                current_user = decoded['username']
    
            decoded['origem'] = origem
            decoded['data_consulta'] = datetime.utcnow()
        except Exception as e:
            print('---->Erro ao Processar o Token: ', str(e), flush=True)
            return jsonify({"ERRO A2": "Erro ao Processar o Token ou o Token já está Expirado!!!"}), 403
        
        return f(current_user=current_user, _jsontoken=decoded, *args, **kwargs)
        
    return wrapper
