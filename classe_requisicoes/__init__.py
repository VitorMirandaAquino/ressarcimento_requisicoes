import requests
import pandas as pd
import re
import os
import time
import shutil

class RequisicoesLiberty:
    """
    Classe para realizar requisições à API Liberty e processar dados.

    Atributos:
        login (str): Usuário para autenticação.
        senha (str): Senha do usuário.

    Métodos:
        - definir_headers(): Retorna os headers padrão para as requisições.
        - fazer_login(): Realiza a autenticação e retorna uma sessão persistente.
        - obter_documentos_danos_eletricos(session, num_processo): Obtém e processa os documentos relacionados a danos elétricos.
        - identificar_extensao_permitida(texto): Verifica se uma string contém uma extensão permitida.
    """

    def __init__(self, login: str, senha: str):
        """
        Inicializa a classe com login e senha.

        Args:
            login (str): Usuário para autenticação.
            senha (str): Senha do usuário.
        """
        self.login = login
        self.senha = senha
        self.headers = None

    def definir_headers(self):
        """
        Define os cabeçalhos padrão para as requisições.

        Returns:
            dict: Dicionário com os headers.
        """
        return {
            "Content-Type": "application/json",
            "x-liberty-ativartrace": "true",
            "x-liberty-nomesistema": "RessarcimentoFiancaui",
            "x-liberty-username": self.login,
        }

    def fazer_login(self):
        """
        Realiza o login na API e retorna uma sessão persistente.

        Returns:
            requests.Session: Sessão autenticada.

        Raises:
            requests.HTTPError: Se a requisição falhar.
        """
        url = "https://ressarcimentofiancabff.yelumseguros.com.br/api/sessao/autenticacaousuario"
        payload = {"usuario": self.login, "senha": self.senha}
        self.headers = self.definir_headers()

        session = requests.Session()
        response = session.post(url, json=payload, headers=self.headers)
        response.raise_for_status()  # Levanta erro caso o status seja diferente de 2xx

        return session
    
    def identificar_extensao_permitida(self, texto):
        """
        Verifica se a string possui uma extensão da lista permitida.

        Args:
            texto (str): String ou URL para análise.

        Returns:
            str: Extensão identificada se for válida.

        Raises:
            ValueError: Se nenhuma extensão válida for encontrada.
        """
        extensoes_permitidas = [
            'doc', 'docx', 'gif', 'jpeg', 'jpg', 'pdf',
            'png', 'ppt', 'pptx', 'txt', 'xls', 'xlsx',
            'eml', 'tif'
        ]

        padrao_extensao = re.compile(r'\.([a-zA-Z0-9]+)(?:\?|$)')
        match = padrao_extensao.search(texto)

        if match:
            extensao = match.group(1).lower()
            if extensao in extensoes_permitidas:
                return extensao
        raise ValueError("Extensão não permitida ou não identificada.")



           

    def obter_documentos_auto(self, session, num_processo):
        """
        Obtém os documentos necessários para um processo.

        Args:
            session (requests.Session): Sessão autenticada.
            num_processo (int): Número do processo.

        Returns:
            pd.DataFrame: DataFrame contendo os documentos.

        Raises:
            ValueError: Em caso de erro na requisição ou processamento dos dados.
        """
        payload = {
            "pCodigoClienteOperacional": "96011528",
            "pNumeroOcorrencia": num_processo,
            "pUploadPerfil": 2,
        }

        url = "https://portalintegracao.yelumseguros.com.br/LibertySinistroUpload/Upload/PUD_Default_Novo.aspx/CarregaDocumentosNecessarios"
        response = session.post(url, json=payload, headers=self.headers)

        if not response.ok:
            raise ValueError(
                f"Erro ao obter informações dos documentos do processo {num_processo}. "
                f"Status Code: {response.status_code}, Response: {response.text}"
            )

        try:
            json_data = response.json()['d']
            df = pd.DataFrame(json_data)

            # Excluir documentos sem id
            df = df[df['IDOnbase'] != 0]

            # Criar numeração para arquivos
            df['num_documento'] = df.groupby('NomeDocumento').cumcount() + 1

            # Filtrar colunas relevantes
            #df = df[["NomeDocumento", "CodigoTipoDocumento", "IDOnbase"]]

            return df
        
        except (ValueError, KeyError) as e:
            raise ValueError(f"Erro ao processar os dados do processo {num_processo}: {str(e)}")

    def adicionar_extensoes_auto(self, sessao, df, num_processo):
        """
        Adiciona extensões aos documentos com base no IDOnbase.

        Args:
            sessao (requests.Session): Sessão autenticada.
            df (pd.DataFrame): DataFrame contendo os documentos.
            num_processo (int): Número do processo.

        Returns:
            pd.DataFrame: DataFrame atualizado com as extensões.

        Raises:
            Exception: Em caso de erro durante o processamento.
        """
        url = "https://portalintegracao.yelumseguros.com.br/LibertySinistroUpload/Upload/PUD_Default_Novo.aspx/ReceberDocumentoOnBase"
        lista_extensoes = []

        for i, row in df.iterrows():
            payload = {
                "codDocumento": row['CodigoTipoDocumento'],
                "idOnBase": row['IDOnbase'],
                "pAqvGrd": False,
                "pCodigoClienteOperacional": "96011528",
                "pMaterializar": False,
                "pNumeroOcorrencia": num_processo,
                "pUploadPerfil": 2,
            }

            response = sessao.post(url, json=payload, headers=self.headers)

            if response.ok:
                try:
                    
                    link = response.json()['d']['Result']
                    extensao = self.identificar_extensao_permitida(link)
                    lista_extensoes.append(extensao)
                except Exception as e:
                    raise ValueError(f"Erro ao processar extensão: {str(e)}")
            else:
                raise ValueError(f"Erro na requisição para obter extensão. Response: {response.text}")

            time.sleep(2)

        df['extensoes'] = lista_extensoes
        return df
    
    def download_documentos_auto(self, sessao, df, num_processo):
        """
        Faz o download dos documentos processados.

        Args:
            sessao (requests.Session): Sessão autenticada.
            df (pd.DataFrame): DataFrame contendo os documentos.
            num_processo (int): Número do processo.

        Raises:
            Exception: Em caso de falhas no download.
        """
        url_download = "https://portalintegracao.yelumseguros.com.br/LibertySinistroUpload/file_upload/{}_api.{}"
        max_retries = 3
        backoff_factor = 60

        # Criar o diretório de saída
        output_dir = os.path.join("download", str(num_processo))
        os.makedirs(output_dir, exist_ok=True)

        try:
            for i, row in df.iterrows():
                tentativa = 0
                sucesso = False
                time.sleep(10)  # Tempo inicial de espera para evitar sobrecarga

                while tentativa < max_retries and not sucesso:
                    print(row['NomeDocumento'])
                    print(row['num_documento'])
                    print(tentativa)
                    time.sleep(backoff_factor * tentativa)  # Aplicar backoff exponencial
                    url_download_atualizado = url_download.format(row['IDOnbase'], row['extensoes'])

                    # Fazer a requisição para baixar o arquivo
                    response = sessao.get(url_download_atualizado, headers=self.headers)

                    # Verificar se o download foi bem-sucedido
                    if response.status_code == 200:
                        file_name = os.path.join(output_dir, f"{row['NomeDocumento']}_{row['num_documento']}.{row['extensoes']}")
                        with open(file_name, "wb") as file:
                            file.write(response.content)

                        sucesso = True
                    else:
                        tentativa += 1

                if not sucesso:
                    shutil.rmtree(output_dir, ignore_errors=True)
                    print(url_download.format(row['IDOnbase'], row['extensoes']))
                    raise ValueError(f"Problema no download dos arquivos do processo {num_processo}.")

        except Exception as e:
            # Certificar que a pasta será limpa em caso de erro inesperado
            shutil.rmtree(output_dir, ignore_errors=True)
            raise

    def obter_documentos_danos_eletricos(self, session, num_processo):
        """
        Obtém e processa os documentos relacionados a danos elétricos.

        Args:
            session (requests.Session): Sessão autenticada.
            num_processo (int): Número do processo para busca de documentos.

        Returns:
            pd.DataFrame: DataFrame contendo os documentos processados.

        Raises:
            ValueError: Se a resposta da API for inválida.
            KeyError: Se as colunas esperadas não estiverem presentes no JSON.
        """
        url = f"https://uploadsinistroresidenciabff.yelumseguros.com.br/tipodocumento/solicitados/2/1400/2/{num_processo}/96011528"

        response = session.get(url, headers=self.headers)
        if not response.ok:
            raise ValueError(
                f"Erro ao obter informações dos documentos do processo {num_processo}. "
                f"Status Code: {response.status_code}, Response: {response.text}"
            )

        try:
            json_data = response.json()
            df = pd.DataFrame(json_data)

            if 'documentosOcorrencia' not in df.columns:
                raise KeyError("A coluna 'documentosOcorrencia' não foi encontrada no JSON recebido.")

            # Explode a coluna documentosOcorrencia e processa os dados
            df_exploded = df.explode('documentosOcorrencia')
            df_exploded['descricao'] = df_exploded['descricao'].str.replace("/", "", regex=False)
            df_exploded['idonbase'] = df_exploded['documentosOcorrencia'].apply(
                lambda x: x.get('idOnbase', None)
            )
            df_exploded['num_documento'] = df_exploded.groupby('descricao').cumcount() + 1

            return df_exploded.reset_index(drop=True)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Erro ao processar os dados do processo {num_processo}: {str(e)}")


    def download_arquivos_danos_eletricos(self, num_processo, tipo_documento, id, descricao, numero_documentos):
        """
        Baixa um arquivo com base nos parâmetros fornecidos e salva localmente.

        Args:
            num_processo (int): Número do processo.
            tipo_documento (str): Tipo do documento (ex: 'pdf', 'jpg').
            id (str): Identificador único do documento.
            descricao (str): Descrição do documento.
            numero_documentos (int): Sequencial do documento.

        Raises:
            ValueError: Se a extensão não for permitida.
            Exception: Para outros erros durante o download.
        """
        try:
            # Construir a URL de download
            url = f"https://uploadsinistroresidenciabff.yelumseguros.com.br/tipoDocOcorrencia/exibir/{num_processo}/{tipo_documento}/2/{id}"
            
            # Realizar a requisição GET para obter o link de download
            response = requests.get(url)
            response.raise_for_status()
            link = response.json().get('message')
            
            if not link:
                raise ValueError("Link de download não encontrado na resposta da API.")

            # Obter o conteúdo do arquivo
            documento = requests.get(link).content

            # Verificar a extensão do arquivo
            tipo_extensao = self.identificar_extensao_permitida(link)

            # Criar o diretório 'output' se não existir
            output_dir = os.path.join(os.getcwd(), f"dados/{str(num_processo)}")
            os.makedirs(output_dir, exist_ok=True)

            # Criar o nome do arquivo
            nome_arquivo = f"{descricao}_{numero_documentos}.{tipo_extensao}"
            caminho_completo = os.path.join(output_dir, nome_arquivo)

            # Salvar o arquivo localmente
            with open(caminho_completo, 'wb') as arquivo:
                arquivo.write(documento)

        except requests.RequestException as err:
            print(f"Erro de requisição: {err}")
        except ValueError as err:
            print(f"Erro de validação: {err}")
        except Exception as err:
            print(f"Ocorreu um erro inesperado: {err}")
        finally:
            time.sleep(3)  # Aguardar entre downloads para evitar sobrecarga

