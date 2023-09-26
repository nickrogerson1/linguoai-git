const checkBox = document.querySelector('#select-all-items')
const checkboxes = document.querySelectorAll('.checkbox')

const applyToAll = () => checkboxes.forEach(x => checkBox.checked && !x.disabled ? x.checked = true : x.checked = false)

// Turn it on and off when all or some selected
const turnMainOnOff = () => {
    const allChecked = [...checkboxes].every(x => x.checked)
    allChecked ? checkBox.checked = true : checkBox.checked = false
}

// Only add listeners when there are submissions
if(checkBox){
    checkboxes.forEach(x => x.addEventListener('click', turnMainOnOff))
    checkBox.addEventListener('click', applyToAll)
}
const formFrozen = document.querySelector('#undo-form-freeze')
if (formFrozen) formFrozen.addEventListener('click', undoFormFreeze)

// Make sure to re-enable checkboxes before submission or they won't go through
const deleteFiles = document.querySelector('#delete-files')
if(deleteFiles) deleteFiles.addEventListener('submit', () => checkboxes.forEach(x => x.disabled = false))

const dropdown = document.querySelector('#dropdown')
if(dropdown) dropdown.addEventListener('change', processCheckboxes)
    


function processCheckboxes() {

    let index = dropdown.selectedIndex

    // 1st, check if it's the log page and send them through in pairs
    if(dropdown.options[index].value.startsWith('/log/')){
        const subs = [...document.querySelectorAll('tbody tr')].reduce((a,x) => {
            const isChecked = x.children[0].children[0].checked
            console.log(isChecked)
            if(isChecked){
                console.log(x.children[2].children[0].pathname)
                return a = a + x.children[2].children[0].pathname.slice(1)
            }
            return a},
            dropdown.options[index].value
        )
        console.log(subs)
        // Reset dropdown
        dropdown.selectedIndex = 0
        return location = subs
    }

    // Continue checking otherwise
    const checkboxes = document.querySelectorAll('.checkbox')
    const ids = [...checkboxes].reduce((a,x) => {
    if(x.checked){
        a = a + x.id + '/'
        }
        return a
    },'')
    
    // Make sure they've selected something first
    if(ids.length && index === 1){
    // Display delete confirmation and fade out form
    // Complicated way of checking for one due to split
        if(ids.split('/').filter(x => x).length === 1){
            const h4 = document.querySelector('#delete-area h4')
            const deleteButton = document.querySelector('#delete')
            h4.innerHTML = 'Are you sure you want to delete the selected result?'
            deleteButton.innerHTML = 'YES, DELETE IT!'
            formFrozen.innerHTML = 'NO, KEEP IT!'
        }
        
        document.querySelector('#delete-area').style.cssText = `
            display: block;
            visibility: visible;`
        dropdown.disabled = true
        checkBox.disabled = true
        
// Got through rows and apply CSS when selected for deletion
        const trs = document.querySelectorAll('.tablesorter tr')
        trs.forEach((tr,i) => {
            tr = tr.children
            tr[0].children[0].disabled = true
            const css = `text-decoration:line-through;
                    opacity:0.5;
                    pointer-events: none;`
            if(i && tr[0].children[0].checked){
                tr[1].style.cssText = tr[2].style.cssText = css
                }
        // IELTS table has 4 columns, so check for it
            if(tr[3] && i && tr[0].children[0].checked){
                tr[3].style.cssText = css
            }
            }
        )     

    } else if (ids.length && index) {
    // Get the zipped documents requested
        location = dropdown.options[index].value + ids
        dropdown.selectedIndex = 0

    } else {
    // Warn them that they've selected nothing
    // Providing it's not the 1st option
        if(index) {
            dropdown.selectedIndex = 0
    // Make sure the warning is visible
            document.body.scrollTop = document.documentElement.scrollTop = 80;
            showInputWarning()
        }
    }
}


function undoFormFreeze(){
    document.querySelector('#delete-area').style.cssText = `
                display: none;
                visibility: hidden;`
    dropdown.selectedIndex = 0
    dropdown.disabled = false
    checkBox.disabled = false
    checkboxes.forEach(x => x.disabled = false)
    document.querySelectorAll('tr td:not(:first-child)')
        .forEach(x => x.style.cssText = `
                text-decoration:initial;
                opacity:1;
            `)
}

// Warn them when they don't select anything
$(document).ready(function() {
    $("#input-warning").hide();
    })
    function showInputWarning() {
        $("#input-warning").fadeTo(2000, 500).slideUp(500, function() {
        $("#input-warning").slideUp(500);
        });
    };