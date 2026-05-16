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

# LINK DA SUA PLANILHA GOOGLE (Substitua pelo link real da sua planilha)
URL_DA_PLANILHA = "https://docs.google.com/spreadsheets/d/15tPcfqlwmhFG70ZKpSBcEHlQECG6PgB1NEh_eSLY69I/edit?gid=865940462#gid=865940462"

@st.cache_data(ttl=600) # Mantém os dados em cache por 10 minutos para ficar rápido
def carregar_dados_do_drive():
    # Recupera a chave secreta que você salvou no painel do Streamlit
    info_chave = st.secrets["gspread"]["service_account"]
    escopos = ["https://googleapis.com", "https://googleapis.com"]
    
    # Conecta usando a biblioteca oficial do Google
    credenciais = Credentials.from_service_account_info(json.loads(info_chave), scopes=escopos)
    cliente_gspread = gspread.authorize(credenciais)
    
    # Abre a planilha pelo link e captura todos os dados da primeira aba
    planilha = cliente_gspread.open_by_url(URL_DA_PLANILHA)
    aba_principal = planilha.get_worksheet(0)
    dados = aba_principal.get_all_records()
    
    return pd.DataFrame(dados)

try:
    # Executa a busca automática nos bastidores
    df_original = carregar_dados_do_drive()
    
    # Padronizar nomes de colunas
    df_original.columns = df_original.columns.str.lower().str.strip()
    
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
    
    col_widths = [65, 55, 82, 210, 140]
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
    
    # 4. BOTÃO DE DOWNLOAD DIRETO
    st.download_button(
        label="📥 Baixar Relatório Atualizado em PDF",
        data=buffer,
        file_name="relatorio_inventario_ultrabooks.pdf",
        mime="application/pdf",
        use_container_width=True
    )

except Exception as e:
    st.error(f"Erro na conexão ou na estrutura dos dados. Certifique-se de que a planilha foi compartilhada com o robô. Detalhes: {e}")
