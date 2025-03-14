document.addEventListener('DOMContentLoaded', function() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const preview = document.getElementById('preview');
    const imageContainer = document.getElementById('imageContainer');
    const overlayContainer = document.getElementById('overlayContainer');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const textResults = document.getElementById('textResults');
    const viewResultBtn = document.getElementById('viewResultBtn');
    const copyTextBtn = document.getElementById('copyTextBtn');
    
    let currentResultId = null;
    
    // Ukryj sekcję wyników na starcie
    results.classList.add('hidden');
    
    // Obsługa przycisku wyboru pliku
    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Obsługa przeciągnij i upuść
    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropzone.classList.add('active');
    });
    
    dropzone.addEventListener('dragleave', function() {
        dropzone.classList.remove('active');
    });
    
    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropzone.classList.remove('active');
        
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    // Obsługa wyboru pliku
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length) {
            handleFile(fileInput.files[0]);
        }
    });
    
    // Przetwarzanie wybranego pliku
    function handleFile(file) {
        if (!file.type.match('image.*')) {
            alert('Proszę wybrać plik obrazu!');
            return;
        }
        
        // Wyświetlenie podglądu
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            imageContainer.classList.remove('hidden');
            overlayContainer.innerHTML = '';
            // Ukryj wyniki z poprzedniego przetwarzania
            results.classList.add('hidden');
        };
        reader.onerror = function(e) {
            alert('Błąd podczas wczytywania pliku: ' + e.target.error);
        };
        reader.readAsDataURL(file);
        
        // Wysłanie pliku do API
        const formData = new FormData();
        formData.append('file', file);
        
        loading.classList.remove('hidden');
        
        fetch('/api/ocr', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Błąd serwera');
                });
            }
            return response.json();
        })
        .then(data => {
            loading.classList.add('hidden');
            if (data.error) {
                alert('Wystąpił błąd: ' + data.error);
                return;
            }
            
            // Pokaż wyniki tylko jeśli są jakieś wykryte teksty
            if (data.detected_texts && data.detected_texts.length > 0) {
                currentResultId = data.result_id;
                viewResultBtn.href = `/view/${currentResultId}`;
                showResults(data);
                results.classList.remove('hidden');
            } else {
                // Jeśli nie wykryto tekstu, pokaż informację
                results.classList.remove('hidden');
                textResults.innerHTML = '<div class="text-block"><p>Nie wykryto żadnego tekstu na obrazie.</p></div>';
            }
        })
        .catch(error => {
            loading.classList.add('hidden');
            alert('Wystąpił błąd: ' + error.message);
        });
    }
    
    // Wyświetlenie wyników OCR
    function showResults(data) {
        textResults.innerHTML = '';
        
        if (data.detected_texts && data.detected_texts.length > 0) {
            let allText = '';
            
            data.detected_texts.forEach((item, index) => {
                // Dodanie tekstu do wyników
                const textElement = document.createElement('div');
                textElement.className = 'text-block';
                textElement.innerHTML = `
                    <p class="text">Tekst ${index + 1}: ${item.text}</p>
                    <p class="confidence">Pewność: ${item.confidence.toFixed(2)}%</p>
                `;
                textResults.appendChild(textElement);
                
                allText += item.text + '\n';
                
                // Dodanie nakładki na obraz
                const overlay = document.createElement('div');
                overlay.className = 'text-overlay';
                
                const imgRect = preview.getBoundingClientRect();
                const scaleX = imgRect.width / preview.naturalWidth;
                const scaleY = imgRect.height / preview.naturalHeight;
                
                const [x1, y1, x2, y2] = item.region;
                
                overlay.style.left = (x1 * scaleX) + 'px';
                overlay.style.top = (y1 * scaleY) + 'px';
                overlay.style.width = ((x2 - x1) * scaleX) + 'px';
                overlay.style.height = ((y2 - y1) * scaleY) + 'px';
                
                overlayContainer.appendChild(overlay);
            });
            
            // Obsługa kopiowania tekstu
            copyTextBtn.onclick = function() {
                navigator.clipboard.writeText(allText).then(() => {
                    alert('Tekst skopiowany do schowka!');
                });
            };
        }
    }
});
