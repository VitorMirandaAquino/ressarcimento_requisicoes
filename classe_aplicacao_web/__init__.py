import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
from classe_requisicoes import RequisicoesLiberty
from classe_navegador import LibertyAutomation
from classe_auto import Procedimentos as Procedimentos_auto

import time

class WebApp:
    def __init__(self):
        self.login_credencial = None
        self.senha_credencial = None
        self.tipo_processo = None
        self.caminho = r"C:\Users\Vitor\Documents\Repositórios\automação\ressarcimento_requisicoes\dados"

    def run(self):
        st.set_page_config(
            page_title="Download de documentos",
            page_icon=":page_facing_up:"
        )

        st.title("Download de documentos :page_facing_up:")
        st.header("Configuração para download")
        self.get_credenciais()
        self.select_tipo_processo()

        if self.login_credencial and self.senha_credencial and self.tipo_processo:
            if self.tipo_processo == "AUTO":
                self.processos_auto_pipeline()
            elif self.tipo_processo == "DANOS ELÉTRICOS":
                self.processos_danos_eletricos_pipeline()


    def get_credenciais(self):
        self.login_credencial = st.text_input("Digite o login do site:")
        self.senha_credencial = st.text_input("Digite a senha do site:", type="password")

    def select_caminho(self):
        st.subheader("Caminho para salvar")
        st.write(self.caminho)

    def select_tipo_processo(self):
        st.subheader("Tipo de Processo")
        self.tipo_processo = st.selectbox("Você deseja baixar as informações de qual tipo de Processo?", ("AUTO", "DANOS ELÉTRICOS"))

    def create_zip(self, folder_path, output_filename):
        with zipfile.ZipFile(output_filename, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file),
                               os.path.join(folder_path, '..')))
                    
    def delete_files_and_folders_in_directory(self, directory_path):
        # Remove todos os arquivos e subpastas na pasta
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                shutil.rmtree(os.path.join(root, dir))

    def processos_auto_pipeline(self):
        st.subheader("Orçamento")
        opcao_orcamento = st.selectbox("Você deseja baixar as informações do orçamento?", ("Não", "Sim"))

        st.subheader("Processo")
        excel_file = st.file_uploader('Insira um arquivo com o número dos processos', type='xlsx')

        if excel_file is not None:
            df_processo = pd.read_excel(excel_file)
            df_processo_show = df_processo.copy()
            df_processo_show['Processo'] = df_processo_show['Processo'].astype('str')

            st.subheader("Procedimento")

            botao_iniciar = st.button("Iniciar Procedimento")

            #self.delete_files_and_folders_in_directory("dados")

            if botao_iniciar:
                lista_docs_baixados = []
                lista_docs_problema = []
                with st.status("Fazendo download dos arquivos ..."):
                    for processo in df_processo.Processo:
                        st.write(f'**Iniciando procedimento para o processo: {processo}**')
                        navegador = LibertyAutomation(self.caminho, processo)  # Instanciando a classe LibertyAutomation
                        #navegador.configurar_navegador_para_download(self.caminho, processo)
                        st.write("Configuração concluída")
                        navegador.realizar_login_liberty(self.login_credencial, self.senha_credencial)
                        st.write("Login concluído.")
                        navegador.localizar_processo()
                        
                        procedimentos = Procedimentos_auto(navegador)  # Instanciando a classe Procedimentos

                        if opcao_orcamento == "Sim":
                            try:
                                procedimentos.baixar_orcamento()
                                st.write("Download do orçamento concluído.")
                            except:
                                navegador.navegador.close()
                                lista_docs_problema.append(processo)
                                st.write("Problema no download do orçamento.")
                                navegador = LibertyAutomation(self.caminho, processo)  # Reinstancia o navegador

                                navegador.realizar_login_liberty(self.login_credencial, self.senha_credencial)
                                navegador.localizar_processo()
                                procedimentos = Procedimentos_auto(navegador)

                        documentos_baixados, flag_problema = procedimentos.downloads()
                        if flag_problema:
                            lista_docs_problema.append(processo)
                        lista_docs_baixados.append(documentos_baixados)
                        st.write("Download dos documentos concluído.")

                st.subheader("Geral")
                df_processo_show['Documentos Baixados'] = lista_docs_baixados
                st.table(df_processo_show)

                for doc in lista_docs_problema:
                    st.warning(f'Problema no download no processo {str(doc)}', icon="⚠️")

                st.button("Reiniciar Procedimento")


    def processos_auto_pipeline_requisicoes(self):
        st.subheader("Orçamento")
        opcao_orcamento = st.selectbox("Você deseja baixar as informações do orçamento?", ("Não", "Sim"))

        st.subheader("Processo")
        excel_file = st.file_uploader('Insira um arquivo com o número dos processos', type='xlsx')

        if excel_file is not None:
            df_processo = pd.read_excel(excel_file)
            df_processo_show = df_processo.copy()
            df_processo_show['Processo'] = df_processo_show['Processo'].astype('str')

            st.subheader("Procedimento")

            botao_iniciar = st.button("Iniciar Procedimento")

            if botao_iniciar:
                with st.status("Fazendo download dos arquivos ..."):
                    for processo in df_processo.Processo:
                        st.write(f'**Iniciando procedimento para o processo: {processo}**')
                        requisicoes = RequisicoesLiberty(login=self.login_credencial, senha=self.senha_credencial)
                        st.write("Configuração concluída")
                        sessao = requisicoes.fazer_login()
                        time.sleep(3)
                        st.write("Login concluído.")

                        if opcao_orcamento == "Sim":
                            try:
                                st.write("Download do orçamento concluído.")
                            except Exception as e:
                                st.write("Problema no download do orçamento.")
                                raise e
                        
                        documentos = requisicoes.obter_documentos_auto(sessao, processo)
                        st.write("Identificação de documentos para download concluída")
                        time.sleep(2)
                        documentos = requisicoes.adicionar_extensoes_auto(sessao, documentos, processo)
                        st.write("Adição de extensões dos documentos concluída.")
                        time.sleep(2)
                        try:
                            requisicoes.download_documentos_auto(sessao, documentos, processo)
                            st.write("Download dos documentos concluído.")
                        except Exception as e:
                            st.warning(f'Problema no download no processo {str(processo)}', icon="⚠️")

                st.button("Reiniciar Procedimento")


    def processos_danos_eletricos_pipeline(self):

        st.subheader("Processo")
        excel_file = st.file_uploader('Insira um arquivo com o número dos processos', type='xlsx')

        if excel_file is not None:
            df_processo = pd.read_excel(excel_file)
            df_processo_show = df_processo.copy()
            df_processo_show['Processo'] = df_processo_show['Processo'].astype('str')

            st.subheader("Procedimento")

            botao_iniciar = st.button("Iniciar Procedimento")
            

            if botao_iniciar:
                with st.status("Fazendo download dos arquivos ..."):
                    for processo in df_processo.Processo:
                        st.write(f'**Iniciando procedimento para o processo: {processo}**'),
                        requisicoes = RequisicoesLiberty(login=self.login_credencial, senha=self.senha_credencial)
                        st.write("Configuração concluída")
                        sessao = requisicoes.fazer_login()
                        time.sleep(3)
                        st.write("Login concluído.")
                        documentos = requisicoes.obter_documentos_danos_eletricos(sessao, processo)
                        st.write("Identificação de documentos para download concluída")
                        for _, row in documentos.iterrows():
                            requisicoes.download_arquivos_danos_eletricos(processo, 
                                                         row['codigo'], 
                                                         row['idonbase'], 
                                                         row['descricao'], 
                                                         row['num_documento'])
                            st.write(f"Download do {row['num_documento']}º documento de tipo: {row['descricao']}")
                        st.write("Download dos documentos concluído.")

                st.button("Reiniciar Procedimento")
