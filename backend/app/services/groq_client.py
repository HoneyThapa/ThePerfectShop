import os
import json
import time
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

class GroqClient:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = GROQ_BASE_URL
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def chat_completion(
        self, 
        messages: list, 
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Make a chat completion request to Groq API"""
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                time.sleep(2)  # Rate limit backoff
                raise
            raise Exception(f"Groq API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Groq client error: {str(e)}")

    def get_insights(self, context_data: Dict[str, Any], filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate AI insights from risk context data"""
        system_prompt = """You are an expert supply chain analyst for retail inventory management. 
        You provide grounded insights based ONLY on the provided data. Never invent SKUs, quantities, or database fields.
        
        Your response must be valid JSON with this exact structure:
        {
            "executive_summary": "Brief overview of key risks and opportunities",
            "prioritized_actions": [
                {
                    "action_type": "markdown|transfer|reorder_pause|bundle|fefo_attention",
                    "priority": "high|medium|low",
                    "description": "What to do",
                    "evidence": ["field1", "field2"],
                    "confidence": 0.85,
                    "expected_impact": "Quantified benefit estimate"
                }
            ],
            "key_metrics": {
                "total_at_risk_value": 0,
                "high_risk_batches": 0,
                "avg_days_to_expiry": 0
            },
            "assumptions": ["List key assumptions made"]
        }"""
        
        user_prompt = f"""Analyze this inventory risk data and provide actionable insights:

Context Data:
{json.dumps(context_data, indent=2, default=str)}

Filters Applied: {filters or 'None'}

Focus on the highest risk items and most impactful actions. Cite specific evidence from the data."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.chat_completion(messages)
        content = response["choices"][0]["message"]["content"]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "executive_summary": "Analysis completed but response format error occurred",
                "prioritized_actions": [],
                "key_metrics": {},
                "assumptions": ["Response parsing failed"]
            }

    def chat_response(self, message: str, context_data: Dict[str, Any], conversation_history: list = None) -> Dict[str, Any]:
        """Generate conversational response with context"""
        system_prompt = """You are a helpful supply chain analyst assistant. Answer questions about inventory risk data.
        
        Rules:
        - Only use data provided in the context
        - Cite specific evidence fields when making claims
        - If data is missing, explicitly state this and ask for clarification
        - Never invent SKUs, quantities, or database values
        - Provide structured actions when relevant
        
        Response format (JSON):
        {
            "response": "Your conversational answer",
            "structured_actions": [
                {
                    "action_type": "type",
                    "description": "what to do",
                    "evidence": ["field1", "field2"]
                }
            ],
            "evidence_used": ["list of data fields referenced"],
            "data_gaps": ["what information is missing"]
        }"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 3 exchanges
        
        user_content = f"""User Question: {message}

Available Context Data:
{json.dumps(context_data, indent=2, default=str)}"""
        
        messages.append({"role": "user", "content": user_content})
        
        response = self.chat_completion(messages)
        content = response["choices"][0]["message"]["content"]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "response": content,
                "structured_actions": [],
                "evidence_used": [],
                "data_gaps": ["Response parsing failed"]
            }

# Global client instance
groq_client = GroqClient()