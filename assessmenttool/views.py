import random
import json
import urllib.parse as urlparse
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404

from .models import User, Assessment, Question, QuestionAnswer, AssessmentQuestion, AssessmentAttempt


def construct_json_response(data, status=1, message="Success"):
    """
    Default response body structure is JSON object with 3 elements.
    :param data: object to be returned in JSON response used for "Data" element
    :param status: numerical status of request (1 = success) used for "Status" element
    :param message: request status message used for "Message" element
    :return: dictionary containing 3 elements, used as the default JSON response body
    """
    return {"Status": status, "Message": message, "Data": data}


def prepopulate_questions():
    """
    On application startup, creates 100 questions, with 5 associated answers each.
    One answer is randomly assigned as the correct answer.
    :return: None
    """
    for question_id in range(100):
        question, created = Question.objects.get_or_create(id=question_id)

        if created:
            question.question_text = "question " + str(question_id)
            correct_answer = random.randint(0, 4)
            for answer_num in range(1, 6):
                is_correct_answer = correct_answer == answer_num
                answer = QuestionAnswer.objects.create(
                    question=question, answer_text="Answer #{} for Question #{}".format(answer_num, question_id),
                    is_correct_answer=is_correct_answer
                )
                question.answers.add(answer)

            question.save()


def get_health(request):
    """
    View method for assessment healthcheck. Used to track remaining time for assessment session.
    Extract assessment ID from 'Referer' header and updates remaining time based on time elapsed from previous
    healthcheck.
    :param request: Django HttpRequest object
    :return: If successful request, return 200-OK and JSON body where 'Data' element is set as 'OK'
    If Referer header is not found or unable to be parsed, return 400-BadRequest
    If assessment is not found, return 404-NotFound
    """
    referer = request.META.get('HTTP_REFERER', None)
    if not referer:
        return HttpResponseBadRequest('Referer header not found')

    try:
        path = urlparse.urlparse(referer).path.split('/')
        assessment_id = path[4]
    except Exception:
        return HttpResponseBadRequest("Unable to parse Referer header")

    assessment = get_object_or_404(Assessment, assessment_uuid=assessment_id)
    current_attempt = assessment.current_attempt()
    if current_attempt:
        current_attempt.update_time_remaining()

    return JsonResponse(construct_json_response("OK"))


@csrf_exempt
def create_user(request):
    """
    View method to create new user
    :param request: Django HttpRequest object
    :return: 201-Created and JSON body where 'Data' element is User object
    """
    user = User.objects.create(title='Data Scientist')

    # TODO: Move to a post-create hook in User model
    user.slug = user.title.lower().replace(' ', '-') + '-' + str(user.id)

    user.save()

    return JsonResponse(construct_json_response(model_to_dict(user)), status=201)


def get_user(request, user_id):
    """
    View method to get User info
    :param request: Django HttpRequest object
    :param user_id: unique identifier for User
    :return: 200-OK and JSON body where 'Data' element is User object
    If User object not found, return 404-NotFound
    """
    # TODO: Use serializers instead of model_to_dict
    user_dict = model_to_dict(get_object_or_404(User, id=user_id))
    return JsonResponse(construct_json_response(user_dict))


