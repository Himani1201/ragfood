import os
import time
from dotenv import load_dotenv
from groq import Groq
from groq._exceptions import RateLimitError, APIError, AuthenticationError, APIConnectionError

# Load environment
load_dotenv()


class GroqLLMClient:
    """Wrapper for Groq API with error handling and retry logic"""
    
    def __init__(self):
        """Initialize Groq client from environment variables"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment. Please add it to .env file.")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        self.max_retries = 3
        self.retry_delay = 1
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.input_tokens = 0  # Per-query tokens
        self.output_tokens = 0  # Per-query tokens
        
        self._verify_connection()
    
    def _verify_connection(self):
        """Test connection on startup"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            print(f"✅ Connected to Groq API")
            print(f"   Model: {self.model}")
            return True
        except AuthenticationError:
            raise Exception("❌ Invalid GROQ_API_KEY. Please check your credentials.")
        except Exception as e:
            raise Exception(f"❌ Cannot reach Groq API: {e}")
    
    def generate_answer(self, prompt, context=None, max_tokens=1024, temperature=0.7):
        """
        Generate answer with retry logic and error handling.
        
        Args:
            prompt: Question/instruction text
            context: Optional context to include in prompt
            max_tokens: Maximum tokens in response
            temperature: Creativity (0-2, lower=more focused)
        
        Returns:
            Generated answer text
        """
        # Ensure max_tokens is an integer
        max_tokens = int(max_tokens)
        
        # Build full prompt with context if provided
        if context:
            full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
        else:
            full_prompt = prompt
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Track usage for cost monitoring
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                self.total_requests += 1
                
                # Store per-query tokens for immediate access
                self.input_tokens = response.usage.prompt_tokens
                self.output_tokens = response.usage.completion_tokens
                
                print(f"📊 Tokens - Input: {response.usage.prompt_tokens}, "
                      f"Output: {response.usage.completion_tokens} "
                      f"(Total: {self.total_input_tokens + self.total_output_tokens})")
                
                return response.choices[0].message.content
            
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"⚠️  Rate limit reached, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Rate limit: {e}")
                    raise
            
            except APIConnectionError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"⚠️  Connection error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Connection failed: {e}")
                    raise
            
            except APIError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"⚠️  API error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ API error: {e}")
                    raise
            
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise
    
    def get_cost(self, input_tokens=None, output_tokens=None):
        """Calculate estimated cost in USD
        
        Args:
            input_tokens: Optional specific input tokens (default uses total)
            output_tokens: Optional specific output tokens (default uses total)
        """
        # Groq pricing: $0.0002 per 1k input tokens, $0.0006 per 1k output tokens
        if input_tokens is None:
            input_tokens = self.total_input_tokens
        if output_tokens is None:
            output_tokens = self.total_output_tokens
        
        input_cost = (input_tokens / 1000) * 0.0002
        output_cost = (output_tokens / 1000) * 0.0006
        return input_cost + output_cost
    
    def print_usage_summary(self):
        """Print usage and cost summary"""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        cost = self.get_cost()
        
        print("\n" + "="*50)
        print("📊 USAGE SUMMARY")
        print("="*50)
        print(f"Total requests: {self.total_requests}")
        print(f"Input tokens: {self.total_input_tokens:,}")
        print(f"Output tokens: {self.total_output_tokens:,}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"💰 Estimated cost: ${cost:.4f}")
        print("="*50 + "\n")
