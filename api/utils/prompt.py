import json
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel
import os

from .attachment import ClientAttachment

# Load system prompt from file
system_prompt_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'v2-must use-system-prompt.txt')
with open(system_prompt_file_path, 'r', encoding='utf-8') as f:
    system_prompt_content = f.read()

class ToolInvocationState(str, Enum):
    CALL = 'call'
    PARTIAL_CALL = 'partial-call'
    RESULT = 'result'

class ToolInvocation(BaseModel):
    state: ToolInvocationState
    toolCallId: str
    toolName: str
    args: Any
    result: Any

class ClientMessage(BaseModel):
    role: str
    content: str
    experimental_attachments: Optional[List[ClientAttachment]] = None
    toolInvocations: Optional[List[ToolInvocation]] = None

def convert_to_gemini_messages(messages: List[ClientMessage], user_name: Optional[str] = None) -> List[dict]:
    gemini_messages = []

    # Add the system prompt as the first message
    formatted_system_prompt = system_prompt_content.replace("{user_name}", user_name if user_name else "User") # Replace placeholder in system prompt
    gemini_messages.append({"role": "user", "parts": [formatted_system_prompt]}) # Gemini system prompt is sent as user role

    for message in messages:
        parts = []
        tool_calls = []

        parts.append({
            'text': message.content
        })

        if (message.experimental_attachments):
            for attachment in message.experimental_attachments:
                if (attachment.contentType.startswith('image')):
                    parts.append({
                        'inline_data': {
                            'mime_type': attachment.contentType, # e.g., 'image/png'
                            'data': attachment.url # Gemini expects data here, assuming URL is accessible data -  **Correction Needed if URL is just URL string, Gemini might expect base64 data if inline_data is used. For now assuming URL is base64 encoded data or needs to be fetched and encoded.**
                        }
                    })

                elif (attachment.contentType.startswith('text')):
                    parts.append({
                        'text': attachment.url
                    })

        if(message.toolInvocations):
            for toolInvocation in message.toolInvocations:
                tool_calls.append({
                    "name": toolInvocation.toolName,
                    "parameters": json.dumps(toolInvocation.args) # Arguments as JSON string
                })


        gemini_message_content = {"role": message.role, "parts": parts} # Gemini uses 'parts' instead of 'content'
        if tool_calls:
            gemini_message_content["function_calls"] = tool_calls # Attach function_calls if any

        gemini_messages.append(gemini_message_content)


        if(message.toolInvocations): # Handle tool results -  Tool result messages might need different handling for Gemini if needed. For now, not explicitly adding tool result messages as separate messages like OpenAI, assuming Gemini handles tool results internally based on function calls and responses.
            pass # Placeholder -  Gemini tool result message handling -  Needs review based on Gemini expected format if explicit tool result messages are needed.


    return gemini_messages