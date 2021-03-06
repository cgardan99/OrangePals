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

# publicaciones
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
            "bookmark": bool(publicacion[5]),
            "es_mio": bool(publicacion[6]),
            "fecha": publicacion[7]
        })
    cur.close()
    return response


# publicaciones bookmarks
@app.route('/bmarks/<usrid>', methods=['GET'])
def get_publicaciones_marcadas(usrid):
    response = {}
    response["publicaciones"] = []

    cur = mysql.connection.cursor()
    cur.callproc('ARMAR_LISTA_PUBLICACIONES_BMARKS', [usrid])
    rows = cur.fetchall()

    for publicacion in rows:
        response["publicaciones"].append({
            "id": publicacion[0],
            "titulo": publicacion[1],
            "texto": publicacion[2],
            "corazones": publicacion[3],
            "comentarios": publicacion[4],
            "bookmark": bool(publicacion[5]),
            "es_mio": bool(publicacion[6]),
            "fecha": publicacion[7]
        })
    cur.close()
    return response


# publicaciones mias
@app.route('/mias/<usrid>', methods=['GET'])
def get_mis_publicaciones(usrid):
    response = {}
    response["publicaciones"] = []

    cur = mysql.connection.cursor()
    cur.callproc('ARMAR_LISTA_PUBLICACIONES_MIA', [usrid])
    rows = cur.fetchall()

    for publicacion in rows:
        response["publicaciones"].append({
            "id": publicacion[0],
            "titulo": publicacion[1],
            "texto": publicacion[2],
            "corazones": publicacion[3],
            "comentarios": publicacion[4],
            "bookmark": bool(publicacion[5]),
            "es_mio": bool(publicacion[6]),
            "fecha": publicacion[7]
        })
    cur.close()
    return response

#######################    Cambios Mosqueda    ####################################
#Altas de publicaciones
@app.route('/add_publicacion/', methods=['POST'])
def crear_publicacion():
    response = {}
    #data = json.loads(request.data)
    data = request.form
    cur = mysql.connection.cursor()
    query = ("INSERT INTO PUBLICACION (TEXTO_PUBLICACION"
    ",USUARIO_ID,TITULO,F_PUBLICACION) VALUES ('"
    + str(data['TEXTO_PUBLICACION']) + "', '"
    + str(data['USUARIO_ID']) + "', '"
    + str(data['TITULO']) + "', "
    + "NOW()" + ");"
    )
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'id_insertado': last_id
    }
    cur.close()
    return jsonify(response)

