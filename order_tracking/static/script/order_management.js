function changeOrder(button) {
    // Logic to change the order status
    const row = button.parentElement.parentElement; 
    const statusSelect = row.querySelector('select'); 
    const selectedStatus = statusSelect.value; 
    alert('Order status changed to: ' + selectedStatus);

}

function deleteOrder(button, orderId) {
    // Find the row that contains the delete button
    var row = button.closest('tr');
   
    // Optionally, add a confirmation step before deleting
    if (confirm("Are you sure you want to remove this order from the view?")) 
        // Temporarily remove the row from the table (without removing from the database)
        row.style.display = 'none';

        // Send an AJAX request to mark the order as removed in the database
        fetch(`/remove_order/${orderId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Order marked as removed.");
            } else {
                alert("Failed to mark order as removed.");
            }
        })
        .catch(error => console.error('Error:', error));
    }

function deleteOrder(orderId) {
    if (confirm('Are you sure you want to delete this order?')) {
        fetch('/delete_order/' + orderId, {
            method: 'DELETE'
        }).then(response => {
            if (response.ok) {
                document.getElementById("order_" + orderId).remove(); 
            } else {
                alert('Failed to delete order.');
            }
        });
    }
}

function showEditDialog(orderId) {
    const row = document.getElementById(`order_${orderId}`);
    
    // Set hidden orderId value
    document.getElementById("orderId").value = orderId;
    
    // Populate the text fields
    document.getElementById("customerName").value = row.cells[0].innerText;
    document.getElementById("contactNumber").value = row.cells[1].innerText;
    document.getElementById("address").value = row.cells[2].innerText;
    document.getElementById("pickupPlace").value = row.cells[3].innerText;
    document.getElementById("pickupDate").value = row.cells[4].innerText;
    document.getElementById("delicacy").value = row.cells[5].innerText;
    document.getElementById("quantity").value = row.cells[6].innerText;
    document.getElementById("container").value = row.cells[7].innerText;
    document.getElementById("specialRequest").value = row.cells[8].innerText;

    const status = row.cells[9].innerText.trim(); 
    
    const statusValue = status.split('.')[1]; 

    const statusDropdown = document.getElementById("status");
   
    // Set the selected option based on the extracted status
    Array.from(statusDropdown.options).forEach(option => {
        if (option.value === statusValue) {
            option.selected = true; // Set the matching option as selected
        }
    });

    // Attach the orderId to the save button
    document.getElementById("saveButton").setAttribute("data-order-id", orderId);
    
    // Display the modal
    document.getElementById("editModal").style.display = "block";
    document.getElementById("modalOverlay").style.display = "block";
}


function closeModal() {
    document.getElementById("editModal").style.display = "none";
    document.getElementById("modalOverlay").style.display = "none";
}

function saveOrder() {
    const orderId = document.getElementById("saveButton").getAttribute("data-order-id");
    console.log("Save button clicked! Order ID: " + orderId);

    let formData = {
        customer_name: document.getElementById("customerName").value,
        contact_number: document.getElementById("contactNumber").value,
        address: document.getElementById("address").value,
        pickup_place: document.getElementById("pickupPlace").value,
        pickup_date: document.getElementById("pickupDate").value,
        delicacy: document.getElementById("delicacy").value,
        quantity: document.getElementById("quantity").value,
        container: document.getElementById("container").value,
        special_request: document.getElementById("specialRequest").value,
        status: document.getElementById("status").value,
    };

    fetch('/update_order/' + orderId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    })
    
    .then(response => {
        console.log('Response:', response);
        return response.json();
    })
    .then(data => {
        console.log('Data received from server:', data);
        if (data.success) {
            closeModal()
            handleSortChange()
        } else {
            alert('Failed to update order.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the order.');
    });
}

function updateUI(orderId, updatedOrder) {
    console.log(updatedOrder); // Log the updatedOrder data to ensure it's correct

    const updateTextContent = (elementId, newText) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerText = newText;
        } else {
            console.warn(`Element with ID ${elementId} not found`);
        }
    };

    updateTextContent("customer_name_" + orderId, updatedOrder.customer_name);
    updateTextContent("contact_number_" + orderId, updatedOrder.contact_number);
    updateTextContent("address_" + orderId, updatedOrder.address);
    updateTextContent("pickup_place_" + orderId, updatedOrder.pickup_place);
    updateTextContent("pickup_date_" + orderId, updatedOrder.pickup_date);
    updateTextContent("delicacy_" + orderId, updatedOrder.delicacy);
    updateTextContent("quantity_" + orderId, updatedOrder.quantity);
    updateTextContent("container_" + orderId, updatedOrder.container);
    updateTextContent("special_request_" + orderId, updatedOrder.special_request);
    updateTextContent("status_" + orderId, updatedOrder.status);
}

document.addEventListener("DOMContentLoaded", () => {
    // Define the mapping of statuses to their user-friendly names
    const statusMap = {
        "OrderStatus.PENDING": "Pending",
        "OrderStatus.IN_PROGRESS": "In Progress",
        "OrderStatus.COMPLETED": "Completed",
        "OrderStatus.REMOVED": "Removed",
    };

    // Select all rows in the table body
    const rows = document.querySelectorAll("#ordersTable tbody tr");

    // Loop through each row to update the status text
    rows.forEach(row => {
        const statusCell = row.cells[9]; 
        const currentStatus = statusCell.innerText.trim();
        // Replace the status if it exists in the mapping
        if (statusMap[currentStatus]) {
            statusCell.innerText = statusMap[currentStatus];
        }
    });


    function filterOrders() {
        const searchValue = document.getElementById('searchBar').value.toLowerCase();
        const rows = document.querySelectorAll("#ordersTable tbody tr");
        let resultsFound = false;
    
        rows.forEach(row => {
            const customerNameCell = row.cells[0];  // Assuming customer name is in the first column
            const statusCell = row.cells[9];        // Assuming order status is in the last column
    
            // Get text content of customer name and status
            const customerName = customerNameCell.innerText.toLowerCase();
            const status = statusCell.innerText.toLowerCase();
    
            // Check if the customer name or status contains the search value
            if (customerName.includes(searchValue) || status.includes(searchValue)) {
                row.style.display = '';  // Show the row
                resultsFound = true;
            } else {
                row.style.display = 'none';  // Hide the row
            }
        });
    
        // Show a message if no results are found
        const noResultsMessage = document.getElementById('noResultsMessage');
        if (!resultsFound) {
            noResultsMessage.style.display = 'block'; // Show "no results" message
        } else {
            noResultsMessage.style.display = 'none'; // Hide the message if results are found
        }
    }
    
    // Add event listener to the search bar to trigger the filter function
    document.getElementById('searchBar').addEventListener('input', filterOrders);    

    // Modal elements
    const placeOrderBtn = document.getElementById('placeOrderBtn');
    const modalOverlay = document.getElementById('orderModalOverlay');
    const placeOrderModal = document.getElementById('placeOrderModal');
   

    // Open modal when the FAB button is clicked
    if (placeOrderBtn) {
        placeOrderBtn.addEventListener('click', () => {
            modalOverlay.style.display = 'block';
            placeOrderModal.style.display = 'block';
        });
    }
});


function showOrderModal() {
    document.getElementById("orderModalOverlay").style.display = "block";
    document.getElementById("placeOrderModal").style.display = "block";
}

function closeOrderModal() {
    document.getElementById("orderModalOverlay").style.display = "none";
    document.getElementById("placeOrderModal").style.display = "none";
}

function createOrder() {
    const form = document.getElementById("placeOrderForm");

    // Retrieve form inputs
    const customerName = form[0].value.trim();
    const contactNumber = form[1].value.trim();
    const address = form[2].value.trim();
    const pickupPlace = form[3].value.trim();
    const pickupDate = form[4].value;
    const delicacy = form[5].value;
    const quantity = form[6].value.trim();
    const container = form[7].value;
    const specialRequest = form[8].value.trim();

    // Basic validation
    if (!customerName || !contactNumber || !address || !pickupPlace || !pickupDate || !delicacy || !quantity || !container) {
        alert("Please fill in all required fields.");
        return;
    }

    if (!/^\d{11,15}$/.test(contactNumber)) {
        alert("Please enter a valid contact number (11-15 digits).");
        return;
    }

    if (new Date(pickupDate) < new Date()) {
        alert("Pickup date cannot be in the past.");
        return;
    }

    // Prepare data object
    const orderData = {
        customerName: customerName,
        contactNumber: contactNumber,
        address: address,
        pickupPlace: pickupPlace,
        pickupDate: pickupDate,
        delicacy: delicacy,
        quantity: parseInt(quantity, 10),
        container: container,
        specialRequest: specialRequest || "",
    };

    // Send data to backend
    fetch("/order_form", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderData),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                handleSortChange()
                closeOrderModal();
                form.reset();
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch((error) => {
            console.error("Fetch error:", error);
            alert("An error occurred while creating the order.");
        });
}
