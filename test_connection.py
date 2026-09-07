import psycopg2
from os import getenv
from dotenv import load_dotenv


def main():
    load_dotenv()
    try:
        conn = psycopg2.connect(getenv('POSTGRES_URI'))
        # Creating a cursor object using the cursor() method
        cursor = conn.cursor()

        # Executing an MYSQL function using the execute() method
        cursor.execute("select version()")

        # Fetch a single row using fetchone() method.
        data = cursor.fetchone()
        print("Connection established to: ", data)

        # Closing the connection
        cursor.close()
        conn.close()

    except Exception as error:
        print(f"Error connecting to PostgreSQL: {error}")


if __name__ == '__main__':
    main()
