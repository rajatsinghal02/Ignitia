// static/script.js

// --- Make this a GLOBAL function by defining it here ---
function showConfirmationModal(config) {
    const confirmationModalOverlay = document.getElementById('confirmation-modal-overlay');
    if (!confirmationModalOverlay) return;

    const titleEl = document.getElementById('confirmation-title');
    const messageEl = document.getElementById('confirmation-message');
    const confirmBtnEl = document.getElementById('confirmation-confirm-btn');
    const formEl = document.getElementById('confirmation-form');
    
    // --- UPDATED BUTTON STYLING LOGIC ---
    // Use classList for more precise control instead of resetting the whole className
    confirmBtnEl.classList.remove('primary', 'danger'); // Remove any previous color classes

    if (config.buttonColor === 'red') {
        confirmBtnEl.classList.add('danger'); // Add danger class for red buttons
    } else {
        confirmBtnEl.classList.add('primary'); // Add primary class for default purple buttons
    }
    // --- END OF UPDATED LOGIC ---

    formEl.querySelectorAll('input[type="hidden"]').forEach(input => input.remove());
    titleEl.textContent = config.title;
    messageEl.innerHTML = config.message;
    confirmBtnEl.textContent = config.confirmText;
    formEl.action = config.formAction;
    
    if (config.newStatus) {
        const statusInput = document.createElement('input');
        statusInput.type = 'hidden';
        statusInput.name = 'new_status';
        statusInput.value = config.newStatus;
        formEl.appendChild(statusInput);
    }
    if (config.goLive) {
        const goLiveInput = document.createElement('input');
        goLiveInput.type = 'hidden';
        goLiveInput.name = 'go_live';
        goLiveInput.value = 'true';
        formEl.appendChild(goLiveInput);
    }
    
    confirmationModalOverlay.classList.add('active');
}


