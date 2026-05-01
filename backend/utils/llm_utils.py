import json
import re

def extract_json(text: str) -> any:
    """
    Extracts JSON from text, handling markdown code blocks and reasoning blocks.
    """
    # 1. Handle potential reasoning blocks (e.g. <think>...</think>)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # 2. Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        content = json_match.group(1).strip()
    else:
        content = text.strip()
    
    # 3. Basic cleanup of potential leading/trailing garbage
    if not content.startswith('{') and not content.startswith('['):
        start_idx = content.find('{')
        if start_idx == -1:
            start_idx = content.find('[')
        
        if start_idx != -1:
            content = content[start_idx:]
            
        # Try to find the end
        end_idx = content.rfind('}')
        if end_idx == -1:
            end_idx = content.rfind(']')
            
        if end_idx != -1:
            content = content[:end_idx+1]
            
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # If it's still not valid, try one last attempt at cleaning
        # Sometimes there's text after the JSON
        try:
            # Simple heuristic: find first { or [ and last } or ]
            return json.loads(content)
        except:
            raise ValueError(f"Could not parse JSON from response: {text[:200]}...")
