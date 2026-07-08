from flask import Flask, request, jsonify
import os
import psycopg2

app = Flask(__name__)

# Conexão automática com o banco de dados do Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def init_db():
    # Cria a tabela para salvar suas métricas se ela não existir
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS metricas_conta (
            id SERIAL PRIMARY KEY,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            saldo NUMERIC(10, 2),
            equidade NUMERIC(10, 2),
            drawdown NUMERIC(5, 2)
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/atualizar-dados', methods=['POST'])
def atualizar_dados():
    dados = request.get_json()
    
    saldo = dados.get('saldo')
    equidade = dados.get('equidade')
    drawdown = dados.get('drawdown')
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO metricas_conta (saldo, equidade, drawdown) VALUES (%s, %s, %s)",
        (saldo, equidade, drawdown)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"status": "sucesso", "mensagem": "Dados gravados no Render!"}), 200

@app.route('/', methods=['GET'])
def painel_visual():
    return "<h1>Painel MT5 Conectado e Ativo!</h1><p>Os graficos aparecerao aqui.</p>"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
