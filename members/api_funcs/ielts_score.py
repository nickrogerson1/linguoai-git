from .band_desc_instruct import instructions
from .make_request import fetch_from_openai


def get_ielts_writing_task_2_score(q,a,language):

    messages = [
            {"role": "system", "content": "You are an IELTS writing examiner."},
            {"role": "user", "content": instructions(language)},
            {"role": "assistant", "content": "Okay, got it."},
            {"role": "user", "content": f"Score the following answer to this IELTS writing question based on the criteria given earlier:\n\nQuestion: {q}\n\nResponse: {a}"}
        ]
    
    model='gpt-4-1106-preview'
    # model='gpt-3.5-turbo'
    # max_tokens=1000
    temperature=1.0

    try:
        return fetch_from_openai(messages,model,temperature)
    except Exception as e: raise
