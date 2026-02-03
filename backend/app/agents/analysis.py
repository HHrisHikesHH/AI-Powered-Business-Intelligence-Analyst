"""
Analysis Agent.
Interprets query results and generates insights, trends, and recommendations.
"""
from loguru import logger
from app.core.llm_client import llm_service, QueryComplexity
from typing import Dict, Any, List, Optional
import json


class AnalysisAgent:
    """Agent responsible for analyzing query results and generating insights."""
    
    def __init__(self):
        self.llm = llm_service
    
    async def analyze_results(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        sql: str,
        results: List[Dict],
        execution_time_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze query results and generate insights.
        
        Args:
            query_understanding: Output from Query Understanding Agent
            natural_language_query: Original natural language query
            sql: Generated SQL query
            results: Query execution results
            execution_time_ms: Query execution time in milliseconds
        
        Returns:
            Dictionary with:
            - insights: List of key insights
            - trends: Detected trends (if applicable)
            - anomalies: Detected anomalies (if any)
            - recommendations: Actionable recommendations
            - summary: Natural language summary
        """
        try:
            logger.info(f"Analyzing {len(results)} result rows")
            
            # Determine if analysis is needed based on result size and query type
            if not results:
                return self._generate_empty_result_analysis(query_understanding, natural_language_query)
            
            # Prepare data summary for LLM
            data_summary = self._prepare_data_summary(results, query_understanding)
            
            # Format prompt
            prompt = self._format_analysis_prompt(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                data_summary=data_summary,
                result_count=len(results),
                execution_time_ms=execution_time_ms
            )
            
            # Use complex model for analysis (requires reasoning)
            response = await self.llm.generate_completion(
                prompt=prompt,
                system_prompt="You are an Analysis Agent specialized in interpreting data and generating business insights. Return only valid JSON.",
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=1500,  # More tokens for detailed analysis
                complexity=QueryComplexity.COMPLEX,  # Use complex model for analysis
                auto_select_model=True
            )
            
            # Parse JSON response
            try:
                analysis = self._parse_analysis_response(response)
                
                # Validate and enrich analysis
                analysis = self._enrich_analysis(analysis, results, query_understanding)
                
                logger.info(f"Analysis complete: {len(analysis.get('insights', []))} insights generated")
                return analysis
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse analysis response: {e}")
                logger.error(f"Response was: {response}")
                return self._generate_fallback_analysis(results, query_understanding)
                
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return self._generate_fallback_analysis(results, query_understanding)
    
    def _prepare_data_summary(self, results: List[Dict], query_understanding: Dict[str, Any]) -> str:
        """Prepare a summary of the data for analysis."""
        if not results:
            return "No results returned."
        
        # Sample first few rows (limit to avoid token limits)
        sample_size = min(10, len(results))
        sample_rows = results[:sample_size]
        
        # Get column names
        columns = list(sample_rows[0].keys()) if sample_rows else []
        
        # Calculate basic statistics for numeric columns
        stats = {}
        for col in columns:
            values = [row.get(col) for row in results if row.get(col) is not None]
            if values and isinstance(values[0], (int, float)):
                try:
                    numeric_values = [float(v) for v in values]
                    stats[col] = {
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "avg": sum(numeric_values) / len(numeric_values),
                        "count": len(numeric_values)
                    }
                except (ValueError, TypeError):
                    pass
        
        summary_parts = [
            f"Total rows: {len(results)}",
            f"Columns: {', '.join(columns)}",
        ]
        
        if stats:
            summary_parts.append("\nNumeric Statistics:")
            for col, stat in stats.items():
                summary_parts.append(
                    f"  {col}: min={stat['min']:.2f}, max={stat['max']:.2f}, "
                    f"avg={stat['avg']:.2f}, count={stat['count']}"
                )
        
        summary_parts.append(f"\nSample rows (first {sample_size}):")
        for i, row in enumerate(sample_rows, 1):
            row_str = ", ".join([f"{k}={v}" for k, v in row.items()])
            summary_parts.append(f"  Row {i}: {row_str}")
        
        return "\n".join(summary_parts)
    
    def _format_analysis_prompt(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str,
        sql: str,
        data_summary: str,
        result_count: int,
        execution_time_ms: Optional[float] = None
    ) -> str:
        """Format the analysis prompt."""
        intent = query_understanding.get("intent", "")
        aggregations = query_understanding.get("aggregations", [])
        has_group_by = len(query_understanding.get("group_by", [])) > 0
        
        prompt = f"""Analyze the following query results and generate insights.

Original Query: {natural_language_query}
Query Intent: {intent}
SQL Query: {sql}
Result Count: {result_count}
Execution Time: {execution_time_ms:.2f}ms (if available)

Data Summary:
{data_summary}

Please provide a comprehensive analysis in JSON format with the following structure:
{{
    "insights": [
        "Key insight 1",
        "Key insight 2",
        ...
    ],
    "trends": [
        {{"description": "Trend description", "type": "increasing|decreasing|stable|cyclical"}},
        ...
    ],
    "anomalies": [
        {{"description": "Anomaly description", "severity": "low|medium|high"}},
        ...
    ],
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2",
        ...
    ],
    "summary": "Natural language summary of the findings (2-3 sentences)"
}}

