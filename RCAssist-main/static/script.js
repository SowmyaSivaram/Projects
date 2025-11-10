document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const csvFileInput = document.getElementById('csv-file');
    const uploadStatus = document.getElementById('upload-status');
    const startStreamBtn = document.getElementById('start-stream-btn');
    const stopStreamBtn = document.getElementById('stop-stream-btn');
    const logStream = document.getElementById('log-stream');
    let socket;
    let tableBody;

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = csvFileInput.files[0];
        if (!file) {
            uploadStatus.textContent = 'Please select a file.';
            return;
        }
        const formData = new FormData();
        formData.append('file', file);
        uploadStatus.textContent = 'Uploading and processing...';
        try {
            const response = await fetch('/classify_csv/', {
                method: 'POST',
                body: formData,
            });
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'result.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                uploadStatus.textContent = 'Processing complete. Your file has been downloaded.';
            } else {
                uploadStatus.textContent = 'Error processing file.';
            }
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.textContent = 'An error occurred.';
        }
    });

    startStreamBtn.addEventListener('click', () => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);

        // Clear previous content and create table structure
        logStream.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'log-table'; // For styling if needed
        const thead = table.createTHead();
        const headerRow = thead.insertRow();
        const headers = ["Log Message", "Error Type", "Severity", "Suggested Root Cause", "Suggested Action"];
        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        tableBody = table.createTBody();
        logStream.appendChild(table);


        startStreamBtn.style.display = 'none';
        stopStreamBtn.style.display = 'inline-block';

        socket.onopen = () => {
            const newRow = tableBody.insertRow();
            const cell = newRow.insertCell();
            cell.colSpan = 5;
            cell.textContent = 'Connection established. Starting simulation...';
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === 'complete') {
                const newRow = tableBody.insertRow();
                const cell = newRow.insertCell();
                cell.colSpan = 5;
                cell.innerHTML = '<b>Simulation Complete.</b>';
                socket.close();
                return;
            }
            const newRow = tableBody.insertRow();
            newRow.insertCell(0).textContent = data.log_message || "N/A";
            newRow.insertCell(1).textContent = data.analysis?.error_type || "N/A";
            newRow.insertCell(2).textContent = data.analysis?.severity || "N/A";
            newRow.insertCell(3).textContent = data.analysis?.suggested_root_cause || "N/A";
            newRow.insertCell(4).textContent = data.analysis?.suggested_action || "N/A";
            logStream.scrollTop = logStream.scrollHeight;
        };

        socket.onclose = () => {
            const newRow = tableBody.insertRow();
            const cell = newRow.insertCell();
            cell.colSpan = 5;
            cell.textContent = 'Connection closed.';
            startStreamBtn.style.display = 'inline-block';
            stopStreamBtn.style.display = 'none';
        };

        socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            const newRow = tableBody.insertRow();
            const cell = newRow.insertCell();
            cell.colSpan = 5;
            cell.textContent = 'An error occurred with the connection.';
        };
    });

    stopStreamBtn.addEventListener('click', () => {
        if (socket) {
            socket.close();
        }
    });
});