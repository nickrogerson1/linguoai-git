# Costs per 1000 tokens
LLM_COSTS = {
    # up to 4k
'gpt-3' : {'input' :0.0015,
            'output': 0.002},
    # up to 8k
'gpt-4' : {'input': 0.03,
            'output': 0.06}
}


# Pricing per 100 words
PRICING = {
    'ielts_writing_task_2': {
        'USD': 0.09,
        'CNY': 0.7
    },
    'corrected_results': {
        'USD': 0.04,
        'CNY': 0.3
    },
    'improved_results': {
        'USD': 0.04,
        'CNY': 0.3
    }
}

MIN_CHARGE = {
    'USD': 0.05,
    'CNY': 0.5
}

