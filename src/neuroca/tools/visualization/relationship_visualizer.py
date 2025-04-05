"""
Relationship Visualizer for NeuroCognitive Architecture

This module provides tools to visualize relationships between different components
of the NeuroCognitive Architecture (NCA) system. It supports visualization of memory
relationships, cognitive process flows, and component dependencies using various
visualization techniques and libraries.

The visualizer can generate interactive graphs, static diagrams, and exportable
visualizations in multiple formats to aid in understanding the complex relationships
within the NCA system.

Usage Examples:
    # Create a basic relationship graph
    visualizer = RelationshipVisualizer()
    visualizer.add_node("memory_1", node_type="episodic_memory")
    visualizer.add_node("memory_2", node_type="semantic_memory")
    visualizer.add_edge("memory_1", "memory_2", relationship="references")
    visualizer.render("memory_relationship.html")

    # Visualize memory system relationships
    memory_viz = MemoryRelationshipVisualizer()
    memory_viz.load_memory_data(memory_system)
    memory_viz.render("memory_system.png")
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

# Visualization libraries
try:
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.patches import Patch
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib not available. Some visualization features will be limited.")

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available. Interactive visualizations will be disabled.")

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False
    logging.warning("Pyvis not available. Network visualizations will be limited.")

# Configure logger
logger = logging.getLogger(__name__)


class VisualizationFormat(Enum):
    """Supported visualization output formats."""
    HTML = "html"
    PNG = "png"
    JPG = "jpg"
    SVG = "svg"
    PDF = "pdf"
    JSON = "json"


class NodeType(Enum):
    """Types of nodes that can be visualized in the NCA system."""
    EPISODIC_MEMORY = "episodic_memory"
    SEMANTIC_MEMORY = "semantic_memory"
    PROCEDURAL_MEMORY = "procedural_memory"
    COGNITIVE_PROCESS = "cognitive_process"
    ATTENTION_MECHANISM = "attention_mechanism"
    EMOTION_CENTER = "emotion_center"
    PERCEPTION_MODULE = "perception_module"
    REASONING_MODULE = "reasoning_module"
    EXTERNAL_SYSTEM = "external_system"
    GENERIC = "generic"


class EdgeType(Enum):
    """Types of relationships between nodes in the NCA system."""
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    TRIGGERS = "triggers"
    INHIBITS = "inhibits"
    STRENGTHENS = "strengthens"
    FLOWS_TO = "flows_to"
    ASSOCIATES_WITH = "associates_with"
    CONTAINS = "contains"
    GENERIC = "generic"


class VisualizationError(Exception):
    """Base exception for visualization errors."""
    pass


class RelationshipVisualizer:
    """
    Core class for visualizing relationships between components in the NCA system.
    
    This class provides the foundation for creating, manipulating, and rendering
    visualizations of relationships between different components of the NCA system.
    It supports multiple visualization backends and output formats.
    """
    
    def __init__(self, title: str = "NCA Relationship Visualization"):
        """
        Initialize a new relationship visualizer.
        
        Args:
            title: Title for the visualization
        """
        self.title = title
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.node_groups: dict[str, list[str]] = {}
        self._nx_graph = None
        self._node_positions = None
        self.last_update = datetime.now()
        
        # Default visualization settings
        self.settings = {
            "node_size": 20,
            "edge_width": 1.5,
            "font_size": 10,
            "show_labels": True,
            "show_legend": True,
            "layout": "force_directed",
            "theme": "light",
            "interactive": True
        }
        
        logger.debug(f"Initialized RelationshipVisualizer with title: {title}")
    
    def add_node(self, node_id: str, 
                 node_type: Union[str, NodeType] = NodeType.GENERIC, 
                 label: Optional[str] = None,
                 attributes: Optional[dict[str, Any]] = None,
                 group: Optional[str] = None) -> None:
        """
        Add a node to the visualization.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of the node (from NodeType enum or string)
            label: Display label for the node (defaults to node_id if None)
            attributes: Additional attributes for the node
            group: Group to which the node belongs
            
        Raises:
            ValueError: If node_id already exists
        """
        if node_id in self.nodes:
            raise ValueError(f"Node with ID '{node_id}' already exists")
        
        # Convert string node_type to enum if needed
        if isinstance(node_type, str):
            try:
                node_type = NodeType(node_type)
            except ValueError:
                logger.warning(f"Unknown node type: {node_type}. Using GENERIC instead.")
                node_type = NodeType.GENERIC
        
        # Create node with attributes
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type.value if isinstance(node_type, NodeType) else node_type,
            "label": label or node_id,
            "attributes": attributes or {}
        }
        
        # Add to group if specified
        if group:
            if group not in self.node_groups:
                self.node_groups[group] = []
            self.node_groups[group].append(node_id)
        
        self.last_update = datetime.now()
        logger.debug(f"Added node: {node_id} of type {node_type}")
    
    def add_edge(self, source_id: str, target_id: str, 
                 relationship: Union[str, EdgeType] = EdgeType.GENERIC,
                 weight: float = 1.0,
                 attributes: Optional[dict[str, Any]] = None,
                 bidirectional: bool = False) -> None:
        """
        Add an edge between two nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            relationship: Type of relationship (from EdgeType enum or string)
            weight: Weight/strength of the relationship
            attributes: Additional attributes for the edge
            bidirectional: If True, creates edges in both directions
            
        Raises:
            ValueError: If source or target nodes don't exist
        """
        # Validate nodes exist
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist")
        if target_id not in self.nodes:
            raise ValueError(f"Target node '{target_id}' does not exist")
        
        # Convert string relationship to enum if needed
        if isinstance(relationship, str):
            try:
                relationship = EdgeType(relationship)
            except ValueError:
                logger.warning(f"Unknown relationship type: {relationship}. Using GENERIC instead.")
                relationship = EdgeType.GENERIC
        
        # Create edge
        edge = {
            "source": source_id,
            "target": target_id,
            "relationship": relationship.value if isinstance(relationship, EdgeType) else relationship,
            "weight": weight,
            "attributes": attributes or {}
        }
        
        self.edges.append(edge)
        
        # Add reverse edge if bidirectional
        if bidirectional:
            reverse_edge = edge.copy()
            reverse_edge["source"], reverse_edge["target"] = reverse_edge["target"], reverse_edge["source"]
            self.edges.append(reverse_edge)
        
        self.last_update = datetime.now()
        logger.debug(f"Added edge: {source_id} -> {target_id} ({relationship})")
    
    def remove_node(self, node_id: str) -> None:
        """
        Remove a node and all its connected edges.
        
        Args:
            node_id: ID of the node to remove
            
        Raises:
            ValueError: If node doesn't exist
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")
        
        # Remove node
        del self.nodes[node_id]
        
        # Remove all edges connected to this node
        self.edges = [edge for edge in self.edges 
                     if edge["source"] != node_id and edge["target"] != node_id]
        
        # Remove from groups
        for group, nodes in self.node_groups.items():
            if node_id in nodes:
                self.node_groups[group].remove(node_id)
        
        self.last_update = datetime.now()
        logger.debug(f"Removed node: {node_id}")
    
    def update_settings(self, **kwargs) -> None:
        """
        Update visualization settings.
        
        Args:
            **kwargs: Settings to update
        """
        self.settings.update(kwargs)
        logger.debug(f"Updated visualization settings: {kwargs}")
    
    def _build_networkx_graph(self) -> nx.Graph:
        """
        Build a NetworkX graph from the current nodes and edges.
        
        Returns:
            NetworkX graph object
        """
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("NetworkX/Matplotlib is required but not available")
        
        # Create directed or undirected graph
        G = nx.DiGraph()
        
        # Add nodes with attributes
        for node_id, node_data in self.nodes.items():
            G.add_node(node_id, **node_data)
        
        # Add edges with attributes
        for edge in self.edges:
            G.add_edge(edge["source"], edge["target"], 
                      relationship=edge["relationship"],
                      weight=edge["weight"], 
                      **edge["attributes"])
        
        self._nx_graph = G
        return G
    
    def _get_node_positions(self, layout: str = None) -> dict[str, tuple[float, float]]:
        """
        Calculate node positions based on the specified layout algorithm.
        
        Args:
            layout: Layout algorithm to use
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("NetworkX/Matplotlib is required but not available")
        
        if self._nx_graph is None:
            self._build_networkx_graph()
        
        layout = layout or self.settings["layout"]
        
        # Choose layout algorithm
        if layout == "force_directed":
            pos = nx.spring_layout(self._nx_graph)
        elif layout == "circular":
            pos = nx.circular_layout(self._nx_graph)
        elif layout == "spectral":
            pos = nx.spectral_layout(self._nx_graph)
        elif layout == "shell":
            # Group nodes by type for shell layout
            shells = []
            node_types = {node["type"] for node in self.nodes.values()}
            for node_type in node_types:
                shell = [node_id for node_id, data in self.nodes.items() 
                        if data["type"] == node_type]
                if shell:
                    shells.append(shell)
            pos = nx.shell_layout(self._nx_graph, shells) if shells else nx.shell_layout(self._nx_graph)
        else:
            pos = nx.spring_layout(self._nx_graph)  # Default to spring layout
        
        self._node_positions = pos
        return pos
    
    def render_matplotlib(self, output_path: str = None, 
                         figsize: tuple[int, int] = (12, 10)) -> None:
        """
        Render the visualization using Matplotlib.
        
        Args:
            output_path: Path to save the visualization (if None, displays it)
            figsize: Figure size as (width, height) in inches
            
        Raises:
            VisualizationError: If Matplotlib is not available
        """
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("Matplotlib is required but not available")
        
        # Build graph if needed
        if self._nx_graph is None:
            self._build_networkx_graph()
        
        # Get node positions
        pos = self._get_node_positions()
        
        # Create figure
        plt.figure(figsize=figsize)
        plt.title(self.title)
        
        # Prepare node colors by type
        node_types = {data["type"] for data in self.nodes.values()}
        color_map = dict(zip(node_types, plt.cm.tab10.colors))
        
        # Draw nodes
        for node_type in node_types:
            node_list = [node_id for node_id, data in self.nodes.items() 
                        if data["type"] == node_type]
            nx.draw_networkx_nodes(
                self._nx_graph, pos,
                nodelist=node_list,
                node_color=color_map[node_type],
                node_size=self.settings["node_size"] * 100,
                alpha=0.8,
                label=node_type
            )
        
        # Draw edges with different styles based on relationship
        edge_types = {edge["relationship"] for edge in self.edges}
        edge_styles = ['-', '--', '-.', ':']
        
        for i, edge_type in enumerate(edge_types):
            edge_list = [(edge["source"], edge["target"]) for edge in self.edges 
                        if edge["relationship"] == edge_type]
            
            # Skip if no edges of this type
            if not edge_list:
                continue
                
            # Use modulo to cycle through styles if we have more types than styles
            style = edge_styles[i % len(edge_styles)]
            
            nx.draw_networkx_edges(
                self._nx_graph, pos,
                edgelist=edge_list,
                width=self.settings["edge_width"],
                alpha=0.7,
                style=style,
                edge_color='gray',
                arrows=True,
                arrowstyle='-|>',
                arrowsize=10
            )
        
        # Draw labels if enabled
        if self.settings["show_labels"]:
            labels = {node_id: data["label"] for node_id, data in self.nodes.items()}
            nx.draw_networkx_labels(
                self._nx_graph, pos,
                labels=labels,
                font_size=self.settings["font_size"],
                font_family='sans-serif'
            )
        
        # Add legend if enabled
        if self.settings["show_legend"]:
            legend_elements = [
                Patch(facecolor=color_map[node_type], label=node_type)
                for node_type in node_types
            ]
            plt.legend(handles=legend_elements, loc='upper right')
        
        plt.axis('off')  # Turn off axis
        
        # Save or display
        if output_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            logger.info(f"Saved visualization to {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def render_plotly(self, output_path: str = None) -> None:
        """
        Render the visualization using Plotly for interactive graphs.
        
        Args:
            output_path: Path to save the visualization (if None, displays it)
            
        Raises:
            VisualizationError: If Plotly is not available
        """
        if not PLOTLY_AVAILABLE:
            raise VisualizationError("Plotly is required but not available")
        
        # Build graph if needed
        if self._nx_graph is None:
            self._build_networkx_graph()
        
        # Get node positions
        pos = self._get_node_positions()
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        # Map node types to colors
        node_types = list({data["type"] for data in self.nodes.values()})
        color_map = {node_type: i for i, node_type in enumerate(node_types)}
        
        for node_id, node_data in self.nodes.items():
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)
            
            # Create hover text
            hover_text = f"ID: {node_id}<br>Type: {node_data['type']}<br>Label: {node_data['label']}"
            if node_data["attributes"]:
                for key, value in node_data["attributes"].items():
                    hover_text += f"<br>{key}: {value}"
            node_text.append(hover_text)
            
            # Assign color based on node type
            node_color.append(color_map[node_data["type"]])
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text' if self.settings["show_labels"] else 'markers',
            hoverinfo='text',
            text=[data["label"] for data in self.nodes.values()] if self.settings["show_labels"] else None,
            textposition="top center",
            hovertext=node_text,
            marker={
                "showscale": True,
                "colorscale": 'Viridis',
                "color": node_color,
                "size": self.settings["node_size"] * 2,
                "line": {"width": 2, "color": '#FFFFFF'}
            }
        )
        
        # Create edge traces
        edge_traces = []
        
        for edge in self.edges:
            source_pos = pos[edge["source"]]
            target_pos = pos[edge["target"]]
            
            # Create line between nodes
            edge_trace = go.Scatter(
                x=[source_pos[0], target_pos[0], None],
                y=[source_pos[1], target_pos[1], None],
                mode='lines',
                line={"width": edge["weight"] * self.settings["edge_width"], "color": '#888'},
                hoverinfo='text',
                hovertext=f"Relationship: {edge['relationship']}<br>Weight: {edge['weight']}"
            )
            edge_traces.append(edge_trace)
        
        # Create figure
        fig = go.Figure(
            data=[node_trace] + edge_traces,
            layout=go.Layout(
                title=self.title,
                showlegend=False,
                hovermode='closest',
                margin={"b": 20, "l": 5, "r": 5, "t": 40},
                xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                plot_bgcolor=('#FFFFFF' if self.settings["theme"] == "light" else '#1E1E1E')
            )
        )
        
        # Add legend for node types
        if self.settings["show_legend"]:
            for node_type, color_idx in color_map.items():
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker={"size": 10, "color": color_idx, "colorscale": 'Viridis'},
                    showlegend=True,
                    name=node_type
                ))
        
        # Save or display
        if output_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            fig.write_html(output_path)
            logger.info(f"Saved interactive visualization to {output_path}")
        else:
            fig.show()
    
    def render_pyvis(self, output_path: str) -> None:
        """
        Render the visualization using PyVis for interactive network graphs.
        
        Args:
            output_path: Path to save the HTML visualization
            
        Raises:
            VisualizationError: If PyVis is not available
        """
        if not PYVIS_AVAILABLE:
            raise VisualizationError("PyVis is required but not available")
        
        # Create network
        net = Network(
            height="750px", 
            width="100%", 
            heading=self.title,
            font_color="black" if self.settings["theme"] == "light" else "white",
            bgcolor="#ffffff" if self.settings["theme"] == "light" else "#222222",
            directed=True
        )
        
        # Map node types to colors
        node_types = list({data["type"] for data in self.nodes.values()})
        color_palette = ["#3366CC", "#DC3912", "#FF9900", "#109618", "#990099", 
                         "#0099C6", "#DD4477", "#66AA00", "#B82E2E", "#316395"]
        color_map = {node_type: color_palette[i % len(color_palette)] 
                    for i, node_type in enumerate(node_types)}
        
        # Add nodes
        for node_id, node_data in self.nodes.items():
            title = f"ID: {node_id}<br>Type: {node_data['type']}<br>Label: {node_data['label']}"
            if node_data["attributes"]:
                for key, value in node_data["attributes"].items():
                    title += f"<br>{key}: {value}"
            
            net.add_node(
                node_id, 
                label=node_data["label"],
                title=title,
                color=color_map[node_data["type"]],
                size=self.settings["node_size"] * 5
            )
        
        # Add edges
        for edge in self.edges:
            net.add_edge(
                edge["source"],
                edge["target"],
                title=f"Relationship: {edge['relationship']}<br>Weight: {edge['weight']}",
                width=edge["weight"] * self.settings["edge_width"],
                arrowStrikethrough=True
            )
        
        # Set physics options for better layout
        net.set_options("""
        var options = {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
              "enabled": true,
              "iterations": 1000
            }
          }
        }
        """)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save the visualization
        net.save_graph(output_path)
        logger.info(f"Saved interactive network visualization to {output_path}")
    
    def export_json(self, output_path: str) -> None:
        """
        Export the visualization data as JSON.
        
        Args:
            output_path: Path to save the JSON file
        """
        data = {
            "title": self.title,
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "groups": self.node_groups,
            "settings": self.settings,
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": self.last_update.isoformat()
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported visualization data to {output_path}")
    
    def load_json(self, input_path: str) -> None:
        """
        Load visualization data from a JSON file.
        
        Args:
            input_path: Path to the JSON file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        with open(input_path, encoding='utf-8') as f:
            data = json.load(f)
        
        self.title = data.get("title", "NCA Relationship Visualization")
        
        # Clear existing data
        self.nodes = {}
        self.edges = []
        self.node_groups = {}
        
        # Load nodes
        for node_data in data.get("nodes", []):
            self.nodes[node_data["id"]] = node_data
        
        # Load edges
        self.edges = data.get("edges", [])
        
        # Load groups
        self.node_groups = data.get("groups", {})
        
        # Load settings
        if "settings" in data:
            self.settings.update(data["settings"])
        
        # Update timestamp
        self.last_update = datetime.now()
        
        logger.info(f"Loaded visualization data from {input_path}")
    
    def render(self, output_path: Optional[str] = None, 
              format: Union[str, VisualizationFormat] = None) -> None:
        """
        Render the visualization in the specified format.
        
        Args:
            output_path: Path to save the visualization (if None, displays it)
            format: Output format (if None, inferred from output_path extension)
            
        Raises:
            VisualizationError: If the format is not supported or required libraries are missing
            ValueError: If output_path is None and format is not specified
        """
        # Validate input
        if output_path is None and not self.settings["interactive"]:
            raise ValueError("output_path must be provided for non-interactive visualizations")
        
        # Determine format
        if format is None and output_path is not None:
            # Infer format from file extension
            ext = os.path.splitext(output_path)[1].lower().lstrip('.')
            try:
                format = VisualizationFormat(ext)
            except ValueError:
                raise VisualizationError(f"Unsupported file extension: {ext}")
        elif isinstance(format, str):
            try:
                format = VisualizationFormat(format.lower())
            except ValueError:
                raise VisualizationError(f"Unsupported format: {format}")
        
        # Render based on format
        if format == VisualizationFormat.HTML:
            if PYVIS_AVAILABLE:
                self.render_pyvis(output_path)
            elif PLOTLY_AVAILABLE:
                self.render_plotly(output_path)
            else:
                raise VisualizationError("HTML visualization requires PyVis or Plotly")
        
        elif format in [VisualizationFormat.PNG, VisualizationFormat.JPG, 
                       VisualizationFormat.SVG, VisualizationFormat.PDF]:
            if MATPLOTLIB_AVAILABLE:
                self.render_matplotlib(output_path)
            else:
                raise VisualizationError(f"{format.value} visualization requires Matplotlib")
        
        elif format == VisualizationFormat.JSON:
            self.export_json(output_path)
        
        elif format is None:
            # Interactive display
            if PLOTLY_AVAILABLE:
                self.render_plotly()
            elif MATPLOTLIB_AVAILABLE:
                self.render_matplotlib()
            else:
                raise VisualizationError("Interactive visualization requires Plotly or Matplotlib")
        
        else:
            raise VisualizationError(f"Unsupported format: {format}")


