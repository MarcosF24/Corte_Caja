import os
from datetime import datetime, timedelta, timezone

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import jwt
import awsgi  # pip install awsgi

# Cargar variables de entorno en local (.env)
load_dotenv()

app = Flask(__name__)

# ================== CONFIGURACIÓN JWT ==================

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
JWT_EXP_MIN = int(os.getenv("JWT_EXP_MIN", "60"))

# DEMO: usuarios quemados. Luego se cambian por BD / microservicio de usuarios.
USERS = {
    "cajero@demo.com": {
        "password": "123456",
        "role": "CAJERO"
    },
    "gerente@demo.com": {
        "password": "123456",
        "role": "GERENTE"
    },
}

# ================== RUTAS ==================

@app.post("/auth/login")
def login():
    """
    Endpoint de login.
    Espera: { "email": "cajero@demo.com", "password": "123456" }
    Responde: { "token": "...", "role": "CAJERO" }
    """
    data = request.get_json() or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Faltan credenciales"}), 400

    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"message": "Credenciales inválidas"}), 401

    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXP_MIN)

    payload = {
        "sub": email,
        "role": user["role"],
        "exp": exp
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return jsonify({
        "token": token,
        "role": user["role"]
    }), 200


@app.get("/auth/me")
def me():
    """
    Devuelve los datos del usuario a partir del JWT.
    Header: Authorization: Bearer <token>
    """
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return jsonify({"message": "No token"}), 401

    token = auth.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify({
            "user": payload.get("sub"),
            "role": payload.get("role")
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expirado"}), 401
    except Exception:
        return jsonify({"message": "Token inválido"}), 401


# ================== HANDLER PARA LAMBDA ==================

def handler(event, context):
    """
    Punto de entrada para AWS Lambda.
    En la consola de Lambda debes poner:
    Handler: app.handler
    """
    return awsgi.response(app, event, context)


# ================== EJECUCIÓN LOCAL ==================

if __name__ == "__main__":
    # Para desarrollo local
    app.run(host="0.0.0.0", port=8001, debug=True)
