
from django.contrib import admin

from .models import (
    Course,
    Lesson,
    Instructor,
    Learner,
    Question,
    Choice,
    Submission,
)


# Display questions inside the course admin page
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


# Display choices inside the question admin page
class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 4


# Display lessons inside the course admin page
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Course admin configuration
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


# Question admin configuration
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ['question_text', 'course', 'grade']
    search_fields = ['question_text']


# Lesson admin configuration
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    search_fields = ['title']


# Register models
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission)
