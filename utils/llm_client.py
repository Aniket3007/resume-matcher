import os
from together import Together
from typing import Dict, Any

class TogetherLLMClient:
    def __init__(self):
        print("[DEBUG] Initializing TogetherLLMClient")
        api_key = os.getenv('TOGETHER_API_KEY')
        print(f"[DEBUG] API key found: {bool(api_key)}")
        
        if not api_key:
            print("[DEBUG] ERROR: TOGETHER_API_KEY environment variable not set")
            raise ValueError("TOGETHER_API_KEY environment variable not set")
        
        try:
            print("[DEBUG] Setting up Together client")
            os.environ['TOGETHER_API_KEY'] = api_key
            self.client = Together()
            self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
            print(f"[DEBUG] Together client initialized with model: {self.model}")
        except Exception as e:
            print(f"[DEBUG] Error initializing Together client: {str(e)}")
            raise
        
    def _make_request(self, messages: list) -> Dict[str, Any]:
        try:
            print("\n[DEBUG] ===== Making Together API Request =====")
            print(f"[DEBUG] Messages: {messages}")
            
            print("\n[DEBUG] ----- API Call Details -----")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Temperature: 0.7")
            print(f"[DEBUG] Max tokens: 500")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            print("\n[DEBUG] ----- Raw API Response -----")
            print(f"[DEBUG] Response type: {type(response)}")
            print(f"[DEBUG] Response dir: {dir(response)}")
            print(f"[DEBUG] Response repr: {repr(response)}")
            
            # Do NOT convert response to list or check for iterability; always return the raw response object
            return response
            
        except Exception as e:
            print(f"\n[DEBUG] !!!!! API REQUEST ERROR: {str(e)}")
            print(f"[DEBUG] Error type: {type(e)}")
            raise

    def get_completion(self, prompt: str):
        try:
            print("\n[DEBUG] ===== Starting get_completion =====")
            print(f"[DEBUG] Prompt length: {len(prompt)}")
            print(f"[DEBUG] First 200 chars of prompt:\n{prompt[:200]}...")
            
            messages = [{"role": "user", "content": prompt}]
            print(f"[DEBUG] Formatted messages: {messages}")
            
            print("\n[DEBUG] ----- Getting API Response -----")
            response = self._make_request(messages)
            
            print("\n[DEBUG] ----- Processing Response -----")
            print(f"[DEBUG] Response type: {type(response)}")
            if hasattr(response, 'choices') and len(response.choices) > 0:
                print(f"[DEBUG] Response .choices[0].message.content: {getattr(response.choices[0].message, 'content', None)}")
            return response
        except Exception as e:
            print(f"\n[DEBUG] !!!!! ERROR in get_completion: {str(e)}")
            print(f"[DEBUG] Error type: {type(e)}")
            raise

    def get_structured_output(self, text: str, output_format: str) -> Dict[str, Any]:
        prompt = f"""Extract the following information from this resume text into {output_format} format.
        If you're not confident about a field, leave it as null.
        Resume text:
        {text}"""
        
        response = self.get_completion(prompt)
        return response  # Caller should handle JSON parsing/validation
