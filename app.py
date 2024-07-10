import streamlit as st
import pdfplumber
import pandas as pd
import json
import tempfile
from openai import OpenAI
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

global_ship_name = None

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)
GPT_MODEL = "gpt-3.5-turbo-16k"

# Convert PDF tables to JSON format
def pdf_to_json_chunks(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        tables = []
        for page_number, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table_number, table in enumerate(page_tables):
                df = pd.DataFrame(table)
                tables.append({
                    "page": page_number + 1,
                    "table_number": table_number + 1,
                    "table": df.to_dict(orient="records")
                })

    with open("basic_json.json", "w", encoding="utf-8") as json_file:
        json.dump(tables, json_file, indent=4)
    return tables

# Process input JSON data using OpenAI to generate structured JSON
def process_with_openai(input_data, append_json_list):
    with open("json_to_json_prompt.txt", "r", encoding="utf-8") as file:
        base_prompt = file.read()

    prompt = f"{base_prompt}\n\n---- Input Data ----\n{json.dumps(input_data, indent=4)}\n\n---- Output JSON ----"

    messages = [
        {"role": "system", "content": "You are an intelligent data converter."},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        max_tokens=10000,
        temperature=1,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    output_message = response.choices[0].message.content
    append_json_list.append(json.loads(output_message))
    return json.loads(output_message)

# Class to handle Neo4j operations
class Neo4jHandler:
    def __init__(self, uri, user, password):
        # Initialize Neo4jHandler with Neo4j connection details
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        # Close the Neo4j connection
        self.driver.close()
    
    def create_document(self, document_name, document_version):
        # Create a document node in Neo4j
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_document, document_name, document_version)
    
    def create_category(self, document_name, category):
        # Create a category node and link it to a document node in Neo4j
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_category, document_name, category)
    
    def create_question(self, category, question_number, question, answer):
        # Create a question node and link it to a category node in Neo4j
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_question, category, question_number, question, answer)
    
    def create_ship(self, ship_name):
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_ship, ship_name)
    
    @staticmethod
    def _create_and_return_document(tx, document_name, document_version):
        # Create and return a document node
        query = (
            "MERGE (d:Document {name: $document_name, version: $document_version}) "
            "RETURN d"
        )
        result = tx.run(query, document_name=document_name, document_version=document_version)
        return result.single()
    
    @staticmethod
    def _create_and_return_category(tx, document_name, category):
        # Create and return a category node, linking it to a document
        query = (
            "MATCH (d:Document {name: $document_name}) "
            "MERGE (c:Category {name: $category}) "
            "MERGE (d)-[:HAS_CATEGORY]->(c) "
            "RETURN c"
        )
        result = tx.run(query, document_name=document_name, category=category)
        return result.single()
    
    @staticmethod
    def _create_and_return_question(tx, category, question_number, question, answer):
        # Create and return a question node, linking it to a category
        query = (
            "MATCH (c:Category {name: $category}) "
            "CREATE (q:Question {number: $question_number, text: $question, answer: $answer}) "
            "MERGE (c)-[:HAS_QUESTION]->(q) "
            "RETURN q"
        )
        result = tx.run(query, category=category, question_number=question_number, question=question, answer=answer)
        return result.single()

    @staticmethod
    def _create_and_return_ship(tx, ship_name):
        # Create and return a ship node
        query = (
            "MERGE (s:Ship {name: $ship_name}) "
            "RETURN s"
        )
        result = tx.run(query, ship_name=ship_name)
        return result.single()
    
# Format answer to JSON if it is a dictionary
def format_answer(answer):
    return json.dumps(answer) if isinstance(answer, dict) else answer

