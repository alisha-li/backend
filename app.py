from flask import Flask, jsonify, render_template_string
import requests
import pandas as pd
from plotly_calplot import calplot
import plotly.io as pio

app = Flask(__name__)

@app.route('/anki-stats', methods=['GET'])
def get_anki_stats():
    # Make a request to AnkiConnect to get stats
    response = requests.post('http://localhost:8765', json={
        "action": "deckNames",
        "version": 6
    })
    data = response.json()
    return jsonify(data)

def get_reviews_by_day():
    url = "http://localhost:8765"  # AnkiConnect API endpoint
    payload = {
        "action": "getNumCardsReviewedByDay",
        "version": 6
    }
    response = requests.post(url, json=payload)

    # Handle errors
    if response.json()["error"] != None:
        raise Exception(f"AnkiConnect error: {response.json().get('error')}")

    return response.json()["result"]

def clean_review_data(data):
    """
    Clean up and fix anomalies in the review data.

    Args:
        data (list): List of [date, review_count] pairs.

    Returns:
        list: Cleaned data.
    """
    cleaned_data = []

    for date, count in data:
        # Correct specific known issues
        if date == "2024-10-17" and count > 1000:
            print(f"Fixing data for {date}: Changing {count} to 196")
            count = 196

        cleaned_data.append([date, count])

    return cleaned_data

def process_reviews_by_day(data):
    # Convert list of lists into a DataFrame
    df = pd.DataFrame(data, columns=["date", "value"])

    # Ensure the 'date' column is in datetime format
    df["date"] = pd.to_datetime(df["date"])

    return df

# Flask route to serve review data as JSON
@app.route("/api/review-data")
def review_data():
    data = get_reviews_by_day()
    return jsonify(data)

# Flask route to generate and serve the heatmap
@app.route("/heatmap")
def heatmap():
    raw_data = get_reviews_by_day()  # Fetch data from AnkiConnect
    cleaned_data = clean_review_data(raw_data)  # Clean the data

    # Convert to DataFrame
    df = pd.DataFrame(cleaned_data, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    
    # Updated custom color scale
    anki_blues = [
        [0.0, "rgb(220, 240, 255)"],  # Very light neon blue
        [0.25, "rgb(120, 180, 255)"], # Light neon blue
        [0.5, "rgb(60, 120, 255)"],   # Medium neon blue
        [1.0, "rgb(0, 80, 255)"],     # Dark neon
    ]

    
    # Generate the heatmap
    fig = calplot(df, x="date", y="value", name="Reviews", colorscale=anki_blues, gap=1, years_title=True)
    html = pio.to_html(fig, full_html=False)
    return render_template_string(html)


if __name__ == '__main__':
    app.run(debug=True)