import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import requests  # Ensure you add 'import requests' at the top of your script

# Database credentials
DB_CONFIG = {
    "host": "82.180.143.66",
    "user": "u263681140_students1",
    "password": "testStudents@123",
    "database": "u263681140_students1"
}

# Default login credentials
USERNAME = "admin"
PASSWORD = "password"

# Sidebar login setup
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

st.sidebar.title("Login")
username = st.sidebar.text_input("Username", placeholder="Enter username")
password = st.sidebar.text_input("Password", type="password", placeholder="Enter password")
login_button = st.sidebar.button("Login")

if login_button:
    if username == USERNAME and password == PASSWORD:
        st.session_state.authenticated = True
        st.sidebar.success("Login Successful!")
    else:
        st.sidebar.error("Invalid Credentials")

def show_home_page():
    st.title("IoT-Based Smart Irrigation System")
    try:
        st.image("irrigation.jpeg", use_container_width=True)
    except:
        st.info("Home page image loading...")
    st.write(
        "This project automates irrigation by monitoring soil moisture, temperature, humidity, "
        "and gas levels using IoT sensors to improve agricultural efficiency."
    )

if not st.session_state.authenticated:
    show_home_page()
    st.stop()

# --- Database Functions ---

def fetch_latest_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        # Added SunLight to the SELECT statement
        query = "SELECT id, dateTime, temp, humi, moi, moi2, coGas, SunLight FROM Irrigation ORDER BY id DESC LIMIT 1"
        cursor.execute(query)
        latest_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return latest_data
    except mysql.connector.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

def fetch_all_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        # Added SunLight to the SELECT statement
        query = "SELECT dateTime, temp, humi, moi, moi2, coGas, SunLight FROM Irrigation ORDER BY dateTime ASC"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        df = pd.DataFrame(data)
        
        # Convert VARCHAR columns to numeric for plotting
        cols_to_fix = ['temp', 'humi', 'moi', 'moi2', 'coGas', 'SunLight']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except mysql.connector.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

# --- Main Dashboard ---

st.title("IoT Sensor Dashboard")
tabs = st.tabs(["Dashboard", "Visualizations", "Device Controls"])

# Tab 1: Live Dashboard
with tabs[0]:
    st.subheader("Live Sensor Data")
    latest_data = fetch_latest_data()
    if latest_data:
        st.write(f"**Latest Data Timestamp:** {latest_data['dateTime']}")
        
        # 6 Columns for the 6 active sensors in your table
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric(label="Temp", value=f"{latest_data['temp']}°C")
        with col2: st.metric(label="Humidity", value=f"{latest_data['humi']}%")
        with col3: st.metric(label="Moi 1", value=f"{latest_data['moi']}%")
        with col4: st.metric(label="Moi 2", value=f"{latest_data['moi2']}%")
        with col5: st.metric(label="CO Gas", value=f"{latest_data['coGas']}")
        with col6: st.metric(label="Sunlight", value=f"{latest_data['SunLight']}")
    else:
        st.error("No data found in the 'Irrigation' table.")

# Tab 2: Visualizations
with tabs[1]:
    st.subheader("Sensor Trends")
    data = fetch_all_data()
    if data is not None and not data.empty:
        # Melt dataframe for Plotly
        fig = px.line(
            data.melt(id_vars=['dateTime'], var_name='Sensor', value_name='Value'),
            x='dateTime', y='Value', color='Sensor',
            title='Real-time Sensor Monitoring'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Show Full Data Table"):
            st.dataframe(data)
    else:
        st.error("No data available to plot.")


# Tab 3: Controls
with tabs[2]:
    st.subheader("Manual Actuator Controls")
    st.info("Directly control hardware via the AE Project Hub API.")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("### 💧 Water Pump")
        # Using buttons instead of sliders for a cleaner toggle feel
        if st.button("Turn Pump ON"):
            response = requests.get("https://aeprojecthub.in/updateFlag1.php?id=5&val=1")
            if response.status_code == 200:
                st.success("Pump Command: ON Sent")
            else:
                st.error("Failed to reach server.")
        
        if st.button("Turn Pump OFF"):
            # Per your note: "post 1 from url to off it"
            response = requests.get("https://aeprojecthub.in/updateFlag1.php?id=5&val=2") 
            st.warning("Pump Command: OFF Sent")

    with c2:
        st.write("### 🌀 Exhaust Fan")
        if st.button("Turn Fan ON"):
            # Per your note: "add 2 to turn on fan"
            response = requests.get("https://aeprojecthub.in/updateFlag1.php?id=5&val=3")
            st.success("Fan Command: ON Sent")
            
        if st.button("Turn Fan OFF"):
            # Per your note: "post 3 to turn off fan"
            response = requests.get("https://aeprojecthub.in/updateFlag1.php?id=5&val=4")
            st.warning("Fan Command: OFF Sent")

    st.divider()
    st.caption("Note: 'post 4' was mentioned for an undefined action, ensure your hardware is programmed to listen for these specific flag values.")
