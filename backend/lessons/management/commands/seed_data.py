from django.core.management.base import BaseCommand
from lessons.models import Lesson, Question


class Command(BaseCommand):
    help = 'Seed database with sample lesson data'

    def handle(self, *args, **options):
        if Lesson.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists, skipping seed'))
            return

        lesson = Lesson.objects.create(
            title="Introduction to Python Programming",
            text="""
Python is a high-level, interpreted programming language known for its simplicity and readability.
Created by Guido van Rossum and first released in 1991, Python has become one of the most popular
programming languages in the world.

Key features of Python include:
- Simple, clean syntax that emphasizes readability
- Dynamic typing and automatic memory management
- A rich standard library
- Support for multiple programming paradigms
- Cross-platform compatibility

Python is widely used in web development, data science, artificial intelligence, automation,
and many other fields. Its gentle learning curve makes it an excellent choice for beginners,
while its powerful features make it suitable for complex enterprise applications.
            """.strip()
        )

        questions_data = [
            {
                "text": "Who created the Python programming language?",
                "correct_answer": "Guido van Rossum",
                "distractor_1": "James Gosling",
                "distractor_2": "Bjarne Stroustrup",
                "order": 1,
            },
            {
                "text": "In what year was Python first released?",
                "correct_answer": "1991",
                "distractor_1": "1989",
                "distractor_2": "1995",
                "order": 2,
            },
            {
                "text": "What programming paradigm does Python support? (Name at least one)",
                "correct_answer": "object-oriented",
                "distractor_1": "only procedural",
                "distractor_2": "only logic",
                "order": 3,
            },
            {
                "text": "What is Python known for emphasizing in its syntax?",
                "correct_answer": "readability",
                "distractor_1": "brevity at any cost",
                "distractor_2": "explicit typing everywhere",
                "order": 4,
            },
            {
                "text": "Is Python a compiled or interpreted language?",
                "correct_answer": "interpreted",
                "distractor_1": "compiled to machine code only",
                "distractor_2": "transpiled to C++ exclusively",
                "order": 5,
            },
        ]

        for q_data in questions_data:
            Question.objects.create(
                lesson=lesson,
                **q_data
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created lesson with {len(questions_data)} questions'
            )
        )
