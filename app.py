from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Database configuration
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',          # XAMPP default username
            password='',          # XAMPP default password (empty)
            database='ai_chatbot' # Your database name
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Create database tables if they don't exist
def init_db():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create chat_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error initializing database: {e}")

# Initialize the database
init_db()

# Built-in knowledge base
knowledge_base = {
    "greetings": {
        "hello": "Hello there! How can I assist you today?",
        "hi": "Hi! What can I do for you?",
        "hey": "Hey! Nice to see you. How can I help?",
        "good morning": "Good morning! Ready to start the day?",
        "good afternoon": "Good afternoon! How's your day going?",
        "good evening": "Good evening! How can I assist you tonight?"
    },
    "education": {
        "study tips": "Here are some study tips:\n1. Create a study schedule\n2. Take regular breaks\n3. Use active recall techniques\n4. Teach what you've learned to someone else\n5. Stay organized",
        "best learning methods": "The most effective learning methods include:\n- Spaced repetition\n- Interleaved practice\n- Elaboration\n- Concrete examples\n- Dual coding",
        "online courses": "Some great platforms for online learning:\n1. Coursera\n2. edX\n3. Khan Academy\n4. Udemy\n5. MIT OpenCourseWare"
    },
    "coding": {
        "python": "Python is a great language to learn! Some key concepts:\n- Variables and data types\n- Control structures\n- Functions\n- Object-oriented programming\n- Modules and packages",
        "javascript": "JavaScript essentials:\n- Variables (let, const)\n- Functions and arrow functions\n- DOM manipulation\n- Async programming\n- ES6+ features",
        "web development": "For web development, you should learn:\n1. HTML for structure\n2. CSS for styling\n3. JavaScript for interactivity\n4. A frontend framework like React\n5. Backend technologies like Node.js"
    },
    "default": "I'm sorry, I don't have information about that. System is under development?"
}

def get_ai_response(prompt):
    prompt_lower = prompt.lower()
    
    # Check greetings
    for keyword, response in knowledge_base["greetings"].items():
        if keyword in prompt_lower:
            return response
    
    # Check education topics
    for keyword, response in knowledge_base["education"].items():
        if keyword in prompt_lower:
            return response
    
    # Check coding topics
    for keyword, response in knowledge_base["coding"].items():
        if keyword in prompt_lower:
            return response
    
    # Default response
    return knowledge_base["default"]

# Function to save chat history
def save_chat_history(user_id, user_message, ai_response):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_id, user_message, ai_response) VALUES (%s, %s, %s)",
                (user_id, user_message, ai_response)
            )
            connection.commit()
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error saving chat history: {e}")

# Function to get chat history for a user
def get_chat_history(user_id):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT user_message, ai_response, created_at FROM chat_history WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            history = cursor.fetchall()
            cursor.close()
            connection.close()
            return history
    except Error as e:
        print(f"Error getting chat history: {e}")
        return []

# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get chat history for the current user
    chat_history = get_chat_history(session['user_id'])
    return render_template('home.html', chat_history=chat_history)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            
            # Hash password and insert new user
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            
            connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            connection.close()
                        
# Set user session
            session['user_id'] = user_id
            return jsonify({'success': True}), 200
            
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get user by email
            cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
            # Verify password
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Login failed'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'success': False, 'message': 'Message is required'}), 400
    
    try:
        # Get AI response from built-in knowledge
        ai_response = get_ai_response(user_message)
        
        # Save chat history
        save_chat_history(session['user_id'], user_message, ai_response)
        
        return jsonify({
            'success': True,
            'ai_response': ai_response
        }), 200
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'success': False, 'message': 'Chat failed'}), 500

@app.route('/get_history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        chat_history = get_chat_history(session['user_id'])
        return jsonify({
            'success': True,
            'history': chat_history
        }), 200
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({'success': False, 'message': 'Failed to get history'}), 500

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)