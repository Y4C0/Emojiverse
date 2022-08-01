function showPreview(event)
{
    if(event.target.files.length > 0)
    {
        if (event.target.files[0].name.split('.').pop() === 'mp4')
        {
            var previewDiv = document.getElementById("preview");
            previewDiv.style.display = "none";
            var previewVid = document.getElementById("status");
            previewVid.src = "/static/ok.png";
            previewVid.style.display = "block"
        }
        else
        {
            var previewVid = document.getElementById("status");
            previewVid.style.display = "none"
            var src = URL.createObjectURL(event.target.files[0]);
            var previewDiv = document.getElementById("preview");
            previewDiv.style.display = "block";
            var preview = document.getElementById("file-ip-1-preview");
            preview.src = src;
            preview.style.display = "block";
        }
        var e = document.getElementById("btn");
        e.removeAttribute("disabled");
    }
}

function spinner()
{
    const spinnerDisplayer = document.querySelector('.spinner-displayer');
    const btn = document.getElementById('btn');
    btn.addEventListener('click', () => {
    spinnerDisplayer.classList.add('loading');
    })
}
spinner();