import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "82.180.143.66",
    "user": "u263681140_students1",
    "password": "testStudents@123",
    "database": "u263681140_students1"
}

DEFAULT_USER = "admin"
DEFAULT_PASS = "admin123"

# --- FUNCTIONS ---
def get_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT * FROM WeatherForcast ORDER BY DateTime DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert numeric columns from string to float for graphing
        numeric_cols = ['Temp', 'Humi', 'Rain', 'Moisture', 'WindSpeed']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        return df
    except Exception as e:
        st.error(f"Error connecting to DB: {e}")
        return pd.DataFrame()

# --- LOGIN UI ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("Weather Station Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == DEFAULT_USER and pwd == DEFAULT_PASS:
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Invalid Username or Password")
else:
    # --- MAIN APP ---
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("🌤️ Weather Forecast Dashboard")
    
    df = get_data()
    
    if not df.empty:
        tab1, tab2 = st.tabs(["📍 Latest Data", "📊 Trends & History"])

        with tab1:
            st.subheader("Most Recent Reading")
            latest = df.iloc[0]
            
            # Displaying key metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Temperature", f"{latest['Temp']}°C")
            col2.metric("Humidity", f"{latest['Humi']}%")
            col3.metric("Rainfall", f"{latest['Rain']}mm")
            col4.metric("Moisture", f"{latest['Moisture']}%")
            
            st.write(f"**Last Updated:** {latest['DateTime']}")
            st.write(f"**Wind:** {latest['WindSpeed']} m/h ({latest['WindDirection']})")
            st.write(f"**Sunlight:** {latest['SunLigh']}")

        with tab2:
            st.subheader("Visual Weather Trends")
            
            # Prepare data for Plotly (melting for different colors)
            df_melted = df.melt(id_vars=['DateTime'], 
                                value_vars=['Temp', 'Humi', 'Rain', 'Moisture', 'WindSpeed'],
                                var_name='Metric', value_name='Value')
            
            fig = px.line(df_melted, x='DateTime', y='Value', color='Metric',
                          title="All Weather Parameters Over Time",
                          labels={"Value": "Measurement", "DateTime": "Time"},
                          template="plotly_dark")
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.subheader("Historical Data Table")
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found in the database.")
