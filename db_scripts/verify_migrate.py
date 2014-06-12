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

# Find the maximum id in run_config_id
curs.execute("SELECT MAX(id) FROM run_config;")

max_id = curs.fetchall()[0][0]

for x in range(1, max_id + 1):

    curs.execute("""SELECT DISTINCT
        networks_id, trails_id, mutate_id, generations, population,
        moves_limit, elite_count, p_mutate, p_crossover, weight_min,
        weight_max
        FROM run
        WHERE run_config_id=%s;""", (x, ))

    data = curs.fetchall()

    if len(data) != 1:
        print "ERROR! There is more than one match for ID {0}.".format(x)
        print data
        sys.exit(1)

curs.close()
conn.close()
