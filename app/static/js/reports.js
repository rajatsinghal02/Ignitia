document.addEventListener('DOMContentLoaded', function () {
    // --- Animate Stat Cards ---
    const counters = document.querySelectorAll('.stat-card .value');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-value'), 10);
        let current = 0;
        const increment = target / 100; // Animate in 100 steps

        const updateCounter = () => {
            if (current < target) {
                current += increment;
                counter.textContent = Math.ceil(current).toLocaleString();
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toLocaleString();
            }
        };
        updateCounter();
    });

    // =============================================
    // NEW CHART LOGIC
    // =============================================
    const purple_primary = '#8b74cc';
    const purple_secondary = '#b7a9df';
    const textColor = '#53399c';

    // --- Chart 1: All Investigation Reports (Line Chart) ---
    const allReportsCtx = document.getElementById('allReportsChart');
    if (allReportsCtx) {
        new Chart(allReportsCtx, {
            type: 'line',
            data: {
                labels: chart1Labels,
                datasets: [
                    {
                        label: 'Total Investigations',
                        data: chart1TotalData,
                        borderColor: purple_primary,
                        backgroundColor: 'rgba(139, 116, 204, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: purple_primary,
                        pointBorderColor: '#fff',
                        pointHoverRadius: 7,
                        pointHoverBorderWidth: 2,
                    },
                    {
                        label: 'Completed',
                        data: chart1CompletedData,
                        borderColor: purple_secondary,
                        backgroundColor: 'rgba(183, 169, 223, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: purple_secondary,
                        pointBorderColor: '#fff',
                        pointHoverRadius: 7,
                        pointHoverBorderWidth: 2,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', align: 'end' } },
                scales: {
                    y: { grid: { drawBorder: false } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // =======================================================
    // NEW SLIDER AND FILTER LOGIC
    // =======================================================

    // --- 1. Initialize Swiper Slider ---
    const swiper = new Swiper('#investigation-swiper', {
        slidesPerView: 1,
        spaceBetween: 20,
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        breakpoints: {
            640: { slidesPerView: 2 },
            1024: { slidesPerView: 3 },
            1280: { slidesPerView: 4 },
        },
    });

    // --- 2. Initialize Flatpickr Date Picker ---
    const datePickerInput = document.getElementById('date-range-picker');
    const clearFilterBtn = document.getElementById('clear-filter-btn');

    const fp = flatpickr(datePickerInput, {
        mode: 'range',
        dateFormat: 'Y-m-d',
        onClose: function(selectedDates) {
            // Only filter if a full range (2 dates) is selected
            if (selectedDates.length === 2) {
                filterInvestigations(selectedDates);
                clearFilterBtn.style.display = 'inline-block';
            }
        }
    });
    
    // --- 3. Filter Logic ---
    function filterInvestigations(dates) {
        const [startDate, endDate] = dates;
        const slides = document.querySelectorAll('#investigation-swiper .swiper-slide');

        slides.forEach(slide => {
            const invDate = new Date(slide.dataset.date);
            // Check if the investigation date is within the selected range
            if (invDate >= startDate && invDate <= endDate) {
                slide.style.display = 'flex'; // Use 'flex' to match Swiper's default
            } else {
                slide.style.display = 'none';
            }
        });

        swiper.update(); // CRITICAL: Tell Swiper to recalculate its layout
    }

    // --- 4. Clear Filter Logic ---
    clearFilterBtn.addEventListener('click', () => {
        fp.clear(); // Clear the date picker
        document.querySelectorAll('#investigation-swiper .swiper-slide').forEach(slide => {
            slide.style.display = 'flex'; // Show all slides again
        });
        swiper.update(); // Update Swiper
        clearFilterBtn.style.display = 'none'; // Hide the clear button
    });

    // =======================================================
    // NEW HIERARCHICAL MODAL LOGIC
    // =======================================================

    // --- 1. Modal Elements ---
    const capturesModal = document.getElementById('captures-modal-overlay');
    const groupAnalysisModal = document.getElementById('group-analysis-modal-overlay');
    const personDetailsModal = document.getElementById('person-details-modal-overlay');
    const allModals = [capturesModal, groupAnalysisModal, personDetailsModal];
    let modalStack = [];

    // --- 2. Modal Stack Management ---
    function openModal(modal) {
        if (modalStack.length > 0) {
            const currentTop = modalStack[modalStack.length - 1];
            currentTop.classList.remove('active');
        }
        modal.classList.add('active');
        modalStack.push(modal);
    }

    function closeTopModal() {
        if (modalStack.length === 0) return;
        const closingModal = modalStack.pop();
        closingModal.classList.remove('active');

        if (modalStack.length > 0) {
            const newTopModal = modalStack[modalStack.length - 1];
            newTopModal.classList.add('active');
        }
    }

    // --- 3. Global Close Listeners ---
    allModals.forEach(modal => {
        if (!modal) return;
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeTopModal();
            }
        });
        const closeBtn = modal.querySelector('.modal-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeTopModal);
        }
    });


    // --- 4. Investigation Card Click -> Open Captures Modal ---
    const sliderContainer = document.getElementById('investigation-swiper');
    sliderContainer.addEventListener('click', function(e) {
        const card = e.target.closest('.report-inv-card');
        if (!card) return;

        const investigationId = card.dataset.investigationId;
        const investigationTitle = card.querySelector('h4').textContent;
        const modalGrid = capturesModal.querySelector('#captures-modal-grid');
        const modalTitle = capturesModal.querySelector('#captures-modal-title');
        // ===== START: MODIFIED SECTION =====
        const modalSubtitle = capturesModal.querySelector('#captures-modal-subtitle'); // 1. Get the subtitle element
        
        modalTitle.textContent = `Captures for: ${investigationTitle}`;
        modalSubtitle.textContent = 'Loading captures...'; // 2. Set a loading state
        // ===== END: MODIFIED SECTION =====
        modalGrid.innerHTML = '<p class="placeholder-text">Loading...</p>';
        openModal(capturesModal);
        
        fetch(`/investigation/${investigationId}/captures`)
            .then(response => response.json())
            .then(captures => {
                // ===== START: MODIFIED SECTION =====
                const captureCount = captures.length; // 3. Get the count
                modalSubtitle.textContent = `Viewing ${captureCount} captured images for this investigation.`; // 4. Update the text
                // ===== END: MODIFIED SECTION =====
                
                modalGrid.innerHTML = '';
                if (captures.length > 0) {
                    captures.forEach(capture => {
                        const imgWrapper = document.createElement('div');
                        imgWrapper.className = 'capture-image-wrapper';
                        imgWrapper.dataset.captureId = capture.id; // IMPORTANT
                        imgWrapper.innerHTML = `<img src="${capture.url}" alt="Capture">`;
                        modalGrid.appendChild(imgWrapper);
                    });
                } else {
                    modalGrid.innerHTML = '<p class="placeholder-text">No captures found.</p>';
                }
            })
            .catch(error => {
                console.error('Error fetching captures:', error);
                modalSubtitle.textContent = 'Could not load captures.'; // Handle error state
                modalGrid.innerHTML = '<p class="placeholder-text error">Could not load captures.</p>';
            });
    });

    // --- 5. Capture Click -> Open Group Analysis Modal ---
    capturesModal.querySelector('#captures-modal-grid').addEventListener('click', (e) => {
        const wrapper = e.target.closest('.capture-image-wrapper');
        if (!wrapper) return;

        const captureId = wrapper.dataset.captureId;
        const grid = groupAnalysisModal.querySelector('#group-faces-grid');
        grid.innerHTML = '<p class="placeholder-text">Analyzing image... Please wait.</p>';
        openModal(groupAnalysisModal);

        fetch(`/capture/${captureId}/analyze`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                populateAndOpenGroupModal(data);
            })
            .catch(error => {
                console.error('Analysis failed:', error);
                grid.innerHTML = `<p class="placeholder-text error">Analysis failed: ${error.message}</p>`;
            });
    });

    function populateAndOpenGroupModal(data) {
        const { group_stats, faces } = data;
        
        // Populate header
        document.getElementById('group-total-faces').textContent = group_stats.total_faces || 0;
        document.getElementById('group-male-count').textContent = group_stats.male_count || 0;
        document.getElementById('group-female-count').textContent = group_stats.female_count || 0;
        document.getElementById('group-panic-score').textContent = `${group_stats.panic_score || 0}%`;

        // Populate grid
        const grid = document.getElementById('group-faces-grid');
        grid.innerHTML = '';

        if (faces.length > 0) {
            faces.forEach(face => {
                const card = document.createElement('div');
                card.className = 'face-card';
                // Store all data on the element for the next modal
                Object.keys(face).forEach(key => {
                    card.dataset[key] = face[key];
                });
                
                card.innerHTML = `
                    <img src="${face.crop_base64}" alt="Face crop">
                    <div class="face-card-info">
                        ${face.gender}, ${face.age_range}<br>
                        <strong>Panic: ${face.panic_score}%</strong>
                    </div>
                `;
                grid.appendChild(card);
            });
        } else {
            grid.innerHTML = '<p class="placeholder-text">No faces were detected in this capture.</p>';
        }
    }


    // --- 6. Face Crop Click -> Open Person Details Modal ---
    groupAnalysisModal.querySelector('#group-faces-grid').addEventListener('click', (e) => {
        const card = e.target.closest('.face-card');
        if (!card) return;
        populateAndOpenPersonModal(card.dataset);
    });

    function populateAndOpenPersonModal(personData) {
        document.getElementById('person-detail-img').src = personData.crop_base64;
        document.getElementById('person-detail-gender').textContent = personData.gender;
        document.getElementById('person-detail-age').textContent = personData.age_range;
        document.getElementById('person-detail-emotion').textContent = personData.emotion_label;
        document.getElementById('person-detail-vulnerability').textContent = personData.vulnerability;
        document.getElementById('person-detail-fear').textContent = personData.fear_score;
        document.getElementById('person-detail-panic').innerHTML = `${personData.panic_score}%`;

        openModal(personDetailsModal);
    }
});