import streamlit as st
import requests
import pandas as pd
from geopy.distance import geodesic
import matplotlib.pyplot as plt

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="Smart Tourist & Service Analytics", layout="wide")

st.title("🌍 Smart Tourist Planning & Location-Based Service Analytics System")

st.markdown("""
This system helps **tourists plan visits intelligently**
and provides **analytics on service availability** using open-source map data.
""")

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["🧳 Tourist Planner", "📊 Service Analytics"])

# ---------------- COMMON FUNCTIONS ----------------
HEADERS = {"User-Agent": "StudentProject/1.0"}

def get_coordinates(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    res = requests.get(url, params=params, headers=HEADERS, timeout=10)
    data = res.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])

def get_nearby(lat, lon, key, value, radius=3000):
    query = f"""
    [out:json];
    node(around:{radius},{lat},{lon})["{key}"="{value}"];
    out;
    """

    try:
        res = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            headers=HEADERS,
            timeout=30
        )

        # Step 1: check HTTP status
        if res.status_code != 200:
            return []

        # Step 2: check empty response
        if res.text.strip() == "":
            return []

        # Step 3: parse JSON safely
        data = res.json()
        return data.get("elements", [])

    except Exception:
        # Any error → return empty list instead of crashing
        return []


tab1, tab2 = st.tabs(["🧳 Tourist Planner", "📊 Service Analytics"])

with tab1:
    st.header("🧳 Smart Tourist Planner")

    location = st.text_input("Enter tourist location", "Tirupati")
    time_option = st.selectbox("Available time", ["Half Day", "One Day"])

    if st.button("Generate Travel Plan"):
        coords = get_coordinates(location)

        if not coords:
            st.error("Location not found")
        else:
            lat, lon = coords
            attractions = get_nearby(lat, lon, "tourism", "attraction")

            if not attractions:
                st.warning("No attractions found")
            else:
                plan = []

                for place in attractions[:8]:
                    name = place.get("tags", {}).get("name", "Unnamed Place")
                    p_lat = place["lat"]
                    p_lon = place["lon"]
                    dist = round(geodesic((lat, lon), (p_lat, p_lon)).km, 2)

                    plan.append({
                        "Place": name,
                        "Distance (km)": dist
                    })

                df = pd.DataFrame(plan).sort_values("Distance (km)")

                st.subheader("📍 Suggested Visit Order (Nearest First)")
                st.table(df.head(4 if time_option == "Half Day" else 6))

                st.success("Travel plan generated successfully")

with tab2:
    st.header("📊 Location-Based Service Analytics")

    location = st.text_input(
        "Enter location for analysis",
        "Tirupati",
        key="analytics_location"
    )

    if st.button("Analyze Services"):
        coords = get_coordinates(location)

        if not coords:
            st.error("Location not found")
        else:
            lat, lon = coords

            st.info("Analyzing service availability...")

            # Fetch different services
            hospitals = get_nearby(lat, lon, "amenity", "hospital")
            hotels = get_nearby(lat, lon, "tourism", "hotel")
            restaurants = get_nearby(lat, lon, "amenity", "restaurant")
            fuel = get_nearby(lat, lon, "amenity", "fuel")

            # Create analytics data
            data = {
                "Service": [
                    "Hospitals",
                    "Hotels",
                    "Restaurants",
                    "Petrol Bunks"
                ],
                "Count": [
                    len(hospitals),
                    len(hotels),
                    len(restaurants),
                    len(fuel)
                ]
            }

            df = pd.DataFrame(data)

            # Show table
            st.subheader("Service Availability Summary")
            st.table(df)

            # Plot bar chart
            st.subheader("Service Distribution Chart")

            fig, ax = plt.subplots()
            ax.bar(df["Service"], df["Count"])
            ax.set_ylabel("Number of Services")
            ax.set_title("Nearby Service Availability")

            st.pyplot(fig)

            # Insight generation (THIS IS IMPORTANT)
            st.subheader("📌 Key Insights")

            if len(hospitals) < 3:
                st.warning("⚠️ Low hospital availability in this area")
            else:
                st.success("✅ Adequate hospital coverage")

            if len(hotels) > len(hospitals):
                st.info("🏨 Tourist-oriented area with more hotels")

            st.success("Service analytics completed")
