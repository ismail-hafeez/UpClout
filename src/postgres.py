import psycopg2
import pandas as pd

conn = psycopg2.connect(database="postgres", user="postgres", password=1040)

cur = conn.cursor()

cur.execute(
    """
    select EmployeeID, FirstName, Gender, department, position, salary
    from employee
    where salary > (
        select avg(salary)
        from employee
    )
    """
)

columns = [
    "EmployeeID", "FirstName", "Gender",
    "Department", "Position", "Salary"
]

tup = cur.fetchall()

df = pd.DataFrame(tup, columns=columns)
print(df)


#conn.commit()

cur.close()
conn.close()