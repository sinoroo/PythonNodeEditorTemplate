"""Base node class."""
from typing import Dict, List, Optional, Tuple


class NodePort:
    """Input/Output port for nodes."""
    
    def __init__(self, name: str, port_type: str, data_type: str = "Any"):
        self.name = name
        self.port_type = port_type  # "input" or "output"
        self.data_type = data_type
    
    def __hash__(self):
        return hash((self.name, self.port_type))


class BaseNode:
    """Base class for canvas nodes."""
    
    _node_id_counter = 0
    
    def __init__(self, node_id: Optional[int] = None, title: str = "", 
                 image_path: str = "", category: str = ""):
        if node_id is None:
            BaseNode._node_id_counter += 1
            node_id = BaseNode._node_id_counter
        
        self.node_id = node_id
        self.title = title
        self.image_path = image_path
        self.category = category
        
        # Position on canvas
        self.x: float = 0
        self.y: float = 0
        
        # Ports
        self.input_ports: Dict[str, NodePort] = {}
        self.output_ports: Dict[str, NodePort] = {}
        
        # Connections
        self.input_connections: Dict[str, Tuple[int, str]] = {}  # port_name -> (node_id, port_name)
        self.output_connections: Dict[str, List[Tuple[int, str]]] = {}  # port_name -> [(node_id, port_name), ...]
    
    def add_input_port(self, name: str, data_type: str = "Any"):
        """Add an input port."""
        self.input_ports[name] = NodePort(name, "input", data_type)
    
    def add_output_port(self, name: str, data_type: str = "Any"):
        """Add an output port."""
        self.output_ports[name] = NodePort(name, "output", data_type)
    
    def connect_input(self, port_name: str, node_id: int, target_port: str):
        """Connect an input port to another node's output."""
        self.input_connections[port_name] = (node_id, target_port)
    
    def connect_output(self, port_name: str, node_id: int, target_port: str):
        """Connect an output port to another node's input."""
        if port_name not in self.output_connections:
            self.output_connections[port_name] = []
        self.output_connections[port_name].append((node_id, target_port))
    
    def disconnect_input(self, port_name: str):
        """Disconnect an input port."""
        if port_name in self.input_connections:
            del self.input_connections[port_name]
    
    def disconnect_output(self, port_name: str, node_id: int = None, target_port: str = None):
        """Disconnect an output port."""
        if port_name in self.output_connections:
            if node_id is None:
                del self.output_connections[port_name]
            else:
                self.output_connections[port_name] = [
                    conn for conn in self.output_connections[port_name]
                    if not (conn[0] == node_id and conn[1] == target_port)
                ]
    
    def to_dict(self) -> dict:
        """Serialize node to dictionary."""
        return {
            'node_id': self.node_id,
            'title': self.title,
            'image_path': self.image_path,
            'category': self.category,
            'x': self.x,
            'y': self.y,
            'input_ports': list(self.input_ports.keys()),
            'output_ports': list(self.output_ports.keys()),
            'input_connections': self.input_connections,
            'output_connections': self.output_connections,
        }
    
    def __repr__(self):
        return f"Node({self.title}, id={self.node_id})"