#Bajas de publicaciones
@app.route('/delete_publicacion/<id>', methods=['GET'])
def eliminar_publicaciones(id):
    response = {}
    response["publicaciones"] = []

    cur = mysql.connection.cursor()
    query = "DELETE FROM TAG_PUBLICACION WHERE PUBLICACION_ID = "+str(id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM COMENTARIO WHERE PUBLICACION_ID = "+str(id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM CORAZON WHERE PUBLICACION_ID = "+str(id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM BMARK WHERE PUBLICACION_ID = "+str(id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM PUBLICACION WHERE ID = "+str(id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()


    response = {
        'desc':"publicacion eliminada"
    }

    
    return response


#Altas de comentarios
@app.route('/add_comentario/', methods=['POST'])
def crear_comentario():
    response = {}
    data = request.form
    cur = mysql.connection.cursor()
    query = ("INSERT INTO COMENTARIO (TEXTO, USUARIO_ID"
    ",PUBLICACION_ID,COMENTARIO_ID,F_PUBLICACION) VALUES ('"
    + str(data['TEXTO']) + "', '"
    + str(data['USUARIO_ID']) + "', '"
    + str(data['PUBLICACION_ID']) + "', '"
    + str(data['COMENTARIO_ID']) + "', "
    + "NOW()" + ");"    
    )
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'id_insertado': last_id
    }
    cur.close()
    return jsonify(response)
    

#Bajas de comentarios
@app.route('/delete_comentario/<id>', methods=['GET'])
def eliminar_comentarios(id):
    response = {}
    response["comentarios"] = []
    
    cur = mysql.connection.cursor()
    query = "DELETE FROM CORAZON WHERE comentario_id = "+str(id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM COMENTARIO WHERE ID = " + str(id) + ";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()

    response = {
        'desc':"comentario eliminado"
    }

    cur.close()
    return response

#Altas de corazon
@app.route('/toggle_corazon/', methods=['POST'])
def toggle_corazon():
    response = {}
    data = request.form
    cur = mysql.connection.cursor()

    liked = True if data['LIKED'] == "true" else False

    if not liked:
        query =  ("INSERT INTO CORAZON (PUBLICACION_ID"
        ", USUARIO_ID, FECHA) VALUES ('"
        + str(data['PUBLICACION_ID']) + "', '"
        + str(data['USUARIO_ID']) + "', "
        + "NOW()" + ");"
        )
    else:
        query = ("DELETE FROM CORAZON WHERE PUBLICACION_ID = " + str(data['PUBLICACION_ID']) + " AND USUARIO_ID = " + str(data['USUARIO_ID']) + ";")  

    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'id_insertado': last_id,
        'desc': "Reacción eliminada" if liked else "Reacción enviada" 
    }
    cur.close()
    return jsonify(response)


#Altas de corazon
@app.route('/toggle_corazon_cm/', methods=['POST'])
def toggle_corazon_cm():
    response = {}
    data = request.form
    cur = mysql.connection.cursor()

    liked = True if data['LIKED'] == "true" else False

    if not liked:
        query =  ("INSERT INTO CORAZON (COMENTARIO_ID"
        ", USUARIO_ID, FECHA) VALUES ('"
        + str(data['COMENTARIO_ID']) + "', '"
        + str(data['USUARIO_ID']) + "', "
        + "NOW()" + ");"
        )
    else:
        query = ("DELETE FROM CORAZON WHERE COMENTARIO_ID = " + str(data['COMENTARIO_ID']) + " AND USUARIO_ID = " + str(data['USUARIO_ID']) + ";")  

    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'id_insertado': last_id,
        'desc': "Reacción eliminada" if liked else "Reacción enviada" 
    }
    cur.close()
    return jsonify(response)

    
#Bajas de corazon
@app.route('/delete_corazon/<id>', methods=['GET'])
def eliminar_corazon(id):
    response = {}
    cur = mysql.connection.cursor()
    query = "DELETE FROM CORAZON WHERE ID = " + str(id) + ";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()

    response = {
        'exito':"corazon eliminado"
    }

    cur.close()
    return response

##########################################################################


########################   ACTUALIZAR PUBLICACIONES   ########################
@app.route('/update_publicacion/<publication_id>', methods=['POST'])
def actualizar_publicacion(publication_id):
    response = {}
    data = request.form

    cur = mysql.connection.cursor()
    query = ("UPDATE PUBLICACION SET TEXTO_PUBLICACION = '" + str(data['TEXTO_PUBLICACION']) + "', "
    " TITULO = '" + str(data['TITULO']) +"' WHERE ID = " + str(publication_id) + ";")
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    cur.close()

    etiquetas = data["ETIQUETAS"].split(" ")
    for i in etiquetas:
        cur = mysql.connection.cursor()
        cur.callproc('creacion_tag', [publication_id, i])
        mysql.connection.commit()
        cur.close()

    response = {
        'exito': isinstance(last_id,int),
        'id_insertado': last_id,
        'desc': "Modificacion realizada con éxito."
    }
    return jsonify(response)

######################## OBTENER TODAS LAS PUBLICACIONES  ########################
@app.route('/get_publicaciones/', methods=['GET'])
def obtener_publicaciones():
    response = {}
    response["publicaciones"] = []
    cur = mysql.connection.cursor()
    query = ("SELECT ID, TITULO, TEXTO_PUBLICACION, F_PUBLICACION, USUARIO_ID FROM PUBLICACION")
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    for publicacion in rows:
        response["publicaciones"].append({
            "ID": publicacion[0],
            "TITULO": publicacion[1],
            "TEXTO_PUBLICACION": publicacion[2],
            "F_PUBLICACION": publicacion[3],
            "USUARIO_ID": publicacion[4]
        })
    cur.close()
    return response


###########################    OBTENER UNA PUBLICACION EN ESPECIFICO    ###########################
@app.route('/get_publicacion/<publication_id>', methods=['GET'])
def obtener_publicacion(publication_id):
    response = {}
    cur = mysql.connection.cursor()
    query = ("SELECT ID, TITULO, TEXTO_PUBLICACION, F_PUBLICACION, USUARIO_ID FROM" 
    " PUBLICACION WHERE ID = " + str(publication_id) + ";")
    cur.execute(query)
    mysql.connection.commit()
    publicacion = cur.fetchone()
    response["publicacion"] = {
        "ID": publicacion[0],
        "TITULO": publicacion[1],
        "TEXTO_PUBLICACION": publicacion[2],
        "F_PUBLICACION": publicacion[3],
        "USUARIO_ID": publicacion[4]
    }
    cur.close()

    cur = mysql.connection.cursor()
    query = ("SELECT t.nombre FROM" 
    " tag t, tag_publicacion tg WHERE tg.publicacion_ID = " + str(publication_id) +
    " and tg.tag_id = t.id;")
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    response["publicacion"]["TAGS"] = ""
    for tag in rows:
        response["publicacion"]["TAGS"] += (tag[0] + " ")
    cur.close()
    return response


##############################  ACTUALIZAR USUARIO  ##############################
@app.route('/get_user/<user_id>', methods=['GET'])
def obtener_usuario(user_id):
    response = {}
    data = request.form
    cur = mysql.connection.cursor()
    query = ("SELECT U.USERNAME, U.EMAIL, P.NOMBRE, P.ID FROM USUARIO U, PAIS P WHERE P.ID = U.PAIS AND U.ID = " + str(user_id) + ";")
    cur.execute(query)
    mysql.connection.commit()
    row = cur.fetchone()
    last_id = cur.lastrowid
    response = {
        'USERNAME': row[0],
        'PAIS': row[2],
        'EMAIL': row[1],
        'PAIS_ID': row[3]
    }
    cur.close()
    return jsonify(response)


##############################  ACTUALIZAR USUARIO  ##############################
@app.route('/update_user/<user_id>', methods=['POST'])
def actualizar_usuario(user_id):
    response = {}
    data = request.form
    cur = mysql.connection.cursor()
    query = ("UPDATE USUARIO SET USERNAME = '" + str(data['USERNAME']) + "', "
    " EMAIL = '" + str(data['EMAIL']) +"', PAIS = " + str(data['PAIS']) + " WHERE ID = " + str(user_id) + ";")
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'usuario_actualizado': last_id,
        'desc': "Usuario actualizado."
    }
    cur.close()
    return jsonify(response)


