
class User:
    """
    This has information about the User. This will include dietary restrictions and other information.
        - username (String): Username defined by consumer
        - restrictions (Dictionary): A list of strings defining the dietary restrictions of our user
    """
    def __init__(self, username, restrictions):
        assert isinstance(restrictions, dict)
        self.username = username
        self.restrictions = restrictions


    def get_username(self):
        return self.username
    

    def get_dietary_restrictions(self):
        return self.restrictions
    

    def get_ingredient_restriction(self, ingredient):
        assert ingredient in self.restrictions.keys()

        return self.restrictions[ingredient.lower()]
    

    def change_restriction(self, ingredient, scale):
        assert ingredient in self.restrictions.keys()

        self.restrictions[ingredient.lower()] = scale
        return self.restrictions[ingredient]
    

    def add_restriction(self, ingredient, scale):
        assert isinstance(ingredient, str)
        self.restrictions[ingredient.lower()] = scale
        return self.restrictions[ingredient]