class MemoryRelationshipVisualizer(RelationshipVisualizer):
    """
    Specialized visualizer for memory relationships in the NCA system.
    
    This class extends the base RelationshipVisualizer with specific functionality
    for visualizing memory relationships, including methods to load memory data
    from the NCA memory system.
    """
    
    def __init__(self, title: str = "NCA Memory Relationship Visualization"):
        """
        Initialize a memory relationship visualizer.
        
        Args:
            title: Title for the visualization
        """
        super().__init__(title)
        
        # Memory-specific settings
        self.update_settings(
            node_size=25,
            show_memory_strength=True,
            highlight_active_memories=True
        )
        
        logger.debug("Initialized MemoryRelationshipVisualizer")
    
    def load_memory_data(self, memory_system: Any) -> None:
        """
        Load memory data from the NCA memory system.
        
        Args:
            memory_system: The memory system object from which to load data
            
        Note:
            This is a placeholder method that should be implemented based on
            the actual memory system implementation.
        """
        # This is a placeholder implementation
        # In a real implementation, this would extract memory nodes and relationships
        # from the actual memory system implementation
        
        logger.warning("Using placeholder implementation of load_memory_data")
        logger.info(f"Loading memory data from memory system: {memory_system}")
        
        # Example implementation (to be replaced with actual implementation)
        try:
            # Add memory tiers as groups
            memory_tiers = ["episodic", "semantic", "procedural"]
            
            for tier in memory_tiers:
                # Get memories from this tier (placeholder)
                memories = getattr(memory_system, f"get_{tier}_memories", lambda: [])()
                
                # Add each memory as a node
                for memory in memories:
                    memory_id = getattr(memory, "id", str(id(memory)))
                    memory_type = f"{tier}_memory"
                    
                    # Extract attributes
                    attributes = {}
                    for attr in ["strength", "creation_time", "last_access", "activation"]:
                        if hasattr(memory, attr):
                            attributes[attr] = getattr(memory, attr)
                    
                    # Add the node
                    self.add_node(
                        node_id=memory_id,
                        node_type=memory_type,
                        label=getattr(memory, "label", memory_id),
                        attributes=attributes,
                        group=tier
                    )
                    
                    # Add relationships to other memories
                    if hasattr(memory, "relationships"):
                        for rel in memory.relationships:
                            target_id = getattr(rel, "target_id", None)
                            if target_id:
                                self.add_edge(
                                    source_id=memory_id,
                                    target_id=target_id,
                                    relationship=getattr(rel, "type", "associates_with"),
                                    weight=getattr(rel, "strength", 1.0)
                                )
            
            logger.info(f"Loaded {len(self.nodes)} memory nodes and {len(self.edges)} relationships")
            
        except Exception as e:
            logger.error(f"Error loading memory data: {str(e)}")
            raise
    
    def highlight_active_memories(self, active_ids: list[str], color: str = "#FF5733") -> None:
        """
        Highlight currently active memories in the visualization.
        
        Args:
            active_ids: List of IDs of active memories
            color: Color to use for highlighting
        """
        for node_id in active_ids:
            if node_id in self.nodes:
                self.nodes[node_id]["attributes"]["active"] = True
                self.nodes[node_id]["attributes"]["highlight_color"] = color
        
        logger.debug(f"Highlighted {len(active_ids)} active memories")


