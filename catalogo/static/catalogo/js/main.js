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
        const { contentId, contentTitle, reportedLink, itemType, episodeTitle = '', serverLabel = '' } = button.dataset;

        if (!contentId || !contentTitle || !reportedLink || !itemType) {
            console.error('Datos incompletos para reporte:', button.dataset);
            alert('Faltan datos para enviar el reporte.');
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
        const reportUrl = '/reportar-enlace/'; // Asegúrate que esta URL es correcta
        
        const originalButtonText = button.textContent;
        button.disabled = true;
        button.textContent = 'Reportando...';

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
                alert('¡Gracias! Tu reporte ha sido enviado.');
                button.textContent = 'Reportado'; // Mantener como reportado y deshabilitado
            } else {
                alert('Error al enviar el reporte: ' + (data.message || 'Inténtalo de nuevo.'));
                button.textContent = originalButtonText;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error en la petición de reporte:', error);
            alert('Hubo un error de conexión al reportar el enlace.');
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
        reportBtn.textContent = 'Reportar Video'; // Nombre del botón
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


    // --- Reproductor de Películas (Video.js) ---
    let moviePlayer;
    const moviePlayerElement = document.getElementById('main-video-player'); // ID correcto para película
    const moviePlayerOptionsContainer = document.getElementById('movie-player-options'); // Contenedor general

    if (moviePlayerElement && moviePlayerOptionsContainer) {
        const movieServerButtonsContainer = moviePlayerOptionsContainer.querySelector('#movie-server-buttons');
        const movieReportButtonContainer = moviePlayerOptionsContainer.querySelector('#movie-report-button-container');
        const movieIframeDataElement = moviePlayerOptionsContainer.querySelector('#movie-iframe-data');

        if (movieServerButtonsContainer && movieReportButtonContainer && movieIframeDataElement) {
            const iframeSourcesString = movieIframeDataElement.dataset.iframes;
            const movieId = movieIframeDataElement.dataset.id;
            const movieTitle = movieIframeDataElement.dataset.title;
            const itemType = movieIframeDataElement.dataset.itemType; // Asegúrate que este data-attribute existe
            const originalIframes = iframeSourcesString ? iframeSourcesString.split('|||').filter(link => link.trim() !== '') : [];

            movieServerButtonsContainer.innerHTML = '';
            movieReportButtonContainer.innerHTML = '';

            if (originalIframes.length > 0) {
                moviePlayer = videojs('main-video-player'); // Usa el ID correcto aquí

                // Cargar el primer iframe por defecto SIN AUTOPLAY
                moviePlayer.src({ src: originalIframes[0], type: 'application/x-mpegURL' });
                // NO moviePlayer.play();

                createOrUpdateReportButton(movieReportButtonContainer, {
                    contentId: movieId,
                    contentTitle: movieTitle,
                    itemType: itemType,
                    activeIframeSrc: originalIframes[0],
                    activeServerLabel: "Servidor 1"
                });

                originalIframes.forEach((iframeSrc, index) => {
                    const serverLabel = `Servidor ${index + 1}`;
                    const serverButton = document.createElement('button');
                    serverButton.classList.add('button', 'button--secondary', 'change-movie-server-btn');
                    serverButton.textContent = serverLabel;
                    serverButton.dataset.iframeSrc = iframeSrc;

                    if (index === 0) { serverButton.classList.add('active'); }

                    serverButton.addEventListener('click', function() {
                        const newSrc = this.dataset.iframeSrc;
                        if (newSrc && moviePlayer) {
                            moviePlayer.src({ src: newSrc, type: 'application/x-mpegURL' });
                            // NO moviePlayer.play();
                            
                            movieServerButtonsContainer.querySelectorAll('.change-movie-server-btn.active').forEach(b => b.classList.remove('active'));
                            this.classList.add('active');

                            createOrUpdateReportButton(movieReportButtonContainer, {
                                contentId: movieId,
                                contentTitle: movieTitle,
                                itemType: itemType,
                                activeIframeSrc: newSrc,
                                activeServerLabel: serverLabel
                            });
                        }
                    });
                    movieServerButtonsContainer.appendChild(serverButton);
                });
            } else {
                const h4 = moviePlayerOptionsContainer.querySelector('h4');
                moviePlayerOptionsContainer.innerHTML = '';
                if (h4) moviePlayerOptionsContainer.appendChild(h4);
                moviePlayerOptionsContainer.innerHTML += '<p class="message message--warning">No hay enlaces de reproducción disponibles.</p>';
            }
        } else {
             console.warn("Movie player: Faltan contenedores para botones de servidor o reporte, o el div de datos.");
        }
    }


    // --- Reproductor de Series/Anime (Video.js) ---
    let seriesAnimePlayer;
    const seriesAnimePlayerElement = document.getElementById('series-anime-main-video-player');
    const dynamicPlayerSection = document.getElementById('dynamic-player-section');
    const currentEpisodeTitlePlayerEl = document.getElementById('current-episode-title-player');
    const currentEpisodeControlsContainer = document.getElementById('current-episode-controls'); // Contenedor general

    if (seriesAnimePlayerElement && dynamicPlayerSection && currentEpisodeTitlePlayerEl && currentEpisodeControlsContainer) {
        const episodeServerButtonsContainer = currentEpisodeControlsContainer.querySelector('#episode-server-buttons');
        const episodeReportButtonContainer = currentEpisodeControlsContainer.querySelector('#episode-report-button-container');
        
        if (!episodeServerButtonsContainer || !episodeReportButtonContainer) {
            console.warn("Series/Anime player: Faltan contenedores para botones de servidor o reporte de episodio.");
        } else {
            seriesAnimePlayer = videojs('series-anime-main-video-player');

            document.querySelectorAll('.series-anime-detail-page .play-episode-master-btn').forEach(masterButton => {
                masterButton.addEventListener('click', function() {
                    const episodeItem = this.closest('.episode-item');
                    const { episodeTitle, episodeIframes, contentId, contentTitle, itemType } = episodeItem.dataset;
                    const originalIframes = episodeIframes ? episodeIframes.split('|||').filter(link => link.trim() !== '') : [];

                    episodeServerButtonsContainer.innerHTML = '';
                    episodeReportButtonContainer.innerHTML = '';

                    if (originalIframes.length === 0) {
                        alert('No hay enlaces de reproducción disponibles para este episodio.');
                        currentEpisodeTitlePlayerEl.textContent = episodeTitle + " (Sin enlaces)";
                        dynamicPlayerSection.style.display = 'block'; // Mostrar sección pero sin opciones
                        // Podrías ocultar los contenedores de botones si no hay iframes
                        episodeServerButtonsContainer.style.display = 'none';
                        episodeReportButtonContainer.style.display = 'none';
                        // Y resetear el reproductor
                        if (seriesAnimePlayer) seriesAnimePlayer.reset();
                        return;
                    }

                    episodeServerButtonsContainer.style.display = 'flex'; // O el display que uses
                    episodeReportButtonContainer.style.display = 'flex';


                    currentEpisodeTitlePlayerEl.textContent = episodeTitle;
                    dynamicPlayerSection.style.display = 'block';

                    seriesAnimePlayer.src({ src: originalIframes[0], type: 'application/x-mpegURL' });
                    // NO seriesAnimePlayer.play();

                    createOrUpdateReportButton(episodeReportButtonContainer, {
                        contentId: contentId,
                        contentTitle: contentTitle,
                        itemType: itemType,
                        episodeTitle: episodeTitle,
                        activeIframeSrc: originalIframes[0],
                        activeServerLabel: "Servidor 1"
                    });

                    originalIframes.forEach((iframeSrc, index) => {
                        const serverLabel = `Servidor ${index + 1}`;
                        const serverButton = document.createElement('button');
                        serverButton.classList.add('button', 'button--secondary', 'change-episode-server-btn');
                        serverButton.textContent = serverLabel;
                        serverButton.dataset.iframeSrc = iframeSrc;

                        if (index === 0) { serverButton.classList.add('active'); }

                        serverButton.addEventListener('click', function() {
                            const newSrc = this.dataset.iframeSrc;
                            if (newSrc && seriesAnimePlayer) {
                                seriesAnimePlayer.src({ src: newSrc, type: 'application/x-mpegURL' });
                                // NO seriesAnimePlayer.play();
                                
                                episodeServerButtonsContainer.querySelectorAll('.change-episode-server-btn.active').forEach(b => b.classList.remove('active'));
                                this.classList.add('active');

                                createOrUpdateReportButton(episodeReportButtonContainer, {
                                    contentId: contentId,
                                    contentTitle: contentTitle,
                                    itemType: itemType,
                                    episodeTitle: episodeTitle,
                                    activeIframeSrc: newSrc,
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

    // --- Funcionalidad de Acordeón para Temporadas (Implementación JS Pura) ---
    const seasonBlocks = document.querySelectorAll('.series-anime-detail-page .season-block');

    seasonBlocks.forEach(block => {
        const title = block.querySelector('.season-title'); // h3
        const content = block.querySelector('.season-episodes-content'); // div que envuelve la ul

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
                    // Opcional: Cerrar otros bloques
                    /*
                    seasonBlocks.forEach(otherBlock => {
                        if (otherBlock !== block) {
                            const otherTitle = otherBlock.querySelector('.season-title');
                            const otherContent = otherBlock.querySelector('.season-episodes-content');
                            if (otherTitle && otherContent && otherTitle.classList.contains('expanded')) {
                                otherContent.style.maxHeight = null;
                                otherContent.style.paddingTop = '0px';
                                otherContent.style.paddingBottom = '0px';
                                otherTitle.classList.remove('expanded');
                                otherContent.classList.remove('expanded');
                            }
                        }
                    });
                    */
                    title.classList.add('expanded');
                    content.classList.add('expanded');
                    content.style.maxHeight = content.scrollHeight + "px";
                }
            });
        }
    });

});