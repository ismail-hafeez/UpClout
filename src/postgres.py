import psycopg2
import pandas as pd

conn = psycopg2.connect(database="postgres", user="postgres", password=1040)
cur = conn.cursor()

def insert_influencer_data(first_name: str, last_name: str, gender: str, department: str, position: str, salary: float) -> str:

    insert_query = """
        INSERT INTO employee (firstname, lastname, gender, department, Position, Salary)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    cur.execute(insert_query, (first_name, last_name, gender, department, position, salary))

    conn.commit()

    cur.close()
    conn.close()

    return "Data inserted successfully!"


