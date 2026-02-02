import sqlite3

conn = sqlite3.connect('usuarios.db')
cursor = conn.cursor()

# Cria a tabela
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL
    )
''')

# Insere um usuário de teste (Senha em texto puro para o exemplo, mas use hash em produção)
try:
    cursor.execute("INSERT INTO usuarios (email, senha) VALUES ('seu@email.com', '123')")
    conn.commit()
except:
    pass

conn.close()