from g4f.client import AsyncClient
from src.analyzer.promt import ROLE
from g4f.Provider import RetryProvider, Bing, GeekGpt, Liaobots, Phind, Raycast

async def get_analyzed(content: str, tool_call_query: str):
    client = AsyncClient(provider=RetryProvider([Bing, GeekGpt, Liaobots, Phind, Raycast], shuffle=True))
    tool_call = {
        "type": "function",
        "function": {
            "name": "search_tool",
            "arguments": {
            "query": tool_call_query,
            "max_results": 5,
            "max_words": 1500,
            "backend": "auto",
            "add_text": True,
            "timeout": 10
            }
        }
    }
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "developer", "content": ROLE},
                  {"role": "user", "content": content}],
        tool_call=tool_call
    )
    return response.choices[0].message.content
