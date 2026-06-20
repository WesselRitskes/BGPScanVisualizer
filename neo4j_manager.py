from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path

import os
from dotenv import load_dotenv
load_dotenv()

uri = os.getenv('NEO4J_URI')
name = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(
    uri,
    auth=(name, password),
)

PUBLIC_AS = "Public_AS"
PRIVATE_AS = "Private_AS"
ROUTER = "Router"

ROUTER_TO_AS_RELATION = "LINK"
ROUTER_BELONGS_TO_AS_RELATION = "LOCATED_IN"
INTER_AS_RELATION = "PEERS_WITH"
PRIVATE_AS_BELONGS_TO_AS_RELATION = "PRIVATE_OF"

class Neo4jManager:
    def __init__(self, ctx):
        self.ctx = ctx

    #
    # Graph obtaining methods (currently not used, potential use-case in PyQt visualizing)
    #

    def inspect(self, asn):
        # Query returns:
        #  - AS node
        #  - It's private AS's
        #  - Direct routers
        #  - Private AS's routers
        result = self.ctx.run(f"""
            MATCH (a1:{PUBLIC_AS} {{asn:{asn}}})
            OPTIONAL MATCH priv_as_list=(p:{PRIVATE_AS})-[:{PRIVATE_AS_BELONGS_TO_AS_RELATION}]->(a1)
            OPTIONAL MATCH publ_routers=(r1:{ROUTER})-[:{ROUTER_BELONGS_TO_AS_RELATION}]->(a1)
            OPTIONAL MATCH priv_routers=(r2:{ROUTER})-[:{ROUTER_BELONGS_TO_AS_RELATION}]->(p)
            RETURN priv_as_list, publ_routers, priv_routers;
        """)
        return _result_to_graph(result)

    def get_inter_as_relations(self):
        return self.ctx.run(f"""
                    MATCH (a1:{PUBLIC_AS})
                    OPTIONAL MATCH p=(a1)<-[:{INTER_AS_RELATION}]->(a2:{PUBLIC_AS})
                    WHERE a1.asn <> a2.asn
                    RETURN a1, p;
                """)

    def visualize(self, query):
        return _result_to_graph(self.ctx.run(query))

    def overview(self):
        return _result_to_graph(self.get_inter_as_relations())


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
                        "id": str(value.id),
                        "label": _get_name(value),
                        "type": next(iter(value.labels)).lower(),
                    }
                }

            elif isinstance(value, Relationship):
                edges.add((
                    str(value.start_node.id),
                    str(value.end_node.id),
                    value.type
                ))

            elif isinstance(value, Path):
                for node in value.nodes:
                    nodes[str(node.id)] = {
                        "data": {
                            "id": str(node.id),
                            "asn": str(node.get("asn")),
                            "label": _get_name(node),
                            "type": next(iter(node.labels)).lower(),
                        }
                    }

                for rel in value.relationships:
                    edges.add((
                        str(rel.start_node.id),
                        str(rel.end_node.id),
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