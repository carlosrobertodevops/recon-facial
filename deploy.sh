#!/bin/bash
echo "---> Iniciando o processo de Deploy"

echo "================> Processando o Conteiner...!!!"
### GERA o CONTEINER
nome_conteiner="registry.gitlab.com/fabiopaes/recon-facial"
sudo docker build -t $nome_conteiner -f Dockerfile .

### Envia o Conteiner para o GitLab
sudo docker push $nome_conteiner

echo "-----------> Processo Finalizado com Sucesso!!!"