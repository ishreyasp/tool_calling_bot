import os
import json
import sys
from config import load_openai_key
from typing import Dict, List, Any
from tools import calculator_tool, get_current_time, web_search

# Window size for conversation memory
WINDOW_SIZE = 3

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are a helpful assistant with access to three tools:
- calculator_tool for mathematical calculations, percentages, and functions. 
  For example if user asks What is 15 percent of 847, you should reply with "15 percent of 847 is 127.05".
- get_current_time for timezone-aware time queries  
  For example if user asks What is the current time in US/Eastern, you should reply with "The current time in US/Eastern is 2023-10-01 12:00:00".
- web_search for finding information online
  For example if user asks What is the capital of France, you should reply with "The capital of France is Paris".

You can chain tools together when needed. For example:
- Get current time and use the result in calculations
- Search for information and then calculate percentages from the data
- Use results from one tool as input to another tool

Always be conversational, explain what tools you're using and explain your reasoning when chaining tools. 
After getting tool results, provide a complete answer with the actual results."""

# Full chat history storage
chat_history = []

def build_prompt_windowed(chat_history, user_input):
    """
    Build a prompt using only the most recent WINDOW_SIZE exchanges.
    
    Args:
        chat_history (List[Dict[str, str]]): Full chat history with user and AI messages
        user_input (str): Current user input to include in the prompt

    Returns:
        List[Dict[str, str]]: List of messages formatted for OpenAI API    
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Get the most recent WINDOW_SIZE exchanges
    if len(chat_history) > WINDOW_SIZE:
        recent_history = chat_history[-WINDOW_SIZE:]
    else:
        recent_history = chat_history
    
    # Add recent exchanges to messages
    for entry in recent_history:
        messages.append({"role": "user", "content": entry['user']})
        messages.append({"role": "assistant", "content": entry['ai']})
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    return messages

def add_to_chat_history(user_input: str, ai_response: str):
    """
    Add a user-AI exchange to the chat history.
    
    Args:
        user_input (str): The user's message
        ai_response (str): The AI's response
    """
    global chat_history
    
    exchange = {
        'user': user_input,
        'ai': ai_response
    }
    
    chat_history.append(exchange)

def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Define tool schemas for the LLM
    
    Returns:
        List[Dict[str, Any]]: List of tool schema dictionaries in OpenAI format.
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
        tool_name (str): Name of the tool to execute. 
            
        arguments (Dict[str, Any]): Dictionary of arguments to pass to the tool.
    
    Returns:
        str: Result from the tool execution, or error message if tool fails.
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
    """
    print("Sending request to OpenAI...")
    try:
        # Call the OpenAI API with the provided messages and tools
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto",
            temperature=0.1
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
            for i, tool_call in enumerate(response_message.tool_calls, 1):
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"   {i}. Using tool: {function_name}")
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
                tool_choice="auto",
                temperature=0.1
            )
            
            final_content = final_response.choices[0].message.content
            
            # Support for additional tool chaining if LLM requests more tools
            if final_response.choices[0].message.tool_calls:
                print("Additional tool chaining detected, continuing...")
                # Add the new assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": final_content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in final_response.choices[0].message.tool_calls
                    ]
                })
                
                # Execute additional tools
                for tool_call in final_response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Chaining tool: {function_name}")
                    tool_result = call_appropriate_tool(function_name, function_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Get final response after chaining
                chained_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice="auto",
                    temperature=0.1
                )
                
                return chained_response.choices[0].message.content or final_content
        
            return final_content
            
        else:
            return response_message.content
            
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"

def chat_interface(client, tools: List[Dict]) -> None:
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
            messages = build_prompt_windowed(chat_history, user_input)
            
            # Get response based on API provider
            try:
                response = chat_with_llm(client, messages, tools)
                print(f"\nBot: {response}\n")

                # Add exchange to chat history for windowed memory
                add_to_chat_history(user_input, response)

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
            ║  Commands: 'quit', 'q', 'exit' to exit                                       ║
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
    
    # Load tool schemas
    print("Loading tool schemas...")
    try:
        tools = get_tool_schemas() 
    except Exception as e:
        print(f"Error: Failed loading tool schemas: {e}")
        sys.exit(1)

    # Start the chat interface
    print("Starting chat interface...")
    try:
        chat_interface(client, tools)  
    except KeyboardInterrupt:
        print("\n\nChat interrupted by you. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: Unexpected error in chat interface: {e}")
        sys.exit(1)
    
    print("\nThanks for using Tool Calling Bot!")    

if __name__ == "__main__":      
    main()      