const dzBlock = document.querySelector('#dropzone-block')
const form = document.querySelector('.form-group')

// Count the words and characters
form.addEventListener('input', () => {
    const word_count = form.dataset.replicatedValue.trim().split(/\s+/).filter(x => x).length
    form.nextElementSibling.innerHTML = `Word Count: ${word_count}`
})


const clearInput = () => {
    document.querySelector('#manual-input-form').reset()
    // Fixes bug if the form has been returned with errors
    form.lastElementChild.innerText = ''
    form.setAttribute('data-replicated-value','')
    // Reset the counters
    form.nextElementSibling.innerHTML = 'Word Count: 0'
    // Bring back the file upload section
    dzBlock.style.display = 'initial'
    document.querySelector('#top-card').style.marginBottom = '30px'
}


document.querySelector('#clear').addEventListener('click', clearInput)



const ws = new WebSocket(`wss://${window.location.host}/ws/bulk-submission/`);

ws.onclose = e => {
    console.error('Web Socket closed unexpectedly');
    };

// Starts when row initiated then stops counting when status changes
const counter = taskId => {
    let secs = 0
    const cell = document.querySelector(`#${taskId} td:nth-child(2)`)
    const incrementer = () => {
        secs++
        const s = secs === 1 ? '' : 's'
        cell.innerHTML = `${secs} sec${s}`
        const status = document.querySelector(`#${taskId} td:last-child`).innerHTML
        if(status === 'Completed' || status === 'Failed') {
            clearInterval(interval)
            }
        }
const interval = setInterval(incrementer, 1000)
}


const countdown = (taskId, retryCount, secs, maxAttempts) => {
    const getOrd = n => ['st','nd','rd'][((n+90)%100-10)%10-1]||'th'
    const status = document.querySelector(`#${taskId} td:last-child`)

      const decrementer = () => {
        secs-- 
        console.log(`Seconds: ${secs}`)
        const s = secs === 1 ? '' : 's'

        if(retryCount === maxAttempts){
            status.innerHTML = `FINAL attempt: retrying in ${secs} sec${s}`
          } else {
            status.innerHTML = `${retryCount}${getOrd(retryCount)} attempt: retrying in ${secs} sec${s}`
        }
        
        if(!secs || Math.sign(secs) === -1){
            if(retryCount === maxAttempts){
                status.innerHTML = `FINAL attempt: retrying...`
            } else {
                status.innerHTML = `${retryCount}${getOrd(retryCount)} attempt: retrying...`
            }
            
            clearInterval(interval)
        }
      }
    const interval = setInterval(decrementer, 1000)
  }


const addRow = (wordCount, cost, fileName, taskId, status) => {

    const tr = document.createElement('tr')
        tr.id = `${taskId}`

        const td0 = document.createElement('td')
        const id = document.querySelector('table').rows.length++
        td0.innerHTML = `${id}.`

        const td1 = document.createElement('td')
        td1.innerHTML = 0
        td1.className = 'text-center'

        const td2 = document.createElement('td')
        td2.innerHTML = wordCount
        td2.className = 'text-center'

        const td3 = document.createElement('td')
        td3.innerHTML = cost
        td2.className = 'text-center'

        const td4 = document.createElement('td')
        td4.innerHTML = fileName
        td4.className = 'inject-link'

        const td5 = document.createElement('td')
        td5.innerHTML = status

        tr.append(td0,td1,td2,td3,td4,td5)

        document.querySelector('tbody').append(tr)

        // Start counter after initialization
        counter(taskId)
    }





ws.onmessage = e => {
    const data = JSON.parse(e.data);
    console.log(data)


    if(data.wordCount){
    const { wordCount, cost, fileName, taskId, status } = data
    addRow(wordCount, cost, fileName, taskId, status)

    } else if(data.status === 'success') {

        const { taskId, new_balance, pk } = data

    // Check the taskId exists before continuing
        if(!document.querySelector(`#${taskId}`)) return

    //Add link to the new db entry
        const el = document.querySelector(`#${taskId} td.inject-link`)
        const page = window.location.toString().includes('corrected') ? 'corrected' : 'improved'
        const newLink = `<a href="/${page}-results/${pk}/">${el.innerHTML}</a>`
        el.innerHTML = newLink
    //Update other info
        document.querySelector(`#${taskId} td:last-child`).innerHTML = 'Completed'
        document.querySelector('#balance').innerHTML = new_balance.toFixed(2)

        } else if(data.status === 'failed') {
 
        let { taskId, retryCount, delay, maxRetries } = data

        // Check the taskId exists before continuing
        if(!document.querySelector(`#${taskId}`)) return

        retryCount += 2
        const maxAttempts = maxRetries + 1


        if(retryCount <= maxAttempts){
            countdown(taskId, retryCount, delay, maxAttempts) 

        } else {

        const el = document.querySelector(`#${taskId}`)
        const curr = el.children[3].innerHTML.startsWith('$') ? '$' : '¥'
        el.children[3].innerHTML = curr + 0
        el.children[5].innerHTML = 'Failed'
        el.children[5].style.cssText = 'color:red !important'
        }
    }  
}

const acceptedFiles = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
'application/pdf','text/rtf','text/plain','application/zip','']


Dropzone.autoDiscover = false;
let myDropzone = new Dropzone("#dropzone-area", {
    acceptedFiles : acceptedFiles.toString(),
    parallelUploads : 1
});

myDropzone.on("addedfile", file => {
// Remove text-input
document.querySelector('#text-input').style.display = 'none'
document.querySelector('#reveal-table').style.display = 'block'
console.log(file)


const img = file.previewElement.querySelector("img")
    const root = '/static/img/file-icons/'
    if (file.name.endsWith('docx')){
    img.src = root + "docx.svg";
    } else if (file.name.endsWith('pdf')){
    img.src = root + "pdf.svg";
    } else if (file.name.endsWith('rtf')){
    img.src = root + "rtf.svg";
    } else if (file.name.endsWith('txt')){
    img.src = root + "txt.svg";
    } else if (file.name.endsWith('zip')){
    img.src = root + "zip.svg";
    }  else {
    img.src = root + "error.svg";
    }
});


const inputForm = document.querySelector('#manual-input-form')

const toggleInputForm = () => {
    const txtArea = document.querySelector('#manual-input-form textarea')
    if(txtArea.value){
        dzBlock.style.display = 'none'
        document.querySelector('#top-card').style.marginBottom = '0'
    } else {
        dzBlock.style.display = 'initial'
        document.querySelector('#top-card').style.marginBottom = '30px'
    }
}

inputForm.addEventListener('input', toggleInputForm)