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


# ==========================================
# Healthcheck
# ==========================================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "cortes"}), 200


# ==========================================
# ENDPOINT BÁSICO: LISTAR CORTES (CRUD SIMPLE)
# ==========================================
@app.route("/cortes", methods=["GET"])
def listar_cortes():
    """
    Lista cortes de manera simple. No es el que usa el dashboard principal,
    pero lo dejamos disponible.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id,
                       c.usuario_id,
                       u.nombre AS cajero,
                       c.monto_inicial,
                       c.monto_final,
                       c.fecha_inicio,
                       c.fecha_fin,
                       c.turno,
                       c.estado,
                       c.observaciones
                FROM cortes c
                JOIN usuarios u ON u.id = c.usuario_id
                ORDER BY c.fecha_inicio DESC
                """
            )
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cortes", methods=["POST"])
def abrir_corte():
    """
    Abre un corte sencillo. (Puedes usarlo desde otros flujos si quieres.)
    Body esperado:
    {
      "usuario_id": 2,
      "monto_inicial": 1000
    }
    """
    data = request.get_json() or {}
    usuario_id = data.get("usuario_id")
    monto_inicial = float(data.get("monto_inicial") or 0)

    if not usuario_id:
        return jsonify({"error": "usuario_id es obligatorio"}), 400

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

            cursor.execute(
                """
                SELECT id, usuario_id, monto_inicial, monto_final,
                       fecha_inicio, fecha_fin, estado
                FROM cortes
                WHERE id = %s
                """,
                (corte_id,)
            )
            corte = cursor.fetchone()
        conn.close()
        return jsonify(corte), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cortes/<int:corte_id>/cerrar", methods=["POST"])
