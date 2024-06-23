# Instructions
1. Begin by installing all the necessary libraries with ```pip install -r requirements.txt```
2. Create a file named ```.env``` in the cloned repository and  type ```OPENAI_API_KEY="Your api key"```
3. Download and install neo4j database (https://neo4j.com/download/)
4. Create a project and set credentials for the same
5. Update the credentials in the codebase in ```app.py```
   ```
   uri = "bolt://localhost:7687"  # Update with your Neo4j URI
   user = "neo4j"  # Update with your Neo4j username
   password = "yatharth2004"  # Update with your Neo4j password```
6. Once the installation is complete, you can locally execute it by entering ```streamlit run app.py```
