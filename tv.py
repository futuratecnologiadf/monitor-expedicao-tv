import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path
import psycopg2
import json

# ==================== CONFIGURAÇÃO STREAMLIT ====================
st.set_page_config(
    page_title="Painel de Expedição",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS para modo TV, Kanban e Animação
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden;
            height: 100vh;
            background-color: #0E1117;
        }
        .block-container { padding: 0.5rem !important; }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .status-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            font-size: 1rem;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-bottom: 4px solid;
            color: #FFFFFF;
            text-align: center;
            min-height: 80px;
        }

        .pedido-card {
            animation: slideIn 0.5s ease-out forwards;
            background-color: #131923;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 10px;
            font-family: system-ui;
        }
        
        .pedido-id { font-weight: bold; font-size: 1rem; }
        
        .pedido-cliente { 
            color: #c9d1d9; 
            font-size: 1.05rem;
            font-weight: 500; 
            display: block; 
            margin-top: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .pedido-hora-container { 
            color: #8b949e; 
            font-size: 0.8rem; 
            float: right;
            text-align: right;
        }
        
        .tempo-contador { font-weight: bold; }

        ::-webkit-scrollbar { width: 0px; }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================
def calcular_tempo_passado(hora_string):
    """Calcula a diferença de tempo entre agora e a emissão do pedido"""
    try:
        agora = datetime.now()
        hora_pedido = datetime.strptime(hora_string, '%H:%M').replace(
            year=agora.year, month=agora.month, day=agora.day
        )
        if hora_pedido > agora:
            hora_pedido -= timedelta(days=1)
        diff = agora - hora_pedido
        minutos_totais = int(diff.total_seconds() / 60)
        
        if minutos_totais < 60:
            return f"{minutos_totais}min"
        else:
            horas = minutos_totais // 60
            min_rest = minutos_totais % 60
            return f"{horas}h {min_rest}min" if min_rest > 0 else f"{horas}h"
        
    except:
        return ""

def fetch_sales_data(loja):
    """Busca dados do banco com garantia de unicidade no SQL"""
    try:
        config = st.secrets["postgres"]

        QUERY = f"""
        SELECT DISTINCT ON (p.serie, p.nu_nota)
                p.serie || '-' || p.nu_nota as pedido,
                p.numnota,
                CASE
                    WHEN a.passo = '1' THEN 'PEDIDO EMITIDO'
                    WHEN a.passo = '2' THEN 'SEPARAÇÃO'
                    WHEN a.passo = '3' THEN 'CONFERÊNCIA'
                    WHEN a.passo = '4' THEN 'FATURAMENTO'
                    WHEN a.passo = '5' THEN 'ENTREGA'
                    ELSE 'PEDIDO EMITIDO'
                END status,
                p.cliente,
                TO_CHAR(CAST(p.hora as time), 'HH24:MI') as hora
        FROM pedido as p
        LEFT OUTER JOIN mpassos a ON a.cd_loja = p.loja AND a.cd_cliente = p.codcli AND a.documento = p.nu_nota
        WHERE   p.dt_emissao = CURRENT_DATE and
                p.loja = '{loja}' and
                p.tpretirada = '7'
        ORDER BY p.serie DESC, p.nu_nota DESC, a.passo DESC
        """
        connection = psycopg2.connect(**config)
        df = pd.read_sql(QUERY, connection)
        connection.close()
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

# ==================== INTERFACE KANBAN ====================
def main():
    # 1. Container que limpa a tela a cada ciclo (Resolve o problema da duplicata visual)
    placeholder = st.empty()
    params = st.query_params
    loja = params.get("loja", "07")  # Pega a loja da URL ou usa '07' como padrão

    try:
        cfg = st.secrets["postgres"]
        st.write(f"✅ Secrets OK - host: {cfg['host']}")
        conn = psycopg2.connect(**cfg)
        st.write("✅ Banco conectado!")
        conn.close()
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        st.stop()
    
    config_kanban = {
        'PEDIDO EMITIDO':   {"cor": "#CCCCCC", "icon": "💻"},
        'SEPARAÇÃO':     {"cor": "#FF2121", "icon": "📦"},
        'CONFERÊNCIA':      {"cor": "#FF9500", "icon": "🔍"},
        'FATURAMENTO':      {"cor": "#0095FF", "icon": "🧾"},
        'ENTREGA':         {"cor": "#00FF51", "icon": "✅"}
    }

    # 2. Loop de atualização infinita para a TV
    while True:
        df_raw = fetch_sales_data(loja)
        
        # LIMPEZA CRÍTICA: Remove duplicatas no Pandas antes de desenhar
        if not df_raw.empty:
            df = df_raw.drop_duplicates(subset=['pedido'], keep='first').copy()
        else:
            df = pd.DataFrame()

        with placeholder.container():
            cols = st.columns(5)
            
            for (status_nome, cfg), col_render in zip(config_kanban.items(), cols):
                with col_render:
                    # Filtra apenas pedidos deste status
                    subset = df[df['status'] == status_nome].head(12) if not df.empty else pd.DataFrame()
                    subset_view = subset.drop_duplicates(subset=['pedido'], keep='first').head(10) if not subset.empty else pd.DataFrame()


                    st.markdown(f'''
                        <div class="status-header" style="border-bottom-color: {cfg['cor']};">
                            <span style="font-size: 1.5rem;">{cfg['icon']}</span>
                            <span>{status_nome}</span>
                            <span style="font-size: 0.8rem; color: gray;">{len(df[df['status'] == status_nome]) if not df.empty else 0} PEDIDOS</span>
                        </div>
                    ''', unsafe_allow_html=True)

                    if subset_view.empty:
                        st.markdown("<p style='text-align:center; color:#30363d; margin-top:20px;'>Vazio</p>", unsafe_allow_html=True)
                    else:
                        for i, row in subset_view.iterrows():
                            tempo = calcular_tempo_passado(row['hora'])
                            
                            # O HTML do card sem as linhas internas (bordas removidas via CSS lá em cima)
                            st.markdown(f'''
                                <div class="pedido-card">
                                    <div class="pedido-hora-container">
                                        <span>{row['hora']}</span><br>
                                        <span class="tempo-contador" style="color: {cfg['cor']};">{tempo}</span>
                                    </div>
                                    <div class="pedido-id" style="color: {cfg['cor']};">{row['pedido']}</div>
                                    <span class="pedido-cliente">{row['cliente']}</span>
                                </div>
                            ''', unsafe_allow_html=True)
        
        # 3. Tempo de espera antes da próxima leitura do banco
        time.sleep(2)

if __name__ == "__main__":
    main()
