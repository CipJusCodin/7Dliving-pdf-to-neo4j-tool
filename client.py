import streamlit as st
from neo4j import GraphDatabase
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)
GPT_MODEL = "gpt-3.5-turbo-16k"

# Set up Neo4j connection
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "yatharth2004"
driver = GraphDatabase.driver(uri, auth=(username, password))

def get_db_schema():
    with driver.session() as session:
        # Fetch categories and questions from Neo4j
        categories_query = (
            "MATCH (c:Category)-[:HAS_QUESTION]->(q:Question) "
            "RETURN c.name AS category, collect(q.number) AS questions"
        )
        result = session.run(categories_query)
        schema_info = {record['category']: record['questions'] for record in result}
        
    return schema_info

def generate_cypher_query(natural_language_query, schema_info):
    # Generate prompt based on available categories and questions
    prompt = f"Generate a Cypher query to find the answer to '{natural_language_query}' based on the following schema:\n\n"
    for category, questions in schema_info.items():
        prompt += f"- Category: {category}\n"
        prompt += "  - Questions: " + ", ".join(questions) + "\n"
    
    messages = [
        {"role": "system", "content": "You are an intelligent Neo4j prompt generator."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model=GPT_MODEL,  
        messages=messages,
        max_tokens=1000,
        temperature=1,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    cypher_query = response.choices[0].message.content.strip()
    return cypher_query

def execute_cypher_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

def main():
    st.title("Neo4j Graph Query Interface")

    st.write("## Database Schema")
    schema_info = get_db_schema()
    st.write("Available Categories and Questions:")
    for category, questions in schema_info.items():
        st.write(f"- Category: {category}")
        st.write("  - Questions:", questions)

    user_query = st.text_input("Enter your query:")
    if user_query:
        cypher_query = generate_cypher_query(user_query, schema_info)
        st.write(f"### Generated Cypher Query:\n{cypher_query}")

        results = execute_cypher_query(cypher_query)
        st.write("### Results:")
        st.json(results)

if __name__ == "__main__":
    main()
