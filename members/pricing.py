# Costs per 1000 tokens
LLM_COSTS = {
    # up to 4k
'gpt-3' : {'input' :0.001,
            'output': 0.002},
    # up to 128k
'gpt-4' : {'input': 0.01,
            'output': 0.03}
}


# Pricing per word
PRICING = {
    'ielts_writing_task_2': {
        'USD': 0.0009,
        'CNY': 0.007
    },
    'corrected_results': {
        'USD': 0.0004,
        'CNY': 0.003
    },
    'improved_results': {
        'USD': 0.0004,
        'CNY': 0.003
    }
}

MIN_CHARGE = {
    'USD': 0.05,
    'CNY': 0.5
}

