import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, SafetySetting, Part
from google.ai.generativelanguage_v1beta.types import ToolCall as GeminiToolCall  # Correct import
from google.ai.generativelanguage_v1beta.types import ToolFunction as GeminiToolFunction # Correct import


from .utils.prompt import ClientMessage, convert_to_gemini_messages, system_prompt_content
from .utils.tools import get_current_weather, get_search_results_tavily

load_dotenv(".env.local")

app = FastAPI()

# Configure Gemini model
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.0-flash-thinking-exp-01-21")

# Enable/Disable Weather Tool from environment variable
WEATHER_TOOL_ENABLED = os.environ.get("TOGGLE_WEATHER_TOOL") == 'true'
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

available_tools = {}
if WEATHER_TOOL_ENABLED:
    available_tools["get_current_weather"] = get_current_weather
if TAVILY_API_KEY:  # Only add Tavily tool if API key is available
    available_tools["get_search_results_tavily"] = lambda query: get_search_results_tavily(query, api_key=TAVILY_API_KEY)


class Request(BaseModel):
    messages: List[ClientMessage]
    user_name: Optional[str] = Field(default=None, description="User's name for greeting")

def generate_gemini_tool_config():
    tool_config = []
    if WEATHER_TOOL_ENABLED:
        weather_tool_function = GeminiToolFunction(
            name="get_current_weather",
            description="Get the current weather at a location",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "latitude": {
                        "type": "NUMBER",
                        "description": "The latitude of the location",
                    },
                    "longitude": {
                        "type": "NUMBER",
                        "description": "The longitude of the location",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        )
        weather_tool = {"function_declarations": [weather_tool_function]}
        tool_config.append(weather_tool)

    if TAVILY_API_KEY: # Only include Tavily tool if API key is available
        tavily_tool_function = GeminiToolFunction(
            name="get_search_results_tavily",
            description="Get search results from Tavily for a query",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        )
        tavily_tool = {"function_declarations": [tavily_tool_function]}
        tool_config.append(tavily_tool)

    return tool_config


def stream_text(messages: List[ChatCompletionMessageParam], user_name: Optional[str] = None, protocol: str = 'data'):
    gemini_messages = convert_to_gemini_messages(messages, user_name=user_name)
    tool_config = generate_gemini_tool_config()

    generation_config = GenerationConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=65536,
        response_mime_type="text/plain",
    )
    safety_settings = [
        SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
        SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    ]


    stream = model.generate_content(
        contents=gemini_messages,
        generation_config=generation_config,
        safety_settings=safety_settings,
        tools=tool_config if tool_config else None, # Pass tools conditionally
        stream=True,
    )

    draft_tool_calls = []
    draft_tool_calls_index = -1


    try:
        for chunk in stream:
            for candidate in chunk.candidates:
                if candidate.finish_reason:
                    continue  # Skip if the candidate has a finish reason (e.g., stop)

                part = candidate.content.parts[0] # Gemini returns parts in content

                if isinstance(part, Part.text): # Text response
                    text = part.text
                    if text:
                        yield f'0:{json.dumps(text)}\n'

                elif part.function_call: # Tool call
                    tool_call = part.function_call

                    tool_call_id = f"tool_call_{draft_tool_calls_index + 1}" # Generate a unique ID
                    tool_name = tool_call.name
                    tool_arguments = tool_call.args

                    draft_tool_calls_index += 1
                    draft_tool_calls.append({
                        "id": tool_call_id,
                        "name": tool_name,
                        "arguments": tool_arguments
                    })

                    yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                        id=tool_call_id,
                        name=tool_name,
                        args=json.dumps(tool_arguments))


            if chunk.candidates == []: # Handle empty chunk -  Gemini might not send usage info like OpenAI
                yield 'e:{{"finishReason":"tool-calls" if len(draft_tool_calls) > 0 else "stop","usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n' # Placeholder usage


        # Process tool calls after stream ends
        if draft_tool_calls:
            for tool_call in draft_tool_calls:
                tool_result = available_tools[tool_call["name"]](**tool_call["arguments"])

                yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                    id=tool_call["id"],
                    name=tool_call["name"],
                    args=json.dumps(tool_call["arguments"]),
                    result=json.dumps(tool_result))

            yield 'e:{{"finishReason":"tool-calls","usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n' # Finish reason for tool calls

        else:
             yield 'e:{{"finishReason":"stop","usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n' # Finish reason for regular stop


    except Exception as e:
        print(f"Streaming error: {e}")
        yield f'e:{{"finishReason":"error","error":"Streaming error: {str(e)}","usage":{{"promptTokens":0,"completionTokens":0}},"isContinued":false}}\n' # Error finish reason


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    user_name = request.user_name  # Extract user_name from the request

    openai_messages = convert_to_gemini_messages(messages, user_name=user_name) # Correctly convert messages, passing user_name
    response = StreamingResponse(stream_text(openai_messages, user_name=user_name, protocol=protocol)) # Pass user_name to stream_text
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response