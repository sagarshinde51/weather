import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier
import numpy as np

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
        
        # Convert numeric columns from string/decimal to float
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
        tab1, tab2, tab3 = st.tabs(["📍 Latest Data", "📊 Trends & History", "🤖 Attack Prediction"])

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
            
            # Prepare data for Plotly
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

        with tab3:
            st.subheader("Seasonal Cardiac Attack Risk Prediction")
            st.write("Predict potential cardiac risk based on patient vitals and seasonal ambient conditions.")
            
            features = ['Heart_Rate', 'Oxygen', 'Body_temp', 'Temp', 'Humi', 'Month']
            
            # Data preprocessing for training
            clean_df = df.dropna(subset=['Heart_Rate', 'Oxygen', 'Body_temp', 'Temp', 'Humi']).copy()
            clean_df['Month'] = clean_df['Date_Time'].dt.month
            
            if len(clean_df) < 5:
                st.warning("Insufficient data in the database to train the model. At least 5 readings are required.")
            else:
                # Synthetic risk labeling based on medical & seasonal stress risk indicators
                # Extreme cold/heat combined with abnormal vitals elevates risk
                is_winter = clean_df['Month'].isin([11, 12, 1, 2])
                extreme_temp = (clean_df['Temp'] < 15) | (clean_df['Temp'] > 38)
                abnormal_hr = (clean_df['Heart_Rate'] > 100) | (clean_df['Heart_Rate'] < 50)
                low_oxygen = clean_df['Oxygen'] < 92
                
                clean_df['Risk'] = np.where(
                    (low_oxygen & abnormal_hr) | (is_winter & extreme_temp & abnormal_hr), 
                    1, 
                    0
                )
                
                # Train Random Forest Classifier
                X = clean_df[features]
                y = clean_df['Risk']
                
                # Check if both classes exist, otherwise add synthetic balanced samples for fitting
                if len(np.unique(y)) < 2:
                    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
                    dummy_X = pd.DataFrame([
                        {'Heart_Rate': 120, 'Oxygen': 88, 'Body_temp': 38.5, 'Temp': 10, 'Humi': 85, 'Month': 1},
                        {'Heart_Rate': 72, 'Oxygen': 98, 'Body_temp': 36.6, 'Temp': 24, 'Humi': 50, 'Month': 4}
                    ])
                    dummy_y = [1, 0]
                    rf_model.fit(pd.concat([X, dummy_X]), pd.concat([y, pd.Series(dummy_y)]))
                else:
                    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
                    rf_model.fit(X, y)

                # Prediction UI
                latest_record = clean_df.iloc[0]
                st.markdown("**Latest Parameters Used for Prediction:**")
                st.write(f"- **Heart Rate:** {latest_record['Heart_Rate']} BPM | **SpO2:** {latest_record['Oxygen']}% | **Body Temp:** {latest_record['Body_temp']}°C")
                st.write(f"- **Ambient Temp:** {latest_record['Temp']}°C | **Humidity:** {latest_record['Humi']}% | **Month:** {int(latest_record['Month'])}")
                
                if st.button("Predict Cardiac Risk", type="primary"):
                    input_data = pd.DataFrame([[
                        latest_record['Heart_Rate'],
                        latest_record['Oxygen'],
                        latest_record['Body_temp'],
                        latest_record['Temp'],
                        latest_record['Humi'],
                        latest_record['Month']
                    ]], columns=features)
                    
                    prediction = rf_model.predict(input_data)[0]
                    prediction_prob = rf_model.predict_proba(input_data)[0][1] * 100
                    
                    st.divider()
                    if prediction == 1:
                        st.error(f"⚠️ **High Seasonal Cardiac Risk Detected!** (Risk Probability: {prediction_prob:.2f}%)")
                        st.warning("Recommendation: Immediate medical evaluation is advised due to adverse seasonal vitals stress.")
                    else:
                        st.success(f"✅ **Low Cardiac Risk** (Risk Probability: {prediction_prob:.2f}%)")
                        st.info("Vitals and seasonal weather conditions are within normal parameters.")
    else:
        st.warning("No data found in the database.")
