async function fetchImages() {
    const res = await fetch('/images');
    const data = await res.json();
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    data.forEach(url => {
        const img = document.createElement('img');
        img.src = url + '?t=' + Date.now();
        img.style.width = '100%';
        grid.appendChild(img);
    });
}

setInterval(fetchImages, 10050);
fetchImages();
