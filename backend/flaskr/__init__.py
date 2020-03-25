import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app, resources={'/': {'origins': '*'}})

    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        categories_dict = {}

        # Iterate through the list of categories.
        for category in categories:
            categories_dict[category.id] = category.type

        # If there is no category exist at all, return a 404 error.
        if (len(categories_dict) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'categories': categories_dict
        })

    '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    @app.route('/questions')
    def get_questions():

        questions = Question.query.all()

        total_questions = len(questions)
        current_questions = paginate_qns(request, questions)

        categories = Category.query.all()
        categories_dict = {}

        # Iterate through the list of categories.
        for category in categories:
            categories_dict[category.id] = category.type

        # If there is no questions exist at all, return a 404 error.
        if (len(current_questions) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'categories': categories_dict
        })

    '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter_by(id=id).one_or_none()

            # If there is no question found by that Question Id, return a 404 error.
            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': id
            })

        except:
            abort(422)

    '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        # Validate if the request body has all the required keys. Else, return a 422 error.
        if ((body.get('question') is None) or (body.get('answer') is None) or (body.get('difficulty') is None) or (body.get('category') is None)):
            abort(422)
        else:
            new_question = body.get('question')
            new_answer = body.get('answer')
            new_difficulty = body.get('difficulty')
            new_category = body.get('category')

            try:
                question = Question(
                    question=new_question,
                    answer=new_answer,
                    difficulty=new_difficulty,
                    category=new_category
                )
                question.insert()

                questions = Question.query.order_by(Question.id).all()
                current_questions = paginate_qns(request, questions)

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'question_created': question.question,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })

            except:
                abort(422)
    '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()

        # Check if the request body contains the 'searchTerm' key. Otherwise, return a 422 error.
        if body.get('searchTerm') is None:
            abort(422)

        searchTerm = body.get('searchTerm', '')

        questions = Question.query.filter(
            Question.question.ilike(f'%{searchTerm}%')).all()

        # If there is no question that contains the value of the 'searchTerm', return a 404 error.
        if (len(questions) == 0):
            abort(404)

        paginated = paginate_qns(request, questions)

        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all())
        })

    '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):
        category = Category.query.filter_by(id=id).one_or_none()

        # If there is no category that matches the category id provided, return a 404 error.
        if (category is None):
            abort(404)

        questions = Question.query.filter_by(category=category.id).all()

        paginated = paginate_qns(request, questions)

        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all()),
            'current_category': category.type
        })
    '''

  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''

    @app.route('/quizzes', methods=['POST'])
    def get_random_question():
        body = request.get_json()

        if ((body.get('previous_questions') is None) or (body.get('quiz_category') is None)):
            abort(400)

        previous = body.get('previous_questions')

        category = body.get('quiz_category')

        # The category 'ALL' has been assigned the value of '0'.
        if (category['id'] == 0):
            questions = Question.query.all()
        else:
            questions = Question.query.filter_by(category=category['id']).all()

        total = len(questions)

        # This function is used to mark a question that has come up before.
        def check_if_previously_used(question):
            used = False
            for q in previous:
                if (q == question.id):
                    used = True

        random_question = questions[random.randrange(0, len(questions), 1)]

        # For every random_question fetched from the DB, check if it has been used before.
        while (check_if_previously_used(random_question)):
            random_question = questions[random.randrange(0, len(questions), 1)]

            if (len(previous) == total):
                return jsonify({
                    'success': True
                })

        return jsonify({
            'success': True,
            'question': random_question.format()
        })

    '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(400)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    return app


def paginate_qns(request, questions):
    # This function is a helper function to assist with paginating the responses.
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions_to_paginate = [question.format() for question in questions]
    current_questions = questions_to_paginate[start:end]

    return current_questions