@csrf_exempt
def create_assessment(request, user_id):
    """
    View method to create new assessment and assign questions to it
    :param request: Django HttpRequest object
    :param user_id: unique identifier for User
    :return: 201-Created and JSON body where 'Data' element is assessment ID
    400-BadRequest if specified User ID does not exist
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseBadRequest("Specified user ID does not exist.")

    assessment = Assessment.objects.create(user=user)

    # For testing purposes, populates 100 question objects
    prepopulate_questions()

    # TODO: Only add questions matching a relevant filter / category based on user type or assessment type
    for i in range(assessment.question_count):
        # TODO: Select random question ID from existing question IDs, instead of 0-99 range.
        # We are assuming questions are prepopulated.
        question_id = i if assessment.is_not_random_question else random.randint(0, 99)
        assessment.questions.add(Question.objects.get(id=question_id))

    assessment.save()
    return JsonResponse(construct_json_response(assessment.assessment_uuid), status=201)


def get_assessment(request, assessment_id):
    """
    View method to get existing assessment
    :param request: Django HttpRequest object
    :param assessment_id: unique identifier for Assessment
    :return: 200-OK and JSON body where 'Data' element is assessment object, with associated list of attempts
    404-NotFound if assessment does not exist
    """
    assessment = get_object_or_404(Assessment, assessment_uuid=assessment_id)
    assessment_dict = model_to_dict(assessment, exclude=["questions"])

    attempts = [model_to_dict(attempt) for attempt in assessment.attempts.all()]
    assessment_dict['attempts'] = attempts

    return JsonResponse(construct_json_response(assessment_dict))


def get_question(request, assessment_id, question_index):
    """
    View method to get question for assessment
    :param request: Django HttpRequest object
    :param assessment_id: unique identifier for Assessment
    :param question_index: user-friendly array index for question. Subtract 1 for actual array index for Question
    in list of Assessment questions
    :return: 200-OK and JSON body where 'Data' element is question object, with associated list of answer choices
    400-BadRequest if assessment or question does not exist
    404-NotFound if question does not exist
    """
    try:
        assessment = Assessment.objects.get(assessment_uuid=assessment_id)
    except Assessment.DoesNotExist:
        return HttpResponseBadRequest("Assessment does not exist")

    try:
        question = assessment.questions.all()[question_index - 1]
    except Exception as exc:
        # TODO: better exception handling
        return HttpResponseBadRequest("Assessment does not exist")

    question_dict = model_to_dict(question)
    question_dict['Options'] = [model_to_dict(answer, fields={"id", "answer_text"}) for answer in question.answers.all()]

    return JsonResponse(construct_json_response(question_dict))


@csrf_exempt
def submit_answer(request, assessment_id, question_index):
    """
    View method to submit answer for assessment question
    :param request: Django HttpRequest object
    :param assessment_id: unique identifier for Assessment
    :param question_index: user-friendly array index for question. Subtract 1 for actual array index for Question
    in list of Assessment questions
    :return: 200-OK and JSON body where 'Data' element is Boolean-True
    400-BadRequest if assessment is not found
    404-NotFound if question is not found
    """
    body = json.loads(request.body)

    assessment = Assessment.objects.get(assessment_uuid=assessment_id)
    try:
        current_attempt = assessment.current_attempt()
    except Assessment.DoesNotExist:
        return HttpResponseBadRequest("Assessment does not exist")

    question = assessment.questions.all()[question_index - 1]
    AssessmentQuestion.objects.create(attempt=current_attempt, question=question, answer_id=int(body['OptionId']))

    current_attempt.next_question_index += 1
    current_attempt.save()

    return JsonResponse(construct_json_response(True))


@csrf_exempt
def start_assessment(request, assessment_id):
    """
    View method to start or resume assessment.
    - If assessment has in-progress attempt, then if user has specified end_existing_attempt flag, end the existing
    attempt and start a new one. Otherwise, resume the existing one.
    - If no in-progress attempt, start a new attempt
    :param request: Django HttpRequest object
    :param assessment_id: unique identifier for Assessment
    :return: 200-OK and JSON body where 'Data' element is Boolean-True
    404-NotFound if assessment is not found
    """
    end_existing_attempt_flag = False

    if request.body:
        body = json.loads(request.body)
        end_existing_attempt_flag = int(body.get("end_existing_attempt"))

    assessment = get_object_or_404(Assessment, assessment_uuid=assessment_id)

    if assessment.has_in_progress_attempt():
        if end_existing_attempt_flag:
                assessment.current_attempt().end_attempt()
        else:
            current_attempt = assessment.current_attempt()
            current_attempt.last_healthcheck = timezone.now()
            current_attempt.save()

    else:
        AssessmentAttempt.objects.create(
            assessment=assessment, remaining_seconds=assessment.duration_minutes * 60, next_question_index=0
        )

        assessment.test_attempts_count += 1
        assessment.save()

    return JsonResponse(construct_json_response(True))


@csrf_exempt
def end_assessment(request, assessment_id):
    """
    View method to end assessment
    :param request: Django HttpRequest object
    :param assessment_id: unique identifer for Assessment
    :return: 200-OK and JSON body where 'Data' element is Boolean-True
    404-NotFound if assessment is not found
    """

    attempt = get_object_or_404(Assessment, assessment_uuid=assessment_id).current_attempt()

    if not attempt:
        return HttpResponseBadRequest("No assessment attempt found")

    attempt.end_attempt()

    return JsonResponse(construct_json_response(True))
