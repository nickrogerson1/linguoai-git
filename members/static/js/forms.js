
const displayLoader = () => {
    // Only run if form has been completed
    const parts = [...document.querySelectorAll('.form-group')]
    const check = parts.every(x => x.dataset.replicatedValue)
    if(check) {
        document.querySelector('#overlay').style.display = 'block'
    }
}


const button = document.querySelector('#button')
button.addEventListener('click', displayLoader)


const form = document.querySelector('.form-group')

// Count the words and characters
form.addEventListener('input', () => {
    const word_count = form.dataset.replicatedValue.trim().split(/\s+/).length
    const char_count = form.dataset.replicatedValue.length
    form.nextElementSibling.innerHTML = `Word Count: ${word_count}&nbsp;&nbsp;|&nbsp;&nbsp;Character Count: ${char_count}`
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