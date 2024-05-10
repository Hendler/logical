import unittest
# Importing necessary modules from folpy based on the GitHub repository structure
from folpy.utils.methods import substructures_updown, substructures_downup, substructures_by_maximals
from folpy.examples.lattices import gen_chain, rhombus, M3, N5
from folpy.examples.posets import gen_chain as gen_chain_poset, rhombus as rhombus_poset, M3 as M3_poset
from folpy import utils

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
    # Manually added logical statements with their Prolog representation and truth values
    ("All cats are animals. Therefore, if something is a cat, it is an animal.", True, "animal(X) :- cat(X)."),
    ("If something is a fish, it can swim. Sharks are fish. Therefore, sharks can swim.", True, "can_swim(X) :- fish(X)."),
    ("All birds can fly. Ostriches are birds. Therefore, ostriches can fly.", False, "can_fly(X) :- bird(X), not(ostrich(X))."),
    ("If a plant is a cactus, it lives in the desert. Therefore, if something lives in the desert, it is a cactus.", False, "cactus(X) :- lives_in_desert(X)."),
    ("Every square is a rectangle. Therefore, if something is a rectangle, it is a square.", False, "square(X) :- rectangle(X)."),
    ("If a creature has feathers, it is a bird. A swan has feathers. Therefore, a swan is a bird.", True, "bird(X) :- has_feathers(X)."),
    ("All planets revolve around the sun. Earth is a planet. Therefore, Earth revolves around the sun.", True, "revolves_around_sun(X) :- planet(X)."),
    ("If an animal is a reptile, it lays eggs. A crocodile is a reptile. Therefore, a crocodile lays eggs.", True, "lays_eggs(X) :- reptile(X)."),
    ("Every prime number is odd. Eleven is a prime number. Therefore, eleven is odd.", True, "odd(X) :- prime(X), not(X = 2)."),
    ("If a figure is a rectangle, it has four sides. A square is a rectangle. Therefore, a square has four sides.", True, "has_four_sides(X) :- rectangle(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    # New logical statements generated with their Prolog representation and truth values
    ("exists(X, (is_a(X, men) & are_bipedal_and_men_are_mortal(X))).", False),
    ("forall(X, (is_a(X, mammals) -> have_six_legs_and_mammals_have_wheels(X))).", True),
    ("forall(X, (is_a(X, insects) -> have_wheels_or_insects_have_fur(X))).", True),
    # ... more new logical statements follow ...
    # Additional test cases to ensure robustness and correctness of the translation logic
    ("All men are mortal. Socrates is a man. Therefore, Socrates is mortal.", True),
    ("No birds have fur. Tweety is a bird. Therefore, Tweety does not have fur.", True),
    ("Some mammals are bipedal. A kangaroo is a mammal. Therefore, a kangaroo is bipedal.", True),
    ("If a vehicle has wheels, it can move. A bicycle has wheels. Therefore, a bicycle can move.", True),
    ("All insects have six legs. A spider is an insect. Therefore, a spider has six legs.", False),  # Spiders are not insects
    ("If an animal is a bird, it can fly. A penguin is a bird. Therefore, a penguin can fly.", False),  # Penguins cannot fly
    # ... more test cases to be added ...
    ("All humans are mortal.", True, "mortal(X) :- human(X)."),
    ("Some birds can fly.", True, "can_fly(X) :- bird(X), not(penguin(X))."),
    ("No dogs have wings.", True, ":- dog(X), has_wings(X)."),
    ("All mammals have fur.", False, "has_fur(X) :- mammal(X), not(whale(X))."),
    ("Some cars can fly.", False, "can_fly(X) :- car(X), has_wings(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a creature is a mammal, it is not a bird. A platypus is a mammal. Therefore, a platypus is not a bird.", True, "not_bird(X) :- mammal(X), not(bird(X))."),
    ("Every prime number is odd. Two is a prime number. Therefore, two is odd.", False, "odd(X) :- prime(X), not(X = 2)."),
    ("If an animal is a cat, it is a mammal. A lion is a cat. Therefore, a lion is a mammal.", True, "mammal(X) :- cat(X)."),
    ("All citrus fruits are sour. An orange is a citrus fruit. Therefore, an orange is sour.", True, "sour(X) :- citrus(X)."),
    ("If a number is even, it is divisible by two. Four is an even number. Therefore, four is divisible by two.", True, "divisible_by_two(X) :- even(X)."),
    ("A square has four equal sides. A rectangle does not have four equal sides. Therefore, a rectangle is not a square.", True, "not_square(X) :- rectangle(X), not(equal_sides(X, 4))."),
    ("All bachelors are unmarried. John is a bachelor. Therefore, John is unmarried.", True, "unmarried(X) :- bachelor(X)."),
    ("Some birds cannot fly. An ostrich is a bird. Therefore, an ostrich cannot fly.", True, "cannot_fly(X) :- bird(X), ostrich(X)."),
    ("If an animal is a mammal, it breathes air. A whale is a mammal. Therefore, a whale breathes air.", True, "breathes_air(X) :- mammal(X)."),
    ("All humans are mortal. Plato is human. Therefore, Plato is mortal.", True, "mortal(X) :- human(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a number is divisible by 10, it ends with a 0. Twenty is divisible by 10. Therefore, twenty ends with a 0.", True, "ends_with_zero(X) :- divisible_by_ten(X)."),
    ("All birds have beaks. A sparrow is a bird. Therefore, a sparrow has a beak.", True, "has_beak(X) :- bird(X)."),
    ("If an animal is an amphibian, it can live both on land and in water. A frog is an amphibian. Therefore, a frog can live both on land and in water.", True, "lives_on_land_and_water(X) :- amphibian(X)."),
    ("Every prime number greater than 2 is odd. Five is a prime number greater than 2. Therefore, five is odd.", True, "odd(X) :- prime(X), greater_than_two(X)."),
    ("If a shape has four equal sides, it is a square. A rhombus has four equal sides. Therefore, a rhombus is a square.", False, "square(X) :- shape(X), has_four_equal_sides(X)."),
    ("A rectangle has four sides. If a shape is a rectangle, then it has four sides.", True, "has_four_sides(X) :- rectangle(X)."),
    ("All roses are flowers. If a plant is a rose, then it is a flower.", True, "flower(X) :- rose(X)."),
    ("If an animal is a mammal, it breathes air. A whale is a mammal. Therefore, a whale breathes air.", True, "breathes_air(X) :- mammal(X)."),
    ("All humans are mortal. Plato is human. Therefore, Plato is mortal.", True, "mortal(X) :- human(X)."),
    ("If a number is divisible by 3, it is odd. Nine is divisible by 3. Therefore, nine is odd.", True, "odd(X) :- divisible_by_three(X)."),
    ("All planets orbit the sun. Venus is a planet. Therefore, Venus orbits the sun.", True, "orbits_sun(X) :- planet(X)."),
    ("If an animal is a fish, it lives in water. A goldfish is a fish. Therefore, a goldfish lives in water.", True, "lives_in_water(X) :- fish(X)."),
    ("Every square has four sides. A rectangle has four sides. Therefore, a rectangle is a square.", False, "square(X) :- rectangle(X), has_four_sides(X)."),
    ("If a creature is a bird, it can fly. An emu is a bird. Therefore, an emu can fly.", False, "can_fly(X) :- bird(X), not(emu(X))."),
    ("If a number is divisible by 5, it ends with 0 or 5. Ten is divisible by 5. Therefore, ten ends with 0 or 5.", True, "ends_with_zero_or_five(X) :- divisible_by_five(X)."),
    ("All flowers need water to survive. A rose is a flower. Therefore, a rose needs water to survive.", True, "needs_water_to_survive(X) :- flower(X)."),
    ("If an animal is a bear, it is a mammal. A grizzly is a bear. Therefore, a grizzly is a mammal.", True, "mammal(X) :- bear(X)."),
    ("Every even number is divisible by 2. Six is an even number. Therefore, six is divisible by 2.", True, "divisible_by_two(X) :- even(X)."),
    ("If a food is a vegetable, it is healthy. A potato is a vegetable. Therefore, a potato is healthy.", True, "healthy(X) :- vegetable(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a creature is a mammal, it has hair. A whale is a mammal. Therefore, a whale has hair.", True, "has_hair(X) :- mammal(X), not(whale(X))."),
    ("All prime numbers are odd. Two is a prime number. Therefore, two is odd.", False, "odd(X) :- prime(X), not(X = 2)."),
    ("If an animal is a bird, it can fly. An ostrich is a bird. Therefore, an ostrich can fly.", False, "can_fly(X) :- bird(X), not(ostrich(X))."),
    ("Every square has four equal sides. Therefore, if something has four equal sides, it is a square.", False, "square(X) :- has_four_equal_sides(X), not(X = square)."),
    ("If a number is divisible by four, it is even. Sixteen is divisible by four. Therefore, sixteen is even.", True, "even(X) :- divisible_by_four(X)."),
    ("All flowers produce nectar. A daisy is a flower. Therefore, a daisy produces nectar.", True, "produces_nectar(X) :- flower(X)."),
    ("If a food is a fruit, it is sweet. A lemon is a fruit. Therefore, a lemon is sweet.", False, "sweet(X) :- fruit(X), not(lemon(X))."),
    ("All bachelors are unmarried men. John is unmarried. Therefore, John is a bachelor.", False, "bachelor(X) :- unmarried(X), man(X), not(john(X))."),
    ("If an object is a circle, it is round. A plate is round. Therefore, a plate is a circle.", False, "circle(X) :- round(X), not(plate(X))."),
    ("Every insect has six legs. A spider has eight legs. Therefore, a spider is not an insect.", True, "not_insect(X) :- has_eight_legs(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a number is divisible by 4, it is even. Eight is divisible by 4. Therefore, eight is even.", True, "even(X) :- divisible_by_four(X)."),
    ("All citrus fruits are sour. A lemon is a citrus fruit. Therefore, a lemon is sour.", True, "sour(X) :- citrus(X)."),
    ("If a shape has four sides, it is a quadrilateral. A square has four sides. Therefore, a square is a quadrilateral.", True, "quadrilateral(X) :- has_four_sides(X)."),
    ("Every mammal has a brain. A dolphin is a mammal. Therefore, a dolphin has a brain.", True, "has_brain(X) :- mammal(X)."),
    ("If an animal is a bird, it has feathers. A penguin is a bird. Therefore, a penguin has feathers.", True, "has_feathers(X) :- bird(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a creature is a mammal, it has hair. A bear is a mammal. Therefore, a bear has hair.", True, "has_hair(X) :- mammal(X), not(bear(X))."),
    ("All prime numbers are odd. Three is a prime number. Therefore, three is odd.", True, "odd(X) :- prime(X), not(X = 2)."),
    ("If an animal is a bird, it can fly. A chicken is a bird. Therefore, a chicken can fly.", False, "can_fly(X) :- bird(X), not(chicken(X))."),
    ("Every square has four equal sides. Therefore, if something has four equal sides, it is a square.", False, "square(X) :- has_four_equal_sides(X), not(X = square)."),
    ("If a number is divisible by four, it is even. Thirty-two is divisible by four. Therefore, thirty-two is even.", True, "even(X) :- divisible_by_four(X)."),
    ("All flowers produce nectar. A sunflower is a flower. Therefore, a sunflower produces nectar.", True, "produces_nectar(X) :- flower(X)."),
    ("If a food is a vegetable, it contains fiber. A carrot is a vegetable. Therefore, a carrot contains fiber.", True, "contains_fiber(X) :- vegetable(X)."),
    ("All bachelors are unmarried men. Steve is unmarried. Therefore, Steve is a bachelor.", False, "bachelor(X) :- unmarried(X), man(X), not(steve(X))."),
    ("If an object is a circle, it is round. A coin is round. Therefore, a coin is a circle.", False, "circle(X) :- round(X), not(coin(X))."),
    ("Every insect has six legs. A beetle has six legs. Therefore, a beetle is an insect.", True, "insect(X) :- has_six_legs(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a mammal is aquatic, it can swim. A dolphin is an aquatic mammal. Therefore, a dolphin can swim.", True, "can_swim(X) :- aquatic_mammal(X)."),
    ("All prime numbers are odd. Five is a prime number. Therefore, five is odd.", True, "odd(X) :- prime(X), not(X = 2)."),
    ("If an animal is a mammal, it has hair. A hippopotamus is a mammal. Therefore, a hippopotamus has hair.", True, "has_hair(X) :- mammal(X), not(hippopotamus(X))."),
    ("Every square has four equal sides. Therefore, if something has four equal sides, it is a square.", False, "square(X) :- has_four_equal_sides(X), not(X = rectangle)."),
    ("If a number is divisible by six, it is even. Twelve is divisible by six. Therefore, twelve is even.", True, "even(X) :- divisible_by_six(X)."),
    ("All flowers produce pollen. A tulip is a flower. Therefore, a tulip produces pollen.", True, "produces_pollen(X) :- flower(X)."),
    ("If a food is a vegetable, it contains fiber. A carrot is a vegetable. Therefore, a carrot contains fiber.", True, "contains_fiber(X) :- vegetable(X)."),
    ("All bachelors are unmarried men. Bob is unmarried. Therefore, Bob is a bachelor.", False, "bachelor(X) :- unmarried(X), man(X), not(bob(X))."),
    ("If an object is a sphere, it is round. A basketball is a sphere. Therefore, a basketball is round.", True, "round(X) :- sphere(X)."),
    ("Every insect has six legs. A butterfly has six legs. Therefore, a butterfly is an insect.", True, "insect(X) :- has_six_legs(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a number is divisible by 2, it is even. Four is divisible by 2. Therefore, four is even.", True, "even(X) :- divisible_by_two(X)."),
    ("All mammals are vertebrates. A cow is a mammal. Therefore, a cow is a vertebrate.", True, "vertebrate(X) :- mammal(X)."),
    ("If an animal is a fish, it lives in water. A salmon is a fish. Therefore, a salmon lives in water.", True, "lives_in_water(X) :- fish(X)."),
    ("Every bird has feathers. A robin is a bird. Therefore, a robin has feathers.", True, "has_feathers(X) :- bird(X)."),
    ("If a plant is a tree, it has roots. An oak is a tree. Therefore, an oak has roots.", True, "has_roots(X) :- tree(X)."),
    ("All citizens have the right to vote. Tom is a citizen. Therefore, Tom has the right to vote.", True, "has_right_to_vote(X) :- citizen(X)."),
    ("If a shape is a square, it has four sides. This shape has four sides. Therefore, this shape is a square.", False, "square(X) :- has_four_sides(X), not(rectangle(X))."),
    ("Every prime number greater than two is odd. Seven is a prime number greater than two. Therefore, seven is odd.", True, "odd(X) :- prime(X), greater_than_two(X)."),
    ("If an object is a cube, it has six faces. A dice is a cube. Therefore, a dice has six faces.", True, "has_six_faces(X) :- cube(X)."),
    ("All flowers need sunlight to grow. A sunflower is a flower. Therefore, a sunflower needs sunlight to grow.", True, "needs_sunlight_to_grow(X) :- flower(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    # Adding new logical statements to expand the dataset towards 1000 entries
    ("If a number is divisible by 8, it is even. Sixteen is divisible by 8. Therefore, sixteen is even.", True, "even(X) :- divisible_by_eight(X)."),
    ("All mammals have a vertebral column. A horse is a mammal. Therefore, a horse has a vertebral column.", True, "vertebral_column(X) :- mammal(X)."),
    ("If an animal is a bird, it has two legs. A sparrow is a bird. Therefore, a sparrow has two legs.", True, "two_legs(X) :- bird(X)."),
    ("Every prime number greater than two is odd. Nineteen is a prime number greater than two. Therefore, nineteen is odd.", True, "odd(X) :- prime(X), greater_than_two(X)."),
    ("If a shape is a polygon, it has at least three sides. A triangle is a polygon. Therefore, a triangle has at least three sides.", True, "at_least_three_sides(X) :- polygon(X)."),
    ("All citrus fruits have vitamin C. A grapefruit is a citrus fruit. Therefore, a grapefruit has vitamin C.", True, "vitamin_c(X) :- citrus_fruit(X)."),
    ("If a vehicle is an automobile, it has an engine. A car is an automobile. Therefore, a car has an engine.", True, "engine(X) :- automobile(X)."),
    ("Every insect has an exoskeleton. A beetle is an insect. Therefore, a beetle has an exoskeleton.", True, "exoskeleton(X) :- insect(X)."),
    ("If a liquid is an acid, it has a pH less than 7. Vinegar is an acid. Therefore, vinegar has a pH less than 7.", True, "ph_less_than_seven(X) :- acid(X)."),
    ("All flowering plants have stems. A rose is a flowering plant. Therefore, a rose has a stem.", True, "stem(X) :- flowering_plant(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a number is divisible by 9, it is odd. Eighteen is divisible by 9. Therefore, eighteen is odd.", False, "odd(X) :- divisible_by_nine(X), not(even(X))."),
    ("All mammals have a brain. A bat is a mammal. Therefore, a bat has a brain.", True, "has_brain(X) :- mammal(X)."),
    ("If a vehicle has an engine, it can move. A car has an engine. Therefore, a car can move.", True, "can_move(X) :- vehicle(X), has_engine(X)."),
    ("Every bird has wings. A robin is a bird. Therefore, a robin has wings.", True, "has_wings(X) :- bird(X)."),
    ("If a plant is a tree, it has leaves. An oak is a tree. Therefore, an oak has leaves.", True, "has_leaves(X) :- tree(X)."),
    ("All citizens have the right to vote. Alice is a citizen. Therefore, Alice has the right to vote.", True, "has_right_to_vote(X) :- citizen(X)."),
    ("If a shape is a square, it has four sides. This shape has four sides. Therefore, this shape is a square.", False, "square(X) :- has_four_sides(X), not(all_shapes_with_four_sides_are_squares(X))."),
    ("Every prime number greater than two is odd. Thirteen is a prime number greater than two. Therefore, thirteen is odd.", True, "odd(X) :- prime(X), greater_than_two(X)."),
    ("If an object is a cube, it has six faces. A dice is a cube. Therefore, a dice has six faces.", True, "has_six_faces(X) :- cube(X)."),
    ("All flowers need sunlight to grow. A daisy is a flower. Therefore, a daisy needs sunlight to grow.", True, "needs_sunlight_to_grow(X) :- flower(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
    ("If a number is divisible by 10, it is even. Twenty is divisible by 10. Therefore, twenty is even.", True, "even(X) :- divisible_by_ten(X)."),
    ("All mammals have hair. A bear is a mammal. Therefore, a bear has hair.", True, "has_hair(X) :- mammal(X)."),
    ("If a vehicle has wheels, it can move. A bicycle has wheels. Therefore, a bicycle can move.", True, "can_move(X) :- has_wheels(X)."),
    ("Every bird has feathers. A sparrow is a bird. Therefore, a sparrow has feathers.", True, "has_feathers(X) :- bird(X)."),
    ("If a plant is a tree, it has leaves. An oak is a tree. Therefore, an oak has leaves.", True, "has_leaves(X) :- tree(X)."),
    ("All citizens have the right to vote. Alice is a citizen. Therefore, Alice has the right to vote.", True, "right_to_vote(X) :- citizen(X)."),
    ("If a shape is a square, it has four sides. This shape has four sides. Therefore, this shape is a square.", False, "square(X) :- has_four_sides(X), not(all_shapes_with_four_sides_are_squares(X))."),
    ("Every prime number greater than two is odd. Seventeen is a prime number greater than two. Therefore, seventeen is odd.", True, "odd(X) :- prime(X), greater_than_two(X)."),
    ("If an object is a cube, it has six faces. A dice is a cube. Therefore, a dice has six faces.", True, "has_six_faces(X) :- cube(X)."),
    ("All flowers need sunlight to grow. A daisy is a flower. Therefore, a daisy needs sunlight to grow.", True, "needs_sunlight_to_grow(X) :- flower(X)."),
    # ... more logical statements will be added here to reach a total of 1000 ...
]

class TestLogicalStatements(unittest.TestCase):

    def test_statement_1(self):
        statement, expected = logical_statements[0]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_2(self):
        statement, expected = logical_statements[1]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_3(self):
        statement, expected = logical_statements[2]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_4(self):
        statement, expected = logical_statements[3]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_5(self):
        statement, expected = logical_statements[4]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_6(self):
        statement, expected = logical_statements[5]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_7(self):
        statement, expected = logical_statements[6]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_8(self):
        statement, expected = logical_statements[7]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_9(self):
        statement, expected = logical_statements[8]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    def test_statement_10(self):
        statement, expected = logical_statements[9]
        self.assertEqual(parse_and_evaluate(statement), expected, f"Statement failed: {statement}")

    # ... [additional test methods will be added here following the same pattern]

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
        x = Variable('x')
        return ForAll(x, Implies(Predicate(subject)(x), Predicate(predicate)(x)))

    # Example translation for a conditional statement
    if "If" in statement and "then" in statement:
        antecedent, consequent = statement.split(" then ")
        antecedent = antecedent.replace("If ", "")
        return Implies(Predicate(antecedent), Predicate(consequent))

    # Example translation for an existential quantification statement
    if "Some" in statement and "are" in statement:
        subject, predicate = statement.split(" are ")
        subject = subject.replace("Some ", "")
        x = Variable('x')
        return Exists(x, And(Predicate(subject)(x), Predicate(predicate)(x)))

    # Example translation for a conjunction statement
    if " and " in statement:
        parts = statement.split(" and ")
        return And([Predicate(part) for part in parts])

    # Example translation for a disjunction statement
    if " or " in statement:
        parts = statement.split(" or ")
        return Or([Predicate(part) for part in parts])

    # Example translation for a negation statement
    if "It is not the case that" in statement:
        statement = statement.replace("It is not the case that ", "")
        return Not(Predicate(statement))

    # Example translation for a biconditional statement
    if " if and only if " in statement:
        parts = statement.split(" if and only if ")
        return Iff(Predicate(parts[0]), Predicate(parts[1]))

    # Placeholder for unrecognized statements
    return None

def evaluate_formula(formula):
    # Expanded domain and interpretation to cover all entities and predicates
    domain = {'Socrates', 'Plato', 'Aristotle', 'men', 'mortal', 'birds', 'dogs', 'animals', 'mammals', 'carnivores', 'lions', 'students', 'vehicles', 'insects'}
    interpretation = {
        'Human': lambda x: x in {'Socrates', 'Plato', 'Aristotle'},
        'Mortal': lambda x: x in {'Socrates', 'Plato', 'Aristotle', 'men'},
        'Bird': lambda x: x in {'birds'},
        'Dog': lambda x: x in {'dogs'},
        'Animal': lambda x: x in {'dogs', 'animals', 'mammals'},
        'Mammal': lambda x: x in {'mammals', 'lions'},
        'Carnivore': lambda x: x in {'carnivores', 'lions'},
        'Lion': lambda x: x in {'lions'},
        'Student': lambda x: x in {'students'},
        'Vehicle': lambda x: x in {'vehicles'},
        'Insect': lambda x: x in {'insects'},
        'can_fly': lambda x: x in {'birds'},  # Simplified example, real logic may vary
        'have_fur': lambda x: x in {'dogs', 'mammals'},
        'bipedal': lambda x: x in {'humans', 'birds'},  # Assuming 'humans' is part of the domain
        'have_wheels': lambda x: x in {'vehicles'},
        'have_six_legs': lambda x: x in {'insects'},
        'have_wings': lambda x: x in {'birds', 'insects'},
        # ... additional predicates and their interpretations ...
    }
    # Create the model with the expanded domain and interpretation
    model = Model(domain=domain, interpretation=interpretation)
    # Evaluate the formula using the model
    return model.satisfies(formula)
