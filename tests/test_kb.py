import unittest
from nl_to_logic import NLtoLogic

class TestNLtoLogic(unittest.TestCase):
    def setUp(self):
        self.nltologic = NLtoLogic()

    def test_find_related_statements(self):
        # Add some statements to the knowledge base
        self.nltologic.add_text_to_knowledge_base("The sky is blue. The ocean is deep.")
        self.nltologic.add_text_to_knowledge_base("The sun rises in the east. The sun sets in the west.")

        # Test find_related_statements with a related sentence
        sentence = "The sky is blue during the day."
        similar_statements, contradictions = self.nltologic.find_related_statements(sentence)

        self.assertIn("The sky is blue", similar_statements)
        self.assertNotIn("The ocean is deep", similar_statements)
        self.assertNotIn("The sun rises in the east", similar_statements)
        self.assertNotIn("The sun sets in the west", similar_statements)
        self.assertEqual(contradictions, [])

        # Test find_related_statements with a contradictory sentence
        sentence = "The sky is not blue during the day."
        similar_statements, contradictions = self.nltologic.find_related_statements(sentence)

        self.assertNotIn("The sky is blue", similar_statements)
        self.assertNotIn("The ocean is deep", similar_statements)
        self.assertNotIn("The sun rises in the east", similar_statements)
        self.assertNotIn("The sun sets in the west", similar_statements)

    def test_check_truthiness(self):
        # Add some statements to the knowledge base
        self.nltologic.add_text_to_knowledge_base("The sky is blue during the day. The sun rises in the east.")
        self.nltologic.add_text_to_knowledge_base("The sky is not blue at night. The sun sets in the west.")

        # Test check_truthiness with a definitely true statement
        sentence = "The sky is blue during the day."
        truthiness = self.nltologic.check_truthiness(sentence)
        self.assertEqual(truthiness, 0)

        # Test check_truthiness with a definitely not true statement
        sentence = "The sky is blue during the night."
        truthiness = self.nltologic.check_truthiness(sentence)
        self.assertEqual(truthiness, 1)

        # Test check_truthiness with an uncertain statement
        self.nltologic.add_text_to_knowledge_base("Some people say the sky is green during the day.")
        sentence = "The sky is green during the day."
        truthiness = self.nltologic.check_truthiness(sentence)
        self.assertGreater(truthiness, 0)
        self.assertLess(truthiness, 1)


if __name__ == '__main__':
    unittest.main()