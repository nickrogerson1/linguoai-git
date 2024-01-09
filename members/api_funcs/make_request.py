from openai import OpenAI
import environ

env = environ.Env()
env.read_env(env.str('ENV_PATH','.env'))
api_key = env('OPENAI_API_KEY')

# Send all Openai requests through this function
# Can focus all the error handling here

def fetch_from_openai(prompt,model):

    try:
       
        client = OpenAI(api_key=api_key)
        
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

        result = res.choices[0].message.content

        return [result, model, prompt_tokens, completion_tokens, total_tokens]    

    except Exception as e: raise



def get_text_from_openai(image_url):

    try:

        client = OpenAI(api_key=api_key)

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