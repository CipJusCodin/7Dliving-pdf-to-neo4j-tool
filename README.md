# Instructions
1. Clone the repository to your local computer using ```git clone https://github.com/CipJusCodin/7Dliving-pdf-to-neo4j-tool.git```
2. Create a Python environment (optional but recommended)
3. Begin by installing all the necessary libraries with ```pip install -r requirements.txt```
4. Create a file named ```.env``` in the cloned repository and  type ```OPENAI_API_KEY="Your api key"```
5. Download and install neo4j database (https://neo4j.com/download/)
6. Create a project in neo4j and set credentials for the same
7. Update the credentials in the codebase in ```app.py``` & ```ships.py```
   ```
   uri = "bolt://localhost:7687"  # Update with your Neo4j URI
   user = "neo4j"  # Update with your Neo4j username
   password = "yatharth2004"  # Update with your Neo4j password
   ```
8. You can locally run the file now by entering ```streamlit run app.py```


# Files
1. ```json_to_json_prompt.txt``` - Contains the prompt to structure json
2. ```app.py``` - Code that converts a pdf file to a plain json using pdfplumber, restructures that json file to a more structured format using Openai API key and then stores in the neo4j database. All currently deployed on streamlit interface.
3. ```client.py``` - Fetching data from neo4j using NLP (Work in progress).
4. ```Marilena.pdf``` - Pdf used for testing 
5. ```neo4j_fetching_prompt.txt``` - Contains the prompt to generate cypher queries 
6. ```ships.py``` - Fetches the existing ship names from neo4j DB