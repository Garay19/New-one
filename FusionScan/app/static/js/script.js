document.addEventListener('DOMContentLoaded', function() {
    // --- Camera Selection ---
    const cameraSelect = document.createElement('select');
    cameraSelect.id = 'cameraSelect';
    document.body.appendChild(cameraSelect); // Or append to a specific container

    navigator.mediaDevices.enumerateDevices()
        .then(function(devices) {
            devices.forEach(function(device) {
                if (device.kind === 'videoinput') {
                    const option = document.createElement('option');
                    option.value = device.deviceId;
                    option.text = device.label || `Camera ${cameraSelect.length + 1}`;
                    cameraSelect.appendChild(option);
                }
            });

            // Handle camera changes
            cameraSelect.addEventListener('change', function() {
                const selectedCameraId = this.value;
                console.log('Selected camera ID:', selectedCameraId);

                // Send the selected camera ID to the Flask backend
                fetch('/update_camera', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ cameraId: selectedCameraId })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    console.log('Camera ID updated on the server');
                    // Reload the video feed or update the stream (implementation depends on your approach)
                    // You might need to stop the current stream and start a new one with the new camera ID
                })
                .catch(error => {
                    console.error('Error updating camera:', error);
                });
            });

        })
        .catch(function(err) {
            console.error('Error accessing media devices.', err);
        });

    // --- Temperature Display ---
    function updateTemperature() {
        fetch('/get_temperature')
            .then(response => response.json())
            .then(data => {
                const temperatureElement = document.getElementById('temperatureDisplay');
                if (temperatureElement) {
                    if (data.error) {
                        temperatureElement.textContent = `Temperature: Error`;
                    } else {
                        temperatureElement.textContent = `Temperature: ${data.temperature}°C`;
                    }
                }
            })
            .catch(error => console.error('Error fetching temperature:', error));
    }

    setInterval(updateTemperature, 1000); // Update every 1 second
});