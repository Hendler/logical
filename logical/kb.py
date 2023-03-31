import random
import re
import numpy as np
from nltk import pos_tag
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import psycopg2
import spacy


class NLtoLogic:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")
        self.centroids = None
        self.centroid_labels = None
        self.conn = psycopg2.connect("dbname=your_database user=your_user password=your_password")
        self.nlp = spacy.load("en_core_web_sm")

    def split_sentences(self, text):
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        return sentences

    def generate_embeddings(self, text):
        sentences = self.split_sentences(text)
        embeddings = self.model.encode(sentences)
        return embeddings

    def cluster_embeddings(self, embeddings, n_clusters):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(embeddings)
        self.centroids = kmeans.cluster_centers_

    def assign_centroid_ids(self, embeddings):
        distances = cosine_similarity(embeddings, self.centroids)
        centroid_ids = np.argmax(distances, axis=1)
        return centroid_ids

    def centroid_to_label(self, centroid):
        with self.conn.cursor() as cur:
            cur.execute("SELECT label FROM centroid_labels WHERE id = %s", (centroid,))
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                return None

    def get_pos_tag(self, word):
        pos = pos_tag([word])[0][1]
        if pos.startswith("N"):
            return "NOUN"
        elif pos.startswith("V"):
            return "VERB"
        else:
            return None

    def add_text_to_knowledge_base(self, text):
        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            # Extract and store facts and rules from the paragraph
            # This can be done using the existing methods to process natural language text
            pass

    def regenerate_centroids(self):
        # Regenerate centroids based on the current knowledge base
        # This can be done using the existing methods to process natural language text
        pass

    def regenerate_centroid_labels(self):
        # Regenerate centroid labels based on the current centroids
        # This can be done using the existing methods to process natural language text
        pass

    def check_truthiness(self, sentence):
        similar_statements, contradictions = self.find_related_statements(sentence)
        total_statements = len(similar_statements) + len(contradictions)
        if total_statements == 0:
            return 0
        truthiness = len(contradictions) / total_statements
        return truthiness

    def find_related_statements(self, sentence):
        centroids = self.extract_centroids(sentence)
        similar_statements = []
        contradictions = []

        for centroid in centroids:
            label = self.centroid_to_label(centroid)
            pos = self.get_pos_tag(label)

            if pos == "NOUN" or pos == "VERB":
                with self.conn.cursor() as cur:
                    cur.execute("SELECT subject, predicate, object FROM facts")
                    rows = cur.fetchall()

                    for row in rows:
                        if label in row:
                            similar_statement = " ".join(row)
                            if self.are_contradictory(similar_statement, sentence):
                                contradictions.append(similar_statement)
                            else:
                                similar_statements.append(similar_statement)
        return similar_statements, contradictions

    def find_random_contradictions(self, n=10):
        with self.conn.cursor() as cur:
            cur.execute("SELECT subject, predicate, object FROM facts")
            rows = cur.fetchall()

        random.shuffle(rows)
        contradictions = []

        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                statement1 = " ".join(rows[i])
                statement2 = " ".join(rows[j])
                if self.are_contradictory(statement1, statement2):
                    contradictions.append((statement1, statement2))
                    if len(contradictions) == n:
                        break
            if len(contradictions) == n:
                break

        return contradictions