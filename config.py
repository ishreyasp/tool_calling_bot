import os
from openai import OpenAI
from dotenv import load_dotenv

def load_openai_key():
    """
    Initialize and return the OpenAI client with API key from environment variables.
    
    Returns:
        API client instance (OpenAI)
    
    Raises:
        ValueError: If API key is not set or provider is invalid
        ImportError: If required library is not installed

    Environment Variables:
        OPENAI_API_KEY (str): Your OpenAI API key from https://platform.openai.com/api-keys
    
    Returns:
        Configured OpenAI client instance ready for API calls
    
    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set or empty
        ImportError: If OpenAI library is not installed
        Exception: If OpenAI client initialization fails (e.g., invalid API key)    
    """

    # Load environment variables from .env file
    load_dotenv()

    # Get OpenAI API key from environment variable
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Check if API key is set
    if not OPENAI_API_KEY:
            raise ValueError("Error: OpenAI API key not found! Please set the OPENAI_API_KEY environment variable.")

    # Validate that the API key is not just whitespace
    if not OPENAI_API_KEY.strip():
        raise ValueError("Error: OpenAI API key cannot be empty or only whitespace")

    # Initialize OpenAI client with the API key    
    try: 
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI API key loaded successfully.")
        return client
    except ImportError:
        raise ImportError("Error: OpenAI library not installed")
    except Exception as e:
        raise Exception(f"Error: Failed to initialize OpenAI client: {str(e)}")