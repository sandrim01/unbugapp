document.addEventListener('DOMContentLoaded', function() {
    // Header date display
    const headerDateElement = document.getElementById('header-date');
    if (headerDateElement) {
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        const today = new Date();
        headerDateElement.textContent = today.toLocaleDateString('pt-BR', options);
    }

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Theme functionality moved to theme.js
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Sidebar toggler
    const sidebarToggler = document.getElementById('sidebar-toggler');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggler && sidebar) {
        sidebarToggler.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            this.classList.toggle('open');
        });
    }
    
    // Sidebar submenu toggle
    const hasSubmenuItems = document.querySelectorAll('.has-submenu');
    
    hasSubmenuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (e.target === this || e.target.parentElement === this) {
                e.preventDefault();
                this.classList.toggle('open');
                const submenu = this.nextElementSibling;
                if (submenu && submenu.classList.contains('nav-submenu')) {
                    submenu.classList.toggle('show');
                }
            }
        });
    });
    
    // Inicializar submenus abertos por padrão
    document.addEventListener('DOMContentLoaded', function() {
        const activeItems = document.querySelectorAll('.nav-submenu.show');
        activeItems.forEach(submenu => {
            const prevItem = submenu.previousElementSibling;
            if (prevItem && prevItem.classList.contains('has-submenu')) {
                prevItem.classList.add('open');
            }
        });
    });

    // Confirm delete
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este item?')) {
                e.preventDefault();
            }
        });
    });

    // Dynamic form fields
    const typeSelector = document.getElementById('type');
    if (typeSelector) {
        const clientFields = document.getElementById('client-fields');
        const supplierFields = document.getElementById('supplier-fields');

        typeSelector.addEventListener('change', function() {
            if (this.value === 'income') {
                if (clientFields) clientFields.style.display = 'block';
                if (supplierFields) supplierFields.style.display = 'none';
            } else if (this.value === 'expense') {
                if (clientFields) clientFields.style.display = 'none';
                if (supplierFields) supplierFields.style.display = 'block';
            }
        });

        // Trigger change event to set initial state
        if (typeSelector.value) {
            const event = new Event('change');
            typeSelector.dispatchEvent(event);
        }
    }

    // File input display
    const fileInput = document.querySelector('.custom-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0].name;
            const nextSibling = e.target.nextElementSibling;
            nextSibling.innerText = fileName;
        });
    }

    // Dynamic select field population based on another field
    const projectSelect = document.getElementById('project_id');
    const serviceOrderSelect = document.getElementById('service_order_id');
    
    if (projectSelect && serviceOrderSelect) {
        const fetchRelatedData = async (projectId) => {
            if (!projectId) return;
            
            try {
                const response = await fetch(`/orders/by-project/${projectId}`);
                const data = await response.json();
                
                // Clear the service order select
                serviceOrderSelect.innerHTML = '<option value="">Selecione</option>';
                
                // Add new options
                data.forEach(order => {
                    const option = document.createElement('option');
                    option.value = order.id;
                    option.textContent = `#${order.id} - ${order.title}`;
                    serviceOrderSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error fetching service orders:', error);
            }
        };
        
        projectSelect.addEventListener('change', function() {
            fetchRelatedData(this.value);
        });
        
        // Trigger change event to set initial state if value exists
        if (projectSelect.value) {
            const event = new Event('change');
            projectSelect.dispatchEvent(event);
        }
    }

    // Quantity validation for inventory items
    const quantityInput = document.getElementById('quantity');
    const inventoryItemSelect = document.getElementById('inventory_item_id');
    const addItemForm = document.getElementById('add-item-form');
    
    if (quantityInput && inventoryItemSelect && addItemForm) {
        addItemForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const itemId = inventoryItemSelect.value;
            const quantity = parseInt(quantityInput.value);
            
            if (!itemId || !quantity) return;
            
            try {
                const response = await fetch(`/inventory/check-stock/${itemId}`);
                const data = await response.json();
                
                if (quantity > data.available) {
                    alert(`Estoque insuficiente. Disponível: ${data.available}`);
                    return;
                }
                
                // If validation passes, submit the form
                this.submit();
            } catch (error) {
                console.error('Error checking inventory:', error);
            }
        });
    }
    
    // Date range validation
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        endDateInput.addEventListener('change', function() {
            const startDate = new Date(startDateInput.value);
            const endDate = new Date(this.value);
            
            if (endDate < startDate) {
                alert('A data de conclusão não pode ser anterior à data de início.');
                this.value = '';
            }
        });
    }
});