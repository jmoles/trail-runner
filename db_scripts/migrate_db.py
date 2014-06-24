import os
import psycopg2
import sys

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    # Source:
    # http://stackoverflow.com/questions/3041986/python-command-line-yes-no-input
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

HOST=os.environ["PSYCOPG2_DB_HOST"]
DB=os.environ["PSYCOPG2_DB_DB"]
USER=os.environ["PSYCOPG2_DB_USER"]
PASSWORD=os.environ["PSYCOPG2_DB_PASS"]

dsn = "host={0} dbname={1} user={2} password={3}".format(
    HOST, DB, USER, PASSWORD)

conn = psycopg2.connect(dsn)
curs = conn.cursor()

# Add column for run_config_id to run table.
curs.execute("""ALTER TABLE run
    ADD COLUMN run_config_id int NOT NULL DEFAULT 0;""")

# Create the run_config table.

curs.execute("""CREATE TABLE run_config (
    id serial  NOT NULL,
    networks_id int  NOT NULL,
    trails_id int  NOT NULL,
    mutate_id int  NOT NULL,
    generations smallint  NOT NULL,
    population smallint  NOT NULL,
    moves_limit smallint  NOT NULL,
    elite_count smallint  NOT NULL,
    p_mutate real  NOT NULL,
    p_crossover real  NOT NULL,
    weight_min real  NOT NULL,
    weight_max real  NOT NULL,
    CONSTRAINT run_config_pk PRIMARY KEY (id)
);""")

conn.commit()
curs.close()

print "SUCCESS: Finished creating run_config table."

curs = conn.cursor()
# Get the distinct values from run and populate the run_config table.
curs.execute("""INSERT INTO run_config(
    networks_id, trails_id, mutate_id, generations, population,
    moves_limit, elite_count, p_mutate, p_crossover, weight_min,
    weight_max)
    (SELECT DISTINCT
        networks_id, trails_id, mutate_id, generations, population,
        moves_limit, elite_count, p_mutate, p_crossover, weight_min,
        weight_max
        FROM run);""")

conn.commit()
curs.close()

print "SUCCESS: Populated run_config table."

curs = conn.cursor()

curs.execute("""SELECT id, networks_id, trails_id, mutate_id, generations, population, moves_limit, elite_count, p_mutate, p_crossover, weight_min, weight_max FROM run_config;""")

record_list = curs.fetchall()

curs.close()

for record in record_list:

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

print "SUCCESS: Updated run table records."

# Go back and remove the default from run_config_id
curs = conn.cursor()
curs.execute("""ALTER TABLE run
    ALTER COLUMN run_config_id DROP DEFAULT;""")

conn.commit()

print "SUCCESS: Removed default from run."

# Add the foreign key references.
curs = conn.cursor()
curs.execute("""ALTER TABLE run_config
    ADD CONSTRAINT run_config_mutate
    FOREIGN KEY (mutate_id)
    REFERENCES mutate (id) NOT DEFERRABLE;""")

curs.execute("""ALTER TABLE run_config
    ADD CONSTRAINT run_config_networks
    FOREIGN KEY (networks_id)
    REFERENCES networks (id) NOT DEFERRABLE;""")

curs.execute("""ALTER TABLE run_config
    ADD CONSTRAINT run_config_trails
    FOREIGN KEY (trails_id)
    REFERENCES trails (id) NOT DEFERRABLE;""")

curs.execute("""ALTER TABLE run
    ADD CONSTRAINT run_run_config
    FOREIGN KEY (run_config_id)
    REFERENCES run_config (id) NOT DEFERRABLE;""")

conn.commit()
curs.close()

print "SUCCESS: Added foreign key constraints."

# Add all of the indexes.
curs = conn.cursor()

curs.execute("""CREATE INDEX idx_run_config_id
    ON run
    USING btree
    (run_config_id);""")

curs.execute("""CREATE INDEX idx_networks_id_rc
    ON run_config
    USING btree
    (networks_id);""")

curs.execute("""CREATE INDEX idx_trails_id_rc
    ON run_config
    USING btree
    (trails_id);""")

curs.execute("""CREATE INDEX idx_mutate_id_rc
    ON run_config
    USING btree
    (mutate_id);""")

curs.execute("""CREATE INDEX idx_generations_rc
    ON run_config
    USING btree
    (generations);""")

curs.execute("""CREATE INDEX idx_population_rc
    ON run_config
    USING btree
    (population);""")

curs.execute("""CREATE INDEX idx_moves_limit_rc
    ON run_config
    USING btree
    (moves_limit);""")

curs.execute("""CREATE INDEX idx_elite_count_rc
    ON run_config
    USING btree
    (elite_count);""")

curs.execute("""CREATE INDEX idx_p_mutate_rc
    ON run_config
    USING btree
    (p_mutate);""")

curs.execute("""CREATE INDEX idx_p_crossover_rc
    ON run_config
    USING btree
    (p_crossover);""")

curs.execute("""CREATE INDEX idx_weight_min_rc
    ON run_config
    USING btree
    (weight_min);""")

curs.execute("""CREATE INDEX idx_weight_max_rc
    ON run_config
    USING btree
    (weight_max);""")

conn.commit()
curs.close()

print "SUCCESS: Created indexes."

print "Running verification!"

curs = conn.cursor()
# Find the maximum id in run_config_id
curs.execute("SELECT MAX(id) FROM run_config;")

max_id = curs.fetchall()[0][0]

# Verify that every ID from run is in run_config.
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
        curs.close()
        conn.close()
        sys.exit(1)

curs.close()

# Verify that there are no "0" in run table in run_config_id col.
curs = conn.cursor()

curs.execute("""SELECT *
    FROM RUN
    WHERE run_config_id=0;""")

if curs.rowcount > 0:
    print "ERROR! There are rows in run that are not 0!"
    curs.close()
    conn.close()
    sys.exit()

curs.close()

print "SUCCESS: Verification passed!\n"

answer = query_yes_no("Do you wish to drop columns from table 'run'?")

if answer:

    curs = conn.cursor()

    curs.execute("""ALTER TABLE run
    DROP COLUMN trails_id CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN networks_id CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN mutate_id CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN generations CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN population CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN moves_limit CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN elite_count CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN p_mutate CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN p_crossover CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN weight_min CASCADE;""")

    curs.execute("""ALTER TABLE run
    DROP COLUMN weight_max CASCADE;""")

    conn.commit()

    print "SUCCESS: Dropped columns from run!"


conn.close()
