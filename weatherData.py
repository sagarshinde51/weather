import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "82.180.143.66",
    "user": "u263681140_students",
    "password": "testStudents@123",
    "database": "u263681140_students"
}

DEFAULT_USER = "admin"
DEFAULT_PASS = "admin123"

# --- FUNCTIONS ---
def get_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT * FROM heart_rate ORDER BY Date_Time DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert numeric columns from string/decimal to float for graphing
        numeric_cols = ['Body_temp', 'Oxygen', 'Heart_Rate', 'Temp', 'Humi']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Date_Time'] = pd.to_datetime(df['Date_Time'])
        return df
    except Exception as e:
        st.error(f"Error connecting to DB: {e}")
        return pd.DataFrame()

# --- LOGIN UI ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("Health & Vitals Login")
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

    st.title("❤️ Heart Rate & Vitals Dashboard")
    
    df = get_data()
    
    if not df.empty:
        tab1, tab2 = st.tabs(["📍 Latest Data", "📊 Trends & History"])

        with tab1:
            st.subheader("Most Recent Reading")
            latest = df.iloc[0]
            
            # Primary vitals metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Heart Rate", f"{latest['Heart_Rate']} BPM")
            col2.metric("Oxygen (SpO2)", f"{latest['Oxygen']}%")
            col3.metric("Body Temp", f"{latest['Body_temp']}°C")

            # Environmental ambient metrics
            col4, col5 = st.columns(2)
            col4.metric("Ambient Temp", f"{latest['Temp']}°C")
            col5.metric("Humidity", f"{latest['Humi']}%")
            
            st.write(f"**Last Updated:** {latest['Date_Time']}")

        with tab2:
            st.subheader("Visual Vitals Trends")
            
            # Prepare data for Plotly (melting for different colors)
            df_melted = df.melt(id_vars=['Date_Time'], 
                                value_vars=['Heart_Rate', 'Oxygen', 'Body_temp', 'Temp', 'Humi'],
                                var_name='Metric', value_name='Value')
            
            fig = px.line(df_melted, x='Date_Time', y='Value', color='Metric',
                          title="All Vitals Parameters Over Time",
                          labels={"Value": "Measurement", "Date_Time": "Time"},
                          template="plotly_dark")
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.subheader("Historical Data Table")
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found in the database.")
