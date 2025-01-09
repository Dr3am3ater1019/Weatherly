from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Weather API Key
API_KEY = "b7d988d3551b84d6ff7410d1df0fccea"

# LiiNK Guidelines (temperature thresholds in Fahrenheit)
LiiNK_GUIDELINES = {
    "too_cold": 32,  # Below 32°F
    "too_hot": 95,   # Above 95°F
    "safe_min": 32,  # Minimum safe temperature
    "safe_max": 95   # Maximum safe temperature
}

HEALTH_CONCERN_COLORS = {
    'comfortable': 'green',
    'caution': 'yellow',
    'danger': 'red',
    'no_play': 'purple'
}

# Landing page route
@app.route("/", methods=["GET"])
def landing():
    return render_template("landing.html")  # Serve the landing animation page

# Main weather page route
@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")  # Serve the main weather page

# Fetch weather data by user-provided location
@app.route("/weather", methods=["GET"])
def weather():
    location = request.args.get("location")
    city, state, country = parse_location(location)

    weather_data = get_weather_data(city, state, country)
    if weather_data:
        return jsonify(format_weather_data(weather_data))
    else:
        return jsonify({"error": "Location not found or API error"}), 404

# Fetch weather data by geographic coordinates
@app.route("/weather_by_coords", methods=["GET"])
def weather_by_coords():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if lat and lon:
        api_url_weather = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=imperial"
        try:
            response_weather = requests.get(api_url_weather)
            if response_weather.status_code == 200:
                weather_data = response_weather.json()
                
                # Fetch AQI data
                api_url_aqi = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
                response_aqi = requests.get(api_url_aqi)
                if response_aqi.status_code == 200:
                    aqi_data = response_aqi.json()
                    aqi = aqi_data['list'][0]['main']['aqi']
                    weather_data['air_quality'] = aqi
                    return jsonify(format_weather_data(weather_data))
            return jsonify({"error": "Weather data not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid coordinates"}), 400

# Helper function to parse location
def parse_location(location):
    """Parse location into city, state, and country."""
    parts = location.split(",")
    city = parts[0].strip() if len(parts) > 0 else ""
    state = parts[1].strip() if len(parts) > 1 else ""
    country = parts[2].strip() if len(parts) > 2 else "US"
    return city, state, country

# Helper function to get weather data
def get_weather_data(city, state=None, country='US'):
    location = f"{city},{state if state else ''},{country}".strip(',')
    api_url_weather = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=imperial"

    try:
        response_weather = requests.get(api_url_weather)
        if response_weather.status_code == 200:
            weather_data = response_weather.json()
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']

            # Fetch AQI data
            api_url_aqi = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
            response_aqi = requests.get(api_url_aqi)
            if response_aqi.status_code == 200:
                aqi_data = response_aqi.json()
                aqi = aqi_data['list'][0]['main']['aqi']
                weather_data['air_quality'] = aqi
                return weather_data
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Error fetching weather data or AQI: {e}")
        return None

# Format weather data for response
def format_weather_data(weather_data):
    """Format weather data for response."""
    temp = weather_data["main"]["temp"]
    wind_speed = weather_data["wind"]["speed"]
    aqi = weather_data.get("air_quality", 50)  # Default AQI to 50 if not available
    recommendation = analyze_weather(temp, wind_speed, aqi)

    return {
        "location": f"{weather_data['name']}, {weather_data['sys']['country']}",
        "temperature": temp,
        "condition": weather_data["weather"][0]["description"],
        "humidity": weather_data["main"]["humidity"],
        "wind_speed": wind_speed,
        "recommendation": recommendation
    }

# Comprehensive weather analysis
def analyze_weather(temp, wind_speed, aqi):
    """Analyze weather conditions using multiple factors (temperature, wind speed, AQI)."""
    heat_color, heat_message = heat_analysis(temp)
    cold_color, cold_message = cold_weather_analysis(temp)
    aqi_color, aqi_message = aqi_analysis(aqi)

    # Combine results to create a comprehensive weather analysis
    if heat_color == 'danger' or cold_color == 'danger' or aqi_color == 'danger':
        return "Danger! Outdoor play should be avoided."
    elif heat_color == 'caution' or cold_color == 'caution' or aqi_color == 'caution':
        return "Caution! Limit outdoor play to 20 minutes or less."
    else:
        return "Comfortable! Outdoor play is safe for more than 20 minutes."

# Heat analysis
def heat_analysis(air_temp):
    if air_temp >= 80:
        if air_temp < 90:
            return 'caution', "Caution for play (≤20 minutes)"
        elif air_temp >= 90 and air_temp <= 105:
            return 'danger', "Danger – Limit play (<20 minutes)"
        else:
            return 'danger', "Danger – No outdoor play"
    else:
        return 'comfortable', "Comfortable play (>20 minutes)"

# Cold weather analysis
def cold_weather_analysis(air_temp):
    if air_temp < 0:  # Below 0°F
        return 'no_play', "Extreme caution – No play (below 0°F)"
    elif 0 <= air_temp <= 13:
        return 'no_play', "Danger – No play"
    elif 13 < air_temp <= 32:
        return 'caution', "Caution for play (≤20 minutes)"
    else:
        return 'comfortable', "Comfortable play (>20 minutes)"

# AQI analysis
def aqi_analysis(aqi):
    if aqi <= 50:
        return 'comfortable', "Good air quality – Play without restrictions"
    elif 51 <= aqi <= 100:
        return 'caution', "Moderate air quality – Play with caution (≤20 minutes)"
    elif 101 <= aqi <= 150:
        return 'danger', "Unhealthy for sensitive groups – Limit play (<20 minutes)"
    else:
        return 'danger', "Unhealthy air quality – No outdoor play"

if __name__ == "__main__":
    app.run(debug=True)
