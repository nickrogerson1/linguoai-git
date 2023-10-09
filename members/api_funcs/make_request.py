import openai
import environ

env = environ.Env()
env.read_env(env.str('ENV_PATH','.env'))
openai.api_key = env('OPENAI_API_KEY')

# Send all Openai requests through this function
# Can focus all the error handling here

def fetch_from_openai(prompt,model,max_tokens,temp):

    try:
        res = openai.ChatCompletion.create(
            messages=prompt,
            model=model,
            max_tokens=max_tokens,
        # Alter temp or top_p - not both!
            temperature=temp,
            # top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
    
        # DB data
        model = res['model']
        prompt_tokens = res['usage']['prompt_tokens']
        completion_tokens = res['usage']['completion_tokens']
        total_tokens = res['usage']['total_tokens']

        result = res['choices'][0]['message']['content']
        print(result)

        return [result, model, prompt_tokens, completion_tokens, total_tokens]    

    except Exception as e: raise