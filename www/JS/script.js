document.addEventListener("DOMContentLoaded", () => {
    const locationInput = document.getElementById("location");

    // Initialize Google Places Autocomplete for the location field
    const locationAutocomplete = new google.maps.places.Autocomplete(locationInput);

    locationAutocomplete.addListener("place_changed", () => {
        const place = locationAutocomplete.getPlace();
        if (!place.geometry) {
            console.error("No details available for the selected location.");
        }
    });

    // Handle form submission
    document.getElementById("weather-form").addEventListener("submit", async function (event) {
        event.preventDefault();

        const location = locationInput.value;

        try {
            const response = await fetch(`/weather?location=${encodeURIComponent(location)}`);
            const data = await response.json();

            if (response.ok) {
                displayWeather(data);
            } else {
                displayError(data.error);
            }
        } catch (error) {
            displayError("Network error occurred.");
        }
    });

    // Fetch weather using geolocation
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;

                try {
                    // Send latitude and longitude to the backend
                    const response = await fetch(`/weather_by_coords?lat=${latitude}&lon=${longitude}`);
                    const data = await response.json();

                    if (response.ok) {
                        displayWeather(data);
                    } else {
                        displayError(data.error);
                    }
                } catch (error) {
                    displayError("Failed to fetch weather for your current location.");
                }
            },
            (error) => {
                console.error("Error obtaining location:", error.message);
            }
        );
    } else {
        console.error("Geolocation is not supported by this browser.");
    }

    // Function to display weather data
    function displayWeather(data) {
        document.getElementById("weather-result").innerHTML = `
            <div class="weather-info">
                <h2>Weather in ${data.location}</h2>
                <p>Temperature: ${data.temperature} °F</p>
                <p>Condition: ${data.condition}</p>
                <p>Humidity: ${data.humidity}%</p>
                <p>Wind Speed: ${data.wind_speed} mph</p>
                <p><strong>${data.recommendation}</strong></p>
            </div>
        `;
    }

    // Function to display error messages
    function displayError(message) {
        document.getElementById("weather-result").innerHTML = `<p class="error">${message}</p>`;
    }

    // Check if the page has already been redirected to index page
    if (!sessionStorage.getItem('landingPageShown') && !sessionStorage.getItem('indexPageLoaded')) {
        // First time visit, show the landing page and then redirect to index
        sessionStorage.setItem('landingPageShown', 'true');
        window.location.replace("/"); // Redirect to the landing page
    } else if (sessionStorage.getItem('landingPageShown') && !sessionStorage.getItem('indexPageLoaded')) {
        // After landing page is shown, redirect to index page
        sessionStorage.setItem('indexPageLoaded', 'true');
        window.location.replace("/index"); // Go to the index page directly
    }

    // Event listener for beforeunload to reset sessionStorage flags on page unload
    window.addEventListener("beforeunload", () => {
        sessionStorage.removeItem('landingPageShown');
        sessionStorage.removeItem('indexPageLoaded');
    });
});
