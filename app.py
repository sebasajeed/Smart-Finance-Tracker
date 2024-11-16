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
    
    # Generate insights for the homepage
    cursor.execute('SELECT DISTINCT category FROM transactions')
    categories = [row['category'] for row in cursor.fetchall()]

    cursor.execute('SELECT category, SUM(amount) AS total_amount FROM transactions GROUP BY category')
    spending_data = cursor.fetchall()

    # Fetch user-defined priorities from DB
    user_priorities = {}
    cursor.execute('SELECT category, priority FROM user_priorities')
    for row in cursor.fetchall():
        user_priorities[row['category']] = row['priority']

    insights = generate_insights(spending_data, user_priorities)
    
    conn.close()
    return render_template('home.html', transactions=transactions, insights=insights)

def generate_insights(spending_data, user_priorities):
    insights = []

    for data in spending_data:
        category = data['category']
        total_amount = data['total_amount']
        priority = user_priorities.get(category, 3)  # Default priority is 3 (medium)

        # Example budget settings
        if priority > 3:
            budget = 100  # High priority budget (example)
        elif priority < 3:
            budget = 50  # Low priority budget (example)
        else:
            budget = 75  # Medium priority budget (example)

        if total_amount > budget:
            insights.append({
                'message': f'Your "{category}" spending went ${total_amount - budget:.2f} over budget as per your priorities. Keep an eye on it!',
                'type': 'over-budget'
            })
        elif total_amount < budget:
            insights.append({
                'message': f'You spent ${budget - total_amount:.2f} less on "{category}" based on your priorities. Great savings!',
                'type': 'under-budget'
            })
        else:
            insights.append({
                'message': f'Your "{category}" spending is on track as per your priorities. Keep it steady!',
                'type': 'on-budget'
            })

    return insights

@app.route('/priorities', methods=('GET', 'POST'))
def priorities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM transactions')
    categories = [row[0] for row in cursor.fetchall()]

    # Fetch existing user priorities
    cursor.execute('SELECT category, priority FROM user_priorities')
    existing_priorities = {row[0]: row[1] for row in cursor.fetchall()}

    if request.method == 'POST':
        for category in categories:
            priority = int(request.form.get(category, 3))  # Get form input
            if category in existing_priorities:
                cursor.execute(
                    'UPDATE user_priorities SET priority = %s WHERE category = %s',
                    (priority, category)
                )
            else:
                cursor.execute(
                    'INSERT INTO user_priorities (category, priority) VALUES (%s, %s)',
                    (category, priority)
                )
        conn.commit()
        return redirect(url_for('home'))

    conn.close()
    return render_template('priorities.html', categories=categories, existing_priorities=existing_priorities)

if __name__ == '__main__':
    app.run(debug=True)
