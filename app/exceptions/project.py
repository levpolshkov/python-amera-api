import falcon


class ProjectMemberNotFound(falcon.HTTPBadRequest):
    def __init__(self):
        title = "Project member not found"
        description = "There was a problem validating your participation in this project"
        super().__init__(title=title, description=description)


class NotEnoughPriviliges(falcon.HTTPBadRequest):
    def __init__(self):
        title = "Not enough project privileges"
        description = "There was a problem validating your project privileges for this action"
        super().__init__(title=title, description=description)


class NotProjectOwner(falcon.HTTPBadRequest):
    def __init__(self):
        title = "You are not the project owner"
        description = "There was a problem validating your project ownership in order to make this action"
        super().__init__(title=title, description=description)


class ContractDoesNotBelongProject(falcon.HTTPBadRequest):
    def __init__(self):
        title = "Specified contract does not belong to this project"
        description = "There was a problem validating the reference of the specified contract to this project"
        super().__init__(title=title, description=description)


class MemberDoesNotBelongToContract(falcon.HTTPBadRequest):
    def __init__(self):
        title = "This contract invite is intended for another member"
        description = "There was a problem validating the reference of the specified contract to yourself"
        super().__init__(title=title, description=description)
