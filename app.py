import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json
from google.oauth2.service_account import Credentials
import gspread
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# CONFIGURAÇÃO DA PÁGINA WEB
st.set_page_config(page_title="Gerador de Relatórios", page_icon="📊", layout="centered")

st.title("📊 Gerador Automatizado de Relatórios")
st.write("O sistema está conectado diretamente ao Google Drive. Clique no botão abaixo para gerar o relatório atualizado.")

@st.cache_data(ttl=60)
def carregar_dados_do_drive():
    # Coleta os dados limpos direto dos campos individuais dos Secrets
    credenciais_dict = {
        "type": "service_account",
        "project_id": st.secrets["google_drive"]["project_id"],
        "private_key": st.secrets["google_drive"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["google_drive"]["client_email"],
        "token_uri": "https://googleapis.com"
    }
    
    escopos = ["https://googleapis.com", "https://googleapis.com"]
    credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente_gspread = gspread.authorize(credenciais)
    
    # URL injetada diretamente no comando de abertura para evitar o erro NoValidUrlKeyFound
    #url_real = "https://google.com"
    #planilha = cliente_gspread.open_by_url(url_real)
    #aba_principal = planilha.get_worksheet(0)
    #dados = aba_principal.get_all_records()

    # Usando a CHAVE pura para o gspread nunca mais dar erro de URL
    CHAVE_DA_PLANILHA = "15tPcfqlwmhFG70ZKpSBcEHlQECG6PgB1NEh_eSLY69l"
    planilha = cliente_gspread.open_by_key(CHAVE_DA_PLANILHA)
    aba_principal = planilha.get_worksheet(0)
    dados = aba_principal.get_all_records()
    
    return pd.DataFrame(dados)
    
    
    return pd.DataFrame(dados)

try:
    df_original = carregar_dados_do_drive()
    
    # Padroniza os nomes das colunas vindas do Google Sheets
    df_original.columns = df_original.columns.str.lower().str.strip()
    
    # Correção para ler a coluna mesmo que ela tenha acento na planilha
    if 'endereço' in df_original.columns:
        df_original = df_original.rename(columns={'endereço': 'endereco'})
    
    # Aplica os filtros e ordenações solicitados
    df_original['endereco'] = df_original['endereco'].astype(str).str.strip()
    df = df_original[df_original['endereco'] == '01010333 - ULTRABOOK/NOTEBOOK / TABLET']
    df = df.sort_values(by='responsavel', ascending=True)
    
    st.info(f"Conexão com o Google Drive ativa. Encontrados {len(df)} registros atualizados.")
    
    # CONSTRUÇÃO DO PDF EM MEMÓRIA
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22,
        textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=10
    )
    normal_style = styles['Normal']
    
    data_hora_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Paragraph("RELATÓRIO DE INVENTÁRIO (SISTEMA NUVEM DIRETO)", title_style))
    story.append(Paragraph("<b>Filtro por Endereço:</b> 01010333 - ULTRABOOK/NOTEBOOK / TABLET", normal_style))
    story.append(Paragraph(f"<b>Total de Itens Encontrados:</b> {len(df)}", normal_style))
    story.append(Paragraph(f"<b>Data de Emissão:</b> {data_hora_emissao}", normal_style))
    story.append(Spacer(1, 15))
    
    col_widths = [60, 55, 95, 182, 160]
    table_data = [['Patrimônio', 'Marca', 'Modelo', 'Unidade Administrativa', 'Responsável']]
    
    ultimo_responsavel = None
    linhas_com_borda_inferior = []
    contador_linha = 1
    
    for _, row in df.iterrows():
        responsavel_atual = str(row['responsavel'])
        if ultimo_responsavel is not None and responsavel_atual != ultimo_responsavel:
            linhas_com_borda_inferior.append(contador_linha - 1)
            
        table_data.append([
            str(row['patrimonio']),
            Paragraph(str(row['marca']), normal_style),
            Paragraph(str(row['modelo']), normal_style),
            Paragraph(str(row['unidade_administrativa']), normal_style),
            Paragraph(responsavel_atual, normal_style)
        ])
        ultimo_responsavel = responsavel_atual
        contador_linha += 1
        
    estilo_tabela = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]
    
    for linha_idx in linhas_com_borda_inferior:
        estilo_tabela.append(('LINEBELOW', (0, linha_idx), (-1, linha_idx), 2.0, colors.HexColor("#1A365D")))
        
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(estilo_tabela))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    
    st.download_button(
        label="📥 Baixar Relatório Atualizado em PDF",
        data=buffer,
        file_name="relatorio_inventario_ultrabooks.pdf",
        mime="application/pdf",
        use_container_width=True
    )

#except Exception as e:
#    st.error(f"Erro na conexão ou na estrutura dos dados. Certifique-se de que a planilha foi compartilhada com o robô. Detalhes: {e}")

except Exception as e:
    # Este comando vai exibir o erro técnico real em uma caixa vermelha detalhada
    st.exception(e)
