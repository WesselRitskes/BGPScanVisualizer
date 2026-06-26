from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path

PUBLIC_AS = "Public_AS"
PRIVATE_AS = "Private_AS"
ROUTER = "Router"

ROUTER_TO_AS_RELATION = "LINK"
ROUTER_BELONGS_TO_AS_RELATION = "LOCATED_IN"
INTER_AS_RELATION = "PEERS_WITH"
PRIVATE_AS_BELONGS_TO_AS_RELATION = "PRIVATE_OF"

import os
from dotenv import load_dotenv
load_dotenv()

uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(
    uri,
    auth=(username, password),
)

class Neo4jManager:
    def __init__(self, ctx):
        self.ctx = ctx

    #
    # Graph obtaining methods (currently not used, potential use-case in PyQt visualizing)
    #

    def inspect_public_as(self, asn):
        # Query returns:
        #  - AS node
        #  - It's private AS's
        #  - Direct routers
        return self.visualize(f"""
            MATCH (a1:{PUBLIC_AS} {{asn:{asn}}})
            OPTIONAL MATCH priv_as_list=(p:{PRIVATE_AS})-[:{PRIVATE_AS_BELONGS_TO_AS_RELATION}]->(a1)
            OPTIONAL MATCH publ_routers=(r1:{ROUTER})-[:{ROUTER_BELONGS_TO_AS_RELATION}]->(a1)
            RETURN priv_as_list, publ_routers;
        """)

    def inspect_private_as(self, as_id):
        # Query returns:
        #  - Private AS
        #  - Its public AS
        #  - Direct routers
        return self.visualize(f"""
            MATCH belongs=(a1:{PRIVATE_AS} {{as_id:"{as_id}"}})-[:{PRIVATE_AS_BELONGS_TO_AS_RELATION}]->(a2)
            OPTIONAL MATCH routers=(r1:{ROUTER})-[:{ROUTER_BELONGS_TO_AS_RELATION}]->(a1)
            RETURN belongs, routers;
        """)

    def inspect_router(self, r_id):
        # Query returns:
        #  - Router node
        #  - AS it belongs to
        #  - Potential links
        return self.visualize(f"""
            MATCH belongs=(r:{ROUTER} {{router_id:"{r_id}"}})-[:{ROUTER_BELONGS_TO_AS_RELATION}]->(a1)
            OPTIONAL MATCH links=(r)-[:{ROUTER_TO_AS_RELATION}]->(a2)
            RETURN belongs, links;
        """)

    def overview(self):
        # Query returns:
        #  - All public AS nodes
        #  - Their peer links.
        return self.visualize(f"""
                    MATCH (a1:{PUBLIC_AS})
                    OPTIONAL MATCH p=(a1)<-[:{INTER_AS_RELATION}]->(a2:{PUBLIC_AS})
                    WHERE a1.asn <> a2.asn
                    RETURN a1, p;
                """)

    def visualize(self, query):
        return _result_to_graph(self.ctx.run(query))


#
# Helper functions
#

def _result_to_graph(result):
    nodes = {}
    edges = set()

    for record in result:
        for value in record.values():

            if isinstance(value, Node):
                nodes[str(value.id)] = {
                    "data": {
                        "id": _get_id(value),
                        "label": _get_name(value),
                        "type": next(iter(value.labels)),
                    }
                }

            elif isinstance(value, Relationship):
                edges.add((
                    _get_id(value.start_node),
                    _get_id(value.end_node),
                    value.type
                ))

            elif isinstance(value, Path):
                for node in value.nodes:
                    nodes[str(node.id)] = {
                        "data": {
                            "id": _get_id(node),
                            "label": _get_name(node),
                            "type": next(iter(node.labels)),
                        }
                    }

                for rel in value.relationships:
                    edges.add((
                        _get_id(rel.start_node),
                        _get_id(rel.end_node),
                        rel.type
                    ))

    return nodes, edges

def _get_name(node):
    node_type = next(iter(node.labels))

    if node_type == PUBLIC_AS:
        return f"AS{node.get('asn')}"
    elif node_type == PRIVATE_AS:
        return f"AS{node.get('as_id')}"
    elif node_type == ROUTER:
        return f"R({node.get('router_id')})"

def _get_id(node):
    node_type = next(iter(node.labels))

    if node_type == PUBLIC_AS:
        return f"{node.get('asn')}"
    elif node_type == PRIVATE_AS:
        return f"{node.get('as_id')}"
    elif node_type == ROUTER:
        return f"{node.get('router_id')}"