# Populate Neo4j database with structured JSON data
def populate_data(json_data):
    global global_ship_name
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "yatharth2004"
    
    handler = Neo4jHandler(uri, user, password)
    
    try:
        document_name = json_data["Document Name"]
        document_version = json_data["Document Version"]

        for category, questions in json_data["Categories"].items():
            for question in questions:
                if question["Question Number"] == "1.2":
                    new_ship_name = question["Answer"]
                    if new_ship_name:
                        global_ship_name = new_ship_name

        if not global_ship_name:
            raise ValueError("Ship name not found in JSON.")

        handler.create_document(document_name, document_version)
        handler.create_ship(global_ship_name)

        for category, questions in json_data["Categories"].items():
            handler.create_category(document_name, category)
            for question in questions:
                question_number = question["Question Number"]
                question_text = question["Question"]
                answer = format_answer(question["Answer"])
                handler.create_question(category, question_number, question_text, answer)

        # Link questions and categories to the ship node
            with handler.driver.session() as session:
                session.run(
                    "MATCH (s:Ship {name: $ship_name}) "
                    "MATCH (d:Document {name: $document_name}) "
                    "MERGE (s)-[:HAS_DOCUMENT]->(d)",
                    ship_name=global_ship_name, document_name=document_name
                )

                for category in json_data["Categories"]:
                    session.run(
                        "MATCH (s:Ship {name: $ship_name}) "
                        "MATCH (c:Category {name: $category}) "
                        "MERGE (s)-[:HAS_CATEGORY]->(c)",
                        ship_name=global_ship_name, category=category
                    )

    finally:
        handler.close()

# Run a query on the Neo4j database to retrieve ship names
def run_ships_query():
    class Neo4jQueryRunner:
        def __init__(self, uri, user, password):
            self.driver = GraphDatabase.driver(uri, auth=(user, password))

        def close(self):
            # Close the Neo4j connection
            self.driver.close()

        def run_query(self, query):
            # Run a Cypher query on the Neo4j database
            with self.driver.session() as session:
                result = session.run(query)
                return [record["q.answer"] for record in result]

    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "yatharth2004"

    query_runner = Neo4jQueryRunner(uri, user, password)
    query = 'MATCH (q:Question {number: "1.2"}) RETURN q.answer'
    results = query_runner.run_query(query)
    query_runner.close()
    return results

# Main function to run the Streamlit app
def main():
    st.title("PDF to JSON Table Extractor and Neo4j Populator")

    # Display results from ships query in an expander
    with st.expander("Available Ship names in database"):
        results = run_ships_query()
        for result in results:
            st.write(result)

    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        temp_files = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_files.append(tmp_file.name)

        if st.button("Convert to JSON and Populate Neo4j"):
            st.write("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # Add space after the button
            all_converted_data = []

            for tmp_file_path in temp_files:
                with st.spinner('Creating Basic JSON...'):
                    tables = pdf_to_json_chunks(tmp_file_path)
                    st.markdown("<h5 style='color: #fae7b5;'>Basic JSON has been created ✓</h5>", unsafe_allow_html=True)
                    with st.expander("View Basic JSON"):
                        st.json(tables)

                chunk_size = 5  # Number of tables per chunk
                converted_data = []

                with st.spinner('Structuring basic JSON using OpenAI...'):
                    for i in range(0, len(tables), chunk_size):
                        chunk = tables[i:i + chunk_size]
                        for table in chunk:
                            process_with_openai(table, converted_data)

                st.markdown("<h5 style='color: #fae7b5;'>Structured JSON has been created ✓</h5>", unsafe_allow_html=True)

                with st.expander("View Structured JSON"):
                    st.json(converted_data)

                with st.spinner('Populating Neo4j database...'):
                    for data in converted_data:
                        populate_data(data)

                st.markdown("<h5 style='color: #fae7b5;'>Neo4j database has been populated ✓</h5>", unsafe_allow_html=True)
                all_converted_data.extend(converted_data)

            st.success(f"Conversion and population successful for ship {global_ship_name}")

            with open("structured_json.json", "w", encoding="utf-8") as json_file:
                json.dump(all_converted_data, json_file, indent=4)

if __name__ == "__main__":
    main()