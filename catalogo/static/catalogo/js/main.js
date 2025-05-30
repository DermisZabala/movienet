document.addEventListener('DOMContentLoaded', function() {

    // --- Navegación Móvil ---
    const navToggle = document.querySelector('.nav-toggle');
    const siteHeader = document.querySelector('.site-header');
    if (navToggle && siteHeader) {
        navToggle.addEventListener('click', () => {
            siteHeader.classList.toggle('nav-active');
        });
    }

    // --- Funcionalidad "Mostrar más" ---
    const contentGrid = document.getElementById('content-grid');
    const showMoreBtn = document.getElementById('show-more-btn');
    let itemsToShow = 10;
    const increment = 5;

    if (contentGrid && showMoreBtn) {
        const allCards = Array.from(contentGrid.getElementsByClassName('card'));
        function displayCards() {
            allCards.forEach((card, index) => {
                if (index < itemsToShow) card.classList.add('visible');
            });
            if (itemsToShow >= allCards.length) showMoreBtn.classList.add('hidden');
            else showMoreBtn.classList.remove('hidden');
        }
        showMoreBtn.addEventListener('click', () => { itemsToShow += increment; displayCards(); });
        if (allCards.length > 0) displayCards(); else if(allCards.length === 0 && showMoreBtn) showMoreBtn.classList.add('hidden');
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
        // reportedLink aquí será la URL de embed (ej. https://vidsrc.icu/embed/...)
        const { contentId, contentTitle, reportedLink, itemType, episodeTitle = '', serverLabel = '' } = button.dataset;

        if (!contentId || !contentTitle || !reportedLink || !itemType) {
            console.error('Incomplete data for report:', button.dataset); // English console
            alert('Missing data to send the report.'); // English alert
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
        const reportUrl = '/reportar-enlace/'; 
        
        const originalButtonText = button.textContent;
        button.disabled = true;
        button.textContent = 'Reporting...'; // English text

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
                alert('Thank you! Your report has been submitted.'); // English alert
                button.textContent = 'Reported';  // English text
            } else {
                alert('Error sending report: ' + (data.message || 'Try again.')); // English alert
                button.textContent = originalButtonText;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error in report request:', error); // English console
            alert('There was a connection error while reporting the link.'); // English alert
            button.textContent = originalButtonText;
            button.disabled = false;
        });
    }

    // --- Función para crear y actualizar el botón de reporte único ---
    function createOrUpdateReportButton(container, data) {
        let reportBtn = container.querySelector('.report-video-btn');
        if (!reportBtn) {
            reportBtn = document.createElement('button');
            reportBtn.classList.add('button', 'button--danger', 'report-video-btn');
            container.appendChild(reportBtn);
            reportBtn.addEventListener('click', handleReportLink);
        }
        reportBtn.textContent = 'Report Video'; // English text
        reportBtn.dataset.contentId = data.contentId;
        reportBtn.dataset.contentTitle = data.contentTitle;
        reportBtn.dataset.itemType = data.itemType;
        reportBtn.dataset.reportedLink = data.activeIframeSrc; // activeIframeSrc será la URL de EMBED
        reportBtn.dataset.serverLabel = data.activeServerLabel;
        if (data.episodeTitle) {
            reportBtn.dataset.episodeTitle = data.episodeTitle;
        }
        reportBtn.disabled = false;
    }


    // --- Reproductor de Películas (iframe) ---
    const movieIframePlayerElement = document.getElementById('main-iframe-player');
    const moviePlayerOptionsContainer = document.getElementById('movie-player-options');
    const movieIframeDataElement = document.getElementById('movie-iframe-data');
    let currentMovieActiveEmbedUrl = ""; // Almacenar la URL de EMBED activa para la película

    if (movieIframePlayerElement && moviePlayerOptionsContainer && movieIframeDataElement) {
        const movieServerButtonsContainer = moviePlayerOptionsContainer.querySelector('#movie-server-buttons');
        const movieReportButtonContainer = moviePlayerOptionsContainer.querySelector('#movie-report-button-container');

        if (movieServerButtonsContainer && movieReportButtonContainer) {
            const iframeSourcesString = movieIframeDataElement.dataset.iframes;
            const movieId = movieIframeDataElement.dataset.id;
            const movieTitle = movieIframeDataElement.dataset.title;
            const itemType = movieIframeDataElement.dataset.itemType; // This will be "pelicula"
            const originalIframes = iframeSourcesString ? iframeSourcesString.split('|||').filter(link => link.trim() !== '') : []; // Estas son las URLs de EMBED

            movieServerButtonsContainer.innerHTML = '';
            movieReportButtonContainer.innerHTML = '';

            if (originalIframes.length > 0) {
                currentMovieActiveEmbedUrl = originalIframes[0]; // Asignar la primera URL de embed como activa

                if (movieIframePlayerElement.src !== currentMovieActiveEmbedUrl) {
                    movieIframePlayerElement.src = currentMovieActiveEmbedUrl; 
                }

                createOrUpdateReportButton(movieReportButtonContainer, {
                    contentId: movieId,
                    contentTitle: movieTitle,
                    itemType: itemType,
                    activeIframeSrc: currentMovieActiveEmbedUrl, 
                    activeServerLabel: "Server 1" // English text
                });

                originalIframes.forEach((iframeEmbedSrc, index) => {
                    const serverLabel = `Server ${index + 1}`; // English text
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
             console.warn("Movie player (iframe): Missing containers for server or report buttons."); // English console
        }
    }


    // --- Reproductor de Series/Anime (iframe) ---
    const seriesAnimeIframePlayerElement = document.getElementById('series-anime-main-iframe-player');
    const dynamicPlayerSection = document.getElementById('dynamic-player-section');
    const currentEpisodeTitlePlayerEl = document.getElementById('current-episode-title-player');
    const currentEpisodeControlsContainer = document.getElementById('current-episode-controls'); 
    let currentEpisodeActiveEmbedUrl = ""; // Almacenar la URL de EMBED activa para el episodio actual

    if (seriesAnimeIframePlayerElement && dynamicPlayerSection && currentEpisodeTitlePlayerEl && currentEpisodeControlsContainer) {
        const episodeServerButtonsContainer = currentEpisodeControlsContainer.querySelector('#episode-server-buttons');
        const episodeReportButtonContainer = currentEpisodeControlsContainer.querySelector('#episode-report-button-container');
        
        if (!episodeServerButtonsContainer || !episodeReportButtonContainer) {
            console.warn("Series/Anime player (iframe): Missing containers for episode server or report buttons."); // English console
        } else {
            document.querySelectorAll('.series-anime-detail-page .play-episode-master-btn').forEach(masterButton => {
                masterButton.addEventListener('click', function() {
                    const episodeItem = this.closest('.episode-item');
                    const { episodeTitle, episodeIframes, contentId, contentTitle, itemType } = episodeItem.dataset; // itemType will be 'serie' or 'anime'
                    const originalIframes = episodeIframes ? episodeIframes.split('|||').filter(link => link.trim() !== '') : []; // URLs de EMBED

                    episodeServerButtonsContainer.innerHTML = '';
                    episodeReportButtonContainer.innerHTML = '';
                    const h4Title = currentEpisodeControlsContainer.querySelector('h4');
                    if (h4Title) h4Title.style.display = 'block';

                    if (originalIframes.length === 0) {
                        alert('No playback links available for this episode.'); // English alert
                        currentEpisodeTitlePlayerEl.textContent = episodeTitle + " (No links)"; // English text
                        dynamicPlayerSection.style.display = 'block'; 
                        episodeServerButtonsContainer.style.display = 'none';
                        episodeReportButtonContainer.style.display = 'none';
                        if (h4Title) h4Title.style.display = 'none';
                        seriesAnimeIframePlayerElement.src = ''; 
                        currentEpisodeActiveEmbedUrl = ""; 
                        return;
                    }

                    episodeServerButtonsContainer.style.display = 'flex'; 
                    episodeReportButtonContainer.style.display = 'flex';

                    currentEpisodeTitlePlayerEl.textContent = episodeTitle;
                    dynamicPlayerSection.style.display = 'block';

                    currentEpisodeActiveEmbedUrl = originalIframes[0]; 
                    seriesAnimeIframePlayerElement.src = currentEpisodeActiveEmbedUrl;

                    createOrUpdateReportButton(episodeReportButtonContainer, {
                        contentId: contentId,
                        contentTitle: contentTitle, 
                        itemType: itemType,
                        episodeTitle: episodeTitle, 
                        activeIframeSrc: currentEpisodeActiveEmbedUrl, 
                        activeServerLabel: "Server 1" // English text
                    });

                    originalIframes.forEach((iframeEmbedSrc, index) => {
                        const serverLabel = `Server ${index + 1}`; // English text
                        const serverButton = document.createElement('button');
                        serverButton.classList.add('button', 'button--secondary', 'change-episode-server-btn');
                        serverButton.textContent = serverLabel;
                        serverButton.dataset.iframeSrc = iframeEmbedSrc; 

                        if (iframeEmbedSrc === currentEpisodeActiveEmbedUrl) {
                           serverButton.classList.add('active');
                        }

                        serverButton.addEventListener('click', function() {
                            const newEmbedSrc = this.dataset.iframeSrc; 
                            if (newEmbedSrc && seriesAnimeIframePlayerElement) {
                                seriesAnimeIframePlayerElement.src = newEmbedSrc;
                                currentEpisodeActiveEmbedUrl = newEmbedSrc; 
                                
                                episodeServerButtonsContainer.querySelectorAll('.change-episode-server-btn.active').forEach(b => b.classList.remove('active'));
                                this.classList.add('active');

                                createOrUpdateReportButton(episodeReportButtonContainer, {
                                    contentId: contentId,
                                    contentTitle: contentTitle,
                                    itemType: itemType,
                                    episodeTitle: episodeTitle,
                                    activeIframeSrc: currentEpisodeActiveEmbedUrl, 
                                    activeServerLabel: serverLabel
                                });
                            }
                        });
                        episodeServerButtonsContainer.appendChild(serverButton);
                    });

                    dynamicPlayerSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                });
            });
        }
    }

    // --- Funcionalidad de Acordeón para Temporadas ---
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
});