# Tool Calling Bot

A chatbot that can use external tools through direct API calls to solve problems it can't answer alone. This bot demonstrates the core concept of AI agents - systems that can reason about when and how to use tools to accomplish tasks.

## Features
- Calculator Tool: Safely evaluate mathematical expressions including functions like sqrt, sin, cos, etc.
- Time Tool: Get current time in any timezone worldwide
- Web Search Tool: Search the web using DuckDuckGo's API

## Quick Start
1. Clone and Install
    ```bash
    git clone <your-repo-url>
    cd tool_calling_bot
    pip install -r requirements.txt
    ```

2. Get OpenAI API Keys
    - Visit: https://platform.openai.com/api-keys
    - Create an API key

3. Create .env
    - Set environment variable: OPENAI_API_KEY='your-key-here'    

4. Install Dependencies
    - openai>=1.0.0
    - requests>=2.25.0
    - python-dateutil>=2.8.0
    - pytz>=2021.1
    - sympy>=1.9 
    - python-dotenv>=0.19.0 
    ```bash
    pip install -r requirements.txt
    ```

5. Run the Bot
    ```bash
    python main.py
    ```
## Example Conversations
### 1. Calculator Query
```text
You: What is 15% of 847?
Using tool: calculator_tool
Bot: 15% of 847 is 127.05.
```

### 2. Time Query
```text
You: What time is it in Tokyo right now?
Using tool: get_current_time
Bot: Current time in Asia/Tokyo: 2024-08-01 14:30:22 JST (Thursday)
```

### 3. Web Search Query
```text
You: Search for recent news about artificial intelligence
Using tool: web_search
Bot: Search results for 'recent news about artificial intelligence':
Artificial intelligence (AI) is intelligence demonstrated by machines...
Source: Wikipedia
URL: https://en.wikipedia.org/wiki/Artificial_intelligence
```

### 4. Multi-Tool Query  
```text
You: What time is it in Tokyo, and what is 25% of 200?
Using tool: get_current_time
Using tool: calculator_tool
Bot: Here's the information you requested:
Time in Tokyo: Current time in Asia/Tokyo: 2024-08-01 14:30:22 JST (Thursday)
Calculation: 25% of 200 = 0.25 * 200 = 50
```
## Known Limitations
- Web Search: Limited to DuckDuckGo API results, may not have real-time information for all queries
- Calculator: Only supports safe mathematical operations (no file system access)
- Timezone: Requires exact timezone names (use pytz.all_timezones for full list)
- Rate Limits: Subject to API provider rate limits

## Demo Video
