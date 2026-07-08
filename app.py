from flask import Flask, request, jsonify, render_template_string, session, redirect, url_value_preprocessor
import os
import psycopg2

app = Flask(__name__)
# Chave de segurança para proteger o seu login (pode deixar como está)
app.secret_key = "chave_secreta_super_segura_ftmo"

# Senha que você vai usar para entrar no seu site (Altere se quiser!)
SENHA_DE_ACESSO = "123456"

DATABASE_URL = os.environ.get('DATABASE_URL')

def obter_conexao():
    return psycopg2.connect(DATABASE_URL)

# --- TELA DE LOGIN (ESTILO FTMO) ---
TELA_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>FTMO Dashboard - Login</title>
    <style>
        body { background-color: #0b1528; color: white; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background-color: #12223d; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); text-align: center; width: 300px; }
        h2 { color: #00e676; margin-bottom: 25px; }
        input[type="password"] { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #203a61; border-radius: 4px; background-color: #0b1528; color: white; box-sizing: border-box; }
        button { background-color: #00e676; color: #0b1528; border: none; padding: 12px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #00b359; }
        .erro { color: #ff5252; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>FTMO MENTOR</h2>
        <p>Digite sua senha de acesso:</p>
        {% if erro %} <p class="erro">{{ erro }}</p> {% endif %}
        <form method="POST">
            <input type="password" name="senha" placeholder="Sua Senha" required>
            <button type="submit">Entrar no Painel</button>
        </form>
    </div>
</body>
</html>
"""

# --- TELA DO PAINEL VISUAL (ESTILO FTMO) ---
PAINEL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>FTMO MENTOR - Dashboard</title>
    <style>
        body { background-color: #0b1528; color: white; font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #12223d; padding-bottom: 15px; margin-bottom: 30px; }
        .logo { color: #00e676; font-size: 24px; font-weight: bold; }
        .logout { color: #ff5252; text-decoration: none; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background-color: #12223d; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border-left: 5px solid #203a61; }
        .card.sucesso { border-left-color: #00e676; }
        .card.perigo { border-left-color: #ff5252; }
        .card-titulo { color: #8aa1c4; font-size: 14px; text-transform: uppercase; margin-bottom: 10px; }
        .card-valor { font-size: 28px; font-weight: bold; }
        .alerta { background-color: #ff5252; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; text-align: center; }
    </style>
    <meta float-content="no-cache">
    <script> setTimeout(function(){ location.reload(); }, 10000); </script> <!-- Atualiza a tela sozinho a cada 10 segundos -->
</head>
<body>
    <div class="header">
        <div class="logo">FTMO MENTOR PANEL</div>
        <div>
            <span style="color: #8aa1c4; margin-right: 15px;">Status: <b style="color: #00e676;">CONECTADO AO MT5</b></span>
            <a href="/logout" class="logout">Sair</a>
        </div>
    </div>

    {% if dados.drawdown > 4.5 %}
    <div class="alerta">ALERTA: Você está muito próximo do limite de perda máxima diária! Cuidado!</div>
    {% endif %}

    <div class="grid">
        <div class="card sucesso">
            <div class="card-titulo">Saldo da Conta (Balance)</div>
            <div class="card-valor">$ {{ dados.saldo }}</div>
        </div>
        <div class="card sucesso">
            <div class="card-titulo">Capital Flutuante (Equity)</div>
            <div class="card-valor">$ {{ dados.equidade }}</div>
        </div>
        <div class="card {% if dados.drawdown > 3.0 %}perigo{% else %}sucesso{% endif %}">
            <div class="card-titulo">Drawdown Flutuante Atual</div>
            <div class="card-valor">{{ dados.drawdown }} %</div>
        </div>
    </div>

    <div class="card" style="border-left-color: #00e676;">
        <div class="card-titulo">Última Atualização do Servidor</div>
        <div style="font-size: 16px; margin-top: 5px; color: #00e676;">{{ dados.data }} (Horário Global GMT)</div>
    </div>
</body>
</html>
"""

# --- ROTAS DO SISTEMA ---

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
    # Se o usuário tentar logar
    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        if senha_digitada == SENHA_DE_ACESSO:
            session['logado'] = True
            return redirect('/')
        else:
            return render_template_string(TELA_LOGIN_HTML, erro="Senha incorreta! Tente novamente.")

    # Se não estiver logado, mostra a tela de login
    if not session.get('logado'):
        return render_template_string(TELA_LOGIN_HTML, erro=None)

    # Se estiver logado, busca o último dado gravado no cofre Postgres
    conn = obter_conexao()
    cur = conn.cursor()
    cur.execute("SELECT saldo, equidade, drawdown, data_hora FROM metricas_conta ORDER BY id DESC LIMIT 1")
    linha = cur.fetchone()
    cur.close()
    conn.close()

    if linha:
        dados_atuais = {"saldo": linha[0], "equidade": linha[1], "drawdown": linha[2], "data": linha[3]}
    else:
        dados_atuais = {"saldo": "0.00", "equidade": "0.00", "drawdown": "0.00", "data": "Sem dados enviados ainda"}

    return render_template_string(PAINEL_HTML, dados=dados_atuais)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
