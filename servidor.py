from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from engine_ia import EngineIA 

app = Flask(__name__)
CORS(app)

# Inicializa a IA uma única vez ao ligar o servidor
ia_engine = EngineIA().inicializar_sistema()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/ia')
def ia_page():
    return render_template('chat.html')

def validar_no_db(email, senha):
    try:
        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email, role FROM usuarios WHERE email=? AND senha=?", (email, senha))
        usuario = cursor.fetchone()
        conn.close()
        return usuario
    except sqlite3.OperationalError:
        return None

@app.route('/login', methods=['POST'])
def login_endpoint():
    dados = request.json
    usuario = validar_no_db(dados.get('email'), dados.get('senha'))
    if usuario:
        return jsonify({"status": "sucesso", "role": usuario[1]}), 200
    return jsonify({"status": "erro", "mensagem": "Credenciais inválidas"}), 401

@app.route('/perguntar', methods=['POST'])
def perguntar():
    dados = request.json
    pergunta = dados.get('mensagem')
    # A Engine processa a lógica complexa e o servidor apenas entrega
    res = ia_engine.invoke({"question": pergunta}) 
    return jsonify({"resposta": res["answer"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)