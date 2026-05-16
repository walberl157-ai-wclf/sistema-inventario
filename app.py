import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# CONFIGURAÇÃO DA PÁGINA WEB
st.set_page_config(page_title="Gerador de Relatórios", page_icon="📊", layout="centered")

st.title("📊 Gerador Automatizado de Relatórios")
st.write("Faça o upload do arquivo CSV do inventário para gerar o PDF formatado.")

# 1. COMPONENTE VISUAL PARA ENVIAR O ARQUIVO CSV
arquivo_enviado = st.file_uploader("Selecione o arquivo .csv do inventário", type=["csv"])

if arquivo_enviado is not None:
    try:
        # 2. CARREGAR E FILTRAR OS DADOS DO CSV ENVIADO
        df_original = pd.read_csv(arquivo_enviado)
        
        # Padronizar nomes de colunas (caso haja variações)
        df_original.columns = df_original.columns.str.lower().str.strip()
        
        # Filtro fixo solicitado
        df_original['endereco'] = df_original['endereco'].astype(str).str.strip()
        df = df_original[df_original['endereco'] == '01010333 - ULTRABOOK/NOTEBOOK / TABLET']
        df = df.sort_values(by='responsavel', ascending=True)
        
        st.success(f"Arquivo processado com sucesso! Encontrados {len(df)} registros para o filtro.")
        
        # 3. CONSTRUÇÃO DO PDF EM MEMÓRIA (Sem precisar salvar em disco rígido)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        
        # Estilos do Relatório
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22,
            textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=10
        )
        normal_style = styles['Normal']
        
        # Cabeçalho do PDF
        data_hora_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph("RELATÓRIO DE INVENTÁRIO (SISTEMA WEB)", title_style))
        story.append(Paragraph("<b>Filtro por Endereço:</b> 01010333 - ULTRABOOK/NOTEBOOK / TABLET", normal_style))
        story.append(Paragraph(f"<b>Total de Itens Encontrados:</b> {len(df)}", normal_style))
        story.append(Paragraph(f"<b>Data de Emissão:</b> {data_hora_emissao}", normal_style))
        story.append(Spacer(1, 15))
        
        # Tabela
        col_widths = [60, 60, 92, 180, 160]
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
        
        # Gerar o PDF no buffer
        doc.build(story)
        buffer.seek(0)
        
        # 4. BOTÃO DE DOWNLOAD NA INTERFACE WEB
        st.download_button(
            label="📥 Baixar Relatório em PDF",
            data=buffer,
            file_name="relatorio_inventario_ultrabooks.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo. Verifique se as colunas estão corretas. Detalhes: {e}")
