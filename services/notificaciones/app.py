import os
from datetime import datetime

from flask import Flask, request, jsonify
import pymysql
from pymysql.cursors import DictCursor

# Cargar .env en entorno local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import boto3


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "corte_caja"),
    "cursorclass": DictCursor,
}

SES_REGION = os.getenv("SES_REGION", "us-east-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")

app = Flask(__name__)
ses = boto3.client("ses", region_name=SES_REGION)


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def enviar_correo_reporte(to_email, asunto, cuerpo_texto, cuerpo_html):
    if not SES_FROM_EMAIL:
        raise RuntimeError("SES_FROM_EMAIL no está configurado")

    ses.send_email(
        Source=SES_FROM_EMAIL,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": asunto, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": cuerpo_texto, "Charset": "UTF-8"},
                "Html": {"Data": cuerpo_html, "Charset": "UTF-8"},
            },
        },
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "notificaciones"}), 200


@app.route("/notificaciones/enviar-reporte-final", methods=["POST"])
def enviar_reporte_final():
    data = request.get_json(force=True)
    reporte_id = data.get("reporte_id")
    corte_final_id = data.get("corte_final_id")
    fecha_str = data.get("fecha")  # "YYYY-MM-DD"
    pdf_url = data.get("archivo_pdf_url")
    excel_url = data.get("archivo_excel_url")

    if not (reporte_id and corte_final_id and fecha_str and pdf_url and excel_url):
        return jsonify({
            "error": "reporte_id, corte_final_id, fecha, archivo_pdf_url y archivo_excel_url son requeridos"
        }), 400

    conn = get_connection()
    try:
        # Obtener gerentes
        sql_gerentes = """
            SELECT id, email, nombre
            FROM usuarios
            WHERE rol = 'GERENTE'
        """
        with conn.cursor() as cursor:
            cursor.execute(sql_gerentes)
            gerentes = cursor.fetchall()

        if not gerentes:
            return jsonify({"warning": "No hay usuarios con rol GERENTE para notificar"}), 200

        asunto = f"Reporte final de corte de caja - {fecha_str}"
        cuerpo_texto_base = f"""
Se ha generado el reporte final de corte de caja correspondiente a la fecha {fecha_str}.

Puedes consultar los archivos en las siguientes rutas:

PDF: {pdf_url}
Excel: {excel_url}

ID del corte final: {corte_final_id}
ID del reporte: {reporte_id}
"""
        cuerpo_html_base = f"""
<p>Se ha generado el <strong>reporte final de corte de caja</strong> correspondiente a la fecha {fecha_str}.</p>
<p>Puedes consultar los archivos en las siguientes rutas:</p>
<ul>
  <li>PDF: <a href="{pdf_url}">{pdf_url}</a></li>
  <li>Excel: <a href="{excel_url}">{excel_url}</a></li>
</ul>
<p>
  ID del corte final: <strong>{corte_final_id}</strong><br/>
  ID del reporte: <strong>{reporte_id}</strong>
</p>
"""

        sql_insert_notif = """
            INSERT INTO notificaciones (usuario_id, asunto, mensaje, enviado, fecha_envio)
            VALUES (%s, %s, %s, %s, %s)
        """
        sql_update_notif = """
            UPDATE notificaciones
            SET enviado = %s, fecha_envio = %s
            WHERE id = %s
        """

        with conn.cursor() as cursor:
            for g in gerentes:
                usuario_id = g["id"]
                email = g["email"]
                nombre = g["nombre"]

                cuerpo_texto = f"Hola {nombre},\n\n" + cuerpo_texto_base
                cuerpo_html = f"<p>Hola {nombre},</p>" + cuerpo_html_base

                # Crear notificación como no enviada
                cursor.execute(
                    sql_insert_notif,
                    (usuario_id, asunto, cuerpo_texto_base, 0, None),
                )
                notif_id = cursor.lastrowid

                try:
                    enviar_correo_reporte(email, asunto, cuerpo_texto, cuerpo_html)
                    # Marcar como enviada
                    cursor.execute(
                        sql_update_notif,
                        (1, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), notif_id),
                    )
                except Exception as e:
                    print(f"Error enviando correo a {email}: {e}")

            conn.commit()

        return jsonify({"message": "Notificaciones procesadas"}), 200

    finally:
        conn.close()


@app.route("/notificaciones", methods=["GET"])
def listar_notificaciones():
    usuario_id = request.args.get("usuario_id", type=int)
    if not usuario_id:
        return jsonify({"error": "usuario_id es requerido"}), 400

    sql = """
        SELECT id, usuario_id, asunto, mensaje, enviado, fecha_envio
        FROM notificaciones
        WHERE usuario_id = %s
        ORDER BY COALESCE(fecha_envio, NOW()) DESC, id DESC
    """

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (usuario_id,))
            rows = cursor.fetchall()
    finally:
        conn.close()

    for r in rows:
        if isinstance(r.get("fecha_envio"), datetime):
            r["fecha_envio"] = r["fecha_envio"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(rows), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8005"))
    app.run(host="0.0.0.0", port=port, debug=True)

try:
    import awsgi

    def handler(event, context):
        return awsgi.response(app, event, context)
except ImportError:
    pass
