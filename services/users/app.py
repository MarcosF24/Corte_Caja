import os
from flask import Flask, request, jsonify
import pymysql
from pymysql.cursors import DictCursor

# .env solo en local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

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
    return jsonify({"status": "ok", "service": "users"}), 200


@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    """
    Lista todos los usuarios registrados (sin mostrar la contraseña).
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
        return jsonify({"error": str(e)}), 500


@app.route("/usuarios", methods=["POST"])
def crear_usuario():
    """
    Crea un nuevo usuario.
    Body esperado:
    {
        "email": "user@demo.com",
        "password": "123456",
        "nombre": "Nombre Apellido",
        "rol": "CAJERO" | "GERENTE" | "ADMIN" (opcional, por defecto CAJERO)
    }
    """
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")
    nombre = data.get("nombre")
    rol = data.get("rol", "CAJERO")

    if not email or not password or not nombre:
        return jsonify({"error": "email, password y nombre son obligatorios"}), 400

    if rol not in ("GERENTE", "CAJERO", "ADMIN"):
        return jsonify({"error": "rol inválido"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (email, password, nombre, rol)
                VALUES (%s, %s, %s, %s)
                """,
                (email, password, nombre, rol)
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

@app.route("/usuarios/<int:user_id>", methods=["DELETE"])
def eliminar_usuario(user_id):
    """
    Elimina un usuario por id.
    De momento dejamos la validación de "no borrar gerente principal"
    al frontend (no le muestra el botón).
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Verificar que exista
            cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                conn.close()
                return jsonify({"error": "Usuario no encontrado"}), 404

            cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
            conn.commit()
        conn.close()
        return jsonify({"message": "Usuario eliminado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Local
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))
    app.run(host="0.0.0.0", port=port, debug=True)

# Handler para Lambda
try:
    import awsgi

    def handler(event, context):
        return awsgi.response(app, event, context)
except ImportError:
    pass
