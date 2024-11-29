function getCurrentTableIndex() {
    const path = window.location.pathname;
    const match = path.match(/\/admin\/(\d+)/);
    return match ? parseInt(match[1]) : 0;
}

function selectTable(element) {
    const index = element.dataset.index;
    // Only update URL if it's different from current
    if (index !== getCurrentTableIndex().toString()) {
        window.location.href = `/admin/${index}`;
    }
}

// Set active table based on URL
function setActiveTableFromUrl() {
    const currentIndex = getCurrentTableIndex();
    const tableItems = document.querySelectorAll('.table-item');

    tableItems.forEach(item => {
        item.classList.remove('bg-blue-600');
        item.classList.add('bg-gray-700');

        if (parseInt(item.dataset.index) === currentIndex) {
            item.classList.remove('bg-gray-700');
            item.classList.add('bg-blue-600');
        }
    });
}

// Initialize based on URL
document.addEventListener('DOMContentLoaded', () => {
    setActiveTableFromUrl();
});