from flask import Flask, request, jsonify, render_template_string, session, redirect
import os
import psycopg2

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_trader_no_corre"

# Defina a sua senha mestre para acessar o painel aqui
SENHA_DE_ACESSO = "123456"

DATABASE_URL = os.environ.get('DATABASE_URL')

def obter_conexao():
    return psycopg2.connect(DATABASE_URL)

# --- TELA DE LOGIN PREMIUM (TRADER NO CORRE) ---
TELA_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Autenticação</title>
    <style>
        body { background: linear-gradient(135deg, #070c14 0%, #0d1527 100%); color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background-color: #111c30; padding: 45px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.6); text-align: center; width: 340px; border: 1px solid #1a2b49; }
        .brand { font-size: 28px; font-weight: 800; letter-spacing: 1px; margin-bottom: 5px; color: #ffffff; }
        .sub-brand { color: #00e676; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 30px; }
        .input-group { position: relative; margin-bottom: 25px; }
        input[type="password"] { width: 100%; padding: 14px; border: 1px solid #1f365c; border-radius: 6px; background-color: #070c14; color: white; box-sizing: border-box; font-size: 16px; transition: 0.3s; }
        input[type="password"]:focus { border-color: #00e676; outline: none; box-shadow: 0 0 8px rgba(0,230,118,0.2); }
        button { background: linear-gradient(90deg, #00e676 0%, #00b359 100%); color: #070c14; border: none; padding: 14px; width: 100%; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; transition: 0.3s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,230,118,0.4); }
        .erro-msg { color: #ff5252; background-color: rgba(255,82,82,0.1); border: 1px solid rgba(255,82,82,0.2); padding: 10px; border-radius: 4px; margin-bottom: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="brand">TRADER NO CORRE</div>
        <div class="sub-brand">Mentor Risk Protocol</div>
        {% if erro %} <div class="erro-msg">{{ erro }}</div> {% endif %}
        <form method="POST">
            <div class="input-group">
                <input type="password" name="senha" placeholder="Chave de Acesso" required>
            </div>
            <button type="submit">Desbloquear Painel</button>
        </form>
    </div>
</body>
</html>
"""

# --- DASHBOARD PREMIUM (ESTILO ORIGINAL PROP FIRM) ---
PAINEL_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Trader no Corre - Dashboard</title>
    <style>
        body { background-color: #070c14; color: #ecf0f1; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
        .navbar { background-color: #0d1527; height: 70px; display: flex; justify-content: space-between; align-items: center; padding: 0 40px; border-bottom: 1px solid #1a2b49; }
        .nav-logo { font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px; }
        .nav-logo span { color: #00e676; }
        .nav-status { display: flex; align-items: center; gap: 20px; }
        .badge { background-color: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; color: #00e676; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .logout-btn { color: #ff5252; text-decoration: none; font-size: 14px; font-weight: 600; transition: 0.3s; }
        .logout-btn:hover { color: #ff1a1a; }
        
        .main-container { max-width: 1200px; margin: 40px auto; padding: 0 20px; box-sizing: border-box; }
        
        .alert-zone { background: linear-gradient(90deg, #ff5252 0%, #b33636 100%); color: white; padding: 18px 25px; border-radius: 8px; margin-bottom: 30px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 15px rgba(255,82,82,0.2); }
        
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }
        .metric-card { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 10px; padding: 25px; position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
        .metric-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background-color: #1f365c; }
        .metric-card.success::before { background-color: #00e676; }
        .metric-card.danger::before { background-color: #ff5252; }
        
        .card-label { color: #7f8c8d; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
        .card-value { font-size: 32px; font-weight: 700; color: #ffffff; font-family: 'Courier New', Courier, monospace; }
        
        .footer-card { background-color: #0d1527; border: 1px solid #1a2b49; border-radius: 10px; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        .footer-text { color: #7f8c8d; font-size: 13px; }
        .footer-time { color: #00e676; font-weight: 600; font-family: monospace; font-size: 14px; }
    </style>
    <script> setTimeout(function(){ location.reload(); }, 10000); </script>
</head>
<body>
    <div class="navbar">
        <div class="nav-logo">TRADER<span>NO_CORRE</span></div>
        <div class="nav-status">
            <div class="badge">Matrix Link Active</div>
            <a href="/logout" class="logout-btn">Desconectar</a>
        </div>
    </div>

    <div class="main-container">
        {% if dados.drawdown > 4.5 %}
        <div class="alert-zone">🚨 OPERAÇÃO EM RISCO CRÍTICO: Drawdown flutuante muito próximo do limite máximo de exclusão diária. O módulo Mentor EA iniciará a blindagem automática caso necessário.</div>
        {% endif %}

        <div class="metrics-grid">
            <div class="metric-card success">
                <div class="card-label">Saldo de Conta (Balance)</div>
                <div class="card-value">$ {{ dados.saldo }}</div>
            </div>
            <div class="metric-card success">
                <div class="card-label">Capital Flutuante (Equity)</div>
                <div class="card-value">$ {{ dados.equidade }}</div>
            </div>
            <div class="metric-card {% if dados.drawdown > 3.0 %}danger{% else %}success{% endif %}">
                <div class="card-label">Drawdown de Risco Atual</div>
                <div class="card-value">{{ dados.drawdown }}%</div>
            </div>
        </div>

        <div class="footer-card">
            <div class="footer-text">Sincronização de telemetria MetaTrader 5 (MT5 Gateway)</div>
            <div class="footer-time">Último pulso: {{ dados.data }}</div>
        </div>
    </div>
</body>
</html>
"""

# --- ROTAS INTERNAS DO SERVIDOR ---

@app.route('/atualizar-dados', methods=['POST'])
def atualizar_dados():
    dados = request.get_json()
    saldo = dados.get('saldo')
    equidade = dados.get('equidade')
    drawdown = dados.get('drawdown')
    
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

@app.route('/', methods=['GET', 'POST'])
def principal():
    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        if senha_digitada == SENHA_DE_ACESSO:
            session['logado'] = True
            return redirect('/')
        else:
            return render_template_string(TELA_LOGIN_HTML, erro="Senha inválida para este terminal.")

    if not session.get('logado'):
        return render_template_string(TELA_LOGIN_HTML, erro=None)

    conn = obter_conexao()
    cur = conn.cursor()
    cur.execute("SELECT saldo, equidade, drawdown, to_char(data_hora, 'DD/MM/YYYY HH24:MI:SS') FROM metricas_conta ORDER BY id DESC LIMIT 1")
    linha = cur.fetchone()
    cur.close()
    conn.close()

    if linha:
        # Puxa cada coluna individual do banco de dados na ordem exata
        dados_atuais = {
            "saldo": f"{linha[0]:,.2f}",
            "equidade": f"{linha[1]:,.2f}",
            "drawdown": f"{linha[2]:.2f}",
            "data": linha[3]
        }
    else:
        dados_atuais = {"saldo": "0.00", "equidade": "0.00", "drawdown": "0.00", "data": "Aguardando primeiro sinal técnico..."}

    return render_template_string(PAINEL_HTML, dados=dados_atuais)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
