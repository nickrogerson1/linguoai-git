// Exclude the drop down
const forms = document.querySelectorAll('.form-group:not(.form-group:first-child')

// Count the words and characters
forms.forEach( form => {
    form.addEventListener('input', () => {
        const word_count = form.dataset.replicatedValue.trim().split(/\s+/).filter(x => x).length
        form.nextElementSibling.innerHTML = `Word Count: ${word_count}`
    })
})


const clearInput = () => {
    forms.forEach(form => {
        form.children[0].value = ''
        form.setAttribute('data-replicated-value','')
    // Reset the counters
        form.nextElementSibling.innerHTML = 'Word Count: 0'
    })
}


document.querySelector('#clear').addEventListener('click', clearInput)


$(document).ready(function() {
    forms.forEach( form => {
            const word_count = form.textContent.trim().split(/\s+/).filter(x => x).length
            form.nextElementSibling.innerHTML = `Word Count: ${word_count}`
    })
})