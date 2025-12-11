from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
import os
import shutil
import uuid
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse # <--- Adicione HTMLResponse

# --- CONFIGURAÇÃO INICIAL ---

# 1. Carrega as senhas do arquivo .env
load_dotenv()

app = FastAPI(title="Gerador de Relatórios PDF - Enterprise Edition")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Configuração do Servidor de Email (Lê do .env)
# Verifica se as variáveis existem para evitar erro silencioso
if not os.getenv("MAIL_USERNAME"):
    print("⚠️ AVISO: Configurações de e-mail não encontradas no .env")

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "remetente@exemplo.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- LÓGICA DE NEGÓCIO (DATA SCIENCE & PDF) ---

def processar_relatorio(input_path, output_path, author_name):
    """Lê Excel, cria gráficos e gera PDF."""
    
    # Leitura
    df = pd.read_excel(input_path)
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'])
    
    # KPIs
    total_vendas = df['Valor'].sum()
    ticket_medio = df['Valor'].mean()
    top_produto = df.groupby('Produto')['Valor'].sum().idxmax() if not df.empty else "N/A"
    
    def format_currency(val):
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Gráfico 1: Barras
    plt.figure(figsize=(10, 4))
    if not df.empty:
        df.groupby('Categoria')['Valor'].sum().sort_values().tail(10).plot(kind='barh', color='#2c3e50')
    plt.title('Top Categorias')
    plt.tight_layout()
    chart1_name = f"chart_cat_{uuid.uuid4()}.png"
    chart1_path = os.path.join(BASE_DIR, chart1_name)
    plt.savefig(chart1_path)
    plt.close()

    # Gráfico 2: Temporal
    chart2_path = None
    if 'Data' in df.columns and not df.empty:
        vendas_tempo = df.set_index('Data').resample('W')['Valor'].sum()
        plt.figure(figsize=(10, 4))
        plt.plot(vendas_tempo.index, vendas_tempo.values, marker='o', color='#27ae60')
        plt.title('Evolução Semanal')
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        chart2_name = f"chart_time_{uuid.uuid4()}.png"
        chart2_path = os.path.join(BASE_DIR, chart2_name)
        plt.savefig(chart2_path)
        plt.close()

    # HTML Template
    env = Environment(loader=FileSystemLoader(BASE_DIR))
    template = env.get_template('template.html')
    tabela_html = df.to_html(index=False, classes='table-content', float_format=lambda x: format_currency(x) if isinstance(x, float) else x)

    html_out = template.render(
        titulo="Relatório Financeiro",
        autor=author_name,
        data_geracao=datetime.now().strftime("%d/%m/%Y"),
        kpi_total=format_currency(total_vendas),
        kpi_media=format_currency(ticket_medio),
        kpi_top=top_produto,
        tabela_html=tabela_html,
        grafico_barras=f"file://{chart1_path}",
        grafico_temporal=f"file://{chart2_path}" if chart2_path else ""
    )

    # Gera PDF
    HTML(string=html_content_fixo(html_out), base_url=BASE_DIR).write_pdf(output_path)
    
    # Limpa gráficos
    if os.path.exists(chart1_path): os.remove(chart1_path)
    if chart2_path and os.path.exists(chart2_path): os.remove(chart2_path)

def html_content_fixo(html_content):
    return html_content

def limpar_arquivos(files):
    for f in files:
        try:
            if os.path.exists(f): os.remove(f)
        except: pass

# --- ENDPOINTS DA API ---

app = FastAPI(title="Gerador de Relatórios PDF - Enterprise Edition")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- NOVO: ROTA PARA A INTERFACE (FRONTEND) ---
@app.get("/", response_class=HTMLResponse)
async def home():
    """Renderiza a página HTML da interface."""
    path_ui = os.path.join(BASE_DIR, "ui.html")
    with open(path_ui, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/gerar-pdf-download/")
async def gerar_pdf_download(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    autor: str = "Gabriel"
):
    """Gera o PDF e faz o download direto no navegador."""
    valida_excel(file)
    
    ids = str(uuid.uuid4())
    temp_in = os.path.join(BASE_DIR, f"temp_{ids}.xlsx")
    temp_out = os.path.join(BASE_DIR, f"relatorio_{ids}.pdf")

    try:
        with open(temp_in, "wb") as b:
            shutil.copyfileobj(file.file, b)
        
        processar_relatorio(temp_in, temp_out, autor)
        
        background_tasks.add_task(limpar_arquivos, [temp_in, temp_out])
        return FileResponse(temp_out, filename=f"Relatorio_{autor}.pdf")
    except Exception as e:
        limpar_arquivos([temp_in])
        return JSONResponse(status_code=500, content={"erro": str(e)})


@app.post("/gerar-pdf-email/")
async def gerar_pdf_email(
    background_tasks: BackgroundTasks,
    email_destino: EmailStr = Form(...),  # Recebe o email via formulário
    file: UploadFile = File(...),
    autor: str = Form("Gabriel")
):
    """Gera o PDF e envia para o e-mail informado."""
    valida_excel(file)
    
    ids = str(uuid.uuid4())
    temp_in = os.path.join(BASE_DIR, f"temp_{ids}.xlsx")
    temp_out = os.path.join(BASE_DIR, f"relatorio_{ids}.pdf")

    try:
        # 1. Salva e Processa
        with open(temp_in, "wb") as b:
            shutil.copyfileobj(file.file, b)
        
        processar_relatorio(temp_in, temp_out, autor)

        # 2. Prepara o E-mail
        message = MessageSchema(
            subject=f"Relatório Financeiro - {autor}",
            recipients=[email_destino],
            body=f"Olá,\n\nSegue em anexo o relatório gerado automaticamente.\n\nAtt,\nSistema {autor}",
            subtype=MessageType.plain,
            attachments=[temp_out]
        )

        # 3. Envia (usando FastAPI-Mail)
        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)
        
        # 4. Limpa arquivos DEPOIS de enviar
        background_tasks.add_task(limpar_arquivos, [temp_in, temp_out])

        return {"status": "sucesso", "mensagem": f"Relatório enviado para {email_destino}"}

    except Exception as e:
        limpar_arquivos([temp_in, temp_out])
        return JSONResponse(status_code=500, content={"erro": str(e)})

def valida_excel(file: UploadFile):
    if "spreadsheet" not in file.content_type and "excel" not in file.content_type:
         raise HTTPException(status_code=415, detail="Arquivo inválido. Envie um .xlsx")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)