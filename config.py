import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_openai_key():
    """
    Initialize and return the OpenAI client.
    
    Returns:
        API client instance (OpenAI)
    
    Raises:
        ValueError: If API key is not set or provider is invalid
        ImportError: If required library is not installed
    """
    
    if not OPENAI_API_KEY:
            raise ValueError( "OpenAI API key not found! Please set the OPENAI_API_KEY environment variable.")

    try: 
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI API key loaded successfully.")
        return client
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Install it with: pip install openai"
            )
        
        