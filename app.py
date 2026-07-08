from flask import Flask, request, jsonify, render_template_string, session, redirect
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_trader_no_corre"

SENHA_DE_ACESSO = "123456"
DATABASE_URL = os.environ.get('DATABASE_URL')

def obter_conexao():
    return psycopg2.connect(DATABASE_URL)

# --- SISTEMA AUTOCORREÇÃO: CRIA AS COLUNAS SE ELAS NÃO EXISTIREM ---
def ajustar_banco():
    try:
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute("ALTER TABLE metricas_conta ADD COLUMN IF NOT EXISTS conta VARCHAR(50) DEFAULT 'Padrão';")
        cur.execute("ALTER TABLE metricas_conta ADD COLUMN IF NOT EXISTS servidor VARCHAR(100) DEFAULT 'Desconhecido';")
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass

# --- TELA DE LOGIN ---
TELA_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Autenticação</title>
    <style>
        body { background: linear-gradient(135deg, #070c14 0%, #0d1527 100%); color: #ffffff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background-color: #111c30; padding: 45px; border-radius: 12px; text-align: center; width: 340px; border: 1px solid #1a2b49; }
        .brand { font-size: 28px; font-weight: 800; margin-bottom: 5px; }
        .sub-brand { color: #00e676; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 30px; }
        input[type="password"] { width: 100%; padding: 14px; border: 1px solid #1f365c; border-radius: 6px; background-color: #070c14; color: white; box-sizing: border-box; font-size: 16px; margin-bottom: 25px; }
        button { background: linear-gradient(90deg, #00e676 0%, #00b359 100%); color: #070c14; border: none; padding: 14px; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 16px; text-transform: uppercase; width: 100%; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="brand">TRADER NO CORRE</div>
        <div class="sub-brand">Mentor Risk Protocol</div>
        <form method="POST">
            <input type="password" name="senha" placeholder="Chave de Acesso" required>
            <button type="submit">Desbloquear Painel</button>
        </form>
    </div>
</body>
</html>
"""

# --- TELA DE SELEÇÃO DE CONTAS (ESTILO LISTA FTMO ORIGINAL) ---
TELA_SELECAO_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Contas Ativas</title>
    <style>
        body { background-color: #070c14; color: #ecf0f1; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
        .navbar { background-color: #0d1527; height: 70px; display: flex; justify-content: space-between; align-items: center; padding: 0 40px; border-bottom: 1px solid #1a2b49; }
        .nav-logo { font-size: 22px; font-weight: 800; color: #ffffff; }
        .nav-logo span { color: #00e676; }
        .main-container { max-width: 1000px; margin: 50px auto; padding: 0 20px; }
        h2 { font-size: 24px; font-weight: 700; margin-bottom: 25px; display: flex; align-items: center; gap: 10px; }
        .ponto-verde { width: 10px; height: 10px; background-color: #00e676; border-radius: 50%; display: inline-block; }
        .account-card { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 8px; padding: 25px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .account-details { display: flex; flex-direction: column; gap: 8px; }
        .acc-type { background-color: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; color: #00e676; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
        .acc-number { font-size: 20px; font-weight: 700; color: #ffffff; margin-top: 5px; }
        .acc-metrics { color: #7f8c8d; font-size: 14px; margin-top: 5px; }
        .acc-metrics b { color: #ffffff; font-family: monospace; }
        .btn-detalhe { background-color: #12223d; border: 1px solid #203a61; color: #ffffff; padding: 12px 24px; border-radius: 6px; font-weight: 600; text-decoration: none; transition: 0.3s; }
        .btn-detalhe:hover { background-color: #00e676; color: #070c14; border-color: #00e676; }
        .no-data { text-align: center; color: #7f8c8d; padding: 40px; border: 1px dashed #1a2b49; border-radius: 8px; }
    </style>
    <script> setTimeout(function(){ location.reload(); }, 5000); </script>
</head>
<body>
    <div class="navbar">
        <div class="nav-logo">TRADER<span>NO_CORRE</span></div>
        <a href="/logout" style="color: #ff5252; text-decoration: none; font-weight: 600;">Sair</a>
    </div>
    <div class="main-container">
        <h2><span class="ponto-verde"></span> Contas Identificadas</h2>
        {% if contas %}
            {% for c in contas %}
            <div class="account-card">
                <div class="account-details">
                    <div>
                        <span class="acc-type">Broker: {{ c.servidor }}</span>
                        <span class="acc-type" style="background-color:rgba(32,148,250,0.1); border-color:#2094fa; color:#2094fa; margin-left:5px;">MT5 Connected</span>
                    </div>
                    <div class="acc-number">ID: {{ c.conta }}</div>
                    <div class="acc-metrics">
                        Balance: <b>$ {{ c.saldo }}</b> &nbsp;|&nbsp; Equity: <b>$ {{ c.equidade }}</b>
                    </div>
                </div>
                <div>
                    <a href="/dashboard/{{ c.conta }}" class="btn-detalhe">Análise Metrix &gt;</a>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="no-data">Nenhuma conta ou corretora enviando telemetria ativa. Jogue o robô no gráfico.</div>
        {% endif %}
    </div>
</body>
</html>
"""
# --- PAINEL DE MÉTRICAS INTERNAS AVANÇADAS (ESTILO COMPLETO DA IMAGEM) ---
TELA_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Métricas da Conta {{ conta }}</title>
    <style>
        body { background-color: #070c14; color: #ecf0f1; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
        .navbar { background-color: #0d1527; height: 70px; display: flex; justify-content: space-between; align-items: center; padding: 0 40px; border-bottom: 1px solid #1a2b49; }
        .nav-logo { font-size: 22px; font-weight: 800; color: #ffffff; text-decoration: none; }
        .nav-logo span { color: #00e676; }
        .main-container { max-width: 1250px; margin: 30px auto; padding: 0 20px; display: flex; flex-direction: column; gap: 25px; }
        .topo-layout { display: grid; grid-template-columns: 1fr 2fr; gap: 25px; }
        .secao-bloco { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 8px; padding: 25px; }
        .titulo-bloco { font-size: 16px; font-weight: 700; margin-bottom: 20px; text-transform: uppercase; color: #ffffff; }
        .gauge-container { text-align: center; padding: 10px 0; }
        .gauge-valor { font-size: 36px; font-weight: bold; color: #00e676; }
        .gauge-subtext { color: #00e676; font-size: 14px; font-weight: 600; }
        .tab-objetivos { width: 100%; border-collapse: collapse; }
        .tab-objetivos th { text-align: left; color: #7f8c8d; font-size: 12px; padding-bottom: 15px; }
        .tab-objetivos td { padding: 14px 0; border-bottom: 1px solid #1a2b49; font-size: 15px; }
        .obj-nome { color: #2094fa; font-weight: 600; }
        .check-ok { width: 22px; height: 22px; background-color: #00e676; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #070c14; font-weight: bold; }
        .check-fail { width: 22px; height: 22px; background-color: #ff5252; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
        .linha-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        .card-pequeno { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 6px; padding: 18px; text-align: center; }
        .card-pequeno-lbl { color: #7f8c8d; font-size: 13px; margin-bottom: 8px; }
        .card-pequeno-val { font-size: 22px; font-weight: 700; font-family: monospace; }
        .grid-inferior { display: grid; grid-template-columns: 1fr 1.5fr; gap: 25px; }
        .grid-estatisticas { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .est-item { background-color: #111c30; border: 1px solid #1a2b49; border-radius: 6px; padding: 15px; }
        .est-lbl { color: #7f8c8d; font-size: 12px; margin-bottom: 6px; }
        .est-val { font-size: 18px; font-weight: bold; color: #ffffff; font-family: monospace; }
        .tab-diario { width: 100%; border-collapse: collapse; }
        .tab-diario th { text-align: left; color: #7f8c8d; font-size: 12px; padding-bottom: 12px; }
        .tab-diario td { padding: 12px 0; border-bottom: 1px solid #1a2b49; font-family: monospace; font-size: 14px; }
        .data-link { color: #2094fa; text-decoration: none; font-weight: 600; }
        .val-lucro { color: #00e676; }
        .val-preju { color: #ff5252; }
    </style>
    <script> setTimeout(function(){ location.reload(); }, 5000); </script>
</head>
<body>
    <div class="navbar">
        <a href="/" class="nav-logo">TRADER<span>NO_CORRE</span></a>
        <span style="color: #7f8c8d; font-size: 14px;">Servidor: <b style="color:#ffffff;">{{ servidor }}</b></span>
    </div>
    <div class="main-container">
        <div class="topo-layout">
            <div class="secao-bloco">
                <div class="titulo-bloco">Pontuação de Disciplina</div>
                <div class="gauge-container">
                    <div style="font-size: 40px; margin-bottom: 10px;">📊</div>
                    <div class="gauge-valor">80%</div>
                    <div class="gauge-subtext">Bom</div>
                </div>
            </div>
            <div class="secao-bloco">
                <div class="titulo-bloco">Objetivos de Trading</div>
                <table class="tab-objetivos">
                    <thead><tr><th>Objetivos de Trading</th><th>Resultado</th><th style="text-align:right;">Resumo</th></tr></thead>
                    <tbody>
                        <tr><td class="obj-nome">4 Dias Mínimos de Trading</td><td>13</td><td align="right"><div class="check-ok">✓</div></td></tr>
                        <tr><td class="obj-nome">Perda Máxima Diária: -$500</td><td class="val-preju">$ {{ dados.perda_diaria }}</td><td align="right"><div class="check-ok">✓</div></td></tr>
                        <tr><td class="obj-nome">Perda Máxima: -$1.000</td><td class="val-preju">$ {{ dados.perda_maxima }}</td><td align="right"><div class="check-ok">✓</div></td></tr>
                        <tr><td class="obj-nome">Meta de Lucro: $1.000</td><td class="val-lucro">$ 0.00</td><td align="right"><div class="check-fail">✗</div></td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="linha-cards">
            <div class="card-pequeno"><div class="card-pequeno-lbl">Perda permitida hoje</div><div class="card-pequeno-val" style="color:#00e676;">$ 500.00</div></div>
            <div class="card-pequeno"><div class="card-pequeno-lbl">Perda máxima permitida</div><div class="card-pequeno-val" style="color:#00e676;">$ 1,000.00</div></div>
            <div class="card-pequeno"><div class="card-pequeno-lbl">Lucros de hoje</div><div class="card-pequeno-val {% if '-' in dados.lucro_hoje %}val-preju{% else %}val-lucro{% endif %}">$ {{ dados.lucro_hoje }}</div></div>
        </div>
        <div class="grid-inferior">
            <div class="secao-bloco">
                <div class="titulo-bloco">Estatísticas</div>
                <div class="grid-estatisticas">
                    <div class="est-item"><div class="est-lbl">Equidade</div><div class="est-val">$ {{ dados.equidade }}</div></div>
                    <div class="est-item"><div class="est-lbl">Balance</div><div class="est-val">$ {{ dados.saldo }}</div></div>
                    <div class="est-item"><div class="est-lbl">Rácio de ganhos</div><div class="est-val" style="color:#00e676;">48.81 %</div></div>
                    <div class="est-item"><div class="est-lbl">Média de lucros</div><div class="est-val" style="color:#00e676;">$ 25.72</div></div>
                    <div class="est-item"><div class="est-lbl">Prejuízo médio</div><div class="est-val" style="color:#ff5252;">-$ 33.95</div></div>
                    <div class="est-item"><div class="est-lbl">Number of trades</div><div class="est-val">168</div></div>
                    <div class="est-item"><div class="est-lbl">Lots</div><div class="est-val">160.92</div></div>
                    <div class="est-item"><div class="est-lbl">Rácio de Sharpe</div><div class="est-val" style="color:#ff5252;">-0.51</div></div>
                </div>
            </div>
            <div class="secao-bloco">
                <div class="titulo-bloco">Resumo Diário</div>
                <table class="tab-diario">
                    <thead><tr><th>Data</th><th>Posições</th><th>Lots</th><th style="text-align:right;">Resultado</th></tr></thead>
                    <tbody>
                        <tr><td><a href="#" class="data-link">08/07</a></td><td>8</td><td>3.43</td><td align="right" class="val-preju">-$105.28</td></tr>
                        <tr><td><a href="#" class="data-link">07/07</a></td><td>21</td><td>32.63</td><td align="right" class="val-preju">-$288.11</td></tr>
                        <tr><td><a href="#" class="data-link">06/07</a></td><td>37</td><td>65.31</td><td align="right" class="val-preju">-$90.21</td></tr>
                        <tr><td><a href="#" class="data-link">03/07</a></td><td>6</td><td>2.01</td><td align="right" class="val-lucro">$65.30</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- INGESTÃO DE SINAL ---
@app.route('/atualizar-dados', methods=['POST'])
def atualizar_dados():
    try:
        dados = request.get_json(force=True)
        conta = str(dados.get('conta', 'Padrão'))
        servidor = str(dados.get('servidor', 'Desconhecido'))
        saldo = float(dados.get('saldo', 0.0))
        equidade = float(dados.get('equidade', 0.0))
        drawdown = float(dados.get('drawdown', 0.0))
        
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO metricas_conta (saldo, equidade, drawdown, conta, servidor) VALUES (%s, %s, %s, %s, %s)",
            (saldo, equidade, drawdown, conta, servidor)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "sucesso"}), 200
    except:
        return jsonify({"status": "erro"}), 400

# --- INTERFACE: CONTAS ATIVAS ---
@app.route('/', methods=['GET', 'POST'])
def principal():
    if request.method == 'POST':
        if request.form.get('senha') == SENHA_DE_ACESSO:
            session['logado'] = True
            return redirect('/')
        else:
            return render_template_string(TELA_LOGIN_HTML, erro="Senha Inválida.")

    if not session.get('logado'):
        return render_template_string(TELA_LOGIN_HTML, erro=None)

    lista_contas = []
    try:
        conn = obter_conexao()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT ON (conta) conta, servidor, saldo, equidade 
            FROM metricas_conta 
            WHERE conta != 'Padrão'
            ORDER BY conta, id DESC
        """)
        linhas = cur.fetchall()
        cur.close() conn.close()
        for l in linhas:lista_contas.append({"conta": l['conta'],"servidor": l['servidor'],"saldo": f"{float(l['saldo']):,.2f}","equidade": f"{float(l['equidade']):,.2f}"})except:passreturn render_template_string(TELA_SELECAO_HTML, contas=lista_contas)--- INTERFACE: MÉTRICAS INTERNAS POR CONTA ---@app.route('/dashboard/<numero_conta>')def dashboard_individual(numero_conta):if not session.get('logado'): return redirect('/')dados_finais = {"saldo": "0.00", "equidade": "0.00", "drawdown": "0.00","perda_diaria": "0.00", "perda_maxima": "0.00", "lucro_hoje": "0.00"}nome_servidor = "Desconhecido"try:conn = obter_conexao()cur = conn.cursor(cursor_factory=RealDictCursor)cur.execute("SELECT saldo, equidade, drawdown, servidor FROM metricas_conta WHERE conta = %s ORDER BY id DESC LIMIT 1", (numero_conta,))linha = cur.fetchone()cur.close()conn.close()if linha:v_saldo = float(linha['saldo'])v_equi = float(linha['equidade'])v_dd = float(linha['drawdown'])nome_servidor = str(linha['servidor'])v_perda = v_saldo - v_equiif v_perda < 0: v_perda = 0.0dados_finais = {"saldo": f"{v_saldo:,.2f}","equidade": f"{v_equi:,.2f}","drawdown": f"{v_dd:.2f}","perda_diaria": f"-{v_perda:.2f}" if v_perda > 0 else "0.00","perda_maxima": f"-{v_perda:.2f}" if v_perda > 0 else "0.00","lucro_hoje": f"-{v_perda:.2f}" if v_perda > 0 else "0.00"}except:passreturn render_template_string(TELA_DASHBOARD_HTML, conta=numero_conta, servidor=nome_servidor, dados=dados_finais)@app.route('/logout')def logout():session.pop('logado', None)return redirect('/')if name == 'main':ajustar_banco()app.run(debug=True)
