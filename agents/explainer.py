"""
Agent 3: Explainer - Generate natural language explanations of query results.
"""

import logging
import json
from typing import List, Dict
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class ExplainerAgent:
    """Agent responsible for explaining query results in natural language."""
    
    def __init__(self):
        """Initialize explainer agent with Groq API client."""
        self.client = Groq(api_key=settings.api.groq_api_key)
        self.model = "llama-3.1-8b-instant"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def explain_results(self, question: str, sql: str, results: List[Dict]) -> str:
        """
        Generate natural language explanation of query results.
        
        Args:
            question: Original user question
            sql: SQL query that was executed
            results: Query results as list of dictionaries
            
        Returns:
            Natural language explanation in markdown format
        """
        try:
            # Limit result size in prompt to avoid token limits
            sample_results = results[:10] if len(results) > 10 else results
            
            # Convert results to JSON string
            results_json = json.dumps(sample_results, indent=2, default=str)
            
            prompt = PromptTemplates.results_explanation_prompt(
                question=question,
                sql=sql,
                results=results_json,
                result_count=len(results)
            )
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.RESULTS_EXPLANATION_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            explanation = completion.choices[0].message.content
            
            logger.info("Generated results explanation")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            # Fallback to basic summary
            return self._fallback_explanation(question, results)
    
    def _fallback_explanation(self, question: str, results: List[Dict]) -> str:
        """
        Generate basic explanation when API fails.
        
        Args:
            question: Original user question
            results: Query results
            
        Returns:
            Basic explanation text
        """
        row_count = len(results)
        
        explanation = f"### Query Results\n\n"
        explanation += f"Found **{row_count}** results for your question: \"{question}\"\n\n"
        
        if row_count > 0:
            # Show column names
            columns = list(results[0].keys())
            explanation += f"**Columns:** {', '.join(columns)}\n\n"
            
            # Basic insights
            explanation += "**Key Insights:**\n"
            explanation += f"- Total records returned: {row_count}\n"
            
            # If there's a numeric column, try to show sum/avg
            for col in columns:
                if row_count > 0 and isinstance(results[0].get(col), (int, float)):
                    total = sum(row.get(col, 0) for row in results if row.get(col) is not None)
                    avg = total / row_count
                    explanation += f"- Total {col}: {total:.2f}\n"
                    explanation += f"- Average {col}: {avg:.2f}\n"
                    break
        else:
            explanation += "No results found matching your criteria.\n"
        
        return explanation
    
    def generate_insights(self, results: List[Dict]) -> List[str]:
        """
        Analyze result data for patterns and insights.
        
        Args:
            results: Query results
            
        Returns:
            List of insight strings
        """
        insights = []
        
        if not results:
            insights.append("No data available for analysis")
            return insights
        
        row_count = len(results)
        insights.append(f"Total records: {row_count}")
        
        # Analyze numeric columns
        columns = list(results[0].keys())
        
        for col in columns:
            # Check if column is numeric
            sample_value = results[0].get(col)
            
            if isinstance(sample_value, (int, float)):
                values = [row.get(col) for row in results if row.get(col) is not None]
                
                if values:
                    total = sum(values)
                    avg = total / len(values)
                    max_val = max(values)
                    min_val = min(values)
                    
                    insights.append(f"{col}: min={min_val}, max={max_val}, avg={avg:.2f}")
        
        return insights
    
    def format_explanation(self, summary: str, insights: List[str]) -> str:
        """
        Combine summary and insights into formatted markdown.
        
        Args:
            summary: Main summary text
            insights: List of key insights
            
        Returns:
            Formatted explanation in markdown
        """
        explanation = f"{summary}\n\n"
        
        if insights:
            explanation += "### Key Insights\n\n"
            for insight in insights:
                explanation += f"- {insight}\n"
        
        return explanation


# Global explainer agent instance
explainer = ExplainerAgent()
