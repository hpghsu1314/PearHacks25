
class User:
    """
    This has information about the User. This will include dietary restrictions and other information.
        - username (String): Username defined by consumer
        - restrictions (List): A list of strings defining the dietary restrictions of our user
    """
    def __init__(self, username, restrictions):
        self.username = username
        self.restrictions = restrictions

    def get_username(self):
        return self.username
    
    def get_dietary_restrictions(self):
        return self.restrictions