from neo4j import GraphDatabase
import os

# Environment variables for secure storage
NEO4J_URI = "neo4j+s://fa6b80d7.databases.neo4j.io"
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Initialize Neo4j Driver
# Using execute_read as read_transaction is deprecated
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def get_concept_data(tx, concept_name):
    """
    Fetch all content related to a concept from the Neo4j database.
    """
    query = (
        "MATCH (chunk:Chunk)-[:HAS_ENTITY]->(concept:Concept {id: $concept_name}) "
        "RETURN chunk.text, concept.name "
        "LIMIT 10"
    )  # Fixed the spacing between RETURN and LIMIT
    results = tx.run(query, concept_name=concept_name)
    return [{"text": record["chunk.text"], "concept": record["concept.name"]} for record in results]

def run_test_query():
    """
    Execute a test query directly from the script.
    """
    try:
        with driver.session() as session:
            results = session.execute_read(get_concept_data, "Make It Obvious")
            print('Query Result Type:', type(results))
            print("Query Results:", results)
    except Exception as e:
        print("Error executing test query:", str(e))
    finally:
        driver.close()

if __name__ == "__main__":
    run_test_query()
