"""
Memory Visualizer for NeuroCognitive Architecture (NCA)

This module provides visualization tools for the three-tiered memory system in the NCA.
It enables developers and researchers to visualize memory structures, relationships,
and dynamics for debugging, analysis, and presentation purposes.

The visualizer supports multiple output formats and visualization types:
- Memory structure graphs
- Memory usage heatmaps
- Memory access patterns
- Memory relationship networks
- Time-series memory state changes

Usage examples:
    # Create a visualizer for a specific memory system
    visualizer = MemoryVisualizer(memory_system)
    
    # Generate a structure graph
    visualizer.create_structure_graph(output_path="memory_structure.png")
    
    # Generate a heatmap of memory usage
    visualizer.create_usage_heatmap(output_path="memory_usage.png")
    
    # Visualize memory access patterns over time
    visualizer.create_access_pattern_visualization(
        time_range=(start_time, end_time),
        output_path="access_patterns.html"
    )
"""

import logging
import os
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional, Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from plotly import graph_objects as go

# Configure logging
logger = logging.getLogger(__name__)


class VisualizationFormat(Enum):
    """Supported visualization output formats."""
    PNG = auto()
    JPG = auto()
    SVG = auto()
    HTML = auto()
    PDF = auto()


class VisualizationType(Enum):
    """Types of memory visualizations available."""
    STRUCTURE = auto()  # Memory structure visualization
    USAGE = auto()      # Memory usage patterns
    ACCESS = auto()     # Memory access patterns
    NETWORK = auto()    # Memory relationship network
    TIMELINE = auto()   # Time-series memory state changes


