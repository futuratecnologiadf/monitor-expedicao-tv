import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path
import psycopg2
import json

# ==================== CONFIGURAÇÃO STREAMLIT ====================
st.set_page_config(
    page_title="Gerencial de Expedição",
    page_icon="https://cdn-icons-png.flaticon.com/128/7656/7656399.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS para modo TV e lista de pedidos
st.markdown("""
    <link rel="stylesheet" href="https://cloudflare.com">
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden;
            min-height: 100vh;
            background-color: #0E1117;
        }
        .block-container {
            padding: 1rem !important;
            max-width: 100% !important;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .panel-title {
            font-size: clamp(1.8rem, 3vw, 2.4rem);
            font-weight: 800;
            color: #ffffff;
            margin: 0;
        }

        /* BOTÕES STATUS */
        div.stButton > button {
            width: 100%;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.05);
            color: #f8f8f8;
            font-size: 0.9rem;
            padding: 0.65rem 1rem;
            transition: all 0.2s ease;
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            background: rgba(255,255,255,0.08);
        }

        /* STATUS ATIVO */
        .active-status button {
            border-width: 3px !important;
            font-weight: bold !important;
            box-shadow: 0 0 10px rgba(255,255,255,0.15);
        }
            
        .status-summary {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: center;
            margin-bottom: 1rem;
        }

        .status-filter-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.65rem 1rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            font-size: 0.9rem;
            white-space: nowrap;
            text-decoration: none !important;
            transition: all 0.2s ease;
        }

        .status-filter-btn:hover {
            transform: translateY(-2px);
            background: rgba(255,255,255,0.08);
        }
            
        .status-filter-btn {
            text-decoration: none !important;
        }
            
        .table-container {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding-top: 0.8rem;
        }

        .table-header{
            display: grid;
            grid-template-columns: 0.8fr 0.5fr 0.7fr 2.5fr 0.5fr 0.5fr;
            gap: 1rem;
            text-align: center;
            padding-bottom: 0.3rem;
        }


        .table-row {
            display: grid;
            grid-template-columns: 0.8fr 0.5fr 0.7fr 2.5fr 0.5fr 0.5fr;
            gap: 1rem;
            align-items: center;
            width: 100%;
            box-sizing: border-box;
        }

        #col-retirada,
        [id$="-col-retirada"] {
            padding-left: 0.8rem;
            max-width: 32ch;
            text-align: left;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            alingn-items: center;
        }
            
        #col-status,
        [id$="-col-status"] {
            max-width: 20ch;
            text-align: left;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-weight: bold;
        }

        #col-pedido,
        [id$="-col-pedido"] {
            max-width: 9ch;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-weight: bold;
        }

        #col-cliente,
        [id$="-col-cliente"] {
            max-width: 300ch;
            text-align: left;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        #col-hora,
        [id$="-col-hora"] {
            max-width: 15ch;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        #col-tempo,
        [id$="-col-tempo"] {
            max-width: 20ch;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-weight: bold;
        }

        .table-header {
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.75rem;
            text-align: center;
        }

        .table-row {
            animation: slideIn 0.4s ease-out forwards;
            background-color: #131923;
            padding: 2px;
            border-radius: 4px;
            min-height: 5px;
            transition: transform 0.2s ease;
            border-left: 3px solid transparent;
            margin-bottom: 8px;
        }

        .table-row:hover {
            transform: translateY(-2px);
            background-color: #171f2a;
        }

        .table-cell {
            color: #f0f6fc;
            font-size: clamp(0.95rem, 1vw, 1.05rem);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .table-cell.summary {
            color: #8b949e;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.45rem 0.85rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.85rem;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .priority-flag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.6rem;
            height: 1.6rem;
            border-radius: 0.35rem;
            margin-right: 0.5rem;
            overflow: hidden;
        }

        .priority-flag svg {
            width: 1.1rem;
            height: 1.1rem;
            display: block;
        }
            
        @media (max-width: 1200px) {
            .table-header,
            .table-row {
                grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
                gap: 0.5rem;
            }
            .table-header div:nth-child(6),
            .table-row div:nth-child(6) {
                display: none;
            }
        }

        @media (max-width: 900px) {
            .table-header,
            .table-row {
                grid-template-columns: 1fr 1fr 1fr 1fr;
                gap: 0.4rem;
            }
            .table-header div:nth-child(5),
            .table-row div:nth-child(5),
            .table-header div:nth-child(6),
            .table-row div:nth-child(6) {
                display: none;
            }
        }

        @media (max-width: 700px) {
            .table-header,
            .table-row {
                grid-template-columns: 1fr 1fr 1fr;
                gap: 0.3rem;
            }
            .table-header div:nth-child(4),
            .table-row div:nth-child(4),
            .table-header div:nth-child(5),
            .table-row div:nth-child(5),
            .table-header div:nth-child(6),
            .table-row div:nth-child(6) {
                display: none;
            }
        }

        ::-webkit-scrollbar { width: 0px; }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================
def get_priority_flag_svg(color):
    return f'''
        <span class="priority-flag" style="color: {color};">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path fill="currentColor" d="M4 3a1 1 0 0 1 1 1v16a1 1 0 1 1-2 0V4a1 1 0 0 1 1-1zm3 2h9.5a1 1 0 0 1 .93.63l1.5 3.75a1 1 0 0 1 0 .84L16.43 14.4a1 1 0 0 1-.93.6H7v-6z"/>
            </svg>
        </span>
    '''


def calcular_tempo_passado(hora_string):
    """Calcula a diferença de tempo entre agora e a emissão do pedido"""
    try:
        agora = datetime.now()
        # Tentar parsear diferentes formatos de data/hora
        try:
            # Formato: DD/MM/YYYY HH:MM
            hora_pedido = datetime.strptime(hora_string, '%d/%m/%Y %H:%M')
        except ValueError:
            try:
                # Formato: HH:MM (fallback)
                hora_pedido = datetime.strptime(hora_string, '%H:%M').replace(
                    year=agora.year, month=agora.month, day=agora.day
                )
                if hora_pedido > agora:
                    hora_pedido -= timedelta(days=1)
            except ValueError:
                return ""

        # Calcular tempo decorrido mesmo para dias anteriores
        diff = agora - hora_pedido
        minutos_totais = int(diff.total_seconds() / 60)
        if minutos_totais < 0:
            minutos_totais = 0

        if minutos_totais < 60:
            return f"{minutos_totais}min"

        horas = minutos_totais // 60
        min_rest = minutos_totais % 60
        if horas < 24:
            return f"{horas}h {min_rest}min" if min_rest > 0 else f"{horas}h"

        dias = horas // 24
        horas_restantes = horas % 24
        if horas_restantes == 0:
            return f"{dias}d {min_rest}min" if min_rest > 0 else f"{dias}d"
        return f"{dias}d {horas_restantes}h {min_rest}min" if min_rest > 0 else f"{dias}d {horas_restantes}h"
    except:
        return ""

def fetch_sales_data(loja):
    """Busca dados do banco com garantia de unicidade no SQL"""
    try:
        config_path = Path(__file__).parent.parent / '_postgresql.json'
        with open(config_path) as f:
            config = json.load(f)

        QUERY = f"""
        SELECT DISTINCT ON (p.serie, p.nu_nota)
                CASE
                    WHEN p.tpretirada = '7' THEN 'ALTA'
                    WHEN p.tpretirada = '8' THEN 'MÉDIA'
                    WHEN p.tpretirada = '9' THEN 'BAIXA'
                    ELSE 'BAIXA'
                END as retirada,
                t.descricao as tipo_retirada,
                p.serie || '-' || p.nu_nota as pedido,
                (TO_CHAR(CAST(p.dt_emissao as date), 'DD/MM/YYYY') || ' ' || TO_CHAR(CAST(p.hora as time), 'HH24:MI')) as hora,
                CASE
                    WHEN a.passo = '1' THEN 'PEDIDO EMITIDO'
                    WHEN a.passo = '2' THEN 'SEPARAÇÃO'
                    WHEN a.passo = '3' THEN 'CONFERÊNCIA'
                    WHEN a.passo = '4' THEN 'NOTA EMITIDA'
                    WHEN a.passo = '5' THEN 'ENTREGA'
                    ELSE 'PEDIDO EMITIDO'
                END status,
                (p.codcli || ' - ' || p.cliente) as cliente
        FROM pedido as p
        LEFT OUTER JOIN mpassos a ON a.cd_loja = p.loja AND a.cd_cliente = p.codcli AND a.documento = p.nu_nota
        LEFT OUTER JOIN tretira2 t ON t.tpretirada = p.tpretirada
        WHERE   p.dt_emissao >= CURRENT_DATE-1 and
                p.loja = '{loja}'
        ORDER BY p.serie DESC, p.nu_nota DESC, a.passo desc, p.tpretirada
        """
        connection = psycopg2.connect(**config)
        df = pd.read_sql(QUERY, connection)
        connection.close()
        return df
    except:
        return pd.DataFrame()

# ==================== INTERFACE KANBAN ====================
def main():
    # Inicializar session state para o filtro de pesquisa e auto-refresh
    if 'search_text' not in st.session_state:
        st.session_state.search_text = ""
    if 'status_filter' not in st.session_state:
        st.session_state.status_filter = None
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    params = st.query_params
    loja = params.get("loja", "01")
    status_param = params.get("status", None)

    config_status = {
        'PEDIDO EMITIDO':   {"cor": "#CCCCCC", "icon": "💻", "slug": "pedido-emetido"},
        'SEPARAÇÃO':        {"cor": "#FF2121", "icon": "📦", "slug": "separacao"},
        'CONFERÊNCIA':      {"cor": "#FF9500", "icon": "🔍", "slug": "conferencia"},
        'NOTA EMITIDA':     {"cor": "#0095FF", "icon": "🧾", "slug": "nota-emitida"},
        'ENTREGA':          {"cor": "#00FF51", "icon": "✅", "slug": "entrega"},
    }

    slug_para_status = {
        cfg["slug"]: status_nome
        for status_nome, cfg in config_status.items()
    }

    st.session_state.status_filter = slug_para_status.get(status_param, None)

    status_order = list(config_status.keys())
    status_labels = {
        'PEDIDO EMITIDO': 'Pedido emitido',
        'SEPARAÇÃO': 'Separação',
        'CONFERÊNCIA': 'Conferência',
        'NOTA EMITIDA': 'Nota emitida',
        'ENTREGA': 'Entrega'
    }
    prioridade_color_map = {
        'ALTA': '#FF2121',
        'MÉDIA': "#FFFB00",
        'BAIXA': "#0066FF"
    }

    # Cabeçalho e filtro
    st.markdown('<div class="panel-header">', unsafe_allow_html=True)
    st.markdown(f'<h1 class="panel-title">Painel Gerencial de Expedição</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Campo de pesquisa responsivo
    search_input = st.text_input(
        " ", 
        value=st.session_state.search_text,
        placeholder="Digite para pesquisar...",
        key="search_input"
    )
    
    # Atualizar filtro apenas se mudou
    if search_input != st.session_state.search_text:
        st.session_state.search_text = search_input

    # Buscar dados
    df_raw = fetch_sales_data(loja)
    
    # LIMPEZA CRÍTICA: Remove duplicatas no Pandas antes de desenhar
    if not df_raw.empty:
        df = df_raw.drop_duplicates(subset=['pedido'], keep='first').copy()
    else:
        df = pd.DataFrame()

    # Aplicar filtro ao dataframe
    if st.session_state.search_text and not df.empty:
        df = df[df.apply(lambda row: row.astype(str).str.contains(st.session_state.search_text, case=False, na=False).any(), axis=1)]
    if st.session_state.status_filter and not df.empty:
        df = df[df['status'] == st.session_state.status_filter]

    # Atualizar summary com contagem filtrada
    df_count = df_raw.drop_duplicates(subset=['pedido'], keep='first').copy() if not df_raw.empty else pd.DataFrame()

    status_ativo = st.session_state.status_filter

    buttons_html = '<div class="status-summary">'

    for status_nome, cfg in config_status.items():

        count = len(df_count[df_count['status'] == status_nome]) if not df_count.empty else 0

        ativo = status_ativo == status_nome

        border_width = "3px" if ativo else "1px"
        border_color = cfg["cor"] if ativo else "rgba(255,255,255; 0.12)"
        background_color = cfg["cor"] + "50" if ativo else "rgba(255,255,255; 0.88)"
        text_color = "#ffffff"
        font_weight = "800"

        status_url = f"?loja={loja}&status={cfg['slug']}"

        buttons_html += f'''<a href="{status_url}" class="status-filter-btn" style="border:{border_width} solid {border_color}; color:{text_color}; font-weight:{font_weight}; background-color: {background_color};">
    {cfg['icon']} {status_labels[status_nome].upper()}: {count}
    </a>'''

    todos_ativo = status_ativo is None

    buttons_html += f'''<a href="?loja={loja}" class="status-filter-btn" style="border:{'3px' if todos_ativo else '1px'} solid {'#FFFFFF' if todos_ativo else 'rgba(255,255,255,0.12)'}; color:#FFFFFF; font-weight:{'800' if todos_ativo else '400'};">
    🔄 TODOS
    </a>'''

    buttons_html += '</div>'

    st.markdown(buttons_html, unsafe_allow_html=True)

    if df.empty:
        st.markdown("<div class='table-container'><div class='table-row'><div class='table-cell'>Nenhum pedido encontrado para a loja escolhida.</div></div></div>", unsafe_allow_html=True)
    else:
        df['status_rank'] = df['status'].apply(lambda x: status_order.index(x) if x in status_order else len(status_order))
        df = df.sort_values(by=['status_rank', 'pedido'], ascending=[True, False])

        st.markdown("""
            <div class="table-container">
                <div class="table-header">
                    <div id="col-retirada">Retirada</div>
                    <div id="col-pedido">Pedido</div>
                    <div id="col-status">Status</div>
                    <div id="col-cliente">Cliente</div>
                    <div id="col-hora">Hora</div>
                    <div id="col-tempo">Tempo</div>
                </div>
            """, unsafe_allow_html=True)

        for index, row in df.iterrows():
            tempo = calcular_tempo_passado(row['hora'])
            status_slug = config_status.get(row['status'], {}).get('slug', 'pedido-emetido')
            status_label = status_labels.get(row['status'], row['status'])
            status_color = config_status.get(row['status'], {}).get('cor', '#CCCCCC')
            status_icon = config_status.get(row['status'], {}).get('icon', '')
            prioridade_cor = prioridade_color_map.get(row['retirada'], '#CCCCCC')
            prioridade_flag = get_priority_flag_svg(prioridade_cor)

            st.markdown(f"""
                <div class="table-row" id="row-{index}" style="border-left-color: {status_color};">
                    <div class="table-cell" id="row-{index}-col-retirada" style="font-size: 0.7em">{prioridade_flag}{row['tipo_retirada']}</div>
                    <div class="table-cell" id="row-{index}-col-pedido" style="font-weight: bold; color: {status_color};">{row['pedido']}</div>
                    <div class="table-cell" id="row-{index}-col-status">{status_icon} {status_label.upper()}</div>
                    <div class="table-cell" id="row-{index}-col-cliente">{row['cliente']}</div>
                    <div class="table-cell" id="row-{index}-col-hora">{row['hora']}</div>
                    <div class="table-cell" id="row-{index}-col-tempo">{tempo}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh a cada 2 segundos (apenas se não houve mudança recente no filtro)
    time_now = time.time()
    if time_now - st.session_state.last_refresh >= 2:
        st.session_state.last_refresh = time_now
        st.rerun()

if __name__ == "__main__":
    main()