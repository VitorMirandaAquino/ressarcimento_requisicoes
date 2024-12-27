from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, ElementClickInterceptedException
import time
import os



class LibertyAutomation:
    def __init__(self, caminho, num_processo):
        self.caminho = caminho
        self.num_processo = num_processo
        #self.navegador = self.configurar_navegador_para_download()
        self.navegador = self.configurar_navegador_para_download_local()

    def configurar_navegador_para_download(self):
        servico = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Define o diretório de download
        download_directory = os.path.join(self.caminho, str(self.num_processo))
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)
        
        prefs = {
            "download.default_directory": download_directory,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.images": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        navegador = webdriver.Chrome(service=servico, options=chrome_options)
        return navegador
    
    def configurar_navegador_para_download_local(self):
        #servico = Service(ChromeDriverManager().install())
        chrome_install = ChromeDriverManager().install()

        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver.exe")

        servico = ChromeService(chromedriver_path)
        chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument("--headless")
        
        # Define o diretório de download
        download_directory = os.path.join(self.caminho, str(self.num_processo))
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)
        
        prefs = {
            "download.default_directory": download_directory,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.images": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        navegador = webdriver.Chrome(service=servico, options=chrome_options)
        return navegador    

    def realizar_login_liberty(self, login, senha):
        self.navegador.get("https://ressarcimentofianca.yelumseguros.com.br/login")
        self.navegador.maximize_window()
        self.enviar_valor_para_campo(By.XPATH, '/html/body/app-root/app-login-prestador/div[2]/div/div/div[2]/div[2]/div/div[1]/input', login)
        self.enviar_valor_para_campo(By.XPATH, '/html/body/app-root/app-login-prestador/div[2]/div/div/div[2]/div[2]/div/div[2]/input', senha)
        self.clicar_botao(By.XPATH, '/html/body/app-root/app-login-prestador/div[2]/div/div/div[2]/div[2]/div/div[3]/input')

    def localizar_processo(self):
        self.enviar_valor_para_campo(By.XPATH, '//*[@id="pesquisa"]', self.num_processo)
        self.clicar_botao(By.XPATH, '/html/body/app-root/app-pesquisa/div[2]/div[3]/div[2]/button[1]')

    def clicar_botao(self, by, valor):
        botao = WebDriverWait(self.navegador, 20).until(
            EC.element_to_be_clickable((by, valor))
        )

        botao.click()

    def clicar_botao_download(self, by, valor):
        botao = WebDriverWait(self.navegador, 20).until(
            EC.element_to_be_clickable((by, valor))
        )

        self.executar_script("arguments[0].scrollIntoView(true);", botao)
        
        try:
            botao.click()
        except ElementClickInterceptedException:
            time.sleep(1)
            self.executar_script("arguments[0].scrollIntoView(true);", botao)
            botao.click()
        
    def rolar_pagina(self):

        body = self.navegador.find_element(By.TAG_NAME, 'body')  
        body.send_keys(Keys.PAGE_DOWN)  # Scroll down

    def enviar_valor_para_campo(self, by, valor, texto):
        campo = WebDriverWait(self.navegador, 10).until(
            EC.presence_of_element_located((by, valor))
        )

        campo.send_keys(texto)

    def mudar_para_aba(self, numero_aba):
        WebDriverWait(self.navegador, 10).until(
            EC.number_of_windows_to_be(numero_aba + 1)
        )
        new_window_handle = self.navegador.window_handles[numero_aba]
        self.navegador.switch_to.window(new_window_handle)

    def fechar_aba(self):
        self.navegador.close()
        WebDriverWait(self.navegador, 10).until(
            EC.number_of_windows_to_be(len(self.navegador.window_handles))
        )
        new_window_handle = self.navegador.window_handles[-1]
        self.navegador.switch_to.window(new_window_handle)

    def executar_script(self, script , element):
        self.navegador.execute_script(script, element)