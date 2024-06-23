# Instructions
1. Clone the repository to your local computer using ```git clone https://github.com/CipJusCodin/7Dliving-pdf-to-neo4j-tool.git```
2. Begin by installing all the necessary libraries with ```pip install -r requirements.txt```
3. Create a file named ```.env``` in the cloned repository and  type ```OPENAI_API_KEY="Your api key"```
4. Download and install neo4j database (https://neo4j.com/download/)
5. Create a project and set credentials for the same
6. Update the credentials in the codebase in ```app.py```
   ```
   uri = "bolt://localhost:7687"  # Update with your Neo4j URI
   user = "neo4j"  # Update with your Neo4j username
   password = "yatharth2004"  # Update with your Neo4j password
   ```
7. You can locally run the file now by entering ```streamlit run app.py```
