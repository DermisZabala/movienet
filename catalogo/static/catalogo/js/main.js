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
    let itemsToShow = 20; 
    const increment = 15; 

    if (contentGrid) { 
        const tipoContenido = contentGrid.dataset.tipoContenido; 
        const allCards = Array.from(contentGrid.getElementsByClassName('card'));

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
                    } else {
                        card.classList.remove('visible'); 
                    }
                });
                if (itemsToShow >= allCards.length) {
                    showMoreBtn.classList.add('hidden');
                } else {
                    showMoreBtn.classList.remove('hidden');
                }
            }
            if (showMoreBtn) { // Añadir event listener solo si el botón existe
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

    // --- Reportar Enlace Caído (Handler Genérico) ---
    function handleReportLink(event) {
        const button = event.currentTarget;
        const { contentId, contentTitle, reportedLink, itemType, episodeTitle = '', serverLabel = '' } = button.dataset;

        if (!contentId || !contentTitle || !reportedLink || !itemType) {
            console.error('Incomplete data for report:', button.dataset);
            alert('Missing data to send the report.');
            return;
        }
        const payload = {
            content_id: contentId,
            content_title: contentTitle,
            reported_link: reportedLink, 
            item_type: itemType,
            episode_title: episodeTitle,
            server_label: serverLabel
        };
        const reportUrl = '/reportar-enlace/'; // Asegúrate que esta URL está definida en tus urls.py globales
        
        const originalButtonText = button.textContent;
        button.disabled = true;
        button.textContent = 'Reporting...';

        fetch(reportUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Thank you! Your report has been submitted.');
                button.textContent = 'Reported'; 
            } else {
                alert('Error sending report: ' + (data.message || 'Try again.'));
                button.textContent = originalButtonText;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error in report request:', error);
            alert('There was a connection error while reporting the link.');
            button.textContent = originalButtonText;
            button.disabled = false;
        });
    }

    // --- Función para crear y actualizar el botón de reporte único ---
    function createOrUpdateReportButton(container, data) {
        if (!container) return; // Si el contenedor no existe, no hacer nada
        let reportBtn = container.querySelector('.report-video-btn');
        if (!reportBtn) {
            reportBtn = document.createElement('button');
            reportBtn.classList.add('button', 'button--danger', 'report-video-btn');
            container.appendChild(reportBtn);
            reportBtn.addEventListener('click', handleReportLink);
        }
        reportBtn.textContent = 'Report Video';
        reportBtn.dataset.contentId = data.contentId;
        reportBtn.dataset.contentTitle = data.contentTitle;
        reportBtn.dataset.itemType = data.itemType;
        reportBtn.dataset.reportedLink = data.activeIframeSrc; 
        reportBtn.dataset.serverLabel = data.activeServerLabel;
        if (data.episodeTitle) {
            reportBtn.dataset.episodeTitle = data.episodeTitle;
        }
        reportBtn.disabled = false;
    }


    // --- REPRODUCTOR DE PELÍCULAS (IFRAME) ---
    const movieIframePlayerElement = document.getElementById('main-iframe-player');
    const moviePlayerOptionsContainer = document.getElementById('movie-player-options');
    const movieIframeDataElement = document.getElementById('movie-iframe-data');
    let currentMovieActiveEmbedUrl = ""; 

    if (movieIframePlayerElement && moviePlayerOptionsContainer && movieIframeDataElement) {
        const movieServerButtonsContainer = moviePlayerOptionsContainer.querySelector('#movie-server-buttons');
        const movieReportButtonContainer = moviePlayerOptionsContainer.querySelector('#movie-report-button-container');

        if (movieServerButtonsContainer && movieReportButtonContainer) {
            const iframeSourcesString = movieIframeDataElement.dataset.iframes;
            const movieId = movieIframeDataElement.dataset.id;
            const movieTitle = movieIframeDataElement.dataset.title;
            const itemType = movieIframeDataElement.dataset.itemType; 
            const originalIframes = iframeSourcesString ? iframeSourcesString.split('|||').filter(link => link.trim() !== '') : [];

            movieServerButtonsContainer.innerHTML = '';
            movieReportButtonContainer.innerHTML = '';

            if (originalIframes.length > 0) {
                currentMovieActiveEmbedUrl = originalIframes[0]; 

                if (movieIframePlayerElement.src !== currentMovieActiveEmbedUrl) {
                    movieIframePlayerElement.src = currentMovieActiveEmbedUrl; 
                }

                createOrUpdateReportButton(movieReportButtonContainer, {
                    contentId: movieId,
                    contentTitle: movieTitle,
                    itemType: itemType,
                    activeIframeSrc: currentMovieActiveEmbedUrl, 
                    activeServerLabel: "Server 1" 
                });

                originalIframes.forEach((iframeEmbedSrc, index) => {
                    const serverLabel = `Server ${index + 1}`; 
                    const serverButton = document.createElement('button');
                    serverButton.classList.add('button', 'button--secondary', 'change-movie-server-btn');
                    serverButton.textContent = serverLabel;
                    serverButton.dataset.iframeSrc = iframeEmbedSrc; 

                    if (iframeEmbedSrc === currentMovieActiveEmbedUrl) {
                        serverButton.classList.add('active');
                    }

                    serverButton.addEventListener('click', function() {
                        const newEmbedSrc = this.dataset.iframeSrc; 
                        if (newEmbedSrc && movieIframePlayerElement) {
                            movieIframePlayerElement.src = newEmbedSrc;
                            currentMovieActiveEmbedUrl = newEmbedSrc; 
                            
                            movieServerButtonsContainer.querySelectorAll('.change-movie-server-btn.active').forEach(b => b.classList.remove('active'));
                            this.classList.add('active');

                            createOrUpdateReportButton(movieReportButtonContainer, {
                                contentId: movieId,
                                contentTitle: movieTitle,
                                itemType: itemType,
                                activeIframeSrc: currentMovieActiveEmbedUrl, 
                                activeServerLabel: serverLabel
                            });
                        }
                    });
                    movieServerButtonsContainer.appendChild(serverButton);
                });
            } else {
                const h4 = moviePlayerOptionsContainer.querySelector('h4');
                   if (h4) h4.style.display = 'none';
                   movieServerButtonsContainer.innerHTML = '';
                   movieReportButtonContainer.innerHTML = '';
            }
        } else {
               console.warn("Movie player (iframe): Missing containers for server or report buttons.");
        }
    }


    // --- LÓGICA PARA LA PÁGINA DE REPRODUCTOR DE EPISODIOS ---
    const episodePlayerPageIframe = document.getElementById('episode-iframe-player'); // ID del iframe en episodio_player.html
    const episodePlayerPageData = document.getElementById('episode-player-data'); // Div con datos en episodio_player.html
    const episodePlayerPageControlsContainer = document.getElementById('episode-player-page-controls'); // Contenedor de controles en episodio_player.html
    
    let currentEpisodePageActiveEmbedUrl = ""; // Almacenar la URL de EMBED activa para esta página

    if (episodePlayerPageIframe && episodePlayerPageData && episodePlayerPageControlsContainer) {
        const serverButtonsContainer = episodePlayerPageControlsContainer.querySelector('#episode-player-server-buttons');
        const reportButtonContainer = episodePlayerPageControlsContainer.querySelector('#episode-player-report-button-container');

        if (serverButtonsContainer && reportButtonContainer) {
            const iframeSourcesString = episodePlayerPageData.dataset.iframes;
            const contentId = episodePlayerPageData.dataset.contentId;       // ID de la serie/anime
            const contentTitle = episodePlayerPageData.dataset.contentTitle; // Título de la serie/anime
            const episodeTitle = episodePlayerPageData.dataset.episodeTitle; // Título del episodio actual
            const itemType = episodePlayerPageData.dataset.itemType;         // 'serie' o 'anime'
            
            const originalIframes = iframeSourcesString ? iframeSourcesString.split('|||').filter(link => link.trim() !== '') : [];

            serverButtonsContainer.innerHTML = '';
            reportButtonContainer.innerHTML = '';
            const h4Title = episodePlayerPageControlsContainer.querySelector('h4');
            if (h4Title) h4Title.style.display = 'block';

            if (originalIframes.length > 0) {
                currentEpisodePageActiveEmbedUrl = originalIframes[0];

                if (episodePlayerPageIframe.src !== currentEpisodePageActiveEmbedUrl) {
                    episodePlayerPageIframe.src = currentEpisodePageActiveEmbedUrl;
                }

                createOrUpdateReportButton(reportButtonContainer, {
                    contentId: contentId,
                    contentTitle: contentTitle,
                    itemType: itemType,
                    episodeTitle: episodeTitle,
                    activeIframeSrc: currentEpisodePageActiveEmbedUrl,
                    activeServerLabel: "Server 1"
                });

                originalIframes.forEach((iframeEmbedSrc, index) => {
                    const serverLabel = `Server ${index + 1}`;
                    const serverButton = document.createElement('button');
                    serverButton.classList.add('button', 'button--secondary', 'change-episode-server-btn'); // Puede reutilizar clase o crear una nueva
                    serverButton.textContent = serverLabel;
                    serverButton.dataset.iframeSrc = iframeEmbedSrc;

                    if (iframeEmbedSrc === currentEpisodePageActiveEmbedUrl) {
                        serverButton.classList.add('active');
                    }

                    serverButton.addEventListener('click', function() {
                        const newEmbedSrc = this.dataset.iframeSrc;
                        if (newEmbedSrc && episodePlayerPageIframe) {
                            episodePlayerPageIframe.src = newEmbedSrc;
                            currentEpisodePageActiveEmbedUrl = newEmbedSrc;

                            serverButtonsContainer.querySelectorAll('.change-episode-server-btn.active').forEach(b => b.classList.remove('active'));
                            this.classList.add('active');

                            createOrUpdateReportButton(reportButtonContainer, {
                                contentId: contentId,
                                contentTitle: contentTitle,
                                itemType: itemType,
                                episodeTitle: episodeTitle,
                                activeIframeSrc: currentEpisodePageActiveEmbedUrl,
                                activeServerLabel: serverLabel
                            });
                        }
                    });
                    serverButtonsContainer.appendChild(serverButton);
                });
            } else { 
                if (h4Title) h4Title.style.display = 'none';
                serverButtonsContainer.innerHTML = '';
                reportButtonContainer.innerHTML = '';
                // La plantilla HTML ya muestra un mensaje si no hay iframes
            }
        } else {
            console.warn("Episode Player Page: Missing containers for server or report buttons.");
        }
    }

    // --- Funcionalidad de Acordeón para Temporadas (SOLO EN serie_anime_detail.html) ---
    // Se ejecuta solo si encuentra los elementos específicos de la página de detalle
    if (document.querySelector('.series-anime-detail-page .season-block')) { 
        const seasonBlocks = document.querySelectorAll('.series-anime-detail-page .season-block');
        seasonBlocks.forEach(block => {
            const title = block.querySelector('.season-title');
            const content = block.querySelector('.season-episodes-content');
            if (title && content) {
                title.addEventListener('click', function() {
                    const isExpanded = title.classList.contains('expanded');
                    if (isExpanded) {
                        content.style.maxHeight = null; 
                        content.style.paddingTop = '0px';
                        content.style.paddingBottom = '0px';
                        title.classList.remove('expanded');
                        content.classList.remove('expanded');
                    } else {
                        title.classList.add('expanded');
                        content.classList.add('expanded');
                        content.style.maxHeight = content.scrollHeight + "px";
                    }
                });
            }
        });
    }
});