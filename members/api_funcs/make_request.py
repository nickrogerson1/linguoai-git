from openai import OpenAI
import environ

env = environ.Env()
env.read_env(env.str('ENV_PATH','.env'))
api_key = env('OPENAI_API_KEY')

# Send all Openai requests through this function
# Can focus all the error handling here

def fetch_from_openai(prompt,model,temp):

    try:
       
        client = OpenAI(api_key=api_key)
        
        res = client.chat.completions.create(
            model=model,
            # max_tokens=max_tokens,
            messages=prompt,
            seed=42
        )

        # DB data
        model = res.model
        prompt_tokens = res.usage.prompt_tokens
        completion_tokens = res.usage.completion_tokens
        total_tokens = res.usage.total_tokens

        result = res.choices[0].message.content

        return [result, model, prompt_tokens, completion_tokens, total_tokens]    

    except Exception as e: raise