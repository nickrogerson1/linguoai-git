const checkValidWordCount = e => {
    e.preventDefault()

    const warnings = document.querySelectorAll('.warning-text')
    //Clear warning text if any present
    warnings.forEach(warning => {
        if(warning){
            warning.remove()
        }
    })
    
    let questionWordCount;
    let answerWordCount;

    const question = document.querySelector('#question');
    const answer = document.querySelector('#answer');

    if(question.dataset.replicatedValue){
        questionWordCount = question.dataset.replicatedValue.trim().split(/\s+/).length;
    }
    if(answer.dataset.replicatedValue){
        answerWordCount = answer.dataset.replicatedValue.trim().split(/\s+/).length;
    }

    console.log(answerWordCount)


    // Send back errors if not enough or too many words

    // Same style for all warnings
    const className = 'text-danger warning-text';

    if (!questionWordCount || questionWordCount < 15){
        const warning = Object.assign(document.createElement('h4'), {
            className, 
            textContent:'You need to submit a MINIMUM of 15 words for the question.'
        });
        return question.after(question.nextElementSibling, warning)

    } else if (questionWordCount > 150){
        const warning = Object.assign(document.createElement('h4'), {
            className, 
            textContent:'You need to submit a MAXIMUM of 150 words for the question.'
        });
        return question.after(question.nextElementSibling, warning)
    }


    if (!answerWordCount || answerWordCount < 250){
        const warning = Object.assign(document.createElement('h4'), {
            className, 
            textContent:'You need to submit a MINIMUM of 250 words for your answer.'
        });
        return answer.after(answer.nextElementSibling, warning)

    } else if (answerWordCount > 600){
        const warning = Object.assign(document.createElement('h4'), {
            className, 
            textContent:'You can only submit a MAXIMUM of 600 words for your answer.'
        });
        return answer.after(answer.nextElementSibling, warning)
    } 

    document.querySelector('#overlay').style.display = 'block'
    e.currentTarget.submit()
    
}

document.querySelector('#ielts-form-submit').addEventListener('submit', checkValidWordCount)


// Exclude the select box - not supported by Firefox Aug 2023.
// It knocks out the word count on Firefox
const forms = document.querySelectorAll('.form-group:has(textarea)')

// Count the words and characters
forms.forEach( form => {
    form.addEventListener('input', () => {
        const word_count = form.dataset.replicatedValue.trim().split(/\s+/).length
        const char_count = form.dataset.replicatedValue.length
        form.nextElementSibling.innerHTML = `Word Count: ${word_count}&nbsp;&nbsp;|&nbsp;&nbsp;Character Count: ${char_count}`
    })
})


const clearInput = () => {
    document.querySelector('form').reset()
    forms.forEach(form => {
    // Fixes bug if the form has been returned with errors
        form.lastElementChild.innerText = ''
        form.setAttribute('data-replicated-value','')
    // Reset the counters
        form.nextElementSibling.innerHTML = 'Word Count: 0&nbsp;&nbsp;|&nbsp;&nbsp;Character Count: 0'
    })
}


document.querySelector('#clear').addEventListener('click', clearInput)