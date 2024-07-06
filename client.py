import streamlit as st
from neo4j import GraphDatabase
from openai import OpenAI
import os
from dotenv import load_dotenv
import numpy as np

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
GPT_MODEL = "gpt-3.5-turbo-16k"

uri = "neo4j://localhost:7687"
username = "neo4j"
password = "yatharth2004"
driver = GraphDatabase.driver(uri, auth=(username, password))

# Function to get embedding for a natural language query using OpenAI
def get_query_embedding(query):
    response = client.embeddings.create(input=query, model="text-embedding-ada-002")
    embedding = response.data[0].embedding
    return embedding

# Function to calculate cosine similarity between two vectors
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Function to find nodes in Neo4j with embeddings similar to a given query embedding
def find_similar_nodes(query_embedding, threshold=0.2):
    with driver.session() as session:
        # Query all nodes with embeddings
        nodes = session.run("MATCH (n) WHERE n.embedding IS NOT NULL RETURN n, n.embedding AS embedding").data()
        similar_nodes = []
        for node in nodes:
            embedding = node['embedding']
            similarity = cosine_similarity(query_embedding, embedding)
            if similarity > threshold:
                similar_nodes.append((node['n'], similarity))
    return similar_nodes

# Function to generate Cypher queries based on a natural language query
def generate_cypher_query(natural_language_query):
    query_embedding = get_query_embedding(natural_language_query)
    similar_nodes = find_similar_nodes(query_embedding)

    if not similar_nodes:
        return None  

    cypher_queries = []
    for index, (node, similarity) in enumerate(similar_nodes, start=1):
        question_text = node['text'] 
        cypher_query = (
            f"{index}) MATCH (c:Category)-[:HAS_QUESTION]->(q:Question) "
            f"WHERE q.text = \"{question_text}\" "
            "RETURN q.answer"
        )
        cypher_queries.append((cypher_query, similarity))

    return cypher_queries

# Function to execute a Cypher query against Neo4j database
def execute_cypher_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

# Function to retrieve the schema of the Neo4j database
def get_db_schema():
    with driver.session() as session:
        categories_query = (
            "MATCH (c:Category)-[:HAS_QUESTION]->(q:Question) "
            "RETURN c.name AS category, collect(q.number) AS questions"
        )
        result = session.run(categories_query)
        schema_info = {record['category']: record['questions'] for record in result}
        
    return schema_info

# Main function to run the Streamlit application
def main():
    st.title("Neo4j Graph Query Interface")

    user_query = st.text_input("Enter your query:")
    if user_query:
        cypher_query = generate_cypher_query(user_query)
        if cypher_query is None:
            st.write("No results found.")
        else:
            st.write(f"### Generated Cypher Query:\n{cypher_query}")

            results = execute_cypher_query(cypher_query)
            if not results:
                st.write("### Results:")
                st.write("No result found.")
            else:
                st.write("### Results:")
                st.json(results)

if __name__ == "__main__":
    main()
