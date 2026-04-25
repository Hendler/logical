# for requirements
# rdflib==6.2.0
# from rdflib import Graph


# RDF_FILE_NAME = "myprolog.csv"
# RDF_QUERY_FILE_NAME = "queries.csv"


# def parse_owl(input_text):
#     SYSTEM_ASKING_PROMPT = """
#     Generate RDF and OWL to represent all the knowledge contained in a statement.
#     Logical connections, relationships, things, actions/verbs should be respresented.
#     """

#     ASSISTANT_ASKING_PROMPT = """
#     Please convert the following to standard RDF/OWL.\n

#     """

#     return _openai_wrapper(
#         system_message=SYSTEM_ASKING_PROMPT,
#         example_user_message=f"{ASSISTANT_ASKING_PROMPT} jane is red, jim is blue, they are the same color.",
#         example_assistant_message="same_color(X,Y) :- jane(X), jim(Y).",
#         user_message=f"{ASSISTANT_ASKING_PROMPT}{input_text}",
#     )


# def run_owl(input_text):
#     SYSTEM_ASKING_PROMPT = """
#     Given some owl, and the output of a query, you are designed to explain the result
#     """

#     ASSISTANT_ASKING_PROMPT = """
#     Please explaing why the logic is correct or incorrect, or what might be missing.  \n

#     """

#     return _openai_wrapper(
#         system_message=SYSTEM_ASKING_PROMPT,
#         example_user_message=f"{ASSISTANT_ASKING_PROMPT} jane is red, jim is blue, they are the same color.",
#         example_assistant_message="same_color(X,Y) :- jane(X), jim(Y).",
#         user_message=f"{ASSISTANT_ASKING_PROMPT}{input_text}",
#     )

# def run_rdf_parser(input_text: str):
#     # get ou
#     g = Graph()
#     g.parse('ontology.owl', format='ttl')


# def run_rdf_logic(input_text: str):
#     # get out
#     g = Graph()
#     g.parse('ontology.owl', format='ttl')