class MemoryVisualizer:
    """
    Visualizer for the NCA memory system.
    
    This class provides methods to visualize different aspects of the memory system,
    including structure, usage patterns, access patterns, and relationships between
    memory components.
    
    Attributes:
        memory_system: The memory system to visualize
        default_output_dir: Default directory for saving visualizations
        color_scheme: Color scheme for visualizations
    """
    
    def __init__(
        self, 
        memory_system: Any,
        default_output_dir: Optional[Union[str, Path]] = None,
        color_scheme: Optional[dict[str, str]] = None
    ):
        """
        Initialize the memory visualizer.
        
        Args:
            memory_system: The memory system to visualize
            default_output_dir: Default directory for saving visualizations.
                                If None, uses the current directory.
            color_scheme: Custom color scheme for visualizations.
                          If None, uses default color scheme.
        
        Raises:
            ValueError: If memory_system is None or invalid
            OSError: If default_output_dir is not writable
        """
        if memory_system is None:
            raise ValueError("Memory system cannot be None")
        
        self.memory_system = memory_system
        
        # Set default output directory
        if default_output_dir is None:
            self.default_output_dir = Path.cwd() / "visualizations"
        else:
            self.default_output_dir = Path(default_output_dir)
        
        # Create output directory if it doesn't exist
        try:
            self.default_output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create output directory: {e}")
            raise OSError(f"Cannot create output directory {self.default_output_dir}: {e}")
        
        # Verify output directory is writable
        if not os.access(self.default_output_dir, os.W_OK):
            raise OSError(f"Output directory {self.default_output_dir} is not writable")
        
        # Set color scheme
        self.color_scheme = color_scheme or {
            "working_memory": "#FF5733",  # Orange-red
            "episodic_memory": "#33A8FF",  # Blue
            "semantic_memory": "#33FF57",  # Green
            "background": "#F8F9FA",      # Light gray
            "text": "#212529",            # Dark gray
            "highlight": "#FFC107",       # Yellow
            "connection": "#6C757D"       # Gray
        }
        
        logger.info(f"Initialized MemoryVisualizer with output directory: {self.default_output_dir}")

    def _get_output_path(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Get the full output path for a visualization.
        
        Args:
            output_path: Specific output path. If None, generates a timestamped path
                         in the default output directory.
        
        Returns:
            Path object representing the full output path
        
        Raises:
            ValueError: If the output path is invalid
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return self.default_output_dir / f"memory_viz_{timestamp}.png"
        
        path = Path(output_path)
        
        # If path is just a filename, put it in the default directory
        if not path.is_absolute() and len(path.parts) == 1:
            path = self.default_output_dir / path
        
        # Create parent directories if they don't exist
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create parent directories for output path: {e}")
            raise ValueError(f"Cannot create parent directories for {path}: {e}")
        
        return path

    def _validate_format(self, output_path: Path) -> VisualizationFormat:
        """
        Validate and determine the output format based on file extension.
        
        Args:
            output_path: Path to the output file
        
        Returns:
            VisualizationFormat enum value
        
        Raises:
            ValueError: If the file extension is not supported
        """
        extension = output_path.suffix.lower()
        
        format_map = {
            ".png": VisualizationFormat.PNG,
            ".jpg": VisualizationFormat.JPG, 
            ".jpeg": VisualizationFormat.JPG,
            ".svg": VisualizationFormat.SVG,
            ".html": VisualizationFormat.HTML,
            ".pdf": VisualizationFormat.PDF
        }
        
        if extension not in format_map:
            supported = ", ".join(format_map.keys())
            raise ValueError(
                f"Unsupported file extension: {extension}. "
                f"Supported extensions are: {supported}"
            )
        
        return format_map[extension]

    def _save_figure(self, fig: Figure, output_path: Path, format_type: VisualizationFormat) -> None:
        """
        Save a matplotlib figure to the specified output path.
        
        Args:
            fig: Matplotlib figure to save
            output_path: Path to save the figure to
            format_type: Format to save the figure in
        
        Raises:
            IOError: If saving the figure fails
        """
        try:
            if format_type == VisualizationFormat.PNG:
                fig.savefig(output_path, format='png', dpi=300, bbox_inches='tight')
            elif format_type == VisualizationFormat.JPG:
                fig.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight', quality=95)
            elif format_type == VisualizationFormat.SVG:
                fig.savefig(output_path, format='svg', bbox_inches='tight')
            elif format_type == VisualizationFormat.PDF:
                fig.savefig(output_path, format='pdf', bbox_inches='tight')
            else:
                raise ValueError(f"Unsupported format for matplotlib: {format_type}")
                
            logger.info(f"Saved visualization to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save figure: {e}")
            raise OSError(f"Failed to save figure to {output_path}: {e}")

    def create_structure_graph(
        self, 
        output_path: Optional[Union[str, Path]] = None,
        include_connections: bool = True,
        highlight_nodes: Optional[list[str]] = None
    ) -> Path:
        """
        Create a graph visualization of the memory structure.
        
        Args:
            output_path: Path to save the visualization to.
                         If None, uses a timestamped filename in the default directory.
            include_connections: Whether to include connections between memory components
            highlight_nodes: List of node IDs to highlight in the visualization
        
        Returns:
            Path where the visualization was saved
        
        Raises:
            ValueError: If the output format is not supported
            IOError: If saving the visualization fails
        """
        logger.info("Creating memory structure graph visualization")
        
        # Get full output path
        full_path = self._get_output_path(output_path)
        format_type = self._validate_format(full_path)
        
        try:
            # Extract memory structure from the memory system
            # This is a placeholder - actual implementation would depend on the memory system API
            memory_structure = self._extract_memory_structure()
            
            # Create graph
            G = nx.DiGraph()
            
            # Add nodes for each memory component
            for component_id, component_data in memory_structure["components"].items():
                G.add_node(
                    component_id,
                    type=component_data["type"],
                    size=component_data["size"],
                    label=component_data["name"]
                )
            
            # Add edges for connections between components
            if include_connections:
                for connection in memory_structure["connections"]:
                    G.add_edge(
                        connection["source"],
                        connection["target"],
                        weight=connection.get("weight", 1.0),
                        type=connection.get("type", "default")
                    )
            
            # Create visualization
            plt.figure(figsize=(12, 10))
            
            # Define node colors based on memory type
            node_colors = [
                self.color_scheme[G.nodes[node]["type"]] 
                if G.nodes[node]["type"] in self.color_scheme 
                else self.color_scheme["highlight"]
                for node in G.nodes
            ]
            
            # Highlight specific nodes if requested
            if highlight_nodes:
                for i, node in enumerate(G.nodes):
                    if node in highlight_nodes:
                        node_colors[i] = self.color_scheme["highlight"]
            
            # Define node sizes based on memory size
            node_sizes = [
                100 + 50 * G.nodes[node]["size"] for node in G.nodes
            ]
            
            # Create layout
            pos = nx.spring_layout(G, seed=42)
            
            # Draw nodes
            nx.draw_networkx_nodes(
                G, pos,
                node_color=node_colors,
                node_size=node_sizes,
                alpha=0.8,
                edgecolors=self.color_scheme["text"],
                linewidths=0.5
            )
            
            # Draw edges
            if include_connections:
                nx.draw_networkx_edges(
                    G, pos,
                    edge_color=self.color_scheme["connection"],
                    width=1.0,
                    alpha=0.6,
                    arrowsize=15,
                    arrowstyle='->'
                )
            
            # Draw labels
            nx.draw_networkx_labels(
                G, pos,
                font_size=10,
                font_family="sans-serif",
                font_color=self.color_scheme["text"]
            )
            
            # Add title and legend
            plt.title("Memory Structure Visualization", fontsize=16)
            
            # Create legend
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=self.color_scheme[mem_type], 
                          markersize=10, label=mem_type.replace('_', ' ').title())
                for mem_type in ["working_memory", "episodic_memory", "semantic_memory"]
            ]
            
            if highlight_nodes:
                legend_elements.append(
                    plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor=self.color_scheme["highlight"], 
                              markersize=10, label="Highlighted")
                )
            
            plt.legend(handles=legend_elements, loc="upper right")
            
            # Remove axis
            plt.axis('off')
            
            # Set background color
            plt.gca().set_facecolor(self.color_scheme["background"])
            
            # Save figure
            self._save_figure(plt.gcf(), full_path, format_type)
            plt.close()
            
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to create structure graph: {e}")
            raise ValueError(f"Failed to create structure graph: {e}")

    def create_usage_heatmap(
        self, 
        output_path: Optional[Union[str, Path]] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        memory_types: Optional[list[str]] = None
    ) -> Path:
        """
        Create a heatmap visualization of memory usage.
        
        Args:
            output_path: Path to save the visualization to.
                         If None, uses a timestamped filename in the default directory.
            time_range: Tuple of (start_time, end_time) to visualize.
                        If None, uses all available data.
            memory_types: List of memory types to include in the visualization.
                          If None, includes all memory types.
        
        Returns:
            Path where the visualization was saved
        
        Raises:
            ValueError: If the output format is not supported
            IOError: If saving the visualization fails
        """
        logger.info("Creating memory usage heatmap visualization")
        
        # Get full output path
        full_path = self._get_output_path(output_path)
        format_type = self._validate_format(full_path)
        
        try:
            # Extract memory usage data from the memory system
            # This is a placeholder - actual implementation would depend on the memory system API
            usage_data = self._extract_memory_usage(time_range, memory_types)
            
            # Create DataFrame for the heatmap
            df = pd.DataFrame(usage_data)
            
            # Create heatmap
            plt.figure(figsize=(14, 10))
            
            # Set seaborn style
            sns.set(style="whitegrid")
            
            # Create heatmap
            sns.heatmap(
                df.pivot("component", "time", "usage"),
                cmap="YlOrRd",
                linewidths=0.5,
                linecolor=self.color_scheme["text"],
                cbar_kws={'label': 'Usage (%)'}
            )
            
            # Set title and labels
            plt.title("Memory Usage Heatmap", fontsize=16)
            plt.xlabel("Time", fontsize=12)
            plt.ylabel("Memory Component", fontsize=12)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha="right")
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure
            self._save_figure(plt.gcf(), full_path, format_type)
            plt.close()
            
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to create usage heatmap: {e}")
            raise ValueError(f"Failed to create usage heatmap: {e}")

    def create_access_pattern_visualization(
        self, 
        output_path: Optional[Union[str, Path]] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        memory_components: Optional[list[str]] = None,
        interactive: bool = True
    ) -> Path:
        """
        Create a visualization of memory access patterns over time.
        
        Args:
            output_path: Path to save the visualization to.
                         If None, uses a timestamped filename in the default directory.
            time_range: Tuple of (start_time, end_time) to visualize.
                        If None, uses all available data.
            memory_components: List of memory components to include in the visualization.
                               If None, includes all components.
            interactive: Whether to create an interactive visualization (HTML) or static image
        
        Returns:
            Path where the visualization was saved
        
        Raises:
            ValueError: If the output format is not supported
            IOError: If saving the visualization fails
        """
        logger.info("Creating memory access pattern visualization")
        
        # Get full output path
        full_path = self._get_output_path(output_path)
        format_type = self._validate_format(full_path)
        
        # If interactive is True, force HTML format
        if interactive and format_type != VisualizationFormat.HTML:
            logger.warning(
                f"Interactive visualization requested but output format is {format_type}. "
                f"Changing output path to HTML format."
            )
            full_path = full_path.with_suffix(".html")
            format_type = VisualizationFormat.HTML
        
        try:
            # Extract memory access data from the memory system
            # This is a placeholder - actual implementation would depend on the memory system API
            access_data = self._extract_memory_access_patterns(time_range, memory_components)
            
            if interactive and format_type == VisualizationFormat.HTML:
                # Create interactive visualization with Plotly
                fig = go.Figure()
                
                # Add traces for each memory component
                for component, data in access_data.items():
                    fig.add_trace(go.Scatter(
                        x=data["times"],
                        y=data["access_counts"],
                        mode='lines+markers',
                        name=component,
                        hovertemplate='Time: %{x}<br>Accesses: %{y}<extra></extra>'
                    ))
                
                # Update layout
                fig.update_layout(
                    title="Memory Access Patterns Over Time",
                    xaxis_title="Time",
                    yaxis_title="Access Count",
                    hovermode="closest",
                    legend_title="Memory Components",
                    template="plotly_white"
                )
                
                # Save as HTML
                fig.write_html(
                    full_path,
                    include_plotlyjs="cdn",
                    full_html=True
                )
                
            else:
                # Create static visualization with Matplotlib
                plt.figure(figsize=(14, 8))
                
                # Plot access patterns for each component
                for component, data in access_data.items():
                    plt.plot(
                        data["times"],
                        data["access_counts"],
                        marker='o',
                        linestyle='-',
                        label=component
                    )
                
                # Set title and labels
                plt.title("Memory Access Patterns Over Time", fontsize=16)
                plt.xlabel("Time", fontsize=12)
                plt.ylabel("Access Count", fontsize=12)
                
                # Add legend
                plt.legend(title="Memory Components")
                
                # Add grid
                plt.grid(True, linestyle='--', alpha=0.7)
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha="right")
                
                # Adjust layout
                plt.tight_layout()
                
                # Save figure
                self._save_figure(plt.gcf(), full_path, format_type)
                plt.close()
            
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to create access pattern visualization: {e}")
            raise ValueError(f"Failed to create access pattern visualization: {e}")

    def create_memory_network_visualization(
        self, 
        output_path: Optional[Union[str, Path]] = None,
        focus_component: Optional[str] = None,
        depth: int = 2,
        include_weights: bool = True
    ) -> Path:
        """
        Create a network visualization of memory relationships.
        
        Args:
            output_path: Path to save the visualization to.
                         If None, uses a timestamped filename in the default directory.
            focus_component: ID of the component to focus on. If None, shows the entire network.
            depth: Number of relationship levels to include from the focus component
            include_weights: Whether to visualize relationship weights
        
        Returns:
            Path where the visualization was saved
        
        Raises:
            ValueError: If the output format is not supported or parameters are invalid
            IOError: If saving the visualization fails
        """
        logger.info("Creating memory relationship network visualization")
        
        if depth < 1:
            raise ValueError("Depth must be at least 1")
        
        # Get full output path
        full_path = self._get_output_path(output_path)
        format_type = self._validate_format(full_path)
        
        try:
            # Extract memory relationship data from the memory system
            # This is a placeholder - actual implementation would depend on the memory system API
            relationship_data = self._extract_memory_relationships(focus_component, depth)
            
            # Create graph
            G = nx.Graph()
            
            # Add nodes
            for node_id, node_data in relationship_data["nodes"].items():
                G.add_node(
                    node_id,
                    type=node_data["type"],
                    label=node_data["label"],
                    importance=node_data.get("importance", 1.0)
                )
            
            # Add edges
            for edge in relationship_data["edges"]:
                G.add_edge(
                    edge["source"],
                    edge["target"],
                    weight=edge.get("weight", 1.0),
                    type=edge.get("type", "default")
                )
            
            # Create visualization
            plt.figure(figsize=(16, 12))
            
            # Define node colors based on memory type
            node_colors = [
                self.color_scheme[G.nodes[node]["type"]] 
                if G.nodes[node]["type"] in self.color_scheme 
                else "#999999"  # Default gray
                for node in G.nodes
            ]
            
            # Define node sizes based on importance
            node_sizes = [
                300 * G.nodes[node].get("importance", 1.0) for node in G.nodes
            ]
            
            # Highlight focus component if specified
            if focus_component and focus_component in G.nodes:
                idx = list(G.nodes).index(focus_component)
                node_colors[idx] = self.color_scheme["highlight"]
                node_sizes[idx] *= 1.5  # Make focus node larger
            
            # Create layout - use force-directed layout for network visualization
            pos = nx.spring_layout(G, k=0.3, iterations=50, seed=42)
            
            # Draw edges with varying width based on weight if requested
            if include_weights:
                edge_widths = [G[u][v].get("weight", 1.0) * 2 for u, v in G.edges()]
                nx.draw_networkx_edges(
                    G, pos,
                    width=edge_widths,
                    alpha=0.6,
                    edge_color=self.color_scheme["connection"]
                )
            else:
                nx.draw_networkx_edges(
                    G, pos,
                    width=1.0,
                    alpha=0.6,
                    edge_color=self.color_scheme["connection"]
                )
            
            # Draw nodes
            nx.draw_networkx_nodes(
                G, pos,
                node_color=node_colors,
                node_size=node_sizes,
                alpha=0.8,
                edgecolors=self.color_scheme["text"],
                linewidths=0.5
            )
            
            # Draw labels
            nx.draw_networkx_labels(
                G, pos,
                font_size=10,
                font_family="sans-serif",
                font_color=self.color_scheme["text"]
            )
            
            # Add title
            title = "Memory Relationship Network"
            if focus_component:
                focus_label = relationship_data["nodes"][focus_component]["label"]
                title += f" (Focused on: {focus_label})"
            plt.title(title, fontsize=16)
            
            # Create legend
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=self.color_scheme[mem_type], 
                          markersize=10, label=mem_type.replace('_', ' ').title())
                for mem_type in ["working_memory", "episodic_memory", "semantic_memory"]
            ]
            
            if focus_component:
                legend_elements.append(
                    plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor=self.color_scheme["highlight"], 
                              markersize=10, label="Focus Component")
                )
            
            plt.legend(handles=legend_elements, loc="upper right")
            
            # Remove axis
            plt.axis('off')
            
            # Set background color
            plt.gca().set_facecolor(self.color_scheme["background"])
            
            # Save figure
            self._save_figure(plt.gcf(), full_path, format_type)
            plt.close()
            
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to create memory network visualization: {e}")
            raise ValueError(f"Failed to create memory network visualization: {e}")

    def create_memory_timeline(
        self, 
        output_path: Optional[Union[str, Path]] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        memory_components: Optional[list[str]] = None,
        event_types: Optional[list[str]] = None,
        interactive: bool = True
    ) -> Path:
        """
        Create a timeline visualization of memory events and state changes.
        
        Args:
            output_path: Path to save the visualization to.
                         If None, uses a timestamped filename in the default directory.
            time_range: Tuple of (start_time, end_time) to visualize.
                        If None, uses all available data.
            memory_components: List of memory components to include in the visualization.
                               If None, includes all components.
            event_types: List of event types to include in the visualization.
                         If None, includes all event types.
            interactive: Whether to create an interactive visualization (HTML) or static image
        
        Returns:
            Path where the visualization was saved
        
        Raises:
            ValueError: If the output format is not supported
            IOError: If saving the visualization fails
        """
        logger.info("Creating memory timeline visualization")
        
        # Get full output path
        full_path = self._get_output_path(output_path)
        format_type = self._validate_format(full_path)
        
        # If interactive is True, force HTML format
        if interactive and format_type != VisualizationFormat.HTML:
            logger.warning(
                f"Interactive visualization requested but output format is {format_type}. "
                f"Changing output path to HTML format."
            )
            full_path = full_path.with_suffix(".html")
            format_type = VisualizationFormat.HTML
        
        try:
            # Extract memory timeline data from the memory system
            # This is a placeholder - actual implementation would depend on the memory system API
            timeline_data = self._extract_memory_timeline(time_range, memory_components, event_types)
            
            if interactive and format_type == VisualizationFormat.HTML:
                # Create interactive timeline with Plotly
                fig = go.Figure()
                
                # Add events for each component
                for component, events in timeline_data.items():
                    fig.add_trace(go.Scatter(
                        x=events["times"],
                        y=[component] * len(events["times"]),
                        mode='markers',
                        name=component,
                        marker={
                            "symbol": 'circle',
                            "size": 12,
                            "color": [self.color_scheme.get(event_type, "#999999") 
                                  for event_type in events["types"]]
                        },
                        text=events["descriptions"],
                        hovertemplate='%{text}<br>Time: %{x}<extra></extra>'
                    ))
                
                # Update layout
                fig.update_layout(
                    title="Memory System Timeline",
                    xaxis_title="Time",
                    yaxis_title="Memory Component",
                    hovermode="closest",
                    height=600,
                    template="plotly_white"
                )
                
                # Save as HTML
                fig.write_html(
                    full_path,
                    include_plotlyjs="cdn",
                    full_html=True
                )
                
            else:
                # Create static timeline with Matplotlib
                plt.figure(figsize=(16, 10))
                
                # Get all unique components
                components = list(timeline_data.keys())
                
                # Create y-positions for each component
                y_positions = {comp: i for i, comp in enumerate(components)}
                
                # Plot events for each component
                for component, events in timeline_data.items():
                    y_pos = y_positions[component]
                    
                    # Plot events as markers
                    for i, (time, event_type, desc) in enumerate(zip(
                        events["times"], events["types"], events["descriptions"]
                    )):
                        color = self.color_scheme.get(event_type, "#999999")
                        plt.scatter(time, y_pos, c=color, s=100, zorder=2)
                        
                        # Add annotation for important events
                        if events.get("importance", [1.0] * len(events["times"]))[i] > 1.5:
                            plt.annotate(
                                desc,
                                (time, y_pos),
                                xytext=(0, 10),
                                textcoords="offset points",
                                ha="center",
                                fontsize=8,
                                bbox={
                                    "boxstyle": "round,pad=0.3",
                                    "fc": "white",
                                    "alpha": 0.8
                                }
                            )
                
                # Set y-ticks to component names
                plt.yticks(list(y_positions.values()), list(y_positions.keys()))
                
                # Set title and labels
                plt.title("Memory System Timeline", fontsize=16)
                plt.xlabel("Time", fontsize=12)
                plt.ylabel("Memory Component", fontsize=12)
                
                # Add grid lines
                plt.grid(True, axis='x', linestyle='--', alpha=0.7)
                
                # Create legend for event types
                event_types = set()
                for events in timeline_data.values():
                    event_types.update(events["types"])
                
                legend_elements = [
                    plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor=self.color_scheme.get(event_type, "#999999"), 
                              markersize=10, label=event_type.replace('_', ' ').title())
                    for event_type in event_types
                ]
                
                plt.legend(handles=legend_elements, loc="upper right")
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha="right")
                
                # Adjust layout
                plt.tight_layout()
                
                # Save figure
                self._save_figure(plt.gcf(), full_path, format_type)
                plt.close()
            
            return full_path
            
        except Exception as e:
            logger.error(f"Failed to create memory timeline visualization: {e}")
            raise ValueError(f"Failed to create memory timeline visualization: {e}")

    def _extract_memory_structure(self) -> dict[str, Any]:
        """
        Extract memory structure data from the memory system.
        
        Returns:
            Dictionary containing memory structure data
        
        Note:
            This is a placeholder implementation. The actual implementation
            would depend on the memory system API.
        """
        logger.debug("Extracting memory structure data")
        
        try:
            # Placeholder implementation - in a real system, this would
            # extract actual data from the memory system
            
            # Example structure data
            structure_data = {
                "components": {
                    "wm_1": {
                        "type": "working_memory",
                        "name": "Working Memory",
                        "size": 3
                    },
                    "em_1": {
                        "type": "episodic_memory",
                        "name": "Recent Episodes",
                        "size": 5
                    },
                    "em_2": {
                        "type": "episodic_memory",
                        "name": "Long-term Episodes",
                        "size": 8
                    },
                    "sm_1": {
                        "type": "semantic_memory",
                        "name": "Semantic Network",
                        "size": 10
                    }
                },
                "connections": [
                    {"source": "wm_1", "target": "em_1", "weight": 1.0, "type": "encoding"},
                    {"source": "em_1", "target": "em_2", "weight": 0.7, "type": "consolidation"},
                    {"source": "em_1", "target": "sm_1", "weight": 0.5, "type": "abstraction"},
                    {"source": "em_2", "target": "sm_1", "weight": 0.8, "type": "abstraction"},
                    {"source": "sm_1", "target": "wm_1", "weight": 0.6, "type": "recall"}
                ]
            }
            
            return structure_data
            
        except Exception as e:
            logger.error(f"Failed to extract memory structure: {e}")
            # Return minimal structure to avoid visualization failure
            return {"components": {}, "connections": []}

    def _extract_memory_usage(
        self, 
        time_range: Optional[tuple[datetime, datetime]] = None,
        memory_types: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """
        Extract memory usage data from the memory system.
        
        Args:
            time_range: Tuple of (start_time, end_time) to extract data for
            memory_types: List of memory types to include
        
        Returns:
            List of dictionaries containing memory usage data
        
        Note:
            This is a placeholder implementation. The actual implementation
            would depend on the memory system API.
        """
        logger.debug("Extracting memory usage data")
        
        try:
            # Placeholder implementation - in a real system, this would
            # extract actual data from the memory system
            
            # Generate example time points
            now = datetime.now()
            times = [now - pd.Timedelta(minutes=i*10) for i in range(10)]
            times.reverse()  # Oldest to newest
            
            # Format times for display
            time_strs = [t.strftime("%H:%M:%S") for t in times]
            
            # Example components
            components = [
                "Working Memory",
                "Recent Episodes",
                "Long-term Episodes",
                "Semantic Network"
            ]
            
            # Filter by memory types if specified
            if memory_types:
                # This is a simplistic filter - real implementation would be more sophisticated
                filtered_components = []
                for comp in components:
                    for mem_type in memory_types:
                        if mem_type.lower() in comp.lower():
                            filtered_components.append(comp)
                            break
                components = filtered_components
            
            # Generate example usage data
            usage_data = []
            
            for component in components:
                # Generate realistic usage patterns
                if "Working" in component:
                    # Working memory tends to fluctuate rapidly
                    base = 60
                    variation = 30
                elif "Recent" in component:
                    # Recent episodic memory grows steadily then resets
                    base = 40
                    variation = 20
                elif "Long-term" in component:
                    # Long-term memory grows slowly but steadily
                    base = 20
                    variation = 10
                else:
                    # Semantic memory is most stable
                    base = 30
                    variation = 5
                
                for i, time_str in enumerate(time_strs):
                    # Create realistic patterns
                    if "Working" in component:
                        # Fluctuating pattern
                        usage = base + variation * np.sin(i * 0.8)
                    elif "Recent" in component:
                        # Sawtooth pattern (fills up then clears)
                        usage = base + (i % 5) * (variation / 2)
                    elif "Long-term" in component:
                        # Gradually increasing
                        usage = base + min(i * 3, variation)
                    else:
                        # Stable with slight increase
                        usage = base + i * 0.5
                    
                    # Add random noise
                    usage += np.random.normal(0, 3)
                    
                    # Ensure usage is between 0 and 100
                    usage = max(0, min(100, usage))
                    
                    usage_data.append({
                        "component": component,
                        "time": time_str,
                        "usage": usage
                    })
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Failed to extract memory usage data: {e}")
            # Return minimal data to avoid visualization failure
            return [{"component": "Unknown", "time": "00:00:00", "usage": 0}]

    def _extract_memory_access_patterns(
        self, 
        time_range: Optional[tuple[datetime, datetime]] = None,
        memory_components: Optional[list[str]] = None
    ) -> dict[str, dict[str, list[Any]]]:
        """
        Extract memory access pattern data from the memory system.
        
        Args:
            time_range: Tuple of (start_time, end_time) to extract data for
            memory_components: List of memory components to include
        
        Returns:
            Dictionary mapping component names to access pattern data
        
        Note:
            This is a placeholder implementation. The actual implementation
            would depend on the memory system API.
        """
        logger.debug("Extracting memory access pattern data")
        
        try:
            # Placeholder implementation - in a real system, this would
            # extract actual data from the memory system
            
            # Generate example time points
            now = datetime.now()
            times = [now - pd.Timedelta(minutes=i*5) for i in range(20)]
            times.reverse()  # Oldest to newest
            
            # Example components
            components = {
                "Working Memory": {"pattern": "volatile", "base": 15, "amplitude": 10},
                "Recent Episodes": {"pattern": "increasing", "base": 5, "amplitude": 8},
                "Long-term Episodes": {"pattern": "stable", "base": 2, "amplitude": 3},
                "Semantic Network": {"pattern": "periodic", "base": 8, "amplitude": 5}
            }
            
            # Filter by memory components if specified
            if memory_components:
                components = {k: v for k, v in components.items() if k in memory_components}
            
            # Generate example access pattern data
            access_data = {}
            
            for component, params in components.items():
                pattern = params["pattern"]
                base = params["base"]
                amplitude = params["amplitude"]
                
                access_counts = []
                
                for i in range(len(times)):
                    if pattern == "volatile":
                        # Highly variable access pattern
                        count = base + amplitude * np.random.random()
                    elif pattern == "increasing":
                        # Gradually increasing access pattern
                        count = base + (i / len(times)) * amplitude
                    elif pattern == "stable":
                        # Stable access pattern with small variations
                        count = base + np.random.normal(0, amplitude / 3)
                    elif pattern == "periodic":
                        # Periodic access pattern
                        count = base + amplitude * np.sin(i * np.pi / 5)
                    else:
                        count = base
                    
                    # Add random noise and ensure count is non-negative
                    count = max(0, count + np.random.normal(0, 1))
                    access_counts.append(int(count))
                
                access_data[component] = {
                    "times": times,
                    "access_counts": access_counts
                }
            
            return access_data
            
        except Exception as e:
            logger.error(f"Failed to extract memory access pattern data: {e}")
            # Return minimal data to avoid visualization failure
            now = datetime.now()
            return {"Unknown": {"times": [now], "access_counts": [0]}}

    def _extract_memory_relationships(
        self, 
        focus_component: Optional[str] = None,
        depth: int = 2
    ) -> dict[str, Any]:
        """
        Extract memory relationship data from the memory system.
        
        Args:
            focus_component: ID of the component to focus on
            depth: Number of relationship levels to include
        
        Returns:
            Dictionary containing memory relationship data
        
        Note:
            This is a placeholder implementation. The actual implementation
            would depend on the memory system API.
        """
        logger.debug("Extracting memory relationship data")
        
        try:
            # Placeholder implementation - in a real system, this would
            # extract actual data from the memory system
            
            # Example nodes
            nodes = {
                "wm_1": {"type": "working_memory", "label": "Working Memory", "importance": 1.5},
                "em_1": {"type": "episodic_memory", "label": "Recent Episodes", "importance": 1.2},
                "em_2": {"type": "episodic_memory", "label": "Long-term Episodes", "importance": 1.0},
                "sm_1": {"type": "semantic_memory", "label": "General Knowledge", "importance": 1.3},
                "sm_2": {"type": "semantic_memory", "label": "Domain Knowledge", "importance": 0.8},
                "em_3": {"type": "episodic_memory", "label": "Procedural Memory", "importance": 0.7},
                "wm_2": {"type": "working_memory", "label": "Attention Buffer", "importance": 1.1}
            }
            
            # Example edges
            all_edges = [
                {"source": "wm_1", "target": "em_1", "weight": 0.9, "type": "encoding"},
                {"source": "em_1", "target": "em_2", "weight": 0.7, "type": "consolidation"},
                {"source": "em_1", "target": "sm_1", "weight": 0.5, "type": "abstraction"},
                {"source": "em_2", "target": "sm_1", "weight": 0.8, "type": "abstraction"},
                {"source": "sm_1", "target": "wm_1", "weight": 0.6, "type": "recall"},
                {"source": "sm_1", "target": "sm_2", "weight": 0.4, "type": "association"},
                {"source": "wm_1", "target": "wm_2", "weight": 0.9, "type": "attention"},
                {"source": "wm_2", "target": "em_3", "weight": 0.5, "type": "procedural"},
                {"source": "em_3", "target": "sm_2", "weight": 0.3, "type": "learning"}
            ]
            
            # If focus component is specified, filter the network
            if focus_component and focus_component in nodes:
                # Start with the focus component
                included_nodes = {focus_component}
                
                # Add nodes up to the specified depth
                for _ in range(depth):
                    new_nodes = set()
                    for edge in all_edges:
                        if edge["source"] in included_nodes and edge["target"] not in included_nodes:
                            new_nodes.add(edge["target"])
                        elif edge["target"] in included_nodes and edge["source"] not in included_nodes:
                            new_nodes.add(edge["source"])
                    included_nodes.update(new_nodes)
                
                # Filter nodes and edges
                filtered_nodes = {k: v for k, v in nodes.items() if k in included_nodes}
                filtered_edges = [e for e in all_edges 
                                 if e["source"] in included_nodes and e["target"] in included_nodes]
                
                return {
                    "nodes": filtered_nodes,
                    "edges": filtered_edges
                }
            
            # Return all nodes and edges if no focus component
            return {
                "nodes": nodes,
                "edges": all_edges
            }
            
        except Exception as e:
            logger.error(f"Failed to extract memory relationship data: {e}")
            # Return minimal data to avoid visualization failure
            return {"nodes": {}, "edges": []}

    def _extract_memory_timeline(
        self, 
        time_range: Optional[tuple[datetime, datetime]] = None,
        memory_components: Optional[list[str]] = None,
        event_types: Optional[list[str]] = None
    ) -> dict[str, dict[str, list[Any]]]:
        """
        Extract memory timeline data from the memory system.
        
        Args:
            time_range: Tuple of (start_time, end_time) to extract data for
            memory_components: List of memory components to include
            event_types: List of event types to include
        
        Returns:
            Dictionary mapping component names to timeline data
        
        Note:
            This is a placeholder implementation. The actual implementation
            would depend on the memory system API.
        """
        logger.debug("Extracting memory timeline data")
        
        try:
            # Placeholder implementation - in a real system, this would
            # extract actual data from the memory system
            
            # Generate example time points
            now = datetime.now()
            times = [now - pd.Timedelta(minutes=i*3) for i in range(30)]
            times.reverse()  # Oldest to newest
            
            # Example components and event types
            components = [
                "Working Memory",
                "Recent Episodes",
                "Long-term Episodes",
                "Semantic Network"
            ]
            
            all_event_types = [
                "working_memory",
                "episodic_memory",
                "semantic_memory",
                "encoding",
                "retrieval",
                "consolidation",
                "forgetting"
            ]
            
            # Filter by memory components if specified
            if memory_components:
                components = [c for c in components if c in memory_components]
            
            # Filter by event types if specified
            if event_types:
                filtered_event_types = [et for et in all_event_types if et in event_types]
                all_event_types = filtered_event_types if filtered_event_types else all_event_types
            
            # Generate example timeline data
            timeline_data = {}
            
            for component in components:
                # Number of events depends on component type
                if "Working" in component:
                    # Working memory has frequent events
                    num_events = 20
                elif "Recent" in component:
                    # Recent episodic memory has moderate events
                    num_events = 15
                elif "Long-term" in component:
                    # Long-term memory has fewer events
                    num_events = 8
                else:
                    # Semantic memory has fewest events
                    num_events = 5
                
                # Select random times for events
                event_indices = sorted(np.random.choice(
                    range(len(times)), size=min(num_events, len(times)), replace=False
                ))
                event_times = [times[i] for i in event_indices]
                
                # Generate event types and descriptions
                event_types_list = []
                event_descriptions = []
                event_importance = []
                
                for i, _ in enumerate(event_times):
                    # Select event type based on component
                    if "Working" in component:
                        likely_types = ["working_memory", "encoding", "retrieval"]
                    elif "Recent" in component:
                        likely_types = ["episodic_memory", "encoding", "consolidation"]
                    elif "Long-term" in component:
                        likely_types = ["episodic_memory", "consolidation", "forgetting"]
                    else:
                        likely_types = ["semantic_memory", "retrieval", "consolidation"]
                    
                    # Filter by available event types
                    available_types = [t for t in likely_types if t in all_event_types]
                    if not available_types:
                        available_types = all_event_types
                    
                    # Select random event type
                    event_type = np.random.choice(available_types)
                    event_types_list.append(event_type)
                    
                    # Generate description based on event type
                    if event_type == "working_memory":
                        desc = f"Working memory update: Item {i+1}"
                    elif event_type == "episodic_memory":
                        desc = f"Episodic memory formation: Event {i+1}"
                    elif event_type == "semantic_memory":
                        desc = f"Semantic knowledge update: Concept {i+1}"
                    elif event_type == "encoding":
                        desc = f"Encoding new information: Data {i+1}"
                    elif event_type == "retrieval":
                        desc = f"Information retrieval: Query {i+1}"
                    elif event_type == "consolidation":
                        desc = "Memory consolidation: Strengthening connections"
                    elif event_type == "forgetting":
                        desc = "Forgetting: Removing outdated information"
                    else:
                        desc = f"Memory event: {event_type}"
                    
                    event_descriptions.append(desc)
                    
                    # Assign importance (some events are more important)
                    if i % 5 == 0:  # Every 5th event is important
                        importance = 2.0
                    else:
                        importance = 1.0
                    event_importance.append(importance)
                
                timeline_data[component] = {
                    "times": event_times,
                    "types": event_types_list,
                    "descriptions": event_descriptions,
                    "importance": event_importance
                }
            
            return timeline_data
            
        except Exception as e:
            logger.error(f"Failed to extract memory timeline data: {e}")
            # Return minimal data to avoid visualization failure
            now = datetime.now()
            return {"Unknown": {"times": [now], "types": ["unknown"], "descriptions": ["Error"], "importance": [1.0]}}


def create_visualization(
    memory_system: Any,
    visualization_type: VisualizationType,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Path:
    """
    Convenience function to create a memory visualization.
    
    Args:
        memory_system: The memory system to visualize
        visualization_type: Type of visualization to create
        output_path: Path to save the visualization to
        **kwargs: Additional arguments for the specific visualization type
    
    Returns:
        Path where the visualization was saved
    
    Raises:
        ValueError: If the visualization type is not supported
        IOError: If saving the visualization fails
    
    Example:
        # Create a structure graph visualization
        path = create_visualization(
            memory_system,
            VisualizationType.STRUCTURE,
            output_path="memory_structure.png",
            include_connections=True
        )
    """
    visualizer = MemoryVisualizer(memory_system)
    
    if visualization_type == VisualizationType.STRUCTURE:
        return visualizer.create_structure_graph(output_path=output_path, **kwargs)
    elif visualization_type == VisualizationType.USAGE:
        return visualizer.create_usage_heatmap(output_path=output_path, **kwargs)
    elif visualization_type == VisualizationType.ACCESS:
        return visualizer.create_access_pattern_visualization(output_path=output_path, **kwargs)
    elif visualization_type == VisualizationType.NETWORK:
        return visualizer.create_memory_network_visualization(output_path=output_path, **kwargs)
    elif visualization_type == VisualizationType.TIMELINE:
        return visualizer.create_memory_timeline(output_path=output_path, **kwargs)
    else:
        raise ValueError(f"Unsupported visualization type: {visualization_type}")