import pytest
from folpy import models, utils

# Sample logical statements
logical_statements = [
    ("All men are mortal. Socrates is a man. Therefore, Socrates is mortal.", True),
    ("No birds are dogs. All dogs are animals. Therefore, no birds are animals.", False),
    ("Some mammals are carnivores. All lions are mammals. Therefore, some lions are carnivores.", True),
    ("Laird believes that the most valuable achievement of pure research is its role in expanding knowledge and providing new ideas, while Kim believes that saving lives through medical applications is the most valuable outcome of pure research.", True),
    ("If you eat your meat, then you can have some pudding.", True),
    ("If that animal is a dog, then it is a mammal.", True),
    ("Being unmarried is a necessary condition for being a bachelor.", True),
    ("Being a mammal is a necessary condition for being a dog.", True),
    ("If you spend all day in the sun, you’ll get sunburnt.", False),  # Considering the counterexample of using effective sunblock
    ("All living things deserve moral consideration.", True),
    # Added new logical statements from OpenStax resource
    ("You must complete 120 credit hours to earn a bachelor’s degree.", True),
    ("If you expect to graduate, then you must complete 120 credit hours.", True),
    ("Being unmarried is a necessary condition for being a bachelor.", True),
    ("If you are a bachelor, then you are unmarried.", True),
    ("Being a mammal is a necessary condition for being a dog.", True),
    ("If a creature is a dog, then it is a mammal.", True),
    # Added new logical statements from the Internet Encyclopedia of Philosophy
    ("If John is an only child, then he said that Mary is his sister.", False),
    ("If the Democrats and Republicans are not willing to compromise, then the U.S. will go over the fiscal cliff.", True),
    ("The reason for my uncle’s muscular weakness is the syphilis he suffered from 10 years ago.", True),
    ("Bill will be at the party because he said he would be there.", True),
    ("The keys are either in the kitchen or the bedroom. They are not in the kitchen, so they must be in the bedroom.", True),
    # Added new logical statements based on deductive, inductive, and conductive arguments
    ("Tom is happy only if he is playing guitar. Tom is not playing guitar. Therefore, Tom is not happy.", True),
    ("97% of the Republicans in town Z voted for McX, Jones is a Republican in town Z; therefore, Jones probably voted for McX.", True),
    ("It most likely won’t rain tomorrow. The sky is red tonight. Also, the weather channel reported a 30% chance of rain for tomorrow.", True),
    # Added new logical statements derived from the content on the "Argument" page
    ("John is an only child. John said that Mary is his sister. Therefore, John is not an only child.", False),
    ("The Democrats and Republicans are not willing to compromise. If the Democrats and Republicans are not willing to compromise, then the U.S. will go over the fiscal cliff.", True),
    ("The results of the test are in. Even though few syphilis patients get paresis, we suspect that the reason for your uncle’s paresis is the syphilis he suffered from 10 years ago.", True),
    ("Bill will be at the party. Bill will be at the party because Bill will be at the party.", False),  # Circular reasoning is not valid
    ("Sasha Obama has a sibling. Therefore, Sasha is not an only child.", True),
    ("Obama is U.S. President. Therefore, the earth is the third planet from the sun or it isn’t.", False),  # Irrelevant support does not constitute a valid argument
    ("Tom is happy only if the Tigers win. The Tigers lost; therefore, Tom is definitely not happy.", True),
    ("97% of the Republicans in town Z voted for McX, Jones is a Republican in town Z; therefore, Jones voted for McX.", True),
    ("It most likely won’t rain tomorrow. The sky is red tonight. Also, the weather channel reported a 30% chance of rain for tomorrow.", False),  # Convergent premises do not necessarily lead to a true conclusion
    # Added new logical statements to the array
    ("If all fruits are sweet and some apples are sour, then some apples are not fruits.", False),
    ("Every square is a rectangle but not every rectangle is a square.", True),
    ("If it rains, the ground gets wet. The ground is not wet, so it did not rain.", True),
    ("All roses are flowers and some flowers fade quickly; therefore, some roses fade quickly.", False),
    ("If a number is divisible by 4, then it is an even number. 8 is divisible by 4, so it is an even number.", True),
    ("No reptiles have fur. All dogs have fur. Therefore, no dogs are reptiles.", True),
    ("If a vehicle is a car, then it has wheels. A bicycle has wheels, so it is a car.", False),
    ("All bachelors are unmarried men. John is unmarried. Therefore, John is a bachelor.", False),
    ("If a drink is a soda, it is carbonated. This drink is not carbonated, so it is not a soda.", True),
    ("If a plant is a cactus, it can survive in the desert. This plant can survive in the desert, so it is a cactus.", False),  # Fallacy of affirming the consequent
    ("All prime numbers are odd. 17 is a prime number. Therefore, 17 is odd.", True),
    ("If it is summer, then the days are long. The days are not long, so it is not summer.", True),
    ("Every even number greater than 2 can be expressed as the sum of two primes. 18 is an even number greater than 2. Therefore, 18 can be expressed as the sum of two primes.", True),
    ("If an animal is a bird, it can fly. Penguins are birds. Therefore, penguins can fly.", False),  # Not all birds can fly
    ("A square has four sides. This shape has four sides. Therefore, this shape is a square.", False),  # Not all four-sided shapes are squares
    ("If a number is divisible by 2, it is even. 10 is divisible by 2. Therefore, 10 is even.", True),
    ("All humans are mortal. Plato is human. Therefore, Plato is mortal.", True),
    ("If a food is a fruit, it has seeds. Bananas are fruits. Therefore, bananas have seeds.", True),  # Bananas have tiny seeds
    ("If a vehicle has wheels, it is a car. A bicycle has wheels. Therefore, a bicycle is a car.", False),  # Not all vehicles with wheels are cars
    ("If a person is a doctor, they have a medical degree. Sarah is a doctor. Therefore, Sarah has a medical degree.", True),
    ("All spiders have eight legs. This animal has six legs. Therefore, this animal is not a spider.", True),
    ("If it is raining, the ground will be wet. It is not raining. Therefore, the ground is not wet.", False),  # The ground could be wet for reasons other than rain
    ("Every triangle has three sides. This shape has three sides. Therefore, this shape is a triangle.", False),  # The shape could be any three-sided figure, not necessarily a triangle
    ("If a vehicle is a bicycle, it has two wheels. This vehicle has two wheels. Therefore, this vehicle is a bicycle.", False),  # Other vehicles, like motorcycles, also have two wheels
    ("All citizens have the right to vote. Maria is a citizen. Therefore, Maria has the right to vote.", True),
    ("If a food item is an apple, it is a fruit. This food item is a fruit. Therefore, this food item is an apple.", False),  # The food item could be any type of fruit
    ("If a plant is a fern, it does not produce flowers. This plant does not produce flowers. Therefore, this plant is a fern.", False),  # There are other non-flowering plants besides ferns
    ("If a figure is a circle, it has no corners. This figure has no corners. Therefore, this figure is a circle.", False),  # Not all cornerless figures are circles
    ("All cats are mammals. All lions are cats. Therefore, all lions are mammals.", True),
    ("If a substance is an acid, it turns litmus paper red. This substance turns litmus paper red. Therefore, this substance is an acid.", False),  # Not all substances that turn litmus paper red are acids
    ("Every insect has six legs. This creature has six legs. Therefore, this creature is an insect.", False),  # Other creatures besides insects can have six legs
    ("If a plant is a rose, it has thorns. This plant has thorns. Therefore, this plant is a rose.", False),  # Other plants besides roses can have thorns
    ("All birds lay eggs. All chickens are birds. Therefore, all chickens lay eggs.", True),
    ("If it is a fish, it lives in water. This animal lives in water. Therefore, this animal is a fish.", False),  # Other animals besides fish live in water
    ("If a vehicle is a truck, it is larger than a car. This vehicle is larger than a car. Therefore, this vehicle is a truck.", False),  # Other vehicles besides trucks can be larger than cars
    # ... more logical statements will be added here to reach a total of 100
    ("If a person is a teacher, they work at a school. Alex is a teacher. Therefore, Alex works at a school.", True),
    ("All roses are red. That flower is red. Therefore, that flower is a rose.", False),  # The flower could be any red flower, not necessarily a rose
    ("If a tree is an oak, it has leaves. This tree has leaves. Therefore, this tree is an oak.", False),  # Many trees have leaves, not just oaks
    ("Every square has four sides. This shape has four sides. Therefore, this shape is a square.", False),  # The shape could be any quadrilateral
    ("If an animal is a mammal, it has fur. This animal has fur. Therefore, this animal is a mammal.", False),  # Not all animals with fur are mammals
    ("All birds can fly. An ostrich is a bird. Therefore, an ostrich can fly.", False),  # Ostriches are birds that cannot fly
    ("If it is a reptile, it is cold-blooded. This animal is cold-blooded. Therefore, this animal is a reptile.", False),  # Other animals besides reptiles are also cold-blooded
    ("All elected officials are trustworthy. This person is an elected official. Therefore, this person is trustworthy.", False),  # Being an elected official does not necessarily mean the person is trustworthy
    ("If a plant is a sunflower, it follows the sun. This plant follows the sun. Therefore, this plant is a sunflower.", False),  # Other plants also follow the sun
    ("Every insect has six legs. This creature has six legs. Therefore, this creature is an insect.", False),  # Other creatures besides insects can have six legs
    ("If a number is divisible by 2, it is even. 14 is divisible by 2. Therefore, 14 is even.", True),
    ("All planets orbit a star. Earth is a planet. Therefore, Earth orbits a star.", True),
    ("If a food is a banana, it is yellow. This food is yellow. Therefore, this food is a banana.", False),  # Other foods are yellow besides bananas
    ("Every human has a heart. This creature has a heart. Therefore, this creature is a human.", False),  # Other creatures besides humans have hearts
    ("If a vehicle has two wheels, it is a bicycle. This vehicle has two wheels. Therefore, this vehicle is a bicycle.", False),  # Other vehicles, like motorcycles, also have two wheels
    ("All apples are fruits. This item is an apple. Therefore, this item is a fruit.", True),
    ("If a liquid is water, it is clear. This liquid is clear. Therefore, this liquid is water.", False),  # Other clear liquids exist besides water
    ("All dogs bark. This animal barks. Therefore, this animal is a dog.", False),  # Other animals can bark besides dogs
    ("If a shape is a circle, it has no corners. This shape has no corners. Therefore, this shape is a circle.", False),  # Other shapes can have no corners besides circles
    ("Every prime number is odd. 2 is a prime number. Therefore, 2 is odd.", False),  # 2 is an even prime number
    ("If a person is a firefighter, they can extinguish fires. This person can extinguish fires. Therefore, this person is a firefighter.", False),  # Other people can extinguish fires besides firefighters
    ("All computers can access the internet. This device is a computer. Therefore, this device can access the internet.", True),
    ("If a book is a novel, it has a narrative. This book has a narrative. Therefore, this book is a novel.", False),  # Other books besides novels have narratives
    # ... more logical statements will be added here to reach a total of 1000
    # New logical statements generated with their Prolog representation and truth values
    ("exists(X, (is_a(X, men) & are_bipedal_and_men_are_mortal(X))).", False),
    ("forall(X, (is_a(X, mammals) -> have_six_legs_and_mammals_have_wheels(X))).", True),
    ("forall(X, (is_a(X, insects) -> have_wheels_or_insects_have_fur(X))).", True),
    # ... more new logical statements follow ...
    # The above statements are a sample, the actual code will include all 900 new statements
    ("All fish live in water. This animal lives in water. Therefore, this animal is a fish.", False),  # Other animals besides fish live in water
    ("If a person is a chef, they can cook. This person can cook. Therefore, this person is a chef.", False),  # Other people can cook besides chefs
    ("Every square is a rectangle. This shape is a rectangle. Therefore, this shape is a square.", False),  # Not all rectangles are squares
]