Focus Areas:
- If aggregations present: Highlight key metrics and comparisons
- If GROUP BY present: Identify patterns across groups
- If time-series data: Detect trends and seasonality
- If numeric data: Identify outliers and distributions
- Always provide actionable business recommendations

Return only valid JSON, no markdown or explanations."""
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured analysis."""
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
    
    def _enrich_analysis(
        self,
        analysis: Dict[str, Any],
        results: List[Dict],
        query_understanding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich analysis with additional computed insights."""
        # Ensure all required fields exist
        analysis.setdefault("insights", [])
        analysis.setdefault("trends", [])
        analysis.setdefault("anomalies", [])
        analysis.setdefault("recommendations", [])
        analysis.setdefault("summary", "Analysis complete.")
        
        # Add computed statistics if aggregations present
        aggregations = query_understanding.get("aggregations", [])
        if aggregations and results:
            # Extract aggregation values
            for row in results:
                for col, val in row.items():
                    if any(agg.lower() in col.lower() for agg in aggregations):
                        if isinstance(val, (int, float)):
                            analysis["insights"].append(
                                f"{col}: {val:,.2f}" if isinstance(val, float) else f"{col}: {val:,}"
                            )
        
        return analysis
    
    def _generate_empty_result_analysis(
        self,
        query_understanding: Dict[str, Any],
        natural_language_query: str
    ) -> Dict[str, Any]:
        """Generate analysis for empty results."""
        return {
            "insights": [
                "No results found matching the query criteria.",
                "Consider broadening the search filters or checking if the data exists."
            ],
            "trends": [],
            "anomalies": [
                {
                    "description": "Query returned zero results",
                    "severity": "medium"
                }
            ],
            "recommendations": [
                "Review the query filters - they may be too restrictive",
                "Verify that the data exists in the database for the specified criteria",
                "Consider adjusting date ranges or filter values"
            ],
            "summary": f"The query '{natural_language_query}' returned no results. This may indicate that the specified criteria are too restrictive or that no matching data exists."
        }
    
    def _generate_fallback_analysis(
        self,
        results: List[Dict],
        query_understanding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback analysis when LLM parsing fails."""
        result_count = len(results)
        
        return {
            "insights": [
                f"Query returned {result_count} result(s).",
                "Review the data to identify key patterns and insights."
            ],
            "trends": [],
            "anomalies": [],
            "recommendations": [
                "Review the results manually to extract insights",
                "Consider refining the query for more specific results"
            ],
            "summary": f"Analysis generated for {result_count} result(s). Please review the data for detailed insights."
        }

