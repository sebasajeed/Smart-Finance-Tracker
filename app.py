from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        user='finance_user',  # Replace with your DB username
        password='newpassword',  # Replace with your DB password
        host='localhost',
        database='finance_tracker'  # Replace with your DB name
    )

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM transactions ORDER BY date DESC LIMIT 10')  # Fetch only the 10 most recent transactions
    transactions = cursor.fetchall()

    # Fetch user priorities
    cursor.execute('SELECT category, priority FROM user_priorities')
    priorities = {row['category']: row['priority'] for row in cursor.fetchall()}

    # Generate insights based on priorities
    insights = []
    cursor.execute('SELECT category, SUM(amount) AS total_amount FROM transactions GROUP BY category')
    spending_data = cursor.fetchall()
    for data in spending_data:
        category = data['category']
        total_amount = data['total_amount']
        priority = priorities.get(category, 3)  # Default priority is 3 (medium)

        if priority > 3:
            insights.append(f"Your '{category}' spending is high at ${total_amount:.2f}. Consider reducing it to stay within your budget.")
        elif priority < 3:
            insights.append(f"Good job! You spent ${total_amount:.2f} on '{category}', which is below your set priority.")
        else:
            insights.append(f"Your spending on '{category}' is ${total_amount:.2f}, which is in line with your priority.")

    conn.close()
    return render_template('home.html', transactions=transactions, insights=insights)

@app.route('/all')
def all_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM transactions ORDER BY date DESC')  # Fetch all transactions
    transactions = cursor.fetchall()
    conn.close()
    return render_template('all_transactions.html', transactions=transactions)

@app.route('/add', methods=('GET', 'POST'))
def add_transaction():
    if request.method == 'POST':
        date = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO transactions (date, amount, category, description) VALUES (%s, %s, %s, %s)',
            (date, amount, category, description)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_transaction(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM transactions WHERE id = %s', (id,))
    transaction = cursor.fetchone()

    if request.method == 'POST':
        date = request.form['date']
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        cursor.execute(
            'UPDATE transactions SET date = %s, amount = %s, category = %s, description = %s WHERE id = %s',
            (date, amount, category, description, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    conn.close()
    return render_template('edit.html', transaction=transaction)

@app.route('/delete/<int:id>', methods=('POST',))
def delete_transaction(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/priorities', methods=('GET', 'POST'))
def set_priorities():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT DISTINCT category FROM transactions')
    categories = [row['category'] for row in cursor.fetchall()]

    if request.method == 'POST':
        for category in categories:
            priority = request.form.get(category)
            if priority is not None:
                cursor.execute('REPLACE INTO user_priorities (category, priority) VALUES (%s, %s)', (category, round(float(priority))))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    # Fetch existing priorities
    cursor.execute('SELECT category, priority FROM user_priorities')
    priorities = {row['category']: row['priority'] for row in cursor.fetchall()}
    conn.close()
    return render_template('priorities.html', categories=categories, priorities=priorities)

if __name__ == '__main__':
    app.run(debug=True)
