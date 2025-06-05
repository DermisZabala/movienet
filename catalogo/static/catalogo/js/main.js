document.addEventListener('DOMContentLoaded', function() {

    // --- Navegación Móvil ---
    const navToggle = document.querySelector('.nav-toggle');
    const siteHeader = document.querySelector('.site-header');
    if (navToggle && siteHeader) {
        navToggle.addEventListener('click', () => {
            siteHeader.classList.toggle('nav-active');
        });
    }

    // --- Funcionalidad "Mostrar más" y control de visibilidad de cards ---
    const contentGrid = document.getElementById('content-grid');
    const showMoreBtn = document.getElementById('show-more-btn');
    if (contentGrid) { 
        const tipoContenido = contentGrid.dataset.tipoContenido; 
        const allCards = Array.from(contentGrid.getElementsByClassName('card'));
        let itemsToShow = 20; 
        const increment = 15; 

        if (tipoContenido === 'search' || !showMoreBtn) {
            allCards.forEach(card => card.classList.add('visible')); 
            if (showMoreBtn) { 
                showMoreBtn.classList.add('hidden'); 
            }
        } else { 
            function displayCards() {
                allCards.forEach((card, index) => {
                    if (index < itemsToShow) {
                        card.classList.add('visible'); 
                    }
                });
                if (itemsToShow >= allCards.length) {
                    if (showMoreBtn) showMoreBtn.classList.add('hidden');
                } else {
                    if (showMoreBtn) showMoreBtn.classList.remove('hidden');
                }
            }
            if (showMoreBtn) {
                showMoreBtn.addEventListener('click', () => {
                    itemsToShow += increment;
                    displayCards();
                });
            }
            if (allCards.length > 0) {
                displayCards(); 
            } else if (allCards.length === 0 && showMoreBtn) {
                showMoreBtn.classList.add('hidden'); 
            }
        }
    }
    
    // --- CSRF Token Getter ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    // --- Reportar Enlace Caído (Handler Genérico para CADA botón de reporte individual) ---
    function handleIndividualReportLink(event) {
        const reportButton = event.currentTarget;
        const { 
            contentId, 
            contentTitle, 
            reportedLink,
            itemType, 
            episodeTitle = '', 
            serverLabel = 'Desconocido'
        } = reportButton.dataset;

        if (!contentId || !contentTitle || !reportedLink || !itemType) {
            console.error('Incomplete data for report:', reportButton.dataset);
            alert('Missing data to send the report.');
            return;
        }
        if (!reportedLink || reportedLink === 'about:blank' || reportedLink.trim() === '') {
            alert('No valid link associated with this report button.');
            return;
        }

        const payload = {
            content_id: contentId,
            content_title: contentTitle,
            reported_link: reportedLink, 
            item_type: itemType,
            episode_title: episodeTitle,
            active_server_label: serverLabel
        };
        const reportUrl = '/reportar-enlace/';
        
        const originalButtonText = reportButton.textContent;
        reportButton.disabled = true;
        reportButton.textContent = 'Reporting...';

        fetch(reportUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.message || `Server error: ${response.status}`);
                }).catch(() => { 
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert(data.message || 'Thank you! Your report has been submitted.');
                reportButton.textContent = 'Reported'; 
            } else {
                alert('Error sending report: ' + (data.message || 'Please try again.'));
                reportButton.textContent = originalButtonText;
                reportButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error in report request:', error);
            alert('There was an error while reporting the link: ' + error.message);
            reportButton.textContent = originalButtonText;
            reportButton.disabled = false;
        });
    }

    // --- LÓGICA COMÚN PARA REPRODUCTORES (PELÍCULAS Y EPISODIOS) ---
    // Funciona con el HTML modificado que tiene un solo .server-options-area
    function initializePlayerWithIndividualReports(playerType) {
        const isMovie = playerType === 'movie';
        // console.log(`[JS INIT] Player Type: ${playerType}`);
        
        const iframePlayerElement = document.getElementById(isMovie ? 'main-iframe-player' : 'episode-iframe-player');
        const playerDataElement = document.getElementById(isMovie ? 'movie-iframe-data' : 'episode-player-data');
        
        const optionsAreaId = isMovie ? 'movie-server-options-area' : 'episode-server-options-area';
        const optionsAreaContainer = document.getElementById(optionsAreaId);
        
        const playerControlsContainer = document.getElementById(isMovie ? 'movie-player-options' : 'episode-player-page-controls');
        const h4Title = playerControlsContainer ? playerControlsContainer.querySelector('h4') : null;

        if (!iframePlayerElement || !playerDataElement || !optionsAreaContainer) {
            /* // Descomentar para depurar si los botones no aparecen
            console.warn(`[JS WARN - ${playerType}] Essential elements missing.
                - iframePlayer (for '${isMovie ? 'main-iframe-player' : 'episode-iframe-player'}'): ${!!iframePlayerElement}
                - playerData (for '${isMovie ? 'movie-iframe-data' : 'episode-player-data'}'): ${!!playerDataElement}
                - optionsAreaContainer (for '${optionsAreaId}'): ${!!optionsAreaContainer}
                Button generation aborted.`);
            */
            return;
        }

        const iframeSourcesString = playerDataElement.dataset.iframes || "";
        const contentId = playerDataElement.dataset.id || playerDataElement.dataset.contentId;
        const contentTitle = playerDataElement.dataset.title || playerDataElement.dataset.contentTitle;
        const itemType = playerDataElement.dataset.itemType;
        const episodeTitle = isMovie ? '' : (playerDataElement.dataset.episodeTitle || '');
        
        const originalIframes = iframeSourcesString.split('|||').map(link => link.trim()).filter(link => link !== '');

        optionsAreaContainer.innerHTML = ''; 

        if (h4Title) {
            h4Title.style.display = originalIframes.length > 0 ? 'block' : 'none';
        } else if (playerControlsContainer) { // Si no hay h4 específico, pero sí el contenedor padre, no hacer nada con el h4
            // console.log(`[JS INFO - ${playerType}] h4 title element not found within playerControlsContainer.`);
        }


        if (originalIframes.length > 0) {
            originalIframes.forEach((iframeEmbedSrc, index) => {
                const optionNumber = index + 1;
                const optionLabelText = `Option ${optionNumber}`;

                const pairContainer = document.createElement('div');
                pairContainer.classList.add('option-report-pair');

                const serverButton = document.createElement('button');
                serverButton.classList.add('button', 'button--secondary', `select-${playerType}-option-btn`); 
                serverButton.textContent = optionLabelText; 
                serverButton.type = 'button';
                serverButton.dataset.iframeSrc = iframeEmbedSrc;

                if (index === 0) {
                    serverButton.classList.add('active');
                }

                serverButton.addEventListener('click', function() {
                    const newEmbedSrc = this.dataset.iframeSrc;
                    if (newEmbedSrc && iframePlayerElement.src !== newEmbedSrc && newEmbedSrc !== 'about:blank') { 
                        iframePlayerElement.src = newEmbedSrc;
                        optionsAreaContainer.querySelectorAll(`.select-${playerType}-option-btn.active`).forEach(b => b.classList.remove('active'));
                        this.classList.add('active');
                    }
                });
                pairContainer.appendChild(serverButton);

                const reportButton = document.createElement('button');
                reportButton.classList.add('button', 'report-option-styled-button', 'report-this-option-btn');
                reportButton.textContent = `Report ${optionLabelText}`; 
                reportButton.type = 'button';
                reportButton.dataset.contentId = contentId;
                reportButton.dataset.contentTitle = contentTitle;
                reportButton.dataset.itemType = itemType;
                if (episodeTitle) {
                    reportButton.dataset.episodeTitle = episodeTitle;
                }
                reportButton.dataset.reportedLink = iframeEmbedSrc;
                reportButton.dataset.serverLabel = optionLabelText;
                reportButton.addEventListener('click', handleIndividualReportLink);
                pairContainer.appendChild(reportButton);

                optionsAreaContainer.appendChild(pairContainer);
            });

        } else {
            if (h4Title) h4Title.style.display = 'none';
            optionsAreaContainer.innerHTML = '<p class="message message--info">No streaming options available.</p>';
        }
    }

    initializePlayerWithIndividualReports('movie');
    initializePlayerWithIndividualReports('episode');

    // --- Funcionalidad de Acordeón para Temporadas ---
    if (document.querySelector('.series-anime-detail-page .season-block')) { 
        const seasonBlocks = document.querySelectorAll('.series-anime-detail-page .season-block');
        seasonBlocks.forEach(block => {
            const title = block.querySelector('.season-title');
            const content = block.querySelector('.season-episodes-content');
            if (title && content) {
                title.addEventListener('click', function() {
                    const isExpanded = title.classList.contains('expanded');
                    title.classList.toggle('expanded', !isExpanded);
                    content.classList.toggle('expanded', !isExpanded);
                    if (!isExpanded) {
                        content.style.maxHeight = content.scrollHeight + "px";
                    } else {
                        content.style.maxHeight = null;
                    }
                });
            }
        });
    }
});
