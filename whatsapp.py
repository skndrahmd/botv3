import os
import openai
import sqlite3
from twilio.rest import Client
from flask import Flask, request, render_template, jsonify
import json


# Set up OpenAI and Twilio clients
openai.api_key = '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'
twilio_client = Client('AC652aeef1d32f9cf28315b2558c34aa31', 'fe39d68cac19aae0b3f438ed22fa6670')


def read_txt_file(filename):
    with open(filename, 'r') as file:
        return file.read()

# Set up the SQLite connection
def create_connection():
    conn = None;
    try:
        conn = sqlite3.connect(r"C:\Users\sikan\OneDrive\Desktop\database\employees.db") # Use your path
        print(f'successful connection with sqlite version {sqlite3.version}')
    except:
        print("something is wrong!")

    return conn


# Set up Flask application
app = Flask(__name__)


# Set up route to receive WhatsApp messages
@app.route('/sms', methods=['POST'])

def sms_reply():
    # Get the message body and sender's phone number
    message_body = request.form['Body']
    sender = request.form['From']

    str_sender = str(sender[-12:])
    # print(str_sender)
    # print(type(str_sender))


    conn = create_connection()
    with conn:
        # Query database for user data based on phone number
        cur = conn.cursor()
        cur.execute(f"SELECT e.*, j.title AS job_title, j.desc AS job_description, d.name AS department_name FROM employee e JOIN jobs j ON e.job_id = j.id JOIN department d ON e.dept_id = d.id WHERE e.phone ={str_sender};")

        user_data = cur.fetchone()
        print(user_data)
        print(message_body)



    if user_data is None:
        response_text = "Sorry, I couldn't find your information in the database. Please try again."
    else:
        # Convert user data to JSON format
        user_json = {
            "id": user_data[0], 
            "salary": user_data[1], 
            "name": user_data[2],
            "email": user_data[3],
            "phone": user_data[4], 
            "job_id": user_data[5],
            "dept_id": user_data[6],
            "hire_date": user_data[7], 
            "jobe_title": user_data[8], 
            "job_description": user_data[9], 
            "department_name": user_data[10]  
        }

        policies = read_txt_file("./data/data.txt")
        instructions = read_txt_file("./data/instructions.txt")

        # Construct conversation history including user data
        conversation = [
            {"role": "system", "content": f"{instructions}.As a HR Manager, you provide guidance on company policies, benefits, and HR-related topics. You maintain confidentiality, respect privacy, and know when to escalate concerns to a human HR manager. You're here to assist a specific employee with their queries. These are the company policies: {policies}"},
            {"role": "user", "content": f"{message_body}"},
            {"role": "user", "content": json.dumps(user_json)}
        ]

        # Use OpenAI API to generate response based on message and user data
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation
        )

        # Extract the generated response from the OpenAI API
        response_text = response['choices'][0]['message']['content']
        print(response_text)

    # Send response back through Twilio
    twilio_client.messages.create(
        body=response_text,
        from_='whatsapp:+14155238886',
        to=sender
    )

    return 'OK', 200

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
