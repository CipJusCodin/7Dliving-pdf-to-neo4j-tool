# ships.py
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = "bolt://localhost:7687"
user = "neo4j"
password = "yatharth2004"

class Neo4jQueryRunner:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query):
        with self.driver.session() as session:
            result = session.run(query)
            return [record["q.answer"] for record in result]

if __name__ == "__main__":
    query_runner = Neo4jQueryRunner(uri, user, password)
    query = 'MATCH (q:Question {number: "1.2"}) RETURN q.answer'
    results = query_runner.run_query(query)
    query_runner.close()
    print("Query Results:", results)
    # Return results if needed
