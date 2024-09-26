from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_mysqldb import MySQL
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_generated_secret_key_here'

# Configure MySQL
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'M@lshan2002'
app.config['MYSQL_DB'] = 'chat_app'
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app)

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
        session['username'] = username
        return redirect(url_for('chat'))
    return 'Invalid login'


@app.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw.decode('utf-8')))
    conn.commit()
    
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))

    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username != %s", (session['username'],))
    users = cursor.fetchall()

    return render_template('chat.html', users=[user[0] for user in users], recipient=None)


@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    recipient = request.form['recipient']
    sender = session['username']
    
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender, recipient, message) VALUES (%s, %s, %s)", (sender, recipient, message))
    conn.commit()
    
    return jsonify({'status': 'Message sent'})

@app.route('/chat_history')
def chat_history():
    sender = session['username']
    recipient = request.args.get('recipient')

    conn = mysql.connection
    cursor = conn.cursor()

    if recipient:
        cursor.execute("SELECT sender, recipient, message FROM messages WHERE (sender = %s AND recipient = %s) OR (sender = %s AND recipient = %s)",
                       (sender, recipient, recipient, sender))
    else:
        cursor.execute("SELECT sender, recipient, message FROM messages WHERE sender = %s OR recipient = %s", (sender, sender))

    messages = cursor.fetchall()

    return jsonify([{'sender': row[0], 'message': row[2]} for row in messages])


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)