"""
CIRAH: Network Topologies Module
Defines realistic network topologies with physical attributes:
- Abilene (11 nodes, 14 links, US backbone)
- GEANT (22 nodes, 36 links, pan-European research network)
- Fat-Tree (k=4, 20 switches, datacenter multi-path)
- Diamond-Extended (6 nodes, 8 links, controlled testbed)
"""

import networkx as nx
import numpy as np

def create_diamond_extended() -> nx.DiGraph:
    """Creates a 6-node extended diamond topology for controlled benchmarking."""
    G = nx.DiGraph()
    nodes = ["s1", "s2", "s3", "s4", "s5", "s6"]
    for n in nodes:
        G.add_node(n, type="switch", flow_table_capacity=1000, buffer_size=50)

    # Base links: (u, v, latency_ms, capacity_mbps)
    edges = [
        ("s1", "s2", 5.0, 100.0),
        ("s1", "s3", 7.0, 100.0),
        ("s2", "s4", 6.0, 80.0),
        ("s3", "s4", 6.0, 80.0),
        ("s2", "s5", 8.0, 50.0),
        ("s3", "s5", 8.0, 50.0),
        ("s4", "s6", 5.0, 100.0),
        ("s5", "s6", 7.0, 80.0),
    ]

    for u, v, lat, cap in edges:
        # Add bi-directional directed links
        G.add_edge(u, v, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)
        G.add_edge(v, u, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)

    return G

def create_abilene_topology() -> nx.DiGraph:
    """
    Creates the Abilene Internet2 backbone topology (11 nodes, 14 bi-directional links).
    Nodes: ATLA, CHIN, DNVR, HSTN, INDY, KSCY, LOSA, NYCM, SNVA, STTL, WASH
    """
    G = nx.DiGraph()
    cities = [
        "ATLA", "CHIN", "DNVR", "HSTN", "INDY", 
        "KSCY", "LOSA", "NYCM", "SNVA", "STTL", "WASH"
    ]
    for c in cities:
        G.add_node(c, type="switch", flow_table_capacity=4000, buffer_size=200)

    # Real-world approximate latency (ms) and 10 Gbps / 1000 Mbps normalized capacities
    links = [
        ("NYCM", "CHIN", 15.0, 1000.0),
        ("NYCM", "WASH", 5.0, 1000.0),
        ("WASH", "ATLA", 12.0, 1000.0),
        ("ATLA", "HSTN", 16.0, 1000.0),
        ("ATLA", "INDY", 10.0, 1000.0),
        ("INDY", "CHIN", 5.0, 1000.0),
        ("INDY", "KSCY", 10.0, 1000.0),
        ("CHIN", "KSCY", 8.0, 1000.0),
        ("KSCY", "DNVR", 12.0, 1000.0),
        ("KSCY", "HSTN", 14.0, 1000.0),
        ("HSTN", "LOSA", 28.0, 1000.0),
        ("DNVR", "STTL", 22.0, 1000.0),
        ("DNVR", "SNVA", 20.0, 1000.0),
        ("SNVA", "LOSA", 8.0, 1000.0),
        ("SNVA", "STTL", 16.0, 1000.0),
    ]

    for u, v, lat, cap in links:
        G.add_edge(u, v, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)
        G.add_edge(v, u, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)

    return G

def create_geant_topology() -> nx.DiGraph:
    """
    Creates a simplified GEANT pan-European research backbone topology (22 nodes, 36 links).
    """
    G = nx.DiGraph()
    nodes = [f"G_{i}" for i in range(1, 23)]
    for n in nodes:
        G.add_node(n, type="switch", flow_table_capacity=8000, buffer_size=500)

    # Core ring and cross-connect edges
    edges = [
        ("G_1", "G_2", 8.0, 1000.0), ("G_2", "G_3", 10.0, 1000.0), ("G_3", "G_4", 12.0, 1000.0),
        ("G_4", "G_5", 9.0, 1000.0), ("G_5", "G_6", 11.0, 1000.0), ("G_6", "G_7", 14.0, 1000.0),
        ("G_7", "G_8", 7.0, 1000.0), ("G_8", "G_9", 15.0, 1000.0), ("G_9", "G_10", 8.0, 1000.0),
        ("G_10", "G_11", 13.0, 1000.0), ("G_11", "G_12", 6.0, 1000.0), ("G_12", "G_1", 18.0, 1000.0),
        # Cross chords
        ("G_1", "G_7", 22.0, 1000.0), ("G_3", "G_9", 25.0, 1000.0), ("G_5", "G_11", 20.0, 1000.0),
        ("G_2", "G_8", 24.0, 1000.0), ("G_4", "G_10", 21.0, 1000.0), ("G_6", "G_12", 23.0, 1000.0),
        # Regional branches
        ("G_13", "G_1", 5.0, 500.0), ("G_14", "G_2", 6.0, 500.0), ("G_15", "G_4", 7.0, 500.0),
        ("G_16", "G_5", 5.0, 500.0), ("G_17", "G_7", 8.0, 500.0), ("G_18", "G_8", 6.0, 500.0),
        ("G_19", "G_10", 7.0, 500.0), ("G_20", "G_11", 5.0, 500.0), ("G_21", "G_12", 9.0, 500.0),
        ("G_22", "G_3", 8.0, 500.0),
    ]

    for u, v, lat, cap in edges:
        G.add_edge(u, v, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)
        G.add_edge(v, u, latency=lat, capacity=cap, load=0.0, loss=0.0, status=1, queue=0.0)

    return G

def get_topology(name: str) -> nx.DiGraph:
    """Returns a fresh deep copy of the requested topology."""
    name_lower = name.lower()
    if name_lower in ["diamond", "diamond_extended", "extended"]:
        return create_diamond_extended()
    elif name_lower in ["abilene", "abilene_11"]:
        return create_abilene_topology()
    elif name_lower in ["geant", "geant_22"]:
        return create_geant_topology()
    else:
        raise ValueError(f"Unknown topology: {name}")

def generate_traffic_demands(G: nx.DiGraph, num_flows: int = 10, rng_seed: int = 42) -> list:
    """
    Generates synthetic realistic traffic flow demands between random node pairs.
    Each flow has: (id, src, dst, bandwidth_demand_mbps, sla_max_lat, sla_max_loss)
    """
    rng = np.random.default_rng(rng_seed)
    nodes = list(G.nodes())
    flows = []
    
    for i in range(num_flows):
        src, dst = rng.choice(nodes, size=2, replace=False)
        bw = float(rng.uniform(10.0, 45.0))
        # Find shortest path base latency to set realistic SLA thresholds
        try:
            base_lat = nx.shortest_path_length(G, src, dst, weight="latency")
        except nx.NetworkXNoPath:
            base_lat = 50.0
            
        sla_lat = float(base_lat * rng.uniform(1.8, 2.5))
        sla_loss = float(rng.uniform(1.0, 3.0)) # max 1-3% loss
        
        flows.append({
            "flow_id": f"flow_{i+1}",
            "src": src,
            "dst": dst,
            "bandwidth_mbps": bw,
            "sla_max_latency_ms": sla_lat,
            "sla_max_loss_pct": sla_loss,
            "current_path": None,
            "active": True
        })
    return flows
