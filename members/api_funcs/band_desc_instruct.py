def instructions(language): 
    return f'''
These are the band descriptors to be used to assess the answer. 

You must select a suitable band for each band descriptor: Task Response, Coherence and Cohesion, Lexical Recourse and Grammatical Range, and Accuracy.

You can select a band if the answer matches all the bulletpoints in that band. Always give the benefit of the doubt. Band 9 is the highest and 0 the lowest.

The overall score is calculated by adding all the band scores together and then rounding off to the nearest .5. 

If the score ends in .25, then round down to the nearest integer. For example, 6.25 should be 6.

State reasons for and against why you chose that band in {language}.

Always start by stating the overall score like this %%%%%Band {{overall score}}%%%%%

Return the answer in HTML.

Task Response:
Band 9
▪ fully addresses all parts of the task
▪ presents a fully developed position in answer to the question with relevant, fully extended and well supported ideas

Band 8
▪ sufficiently addresses all parts of the task
▪ presents a well-developed response to the question with relevant, extended and supported ideas

Band 7
▪ addresses all parts of the task
▪ presents a clear position throughout the response
▪ presents, extends and supports main ideas, but there may be a tendency to overgeneralise and/or supporting ideas may lack focus

Band 6
▪ addresses all parts of the task although some parts may be more fully covered than others
▪ presents a relevant position although the conclusions may become unclear or repetitive
▪ presents relevant main ideas but some may be inadequately developed/unclear

Band 5
▪ addresses the task only partially; the format may be inappropriate in places
▪ expresses a position but the development is not always clear and there may be no conclusions drawn
▪ presents some main ideas but these are limited and not sufficiently developed; there may be irrelevant detail

Band 4
▪ responds to the task only in a minimal way or the answer is tangential; the format may be inappropriate
▪ presents a position but this is unclear
▪ presents some main ideas but these are difficult to identify and may be repetitive, irrelevant or not well supported

Band 3
▪ does not adequately address any part of the task
▪ does not express a clear position
▪ presents few ideas, which are largely undeveloped or irrelevant

Band 2
▪ barely responds to the task
▪ does not express a position
▪ may attempt to present one or two ideas but there is no development

Band 1
▪ answer is completely unrelated to the task


Coherence and Cohesion:
Band 9
▪ uses cohesion in such a way that it attracts no attention
▪ skilfully manages paragraphing

Band 8
▪ sequences information and ideas logically
▪ manages all aspects of cohesion well
▪ uses paragraphing sufficiently and appropriately

Band 7
▪ logically organises information and ideas; there is clear progression throughout
▪ uses a range of cohesive devices appropriately although there may be some under-/over-use
▪ presents a clear central topic within each paragraph

Band 6
▪ arranges information and ideas coherently and there is a clear overall progression
▪ uses cohesive devices effectively, but cohesion within and/or between sentences may be faulty or mechanical
▪ may not always use referencing clearly or appropriately
▪ uses paragraphing, but not always logically

Band 5
▪ presents information with some organisation but there may be a lack of overall progression
▪ makes inadequate, inaccurate or over use of cohesive devices
▪ may be repetitive because of lack of referencing and substitution
▪ may not write in paragraphs, or paragraphing may be inadequate

Band 4
▪ presents information and ideas but these are not arranged coherently and there is no clear progression in the response
▪ uses some basic cohesive devices but these may be inaccurate or repetitive
▪ may not write in paragraphs or their use may be confusing

Band 3
▪ does not organise ideas logically
▪ may use a very limited range of cohesive devices, and those used may not indicate a logical relationship between ideas

Band 2
▪ has very little control of organisational features

Band 1
▪ fails to communicate any message 


Lexical Resource:
Band 9
▪ uses a wide range of vocabulary with very natural and sophisticated control of lexical features; rare minor errors occur only as 'slips'

Band 8
▪ uses a wide range of vocabulary fluently and flexibly to convey precise meanings
▪ skilfully uses uncommon lexical items but there may be occasional inaccuracies in word choice and collocation
▪ produces rare errors in spelling and/or word formation

Band 7
▪ uses a sufficient range of vocabulary to allow some flexibility and precision
▪ uses less common lexical items with some awareness of style and collocation
▪ may produce occasional errors in word choice, spelling and/or word formation

Band 6
▪ uses an adequate range of vocabulary for the task
▪ attempts to use less common vocabulary but with some inaccuracy
▪ makes some errors in spelling and/or word formation, but they do not impede communication

Band 5
▪ uses a limited range of vocabulary, but this is minimally adequate for the task
▪ may make noticeable errors in spelling and/or word formation that may cause some difficulty for the reader

Band 4
▪ uses only basic vocabulary which may be used repetitively or which may be inappropriate for the task
▪ has limited control of word formation and/or spelling; errors may cause strain for the reader

Band 3
▪ uses only a very limited range of words and expressions with very limited control of word formation and/or spelling
▪ errors may severely distort the message

Band 2
▪ uses an extremely limited range of vocabulary; essentially no control of word formation and/or spelling

Band 1
▪ can only use a few isolated words


Grammatical Range and Accuracy:
Band 9
▪ uses a wide range of structures with full flexibility and accuracy; rare minor errors occur only as 'slips'

Band 8
▪ uses a wide range of structures
▪ the majority of sentences are error-free
▪ makes only very occasional errors or inappropriacies

Band 7
▪ uses a variety of complex structures
▪ produces frequent error-free sentences
▪ has good control of grammar and punctuation but may make a few errors

Band 6
▪ uses a mix of simple and complex sentence forms
▪ makes some errors in grammar and punctuation but they rarely reduce communication

Band 5
▪ uses only a limited range of structures
▪ attempts complex sentences but these tend to be less accurate than simple sentences
▪ may make frequent grammatical errors and punctuation may be faulty; errors can cause some difficulty for the reader

Band 4
▪ uses only a very limited range of structures with only rare use of subordinate clauses
▪ some structures are accurate but errors predominate, and punctuation is often faulty

Band 3
▪ attempts sentence forms but errors in grammar and punctuation predominate and distort the meaning

Band 2
▪ cannot use sentence forms except in memorised phrases

Band 1
▪ cannot use sentence forms at all

For All band descriptors:
Band 0
▪ does not attend
▪ does not attempt the task in any way
▪ writes a totally memorised response
'''







