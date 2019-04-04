import requests
import json

# Create User
print("--- Creating User ---")
response = requests.post("http://127.0.0.1:8000/users")
user_id = response.json()['Data']['id']
print("User ID:", user_id)

# Get User
print("--- Retrieving User ---")
response = requests.get("http://127.0.0.1:8000/users/" + str(user_id))
user_object = response.json()['Data']
print("User Object:", user_object)

# Create Assessment
print("--- Creating Assessment ---")
response = requests.post("http://127.0.0.1:8000/users/{}/assessments".format(user_id))
assessment_id = response.json()['Data']
print("Assessment ID:", assessment_id)

# Get Assessment
print("--- Retrieving Assessment ---")
response = requests.get("http://127.0.0.1:8000/assessments/{}".format(assessment_id))
assessment_object = response.json()['Data']
num_questions = int(assessment_object['question_count'])
print("Assessment Object (Not Started):", assessment_object)

# Start Assessment
print("--- Starting Assessment ---")
response = requests.post("http://127.0.0.1:8000/assessments/{}/start".format(assessment_id))
assessment_started = response.json()['Data']
print("Assessment Started:", assessment_started)

# Get Started Assessment
print("--- Retrieving Started Assessment ---")
response = requests.get("http://127.0.0.1:8000/assessments/{}".format(assessment_id))
assessment_object = response.json()['Data']
print("Assessment Object (Started):", assessment_object)

# Get Healthcheck
print("--- Running Healthcheck for Assessment ---")
response = requests.get(
    "http://127.0.0.1:8000/assessments/healthz",
    headers={'Referer': "http://127.0.0.1:8000/test/data-scientist-{}/assessment/{}".format(user_id, assessment_id)}
)
healthcheck_status = response.json()['Data']
print("Healthcheck Status:", healthcheck_status)

# Get Started Assessment
print("--- Retrieving Started Assessment ---")
response = requests.get("http://127.0.0.1:8000/assessments/{}".format(assessment_id))
assessment_object = response.json()['Data']
print("Assessment Object (Started):", assessment_object)

# Get all questions
for i in range(num_questions - 1):
    user_question_index = i + 1
    print("--- Get Question #{} ---".format(user_question_index))
    response = requests.get("http://127.0.0.1:8000/assessments/{}/questions/{}".format(assessment_id, user_question_index))
    question_object = response.json()['Data']
    print("Question #{} Object: {}".format(user_question_index, question_object))

    answer_id = question_object['Options'][1]['id']
    print("--- Answer Question #{} ---".format(user_question_index))
    response = requests.post(
        "http://127.0.0.1:8000/assessments/{}/questions/{}/answers".format(assessment_id, user_question_index),
        data=json.dumps({"OptionId": answer_id}),
        headers={"Content-Type": "application/json"}
    )
    answer_status = response.json()['Data']
    print("Answer Status:", answer_status)

# Get Healthcheck
print("--- Running Healthcheck for Assessment ---")
response = requests.get(
    "http://127.0.0.1:8000/assessments/healthz",
    headers={'Referer': "http://127.0.0.1:8000/test/data-scientist-{}/assessment/{}".format(user_id, assessment_id)}
)
healthcheck_status = response.json()['Data']
print("Healthcheck Status:", healthcheck_status)

# Get Started Assessment
print("--- Retrieving Started Assessment ---")
response = requests.get("http://127.0.0.1:8000/assessments/{}".format(assessment_id))
assessment_object = response.json()['Data']
print("Assessment Object (Started):", assessment_object)

# End Assessment
print("--- Ending Assessment ---")
response = requests.post("http://127.0.0.1:8000/assessments/{}/end".format(assessment_id))
assessment_ended = response.json()['Data']
print("Assessment Ended:", assessment_ended)

# Get Started Assessment
print("--- Retrieving Ended Assessment ---")
response = requests.get("http://127.0.0.1:8000/assessments/{}".format(assessment_id))
assessment_object = response.json()['Data']
print("Assessment Object (Ended):", assessment_object)