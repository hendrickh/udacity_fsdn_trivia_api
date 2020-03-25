import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format(
            'postgres@localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_categories(self):

        response = self.client().get('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertNotEqual(len(data['categories']), 0)

    def test_get_questions(self):

        response = self.client().get('/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))

    def test_get_questions_fails_404_error(self):

        response = self.client().get('/questions?page=999')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_delete_question(self):

        # create a new question to be deleted
        question = Question(question="foo", answer="foo",
                            category=1, difficulty=1)
        question.insert()

        question_id = question.id

        total_questions = Question.query.all()

        response = self.client().delete('/questions/{}'.format(question_id))
        data = json.loads(response.data)

        total_questions_after_deletion = Question.query.all()

        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)
        self.assertTrue(len(total_questions) -
                        len(total_questions_after_deletion) == 1)
        self.assertEqual(question, None)

    def test_delete_question_fails_422_error(self):

        response = self.client().delete('/questions/{}'.format(999))
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)

    def test_create_new_question(self):

        self.new_question = {
            'question': 'foo?',
            'answer': 'foo!',
            'difficulty': 1,
            'category': 1
        }

        total_questions_before = Question.query.all()

        response = self.client().post('/questions', json=self.new_question)
        data = json.loads(response.data)

        total_questions_after = Question.query.all()

        question = Question.query.filter_by(id=data['created']).one_or_none()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(total_questions_after) -
                        len(total_questions_before) == 1)
        self.assertIsNotNone(question)

    def test_create_new_question_fails_422_error(self):

        total_questions_before = Question.query.all()

        response = self.client().post('/questions', json={})
        data = json.loads(response.data)

        total_questions_after = Question.query.all()

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertTrue(len(total_questions_after) ==
                        len(total_questions_before))

    def test_search_questions(self):
        response = self.client().post('/questions/search',
                                      json={'searchTerm': 'anne'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 1)
        self.assertEqual(data['questions'][0]['id'], 4)
        self.assertTrue(data['total_questions'])

    def test_search_questions_fails_422_error(self):
        response = self.client().post('/questions/search',
                                      json={})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_search_questions_fails_404_error(self):
        response = self.client().post('/questions/search',
                                      json={'searchTerm': 'foo_doesnt_exist'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_questions_by_category(self):

        response = self.client().get('/categories/2/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertNotEqual(len(data['questions']), 0)
        self.assertEqual(data['current_category'], 'Art')

    def test_get_questions_by_category_fails_404_error(self):

        response = self.client().get('/categories/999/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_play_quiz_game(self):
        self.previous_questions = {
            'previous_questions': [7, 17],
            'quiz_category': {
                'type': 'Science',
                'id': 1
            }

        }

        response = self.client().post('/quizzes',
                                      json=self.previous_questions)

        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])
        self.assertEqual(data['question']['category'], 1)
        self.assertNotEqual(data['question']['id'], 7)
        self.assertNotEqual(data['question']['id'], 17)

    def test_play_quiz_game_fails_400_error(self):

        response = self.client().post('/quizzes', json={})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
