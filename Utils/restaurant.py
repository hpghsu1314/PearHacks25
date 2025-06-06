from Utils.dish import Dish

class Restaurant:
    """
    This has information about each restaurant. Restaurants will have information on each dish on the menu.
        - name (String): Restaurant name (need not be unique)
        - menu (List): A list of Dish objects. See dish.py for information on Dish objects.
    """
    def __init__(self, menu, menu_pdf, name):
        self.name = name
        self.menu_pdf = menu_pdf
        self.menu = menu
        self.actions = {"Add Ingredient" : Dish.add_ingredient, "Change Ingredients": Dish.change_ingredients, "Remove Ingredient": Dish.remove_ingredient, "Get Price": Dish.get_price}


    def get_menu(self):
        return self.menu
    

    def get_restaurant(self):
        return self.name
    

    def change_restaurant_name(self, new_name):
        self.name = new_name


    def add_dish(self, new_dish):
        assert isinstance(new_dish, Dish)
        self.menu.append(new_dish)


    def dish_change(self, action, dish_name, argument):
        for dish in self.menu:
            assert isinstance(dish, Dish)
            if dish.get_dish() == dish_name:
                print(action)
                print(self.actions.keys())
                return self.actions[action](dish, argument)
                
    
    def get_menu_pdf(self):
        return self.menu_pdf
            

    # This is a helper function for debugging
    # Allows the developer to see what possible functions can be called
    def actions_arguments(self):
        return self.actions.keys()