"""
openapi: 3.0.0
info:
  title: {{ project_name }}
paths:
  /example:
    get:
      summary: Example endpoint
      responses:
        '200':
          description: A successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
components:
  schemas:
    ExampleSchema:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
"""
