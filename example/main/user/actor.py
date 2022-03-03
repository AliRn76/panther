from framework.actors import TemplateActor, ApiActor


class UserActor(ApiActor):
    def get_request(self): ...

    def post_request(self): ...
