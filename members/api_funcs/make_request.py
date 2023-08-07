import openai, time
import environ

env = environ.Env()
env.read_env(env.str('ENV_PATH','.env'))
openai.api_key = env('OPENAI_API_KEY')

# Send all Openai requests through this function
# Can focus all the error handling here

# If you add any parameters to this function,
# Make sure you add them to the recursive error handlers!!

# Added count as a parameter to stop weird global variable results
def fetch_from_openai(prompt,model,max_tokens,temp,count=1):

    try:
        res = openai.ChatCompletion.create(
            messages=prompt,
            model=model,
            max_tokens=max_tokens,
        # Alter temp or top_p - not both!
            temperature=temp,
            # top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
    
        # DB data
        model = res['model']
        prompt_tokens = res['usage']['prompt_tokens']
        completion_tokens = res['usage']['completion_tokens']
        total_tokens = res['usage']['total_tokens']

        result = res['choices'][0]['message']['content']
        print(result)
        # result = model = 'text'
        # prompt_tokens = completion_tokens = total_tokens = 1
        return [result, model, prompt_tokens, completion_tokens, total_tokens]    

    except Exception as e:
        print(repr(e))

    # Make three attempts to contact OpenAI
        if count < 3:
            print('Waiting 5 seconds...')
            time.sleep(5)
            count += 1
            print(f'count: {count}')
            return fetch_from_openai(prompt,model,max_tokens,temp,count)
        return False