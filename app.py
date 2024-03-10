import os
import re
import requests
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from pymongo import MongoClient
app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['test']
question_papers_collection = db['qp']
global_scores = {}
mock_test_responses = {}

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check username and password (implementation not included)
        # If login is successful, redirect to the upload page
        return redirect(url_for('upload_question_paper'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process registration form (implementation not included)
        # Assuming registration is successful, redirect to the upload_question_paper route
        return redirect(url_for('upload_question_paper'))
    return render_template('register.html')

@app.route('/upload_question_paper', methods=['GET', 'POST'])
def upload_question_paper():
    if request.method == 'POST':
        file = request.files['file']

        if file:
            # Upload the file to OCR.Space API and process the response
            api_key = '75517053f188957'
            payload = {'apikey': api_key, 'filetype': 'pdf'}
            files = {'file': (file.filename, file.stream, file.content_type)}
            response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
            if response.status_code == 200:
                result = response.json()
                extracted_text = result['ParsedResults'][0]['ParsedText'] if 'ParsedResults' in result else ''
                # Generate the mock test based on the extracted text
                mock_test_id, questions = generate_mock_test(extracted_text)
                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return render_template('mock_test.html', questions=questions, start_time=start_time, mock_test_id=mock_test_id)
            else:
                return "Error processing the file"

    return render_template('upload_question_paper.html')

def generate_mock_test(extracted_text):
    # Generate a unique ID for the mock test
    mock_test_id = len(mock_test_responses) + 1
    # Split the extracted text into questions based on the question mark
    questions = extracted_text.split('?')
    # Remove any empty strings resulting from the split
    questions = [question.strip() for question in questions if question.strip()]
    mock_test_responses[mock_test_id] = {'questions': questions}
    return mock_test_id, questions

@app.route('/submit_mock_test', methods=['POST'])
def submit_mock_test():
    mock_test_id = request.form.get('mock_test_id')
    start_time = datetime.strptime(request.form.get('start_time'), "%Y-%m-%d %H:%M:%S")
    end_time = datetime.now()
    time_taken = end_time - start_time

    # Calculate performance metrics (this is a placeholder)
    score = 0
    total_questions = 0

    # Retrieve the answers from the answer key (assuming it's stored in a dictionary)
    answer_key = {
        1: 'A',  # Example answer key, replace with your actual answer key
        2: 'B',
        3: 'C',
        4: 'D',
        5: 'E',
        6: 'F'
        # Add more answers as needed
    }

    # Retrieve user responses
    user_responses = {}
    questions = mock_test_responses[int(mock_test_id)]['questions']
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            user_responses[question_id] = value

    # Compare user responses with the answer key
    for question_id, user_answer in user_responses.items():
        if question_id in answer_key:
            total_questions += 1
            if user_answer.upper() == answer_key[question_id]:
                score += 1


    # Store the responses for the mock test
    print(score,total_questions)
    global global_scores
    if mock_test_id in global_scores:
        global_scores[mock_test_id]['total_tests'] += 1
        global_scores[mock_test_id]['total_questions'] += total_questions
        global_scores[mock_test_id]['total_score'] += score
    else:
        global_scores[mock_test_id] = {
            'total_tests': 1,
            'total_questions': total_questions,
            'total_score': score,
        }
    # Redirect to a page showing the results
    return redirect(url_for('show_results', mock_test_id=mock_test_id, score=score, total_questions=total_questions, time_taken=time_taken, end_time=end_time))

@app.route('/show_results/<int:mock_test_id>')
def show_results(mock_test_id):
    # Retrieve the mock test responses and display the results
    global global_scores
    total_questions = sum(score['total_questions'] for score in global_scores.values())
    total_score = sum(score['total_score'] for score in global_scores.values())
    end_time = request.args.get('end_time')
    print(global_scores)
    return render_template('results.html', mock_test=1, mock_test_id=mock_test_id, score=total_score, total_questions=total_questions, time_taken=0, end_time=end_time)

if __name__ == '__main__':
    app.run(debug=True)