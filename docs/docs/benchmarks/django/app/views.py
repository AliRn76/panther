from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view()
def hello_world(request):
    return Response(status=200)
