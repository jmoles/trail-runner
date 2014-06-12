import os
import psycopg2

HOST=os.environ["PSYCOPG2_DB_HOST"]
DB=os.environ["PSYCOPG2_DB_DB"]
USER=os.environ["PSYCOPG2_DB_USER"]
PASSWORD=os.environ["PSYCOPG2_DB_PASS"]

dsn = "host={0} dbname={1} user={2} password={3}".format(
    HOST, DB, USER, PASSWORD)

conn = psycopg2.connect(dsn)
curs = conn.cursor()

curs.execute("""SELECT id, networks_id, trails_id, mutate_id, generations, population, moves_limit, elite_count, p_mutate, p_crossover, weight_min, weight_max FROM run_config;""")

record_list = curs.fetchall()

curs.close()
conn.close()

for record in record_list:

    conn = psycopg2.connect(dsn)
    curs = conn.cursor()

    curs.execute("""UPDATE run
        SET run_config_id=%s
        WHERE
        networks_id=%s AND
        trails_id=%s AND
        mutate_id=%s AND
        generations=%s AND
        population=%s AND
        moves_limit=%s AND
        elite_count=%s AND
        round(p_mutate::numeric, 4)=%s AND
        round(p_crossover::numeric, 4)=%s AND
        weight_min=%s AND
        weight_max=%s""",
        (record[0],
        record[1],
        record[2],
        record[3],
        record[4],
        record[5],
        record[6],
        record[7],
        round(record[8], 4),
        round(record[9], 4),
        record[10],
        record[11]))

    conn.commit()

    curs.close()
    conn.close()

