import os
from flask import Flask, request, jsonify
import pymysql
from pymysql.cursors import DictCursor

# Cargar .env solo en local
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
    return jsonify({"status": "ok", "service": "cortes"}), 200


# ========= CORTES =========

@app.route("/cortes", methods=["GET"])
def listar_cortes():
    """
    Lista todos los cortes con info básica.
    Más adelante se puede filtrar por usuario/fecha.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.usuario_id, u.nombre AS usuario_nombre,
                       c.monto_inicial, c.monto_final,
                       c.fecha_inicio, c.fecha_fin, c.estado
                FROM cortes c
                JOIN usuarios u ON u.id = c.usuario_id
                ORDER BY c.id DESC
            """)
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cortes", methods=["POST"])
def abrir_corte():
    """
    Abre un nuevo corte de caja.
    Body esperado:
    {
      "usuario_id": 2,
      "monto_inicial": 1000.00
    }
    Por ahora pasamos usuario_id directo; luego lo podemos sacar del token JWT.
    """
    data = request.get_json() or {}
    usuario_id = data.get("usuario_id")
    monto_inicial = data.get("monto_inicial")

    if not usuario_id or monto_inicial is None:
        return jsonify({"error": "usuario_id y monto_inicial son obligatorios"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cortes (usuario_id, monto_inicial, fecha_inicio, estado)
                VALUES (%s, %s, NOW(), 'ABIERTO')
                """,
                (usuario_id, monto_inicial)
            )
            conn.commit()
            corte_id = cursor.lastrowid

            cursor.execute("""
                SELECT id, usuario_id, monto_inicial, monto_final,
                       fecha_inicio, fecha_fin, estado
                FROM cortes
                WHERE id = %s
            """, (corte_id,))
            corte = cursor.fetchone()
        conn.close()
        return jsonify(corte), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cortes/<int:corte_id>/cerrar", methods=["POST"])
def cerrar_corte(corte_id):
    """
    Cierra un corte.
    Body esperado:
    {
      "monto_final": 1234.56
    }
    """
    data = request.get_json() or {}
    monto_final = data.get("monto_final")

    if monto_final is None:
        return jsonify({"error": "monto_final es obligatorio"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Validar que exista y esté abierto
            cursor.execute("SELECT * FROM cortes WHERE id = %s", (corte_id,))
            corte = cursor.fetchone()
            if not corte:
                conn.close()
                return jsonify({"error": "Corte no encontrado"}), 404
            if corte["estado"] == "CERRADO":
                conn.close()
                return jsonify({"error": "El corte ya está cerrado"}), 400

            cursor.execute("""
                UPDATE cortes
                SET monto_final = %s,
                    fecha_fin = NOW(),
                    estado = 'CERRADO'
                WHERE id = %s
            """, (monto_final, corte_id))
            conn.commit()

            cursor.execute("""
                SELECT id, usuario_id, monto_inicial, monto_final,
                       fecha_inicio, fecha_fin, estado
                FROM cortes
                WHERE id = %s
            """, (corte_id,))
            corte_actualizado = cursor.fetchone()
        conn.close()
        return jsonify(corte_actualizado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= MOVIMIENTOS =========

@app.route("/movimientos", methods=["POST"])
def registrar_movimiento():
    """
    Registra un movimiento en un corte.
    Body:
    {
      "corte_id": 1,
      "tipo": "INGRESO" | "EGRESO",
      "descripcion": "Venta X" ,
      "monto": 100.50
    }
    """
    data = request.get_json() or {}
    corte_id = data.get("corte_id")
    tipo = data.get("tipo")
    descripcion = data.get("descripcion", "")
    monto = data.get("monto")

    if not corte_id or not tipo or monto is None:
        return jsonify({"error": "corte_id, tipo y monto son obligatorios"}), 400

    if tipo not in ("INGRESO", "EGRESO"):
        return jsonify({"error": "tipo debe ser INGRESO o EGRESO"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Validar corte abierto
            cursor.execute("SELECT estado FROM cortes WHERE id = %s", (corte_id,))
            corte = cursor.fetchone()
            if not corte:
                conn.close()
                return jsonify({"error": "Corte no encontrado"}), 404
            if corte["estado"] != "ABIERTO":
                conn.close()
                return jsonify({"error": "El corte no está abierto"}), 400

            cursor.execute("""
                INSERT INTO movimientos (corte_id, tipo, descripcion, monto)
                VALUES (%s, %s, %s, %s)
            """, (corte_id, tipo, descripcion, monto))
            conn.commit()
        conn.close()
        return jsonify({"message": "Movimiento registrado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/movimientos/<int:corte_id>", methods=["GET"])
def listar_movimientos(corte_id):
    """
    Lista movimientos de un corte específico.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, tipo, descripcion, monto, fecha
                FROM movimientos
                WHERE corte_id = %s
                ORDER BY fecha DESC
            """, (corte_id,))
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/guardar-corte", methods=["POST"])
def guardar_corte_completo():
    """
    Endpoint pensado para el formulario de corte.html.

    Body esperado:
    {
      "usuario_id": 2,
      "fecha": "2025-11-29",           // opcional, podemos ignorarla y usar NOW()
      "turno": "Matutino",
      "fondoInicial": 1000,
      "ventasEfectivo": 2000,
      "ventasTarjeta": 1500,
      "gastos": 500,
      "observaciones": "Texto libre"
    }
    """
    data = request.get_json() or {}

    usuario_id = data.get("usuario_id")
    turno = data.get("turno")
    fondo_inicial = float(data.get("fondoInicial") or 0)
    ventas_efectivo = float(data.get("ventasEfectivo") or 0)
    ventas_tarjeta = float(data.get("ventasTarjeta") or 0)
    gastos = float(data.get("gastos") or 0)
    observaciones = data.get("observaciones") or ""

    if not usuario_id:
        return jsonify({"message": "usuario_id es obligatorio"}), 400

    # Neto calculado
    neto = fondo_inicial + ventas_efectivo + ventas_tarjeta - gastos

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1) Crear el corte directamente como CERRADO
            cursor.execute(
                """
                INSERT INTO cortes
                    (usuario_id, monto_inicial, monto_final,
                     fecha_inicio, fecha_fin, turno, estado, observaciones)
                VALUES (%s, %s, %s, NOW(), NOW(), %s, 'CERRADO', %s)
                """,
                (usuario_id, fondo_inicial, neto, turno, observaciones)
            )
            conn.commit()
            corte_id = cursor.lastrowid

            # 2) Registrar movimientos agregados
            if ventas_efectivo > 0:
                cursor.execute(
                    """
                    INSERT INTO movimientos (corte_id, tipo, descripcion, monto)
                    VALUES (%s, 'INGRESO', 'VENTAS_EFECTIVO', %s)
                    """,
                    (corte_id, ventas_efectivo)
                )

            if ventas_tarjeta > 0:
                cursor.execute(
                    """
                    INSERT INTO movimientos (corte_id, tipo, descripcion, monto)
                    VALUES (%s, 'INGRESO', 'VENTAS_TARJETA', %s)
                    """,
                    (corte_id, ventas_tarjeta)
                )

            if gastos > 0:
                cursor.execute(
                    """
                    INSERT INTO movimientos (corte_id, tipo, descripcion, monto)
                    VALUES (%s, 'EGRESO', 'GASTOS', %s)
                    """,
                    (corte_id, gastos)
                )

            conn.commit()

            # 3) Traer info para responder al frontend
            cursor.execute(
                """
                SELECT c.id, c.usuario_id, u.nombre AS cajero,
                       c.monto_inicial, c.monto_final,
                       c.fecha_inicio, c.fecha_fin, c.turno, c.estado,
                       c.observaciones
                FROM cortes c
                JOIN usuarios u ON u.id = c.usuario_id
                WHERE c.id = %s
                """,
                (corte_id,)
            )
            corte = cursor.fetchone()

        conn.close()

        return jsonify({
            "id": corte["id"],
            "cajero": corte["cajero"],
            "fondo_inicial": corte["monto_inicial"],
            "monto_final": corte["monto_final"],
            "turno": corte["turno"],
            "estado": corte["estado"],
            "observaciones": corte["observaciones"],
        }), 201

    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Local
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    app.run(host="0.0.0.0", port=port, debug=True)


# Handler Lambda
try:
    import awsgi

    def handler(event, context):
        return awsgi.response(app, event, context)
except ImportError:
    pass
