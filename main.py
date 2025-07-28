import os
from config import load_openai_key

# def chat_interface():
#     """Interactive chat interface for the tool calling bot."""

#     while True:
#         try:
#             # Get user input
#             user_input = input("You: ").strip()
            
#             if user_input.lower() in ['quit', 'exit', 'q']:
#                 print("Goodbye!")
#                 break
#             elif user_input.lower() == 'help':
#                 print("\nCommands:")
#                 print("- Ask math questions: 'What's 15% of 847?'")
#                 print("- Ask for time: 'What time is it in Tokyo?'")
#                 print("- Search the web: 'Search for Python tutorials'")
#                 print("- Type 'quit' to exit")
#                 print()
#                 continue
#             elif not user_input:
#                 continue
            
#             # Add user message
#             messages.append({"role": "user", "content": user_input})
            
#             # Get response based on API provider
#             response = chat_with_openai(client, messages, tools)
            
#             print(f"\nBot: {response}\n")
            
#             # Add assistant response to conversation history
#             messages.append({"role": "assistant", "content": response})
            
#         except KeyboardInterrupt:
#             print("\n Goodbye!")
#             break
#         except Exception as e:
#             print(f"Unexpected error: {e}")
#             print("Continuing...\n")


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
    
    # tools = get_tool_schemas()  

    # chat_interface()  

if __name__ == "__main__":      
    main()      