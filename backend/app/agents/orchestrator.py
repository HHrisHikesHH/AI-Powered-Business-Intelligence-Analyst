"""
LangGraph-based Orchestrator for multi-agent workflow.
Coordinates Query Understanding -> SQL Generation -> Validation -> Execution -> Analysis -> Visualization pipeline.
Includes retry logic with exponential backoff and self-correction capabilities.
"""
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph import StateGraph, END
from loguru import logger
from app.agents.query_understanding import QueryUnderstandingAgent
from app.agents.sql_generation import SQLGenerationAgent
from app.agents.sql_validator import SQLValidator
from app.agents.analysis import AnalysisAgent
from app.agents.visualization import VisualizationAgent
from app.services.error_handler import error_handler, ErrorCategory
from sqlalchemy.ext.asyncio import AsyncSession
import time
import asyncio


class AgentState(TypedDict):
    """State passed between agents in the workflow."""
    natural_language_query: str
    query_understanding: dict
    generated_sql: str
    validation_result: tuple
    execution_results: list
    execution_time_ms: Optional[float]
    analysis: Optional[dict]
    visualization: Optional[dict]
    error: str
    error_category: Optional[str]
    retry_count: int
    max_retries: int
    step: Literal["understand", "generate", "validate", "execute", "retry", "self_correct", "analyze", "visualize", "complete", "error"]


