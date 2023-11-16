from .band_desc_instruct import instructions, band_descriptors
from .make_request import fetch_from_openai


def get_ielts_writing_task_2_score(q,a,language, lang_model):

    messages = [
            {"role": "system", "content": "You are an IELTS writing examiner."},
            {"role": "user", "content": band_descriptors},
            {"role": "assistant", "content": "Okay, got it."},
            {"role": "user", "content": instructions(language)},
            {"role": "assistant", "content": "Okay, got it."},
            {"role": "user", "content": f"Score the following answer to this IELTS writing question based on the criteria given earlier:\n\nQuestion: {q}\n\nResponse: {a}"}
        ]
    
    
    if lang_model:
        model = lang_model
    else:
    # Default is gpt-4 turbo
        model = 'gpt-4'

    try:
        return fetch_from_openai(messages,model)
    except Exception as e: raise