# For all band descriptors:
# Band 0 – Should only be used when a candidate did not attend or attempt the question in any way, used a language other than English, or where there is proof that a candidate’s answer has been totally memorised.


# Task Response:

# Band 1 – The content is wholly unrelated to the prompt. Any copied rubric must be discounted.

# Band 2 – The content is barely related to the prompt. No position can be identified. There may be glimpses of one or two ideas without development.

# Band 3 – No part of the prompt is adequately addressed, or the prompt has been misunderstood. No relevant position can be identified, and/or there is little direct response to the question. There are a few ideas, and these may be irrelevant or insufficiently developed.

# Band 4 - The prompt is tackled in a minimal way, or the answer is tangential, possibly due to some misunderstanding of the prompt. The format may be inappropriate.

# A position is discernible, but the reader has to read carefully to find it. Main ideas are difficult to identify and such ideas that are identifiable may lack relevance, clarity and/or support. Large parts of the response may be repetitive.

# Band 5 - The main parts of the prompt are incompletely addressed. The format may be inappropriate in places. The writer expresses a position, but the development is not always clear.  Some main ideas are put forward, but they are limited and are not sufficiently developed and/or there may be irrelevant detail. There may be some repetition.

# Band 6 - The main parts of the prompt are addressed (though some may be more fully covered than others). An appropriate format is used. A position is presented that is directly relevant to the prompt, although the conclusions drawn may be unclear, unjustified or repetitive. Main ideas are relevant, but some may be insufficiently developed or may lack clarity, while some supporting arguments and evidence may be less relevant or inadequate.

# Band 7 - The main parts of the prompt are appropriately addressed. A clear and developed position is presented. Main ideas are extended and supported but there may be a tendency to over-generalise or there may be a lack of focus and precision in supporting ideas/material.

# Band 8 - The prompt is appropriately and sufficiently addressed. A clear and well-developed position is presented in response to the question/s. Ideas are relevant, well-extended and supported. There may be occasional omissions or lapses in content.

# Band 9 - The prompt is appropriately addressed and explored in depth. A clear and fully developed position is presented which directly answers the question/s. Ideas are relevant, fully extended and supported. Any lapses in content or support are extremely rare.


# Coherence and Cohesion:

# Band 1 - The writing fails to communicate any message and appears to be a virtual non-writer.

# Band 2 – There is little relevant message or the entire response may be off-topic. There is little evidence of control of organisational features.

# Band 3 – There is no apparent logical organization. Ideas are discernible but difficult to relate to each other. There is minimal use of sequencers or cohesive devices. Those used to do not necessarily indicate a logical relationship between ideas. There is difficulty in identifying referencing. Any attempts at paragraphing are unhelpful.

# Band 4 - Information and ideas evident but not arranged coherently and there is no clear progression within the response. Relationships between ideas can be unclear and/or inadequately marked. There is some use of basic cohesive devices, which may be inaccurate or repetitive. There is inaccurate use or a lack of substitution or referencing. There may be no paragraphing and/or no clear main topic within paragraph.

# Band 5 - Organisation is evident but is not wholly logical and there may be a lack of overall progression. Nevertheless, there is a sense of underlying coherence to the response. The relationship of ideas can be followed but the sentences are not fluently linked to each other. There may be limited/overuse of cohesive devices with some inaccuracy. The writing may be repetitive due to inadequate and/or inaccurate use of reference and substitution. Paragraphing may be inaccurate or missing.

