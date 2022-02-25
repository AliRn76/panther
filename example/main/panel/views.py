"""
    Render: for Template Rendering
    Response: for Rest
    GResponse: for GraphQL
"""

from framework.renderer import TResponse, JResponse, GResponse
from framework.view import View


class AdminView(View):
    def post(self): ...

    def get(self): ...