class CognitiveProcessVisualizer(RelationshipVisualizer):
    """
    Specialized visualizer for cognitive processes in the NCA system.
    
    This class extends the base RelationshipVisualizer with specific functionality
    for visualizing cognitive processes and their interactions.
    """
    
    def __init__(self, title: str = "NCA Cognitive Process Visualization"):
        """
        Initialize a cognitive process visualizer.
        
        Args:
            title: Title for the visualization
        """
        super().__init__(title)
        
        # Process-specific settings
        self.update_settings(
            layout="circular",
            show_process_state=True,
            animate_process_flow=True
        )
        
        logger.debug("Initialized CognitiveProcessVisualizer")
    
    def add_process_flow(self, process_steps: list[dict[str, Any]]) -> None:
        """
        Add a sequence of cognitive process steps to the visualization.
        
        Args:
            process_steps: List of process steps, each containing at least:
                - id: Unique identifier for the step
                - label: Display label for the step
                - type: Type of process step
                - next_steps: List of IDs of possible next steps
        """
        # Add nodes for each process step
        for step in process_steps:
            self.add_node(
                node_id=step["id"],
                node_type=step.get("type", "cognitive_process"),
                label=step.get("label", step["id"]),
                attributes=step.get("attributes", {})
            )
            
            # Add edges to next steps
            for next_step in step.get("next_steps", []):
                self.add_edge(
                    source_id=step["id"],
                    target_id=next_step,
                    relationship="flows_to",
                    weight=step.get("transition_weight", {}).get(next_step, 1.0)
                )
        
        logger.debug(f"Added process flow with {len(process_steps)} steps")


