
class Restaurant:
    """
    This has information about each restaurant. Restaurants will have information on each dish on the menu.
        - name (String): Restaurant name (need not be unique)
        - menu (List): A list of Dish objects. See dish.py for information on Dish objects.
    """
    def __init__(self, name, menu):
        self.name = name
        self.menu = menu

    def get_menu(self):
        return self.menu
    
    def get_restaurant(self):
        return self.name