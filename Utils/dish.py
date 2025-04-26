
class Dish:
    """
    This has information about each dish. Dishes will include the following attributes:
        - name (String): Unique identifiable name (unique per restaurant)
        - ingredients (List): Ingredients for this dish
        - Price (Float): The price of the dish
    """
    def __init__(self, name, ingredients, price):
        self.name = name
        self.ingredients = self.change_ingredients(ingredients)
        self.price = price

    def get_price(self):
        return self.price
    
    def get_ingredients(self):
        return self.ingredients
    
    def get_dish(self):
        return self.name
    
    def add_ingredient(self, ingredient):
        self.ingredients.append(ingredient.lower())
        return self.ingredients

    def change_ingredients(self, new_ingredients):
        self.ingredients = []
        for ingredient in new_ingredients:
            self.ingredients.append(ingredient.lower())
        return self.ingredients
    
    def remove_ingredient(self, ingredient):
        self.ingredients.remove(ingredient.lower())
        return self.ingredients
    
    def list_information(self):
        return f"{self.name} costs {self.price} and has ingredients {self.ingredients}"