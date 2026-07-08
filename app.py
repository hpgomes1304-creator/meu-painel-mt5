from flask import Flask, request, jsonify, render_template_string, session, redirect
import os
import psycopg2

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_trader_no_corre"

# Senha padrão de acesso ao seu painel
SENHA_DE_ACESSO = "123456"

DATABASE_URL = os.environ.get('DATABASE_URL')

def obter_conexao():
    return psycopg2.connect(DATABASE_URL)

# --- TELA DE LOGIN PREMIUM ---
TELA_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Autenticação</title>
    <style>
        body { background: linear-gradient(135deg, #070c14 0%, #0d1527 100%); color: #ffffff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background-color: #111c30; padding: 45px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); text-align: center; width: 340px; border: 1px solid #1a2b49; }
        .brand { font-size: 28px; font-weight: 800; margin-bottom: 5px; }
        .sub-brand { color: #00e676; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 30px; }
        input[type="password"] { width: 100%; padding: 14px; border: 1px solid #1f365c; border-radius: 6px; background-color: #070c14; color: white; box-sizing: border-box; font-size: 16px; margin-bottom: 25px; }
        button { background: linear-gradient(90deg, #00e676 0%, #00b359 100%); color: #070c14; border: none; padding: 14px; width: 100%; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 16px; text-transform: uppercase; width: 100%; }
        .erro-msg { color: #ff5252; background-color: rgba(255,82,82,0.1); padding: 10px; border-radius: 4px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="brand">TRADER NO CORRE</div>
        <div class="sub-brand">Mentor Risk Protocol</div>
        {% if erro %} <div class="erro-msg">{{ erro }}</div> {% endif %}
        <form method="POST">
            <input type="password" name="senha" placeholder="Chave de Acesso" required>
            <button type="submit">Desbloquear Painel</button>
        </form>
    </div>
</body>
</html>
"""

# --- DASHBOARD TRADER NO CORRE ---
PAINEL_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Dashboard</title>
    <style>
        body { background-color: #070c14; color: #ecf0f1; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
        .navbar { background-color: #0d1527; height: 70px; display: flex; justify-content: space-between; align-items: center; padding: 0 40px; border-bottom: 1px solid #1a2b49; }
        .nav-logo { font-size: 22px; font-weight: 800; color: #ffffff; }
        .nav-logo span { color: #00e676; }
        .badge { background-color: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; color: #00e676; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .logout-btn { color: #ff5252; text-decoration: none; font-size: 14px; font-weight: 600; }
        .main-container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }
        .metric-card { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 10px; padding: 25px; border-left: 4px solid #00e676; }
        .card-label { color: #7f8c8d; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 12px; }
        .card-value { font-size: 32px; font-weight: 700; color: #ffffff; font-family: monospace; }
        .footer-card { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 10px; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        .footer-text { color: #7f8c8d; font-size: 13px; }
        .footer-time { color: #00e676; font-weight: 600; font-size: 14px; }
    </style>
    <script> setTimeout(function(){ location.reload(); }, 5000); </script> <!-- Atualiza a tela a cada 5 segundos -->
</head>
<body>
    <div class="navbar">
        <div class="nav-logo">TRADER<span>NO_CORRE</span></div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <div class="badge">Sinal Online</div>
            <a href="/logout" class="logout-btn">Sair</a>
        </div>
    </div>
    <div class="main-container">
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="card-label">Saldo de Conta (Balance)</div>
                <div class="card-value">$ {{ dados.saldo }}</div>
            </div>
            <div class="metric-card">
                <div class="card-label">Capital Flutuante (Equity)</div>
                <div class="card-value">$ {{ dados.equidade }}</div>
            </div>
            <div class="metric-card">
                <div class="card-label">Drawdown Atual</div>
                <div class="card-value">{{ dados.drawdown }} %</div>
            </div>
        </div>
        <div class="footer-card">
            <div class="footer-text">Gateway de Transmissão MetaTrader 5 Ativo</div>
            <div class="footer-time">Último Sinal: {{ dados.data }}</div>
        </div>
    </div>
</body>
</html>
"""

# --- ENTRADA DE DADOS SIMPLIFICADA (EVITA BLOQUEIOS DO RENDER) ---
@app.route('/atualizar-dados', methods=['POST'])
def atualizar_dados():
    try:
        dados = request.get_json(force=True)
        # Força os dados a virarem floats puros antes de salvar no Postgres
        saldo = float(dados.get('saldo', 0.0))
        equidade = float(dados.get('equidade', 0.0))
        drawdown = float(dados.get('drawdown', 0.0))
        
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO metricas_conta (saldo, equidade, drawdown) VALUES (%s, %s, %s)",
            (saldo, equidade, drawdown)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 400

@app.route('/', methods=['GET', 'POST'])
def principal():
    if request.method == 'POST':
        if request.form.get('senha') == SENHA_DE_ACESSO:
            session['logado'] = True
            return redirect('/')
        else:
            return render_template_string(TELA_LOGIN_HTML, erro="Chave de acesso incorreta.")

    if not session.get('logado'):
        return render_template_string(TELA_LOGIN_HTML, erro=None)

    dados_atuais = {
        "saldo": "0.00", "equidade": "0.00", "drawdown": "0.00",
        "data": "Aguardando primeiro pulso do robô MT5..."
    }

    try:
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute("SELECT saldo, equidade, drawdown, to_char(data_hora, 'DD/MM HH24:MI:SS') FROM metricas_conta ORDER BY id DESC LIMIT 1")
        linha = cur.fetchone()
        cur.close()
        conn.close()

        if linha:
            dados_atuais = {
                "saldo": f"{float(linha[0]):,.2f}",
                "equidade": f"{float(linha[1]):,.2f}",
                "drawdown": f"{float(linha[2]):.2f}",
                "data": str(linha[3])
            }
    except Exception as e:
        dados_atuais["data"] = "Conectando ao banco de dados..."

    return render_template_string(PAINEL_HTML, dados=dados_atuais)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
