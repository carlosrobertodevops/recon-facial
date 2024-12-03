# Imagem gerada em Estágio para reduzir seu tamanho Final
# Utilizando como SO: Debian (slin) com Python 3.10.5
FROM python:3.10.5-slim as base

RUN mkdir /app
COPY . /app
WORKDIR /app

RUN apt-get update && apt-get -y --no-install-recommends install gcc python3-dev default-libmysqlclient-dev \
    cmake build-essential python3-opencv && apt-get clean && \
    pip3 install --upgrade pip && pip3 install wheel && pip3 wheel --wheel-dir=/app/wheels -r requirements.txt

FROM python:3.10.5-slim

COPY --from=base /app app

LABEL maintainer="Fabio Paes"
LABEL versio="1.2.1"
LABEL description="Oráculo API de Reconhecimento Facial e Consulta de Indivíduos!!!"

WORKDIR /app

# Atualiza list app, add os apps sem add cache, remove timezone q nao vai ser utilizada
# apaga cache dos apk, remove o pip3 e o apk do SO, remove a pasta wheels com o cache dos apps
RUN apt-get update && apt-get -y --no-install-recommends install default-libmysqlclient-dev && apt-get clean && \
    pip3 install --upgrade pip && pip3 install --no-index --no-cache-dir --find-links=/app/wheels -r requirements.txt && \
    #useradd --no-create-home oraculo-recface && \
    rm -rf /var/cache/apk/* && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/* && \
    rm -rf /app/wheels

#TimeZone de Rio Branco /app/wheels
ENV TZ America/Rio_Branco
# Defini o usuario de uso
#USER oraculo-recface

# 6000
EXPOSE 5002

# Comando a Ser executado, junto com os parâmetros aceitaveis pelo gunicorn
# max-requests 10 --max-requests-jitter 5 Para reiniciar o Worker apos 10 conexoes, de forma aleatoria.
# Ao iniciar o worker receberá max-requests + --max-requests-jitter(aletório de 0 ao valor do jitter) para reiniciar
CMD gunicorn --bind 0.0.0.0:5002 \
	--workers 4 --threads 8 \
	--access-logfile - \
	--graceful-timeout 300 --timeout 300 \
	--error-logfile - \
    --max-requests 5 --max-requests-jitter 3 \
	--worker-tmp-dir /dev/shm \
	wsgi:application
