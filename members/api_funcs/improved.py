from .make_request import fetch_from_openai


def get_improved_submission(original_text):

    messages = [
        {"role": "system", "content": "You are a writing editor."},
        {"role": "user", 
        "content": f"This is a text written by a non-native English speaker. Improve the text to make it seem like it was written by an English native speaker.\n\nHere is the text:\n\n{original_text}"}
    ]


    model='gpt-4-1106-preview'
    # model='gpt-3.5-turbo'
    # max_tokens=5000

    try:
        return fetch_from_openai(messages,model)
    except Exception as e: raise