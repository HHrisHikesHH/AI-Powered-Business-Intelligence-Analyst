"""
Visualization Agent.
Determines optimal chart types and generates Recharts configuration.
"""
from loguru import logger
from app.core.llm_client import llm_service, QueryComplexity
from typing import Dict, Any, List, Optional
import json


class VisualizationAgent:
    """Agent responsible for generating chart visualizations."""
    
    # Chart type mappings
    CHART_TYPES = {
        "line": "LineChart",
        "bar": "BarChart",
        "pie": "PieChart",
        "area": "AreaChart",
        "scatter": "ScatterChart",
        "composed": "ComposedChart"
    }
    
    def __init__(self):
        self.llm = llm_service
    
    async def generate_visualization(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        sql: str,
        results: List[Dict],
        analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate visualization configuration for query results.
        
        Args:
            query_understanding: Output from Query Understanding Agent
            natural_language_query: Original natural language query
            sql: Generated SQL query
            results: Query execution results
            analysis: Optional analysis output for context
        
        Returns:
            Dictionary with:
            - chart_type: Recommended chart type
            - chart_config: Recharts configuration object
            - data_key: Key to use for data values
            - category_key: Key to use for categories (if applicable)
            - title: Chart title
            - description: Chart description
        """
        try:
            logger.info(f"Generating visualization for {len(results)} result rows")
            
            if not results:
                return self._generate_empty_visualization()
            
            # Analyze data structure to determine chart type
            data_structure = self._analyze_data_structure(results, query_understanding)
            
            # Format prompt
            prompt = self._format_visualization_prompt(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                data_structure=data_structure,
                sample_data=results[:5],  # Sample first 5 rows
                analysis=analysis
            )
            
            # Use simple model for visualization (structured output, low cost)
            response = await self.llm.generate_completion(
                prompt=prompt,
                system_prompt="You are a Visualization Agent specialized in determining optimal chart types and generating Recharts configurations. Return only valid JSON.",
                temperature=0.2,  # Low temperature for consistent output
                max_tokens=1000,
                complexity=QueryComplexity.SIMPLE,  # Use simple model for visualization
                auto_select_model=True
            )
            
            # Parse JSON response
            try:
                visualization = self._parse_visualization_response(response)
                
                # Validate and enrich visualization config
                visualization = self._enrich_visualization_config(
                    visualization, results, query_understanding
                )
                
                logger.info(f"Visualization generated: {visualization.get('chart_type', 'unknown')}")
                return visualization
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse visualization response: {e}")
                logger.error(f"Response was: {response}")
                return self._generate_fallback_visualization(results, query_understanding)
                
        except Exception as e:
            logger.error(f"Error in visualization: {e}")
            return self._generate_fallback_visualization(results, query_understanding)
    
    def _analyze_data_structure(
        self,
        results: List[Dict],
        query_understanding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the data structure to inform chart type selection."""
        if not results:
            return {"type": "empty", "columns": []}
        
        columns = list(results[0].keys())
        
        # Identify column types
        numeric_columns = []
        categorical_columns = []
        date_columns = []
        
        for col in columns:
            sample_values = [row.get(col) for row in results[:10] if row.get(col) is not None]
            if not sample_values:
                continue
            
            # Check if numeric
            if all(isinstance(v, (int, float)) for v in sample_values):
                numeric_columns.append(col)
            # Check if date-like
            elif any(isinstance(v, str) and any(x in str(v).lower() for x in ['-', '/', '2024', '2023']) for v in sample_values):
                date_columns.append(col)
            else:
                categorical_columns.append(col)
        
        # Determine structure type
        aggregations = query_understanding.get("aggregations", [])
        has_group_by = len(query_understanding.get("group_by", [])) > 0
        has_order_by = query_understanding.get("order_by") is not None
        
        structure_type = "tabular"
        if has_group_by and aggregations:
            structure_type = "grouped_aggregation"
        elif aggregations and not has_group_by:
            structure_type = "single_aggregation"
        elif has_order_by:
            structure_type = "ordered_list"
        elif date_columns:
            structure_type = "time_series"
        
        return {
            "type": structure_type,
            "columns": columns,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "date_columns": date_columns,
            "row_count": len(results),
            "has_aggregations": len(aggregations) > 0,
            "has_group_by": has_group_by,
            "has_order_by": has_order_by
        }
    
    def _format_visualization_prompt(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        sql: str,
        data_structure: Dict[str, Any],
        sample_data: List[Dict],
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format the visualization prompt."""
        intent = query_understanding.get("intent", "")
        aggregations = query_understanding.get("aggregations", [])
        group_by = query_understanding.get("group_by", [])
        
        prompt = f"""Determine the optimal chart type and generate Recharts configuration for the following query results.

Original Query: {natural_language_query}
Query Intent: {intent}
SQL Query: {sql}

Data Structure:
- Type: {data_structure['type']}
- Columns: {', '.join(data_structure['columns'])}
- Numeric Columns: {', '.join(data_structure.get('numeric_columns', []))}
- Categorical Columns: {', '.join(data_structure.get('categorical_columns', []))}
- Row Count: {data_structure['row_count']}
- Has Aggregations: {data_structure.get('has_aggregations', False)}
- Has GROUP BY: {data_structure.get('has_group_by', False)}

Sample Data (first {len(sample_data)} rows):
{json.dumps(sample_data, indent=2, default=str)}

Analysis Context:
{json.dumps(analysis, indent=2) if analysis else "No analysis available"}

Chart Type Selection Rules:
1. Single aggregation (COUNT, SUM, AVG) without GROUP BY → BarChart or PieChart
2. GROUP BY with aggregation → BarChart (categorical) or LineChart (if time-based)
3. Time-series data → LineChart or AreaChart
4. Ordered list → BarChart (horizontal) or LineChart
5. Comparison across categories → BarChart
6. Distribution → PieChart or BarChart
7. Multiple metrics → ComposedChart

Recharts Configuration Format:
{{
    "chart_type": "line|bar|pie|area|scatter|composed",
    "data_key": "column_name_for_values",
    "category_key": "column_name_for_categories",
    "title": "Chart Title",
    "description": "Chart description",
    "x_axis_label": "X-axis label",
    "y_axis_label": "Y-axis label",
    "colors": ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#8dd1e1"],
    "config": {{
        "width": 800,
        "height": 400,
        "margin": {{"top": 20, "right": 30, "left": 20, "bottom": 5}}
    }}
}}

Return only valid JSON, no markdown or explanations."""
        
        return prompt
    
    def _parse_visualization_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured visualization config."""
        # Clean up response (remove markdown if present)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        return json.loads(response)
    
    def _enrich_visualization_config(
        self,
        visualization: Dict[str, Any],
        results: List[Dict],
        query_understanding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich visualization config with computed defaults."""
        # Ensure all required fields exist
        visualization.setdefault("chart_type", "bar")
        visualization.setdefault("data_key", "")
        visualization.setdefault("category_key", "")
        visualization.setdefault("title", query_understanding.get("intent", "Query Results"))
        visualization.setdefault("description", "")
        visualization.setdefault("x_axis_label", "")
        visualization.setdefault("y_axis_label", "")
        visualization.setdefault("colors", ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#8dd1e1"])
        visualization.setdefault("config", {
            "width": 800,
            "height": 400,
            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 5}
        })
        
        # Auto-detect keys if not provided
        if not visualization.get("data_key") and results:
            columns = list(results[0].keys())
            # Prefer numeric columns
            numeric_cols = [col for col in columns if any(isinstance(results[0].get(col), (int, float)) for row in results[:5])]
            if numeric_cols:
                visualization["data_key"] = numeric_cols[0]
            else:
                visualization["data_key"] = columns[0] if columns else ""
        
        if not visualization.get("category_key") and results:
            columns = list(results[0].keys())
            # Prefer categorical or first non-data-key column
            data_key = visualization.get("data_key", "")
            other_cols = [col for col in columns if col != data_key]
            if other_cols:
                visualization["category_key"] = other_cols[0]
        
        # Map chart type to Recharts component name
        chart_type = visualization.get("chart_type", "bar").lower()
        if chart_type in self.CHART_TYPES:
            visualization["recharts_component"] = self.CHART_TYPES[chart_type]
        else:
            visualization["recharts_component"] = "BarChart"
            visualization["chart_type"] = "bar"
        
        return visualization
    
    def _generate_empty_visualization(self) -> Dict[str, Any]:
        """Generate visualization config for empty results."""
        return {
            "chart_type": "bar",
            "recharts_component": "BarChart",
            "data_key": "",
            "category_key": "",
            "title": "No Data Available",
            "description": "The query returned no results to visualize.",
            "x_axis_label": "",
            "y_axis_label": "",
            "colors": ["#8884d8"],
            "config": {
                "width": 800,
                "height": 400,
                "margin": {"top": 20, "right": 30, "left": 20, "bottom": 5}
            },
            "data": []
        }
    
    def _generate_fallback_visualization(
        self,
        results: List[Dict],
        query_understanding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback visualization when LLM parsing fails."""
        if not results:
            return self._generate_empty_visualization()
        
        columns = list(results[0].keys())
        numeric_cols = [col for col in columns if any(isinstance(results[0].get(col), (int, float)) for row in results[:5])]
        
        data_key = numeric_cols[0] if numeric_cols else columns[0] if columns else ""
        category_key = columns[1] if len(columns) > 1 and columns[1] != data_key else columns[0] if columns else ""
        
        return {
            "chart_type": "bar",
            "recharts_component": "BarChart",
            "data_key": data_key,
            "category_key": category_key,
            "title": query_understanding.get("intent", "Query Results"),
            "description": f"Visualization of {len(results)} results",
            "x_axis_label": category_key or "Category",
            "y_axis_label": data_key or "Value",
            "colors": ["#8884d8", "#82ca9d", "#ffc658"],
            "config": {
                "width": 800,
                "height": 400,
                "margin": {"top": 20, "right": 30, "left": 20, "bottom": 5}
            }
        }

