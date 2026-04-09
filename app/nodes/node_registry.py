"""Node registry and definitions."""
from typing import Dict, List, Type
from .base_node import BaseNode


class DataSourceNode(BaseNode):
    """Data source node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Data Source", "data_source.png", "Data")
        self.add_output_port("data", "DataFrame")


class CSVFileNode(BaseNode):
    """CSV file input node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "CSV File", "csv_file.png", "Data")
        self.add_output_port("data", "DataFrame")


class SQLQueryNode(BaseNode):
    """SQL query node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "SQL Query", "sql_query.png", "Data")
        self.add_output_port("result", "DataFrame")


class RandomDataNode(BaseNode):
    """Random data generator node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Random Data", "random_data.png", "Data")
        self.add_output_port("data", "DataFrame")


class ExcelNode(BaseNode):
    """Excel file input node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Excel File", "excel_file.png", "Data")
        self.add_output_port("data", "DataFrame")


class FilterNode(BaseNode):
    """Data filter node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Filter", "filter.png", "Processing")
        self.add_input_port("data", "DataFrame")
        self.add_output_port("result", "DataFrame")


class AggregateNode(BaseNode):
    """Data aggregation node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Aggregate", "aggregate.png", "Processing")
        self.add_input_port("data", "DataFrame")
        self.add_output_port("result", "DataFrame")


class SortNode(BaseNode):
    """Data sort node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Sort", "sort.png", "Processing")
        self.add_input_port("data", "DataFrame")
        self.add_output_port("result", "DataFrame")


class GroupByNode(BaseNode):
    """Data grouping node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Group By", "group_by.png", "Processing")
        self.add_input_port("data", "DataFrame")
        self.add_output_port("result", "DataFrame")


class JoinNode(BaseNode):
    """Data join node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Join", "join.png", "Processing")
        self.add_input_port("data1", "DataFrame")
        self.add_input_port("data2", "DataFrame")
        self.add_output_port("result", "DataFrame")


class TableViewNode(BaseNode):
    """Table visualization node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Table View", "table_view.png", "Visualization")
        self.add_input_port("data", "DataFrame")


class ChartNode(BaseNode):
    """Chart visualization node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Chart", "chart.png", "Visualization")
        self.add_input_port("data", "DataFrame")


class ScatterPlotNode(BaseNode):
    """Scatter plot visualization node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Scatter Plot", "scatter_plot.png", "Visualization")
        self.add_input_port("data", "DataFrame")


class HistogramNode(BaseNode):
    """Histogram visualization node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Histogram", "histogram.png", "Visualization")
        self.add_input_port("data", "DataFrame")


class HeatmapNode(BaseNode):
    """Heatmap visualization node."""
    def __init__(self, node_id=None):
        super().__init__(node_id, "Heatmap", "heatmap.png", "Visualization")
        self.add_input_port("data", "DataFrame")


# Node registry
NODE_REGISTRY: Dict[str, Type[BaseNode]] = {
    # Data category
    'DataSource': DataSourceNode,
    'CSVFile': CSVFileNode,
    'SQLQuery': SQLQueryNode,
    'RandomData': RandomDataNode,
    'Excel': ExcelNode,
    
    # Processing category
    'Filter': FilterNode,
    'Aggregate': AggregateNode,
    'Sort': SortNode,
    'GroupBy': GroupByNode,
    'Join': JoinNode,
    
    # Visualization category
    'TableView': TableViewNode,
    'Chart': ChartNode,
    'ScatterPlot': ScatterPlotNode,
    'Histogram': HistogramNode,
    'Heatmap': HeatmapNode,
}


def get_nodes_by_category(category: str) -> List[str]:
    """Get all node types in a category."""
    return [
        node_type for node_type, node_class in NODE_REGISTRY.items()
        if node_class().__class__.__bases__[0].__name__ == 'BaseNode'
        and node_class().category == category
    ]


def get_categories() -> List[str]:
    """Get all node categories."""
    categories = set()
    for node_class in NODE_REGISTRY.values():
        categories.add(node_class().category)
    return sorted(list(categories))


def create_node(node_type: str) -> BaseNode:
    """Create a node by type."""
    if node_type in NODE_REGISTRY:
        return NODE_REGISTRY[node_type]()
    raise ValueError(f"Unknown node type: {node_type}")


def get_node_info(node_type: str) -> dict:
    """Get information about a node type."""
    node = create_node(node_type)
    return {
        'type': node_type,
        'title': node.title,
        'category': node.category,
        'input_ports': list(node.input_ports.keys()),
        'output_ports': list(node.output_ports.keys()),
    }
