"""
CIRAH: Control-Plane Intervention Cost Model
Formulates the multi-dimensional cost of network reconfiguration:
  C(a) = lambda_I * C_I(a) + lambda_D * C_D(a) + lambda_L * C_L(a)

Where:
  - C_I: Direct Control-Plane Intervention Cost (OpenFlow Flow-Mod rules, switch reconfigs, packet-in/out messages)
  - C_D: Transient Service Disruption Cost (downtime during rule installation, transient reordering)
  - C_L: Path Latency Delta / SLA Cost
"""

import networkx as nx
from typing import Dict, List, Any, Optional

class InterventionCostModel:
    """
    Evaluates fine-grained control-plane and data-plane reconfiguration costs.
    """

    def __init__(self,
                 w_flow_mod: float = 1.0,     # Cost per OpenFlow FLOW_MOD entry installed/deleted
                 w_switch_hit: float = 2.5,   # Cost per switch modified (CPU/TCAM update overhead)
                 w_ctrl_msg: float = 0.5,     # OpenFlow barrier/echo request overhead
                 w_flow_disrupt: float = 5.0, # Service penalty per interrupted active flow
                 reconfig_delay_ms_per_switch: float = 12.0 # Hardware rule commit delay
                 ):
        self.w_flow_mod = w_flow_mod
        self.w_switch_hit = w_switch_hit
        self.w_ctrl_msg = w_ctrl_msg
        self.w_flow_disrupt = w_flow_disrupt
        self.reconfig_delay_ms_per_switch = reconfig_delay_ms_per_switch

    def compute_intervention_cost(self, 
                                  old_path: Optional[List[str]], 
                                  new_path: Optional[List[str]], 
                                  flow_demand_mbps: float,
                                  is_reassigned: bool = True) -> Dict[str, float]:
        """
        Computes the complete cost vector for transitioning from old_path to new_path.
        """
        # If path didn't change
        if not is_reassigned or old_path == new_path or new_path is None:
            return {
                "flow_mods": 0.0,
                "switches_modified": 0.0,
                "links_changed": 0.0,
                "ctrl_messages": 0.0,
                "disruption_time_ms": 0.0,
                "disruption_cost": 0.0,
                "C_I": 0.0,
                "C_D": 0.0
            }

        old_nodes = set(old_path) if old_path else set()
        new_nodes = set(new_path)
        
        # Switches requiring modifications:
        # 1. New switches needing forwarding rules installed
        # 2. Old switches whose rules must be deleted or redirected
        affected_switches = old_nodes.symmetric_difference(new_nodes)
        if old_path and new_path and old_path[0] == new_path[0]:
            # Ingress switch always updated
            affected_switches.add(new_path[0])
            
        num_switches = len(affected_switches)

        # Flow table rule updates (FLOW_MODs):
        # 1 rule per switch along new path + deletions along obsolete hops
        flow_mods = len(new_path) + max(0, len(old_nodes - new_nodes))

        # Links changed
        old_edges = set((old_path[i], old_path[i+1]) for i in range(len(old_path)-1)) if old_path else set()
        new_edges = set((new_path[i], new_path[i+1]) for i in range(len(new_path)-1))
        links_changed = len(old_edges.symmetric_difference(new_edges))

        # Control plane messages: 1 FLOW_MOD per modification + 1 BARRIER_REQUEST per switch
        ctrl_messages = flow_mods + num_switches

        # Control plane operational cost C_I
        C_I = (self.w_flow_mod * flow_mods + 
               self.w_switch_hit * num_switches + 
               self.w_ctrl_msg * ctrl_messages)

        # Transient service disruption: estimated latency window while rules converge
        disruption_time_ms = num_switches * self.reconfig_delay_ms_per_switch
        # Disruption cost C_D scales with affected flow throughput during interruption
        C_D = (disruption_time_ms / 1000.0) * flow_demand_mbps * self.w_flow_disrupt

        return {
            "flow_mods": float(flow_mods),
            "switches_modified": float(num_switches),
            "links_changed": float(links_changed),
            "ctrl_messages": float(ctrl_messages),
            "disruption_time_ms": float(disruption_time_ms),
            "disruption_cost": float(C_D),
            "C_I": float(C_I),
            "C_D": float(C_D)
        }
