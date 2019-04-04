from uuid import uuid4
from django.db import models
from django.utils import timezone


class User(models.Model):
    """
    Model for a User
    """
    id = models.AutoField(primary_key=True)
    user_uuid = models.UUIDField(default=uuid4())
    slug = models.CharField(max_length=200, null=True)
    title = models.CharField(max_length=200, null=True)
    status = models.IntegerField(default=1)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)


class QuestionAnswer(models.Model):
    """
    Model for answer choice for a given question.
    Question maps to one or more QuestionAnswer objects
    """
    id = models.AutoField(primary_key=True)
    answer_text = models.CharField(max_length=500)
    is_correct_answer = models.BooleanField(default=False)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name="answers")


class Question(models.Model):
    """
    Model for a question
    """
    id = models.AutoField(primary_key=True)
    question_text = models.CharField(max_length=500)


class Assessment(models.Model):
    """
    Model for an assessment
    Assessment maps to one or more Question objects
    User maps to one or more Assessment objects
    """
    assessment_uuid = models.UUIDField(primary_key=True, default=uuid4)
    is_not_random_question = models.BooleanField(null=True)
    is_not_random_question_sort_by_index = models.BooleanField(null=True)
    assessment_info = models.CharField(max_length=200, null=True)
    test_attempts_count = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=60)
    question_count = models.IntegerField(default=15)
    test_type = models.IntegerField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question)

    def has_in_progress_attempt(self, *args, **kwargs):
        """
        Returns whether Assessment currently has in-progress attempt
        :param args:
        :param kwargs:
        :return: boolean
        """
        attempts = self.attempts.all()

        if not attempts:
            return False

        return not attempts.latest('start_date').is_assessment_end

    def current_attempt(self, *args, **kwargs):
        """
        Returns current in-progress attempt for Assessment or None
        :param args:
        :param kwargs:
        :return: AssessmentAttempt or None
        """

        try:
            return AssessmentAttempt.objects.get(assessment=self, is_assessment_end=False)
        except AssessmentAttempt.DoesNotExist:
            return None


class AssessmentAttempt(models.Model):
    """
    Model for an AssessmentAttempt
    Assessment maps to one or more AssessmentAttempt objects
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    is_assessment_end = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    remaining_seconds = models.IntegerField()
    next_question_index = models.IntegerField(null=True)
    last_healthcheck = models.DateTimeField(default=timezone.now())

    def update_time_remaining(self, *args, **kwargs):
        """
        Updates time remaining for assessment attempt, in seconds
        :param args:
        :param kwargs:
        :return: None
        """
        current_time = timezone.now()
        time_elapsed = current_time - self.last_healthcheck

        self.remaining_seconds -= time_elapsed.total_seconds()
        self.last_healthcheck = current_time
        self.save()

    def end_attempt(self, *args, **kwargs):
        """
        Ends current assessment attempt
        :param args:
        :param kwargs:
        :return: None
        """
        self.is_assessment_end = True
        self.end_date = timezone.now()
        self.save()


class AssessmentQuestion(models.Model):
    """
    Model for a question attempt belonging to an AssessmentAttempt
    Question can map to one or more AssessmentQuestion objects
    Attempt can map to one or more AssessmentQuestion objects
    """
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name="questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_id = models.IntegerField(null=True)
