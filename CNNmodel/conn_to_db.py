import psycopg2
import psycopg2.extras

hostname = 'localhost'
database = 'postgres'
username = 'postgres'
pwd = '123456'
port_id = 5432
conn = None

try:
    with psycopg2.connect(
                host = hostname,
                dbname = database,
                user = username,
                password = pwd,
                port = port_id) as conn:

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:

            cur.execute('DROP TABLE IF EXISTS users')

            create_script = ''' CREATE TABLE IF NOT EXISTS users (
                                    id      int PRIMARY KEY,
                                    username    varchar(40) NOT NULL,
                                    password  int) '''
            cur.execute(create_script)

            insert_script  = 'INSERT INTO users (id, username, password) VALUES (%s, %s, %s)'
            insert_values = [(1, 'Yarden', 123), (2, 'Bar', 123), (3, 'Moshe', 123)]
            for record in insert_values:
                cur.execute(insert_script, record)

            update_script = 'UPDATE users SET password = 765'
            cur.execute(update_script)

            #delete_script = 'DELETE FROM tess WHERE name = %s'
            #delete_record = ('James',)
            #cur.execute(delete_script, delete_record)

            cur.execute('SELECT * FROM users')
            for record in cur.fetchall():
                print(record['username'], record['password'])
except Exception as error:
    print(error)
finally:
    if conn is not None:
        conn.close()