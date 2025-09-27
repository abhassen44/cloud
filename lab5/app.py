from flask import Flask, render_template, request, redirect, url_for
import pymysql
from db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

app = Flask(__name__)

# Function to get a database connection
def get_db_connection():
    # Use the RDS endpoint from the config file [cite: 11]
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Main route to display the form and feedback
@app.route('/')
def index():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT author, comment, created_at FROM feedback ORDER BY created_at DESC")
            feedbacks = cursor.fetchall()
    finally:
        conn.close()
    return render_template('index.html', feedbacks=feedbacks)

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    author = request.form['author']
    comment = request.form['comment']
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Insert the new comment into the RDBMS table [cite: 19]
            sql = "INSERT INTO feedback (author, comment) VALUES (%s, %s)"
            cursor.execute(sql, (author, comment))
        conn.commit()
    finally:
        conn.close()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    # You would typically run this on a server, but for the lab, running locally is fine.
    # The application itself would need to be deployed to an EC2 instance or similar service
    # for the public DNS part of the assignment[cite: 22].
    app.run(debug=True, host='0.0.0.0', port=5000)