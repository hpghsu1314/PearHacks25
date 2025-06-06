
class User:
    """
    This has information about the User. This will include dietary restrictions and other information.
        - username (String): Username defined by consumer
        - restrictions (Dictionary): A dictionary of strings -> integers. Integers define the danger scale of the ingredient.
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
        return self.restrictions[ingredient.lower()]
    

    def add_restriction(self, ingredient, scale):
        assert isinstance(ingredient, str)
        assert isinstance(scale, int)

        self.restrictions[ingredient.lower()] = scale
        return self.restrictions[ingredient.lower()]
    
    
    def remove_restriction(self, ingredient):
        assert ingredient in self.restrictions.keys()
        self.restrictions.pop(ingredient)
        return self.restrictions