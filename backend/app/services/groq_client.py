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
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Make a chat completion request to Groq API"""
        try:
            # Remove JSON format requirement as it may cause issues
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
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
        
        Analyze the data and provide insights in this format:
        EXECUTIVE SUMMARY: [Brief overview of key risks and opportunities]
        
        TOP ACTIONS:
        1. [Action type] - [Priority] - [Description] - [Expected impact]
        2. [Action type] - [Priority] - [Description] - [Expected impact]
        3. [Action type] - [Priority] - [Description] - [Expected impact]
        
        KEY METRICS:
        - Total at-risk value: [value]
        - High-risk batches: [count]
        - Average days to expiry: [days]
        
        ASSUMPTIONS:
        - [List key assumptions made]"""
        
        user_prompt = f"""Analyze this inventory risk data and provide actionable insights:

Context Data:
{json.dumps(context_data, indent=2, default=str)}

Filters Applied: {filters or 'None'}

Focus on the highest risk items and most impactful actions. Cite specific evidence from the data."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.chat_completion(messages)
            content = response["choices"][0]["message"]["content"]
            
            # Parse the structured response
            return self._parse_insights_response(content, context_data)
        except Exception as e:
            # Fallback response
            return {
                "executive_summary": f"Analysis completed but AI parsing failed: {str(e)}",
                "prioritized_actions": [],
                "key_metrics": context_data.get("key_metrics", {}),
                "assumptions": ["AI response parsing failed"]
            }

    def _parse_insights_response(self, content: str, context_data: Dict) -> Dict[str, Any]:
        """Parse the AI response into structured format"""
        lines = content.split('\n')
        
        result = {
            "executive_summary": "",
            "prioritized_actions": [],
            "key_metrics": context_data.get("key_metrics", {}),
            "assumptions": []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("EXECUTIVE SUMMARY:"):
                result["executive_summary"] = line.replace("EXECUTIVE SUMMARY:", "").strip()
                current_section = "summary"
            elif line.startswith("TOP ACTIONS:"):
                current_section = "actions"
            elif line.startswith("KEY METRICS:"):
                current_section = "metrics"
            elif line.startswith("ASSUMPTIONS:"):
                current_section = "assumptions"
            elif current_section == "actions" and line.startswith(("1.", "2.", "3.", "4.", "5.")):
                # Parse action line: "1. markdown - high - Apply 30% discount - Save $500"
                parts = line.split(" - ", 3)
                if len(parts) >= 3:
                    action = {
                        "action_type": parts[1].strip() if len(parts) > 1 else "unknown",
                        "priority": parts[2].strip() if len(parts) > 2 else "medium",
                        "description": parts[3].strip() if len(parts) > 3 else parts[0].strip(),
                        "confidence": 0.8,
                        "expected_impact": "AI-generated recommendation"
                    }
                    result["prioritized_actions"].append(action)
            elif current_section == "assumptions" and line.startswith("-"):
                result["assumptions"].append(line[1:].strip())
        
        return result

    def chat_response(self, message: str, context_data: Dict[str, Any], conversation_history: list = None) -> Dict[str, Any]:
        """Generate conversational response with context"""
        system_prompt = """You are a helpful supply chain analyst assistant. Answer questions about inventory risk data.
        
        Rules:
        - Only use data provided in the context
        - Cite specific evidence fields when making claims
        - If data is missing, explicitly state this and ask for clarification
        - Never invent SKUs, quantities, or database values
        - Provide structured actions when relevant
        - Be conversational and helpful"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 3 exchanges
        
        user_content = f"""User Question: {message}

Available Context Data:
{json.dumps(context_data, indent=2, default=str)}"""
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            response = self.chat_completion(messages)
            content = response["choices"][0]["message"]["content"]
            
            return {
                "response": content,
                "structured_actions": [],  # Could be enhanced to parse actions from response
                "evidence_used": ["AI analyzed available context data"],
                "data_gaps": []
            }
        except Exception as e:
            return {
                "response": f"I'm sorry, I encountered an error: {str(e)}. Please try again.",
                "structured_actions": [],
                "evidence_used": [],
                "data_gaps": ["AI service temporarily unavailable"]
            }

# Global client instance
groq_client = GroqClient()