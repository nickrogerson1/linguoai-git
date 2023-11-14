from difflib import HtmlDiff
import nltk.data
from .make_request import fetch_from_openai
from lxml import html, etree
import re


def find_difference(sub, res):
# Break into sentences and find differences
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
    original_text_sents = sent_detector.tokenize(sub)
    openai_res_sents = sent_detector.tokenize(res)
    edited = HtmlDiff().make_table(original_text_sents, openai_res_sents)
# Clean the tables of crappy HTML
    edited = re.sub('nowrap="nowrap"|nowrap', '', edited)
    edited = re.sub('&nbsp;|&#160;', ' ', edited)


# Remove extra columns added by HtmlDiff Library
    table = html.fragment_fromstring(edited)
# My new swanky header element complete with CSS classes
    header = etree.fromstring('''
        <thead id="main-table" class="text-center">
            <tr>
                <th colspan="2">Original</th>
                <th colspan="2">Edited</th>
            </tr>
        </thead>
        ''')
# First remove the extra colgroups
# Using a hack to add the header as I need to go down and then back up the tree
    for i ,el in enumerate(table.getchildren()):
        if i < 2:
            el.getparent().insert(-1, header) 
            el.getparent().remove(el)
# Then remove them from the rows
    for row in table.getchildren()[-1].iterchildren():
        row.remove(row.getchildren()[0])
        row.remove(row.getchildren()[2])
        corrected_version = html.tostring(table).decode('utf-8')
    
    return corrected_version



def get_corrected_submission(original_text):

    messages = [
        {"role": "system", "content": "You are a writing editor."},
        {"role": "user", 
        "content": f"Correct all the errors in each sentence and do not merge sentences. Make the text sound more like an English native speaker when required. If the sentence is gramatically correct, then don't change it. \n\nHere is the text:\n\n{original_text}."}
    ]

    model='gpt-4-1106-preview'
    # model='gpt-3.5-turbo'
    # max_tokens=5000

    try:
        res = fetch_from_openai(messages,model)
    except Exception as e: raise

    if res:
        corrected_version = find_difference(original_text, res[0])
        res.append(corrected_version)
        
    return res