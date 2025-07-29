import os
import json
import sys
from config import load_openai_key
from typing import Dict, List, Any
from tools import calculator_tool, get_current_time, web_search

def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Define tool schemas for the LLM
    
    Returns:
        List[Dict[str, Any]]: List of tool schema dictionaries in OpenAI format.
            Each dictionary contains:
            - type: Always "function" for function calling
            - function: Dictionary with name, description, and parameters
                - name: Function name that matches your Python function
                - description: What the function does (helps LLM decide when to use it)
                - parameters: JSON Schema defining function parameters

    """

    # Define tool schemas
    tool_schemas = [
        {
            "type": "function",
            "function": {
                "name": "calculator_tool",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "get_current_time",
                "description": "Get the current time in a specified timezone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone string like 'UTC', 'US/Eastern', 'Asia/Tokyo', 'Europe/London'"
                        }
                    },
                    "required": ["timezone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search", 
                "description": "Search the web and return top results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search terms to look for"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-5)",
                            "minimum": 1,
                            "maximum": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    print(f"Tool schemas loaded successfully. Available tools: {len(tool_schemas)}")
    return tool_schemas

def call_appropriate_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute the appropriate tool function based on the tool call from the LLM.
    
    Args:
        tool_name (str): Name of the tool to execute. Must match one of:
            - "calculator_tool": For mathematical calculations
            - "get_current_time": For timezone-aware time queries
            - "web_search": For internet search functionality
            
        arguments (Dict[str, Any]): Dictionary of arguments to pass to the tool.
            The structure depends on the specific tool:
            - calculator_tool: {"expression": "math expression"}
            - get_current_time: {"timezone": "timezone string"}
            - web_search: {"query": "search terms", "num_results": integer}
    
    Returns:
        str: Result from the tool execution, or error message if tool fails.
            Success format depends on the tool used.
            Error format: "Error: [description]" or "Error executing [tool]: [details]"
    """
    # Validate tool name and route to appropriate tool function
    try:
        if tool_name == "calculator_tool":
            return calculator_tool(arguments.get("expression", ""))
        elif tool_name == "get_current_time":
            return get_current_time(arguments.get("timezone", "UTC"))
        elif tool_name == "web_search":
            return web_search(arguments.get("query", ""), arguments.get("num_results", 3)
            )
        else:
            return f"Error: Unknown tool '{tool_name}'"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

def chat_with_llm(client, messages: List[Dict], tools: List[Dict]) -> str:
    """
    Handle OpenAI API conversation with tool calling functionality.

    Args:
        client: OpenAI client instance configured with API key
        messages (List[Dict]): Conversation history in OpenAI format.
            Each message has 'role' and 'content' fields.
        tools (List[Dict]): Tool schemas defining available functions.
            Must follow OpenAI Function Calling specification.
    
    Returns:
        str: Final response from the LLM after any tool calls are completed.
            This is the message content that should be displayed to the user.
    
    Raises:
        Exception: Re-raises any critical errors that prevent communication
    """

    print("Sending request to OpenAI...")
    try:
        # Call the OpenAI API with the provided messages and tools
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto"
        )
        

        # Get the response message from the API
        response_message = response.choices[0].message
        
        # Check if the model wants to call tools
        if response_message.tool_calls:
            # Add the assistant's response to messages
            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in response_message.tool_calls
                ]
            })
            
            # Execute each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"Using tool: {function_name}")
                tool_result = call_appropriate_tool(function_name, function_args)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Get final response from the model
            final_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto"
            )
            
            return final_response.choices[0].message.content
        else:
            return response_message.content
            
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"

def chat_interface(client, messages: List[Dict], tools: List[Dict]) -> None:
    """
    Interactive chat interface for the tool calling bot.
    
    Args:
        client: OpenAI client instance for API calls
        messages (List[Dict]): Conversation history including system message
        tools (List[Dict]): Available tool schemas for function calling
        
    Returns:
        None
        
    Raises:
        KeyboardInterrupt: When user presses Ctrl+C (handled by caller)
        Exception: For unexpected errors during chat processing
    """

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif not user_input:
                continue
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get response based on API provider
            try:
                response = chat_with_llm(client, messages, tools)
                print(f"\nBot: {response}\n")

                # Add assistant response to conversation history
                messages.append({"role": "assistant", "content": response})
            except Exception as e:
                print(f"Error : Unexpected error encountered: {str(e)}")    
                messages.pop()

        except KeyboardInterrupt:
            raise    
            
def main() -> None:
    """
    Main chat loop. This function orchestrates the entire bot lifecycle:
        1. Displays welcome message and available commands
        2. Initializes the OpenAI API client
        3. Sets up the conversation context with system message
        4. Loads tool schemas for function calling
        5. Starts the interactive chat interface

    Returns:
        None
        
    Raises:
        SystemExit: If critical initialization fails   
    """

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                               TOOL CALLING BOT                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  AI-powered assistant with mathematical, time, and web search capabilities   ║
║                                                                              ║
║  Calculator    - Math expressions, percentages, functions                    ║
║  Time Helper   - Current time in any timezone                                ║
║  Web Search    - Find information on the internet                            ║
║                                                                              ║
║  Commands: 'quit' to exit                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize API client
    try:
        print("Initializing OpenAI API client...")
        client = load_openai_key()
        print("API client initialized successfully")
    except Exception as e:
        print(f"Error: Failed initializing API client: {e}")
        sys.exit(1)

    # Initialize conversation context
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant with access to three tools: "
                "calculator_tool for mathematical calculations and percentages, "
                "get_current_time for timezone-aware time queries, and "
                "web_search for finding information online. "
                
                "Always be conversational and explain what tools you're using. "
                "When using tools, briefly explain why you chose that tool. "
                "Format your responses to be helpful and easy to read. "
                
                "For calculations, handle both simple math and complex expressions. "
                "For time queries, always specify the timezone clearly. "
                "For web searches, summarize the most relevant information found."
            )
        }
    ]
    
    # Load tool schemas
    print("Loading tool schemas...")
    try:
        tools = get_tool_schemas() 
    except Exception as e:
        print(f"Error executing {tool_name}: {str(e)}")
        sys.exit(1)

    print("Tool schemas loaded successfully")

    # Start the chat interface
    print("Starting chat interface...")
    try:
        chat_interface(client, messages, tools)  
    except KeyboardInterrupt:
        print("\n\nChat interrupted by you. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: Unexpected error in chat interface: {e}")
        sys.exit(1)
    
    # User typed 'quit' or chat ended normally
    print("\nThanks for using Tool Calling Bot!")    

if __name__ == "__main__":      
    main()      