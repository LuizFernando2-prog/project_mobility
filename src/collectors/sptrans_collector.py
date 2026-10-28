"""
Real-time data collector for SPTrans (Olho Vivo) + Google Places enrichment.
"""

import time
import logging
from datetime import datetime

import pyodbc
import requests
from flask import Flask, jsonify

from src.config import (
    SPTRANS_TOKEN,
    GOOGLE_API_KEY,
    get_connection_string,
    SP_LAT_MIN, SP_LAT_MAX,
    SP_LON_MIN, SP_LON_MAX,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_db_connection():
    return pyodbc.connect(get_connection_string())


def is_inside_sao_paulo(lat: float, lon: float) -> bool:
    return SP_LAT_MIN <= lat <= SP_LAT_MAX and SP_LON_MIN <= lon <= SP_LON_MAX


def collect_sptrans_and_google():
    """Collect bus positions and enrich with Google Places data."""
    if not SPTRANS_TOKEN:
        logger.error("SPTRANS_TOKEN not set. Check your .env file.")
        return

    logger.info("Starting real-time collection (SPTrans + Google)")

    try:
        session = requests.Session()
        auth = session.post(
            f"http://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar?token={SPTRANS_TOKEN}"
        )
        if auth.text != "true":
            logger.error("SPTrans authentication failed")
            return

        response = session.get("http://api.olhovivo.sptrans.com.br/v2.1/Posicao")
        data = response.json()

        if "l" not in data:
            logger.warning("SPTrans returned no vehicle data")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        processed = 0

        for line in data["l"]:
            line_code = line.get("cl")
            for vehicle in line.get("vs", []):
                prefix = vehicle.get("p")
                lat = vehicle.get("py")
                lon = vehicle.get("px")
                timestamp = vehicle.get("ta")

                if not is_inside_sao_paulo(lat, lon):
                    continue

                # 1. Store SPTrans position
                cursor.execute(
                    """
                    INSERT INTO Coleta_SPTrans
                        (prefixo, latitude, longitude, linha_codigo, data_hora_sptrans)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (prefix, lat, lon, line_code, timestamp),
                )

                # 2. Enrich with Google Places (if key is available)
                if GOOGLE_API_KEY:
                    _enrich_with_google(cursor, lat, lon)

                processed += 1
                time.sleep(0.25)  # gentle rate limiting

        conn.commit()
        conn.close()
        logger.info(f"Collection finished → {processed} vehicles processed")

    except Exception as exc:
        logger.error(f"Collection error: {exc}")


def _enrich_with_google(cursor, lat: float, lon: float):
    """Reverse geocode + fetch place popularity."""
    try:
        geo_url = (
            f"https://maps.googleapis.com/maps/api/geocode/json"
            f"?latlng={lat},{lon}&key={GOOGLE_API_KEY}"
        )
        geo = requests.get(geo_url, timeout=10).json()

        if geo.get("status") != "OK":
            return

        result = geo["results"][0]
        place_id = result["place_id"]
        address = result["formatted_address"]

        cursor.execute("SELECT place_id FROM Coleta_Google WHERE place_id = ?", (place_id,))
        if cursor.fetchone():
            return  # already known

        cursor.execute(
            """
            INSERT INTO Coleta_Google (latitude, longitude, endereco_completo, place_id)
            VALUES (?, ?, ?, ?)
            """,
            (lat, lon, address, place_id),
        )

        details_url = (
            f"https://maps.googleapis.com/maps/api/place/details/json"
            f"?place_id={place_id}&fields=rating,user_ratings_total,price_level"
            f"&key={GOOGLE_API_KEY}"
        )
        details = requests.get(details_url, timeout=10).json()

        if details.get("status") == "OK":
            d = details.get("result", {})
            cursor.execute(
                """
                INSERT INTO Coleta_Google_Popularidade
                    (place_id, nota_media, total_avaliacoes, faixa_preco)
                VALUES (?, ?, ?, ?)
                """,
                (
                    place_id,
                    d.get("rating"),
                    d.get("user_ratings_total", 0),
                    d.get("price_level", 0),
                ),
            )
    except Exception:
        pass  # non-critical enrichment


def collection_loop(interval_seconds: int = 60):
    while True:
        collect_sptrans_and_google()
        logger.info(f"Waiting {interval_seconds}s for next round...")
        time.sleep(interval_seconds)


@app.route("/")
def status():
    return jsonify({
        "status": "running",
        "focus": "São Paulo",
        "time": datetime.now().strftime("%H:%M:%S"),
    })


if __name__ == "__main__":
    import threading
    threading.Thread(target=collection_loop, daemon=True).start()
    app.run(debug=False, use_reloader=False, port=5000)
