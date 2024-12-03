from difflib import restore
import gc

import cv2
import dlib
import face_recognition
import numpy as np


class RecFace():
    '''REALIZA A CODIFICAÇÃO DA IMAGEM E COMPARAÇÃO EM BUSCA DE ROSTOS IDENTICOS
       https://github.com/ageitgey/face_recognition
    '''

    def __init__(self):
        self.TOLERANCE = 0.6  # 0.6 qnt MAIOR menos preciso.
        self.FRAME_THICKNESS = 3
        self.FONT_THICKNESS = 2
        self.MODEL = 'cnn'  # cnn|hog cnn é maia preciso, mas usa mais recursos do pc e é mais lento

    def clean_dlib(self):
        '''MÉTODO NECESSÁRIO PARA LIMPAR A MEMÓRIA E EVITAR USAR 100% DA RAM
            ESSA É UMA FALHA DO PROJETO QUE É CONTORNADO AQUI
        '''
        del face_recognition.api.cnn_face_detector
        del face_recognition.api.face_encoder

    def init_dlib(self):
        '''METÓDO NECESSÁRIO PARA INICIAR AS CONFS POIS FOI USADO
            O METODO PARA LIMPAR A MEMÓRIA
        '''
        face_recognition.api.cnn_face_detector = dlib.cnn_face_detection_model_v1(
            face_recognition.api.cnn_face_detection_model)
        face_recognition.api.face_encoder = dlib.face_recognition_model_v1(
            face_recognition.api.face_recognition_model)

    def redimensionar(self, localimagem, largura=700, altura=400):
        '''REDIMENSIONA AS FOTOS PARA NÃO PROCESSAR FOTOS MUITO LARGAS OU 
            ALTAS COM MUITOS PIXELS DESNECESSÁRIOS
            Tamnho Default é 700X400
            a Saída é um numpy array
        '''

        # O Arquivo veio por Request... e é um numpy.ndarray
        if type(localimagem).__module__ == np.__name__:
            # cv2.COLOR_BGR2GRAY NÃO houve ganho de desempenho Significativo
            # cv2.COLOR_BGR2RGB cv2.COLOR_BGR2GRAY
            img = cv2.imdecode(localimagem, cv2.COLOR_BGR2RGB)
        else:
            # A Imagem está Salva localmente
            img = cv2.imread(localimagem, cv2.COLOR_BGR2RGB)
        
        # Obtem as dimensoes atuais da foto para saber
        # se precisa ser rediredimensionada
        larg_atual = int(img.shape[1])
        alt_atual = int(img.shape[0])
        if larg_atual > largura or alt_atual > altura:
            #print('Precisa redimensionar...')
            per_largura = ((largura * 100) / larg_atual)
            per_altura = ((altura * 100) / alt_atual)

            if per_largura > per_altura:
                per_reducao = per_largura
            else:
                per_reducao = per_altura

            largura = int(larg_atual * per_reducao / 100)
            altura = int(alt_atual * per_reducao / 100)

            img_resize = (largura, altura)
            retorno = cv2.resize(img, img_resize)

            # Salva a Foto no disco, apenas para testes
            #cv2.imwrite('NOMEFOTO.jpg', retorno)

            del img, localimagem
            gc.collect()
            return retorno
        else:
            img_resize = (larg_atual, alt_atual)
            retorno = cv2.resize(img, img_resize)

            del img, localimagem
            gc.collect()
            return retorno

    def codificar(self, img: str):
        '''CODIFICA A IMAGEM PARA SER INSERIDO NO BD O ARRAY DE 128 ITENS
           Utiliza uma codificação Simples. Mais rápido mas não pega os rostos em fotos ruins ou com máscaras
        '''

        self.init_dlib()
        imagem = self.redimensionar(img)

        i = 1
        while True:
            # Loop necessário qnd a foto vem virada,
            # Vai girar a foto até 4x ou  ate achar o rosto
            encoding = face_recognition.face_encodings(imagem)
            if len(encoding) > 0 or i > 3:
                # Sai do Loop pois Ja achou o Rosto ou Rotacionou ao maximo a imagem
                break
            else:
                imagem = np.rot90(imagem, i)
                print(
                    f'-----------> Rotacionou a Imagem em {i}x em busca de Rostos...', flush=True)

            i += 1
        # Formato do Retorno [[rosto1], [rosto2]...]
        retorno = [item.tolist() for item in encoding]

        del (encoding, imagem)
        gc.collect()
        self.clean_dlib()

        return retorno

    def codificar_mod_aprendizado(self, img: str, num_passagens=1, model='hog'):
        '''CODIFICA A IMAGEM PARA SER INSERIDO NO BD O ARRAY DE 128 ITENS
            usando modelo de aprendizado, mais preciso e mais lento
            para isso realiza o Redimensionamento da Imagem para 700x400 ou mantem se for menor
            num_passagens: é a qnt de vezes que analisa a imagem em busca de faces
        '''

        imagem = self.redimensionar(img)
        self.init_dlib()
        i = 1
        while True:
            locais_face = []
            # Fixa ao máximo 3x para nao sobrecarregar o servidor
            if num_passagens > 3:
                num_passagens = 3
            if model == 'cnn':
                try:
                    # Tenta achar os rostos usando mod aprendizado de maquina usando o MODELO cnn, mais avançado
                    # Se falhar usa o metodo default que é mais rapido mas menos preciso
                    locais_face = face_recognition.face_locations(
                        imagem, number_of_times_to_upsample=num_passagens, model='cnn')
                except:
                    # Mais rapido, menos preciso por usar outro metodo de detecção
                    locais_face = face_recognition.face_locations(
                        imagem, number_of_times_to_upsample=3)
            else:
                locais_face = face_recognition.face_locations(
                    imagem, number_of_times_to_upsample=num_passagens, model='hog')

            if len(locais_face) > 0 or i > 3:
                # Sai do Loop pois Ja achou o Rosto ou Rotacionou ao maximo a imagem
                break
            else:
                imagem = np.rot90(imagem, i)
                print(
                    f'-----------> Rotacionou a Imagem em {i} em busca de Rostos...', flush=True)
            i += 1

        encoding = face_recognition.face_encodings(imagem, locais_face)
        retorno = [item.tolist() for item in encoding]

        del (encoding, imagem, locais_face)
        gc.collect()
        self.clean_dlib()

        return retorno

    def codificar_auto(self, img: str, num_passagens=1):
        '''MÉTODO QUE CODIFICA A FOTO INICIANDO PELO MÉTODO MAIS RÁPIDO
            SE NAO ENCONTRAR, VAI PARA O MÉTODO COM APRENCIZADO DE MÁQUINA
            Passa por todos os métodos em busca do Rosto
        '''
        # print('---> Chamou Metodo Automático...')
        retorno = self.codificar(img)
        if not retorno:
            retorno = self.codificar_mod_aprendizado(img, num_passagens, model='hog')
            if not retorno:
                retorno = self.codificar_mod_aprendizado(img, num_passagens, model='cnn')
        
        return retorno
    
    def compara_rostos(self, lst_img: list):
        '''Recebe uma lista com dois ou varios rostos codificados com o codificar() ou codificar_mod_aprendizado()
            e retorna a similaridade entre os rostos.
            [{'img': [[1,2,3, ..., 128]], 'nome_foto': 'fotoxxx.png'}]
        '''
        # img_buscar = np.asarray(img_cod_buscar, dtype=float)

        resultado = []
        if len(lst_img) <= 1:
            return resultado

        for i, item in enumerate(lst_img):
            for r, rb in enumerate(item['img']):
                for it, img in enumerate(lst_img):
                    # Compara com todos, exceto a propria imagem
                    if it != i:
                        for rc, rosto in enumerate(img['img']):
                            # Para Não fazer a comparação dupla, a->b e b->a
                            if not f"{item['nome_foto']}{r + 1}/{img['nome_foto']}{rc + 1}" in str(resultado) and not f"{img['nome_foto']}{rc + 1}/{item['nome_foto']}{r + 1}" in str(resultado):
                                comp = face_recognition.face_distance(
                                    np.asarray([rb], dtype=float),
                                    np.asarray([rosto], dtype=float)
                                )
                                
                                semelhanca = comp.tolist()[0]
                                # print('---->', semelhanca)
                                if semelhanca < 0.14:
                                    semelhanca = 100
                                else:
                                    semelhanca = round(
                                        100 - ((semelhanca - 0.05) * 100), 2)
                                resultado.append(
                                    {'img_comparado': item['nome_foto'], 'rosto': r + 1, 'distancia': comp.tolist()[0],
                                        'percentual': semelhanca, 'img_buscado': img['nome_foto'], 'rosto_b': rc + 1,
                                        'foto_a_b': f"{item['nome_foto']}{r + 1}/{img['nome_foto']}{rc + 1}"}
                                )

        return resultado

    def comparar(self, img_cod_buscar: list, imgs_cod_comparar: list, sensibilidade=None):
        '''COMPARA DUAS IMAGES E RETORNA SE OS ROSTOS EM img_cod_buscar ESTÁ EM  imgs_cod_comparar
            img_cod_buscar = Uma imagem que o usuario upa para buscar no bd, apos a codificacao()
            imgs_cod_comparar = Uma imagem já codificado que está na base de dados para comparação com img_cod_buscar
            RETORNO PADRAO DA BIBLIOTECA:
            {'encontrado': True, 'itens': {'totalencontrado': 1, 'resultado': [[False, True]]}}
        '''

        if sensibilidade and sensibilidade <= 1.0:
            self.TOLERANCE = sensibilidade

        img_buscar = np.asarray(img_cod_buscar, dtype=float)
        img_comparar = np.asarray(imgs_cod_comparar, dtype=float)
        resultado = []
        retorno = {'encontrado': False}
        totalencontrado = 0

        # Veio só um Rosto no item do BD para comparação
        if len(img_comparar) == 128:
            comp = face_recognition.compare_faces(
                img_buscar, img_comparar, self.TOLERANCE)
            if True in comp:
                retorno['encontrado'] = True
                totalencontrado += 1
                resultado.append(comp)
        else:
            # Veio Varios Rostos no item do BD
            for i, img in enumerate(img_comparar):
                #print(f'Comparando Imagns, {i+1}/{len(imgs_cod_comparar)}')
                comp = face_recognition.compare_faces(
                    img_buscar, img, self.TOLERANCE)
                if True in comp:
                    retorno['encontrado'] = True
                    totalencontrado += 1
                    resultado.append(comp)

        retorno['itens'] = {
            'totalencontrado': totalencontrado, 'resultado': resultado}
        return retorno

    def girar_foto(np_img):
        np_img = np.rot90(np_img, 3)
        return np_img

# Como Chamar a Classe
# rf = RecFace()

# cod_img_upada = rf.codificar_mod_aprendizado('unknown_faces/20201128_082142.jpg')
# cod_img_bd = rf.codificar_mod_aprendizado('1/20200919_091141.jpg', 1)
# print('Tot. Rostos Encontrados na Imagem UPADA', len(cod_img_upada))
# comp = rf.comparar(cod_img_bd, cod_img_upada, 0.65)

# #Verificão do Resultado da comparação
# if comp['encontrado']:
#     total = comp['itens']['totalencontrado']
#     result = comp['itens']['resultado']
#     print(f'Encontrado {total} Itens na comparação {result}')
