import os
from flask import Flask, request, jsonify
import pymysql
from pymysql.cursors import DictCursor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # En Lambda no pasa nada si dotenv no existe
    pass

app = Flask(__name__)

# Configuración DB desde variables de entorno
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "corte_caja"),
    "cursorclass": DictCursor
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


@app.route("/health", methods=["GET"])
def health():
    """Endpoint simple para probar que el servicio está vivo."""
    return jsonify({"status": "ok", "service": "users"}), 200


@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    """
    Lista todos los usuarios registrados.
    De momento SIN autenticación para simplificar las pruebas.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, nombre, rol, fecha_creacion "
                "FROM usuarios ORDER BY id"
            )
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        # En producción loggearíamos el error; aquí lo devolvemos directo
        return jsonify({"error": str(e)}), 500


@app.route("/usuarios", methods=["POST"])
def crear_usuario():
    """
    Crea un nuevo usuario.
    Body esperado:
    {
        "email": "user@demo.com",
        "nombre": "Nombre Apellido",
        "rol": "CAJERO" | "GERENTE" | "ADMIN" (opcional, por defecto CAJERO)
    }
    """
    data = request.get_json() or {}

    email = data.get("email")
    nombre = data.get("nombre")
    rol = data.get("rol", "CAJERO")

    if not email or not nombre:
        return jsonify({"error": "email y nombre son obligatorios"}), 400

    if rol not in ("GERENTE", "CAJERO", "ADMIN"):
        return jsonify({"error": "rol inválido"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (email, nombre, rol)
                VALUES (%s, %s, %s)
                """,
                (email, nombre, rol)
            )
            conn.commit()
            nuevo_id = cursor.lastrowid

            cursor.execute(
                "SELECT id, email, nombre, rol, fecha_creacion "
                "FROM usuarios WHERE id = %s",
                (nuevo_id,)
            )
            usuario = cursor.fetchone()
        conn.close()

        return jsonify(usuario), 201

    except pymysql.err.IntegrityError:
        # Por el UNIQUE en email
        return jsonify({"error": "El correo ya está registrado"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Para correr en local
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))
    app.run(host="0.0.0.0", port=port, debug=True)


# Handler para AWS Lambda
try:
    import awsgi

    def handler(event, context):
        return awsgi.response(app, event, context)
except ImportError:
    # En local no usamos awsgi
    pass
