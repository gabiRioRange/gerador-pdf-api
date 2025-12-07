from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
import os
import shutil
import uuid

app = FastAPI(title="Gerador de Relatórios PDF - Secure & Advanced")

# Define o diretório base do projeto para evitar erros de "File Not Found"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def processar_relatorio(input_path, output_path, author_name):
    """
    Motor de processamento: ETL -> Visualização -> Renderização PDF
    """
    # 1. Leitura e Pré-processamento
    df = pd.read_excel(input_path)
    
    # Conversão de datas é crucial para análise temporal
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'])
    
    # 2. Cálculos de KPIs
    total_vendas = df['Valor'].sum()
    ticket_medio = df['Valor'].mean()
    
    if not df.empty:
        top_produto = df.groupby('Produto')['Valor'].sum().idxmax()
    else:
        top_produto = "N/A"
    
    def format_currency(val):
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # 3. Geração de Gráficos
    
    # --- Gráfico 1: Categorias (Barras) ---
    plt.figure(figsize=(10, 4))
    if not df.empty:
        # Pega as top 5 categorias para não poluir
        df.groupby('Categoria')['Valor'].sum().sort_values(ascending=True).tail(10).plot(kind='barh', color='#2c3e50')
    plt.title('Faturamento por Categoria (Top 10)')
    plt.xlabel('Total (R$)')
    plt.tight_layout()
    
    chart1_filename = f"chart_cat_{uuid.uuid4()}.png"
    chart1_path = os.path.join(BASE_DIR, chart1_filename)
    plt.savefig(chart1_path)
    plt.close()

    # --- Gráfico 2: Evolução Temporal (Linha) ---
    chart2_path = None
    if 'Data' in df.columns and not df.empty:
        # Agrupa por Semana ('W') para suavizar o gráfico
        vendas_tempo = df.set_index('Data').resample('W')['Valor'].sum()
        
        plt.figure(figsize=(10, 4))
        plt.plot(vendas_tempo.index, vendas_tempo.values, marker='o', linestyle='-', color='#27ae60', linewidth=2)
        plt.title('Tendência de Vendas (Semanal)')
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart2_filename = f"chart_time_{uuid.uuid4()}.png"
        chart2_path = os.path.join(BASE_DIR, chart2_filename)
        plt.savefig(chart2_path)
        plt.close()

    # 4. Renderização do Template
    env = Environment(loader=FileSystemLoader(BASE_DIR))
    template = env.get_template('template.html')
    
    tabela_html = df.to_html(index=False, classes='table-content', float_format=lambda x: format_currency(x) if isinstance(x, float) else x)

    html_out = template.render(
        titulo="Relatório Executivo de Vendas",
        autor=author_name,
        data_geracao=datetime.now().strftime("%d/%m/%Y às %H:%M"),
        kpi_total=format_currency(total_vendas),
        kpi_media=format_currency(ticket_medio),
        kpi_top=top_produto,
        tabela_html=tabela_html,
        grafico_barras=f"file://{chart1_path}",
        grafico_temporal=f"file://{chart2_path}" if chart2_path else ""
    )

    # 5. Geração do PDF
    HTML(string=html_content_fixo(html_out), base_url=BASE_DIR).write_pdf(output_path)
    
    # Limpeza dos gráficos temporários
    if os.path.exists(chart1_path): os.remove(chart1_path)
    if chart2_path and os.path.exists(chart2_path): os.remove(chart2_path)

def html_content_fixo(html_content):
    return html_content

def limpar_arquivos(files_to_remove):
    """Remove arquivos temporários após o envio"""
    for f in files_to_remove:
        try:
            if os.path.exists(f): os.remove(f)
        except: pass

# --- ENDPOINTS ---

@app.post("/gerar-pdf/")
async def gerar_pdf_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...), autor: str = "Gabriel"):
    
    # 1. Validação de Segurança (Blue Team Tactic)
    # Apenas aceita arquivos MIME Type de Excel real
    mime_valido = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    if file.content_type != mime_valido:
        raise HTTPException(status_code=415, detail="Tipo de arquivo inválido. Envie apenas .xlsx.")

    unique_id = str(uuid.uuid4())
    temp_input = os.path.join(BASE_DIR, f"temp_input_{unique_id}.xlsx")
    temp_output = os.path.join(BASE_DIR, f"relatorio_{unique_id}.pdf")
    
    # 2. Salva Input
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Processa
    try:
        processar_relatorio(temp_input, temp_output, autor)
    except Exception as e:
        if os.path.exists(temp_input): os.remove(temp_input)
        return {"erro": f"Erro interno: {str(e)}"}

    # 4. Agenda Limpeza
    background_tasks.add_task(limpar_arquivos, [temp_input, temp_output])

    # 5. Retorna
    return FileResponse(temp_output, media_type='application/pdf', filename=f"Relatorio_{autor}.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)