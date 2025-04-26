
class Dish:
    """
    This has information about each dish. Dishes will include the following attributes:
        - name (String): Unique identifiable name (unique per restaurant)
        - ingredients (List): Ingredients for this dish
        - Price (Float): The price of the dish
    """
    def __init__(self, name, ingredients, price):
        self.name = name
        self.ingredients = ingredients
        self.price = price

    def get_price(self):
        return self.price
    
    def get_ingredients(self):
        return self.ingredients
    
    def get_dish(self):
        return self.name