@pytest.mark.parametrize("statement, expected", logical_statements)
def test_logical_statement(statement, expected):
    assert parse_and_evaluate(statement) == expected, f"Statement failed: {statement}"

def parse_and_evaluate(statement):
    # This function will use the "logical" library's functionality to parse and evaluate the statement
    # Translate the English statement into a formal logical structure
    # This is a placeholder for the actual logic to be implemented
    logical_structure = translate_to_logical_structure(statement)

    # Construct the folpy Formula object from the logical structure
    formula = models.Formula(logical_structure)

    # Evaluate the formula using folpy's methods
    # This is a placeholder for the actual evaluation logic to be implemented
    result = evaluate_formula(formula)

    return result

def translate_to_logical_structure(statement):
    # TODO: Implement the logic to parse English statements and convert them into a formal logical structure
    # This function should handle various logical forms such as universal quantification, conditional, biconditional, conjunction, disjunction, negation, etc.
    # The following is a simplified example of how to translate a statement into folpy's logical structure
    # The actual implementation should dynamically construct the logical structure based on the input statement

    # Example translation for a universal quantification statement
    if "All" in statement and "are" in statement:
        subject, predicate = statement.split(" are ")
        subject = subject.replace("All ", "")
        x = models.Variable('x')
        return models.ForAll(x, models.Implies(models.Predicate(subject)(x), models.Predicate(predicate)(x)))

    # Example translation for a conditional statement
    if "If" in statement and "then" in statement:
        antecedent, consequent = statement.split(" then ")
        antecedent = antecedent.replace("If ", "")
        return models.Implies(models.Predicate(antecedent), models.Predicate(consequent))

    # Additional logical structures to be added here

    # Placeholder for unrecognized statements
    return None

def evaluate_formula(formula):
    # TODO: Implement the logic to evaluate the truth value of the logical structure using folpy
    # This is a simplified example of how to evaluate a formula using a predefined model in folpy
    # For the purpose of this example, we assume we have a model where all humans are indeed mortal
    # The actual implementation should include a method to evaluate the formula based on the model
    model = models.Model(
        domain={'Socrates', 'Plato', 'Aristotle'},
        interpretation={
            'Human': lambda x: x in {'Socrates', 'Plato', 'Aristotle'},
            'Mortal': lambda x: x in {'Socrates', 'Plato', 'Aristotle'}
        }
    )
    return model.satisfies(formula)
