// Main JavaScript for TimeWeave

// Utility Functions
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

// Setup CSRF token for AJAX requests
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

// Copy to Clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Đã sao chép!', 'success');
        }, function(err) {
            console.error('Could not copy text: ', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.top = 0;
    textArea.style.left = 0;
    textArea.style.width = "2em";
    textArea.style.height = "2em";
    textArea.style.padding = 0;
    textArea.style.border = "none";
    textArea.style.outline = "none";
    textArea.style.boxShadow = "none";
    textArea.style.background = "transparent";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Đã sao chép!', 'success');
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }
    
    document.body.removeChild(textArea);
}

// Toast notifications
function showToast(message, type = 'info') {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    const toastElement = $(toastHTML);
    $(toastContainer).append(toastElement);
    
    const toast = new bootstrap.Toast(toastElement[0]);
    toast.show();
    
    // Remove from DOM after hidden
    toastElement[0].addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Format datetime for display
function formatDateTime(dateString, timezone = 'Asia/Ho_Chi_Minh') {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN', {
        timeZone: timezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Auto-detect timezone
function detectTimezone() {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (e) {
        return 'Asia/Ho_Chi_Minh';
    }
}

// Initialize tooltips
$(document).ready(function() {
    // Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-detect timezone on forms
    const timezoneSelect = $('select[name="timezone"]');
    if (timezoneSelect.length && !timezoneSelect.val()) {
        const detectedTz = detectTimezone();
        timezoneSelect.val(detectedTz);
    }
});

// Heatmap interaction
$(document).on('mouseenter', '.heatmap-cell', function() {
    const $cell = $(this);
    const info = $cell.data('info');
    
    if (info) {
        $cell.attr('title', `${info.available}/${info.total} người rảnh (${info.percentage}%)`);
    }
});

// Copy share link
$(document).on('click', '.copy-link-btn', function() {
    const link = $(this).data('link');
    copyToClipboard(link);
});

// Confirm dialogs
$(document).on('click', '[data-confirm]', function(e) {
    const message = $(this).data('confirm');
    if (!confirm(message)) {
        e.preventDefault();
        return false;
    }
});

// Auto-refresh heatmap (for real-time updates)
function refreshHeatmap(requestId, timezone) {
    $.ajax({
        url: `/api/request/${requestId}/heatmap/?timezone=${timezone}`,
        method: 'GET',
        success: function(data) {
            updateHeatmapDisplay(data);
        },
        error: function(xhr, status, error) {
            console.error('Failed to refresh heatmap:', error);
        }
    });
}

function updateHeatmapDisplay(data) {
    // Update heatmap cells with new data
    $('.heatmap-cell').each(function() {
        const $cell = $(this);
        const date = $cell.data('date');
        const time = $cell.data('time');
        
        if (data.heatmap[date] && data.heatmap[date][time]) {
            const cellData = data.heatmap[date][time];
            
            // Update class
            $cell.removeClass(function(index, className) {
                return (className.match(/(^|\s)heatmap-level-\S+/g) || []).join(' ');
            });
            $cell.addClass(`heatmap-level-${cellData.level}`);
            
            // Update text
            $cell.text(`${cellData.available}/${cellData.total}`);
            
            // Update data
            $cell.data('info', cellData);
        }
    });
}

// Load suggestions
function loadSuggestions(requestId, limit = 10, minPct = 50) {
    $.ajax({
        url: `/api/request/${requestId}/suggestions/?limit=${limit}&min_pct=${minPct}`,
        method: 'GET',
        success: function(data) {
            displaySuggestions(data.suggestions);
        },
        error: function(xhr, status, error) {
            console.error('Failed to load suggestions:', error);
        }
    });
}

function displaySuggestions(suggestions) {
    const $container = $('#suggestions-list');
    if (!$container.length) return;
    
    if (suggestions.length === 0) {
        $container.html('<div class="alert alert-info">Chưa có đủ dữ liệu để gợi ý khung giờ</div>');
        return;
    }
    
    let html = '<div class="list-group">';
    suggestions.forEach((suggestion, index) => {
        const badgeClass = suggestion.percentage >= 80 ? 'bg-success' : 
                          suggestion.percentage >= 60 ? 'bg-primary' : 'bg-secondary';
        
        html += `
            <div class="list-group-item suggestion-item ${index === 0 ? 'top-suggestion' : ''}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">
                            ${index === 0 ? '<i class="bi bi-star-fill text-warning"></i> ' : ''}
                            ${formatDateTime(suggestion.start_time)} - ${formatDateTime(suggestion.end_time)}
                        </h6>
                        <small class="text-muted">
                            ${suggestion.available_count} / ${suggestion.total_participants} người rảnh
                        </small>
                    </div>
                    <span class="badge ${badgeClass} availability-badge">
                        ${suggestion.percentage}%
                    </span>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    $container.html(html);
}

// Export to calendar formats
function exportToICS(requestId, slotId) {
    // This would generate and download an ICS file
    window.location.href = `/api/request/${requestId}/slot/${slotId}/export/ics/`;
}

// Console welcome message
console.log('%cTimeWeave', 'font-size: 20px; font-weight: bold; color: #0d6efd;');
console.log('Meeting scheduling made easy!');