def create_default_visualizer(visualization_type: str = "general") -> RelationshipVisualizer:
    """
    Factory function to create a visualizer with default settings.
    
    Args:
        visualization_type: Type of visualizer to create
            ("general", "memory", "cognitive")
            
    Returns:
        An initialized visualizer of the appropriate type
        
    Raises:
        ValueError: If visualization_type is not recognized
    """
    if visualization_type.lower() == "general":
        return RelationshipVisualizer()
    elif visualization_type.lower() == "memory":
        return MemoryRelationshipVisualizer()
    elif visualization_type.lower() == "cognitive":
        return CognitiveProcessVisualizer()
    else:
        raise ValueError(f"Unknown visualization type: {visualization_type}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create a visualizer
    visualizer = create_default_visualizer("general")
    
    # Add some example nodes and edges
    visualizer.add_node("memory_1", NodeType.EPISODIC_MEMORY, "Recent conversation")
    visualizer.add_node("memory_2", NodeType.SEMANTIC_MEMORY, "General knowledge")
    visualizer.add_node("process_1", NodeType.COGNITIVE_PROCESS, "Reasoning process")
    visualizer.add_node("attention_1", NodeType.ATTENTION_MECHANISM, "Focus control")
    
    visualizer.add_edge("memory_1", "memory_2", EdgeType.REFERENCES, 0.8)
    visualizer.add_edge("process_1", "memory_1", EdgeType.DEPENDS_ON, 1.2)
    visualizer.add_edge("attention_1", "process_1", EdgeType.TRIGGERS, 1.0)
    visualizer.add_edge("attention_1", "memory_1", EdgeType.STRENGTHENS, 0.5)
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        output_path = tmp.name
    
    # Render the visualization
    try:
        visualizer.render(output_path)
        print(f"Visualization saved to {output_path}")
    except VisualizationError as e:
        print(f"Visualization error: {e}")
        # Fall back to JSON export if visualization libraries are not available
        json_path = output_path.replace(".html", ".json")
        visualizer.export_json(json_path)
        print(f"Visualization data exported to {json_path}")