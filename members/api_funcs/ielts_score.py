from .band_desc_instruct import instructions
from .make_request import fetch_from_openai


def get_ielts_writing_task_2_score(q,a):

    messages = [
            {"role": "system", "content": "You are an IELTS writing examiner."},
            {"role": "user", "content": instructions},
            {"role": "assistant", "content": "Okay, got it."},
            {"role": "user", "content": f"Score the following answer to this IELTS writing question and give examples to justify the band:\n\nQuestion: {q}\n\nResponse: {a}"}
        ]

    messages=messages
    # model='gpt-4'
    model='gpt-3.5-turbo'
    max_tokens=600
    temperature=1.0

    return fetch_from_openai(messages,model,max_tokens,temperature)