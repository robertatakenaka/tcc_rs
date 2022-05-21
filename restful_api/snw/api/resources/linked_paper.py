from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
# from snw.api.schemas import LinkedPaperSchema
# from snw.models import LinkedPaper
# from snw.extensions import db
# from snw.commons.pagination import paginate


from xlingual_papers_recommender import app as rs_app


def handle_response(response):
    if not response:
        code = 201
    elif response.get("error"):
        code = response.get("error_code") or 400
    else:
        code = response.get("success_code") or 200
    return response or {}, code


class LinkedPaperResource(Resource):
    """Single object resource

    ---
    get:
      tags:
        - api
      summary: Get a linked_paper
      description: Get a single linked_paper by ID
      parameters:
        - in: path
          name: linked_paper_id
          schema:
            type: integer
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  linked_paper: LinkedPaperSchema
        404:
          description: linked_paper does not exists
    put:
      tags:
        - api
      summary: Update a linked_paper
      description: Update a single linked_paper by ID
      parameters:
        - in: path
          name: linked_paper_id
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              LinkedPaperSchema
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: linked_paper updated
                  linked_paper: LinkedPaperSchema
        404:
          description: linked_paper does not exists
    """

    method_decorators = [jwt_required()]

    def get(self, pid):
        response = rs_app.get_linked_papers_lists(pid)
        return handle_response(response)

    def put(self, pid):
        return handle_response(rs_app.update_paper(request.json))


class LinkedPaperList(Resource):
    """Creation and get_all

    ---
    get:
      tags:
        - api
      summary: Get a list of linked_papers
      description: Get a list of paginated linked_papers
      responses:
        200:
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResult'
                  - type: object
                    properties:
                      results:
                        type: array
                        items:
                          $ref: '#/components/schemas/LinkedPaperSchema'
    post:
      tags:
        - api
      summary: Create a linked_paper
      description: Create a new linked_paper
      requestBody:
        content:
          application/json:
            schema:
              LinkedPaperSchema
      responses:
        201:
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    example: linked_paper created
                  linked_paper: LinkedPaperSchema
    """

    method_decorators = [jwt_required()]

    def get(self):
        linked_paper_data = request.json
        text = linked_paper_data.get("text")
        subject_area = linked_paper_data.get("subject_area")
        from_year = linked_paper_data.get("from_year")
        to_year = linked_paper_data.get("to_year")
        response = rs_app.search_papers(text, subject_area, from_year, to_year)
        return handle_response(response)

    def post(self):
        # return {"post": "true"}
        linked_paper_data = request.json
        response = rs_app.receive_new_paper(linked_paper_data)
        return handle_response(response)
