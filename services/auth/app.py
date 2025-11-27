from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv; load_dotenv()
import os, jwt

app = Flask(__name__)

JWT_SECRET  = os.getenv("JWT_SECRET", "dev")
JWT_EXP_MIN = int(os.getenv("JWT_EXP_MIN", "60"))

# DEMO: usuarios en duro. Luego podrás validar contra Users Service.
USERS = {
    "cajero@demo.com":  {"password": "123456", "role": "cajero"},
    "gerente@demo.com": {"password": "123456", "role": "gerente"},
}

@app.post("/auth/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").lower().strip()
    pwd   = data.get("password") or ""
    user = USERS.get(email)
    if not user or user["password"] != pwd:
        return jsonify({"message": "Credenciales inválidas"}), 401

    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXP_MIN)
    token = jwt.encode({"sub": email, "role": user["role"], "exp": exp}, JWT_SECRET, algorithm="HS256")
    return jsonify({"token": token, "role": user["role"]})

@app.get("/auth/me")
def me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"message": "No token"}), 401
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify({"user": payload["sub"], "role": payload["role"]})
    except Exception:
        return jsonify({"message": "Token inválido"}), 401

if __name__ == "__main__":
    # Desarrollo local
    app.run(host="0.0.0.0", port=8001, debug=True)
