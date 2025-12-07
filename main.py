import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
import os

class RelatorioPDF:
    def __init__(self, input_file, output_pdf, autor="Sistema"):
        self.input_file = input_file
        self.output_pdf = output_pdf
        self.autor = autor
        self.data = None
        
        # --- CORREÇÃO DE DIRETÓRIOS ---
        # 1. Descobre onde o main.py está salvo no disco
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = base_dir
        
        # 2. Se o arquivo de entrada não tiver caminho completo, usa a pasta do script
        if not os.path.isabs(self.input_file):
             self.input_file = os.path.join(base_dir, self.input_file)
        
        # 3. Define onde salvar o gráfico temporário
        self.chart_filename = os.path.join(base_dir, 'temp_chart.png')

        # 4. (Opcional) Garante que o PDF final saia na mesma pasta também
        if not os.path.isabs(self.output_pdf):
            self.output_pdf = os.path.join(base_dir, self.output_pdf)
             
        self.chart_filename = os.path.join(base_dir, 'temp_chart.png')

    def carregar_dados(self):
        """Etapa 1: Leitura e Limpeza (ETL)"""
        print(f"[1/5] Lendo arquivo {self.input_file}...")
        try:
            # Detecta se é CSV ou Excel
            if self.input_file.endswith('.csv'):
                self.data = pd.read_csv(self.input_file)
            else:
                self.data = pd.read_excel(self.input_file)
            
            # Limpeza básica (exemplo: remover linhas vazias)
            self.data.dropna(inplace=True)
            print("Dados carregados com sucesso.")
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
            exit()

    def gerar_grafico(self):
        """Etapa 2: Gerar Gráfico com Matplotlib"""
        print("[2/5] Gerando gráficos...")
        
        # Exemplo: Agrupar vendas por Categoria (ajuste conforme seus dados)
        # Assumindo colunas 'Categoria' e 'Valor'
        if 'Categoria' in self.data.columns and 'Valor' in self.data.columns:
            df_grouped = self.data.groupby('Categoria')['Valor'].sum()
            
            plt.figure(figsize=(8, 4))
            df_grouped.plot(kind='bar', color='#4a90e2')
            plt.title('Total de Vendas por Categoria')
            plt.xlabel('Categoria')
            plt.ylabel('Valor (R$)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.savefig(self.chart_filename)
            plt.close()
            return os.path.abspath(self.chart_filename)
        else:
            print("Colunas 'Categoria' ou 'Valor' não encontradas para o gráfico. Gerando dummy.")
            return None

    def renderizar_html(self, chart_path):
        """Etapa 3: Popular o Template Jinja2"""
        print("[3/5] Renderizando template HTML...")
        
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template('template.html')
        
        # Converter DataFrame para Tabela HTML (com classes CSS se quiser)
        # Formatando valores monetários se necessário
        tabela_html = self.data.to_html(index=False, classes='table', border=0)
        
        html_out = template.render(
            titulo="Relatório de Vendas Mensal",
            data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M"),
            autor=self.autor,
            tabela_html=tabela_html,
            grafico_path=f"file://{chart_path}" if chart_path else ""
        )
        return html_out

    def gerar_pdf(self, html_content):
        """Etapa 4: Converter HTML para PDF"""
        print("[4/5] Convertendo para PDF...")
        HTML(string=html_content, base_url=self.template_dir).write_pdf(self.output_pdf)

    def limpar_temporarios(self):
        """Etapa 5: Limpeza"""
        if os.path.exists(self.chart_filename):
            os.remove(self.chart_filename)
        print(f"[5/5] Concluído! Arquivo salvo em: {self.output_pdf}")

    def executar(self):
        self.carregar_dados()
        chart_path = self.gerar_grafico()
        html_content = self.renderizar_html(chart_path)
        self.gerar_pdf(html_content)
        self.limpar_temporarios()

# --- Simulação de uso ---
if __name__ == "__main__":
    
    # Vamos criar um Excel dummy para você testar agora mesmo
    print("Criando arquivo Excel de teste...")
    df_teste = pd.DataFrame({
        'Data': pd.date_range(start='2023-01-01', periods=5, freq='D'),
        'Produto': ['Teclado', 'Mouse', 'Monitor', 'Cadeira', 'Headset'],
        'Categoria': ['Periféricos', 'Periféricos', 'Telas', 'Móveis', 'Áudio'],
        'Valor': [150.00, 80.50, 1200.00, 850.00, 250.00]
    })
    df_teste.to_excel('vendas_mock.xlsx', index=False)

    # Instancia e roda o gerador
    app = RelatorioPDF(input_file='vendas_mock.xlsx', output_pdf='Relatorio_Final.pdf', autor="Gabriel")
    app.executar()