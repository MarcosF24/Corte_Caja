import os
import pymysql
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import awsgi

load_dotenv()

app = Flask(__name__)

# ============================================================
#   CONFIG BD
# ============================================================
connection_params = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME"),
    "cursorclass": pymysql.cursors.DictCursor
}

def get_connection():
    return pymysql.connect(**connection_params)


# ============================================================
#   CONFIG SES
# ============================================================
ses = boto3.client("ses", region_name=os.getenv("REGION"))
MAIL_FROM = os.getenv("SES_EMAIL_FROM")
MAIL_TO = os.getenv("SES_EMAIL_TO", MAIL_FROM)


# ============================================================
#   ENDPOINT PRINCIPAL
#   /enviar-correo-reporte-final
# ============================================================
@app.route("/enviar-correo-reporte-final", methods=["POST"])
def enviar_correo_reporte_final():
    data = request.get_json()

    corte_final_id = data.get("corte_final_id")
    pdf_url = data.get("pdf_url")
    excel_url = data.get("excel_url")

    if not corte_final_id or not pdf_url or not excel_url:
        return jsonify({"error": "Datos incompletos"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # 1) Buscar usuario para asociar notificación (el que tenga MAIL_TO)
    usuario_id = 1
    try:
        cursor.execute(
            "SELECT id FROM usuarios WHERE email = %s LIMIT 1",
            (MAIL_TO,)
        )
        row = cursor.fetchone()
        if row:
            usuario_id = row["id"]
    except Exception:
        pass

    # 2) Destinatario fijo
    correos = [MAIL_TO]

    asunto = f"Reporte Final de Corte #{corte_final_id}"

    mensaje_html = f"""
        <h2>Reporte Final del Corte de Caja #{corte_final_id}</h2>

        <p>Tu reporte final ha sido generado correctamente.</p>

        <ul>
            <li><b>PDF:</b> <a href="{pdf_url}">{pdf_url}</a></li>
            <li><b>Excel:</b> <a href="{excel_url}">{excel_url}</a></li>
        </ul>

        <br><br>
        <p>Este correo fue enviado automáticamente por el sistema de Corte de Caja.</p>
    """

    # 3) Enviar con SES
    try:
        resp = ses.send_email(
            Source=MAIL_FROM,
            Destination={"ToAddresses": correos},
            Message={
                "Subject": {"Data": asunto, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": mensaje_html, "Charset": "UTF-8"}
                }
            }
        )
        print("SES response:", resp)
    except Exception as e:
        print("SES ERROR:", e)
        return jsonify({
            "error": f"Error enviando correo: {str(e)}"
        }), 500

    # 4) Registrar notificación
    cursor.execute("""
        INSERT INTO notificaciones (usuario_id, asunto, mensaje, enviado)
        VALUES (%s, %s, %s, %s)
    """, (
        usuario_id,
        asunto,
        f"PDF: {pdf_url} | Excel: {excel_url}",
        1
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Correo enviado correctamente",
        "destinatarios": correos
    }), 200


# ============================================================
#   HANDLER PARA AWS LAMBDA
# ============================================================
def handler(event, context):
    return awsgi.response(app, event, context)
