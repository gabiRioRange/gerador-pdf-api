# 📊 Gerador de Relatórios Financeiros Automatizado (PDF)

> Um microserviço robusto que transforma dados brutos de Excel em relatórios PDF executivos, utilizando Python, Pandas e Docker.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Security](https://img.shields.io/badge/Security-MIME%20Validation-red)

## 📝 Visão Geral

Este projeto é uma API RESTful desenvolvida para automatizar a criação de relatórios gerenciais. O sistema recebe arquivos Excel (`.xlsx`), processa os dados utilizando técnicas de **ETL** (Extract, Transform, Load), calcula KPIs financeiros e gera visualizações gráficas (Matplotlib) incorporadas em um layout PDF profissional (WeasyPrint).

O foco do projeto foi criar uma solução escalável, containerizada e segura, pronta para implantação em nuvem.

## 🚀 Funcionalidades Principais

* **Processamento de Dados (Data Science):**
    * Cálculo automático de Faturamento Total, Ticket Médio e Top Produtos.
    * Análise temporal (tendência de vendas semanais).
    * Geração dinâmica de gráficos de barras e linhas.
* **Engenharia de Backend:**
    * API assíncrona com **FastAPI**.
    * Gerenciamento de tarefas em segundo plano (`BackgroundTasks`) para limpeza de arquivos temporários.
    * Validação de Segurança (verificação rigorosa de MIME Type para evitar uploads maliciosos).
* **Visualização:**
    * Renderização de templates HTML/CSS com **Jinja2**.
    * Layout responsivo para impressão (paginação inteligente, cabeçalhos repetidos).
* **DevOps:**
    * Containerização completa com **Docker** (imagem Linux Debian-slim otimizada).

## 🛠️ Tech Stack

* **Linguagem:** Python 3.9
* **Web Framework:** FastAPI + Uvicorn
* **Análise de Dados:** Pandas
* **Visualização:** Matplotlib
* **Motor de PDF:** WeasyPrint + Jinja2
* **Infraestrutura:** Docker

## ⚙️ Como Executar

### Opção 1: Via Docker (Recomendado)

O projeto já possui um `Dockerfile` configurado para resolver todas as dependências de sistema (GTK/Pango).

1.  **Construa a imagem:**
    ```bash
    docker build -t gerador-pdf .
    ```

2.  **Rode o container:**
    ```bash
    docker run -p 8000:8000 gerador-pdf
    ```

3.  Acesse a documentação interativa (Swagger UI) em: `http://localhost:8000/docs`

### Opção 2: Localmente (Windows/Linux)

1.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: No Windows, pode ser necessário instalar o GTK3 Runtime separadamente para o WeasyPrint funcionar).*

2.  Execute o servidor:
    ```bash
    python api.py
    ```

## 📸 Demonstração
![Swagger UI](Captura de tela 2025-11-01 055658.png)
![Exemplo PDF](Relatorio_Gabriel.pdf)

## 📂 Estrutura do Projeto

```text
/
├── api.py             # Aplicação principal (Endpoints e Lógica de Negócio)
├── template.html      # Layout do relatório (HTML + CSS Jinja2)
├── Dockerfile         # Configuração da imagem Docker
├── requirements.txt   # Dependências do Python
└── main.py            # (Legado) Versão script CLI para testes locais
