import spacy
from neo4j import GraphDatabase

nlp = spacy.load('en_core_web_sm')

def extract_entities_and_intent(query):
    doc = nlp(query)
    entities = [ent.text for ent in doc.ents]
    # Use simple keyword matching for intent detection (for demo purposes)
    if "how many" in query.lower():
        intent = "count"
    elif "find" in query.lower() or "show" in query.lower():
        intent = "fetch"
    else:
        intent = "unknown"
    return entities, intent

# Function to map extracted entities and intent to a Cypher query
def map_to_cypher(entities, intent):
    if intent == "count":
        cypher_query = f"MATCH (n:{entities[0]}) RETURN count(n)"
    elif intent == "fetch":
        cypher_query = f"MATCH (n:{entities[0]}) RETURN n"
    else:
        cypher_query = "Invalid query"
    return cypher_query


class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__password = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__password))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = session.run(query, parameters)
            return [record for record in response]
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()

# Function to process user query
def process_query(user_query):
    entities, intent = extract_entities_and_intent(user_query)
    cypher_query = map_to_cypher(entities, intent)
    return cypher_query

conn = Neo4jConnection(uri="bolt://localhost:7687", user="neo4j", pwd="yatharth2004")

user_query = "How many persons are in the database?"
cypher_query = process_query(user_query)
print("Generated Cypher Query:", cypher_query)

results = conn.query(cypher_query)
for record in results:
    print(record)

# Close the connection
conn.close()
