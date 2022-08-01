    var element = document.getElementById('photos');
    element.addEventListener('click', (event) => {
        if (event.target.className === 'btn btn-danger') {
            const button = event.target;
            const a = button.parentNode;
            const aparent = a.parentNode
            const div = aparent.parentNode;
            if (button.textContent === 'Delete') {
                div.removeChild(aparent);
            }
        }
    });

    var element2 = document.getElementById('clips');
    element2.addEventListener('click', (event) => {
        if (event.target.className === 'btn btn-danger') {
            const button = event.target;
            const a = button.parentNode;
            const aparent = a.parentNode
            const div = aparent.parentNode;
            if (button.textContent === 'Delete') {
                div.removeChild(aparent);
            }
        }
    });

    function showDiv() {
        var x = document.querySelectorAll(".btn");
        x.forEach(item => {
            if (item.style.display == 'block')
                item.style.display = 'none';
            else
                item.style.display = 'block';
        });
    }