def cerrar_corte(corte_id):
    """
    Cierra un corte ABIERTO.
    Body esperado:
    {
      "monto_final": 2500.50
    }
    """
    data = request.get_json() or {}
    monto_final = data.get("monto_final")

    if monto_final is None:
        return jsonify({"error": "monto_final es obligatorio"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE cortes
                SET monto_final = %s,
                    fecha_fin = NOW(),
                    estado = 'CERRADO'
                WHERE id = %s
                """,
                (monto_final, corte_id)
            )
            conn.commit()
        conn.close()
        return jsonify({"message": "Corte cerrado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# MOVIMIENTOS (INGRESOS / EGRESOS)
# ==========================================
@app.route("/movimientos", methods=["POST"])
def registrar_movimiento():
    """
    Registra un movimiento en un corte.
    Body:
    {
      "corte_id": 1,
      "tipo": "INGRESO" | "EGRESO",
      "descripcion": "VENTAS_EFECTIVO" | "VENTAS_TARJETA" | "GASTOS" | ...
      "monto": 150.50
    }
    """
    data = request.get_json() or {}
    corte_id = data.get("corte_id")
    tipo = data.get("tipo")
    descripcion = data.get("descripcion")
    monto = data.get("monto")

    if not corte_id or not tipo or monto is None:
        return jsonify({"error": "corte_id, tipo y monto son obligatorios"}), 400

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO movimientos (corte_id, tipo, descripcion, monto, fecha)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (corte_id, tipo, descripcion, monto)
            )
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
            cursor.execute(
                """
                SELECT id, tipo, descripcion, monto, fecha
                FROM movimientos
                WHERE corte_id = %s
                ORDER BY fecha DESC
                """,
                (corte_id,)
            )
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# ENDPOINT ESPECIAL PARA corte.html: /guardar-corte
# ==========================================
@app.route("/guardar-corte", methods=["POST"])
def guardar_corte_completo():
    """
    Endpoint pensado para el formulario de corte.html.

    Body esperado:
    {
      "usuario_id": 2,
      "fecha": "2025-11-29",  // opcional
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

    neto = fondo_inicial + ventas_efectivo + ventas_tarjeta - gastos

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1) Crear el corte como CERRADO
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
                    INSERT INTO movimientos (corte_id, tipo, descripcion, monto, fecha)
                    VALUES (%s, 'INGRESO', 'VENTAS_EFECTIVO', %s, NOW())
                    """,
                    (corte_id, ventas_efectivo)
                )

            if ventas_tarjeta > 0:
                cursor.execute(
                    """
                    INSERT INTO movimientos (corte_id, tipo, descripcion, monto, fecha)
                    VALUES (%s, 'INGRESO', 'VENTAS_TARJETA', %s, NOW())
                    """,
                    (corte_id, ventas_tarjeta)
                )

            if gastos > 0:
                cursor.execute(
                    """
                    INSERT INTO movimientos (corte_id, tipo, descripcion, monto, fecha)
                    VALUES (%s, 'EGRESO', 'GASTOS', %s, NOW())
                    """,
                    (corte_id, gastos)
                )

            conn.commit()

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


# ==========================================
# ENDPOINT PARA DASHBOARD: /obtener-cortes
# ==========================================
@app.route("/obtener-cortes", methods=["GET"])
def obtener_cortes_dashboard():
    """
    Devuelve la estructura que espera dashboard.js:
    {
      "summary": {
        "total_ventas": ...,
        "total_gastos": ...,
        "neto_total": ...
      },
      "history": [
        {
          "id": ...,
          "fecha": "YYYY-MM-DD",
          "hora": "HH:MM",
          "cajero": "...",
          "fondo_inicial": ...,
          "ventas": ...,
          "gastos": ...,
          "monto_final": ...
        }
      ]
    }
    Soporta filtros opcionales:
      ?fecha=YYYY-MM-DD
      ?cajero=texto
    """
    fecha = request.args.get("fecha")
    cajero_filtro = request.args.get("cajero")

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1) Traer cortes
            query = """
                SELECT c.id,
                       c.usuario_id,
                       u.nombre AS cajero,
                       c.monto_inicial,
                       c.monto_final,
                       c.fecha_inicio,
                       c.fecha_fin,
                       c.turno,
                       c.estado,
                       c.observaciones
                FROM cortes c
                JOIN usuarios u ON u.id = c.usuario_id
                WHERE 1=1
            """
            params = []

            if fecha:
                query += " AND DATE(c.fecha_inicio) = %s"
                params.append(fecha)

            if cajero_filtro:
                query += " AND u.nombre LIKE %s"
                params.append(f"%{cajero_filtro}%")

            query += " ORDER BY c.fecha_inicio DESC"

            cursor.execute(query, params)
            cortes = cursor.fetchall()

            if not cortes:
                conn.close()
                return jsonify({
                    "summary": {
                        "total_ventas": 0,
                        "total_gastos": 0,
                        "neto_total": 0
                    },
                    "history": []
                }), 200

            corte_ids = [c["id"] for c in cortes]

            # 2) Traer agregados de movimientos
            format_strings = ",".join(["%s"] * len(corte_ids))
            cursor.execute(
                f"""
                SELECT corte_id,
                       SUM(CASE WHEN tipo = 'INGRESO' THEN monto ELSE 0 END) AS total_ingresos,
                       SUM(CASE WHEN tipo = 'EGRESO' THEN monto ELSE 0 END) AS total_egresos
                FROM movimientos
                WHERE corte_id IN ({format_strings})
                GROUP BY corte_id
                """,
                corte_ids
            )
            mov_rows = cursor.fetchall()

        conn.close()

        agregados = {row["corte_id"]: row for row in mov_rows}

        history = []
        total_ventas = 0
        total_gastos = 0

        for c in cortes:
            agg = agregados.get(c["id"], {})
            ventas = float(agg.get("total_ingresos") or 0)
            gastos = float(agg.get("total_egresos") or 0)

            total_ventas += ventas
            total_gastos += gastos

            fecha_dt = c["fecha_inicio"]
            if fecha_dt:
                fecha_str = fecha_dt.strftime("%Y-%m-%d")
                hora_str = fecha_dt.strftime("%H:%M")
            else:
                fecha_str = ""
                hora_str = ""

            history.append({
                "id": c["id"],
                "fecha": fecha_str,
                "hora": hora_str,
                "cajero": c["cajero"],
                "fondo_inicial": float(c["monto_inicial"] or 0),
                "ventas": ventas,
                "gastos": gastos,
                "monto_final": float(c["monto_final"] or 0)
            })

        neto_total = total_ventas - total_gastos

        return jsonify({
            "summary": {
                "total_ventas": total_ventas,
                "total_gastos": total_gastos,
                "neto_total": neto_total
            },
            "history": history
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# DETALLE DE CORTE PARA EL MODAL: /corte/<id>
# ==========================================
@app.route("/corte/<int:corte_id>", methods=["GET"])
def detalle_corte(corte_id):
    """
    Devuelve el detalle de un corte en la forma que espera abrirModal() en dashboard.js:
    {
      "cajero": "...",
      "fecha": "YYYY-MM-DD",
      "hora": "HH:MM",
      "fondo_inicial": ...,
      "ventas_efectivo": ...,
      "ventas_tarjeta": ...,
      "total_ventas": ...,
      "gastos": ...,
      "neto_calculado": ...,
      "observaciones": "..."
    }
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id,
                       c.usuario_id,
                       u.nombre AS cajero,
                       c.monto_inicial,
                       c.monto_final,
                       c.fecha_inicio,
                       c.fecha_fin,
                       c.turno,
                       c.estado,
                       c.observaciones
                FROM cortes c
                JOIN usuarios u ON u.id = c.usuario_id
                WHERE c.id = %s
                """,
                (corte_id,)
            )
            corte = cursor.fetchone()

            if not corte:
                conn.close()
                return jsonify({"error": "Corte no encontrado"}), 404

            cursor.execute(
                """
                SELECT tipo, descripcion, monto
                FROM movimientos
                WHERE corte_id = %s
                """,
                (corte_id,)
            )
            movimientos = cursor.fetchall()

        conn.close()

        ventas_efectivo = 0
        ventas_tarjeta = 0
        gastos = 0

        for m in movimientos:
            tipo = m["tipo"]
            desc = (m["descripcion"] or "").upper()
            monto = float(m["monto"] or 0)

            if tipo == "INGRESO":
                if desc == "VENTAS_EFECTIVO":
                    ventas_efectivo += monto
                elif desc == "VENTAS_TARJETA":
                    ventas_tarjeta += monto
                else:
                    ventas_efectivo += monto
            elif tipo == "EGRESO":
                gastos += monto

        total_ventas = ventas_efectivo + ventas_tarjeta
        fondo_inicial = float(corte["monto_inicial"] or 0)
        neto_calculado = fondo_inicial + total_ventas - gastos

        fecha_dt = corte["fecha_inicio"]
        if fecha_dt:
            fecha_str = fecha_dt.strftime("%Y-%m-%d")
            hora_str = fecha_dt.strftime("%H:%M")
        else:
            fecha_str = ""
            hora_str = ""

        return jsonify({
            "cajero": corte["cajero"],
            "fecha": fecha_str,
            "hora": hora_str,
            "fondo_inicial": fondo_inicial,
            "ventas_efectivo": ventas_efectivo,
            "ventas_tarjeta": ventas_tarjeta,
            "total_ventas": total_ventas,
            "gastos": gastos,
            "neto_calculado": neto_calculado,
            "observaciones": corte["observaciones"] or "Ninguna"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# ELIMINAR CORTE: DELETE /corte/<id>
# ==========================================
@app.route("/corte/<int:corte_id>", methods=["DELETE"])
def eliminar_corte(corte_id):
    """
    Elimina un corte y sus movimientos asociados.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Borrar movimientos primero
            cursor.execute("DELETE FROM movimientos WHERE corte_id = %s", (corte_id,))
            # Borrar corte
            cursor.execute("DELETE FROM cortes WHERE id = %s", (corte_id,))
            conn.commit()
        conn.close()
        return jsonify({"message": "Corte eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# LOCAL & LAMBDA HANDLER
# ==========================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    app.run(host="0.0.0.0", port=port, debug=True)


try:
    import awsgi

    def handler(event, context):
        return awsgi.response(app, event, context)
except ImportError:
    pass
