import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="wifi_calibration",
        user="postgres",
        password="okokok"
    )
    print("✅ Connected to PostgreSQL successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")