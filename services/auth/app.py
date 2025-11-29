import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
import jwt
import pymysql
from pymysql.cursors import DictCursor

# .env en local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "super_secreto_en_dev")
JWT_EXP_MIN = int(os.getenv("JWT_EXP_MIN", "60"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "corte_caja"),
    "cursorclass": DictCursor
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def create_token(email: str, role: str):
    exp = datetime.utcnow() + timedelta(minutes=JWT_EXP_MIN)
    payload = {
        "sub": email,
        "role": role,
        "exp": exp
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@app.route("/auth/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "auth"}), 200


@app.route("/auth/login", methods=["POST"])
def login():
    """
    Login contra la tabla 'usuarios' en MySQL.
    Espera:
    {
      "email": "user@demo.com",
      "password": "123456"
    }
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email y password son obligatorios"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT email, password, rol FROM usuarios WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({"message": f"Error de base de datos: {e}"}), 500

    # Validar credenciales (password en texto plano para simplificar)
    if not user or user["password"] != password:
        return jsonify({"message": "Credenciales inválidas"}), 401

    token = create_token(user["email"], user["rol"])

    return jsonify({
        "token": token,
        "role": user["rol"]
    }), 200


@app.route("/auth/me", methods=["GET"])
def me():
    """
    Devuelve el usuario actual a partir del token JWT.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"message": "Token no proporcionado"}), 401

    token = auth_header.split(" ", 1)[1]

    payload = decode_token(token)
    if not payload:
        return jsonify({"message": "Token inválido o expirado"}), 401

    return jsonify({
        "user": payload["sub"],
        "role": payload["role"]
    }), 200


# Local
if __name__ == "__main__":
    app.run(debug=True)


# Handler para Lambda
try:
    import awsgi

    def handler(event, context):
        return awsgi.response(app, event, context)
except ImportError:
    pass
