from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.security import generate_password_hash, check_password_hash

# --- 1. CONFIGURACIÓN ---
app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))

# --- LÓGICA HÍBRIDA (LOCAL vs AWS) ---
# Intenta leer la variable 'DATABASE_URL' (que pondremos en AWS).
# Si no existe, usa tu 'caja.db' local.
# Nota: AWS a veces da la URL como 'postgres://', pero SQLAlchemy necesita 'postgresql://'
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///' + os.path.join(basedir, 'caja.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
# --- 2. MODELOS DE TABLAS ---
class Corte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(10), nullable=False)
    turno = db.Column(db.String(50))
    hora = db.Column(db.String(10), nullable=True)
    cajero = db.Column(db.String(100), nullable=True)
    fondo_inicial = db.Column(db.Float, default=0)
    ventas_efectivo = db.Column(db.Float, default=0)
    ventas_tarjeta = db.Column(db.Float, default=0)
    gastos = db.Column(db.Float, default=0)
    observaciones = db.Column(db.Text, nullable=True)
    def __repr__(self):
        return f'<Corte {self.id} - {self.fecha} por {self.cajero}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cajero')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<User {self.nombre} ({self.email}) - {self.role}>'

# --- 3. RUTAS DE AUTENTICACIÓN Y USUARIOS ---
@app.route('/login', methods=['POST'])
def handle_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"status": "error", "message": "Email y contraseña requeridos"}), 400
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401
    return jsonify({
        "status": "ok",
        "tipo": user.role,
        "nombre": user.nombre or user.email
    })

@app.route('/usuario', methods=['POST'])
def add_user():
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    if not email or not password or not role or not nombre:
        return jsonify({"status": "error", "message": "Faltan campos (nombre, email, pass, rol)"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"status": "error", "message": "El correo ya está registrado"}), 400
    try:
        new_user = User(nombre=nombre, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "status": "ok",
            "message": f"Usuario {role} '{nombre}' creado exitosamente."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error interno: {e}"}), 500

@app.route('/usuarios', methods=['GET'])
def get_users():
    try:
        users_db = User.query.order_by(User.role.desc(), User.nombre).all()
        usuarios = []
        for user in users_db:
            usuarios.append({
                "id": user.id,
                "nombre": user.nombre,
                "email": user.email,
                "role": user.role
            })
        return jsonify({"status": "ok", "usuarios": usuarios})
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        return jsonify({"status": "error", "message": f"Error interno: {e}"}), 500

# --- ¡NUEVA RUTA PARA ELIMINAR USUARIO! ---
@app.route('/usuario/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
            
        # REGLA DE SEGURIDAD: No permitir eliminar al usuario ID 1 (admin principal)
        if user.id == 1:
            return jsonify({"status": "error", "message": "No se puede eliminar al administrador principal"}), 403

        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            "status": "ok",
            "message": f"Usuario '{user.email}' ha sido eliminado."
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar usuario: {e}")
        return jsonify({"status": "error", "message": f"Error interno: {e}"}), 500

# --- 4. RUTAS DE CORTE (Sin cambios) ---
@app.route('/guardar-corte', methods=['POST'])
def handle_guardar_corte():
    data = request.json
    try:
        nuevo_corte = Corte(
            fecha=data.get('fecha'), turno=data.get('turno'),
            hora=data.get('hora'), cajero=data.get('cajero'),
            fondo_inicial=float(data.get('fondoInicial', 0)),
            ventas_efectivo=float(data.get('ventasEfectivo', 0)),
            ventas_tarjeta=float(data.get('ventasTarjeta', 0)),
            gastos=float(data.get('gastos', 0)),
            observaciones=data.get('observaciones')
        )
        db.session.add(nuevo_corte)
        db.session.commit()
        return jsonify({"status": "ok", "message": "Corte guardado exitosamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error interno al guardar: {e}"}), 500

@app.route('/obtener-cortes', methods=['GET'])
def handle_obtener_cortes():
    try:
        filtro_fecha = request.args.get('fecha')
        filtro_cajero = request.args.get('cajero')
        query = Corte.query
        if filtro_fecha:
            query = query.filter(Corte.fecha == filtro_fecha)
        if filtro_cajero:
            query = query.filter(Corte.cajero.ilike(f"%{filtro_cajero}%"))
        cortes_db = query.order_by(Corte.fecha.desc(), Corte.id.desc()).all()
        
        total_ventas, total_gastos, neto_total, historial = 0, 0, 0, []
        
        for corte in cortes_db:
            ventas_calculadas = corte.ventas_efectivo + corte.ventas_tarjeta
            monto_final_calculado = (corte.fondo_inicial + corte.ventas_efectivo) - corte.gastos
            total_ventas += ventas_calculadas
            total_gastos += corte.gastos
            neto_total += monto_final_calculado
            historial.append({
                "id": corte.id, "fecha": corte.fecha, "hora": corte.hora,
                "cajero": corte.cajero, "fondo_inicial": corte.fondo_inicial,
                "monto_final": monto_final_calculado, "ventas": ventas_calculadas,
                "gastos": corte.gastos,
            })
        respuesta = {"summary": {"total_ventas": total_ventas, "total_gastos": total_gastos, "neto_total": neto_total }, "history": historial}
        return jsonify(respuesta)
    except Exception as e:
        print(f"Error al obtener cortes: {e}")
        return jsonify({"status": "error", "message": f"Error interno: {e}"}), 500

@app.route('/corte/<int:corte_id>', methods=['GET'])
def handle_obtener_detalle_corte(corte_id):
    try:
        corte = Corte.query.get_or_404(corte_id)
        ventas_totales = corte.ventas_efectivo + corte.ventas_tarjeta
        neto_calculado = (corte.fondo_inicial + corte.ventas_efectivo) - corte.gastos
        detalle = {
            "id": corte.id, "fecha": corte.fecha, "hora": corte.hora,
            "cajero": corte.cajero, "turno": corte.turno, "fondo_inicial": corte.fondo_inicial,
            "ventas_efectivo": corte.ventas_efectivo, "ventas_tarjeta": corte.ventas_tarjeta,
            "total_ventas": ventas_totales, "gastos": corte.gastos,
            "neto_calculado": neto_calculado, "observaciones": corte.observaciones or "No se registraron observaciones."
        }
        return jsonify(detalle)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error interno: {e}"}), 500
# --- ¡NUEVA RUTA PARA ELIMINAR CORTE! ---
@app.route('/corte/<int:corte_id>', methods=['DELETE'])
def delete_corte(corte_id):
    try:
        corte = Corte.query.get(corte_id)
        if not corte:
            return jsonify({"status": "error", "message": "Corte no encontrado"}), 404

        db.session.delete(corte)
        db.session.commit()
        return jsonify({"status": "ok", "message": "Corte eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error al eliminar: {e}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)