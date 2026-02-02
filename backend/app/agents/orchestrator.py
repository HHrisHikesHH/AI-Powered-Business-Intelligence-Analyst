"""
LangGraph-based Orchestrator for multi-agent workflow.
Coordinates Query Understanding -> SQL Generation -> Validation -> Execution pipeline.
"""
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from loguru import logger
from app.agents.query_understanding import QueryUnderstandingAgent
from app.agents.sql_generation import SQLGenerationAgent
from app.agents.sql_validator import SQLValidator
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio


class AgentState(TypedDict):
    """State passed between agents in the workflow."""
    natural_language_query: str
    query_understanding: dict
    generated_sql: str
    validation_result: tuple
    execution_results: list
    error: str
    step: Literal["understand", "generate", "validate", "execute", "complete", "error"]


class Orchestrator:
    """Orchestrates the multi-agent NL-to-SQL pipeline."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.query_understanding_agent = QueryUnderstandingAgent()
        self.sql_generation_agent = SQLGenerationAgent(db=db)
        self.sql_validator = SQLValidator(db)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand", self._understand_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("execute", self._execute_node)
        
        # Define edges
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "generate")
        workflow.add_edge("generate", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._should_execute,
            {
                "execute": "execute",
                "error": END
            }
        )
        workflow.add_edge("execute", END)
        
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
            
            sql = await self.sql_generation_agent.generate_sql(
                query_understanding=understanding,
                natural_language_query=query,
                use_rag=True
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
                logger.warning(f"SQL validation failed: {error}")
                state["error"] = f"SQL validation failed: {error}"
            else:
                logger.info("SQL validation passed")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in validate node: {e}")
            state["error"] = f"Validation error: {str(e)}"
            state["validation_result"] = (False, str(e))
            state["step"] = "error"
            return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Query Execution node."""
        try:
            sql = state["generated_sql"]
            
            # Execute query with timeout
            from app.services.query_executor import QueryExecutor
            executor = QueryExecutor(self.db)
            results = await executor._execute_sql(sql)
            
            state["execution_results"] = results
            state["step"] = "complete"
            
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return state
            
        except Exception as e:
            logger.error(f"Error in execute node: {e}")
            state["error"] = f"Execution failed: {str(e)}"
            state["step"] = "error"
            return state
    
    def _should_execute(self, state: AgentState) -> Literal["execute", "error"]:
        """Conditional edge function for validation result."""
        validation_result = state.get("validation_result")
        if validation_result and validation_result[0]:
            return "execute"
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
            "error": "",
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
                "error": final_state.get("error", ""),
                "step": final_state.get("step", "error")
            }
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            return {
                "sql": "",
                "results": [],
                "query_understanding": {},
                "validation_passed": False,
                "error": str(e),
                "step": "error"
            }
    
    async def _run_workflow_manual(self, state: AgentState) -> AgentState:
        """Manual workflow execution if LangGraph async not available."""
        # Run nodes sequentially
        state = await self._understand_node(state)
        if state.get("step") == "error":
            return state
        
        state = await self._generate_node(state)
        if state.get("step") == "error":
            return state
        
        state = await self._validate_node(state)
        if not state.get("validation_result", (False, None))[0]:
            return state
        
        state = await self._execute_node(state)
        return state

