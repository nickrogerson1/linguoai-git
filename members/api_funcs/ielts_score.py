from .band_desc_instruct import instructions, band_descriptors
from .make_request import fetch_from_openai, fetch_from_anthropic


def get_ielts_writing_task_2_score(q,a,language, lang_model):
    
    if lang_model:
        model = lang_model
        print(f'TESTING LANG MODEL: {lang_model}')
    else:
    # Default is gpt-4 turbo
        model = 'gpt-4'

    m = [
        {"role": "assistant", "content": "Okay, got it."},
        {"role": "user", "content": instructions(language)},
        {"role": "assistant", "content": "Okay, got it."},
        {"role": "user", "content": f"Score the following answer to this IELTS writing question and give examples to justify the band:\n\nQuestion: {q}\n\nResponse: {a}"}
    ]

    if model == 'claude-3-opus-20240229':
    # Claude doesn't use the `system` key
        m = [
        {"role": "user", "content": f"You are an IELTS writing examiner. {band_descriptors}"},
        ] + m
    else:
         m = [
            {"role": "system", "content": "You are an IELTS writing examiner."},
            {"role": "user", "content": band_descriptors},
        ] + m

    try:
        if model == 'claude-3-opus-20240229':
            print(f'MADE IT TO ANTHROPIC!!')
            return fetch_from_anthropic(m,model)
        
        print(f'MADE IT TO OPENAI!!')
        return fetch_from_openai(m,model)
    except Exception as e: raise
