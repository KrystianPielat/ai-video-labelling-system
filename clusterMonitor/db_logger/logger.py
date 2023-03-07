import os, requests
import psycopg2


def log(source, log, level):
    try:
        conn = psycopg2.connect(
            host=os.environ.get("PSQL_HOST"),
            database=os.environ.get("PSQL_DB"),
            user=os.environ.get("PSQL_USER"),
            password=os.environ.get("PSQL_PASSWORD"),
            port="5432",
        )

        cur = conn.cursor()

        cur.execute(
            "INSERT INTO logs(source, log, level) VALUES('%s','%s','%s')",
            (source, log, level),
        )
    except Exception as ex:
        print(ex)
    return "Invalid credentials", 401
