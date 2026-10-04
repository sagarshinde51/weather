import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import lightgbm as lgb
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

# --- HELPER FUNCTIONS ---
def get_season(month):
    if month in [11, 12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5, 6]:
        return "Summer"
    else:
        return "Rainy"

def get_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT * FROM heart_rate ORDER BY Date_Time DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert numeric columns to float[cite: 1]
        numeric_cols = ['Body_temp', 'Oxygen', 'Heart_Rate', 'Temp', 'Humi']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Date_Time'] = pd.to_datetime(df['Date_Time'])
        
        # Add Season column based on Date_Time month
        df['Season'] = df['Date_Time'].dt.month.apply(get_season)
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

        # ----------------------------- TAB 1: LATEST DATA -----------------------------
        with tab1:
            st.subheader("Most Recent Reading")
            latest = df.iloc[0]
            
            # Primary vitals metrics[cite: 1]
            col1, col2, col3 = st.columns(3)
            col1.metric("Heart Rate", f"{latest['Heart_Rate']} BPM")
            col2.metric("Oxygen (SpO2)", f"{latest['Oxygen']}%")
            col3.metric("Body Temp", f"{latest['Body_temp']}°C")

            # Ambient metrics and Season[cite: 1]
            col4, col5, col6 = st.columns(3)
            col4.metric("Ambient Temp", f"{latest['Temp']}°C")
            col5.metric("Humidity", f"{latest['Humi']}%")
            col6.metric("Season", f"{latest['Season']}")
            
            st.write(f"**Last Updated:** {latest['Date_Time']}")

        # ----------------------------- TAB 2: TRENDS & HISTORY -----------------------------
        with tab2:
            st.subheader("Visual Vitals Trends")
            
            # Line graph for metrics over time[cite: 1]
            df_melted = df.melt(
                id_vars=['Date_Time'], 
                value_vars=['Heart_Rate', 'Oxygen', 'Body_temp', 'Temp', 'Humi'],
                var_name='Metric', 
                value_name='Value'
            )
            
            fig = px.line(
                df_melted, 
                x='Date_Time', 
                y='Value', 
                color='Metric',
                title="All Vitals Parameters Over Time",
                labels={"Value": "Measurement", "Date_Time": "Time"},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.subheader("Historical Data Table")
            # Display dataframe with the newly added 'Season' column
            st.dataframe(df, use_container_width=True)

        # ----------------------------- TAB 3: ATTACK PREDICTION -----------------------------
        with tab3:
            st.subheader("Seasonal Cardiac Attack Risk Prediction (LightGBM)")
            st.write("Analyze cardiac risk across seasonal profiles (Winter, Summer, Rainy) directly from database vitals.")

            # Filter valid numerical entries[cite: 1]
            clean_df = df.dropna(subset=['Heart_Rate', 'Oxygen', 'Body_temp', 'Temp', 'Humi']).copy()

            if clean_df.empty:
                st.error("No valid readings found in the database.")
            else:
                clean_df['Month'] = clean_df['Date_Time'].dt.month
                
                # --- Seasonal Chart ---
                st.markdown("#### 📅 Seasonal Distribution of Recorded Readings")
                season_counts = clean_df['Season'].value_counts().reset_index()
                season_counts.columns = ['Season', 'Readings Count']

                season_colors = {
                    "Winter": "#00d2ff",
                    "Summer": "#ff7675",
                    "Rainy": "#0984e3"
                }

                fig_season = px.bar(
                    season_counts, 
                    x='Season', 
                    y='Readings Count', 
                    color='Season',
                    color_discrete_map=season_colors,
                    text='Readings Count',
                    title="Database Records Classified by Season",
                    template="plotly_dark"
                )
                fig_season.update_traces(textposition='outside')
                st.plotly_chart(fig_season, use_container_width=True)

                st.divider()

                # --- Model Training Setup ---
                features = ['Heart_Rate', 'Oxygen', 'Body_temp', 'Temp', 'Humi', 'Month']

                # Synthetic baseline cases to ensure consistent multi-class fitting
                synthetic_training_data = pd.DataFrame([
                    {'Heart_Rate': 72.0, 'Oxygen': 98.0, 'Body_temp': 36.6, 'Temp': 24.0, 'Humi': 50.0, 'Month': 4, 'Risk': 0},
                    {'Heart_Rate': 68.0, 'Oxygen': 99.0, 'Body_temp': 36.5, 'Temp': 22.0, 'Humi': 55.0, 'Month': 5, 'Risk': 0},
                    {'Heart_Rate': 75.0, 'Oxygen': 97.0, 'Body_temp': 36.8, 'Temp': 26.0, 'Humi': 78.0, 'Month': 8, 'Risk': 0},
                    {'Heart_Rate': 125.0, 'Oxygen': 88.0, 'Body_temp': 38.5, 'Temp': 8.0,  'Humi': 85.0, 'Month': 1, 'Risk': 1},
                    {'Heart_Rate': 110.0, 'Oxygen': 89.0, 'Body_temp': 37.8, 'Temp': 10.0, 'Humi': 80.0, 'Month': 12, 'Risk': 1},
                    {'Heart_Rate': 45.0,  'Oxygen': 90.0, 'Body_temp': 35.8, 'Temp': 6.0,  'Humi': 90.0, 'Month': 2, 'Risk': 1},
                    {'Heart_Rate': 130.0, 'Oxygen': 91.0, 'Body_temp': 39.0, 'Temp': 41.0, 'Humi': 30.0, 'Month': 5, 'Risk': 1}
                ])

                # Medical rules: cold winter stress or abnormal vitals
                is_winter = clean_df['Season'] == "Winter"
                extreme_temp = (clean_df['Temp'] < 16) | (clean_df['Temp'] > 38)
                abnormal_hr = (clean_df['Heart_Rate'] > 100) | (clean_df['Heart_Rate'] < 50)
                low_oxygen = clean_df['Oxygen'] < 92

                clean_df['Risk'] = np.where(
                    (low_oxygen & abnormal_hr) | (is_winter & (extreme_temp | abnormal_hr)), 
                    1, 
                    0
                )

                training_pool = pd.concat([clean_df[features + ['Risk']], synthetic_training_data], ignore_index=True)
                X_train = training_pool[features]
                y_train = training_pool['Risk']

                # LightGBM Classifier
                lgb_model = lgb.LGBMClassifier(
                    n_estimators=50,
                    learning_rate=0.05,
                    max_depth=3,
                    num_leaves=8,
                    min_child_samples=1,
                    random_state=42,
                    verbosity=-1
                )
                lgb_model.fit(X_train, y_train)

                # --- Prediction on Latest Database Value ---
                latest_record = clean_df.iloc[0]
                current_season = latest_record['Season']

                st.markdown("#### 🩺 Latest Patient Parameters from Database")

                # Highlight if current data originates from Winter
                if current_season == "Winter":
                    st.warning("❄️ **Winter Season Detected:** Vasoconstriction and low temperatures significantly increase cardiac workload and attack vulnerability.")
                else:
                    st.info(f"🌿 **Season Detected:** {current_season}")

                c1, c2, c3 = st.columns(3)
                c1.metric("Heart Rate", f"{latest_record['Heart_Rate']} BPM")
                c2.metric("Oxygen (SpO2)", f"{latest_record['Oxygen']}%")
                c3.metric("Body Temp", f"{latest_record['Body_temp']}°C")

                c4, c5, c6 = st.columns(3)
                c4.metric("Ambient Temp", f"{latest_record['Temp']}°C")
                c5.metric("Humidity", f"{latest_record['Humi']}%")
                c6.metric("Season / Month", f"{current_season} (Month {int(latest_record['Month'])})")

                if st.button("Predict Cardiac Risk", type="primary"):
                    input_data = pd.DataFrame([[
                        latest_record['Heart_Rate'],
                        latest_record['Oxygen'],
                        latest_record['Body_temp'],
                        latest_record['Temp'],
                        latest_record['Humi'],
                        latest_record['Month']
                    ]], columns=features)

                    prediction = lgb_model.predict(input_data)[0]
                    prediction_prob = lgb_model.predict_proba(input_data)[0][1] * 100

                    st.divider()
                    if prediction == 1:
                        if current_season == "Winter":
                            st.error(f"🚨 **CRITICAL: High Seasonal Cardiac Risk Detected in Winter!** (Risk Probability: {prediction_prob:.2f}%)")
                            st.markdown("> **Winter Risk Factor:** Cold ambient temperatures trigger peripheral vasoconstriction, driving blood pressure higher and severely straining cardiac output.")
                        else:
                            st.error(f"⚠️ **High Cardiac Risk Detected!** (Risk Probability: {prediction_prob:.2f}%)")
                            st.warning("Recommendation: Immediate medical evaluation is advised due to adverse vitals stress.")
                    else:
                        st.success(f"✅ **Low Cardiac Risk** (Risk Probability: {prediction_prob:.2f}%)")
                        st.info("Vitals and ambient conditions are currently within normal baseline ranges.")
    else:
        st.warning("No data found in the database.")