class Orchestrator:
    """Orchestrates the multi-agent NL-to-SQL pipeline."""
    
    def __init__(self, db: AsyncSession, max_retries: int = 3):
        self.db = db
        self.max_retries = max_retries
        self.query_understanding_agent = QueryUnderstandingAgent()
        self.sql_generation_agent = SQLGenerationAgent(db=db)
        self.sql_validator = SQLValidator(db)
        self.analysis_agent = AnalysisAgent()
        self.visualization_agent = VisualizationAgent()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with retry and self-correction."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand", self._understand_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("retry", self._retry_node)
        workflow.add_node("self_correct", self._self_correct_node)
        workflow.add_node("analyze_and_visualize", self._analyze_and_visualize_node)
        
        # Define edges
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "generate")
        workflow.add_edge("generate", "validate")
        
        # Validation can lead to execute, retry, or error
        workflow.add_conditional_edges(
            "validate",
            self._should_retry_or_execute,
            {
                "execute": "execute",
                "retry": "retry",
                "self_correct": "self_correct",
                "error": END
            }
        )
        
        # Retry node goes back to generate
        workflow.add_edge("retry", "generate")
        
        # Self-correct node goes back to generate
        workflow.add_edge("self_correct", "generate")
        
        # Execution can lead to analyze_and_visualize, skip_analysis, or retry
        workflow.add_conditional_edges(
            "execute",
            self._should_analyze_or_retry,
            {
                "analyze": "analyze_and_visualize",
                "skip_analysis": END,  # Skip analysis for simple queries
                "retry": "retry",
                "error": END
            }
        )
        
        # After analysis and visualization, end
        workflow.add_edge("analyze_and_visualize", END)
        
        return workflow.compile()
    
    async def _understand_node(self, state: AgentState) -> AgentState:
        """Query Understanding node."""
        try:
            query = state["natural_language_query"]
            understanding = await self.query_understanding_agent.understand(query)
            
            state["query_understanding"] = understanding
            state["step"] = "understand"
            
            logger.info(f"Query understood: {understanding.get('intent', 'unknown')}")
            return state
            
        except Exception as e:
            logger.error(f"Error in understand node: {e}")
            state["error"] = f"Query understanding failed: {str(e)}"
            state["step"] = "error"
            return state
    
    async def _generate_node(self, state: AgentState) -> AgentState:
        """SQL Generation node."""
        try:
            understanding = state["query_understanding"]
            query = state["natural_language_query"]
            
            # Use enhanced complexity classification for better model routing
            from app.core.llm_client import llm_service
            complexity = llm_service.classify_from_understanding(understanding)
            logger.debug(f"Classified query complexity: {complexity.value}")
            
            sql = await self.sql_generation_agent.generate_sql(
                query_understanding=understanding,
                natural_language_query=query,
                use_rag=True,
                complexity=complexity  # Pass complexity for better model selection
            )
            
            state["generated_sql"] = sql
            state["step"] = "generate"
            
            logger.info(f"SQL generated: {sql}")
            return state
            
        except Exception as e:
            logger.error(f"Error in generate node: {e}")
            state["error"] = f"SQL generation failed: {str(e)}"
            state["step"] = "error"
            return state
    
    async def _validate_node(self, state: AgentState) -> AgentState:
        """SQL Validation node."""
        try:
            sql = state["generated_sql"]
            
            is_valid, error = await self.sql_validator.validate(sql)
            
            state["validation_result"] = (is_valid, error)
            state["step"] = "validate"
            
            if not is_valid:
                # Categorize error
                error_info = error_handler.categorize_error(
                    Exception(error),
                    context={
                        "sql": sql,
                        "step": "validation",
                        "query": state.get("natural_language_query", "")
                    }
                )
                state["error"] = f"SQL validation failed: {error}"
                state["error_category"] = error_info["category"]
            else:
                logger.info("SQL validation passed")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in validate node: {e}")
            error_info = error_handler.categorize_error(e, context={"step": "validation"})
            state["error"] = f"Validation error: {str(e)}"
            state["error_category"] = error_info["category"]
            state["validation_result"] = (False, str(e))
            state["step"] = "error"
            return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Query Execution node."""
        try:
            sql = state["generated_sql"]
            start_time = time.time()
            
            # Execute query with timeout
            from app.services.query_executor import QueryExecutor
            executor = QueryExecutor(self.db)
            results = await executor._execute_sql(sql)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            state["execution_results"] = results
            state["execution_time_ms"] = execution_time_ms
            state["step"] = "execute"
            
            # Check for empty results (might indicate query intent mismatch)
            if len(results) == 0:
                logger.warning("Query returned empty results - might indicate intent mismatch")
                # Don't fail, but mark for potential analysis
            
            logger.info(f"Query executed successfully, returned {len(results)} rows in {execution_time_ms:.2f}ms")
            return state
            
        except Exception as e:
            logger.error(f"Error in execute node: {e}")
            # Categorize error
            error_info = error_handler.categorize_error(
                e,
                context={
                    "sql": sql,
                    "step": "execution",
                    "query": state.get("natural_language_query", "")
                }
            )
            state["error"] = f"Execution failed: {str(e)}"
            state["error_category"] = error_info["category"]
            state["step"] = "error"
            return state
    
    async def _analyze_node(self, state: AgentState) -> AgentState:
        """Analysis node - generates insights from results."""
        try:
            query_understanding = state["query_understanding"]
            natural_language_query = state["natural_language_query"]
            sql = state["generated_sql"]
            results = state["execution_results"]
            execution_time_ms = state.get("execution_time_ms")
            
            analysis = await self.analysis_agent.analyze_results(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                results=results,
                execution_time_ms=execution_time_ms
            )
            
            state["analysis"] = analysis
            state["step"] = "analyze"
            
            # Check if empty results might indicate intent mismatch
            if len(results) == 0:
                # Ask Analysis Agent if query intent was likely misunderstood
                empty_result_analysis = analysis.get("anomalies", [])
                if empty_result_analysis:
                    logger.warning("Empty results detected - query intent may be misunderstood")
                    # Could trigger query refinement here in future
            
            logger.info(f"Analysis complete: {len(analysis.get('insights', []))} insights generated")
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze node: {e}")
            error_handler.categorize_error(e, context={"step": "analysis"})
            # Don't fail the workflow if analysis fails, just log it
            state["analysis"] = {
                "insights": [],
                "trends": [],
                "anomalies": [],
                "recommendations": [],
                "summary": f"Analysis unavailable: {str(e)}"
            }
            state["step"] = "analyze"
            return state
    
    async def _visualize_node(self, state: AgentState) -> AgentState:
        """Visualization node - generates chart configuration."""
        try:
            query_understanding = state["query_understanding"]
            natural_language_query = state["natural_language_query"]
            sql = state["generated_sql"]
            results = state["execution_results"]
            analysis = state.get("analysis")
            
            visualization = await self.visualization_agent.generate_visualization(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                results=results,
                analysis=analysis
            )
            
            state["visualization"] = visualization
            state["step"] = "complete"
            
            logger.info(f"Visualization complete: {visualization.get('chart_type', 'unknown')} chart")
            return state
            
        except Exception as e:
            logger.error(f"Error in visualize node: {e}")
            # Don't fail the workflow if visualization fails, just log it
            state["visualization"] = {
                "chart_type": "bar",
                "recharts_component": "BarChart",
                "title": "Visualization unavailable",
                "description": f"Visualization generation failed: {str(e)}"
            }
            state["step"] = "complete"
            return state
    
    async def _analyze_and_visualize_node(self, state: AgentState) -> AgentState:
        """Run analysis and visualization in parallel for better performance."""
        try:
            query_understanding = state["query_understanding"]
            natural_language_query = state["natural_language_query"]
            sql = state["generated_sql"]
            results = state["execution_results"]
            execution_time_ms = state.get("execution_time_ms")
            
            # Run analysis and visualization in parallel
            analysis_task = self.analysis_agent.analyze_results(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                results=results,
                execution_time_ms=execution_time_ms
            )
            
            visualization_task = self.visualization_agent.generate_visualization(
                query_understanding=query_understanding,
                natural_language_query=natural_language_query,
                sql=sql,
                results=results,
                analysis=None  # Will be set after analysis completes
            )
            
            # Execute in parallel
            analysis_result, visualization_result = await asyncio.gather(
                analysis_task,
                visualization_task,
                return_exceptions=True
            )
            
            # Handle analysis result
            if isinstance(analysis_result, Exception):
                logger.error(f"Error in analysis: {analysis_result}")
                state["analysis"] = {
                    "insights": [],
                    "trends": [],
                    "anomalies": [],
                    "recommendations": [],
                    "summary": f"Analysis unavailable: {str(analysis_result)}"
                }
            else:
                state["analysis"] = analysis_result
                # Check if empty results might indicate intent mismatch
                if len(results) == 0:
                    empty_result_analysis = analysis_result.get("anomalies", [])
                    if empty_result_analysis:
                        logger.warning("Empty results detected - query intent may be misunderstood")
            
            # Handle visualization result
            if isinstance(visualization_result, Exception):
                logger.error(f"Error in visualization: {visualization_result}")
                state["visualization"] = {
                    "chart_type": "bar",
                    "recharts_component": "BarChart",
                    "title": "Visualization unavailable",
                    "description": f"Visualization generation failed: {str(visualization_result)}"
                }
            else:
                state["visualization"] = visualization_result
            
            state["step"] = "complete"
            
            logger.info(
                f"Analysis and visualization complete: "
                f"{len(state['analysis'].get('insights', []))} insights, "
                f"{state['visualization'].get('chart_type', 'unknown')} chart"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze_and_visualize node: {e}")
            error_handler.categorize_error(e, context={"step": "analyze_and_visualize"})
            # Set defaults on error
            state["analysis"] = {
                "insights": [],
                "trends": [],
                "anomalies": [],
                "recommendations": [],
                "summary": f"Analysis unavailable: {str(e)}"
            }
            state["visualization"] = {
                "chart_type": "bar",
                "recharts_component": "BarChart",
                "title": "Visualization unavailable",
                "description": f"Visualization generation failed: {str(e)}"
            }
            state["step"] = "complete"
            return state
    
    async def _retry_node(self, state: AgentState) -> AgentState:
        """Retry node with exponential backoff."""
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        
        if retry_count >= max_retries:
            logger.error(f"Max retries ({max_retries}) exceeded")
            state["step"] = "error"
            state["error"] = f"Max retries ({max_retries}) exceeded. Last error: {state.get('error', 'Unknown')}"
            return state
        
        # Exponential backoff: 1s, 2s, 4s
        backoff_seconds = 2 ** retry_count
        logger.info(f"Retrying after {backoff_seconds}s (attempt {retry_count + 1}/{max_retries})")
        
        await asyncio.sleep(backoff_seconds)
        
        state["retry_count"] = retry_count + 1
        state["step"] = "retry"
        
        return state
    
    async def _self_correct_node(self, state: AgentState) -> AgentState:
        """Self-correction node - feeds error back to SQL agent."""
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        
        if retry_count >= max_retries:
            logger.error(f"Max self-correction attempts ({max_retries}) exceeded")
            state["step"] = "error"
            return state
        
        try:
            error_category = state.get("error_category", "")
            previous_sql = state.get("generated_sql", "")
            error_message = state.get("error", "")
            query_understanding = state.get("query_understanding", {})
            natural_language_query = state.get("natural_language_query", "")
            
            logger.info(f"Self-correcting SQL (attempt {retry_count + 1}/{max_retries})")
            logger.info(f"Error category: {error_category}, Error: {error_message}")
            
            # Use self-correction for syntax and schema errors
            if error_category in [ErrorCategory.SYNTAX_ERROR.value, ErrorCategory.SCHEMA_ERROR.value]:
                corrected_sql = await self.sql_generation_agent.self_correct_sql(
                    query_understanding=query_understanding,
                    natural_language_query=natural_language_query,
                    previous_sql=previous_sql,
                    error_message=error_message
                )
                
                state["generated_sql"] = corrected_sql
                state["retry_count"] = retry_count + 1
                state["step"] = "self_correct"
                state["error"] = ""  # Clear error for retry
                
                logger.info(f"SQL corrected: {corrected_sql[:100]}...")
            else:
                # For other errors, just increment retry count
                state["retry_count"] = retry_count + 1
                state["step"] = "retry"
            
            return state
            
        except Exception as e:
            logger.error(f"Error in self-correct node: {e}")
            state["error"] = f"Self-correction failed: {str(e)}"
            state["step"] = "error"
            return state
    
    def _should_retry_or_execute(self, state: AgentState) -> Literal["execute", "retry", "self_correct", "error"]:
        """Conditional edge function for validation result with retry logic."""
        validation_result = state.get("validation_result")
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        error_category = state.get("error_category", "")
        
        if validation_result and validation_result[0]:
            return "execute"
        
        # Check if we should retry
        if retry_count >= max_retries:
            return "error"
        
        # Determine retry strategy based on error category
        if error_category in [ErrorCategory.SYNTAX_ERROR.value, ErrorCategory.SCHEMA_ERROR.value]:
            # Use self-correction for syntax and schema errors
            return "self_correct"
        elif error_category in [ErrorCategory.LLM_ERROR.value, ErrorCategory.NETWORK_ERROR.value]:
            # Use retry with backoff for LLM/network errors
            return "retry"
        else:
            # For other errors, try self-correction first
            return "self_correct"
    
    def _is_simple_query(self, state: AgentState) -> bool:
        """
        Determine if query is simple enough to skip analysis/visualization.
        
        Simple queries are:
        - Single table
        - No aggregations (or simple COUNT/SUM)
        - No GROUP BY
        - No joins
        - Simple filters only
        - Small result set (< 10 rows)
        """
        query_understanding = state.get("query_understanding", {})
        execution_results = state.get("execution_results", [])
        
        # Check table count
        tables = query_understanding.get("tables", [])
        if len(tables) > 1:
            return False  # Multiple tables = not simple
        
        # Check for aggregations
        aggregations = query_understanding.get("aggregations", [])
        # Simple aggregations (COUNT, SUM) are OK, but complex ones need analysis
        if aggregations and len(aggregations) > 1:
            return False
        
        # Check for GROUP BY
        group_by = query_understanding.get("group_by", [])
        if group_by:
            return False  # GROUP BY queries benefit from analysis
        
        # Check result count
        if len(execution_results) > 10:
            return False  # Large result sets benefit from analysis
        
        # Simple query - can skip analysis/visualization
        return True
    
    def _should_analyze_or_retry(self, state: AgentState) -> Literal["analyze", "skip_analysis", "retry", "error"]:
        """Conditional edge function for execution result."""
        execution_results = state.get("execution_results", [])
        error = state.get("error", "")
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        
        # If execution succeeded, check if we should analyze or skip
        if not error and execution_results is not None:
            # Skip analysis/visualization for simple queries
            if self._is_simple_query(state):
                return "skip_analysis"
            return "analyze"  # Routes to analyze_and_visualize node
        
        # If error occurred, check if we should retry
        if error and retry_count < max_retries:
            error_category = state.get("error_category", "")
            # Retry for timeout and execution errors
            if error_category in [ErrorCategory.TIMEOUT_ERROR.value, ErrorCategory.EXECUTION_ERROR.value]:
                return "retry"
        
        # Max retries exceeded or non-retryable error
        return "error"
    
    async def process_query(self, natural_language_query: str) -> dict:
        """
        Process a natural language query through the full pipeline.
        
        Args:
            natural_language_query: Natural language query string
        
        Returns:
            Dictionary with:
            - sql: Generated SQL
            - results: Query results
            - query_understanding: Understanding output
            - validation_passed: Boolean
            - error: Error message if any
        """
        # Initialize state
        initial_state: AgentState = {
            "natural_language_query": natural_language_query,
            "query_understanding": {},
            "generated_sql": "",
            "validation_result": (False, None),
            "execution_results": [],
            "execution_time_ms": None,
            "analysis": None,
            "visualization": None,
            "error": "",
            "error_category": None,
            "retry_count": 0,
            "max_retries": self.max_retries,
            "step": "understand"
        }
        
        try:
            # Run workflow - LangGraph supports async nodes
            # Use astream for async execution or ainvoke if available
            if hasattr(self.workflow, 'ainvoke'):
                final_state = await self.workflow.ainvoke(initial_state)
            else:
                # Fallback: run nodes manually if ainvoke not available
                final_state = await self._run_workflow_manual(initial_state)
            
            # Format response
            return {
                "sql": final_state.get("generated_sql", ""),
                "results": final_state.get("execution_results", []),
                "query_understanding": final_state.get("query_understanding", {}),
                "validation_passed": final_state.get("validation_result", (False, None))[0],
                "execution_time_ms": final_state.get("execution_time_ms"),
                "analysis": final_state.get("analysis"),
                "visualization": final_state.get("visualization"),
                "error": final_state.get("error", ""),
                "error_category": final_state.get("error_category"),
                "retry_count": final_state.get("retry_count", 0),
                "step": final_state.get("step", "error")
            }
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            error_info = error_handler.categorize_error(e, context={"step": "orchestrator"})
            return {
                "sql": "",
                "results": [],
                "query_understanding": {},
                "validation_passed": False,
                "execution_time_ms": None,
                "analysis": None,
                "visualization": None,
                "error": str(e),
                "error_category": error_info["category"],
                "retry_count": 0,
                "step": "error"
            }
    
    async def _run_workflow_manual(self, state: AgentState) -> AgentState:
        """Manual workflow execution with retry and self-correction logic."""
        max_retries = state.get("max_retries", self.max_retries)
        
        # Run nodes sequentially with retry logic
        state = await self._understand_node(state)
        if state.get("step") == "error":
            return state
        
        # SQL generation with retry loop
        for attempt in range(max_retries + 1):
            state = await self._generate_node(state)
            if state.get("step") == "error":
                break
            
            state = await self._validate_node(state)
            validation_result = state.get("validation_result", (False, None))
            
            if validation_result[0]:
                # Validation passed, proceed to execution
                break
            else:
                # Validation failed, try self-correction
                if attempt < max_retries:
                    error_category = state.get("error_category", "")
                    if error_category in [ErrorCategory.SYNTAX_ERROR.value, ErrorCategory.SCHEMA_ERROR.value]:
                        state = await self._self_correct_node(state)
                        if state.get("step") == "error":
                            break
                        continue
                    else:
                        # Wait with exponential backoff
                        await self._retry_node(state)
                        continue
                else:
                    # Max retries exceeded
                    state["step"] = "error"
                    return state
        
        # Check if validation passed before execution
        validation_result = state.get("validation_result", (False, None))
        if not validation_result[0]:
            return state
        
        # Execute with retry loop
        for attempt in range(max_retries + 1):
            state = await self._execute_node(state)
            
            if not state.get("error"):
                # Execution succeeded
                break
            else:
                # Execution failed, check if retryable
                if attempt < max_retries:
                    error_category = state.get("error_category", "")
                    if error_category in [ErrorCategory.TIMEOUT_ERROR.value, ErrorCategory.EXECUTION_ERROR.value]:
                        state = await self._retry_node(state)
                        if state.get("step") == "error":
                            break
                        continue
                else:
                    # Max retries exceeded
                    state["step"] = "error"
                    return state
        
        # If execution succeeded, check if we should analyze or skip
        if not state.get("error") and state.get("execution_results") is not None:
            # Skip analysis/visualization for simple queries
            if self._is_simple_query(state):
                logger.info("Skipping analysis/visualization for simple query")
                state["step"] = "complete"
            else:
                state = await self._analyze_and_visualize_node(state)
        
        return state