document.addEventListener('DOMContentLoaded', function () {
    // --- Universal Elements ---
    const html = document.documentElement;
    const body = document.body;
    
    // Enable transitions after page load to prevent initial flicker
    window.addEventListener('load', () => body.classList.add('transitions-enabled'));

    // --- 1. DESKTOP Sidebar Logic ---
    const desktopToggleBtn = document.getElementById('sidebar-toggle-btn');
    if (desktopToggleBtn) {
        desktopToggleBtn.addEventListener('click', function() {
            // Your original desktop code, works perfectly
            const state = html.dataset.sidebarState === 'collapsed' ? 'open' : 'collapsed';
            html.dataset.sidebarState = state;
            localStorage.setItem('sidebarState', state);
        });
    }
    
    // --- 2. MOBILE Sidebar Logic ---
    const mobileToggleBtn = document.getElementById('mobile-sidebar-toggle');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');

    if (mobileToggleBtn) {
        mobileToggleBtn.addEventListener('click', function() {
            body.classList.add('sidebar-mobile-open');
            sidebarOverlay.classList.add('active');
        });
    }

    function closeMobileSidebar() {
        body.classList.remove('sidebar-mobile-open');
        sidebarOverlay.classList.remove('active');
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeMobileSidebar);
    }
    sidebarLinks.forEach(link => {
        link.addEventListener('click', closeMobileSidebar);
    });

    // --- Main App Modal Logic ---
    const openModalBtn = document.getElementById('open-modal-btn');
    const newInvModalOverlay = document.getElementById('new-investigation-modal-overlay');
    if (openModalBtn) openModalBtn.addEventListener('click', (e) => { e.preventDefault(); if (newInvModalOverlay) newInvModalOverlay.classList.add('active'); });
    if (newInvModalOverlay) {
        newInvModalOverlay.querySelector('#modal-close-btn').addEventListener('click', () => newInvModalOverlay.classList.remove('active'));
        newInvModalOverlay.addEventListener('click', (e) => { if (e.target === newInvModalOverlay) newInvModalOverlay.classList.remove('active'); });
    }

    // --- Dynamic Flash Message Logic (updated) ---
    // Auto-dismiss only non-persistent alerts
    document.querySelectorAll('.alert').forEach(alert => {
    // If this is a persistent alert, skip auto-dismiss
    if (alert.classList.contains('alert-persistent')) {
        // still add an animationend listener to remove only when fadeOut happens (e.g. when user clicks close)
        alert.addEventListener('animationend', (e) => {
        if (e.animationName === 'fadeOut') alert.remove();
        });
        return;
    }

    // For normal alerts: add progress & auto fade
    const timeout = 5000;
    const timer = setTimeout(() => {
        alert.classList.add('fade-out');
    }, timeout);

    // When fadeOut animation finishes, remove the node
    alert.addEventListener('animationend', (e) => {
        if (e.animationName === 'fadeOut') alert.remove();
    });

    // If user manually closes before timeout, clear the timeout
    const closeBtn = alert.querySelector('.alert-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
        clearTimeout(timer);
        alert.classList.add('fade-out');
        });
    }
    });

    // --- Edit Modal Logic ---
    const editModalOverlay = document.getElementById('edit-investigation-modal-overlay');
    if (editModalOverlay) {
        editModalOverlay.querySelector('#edit-modal-close-btn').addEventListener('click', () => editModalOverlay.classList.remove('active'));
    }
    const editFileBtn = document.getElementById('edit_drone_photo');
    if (editFileBtn) {
        const editFileChosen = document.getElementById('edit-file-chosen');
        editFileBtn.addEventListener('change', function(){
            editFileChosen.textContent = this.files.length > 0 ? this.files[0].name : 'No new file selected';
        });
    }

    // --- Universal Confirmation Modal Handler ---
    const confirmationModalOverlay = document.getElementById('confirmation-modal-overlay');
    if (confirmationModalOverlay) {
        const closeBtn = confirmationModalOverlay.querySelector('#confirmation-modal-close-btn');
        const cancelBtn = confirmationModalOverlay.querySelector('#confirmation-cancel-btn');
        const closeConfirmationModal = () => confirmationModalOverlay.classList.remove('active');
        if(closeBtn) closeBtn.addEventListener('click', closeConfirmationModal);
        if(cancelBtn) cancelBtn.addEventListener('click', closeConfirmationModal);
    }

    
    function showCustomFlash(message) {
        const container = document.querySelector('.flash-messages');
        if (!container) {
            console.warn('Flash container not found: .flash-messages');
            return;
        }

        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-persistent';

        // Accessibility
        alertDiv.setAttribute('role', 'status');
        alertDiv.setAttribute('aria-live', 'polite');

        const alertContent = document.createElement('div');
        alertContent.className = 'alert-content';

        const alertIcon = document.createElement('div');
        alertIcon.className = 'alert-icon';
        alertIcon.innerHTML = '<i class="fas fa-exclamation-triangle" aria-hidden="true"></i>';

        const alertMessage = document.createElement('div');
        alertMessage.className = 'alert-message';
        // message expected to contain safe HTML like an <a href="...">; keep as innerHTML
        alertMessage.innerHTML = message;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'alert-close-btn';
        closeBtn.setAttribute('aria-label', 'Close alert');
        closeBtn.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i>';

        // Close handler: start fadeOut and remove only after animation ends
        closeBtn.addEventListener('click', () => {
            // Add fade-out class to play animation
            alertDiv.classList.add('fade-out');
        });

        // Make sure we remove only after our fadeOut animation runs
        alertDiv.addEventListener('animationend', (e) => {
            if (e.animationName === 'fadeOut') {
            alertDiv.remove();
            }
        });

        alertContent.appendChild(alertIcon);
        alertContent.appendChild(alertMessage);
        alertDiv.appendChild(alertContent);
        alertDiv.appendChild(closeBtn);

        // Put newest on top
        container.prepend(alertDiv);

        // Focus the close button for keyboard accessibility
        closeBtn.focus();
    }

    // =============================================
    // UNIFIED EVENT LISTENER FOR ALL CARD GRIDS
    // =============================================
    const mainContentArea = document.querySelector('.content-area');
    if(mainContentArea) {
        mainContentArea.addEventListener('click', function(e) {
            const card = e.target.closest('.inv-card');
            if (!card) return; // Exit if the click wasn't on or inside a card

            const isDashboard = card.closest('.dashboard-grid');
            const actionButton = e.target.closest('.inv-action-btn');

            const id = card.dataset.id;
            const title = card.dataset.title;
            const status = card.dataset.status;
            const timestamp = card.dataset.timestamp;

            // --- Logic for Dashboard Cards ---
            if (isDashboard) {
                if (status === 'Live' || status === 'Pending') {
                    showConfirmationModal({
                        title: status === 'Live' ? 'Start Investigation' : 'Continue Investigation',
                        message: Open live screen for <strong>${title}</strong>?,
                        confirmText: status === 'Live' ? 'Yes, Start' : 'Yes, Continue',
                        newStatus: 'Live',
                        goLive: true,
                        formAction: /investigation/${id}/update_status
                    });
                } else if (status === 'Completed') {
                    const investigationsPageUrl = /investigations#${timestamp};
                    const message = This investigation is complete. You can <a href="${investigationsPageUrl}">view or delete it</a>.;
                    showCustomFlash(message);
                }
            // --- Logic for Investigations Page Cards (only if an action button was clicked) ---
            } else if (actionButton) {
                const action = actionButton.dataset.action;
                if (action === 'edit') {
                    const editForm = document.getElementById('edit-investigation-form');
                    editForm.querySelector('[name="title"]').value = card.dataset.title;
                    editForm.querySelector('[name="location"]').value = card.dataset.location;
                    editForm.querySelector('[name="description"]').value = card.dataset.description;
                    editForm.action = /investigation/${id}/edit;
                    if (editModalOverlay) editModalOverlay.classList.add('active');
                } else if (action === 'delete') {
                    showConfirmationModal({
                        title: 'Confirm Deletion', message: Delete <strong>${title}</strong>?,
                        confirmText: 'Yes, Delete', buttonColor: 'red',
                        formAction: /investigation/${id}/delete
                    });
                } else if (action === 'start' || action === 'continue') {
                    showConfirmationModal({
                        title: action === 'start' ? 'Start Investigation' : 'Continue Investigation',
                        message: Open live screen for <strong>${title}</strong>?,
                        confirmText: action === 'start' ? 'Yes, Start' : 'Yes, Continue',
                        newStatus: 'Live', goLive: true,
                        formAction: /investigation/${id}/update_status
                    });
                }
            }
        });
    }
});