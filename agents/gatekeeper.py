"""
Agent 1: Gatekeeper - Intent classification and question validation.
"""

import logging
import json
import re
from typing import Dict, Tuple
from datetime import datetime, timedelta
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from config.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class GatekeeperAgent:
    """Agent responsible for intent classification and question validation."""
    
    def __init__(self):
        """Initialize gatekeeper agent with Groq API client."""
        self.client = Groq(api_key=settings.api.groq_api_key)
        self.model = "llama-3.1-8b-instant"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def classify_intent(self, message: str) -> Dict[str, any]:
        """
        Classify user intent using Llama-3.1-8B via Groq.
        
        Args:
            message: User's input message
            
        Returns:
            Dictionary with:
                - intent: str (greeting, data_query, vague_question, off_topic)
                - confidence: float (0.0-1.0)
                - needs_clarification: bool
                - response: str (response message to user)
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.GATEKEEPER_SYSTEM},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            result = json.loads(response_text)
            
            logger.info(f"Intent classified as: {result.get('intent')} with confidence {result.get('confidence')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Fallback to rule-based classification
            return self._fallback_classification(message)
        
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            # Fallback to rule-based classification
            return self._fallback_classification(message)
    
    def _fallback_classification(self, message: str) -> Dict[str, any]:
        """
        Rule-based fallback classification when API fails.
        
        Args:
            message: User's input message
            
        Returns:
            Classification dictionary
        """
        message_lower = message.lower().strip()
        
        # Check for greetings
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(word in message_lower for word in greetings):
            return {
                "intent": "greeting",
                "confidence": 0.8,
                "needs_clarification": False,
                "response": "Hello! I'm your SQL assistant. I can help you query your database using natural language. What would you like to know about your data?"
            }
        
        # Check for data-related keywords
        data_keywords = ['show', 'get', 'find', 'list', 'count', 'total', 'sum', 'average', 
                        'select', 'query', 'data', 'table', 'records', 'customers', 'orders', 
                        'sales', 'revenue', 'users']
        
        if any(keyword in message_lower for keyword in data_keywords):
            # Check if question is specific enough
            if len(message.split()) < 4:
                return {
                    "intent": "vague_question",
                    "confidence": 0.7,
                    "needs_clarification": True,
                    "response": "Could you be more specific? Please provide more details about what data you're looking for."
                }
            
            return {
                "intent": "data_query",
                "confidence": 0.7,
                "needs_clarification": False,
                "response": "I'll help you with that query."
            }
        
        # Default to off-topic
        return {
            "intent": "off_topic",
            "confidence": 0.6,
            "needs_clarification": False,
            "response": "I can only help with database queries. Please ask a question about your data."
        }
    
    def validate_question(self, question: str) -> Tuple[bool, str]:
        """
        Validate if question is specific enough for SQL generation.
        
        Args:
            question: User's question
            
        Returns:
            Tuple of (is_valid, clarification_message)
        """
        question = question.strip()
        
        # Check minimum length
        if len(question) < 10:
            return False, "Your question seems too short. Could you provide more details?"
        
        # Check if it's just a greeting
        greetings = ['hello', 'hi', 'hey']
        if question.lower() in greetings:
            return False, "Please ask a specific question about your data."
        
        # Check for question words or data keywords
        data_indicators = ['show', 'get', 'find', 'list', 'count', 'how many', 'what', 
                          'which', 'total', 'sum', 'average', 'display']
        
        has_indicator = any(ind in question.lower() for ind in data_indicators)
        
        if not has_indicator:
            return False, "Please rephrase your question to be more specific. For example: 'Show me total sales by region' or 'How many active customers do we have?'"
        
        return True, ""
    
    def preprocess_question(self, question: str) -> str:
        """
        Clean and normalize user question.
        
        Args:
            question: Raw user question
            
        Returns:
            Preprocessed question
        """
        # Strip whitespace
        question = question.strip()
        
        # Expand abbreviations
        abbreviations = {
            r'\bqty\b': 'quantity',
            r'\bamt\b': 'amount',
            r'\btot\b': 'total',
            r'\bavg\b': 'average',
            r'\bpct\b': 'percent',
        }
        
        for abbrev, full in abbreviations.items():
            question = re.sub(abbrev, full, question, flags=re.IGNORECASE)
        
        # Resolve relative time references
        question = self._resolve_time_references(question)
        
        return question
    
    def _resolve_time_references(self, question: str) -> str:
        """
        Resolve relative time references to specific dates.
        
        Args:
            question: Question with potential time references
            
        Returns:
            Question with resolved dates
        """
        now = datetime.now()
        
        # Define time mappings
        replacements = {
            'today': now.strftime('%Y-%m-%d'),
            'yesterday': (now - timedelta(days=1)).strftime('%Y-%m-%d'),
            'last week': f"between '{(now - timedelta(days=7)).strftime('%Y-%m-%d')}' and '{now.strftime('%Y-%m-%d')}'",
            'last month': f"in {(now - timedelta(days=30)).strftime('%Y-%m')}",
            'this month': f"in {now.strftime('%Y-%m')}",
            'this year': f"in {now.strftime('%Y')}",
        }
        
        question_lower = question.lower()
        
        for ref, replacement in replacements.items():
            if ref in question_lower:
                # Replace while preserving original case if possible
                pattern = re.compile(re.escape(ref), re.IGNORECASE)
                question = pattern.sub(replacement, question)
        
        return question


# Global gatekeeper agent instance
gatekeeper = GatekeeperAgent()
