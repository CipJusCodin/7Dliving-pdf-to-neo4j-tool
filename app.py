import streamlit as st
import pdfplumber
import pandas as pd
import json
import tempfile
from openai import OpenAI
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)
GPT_MODEL = "gpt-3.5-turbo-16k"

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

class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_document(self, document_name, document_version):
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_document, document_name, document_version)
    
    def create_category(self, document_name, category):
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_category, document_name, category)
    
    def create_question(self, category, question_number, question, answer):
        with self.driver.session() as session:
            session.write_transaction(self._create_and_return_question, category, question_number, question, answer)
    
    @staticmethod
    def _create_and_return_document(tx, document_name, document_version):
        query = (
            "MERGE (d:Document {name: $document_name, version: $document_version}) "
            "RETURN d"
        )
        result = tx.run(query, document_name=document_name, document_version=document_version)
        return result.single()
    
    @staticmethod
    def _create_and_return_category(tx, document_name, category):
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
        query = (
            "MATCH (c:Category {name: $category}) "
            "CREATE (q:Question {number: $question_number, text: $question, answer: $answer}) "
            "MERGE (c)-[:HAS_QUESTION]->(q) "
            "RETURN q"
        )
        result = tx.run(query, category=category, question_number=question_number, question=question, answer=answer)
        return result.single()

def format_answer(answer):
    if isinstance(answer, dict):
        return json.dumps(answer)
    return answer

def populate_data(json_data):
    uri = "bolt://localhost:7687"  # Update with your Neo4j URI
    user = "neo4j"  # Update with your Neo4j username
    password = "yatharth2004"  # Update with your Neo4j password
    
    handler = Neo4jHandler(uri, user, password)
    
    try:
        document_name = json_data["Document Name"]
        document_version = json_data["Document Version"]
        handler.create_document(document_name, document_version)

        for category, questions in json_data["Categories"].items():
            handler.create_category(document_name, category)
            for question in questions:
                question_number = question["Question Number"]
                question_text = question["Question"]
                answer = format_answer(question["Answer"])
                handler.create_question(category, question_number, question_text, answer)
    finally:
        handler.close()

def main():
    st.title("PDF to JSON Table Extractor and Neo4j Populator")

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

                chunk_size = 5  # Number of tables per chunk
                converted_data = []

                with st.spinner('Structuring basic JSON using OpenAI...'):
                    for i in range(0, len(tables), chunk_size):
                        chunk = tables[i:i + chunk_size]
                        for table in chunk:
                            process_with_openai(table, converted_data)

                st.markdown("<h5 style='color: #fae7b5;'>Structured JSON has been created ✓</h5>", unsafe_allow_html=True)
                with st.spinner('Populating Neo4j database...'):
                    for data in converted_data:
                        populate_data(data)

                st.markdown("<h5 style='color: #fae7b5;'>Neo4j database has been populated ✓</h5>", unsafe_allow_html=True)
                all_converted_data.extend(converted_data)

            st.success("Conversion and population successful!")

            with open("structured_json.json", "w", encoding="utf-8") as json_file:
                json.dump(all_converted_data, json_file, indent=4)

if __name__ == "__main__":
    main()
