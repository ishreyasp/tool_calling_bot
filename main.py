import os
import json
from config import load_openai_key
from typing import Dict, List, Any
from tools import calculator_tool, get_current_time, web_search

def get_tool_schemas() -> List[Dict[str, Any]]:
    """Define tool schemas for the LLM"""

    return [
        {
            "type": "function",
            "function": {
                "name": "calculator_tool",
                "description": "Perform mathematical calculations and evaluate expressions",
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


def chat_interface():
    """Interactive chat interface for the tool calling bot."""

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("\nCommands:")
                print("- Ask math questions: 'What's 15% of 847?'")
                print("- Ask for time: 'What time is it in Tokyo?'")
                print("- Search the web: 'Search for Python tutorials'")
                print("- Type 'quit' to exit")
                print()
                continue
            elif not user_input:
                continue
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get response based on API provider
            response = chat_with_llm(client, messages, tools)
            
            print(f"\nBot: {response}\n")
            
            # Add assistant response to conversation history
            messages.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            print("Continuing...\n")

def call_appropriate_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute the appropriate tool function based on the tool call"""

    try:
        if tool_name == "calculator_tool":
            return calculator_tool(arguments.get("expression", ""))
        elif tool_name == "get_current_time":
            return get_current_time(arguments.get("timezone", "UTC"))
        elif tool_name == "web_search":
            return web_search(
                arguments.get("query", ""),
                arguments.get("num_results", 3)
            )
        else:
            return f"Error: Unknown tool '{tool_name}'"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

def chat_with_llm(client, messages: List[Dict], tools: List[Dict]) -> str:
    """Handle OpenAI API conversation with tool calling"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
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
                model="gpt-4",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            return final_response.choices[0].message.content
        else:
            return response_message.content
            
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"

def main():
    """Main chat loop"""

    print("Tool Calling Bot")
    print("Available tools: calculator, current time, web search")
    print("Type 'quit' to exit, 'help' for commands\n")
    
    # Initialize API client
    try:
        client = get_api_client()
    except Exception as e:
        print(f"Error initializing API client: {e}")
        return

    # Initialize conversation
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to tools. Use the calculator_tool for math, get_current_time for time queries, and web_search for finding information online. Be conversational and explain what tools you are using."
        }
    ]
    
    tools = get_tool_schemas()  

    chat_interface()  

if __name__ == "__main__":      
    main()      