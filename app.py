from flask import (Flask, jsonify, request, render_template, \
make_response, flash, url_for, send_from_directory)
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import hashlib, json, os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLER = os.path.join(BASE_DIR, "static")

def create_app():
    app = Flask(
    __name__,
    template_folder='files',
    static_url_path='',
    static_folder='files/static'
    )

    app.config['MYSQL_HOST'] = os.getenv('BD_SERVER')
    app.config['MYSQL_USER'] = os.getenv('BD_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('BD_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('BD_BD')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLER

    return app

app = create_app()

mysql = MySQL(app)

@app.route('/static/img/<path:filename>') 
def send_file(filename): 
    return send_from_directory(app.config['UPLOAD_FOLDER'] + '/img/', filename)

@app.route('/login/', methods=['POST'])
def iniciar_sesion():
    response = {}
    cur = mysql.connection.cursor()
    data = request.form
    query = (
        "SELECT * FROM USUARIO WHERE EMAIL = '"
        + data["email"] +
        "' AND PWD = sha2('"
        + data["pwd"] + "', 512);"
    )
    cur.execute(query)
    mysql.connection.commit()
    row = cur.fetchone()
    if row:
        response = make_response(json.dumps(
            {
                'exito': True,
                'desc': 'Bienvenido ' + row[1],
                'usrinfo': {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "pais": row[3]
                }
            }
        ))
        response.set_cookie('logged', 'true')
        response.set_cookie('usuario', str(row[0]))
    else:
        response = make_response(json.dumps(
            {
                'exito': False,
                'desc': 'Error en usuario o contraseña.'
            }
        ))
        return response, 403
    return response

@app.route('/obtener_publicaciones/<usrid>', methods=['GET'])
def get_publicaciones(usrid):
    response = {}
    response["publicaciones"] = []

    cur = mysql.connection.cursor()
    cur.callproc('ARMAR_LISTA_PUBLICACIONES', [usrid])
    rows = cur.fetchall()

    for publicacion in rows:
        response["publicaciones"].append({
            "id": publicacion[0],
            "titulo": publicacion[1],
            "texto": publicacion[2],
            "corazones": publicacion[3],
            "comentarios": publicacion[4],
            "bookmark": bool(publicacion[5])
        })
    cur.close()
    return response

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=1000, host='0.0.0.0')