##############################  ACTUALIZAR USUARIO  ##############################
@app.route('/create/', methods=['POST'])
def crear_usuario():
    response = {}
    data = request.form
    cur = mysql.connection.cursor()
    query = ("INSERT INTO USUARIO (USERNAME, EMAIL, PAIS, PWD) VALUES ("
        "'" + data["USERNAME"] + "',"
        "'" + data["EMAIL"] + "',"
        "'" + data["PAIS"] + "',"
        " SHA2('"+ data["PWD"] +"', 512));")
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'usuario_actualizado': last_id,
        'desc': "El usuario ha sido creado."
    }
    cur.close()
    return jsonify(response)


##############################  ELIMINAR USUARIO  ##############################
@app.route('/delete_user/<user_id>', methods=['GET'])
def eliminar_usuario(user_id):
    response = {}

    cur = mysql.connection.cursor()
    query = "DELETE FROM comentario WHERE usuario_id = "+str(user_id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM bmark WHERE USUARIO_ID = "+str(user_id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM CORAZON WHERE usuario_id = "+str(user_id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM TAG_PUBLICACION WHERE PUBLICACION_ID IN (SELECT DISTINCT ID FROM PUBLICACION WHERE USUARIO_ID = "+str(user_id)+");"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM PUBLICACION WHERE usuario_iD = "+str(user_id)+";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor()
    query = "DELETE FROM USUARIO WHERE ID = " + str(user_id) + ";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    response = {
        'desc':"usuario eliminado."
    }

    cur.close()
    return response
###############################################################################

#Altas de bookmark
@app.route('/toggle_bmark/',methods=['POST'])
def crear_bmarks():
    data = request.form
    cur = mysql.connection.cursor()
    marcador = True if data['MARCADO'] == "true" else False

    if not marcador:
        query = ("INSERT INTO BMARK (PUBLICACION_ID,USUARIO_ID) VALUES ('"
        + str(data['PUBLICACION_ID']) + "', '"
        + str(data['USUARIO_ID']) + "');"
        )
    else:
        query = ("DELETE FROM BMARK WHERE PUBLICACION_ID = " + str(data['PUBLICACION_ID']) + " AND USUARIO_ID = " + str(data['USUARIO_ID']) + ";")

    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    last_id = cur.lastrowid
    response = {
        'exito': isinstance(last_id,int),
        'id_insertado': last_id,
        'desc': "Bookmark eliminado" if marcador else "Bookmark añadido"
    }
    cur.close()
    return jsonify(response)

#Bajas de bmark
@app.route('/delete_bmark/<id>',methods=['GET'])
def eleminar_bmark(id):
    response = {}
    response["bmarks"] = []
    cur = mysql.connection.cursor()
    query = "DELETE FROM BMARK WHERE ID = " + str(id) + ";"
    cur.execute(query)
    mysql.connection.commit()
    rows = cur.fetchall()
    response = {
        'exito':"bmark eliminado"
    }
    cur.close()
    return response



@app.route('/detalle_publicacion/<usrid>/<publicacion_id>', methods=['GET'])
def get_publicacion(usrid, publicacion_id):
    response = {}
    response["comentarios"] = []

    cur = mysql.connection.cursor()
    cur.callproc('ARMAR_PUBLICACION', [publicacion_id, usrid])
    rows = cur.fetchall()

    response["publicacion"] = {
        "id": rows[0][0],
        "titulo": rows[0][5],
        "texto": rows[0][1],
        "likes": rows[0][9],
        "bookmark": bool(rows[0][7]),
        "es_mio": bool(rows[0][6]),
        "username": rows[0][2],
        "n_comentarios": rows[0][10],
        "fecha": rows[0][4],
        "user_id": rows[0][3],
        "like_mio": bool(rows[0][8])
    }

    response["publicacion"]["comentarios"] = []

    cur.close()

    cur = mysql.connection.cursor()
    cur.callproc('armar_comentarios', [publicacion_id, usrid])
    rows = cur.fetchall()
    for comentario in rows:
        response["publicacion"]["comentarios"].append({
            "comentario_id": comentario[0],
            "usuario_id": comentario[1],
            "username": comentario[2],
            "texto": comentario[5],
            "publicacion_id": comentario[3],
            "fecha": comentario[4],
            "likes": comentario[8],
            "like_mio": bool(comentario[7]),
            "es_mio": bool(comentario[6])
        })
    cur.close()
    return response





@app.route('/publicar_comentario/<pubid>/<usrid>', methods=['POST'])
def publicar_comentario(pubid, usrid):
    response = {}
    cur = mysql.connection.cursor()
    data = request.form

    query = (
        "INSERT INTO COMENTARIO (USUARIO_ID, PUBLICACION_ID, F_PUBLICACION, TEXTO) VALUES ("
        + str(usrid) + ","
        + str(pubid) + ","
        "now(),"
        + "'" + data["texto"] + "'"
        ");"
    )
    cur.execute(query)
    mysql.connection.commit()

    cur.close()
    response["desc"] = "Comentario publicado con éxito"
    response["id"] = pubid
    return response


@app.route('/get_comentario/<cmid>', methods=['GET'])
def get_comentario(cmid):
    response = {}
    cur = mysql.connection.cursor()

    query = (
        "SELECT TEXTO FROM COMENTARIO WHERE ID = " + str(cmid) + ";"
    )
    cur.execute(query)
    mysql.connection.commit()
    row = cur.fetchone()

    response["texto"] = row[0]

    cur.close()
    return response


@app.route('/update_comentario/<cmid>', methods=['POST'])
def update_comentario(cmid):
    response = {}
    cur = mysql.connection.cursor()
    data = request.form

    query = (
        "UPDATE COMENTARIO SET TEXTO = '" + data["TEXTO"] + "' WHERE ID = " + str(cmid) + ";"
    )
    cur.execute(query)
    mysql.connection.commit()
    row = cur.fetchone()
    response["desc"] = "Comentario actualizado."
    cur.close()
    return response


@app.route('/publicar/<usrid>', methods=['POST'])
def publicar(usrid):
    response = {}
    cur = mysql.connection.cursor()
    data = request.form
    query = (
        "INSERT INTO PUBLICACION (TEXTO_PUBLICACION, USUARIO_ID, F_PUBLICACION, TITULO) VALUES ("
        "'" + data["texto"] + "',"
        + str(usrid) + ","
        "now(),"
        + "'" + data["titulo"] + "'"
        ");"
    )
    cur.execute(query)
    mysql.connection.commit()
    last_id = cur.lastrowid
    
    etiquetas = data["etiquetas"].split(" ")
    for i in etiquetas:
        cur = mysql.connection.cursor()
        cur.callproc('creacion_tag', [last_id, i])
        mysql.connection.commit()
        cur.close()

    cur.close()
    response["desc"] = "Publicado con éxito"
    return response

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=1000, host='0.0.0.0')
