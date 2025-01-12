from openai import OpenAI
import environ
import anthropic

env = environ.Env()
env.read_env(env.str('ENV_PATH','.env'))
OPEN_API_KEY = env('OPENAI_API_KEY')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY')

# Send all Openai requests through this function
# Can focus all the error handling here

def fetch_from_openai(prompt,model):

    try:
       
        client = OpenAI(api_key=OPEN_API_KEY)
        
        res = client.chat.completions.create(
            model=model,
            # max_tokens=max_tokens,
            messages=prompt,
            seed=42,
            top_p=0.2
        )

        # DB data
        model = res.model
        prompt_tokens = res.usage.prompt_tokens
        completion_tokens = res.usage.completion_tokens
        total_tokens = res.usage.total_tokens

        text = res.choices[0].message.content

        return [text, model, prompt_tokens, completion_tokens, total_tokens]    

    except Exception as e: raise



def get_text_from_openai(image_url):

    try:

        client = OpenAI(api_key=OPEN_API_KEY)

        res = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Transcribe the handwritten text only verbatim."},
                {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                },
                },
            ],
            }
        ],
        max_tokens=500,
        )

        return res.choices[0].message.content
    
    except Exception as e:
        print(e)

from pprint import pprint
def fetch_from_anthropic(prompt,model):

    try:
       
        client = anthropic.Anthropic()
        
        res = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=prompt,
            # seed=42,
            # top_p=0.2
        )

        pprint(res)

        # print(res.content[0].text)
        # print(f'MODEL: {res.model}')
        # print(f'PROMPT TOKENS: {res.usage.input_tokens}')
        # print(f'COMPLETION TOKENS: {res.usage.output_tokens}')
        # print(f'TOTAL TOKENS: {res.usage.input_tokens + res.usage.output_tokens}')

        # DB data
        model = res.model
        prompt_tokens = res.usage.input_tokens
        completion_tokens = res.usage.output_tokens
        total_tokens = prompt_tokens + completion_tokens
        text = res.content[0].text

        return [text, model, prompt_tokens, completion_tokens, total_tokens]    

    except Exception as e: raise