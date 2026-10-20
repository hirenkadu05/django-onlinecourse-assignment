
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views import generic

from .models import (
    Course,
    Enrollment,
    Question,
    Choice,
    Submission,
)

import logging

logger = logging.getLogger(__name__)


# User registration
def registration_request(request):
    context = {}

    if request.method == 'GET':
        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )

    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']

        if User.objects.filter(username=username).exists():
            context['message'] = "User already exists."
            return render(
                request,
                'onlinecourse/user_registration_bootstrap.html',
                context
            )

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        login(request, user)
        return redirect('onlinecourse:index')


# User login
def login_request(request):
    context = {}

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')

        context['message'] = "Invalid username or password."

        return render(
            request,
            'onlinecourse/user_login_bootstrap.html',
            context
        )

    return render(
        request,
        'onlinecourse/user_login_bootstrap.html',
        context
    )


# User logout
def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


# Check course enrollment
def check_if_enrolled(user, course):
    if not user.is_authenticated:
        return False

    return Enrollment.objects.filter(
        user=user,
        course=course
    ).exists()


# Course list view
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user

        courses = Course.objects.order_by(
            '-total_enrollment'
        )[:10]

        for course in courses:
            course.is_enrolled = check_if_enrolled(
                user,
                course
            )

        return courses


# Course details view
class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'


# Enroll in a course
def enroll(request, course_id):
    course = get_object_or_404(
        Course,
        pk=course_id
    )

    user = request.user

    if user.is_authenticated:
        if not check_if_enrolled(user, course):
            Enrollment.objects.create(
                user=user,
                course=course,
                mode='honor'
            )

            course.total_enrollment += 1
            course.save()

    return HttpResponseRedirect(
        reverse(
            'onlinecourse:course_details',
            args=(course.id,)
        )
    )


# Extract answers selected in the exam form
def extract_answers(request):
    submitted_answers = []

    for key in request.POST:
        if key.startswith('choice_'):
            for value in request.POST.getlist(key):
                try:
                    submitted_answers.append(int(value))
                except (ValueError, TypeError):
                    continue

    return submitted_answers


# Submit exam
@login_required
def submit(request, course_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(
        Course,
        pk=course_id
    )

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course
    )

    selected_ids = extract_answers(request)

    valid_choices = Choice.objects.filter(
        id__in=selected_ids,
        question__course=course
    )

    submission = Submission.objects.create(
        enrollment=enrollment
    )

    submission.choices.set(valid_choices)

    return redirect(
        'onlinecourse:show_exam_result',
        course_id=course.id,
        submission_id=submission.id
    )


# Calculate and display exam result
@login_required
def show_exam_result(request, course_id, submission_id):

    course = get_object_or_404(
        Course,
        pk=course_id
    )

    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__course=course,
        enrollment__user=request.user
    )

    selected_ids = set(
        submission.choices.values_list(
            'id',
            flat=True
        )
    )

    questions = Question.objects.filter(
        course=course
    ).prefetch_related('choice_set')

    total_score = 0
    possible_score = 0
    question_results = []

    for question in questions:

        possible_score += question.grade

        choices = list(question.choice_set.all())

        selected_for_question = [
            choice.id
            for choice in choices
            if choice.id in selected_ids
        ]

        is_correct = question.is_get_score(
            selected_for_question
        )

        if is_correct:
            total_score += question.grade

        question_results.append({
            'question': question,
            'selected_ids': selected_for_question,
            'is_correct': is_correct,
            'choices': choices,
        })

    if possible_score > 0:
        percentage = (
            total_score / possible_score
        ) * 100
    else:
        percentage = 0

    passed = (
        possible_score > 0
        and percentage >= 80
    )

    context = {
        'course': course,
        'submission': submission,
        'grade': total_score,
        'total_score': total_score,
        'possible_score': possible_score,
        'percentage': percentage,
        'passed': passed,
        'question_results': question_results,
        'questions': questions,
    }

    return render(
        request,
        'onlinecourse/exam_result_bootstrap.html',
        context
    )
