import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException
from classe_navegador import LibertyAutomation

class Procedimentos:
    def __init__(self, liberty_automation: LibertyAutomation):
        self.liberty_automation = liberty_automation

    def baixar_orcamento(self):
        navegador = self.liberty_automation.navegador
        
        time.sleep(7)
        self.liberty_automation.clicar_botao(By.XPATH, '/html/body/app-root/app-ressarcimento/app-footer/footer/button[4]')

        time.sleep(5)
        self.liberty_automation.mudar_para_aba(1)

        self.liberty_automation.clicar_botao(By.XPATH, '//*[@id="budget_report"]/div/div[2]/a/center')

        self.liberty_automation.mudar_para_aba(2)

        self.liberty_automation.clicar_botao(By.XPATH, '//*[@id="btn_pdf_report"]')

        time.sleep(8)
        self.liberty_automation.fechar_aba()

        self.liberty_automation.mudar_para_aba(1)

        self.liberty_automation.clicar_botao(By.XPATH, '//*[@id="photos_menu"]')

        time.sleep(5)
        self.liberty_automation.clicar_botao(By.XPATH, '//*[@id="budgeting-photos-content"]/div[1]/div[2]/div/label')

        self.liberty_automation.clicar_botao(By.XPATH, '//*[@id="budgeting-photos-print"]/div/a[2]')

        time.sleep(8)
        self.liberty_automation.fechar_aba()

        self.liberty_automation.mudar_para_aba(0)

        return navegador

    def downloads(self):
        navegador = self.liberty_automation.navegador

        # Indo para o site com os arquivos
        self.liberty_automation.clicar_botao(By.XPATH, '/html/body/app-root/app-ressarcimento/app-footer/footer/button[6]')
        
        # Mudando para aba com os documentos
        self.liberty_automation.mudar_para_aba(1)

        time.sleep(10)

        documentos_baixados = 0
        flag_problema = False
        tentativas = 0
        
        for i in range(2, 20):
            time.sleep(3)
            element_xpath = f'//*[@id="documento-necessario"]/div[{i}]/div[2]/div/div'


            try:
                element = WebDriverWait(navegador, 10).until(
                    EC.element_to_be_clickable((By.XPATH, element_xpath))
                )
                self.liberty_automation.executar_script("arguments[0].scrollIntoView(true);", element)
                element.click()
                documentos_baixados += 1
            except Exception as e:
                tentativas = tentativas + 1
                if tentativas > 2:
                    break

        time.sleep(2)
        navegador.quit()

        return documentos_baixados, flag_problema