# Band 6 - Information and ideas are generally arranged coherently and there is a clear overall progression. Cohesive devices are used to some good effect but cohesion within and/or between sentences may be faulty or mechanical due to misuse, overuse or omission. The use of reference or substitution may lack flexibility or clarity and result in some repetition or error. Paragraphing may not always be logical and or central topic may not always be clear.

# Band 7 - Information and ideas are logically organised, and there is a clear progression throughout the response. (A few lapses may occur, but these are minor). A range of cohesive devices including reference and substitution is used flexibly but with some inaccuracies or some over/under use. Paragraphing is generally used effectively to support overall coherence, and the sequencing of ideas within a paragraph is generally logical.

# Band 8 - The message can be followed with ease. Information and ideas are logically sequenced, and cohesion is well managed. Occasional lapses in coherence and cohesion may occur. Paragraphing is used sufficiently and appropriately.

# Band 9 - The message can be followed effortlessly. Cohesion is used in such a way that it very rarely attracts attention. Any lapses in coherence or cohesion are minimal. Paragraphing is skillfully managed.


# Lexical Resource:

# Band 1 - No resource is apparent, except for a few isolated words.

# Band 2 – The resource is extremely limited with few recognisable strings, apart from memorised phrases. There is no apparent control of word formation and/or spelling.

# Band 3 - The resource is inadequate (which may be due to the response being significantly underlength). Possible over-dependence on input material or memorised language. Control of word choice and/or spelling is very limited, and errors predominate. These errors may severely impede meaning.

# Band 4 - The resource is limited and inadequate for or unrelated to the task. Vocabulary is basic and may be used repetitively. There may be inappropriate use of lexical chunks (e.g. memorised phrases, formulaic language and/or language from the input material). Inappropriate word choice and/or errors in word formation and/or spelling may impede meaning.

# Band 5 - The resource is limited but minimally adequate for the task. Simple vocabulary may be used accurately but the range does not permit much variation in expression. There may be frequent lapses in the appropriacy of word choice and a lack of flexibility is apparent in frequent simplifications and/or repetitions. Errors in spelling and/or word formation may be noticeable and may cause some difficulty for the reader.

# Band 6 - The resource is generally adequate and appropriate for the task. The meaning is generally clear in spite of a rather restricted range or a lack of precision in word choice. If the writer is a risk-taker, there will be a wider range of vocabulary used but higher degrees of inaccuracy or inappropriacy. There are some errors in spelling and/or word formation, but these do not impede communication.

# Band 7 - The resource is sufficient to allow some flexibility and precision. There is some ability to use less common and/or idiomatic items.  An awareness of style and collocation is evident, though inappropriacies occur.  There are only a few errors in spelling and/or word formation and they do not detract from overall clarity.

# Band 8 - A wide resource is fluently and flexibly used to convey precise meanings. There is skillful use of uncommon and/or idiomatic items when appropriate, despite occasional inaccuracies in word choice and collocation. Occasional errors in spelling and/or word formation may occur, but have minimal impact on communication.

# Band 9 - Full flexibility and precise use are widely evident. A wide range of vocabulary is used accurately and appropriately with very natural and sophisticated control of lexical features. Minor errors in spelling and word formation are extremely rare and have minimal impact on communication.


# Grammatical Range and Accuracy:

# Band 1 - No rateable language is evident.

# Band 2 – There is little or no evidence of sentence forms (except in memorised phrases).

# Band 3 - Sentence forms are attempted, but errors in grammar and punctuation predominate (except in memorised phrases or those taken from the input material). This prevents most meaning from coming through. Length may be insufficient to provide evidence of control of sentence forms.

# Band 4 - A very limited range of structures is used. Subordinate clauses are rare and simple sentences predominate. Some structures are produced accurately but grammatical errors are frequent and may impede meaning. Punctuation is often faulty and inadequate. 

# Band 5 - The range of structures is limited and rather repetitive. Although complex sentences are attempted, they tend to be faulty, and the greatest accuracy is achieved on simple sentences.  Grammatical errors may be frequent and can cause some difficulty for the reader. Punctuation may be faulty.

# Band 6 - A mix of simple and complex sentence forms is used but flexibility is limited. Examples of more complex structures are not marked by the same level of accuracy as in simple structures. Errors in grammar and punctuation occur, but rarely impede communication.

# Band 7 - A variety of complex structures are used with some flexibility and accuracy. Grammar and punctuation are generally well controlled, and error-free sentences are frequent. A few errors in grammar may persist, but these do not impede communication.

# Band 8 - A wide range of structures is flexibly used. The majority of sentences are error-free, and punctuation is well managed. Occasional, non-systematic errors and inappropriacies occur, but have minimal impact on communication.

# Band 9 - A wide range of structures is used with full flexibility and control. Punctuation and grammar are used appropriately throughout. Minor errors are extremely rare and have minimal impact on communication.
