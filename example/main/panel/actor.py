from framework.actors import ApiActor, TemplateActor


class UserActor(ApiActor):
    def get_request(self): ...

    def post_request(self): ...

