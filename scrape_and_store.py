import subprocess
import json
import os
import psycopg2
from datetime import datetime
import uuid

# Define labels (hashtags)
LABELS = [
    "#bitcoin", "#bitcoincharts", "#bitcoiner", "#bitcoinexchange",
    "#bitcoinmining", "#bitcoinnews", "#bitcoinprice", "#bitcointechnology",
    "#bitcointrading", "#bittensor", "#btc", "#cryptocurrency", "#crypto",
    "#defi", "#decentralizedfinance", "#tao"
]

# PostgreSQL connection settings
DB = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",  # change this
    "host": "localhost",
    "port": 5432
}

DATA_SOURCE_ID = 2  # assuming X (Twitter) = 2 in data_sources

def connect_db():
    return psycopg2.connect(**DB)

def ensure_data_source(cur):
    cur.execute("""
        INSERT INTO data_sources (id, name, weight)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (DATA_SOURCE_ID, 'Twitter', 1.0))  # Weight is arbitrary, you can change

def ensure_label_exists(cur, label):
    cur.execute("""
        INSERT INTO data_labels(value)
        VALUES (%s)
        ON CONFLICT DO NOTHING
    """, (label,))

def insert_entity(cur, uri, created_at, label, content_bytes):
    try:
        cur.execute("""
            INSERT INTO data_entities (uri, datetime, source_id, label_value, content, content_size_bytes)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (uri, created_at, DATA_SOURCE_ID, label, content_bytes, len(content_bytes)))
    except Exception as e:
        print(f"[ERROR] Failed to insert entity: {e}")

def run_twscrape(label):
    safe_label = label.replace("#", "")
    json_path = f"{safe_label}.json"
    cmd = ["twscrape", "search", label, "--limit=20"]
    with open(json_path, "w") as f:
        subprocess.run(cmd, stdout=f)
    return json_path

def process_file(json_path):
    tweets = []
    with open(json_path, "r") as f:
        for line in f:
            if line.strip():  # skip empty lines
                try:
                    tweets.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[WARN] Skipping line due to JSON error: {e}")
    return tweets


def main():
    conn = connect_db()
    cur = conn.cursor()

    # Ensure source exists once
    ensure_data_source(cur)

    for label in LABELS:
        print(f"[INFO] Scraping {label}")
        json_path = run_twscrape(label)

        try:
            tweets = process_file(json_path)
        except Exception as e:
            print(f"[ERROR] Failed to load {json_path}: {e}")
            continue

        ensure_label_exists(cur, label)

        for tweet in tweets:
            try:
                if not all(k in tweet for k in ("url", "date", "rawContent")):
                    print("[WARN] Missing fields in tweet, skipping.")
                    continue

                uri = tweet["url"]
                created_at = datetime.fromisoformat(tweet["date"].replace("Z", "+00:00"))
                content = tweet["rawContent"]
                content_bytes = content.encode("utf-8")

                insert_entity(cur, uri, created_at, label, content_bytes)

            except Exception as e:
                print(f"[WARN] Skipping tweet due to error: {e}")

        os.remove(json_path)

    conn.commit()
    cur.close()
    conn.close()
    print("[DONE] All data stored.")

if __name__ == "__main__":
    main()
