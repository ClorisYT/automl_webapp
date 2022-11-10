import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
from imblearn.over_sampling import RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTEENN
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from catboost import CatBoostRegressor, CatBoostClassifier
import numpy as np
from sklearn.metrics import r2_score, accuracy_score, confusion_matrix, mean_absolute_error, mean_squared_error, precision_score, recall_score, f1_score, roc_auc_score
import pickle

st.set_page_config(layout="wide")
st.title("Auto Machine Learning Web Application")

with st.sidebar:
    st.title("Automated Machine Learning Pipeline Web Application")
    st.write("1. Upload your dataset.")
    st.write("2. View a summary of your dataset.")
    st.write("3. Visualize correlation matrix and values distribution.")
    st.write("4. Clean your data.")
    st.write("5. Apply data preprocessing techniques.")
    st.write("6. Train regression/classification models.")
    st.write("7. Evaluate your trained models.")
    st.write("8. Download your models.")
    st.write("Made by [Youssef CHAFIQUI](https://www.ychafiqui.com)")
    st.write("Code on [Github](https://www.github.com/ychafiqui/automl_webapp)")

df = None
if 'df' not in st.session_state:
    st.session_state.df = df
else:
    df = st.session_state.df

st.session_state.eval = False

with st.expander("Upload your data", expanded=True):
    file = st.file_uploader("Upload a dataset", type=["csv"])
    if file is not None:
        df = pd.read_csv(file)
        st.write(df)
        st.write("Dataset shape:", df.shape)

with st.expander("Data Summary"):
    if df is not None:
        st.write(df.describe())

with st.expander("Data Visualization"):
    if df is not None:
        st.subheader("Correlation Heatmap")
        fig = px.imshow(df.corr(numeric_only=True))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig)

        st.subheader("Value Counts")
        all_cols_less_40 = [col for col in df.columns if df[col].nunique() < 40]
        cols_to_show = st.multiselect("Select columns to show", all_cols_less_40)
        for col in cols_to_show:
            st.write(col)
            st.bar_chart(df[col].value_counts())

with st.expander("Data Cleaning"):
    if df is not None:
        st.write("Select cleaning options")
        drop_na0 = st.checkbox("Drop all rows with Nan values")
        drop_na1 = st.checkbox("Drop all columns with Nan values")
        drop_duplicates = st.checkbox("Remove duplicates")
        drop_colmuns = st.checkbox("Drop specific columns")
        if drop_colmuns:
            columns = st.multiselect("Select columns to drop", df.columns)
        if st.button("Apply data cleaning"):
            if drop_na0:
                df = df.dropna(axis=0)
            if drop_na1:
                df = df.dropna(axis=1)
            if drop_duplicates:
                df = df.drop_duplicates()
            if drop_colmuns:
                df = df.drop(columns, axis=1)
            st.session_state.df = df
            st.write(df)
            st.write("Dataset shape:", df.shape)
            st.write("Total number of Nan values remaining:", df.isna().sum().sum())

with st.expander("Data Preprocessing"):
    if df is not None:
        if st.session_state.df is not None:
            df = st.session_state.df
        st.write("Select preprocessing options")
        balance = st.checkbox("Balance your dataset")
        if balance:
            sample_tech = st.selectbox("Select sampling technique", ["Over Sampling", "Under Sampling", "Combined"])
            target = st.selectbox("Select target column to be balanced", df.columns, index=len(df.columns)-1)
        pca = st.checkbox("Apply PCA")
        if pca:
            n_components = st.number_input("Number of PCA components", min_value=1, max_value=min(df.shape[0], df.shape[1]), value=2)
            target = st.selectbox("Select target column to be excluded from PCA", df.columns, index=len(df.columns)-1)

        if st.button("Apply data preprocessing"):
            if balance:
                st.session_state.target = target
                X = df.drop(st.session_state.target, axis=1)
                y = df[st.session_state.target]
                if sample_tech == "Over Sampling":
                    X_resampled, y_resampled = RandomOverSampler(random_state=0).fit_resample(X, y)
                elif sample_tech == "Under Sampling":
                    X_resampled, y_resampled = RandomUnderSampler(random_state=0).fit_resample(X, y)
                elif sample_tech == "Combined":
                    X_resampled, y_resampled = SMOTEENN(random_state=0).fit_resample(X, y)
                df = pd.DataFrame(X_resampled, columns=df.columns[:-1])
                df[st.session_state.target] = y_resampled
                st.bar_chart(df[st.session_state.target].value_counts())
            if pca:
                columns = df.columns
                df = OrdinalEncoder().fit_transform(df)
                df = pd.DataFrame(df, columns=columns)
                st.session_state.target = target
                pca = PCA(n_components=n_components)
                X = df.drop(st.session_state.target, axis=1)
                y = df[st.session_state.target]
                df = pca.fit_transform(X)
                df = pd.DataFrame(df)
                df[st.session_state.target] = y

            st.session_state.df = df
            st.write(df)
            st.write("Dataset shape:", df.shape)
        

with st.expander("Model Training"):
    if df is not None:
        if st.session_state.df is not None:
            df = st.session_state.df
        columns = df.columns
        df = OrdinalEncoder().fit_transform(df)
        df = pd.DataFrame(df, columns=columns)
        st.write("Dataset to be used for training")
        st.write(df)
        st.write("Dataset shape:", df.shape)
        test_data_size = st.slider("Test data size (%)", 10, 90, 20, 5)
        if 'target' not in st.session_state:
            st.session_state.target = st.selectbox("Select target column", df.columns, index=len(df.columns)-1)
        prob = st.radio("Select problem type", ["Classification", "Regression"])
        models = st.multiselect("Select ML models to train", ["Logistic/Linear Regression", "Random Forest", "XGBoost", "CatBoost"])

        if "Logistic/Linear Regression" in models:
            st.subheader("Logistic/Linear Regression Parameters")
            max_iter = st.number_input("Maximum number of iterations", min_value=100, max_value=10000, value=1000)
        if "Random Forest" in models:
            st.subheader("Random Forest Parameters")
            n_estimators = st.number_input("Number of estimators", key=1, min_value=100, max_value=10000, value=1000)
        if "XGBoost" in models:
            st.subheader("XGBoost Parameters")
            n_estimators = st.number_input("Number of estimators", key=2, min_value=100, max_value=10000, value=1000)
        if "CatBoost" in models:
            st.subheader("CatBoost Parameters")
            n_estimators = st.number_input("Number of estimators", key=3, min_value=100, max_value=10000, value=1000)

        if st.button("Train models"):
            if len(models) == 0:
                st.error("Please select at least one model to train")
            else:
                st.session_state.models = []
                st.session_state.model_names = models
                X = df.drop(st.session_state.target, axis=1)
                y = df[st.session_state.target]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_data_size/100)
                if "Logistic/Linear Regression" in models:
                    with st.spinner("Training Logistic/Linear Regression model..."):
                        lr_model = LogisticRegression(max_iter=max_iter) if prob == "Classification" else LinearRegression()
                        lr_model.fit(X_train, y_train)
                        st.success("Logistic/Linear Regression model training complete!")
                        st.session_state.models.append(lr_model)
                if "Random Forest" in models:
                    with st.spinner("Training Random Forest model..."):
                        rf_model = RandomForestClassifier(n_estimators=n_estimators) if prob=="Classification" else RandomForestRegressor(n_estimators=n_estimators)
                        rf_model.fit(X_train, y_train)
                        st.success("Random Forest model training complete!")
                        st.session_state.models.append(rf_model)
                if "XGBoost" in models:
                    with st.spinner("Training XGBoost model..."):
                        xgb_model = XGBClassifier(n_estimators=n_estimators) if prob=="Classification" else XGBRegressor(n_estimators=n_estimators)
                        xgb_model.fit(X_train, y_train)
                        st.success("XGBoost model training complete!")
                        st.session_state.models.append(xgb_model)
                if "CatBoost" in models:
                    with st.spinner("Training CatBoost model..."):
                        cat_model = CatBoostClassifier(n_estimators=n_estimators) if prob=="Classification" else CatBoostRegressor(n_estimators=n_estimators)
                        cat_model.fit(X_train, y_train, verbose=False)
                        st.success("CatBoost model training complete!")
                        st.session_state.models.append(cat_model)
                st.session_state.eval = True

with st.expander("Model Evaluation"):
    if 'models' in st.session_state and len(st.session_state.models) != 0 and st.session_state.eval:
        st.subheader("Evaluation Metrics")
        if prob == "Classification":
            eval_df = pd.DataFrame(columns=["Model", "Accuracy", "Precision", "Recall", "F1 Score"])
            if df[st.session_state.target].nunique() > 2:
                avg = 'micro'
            else:
                avg = 'binary'
            for model, name in zip(st.session_state.models, st.session_state.model_names):
                y_pred = model.predict(X_test)
                row_df = pd.DataFrame({
                    "Model": [name],
                    "Accuracy": [accuracy_score(y_test, y_pred)],
                    "Precision": [precision_score(y_test, y_pred, average=avg)],
                    "Recall": [recall_score(y_test, y_pred, average=avg)],
                    "F1 Score": [f1_score(y_test, y_pred, average=avg)]
                })
                eval_df = pd.concat([eval_df, row_df], ignore_index=True)
            st.table(eval_df)
            st.subheader("Confusion Matrix")
            cols = st.columns(len(st.session_state.models))
            for i, col in enumerate(cols):
                col.write(st.session_state.model_names[i])
                y_pred = st.session_state.models[i].predict(X_test)
                col.table(confusion_matrix(y_test, y_pred))
        elif prob == "Regression":
            eval_df = pd.DataFrame(columns=["Model", "R2 Score", "Mean Absolute Error", "Mean Squared Error", "Root Mean Squared Error"])
            for model, name in zip(st.session_state.models, st.session_state.model_names):
                y_pred = model.predict(X_test)
                row_df = pd.DataFrame({
                    "Model": [name],
                    "R2 Score": [r2_score(y_test, y_pred)],
                    "Mean Absolute Error": [mean_absolute_error(y_test, y_pred)],
                    "Mean Squared Error": [mean_squared_error(y_test, y_pred)],
                    "Root Mean Squared Error": [np.sqrt(mean_squared_error(y_test, y_pred))]
                })
                eval_df = pd.concat([eval_df, row_df], ignore_index=True)
            st.table(eval_df)

with st.expander("Model Download"):
    if 'models' in st.session_state and len(st.session_state.models) != 0:
        st.write("Download your trained models")
        for m, model_name in zip(st.session_state.models, st.session_state.model_names):
            st.download_button(label="Download " + model_name + " model", data=pickle.dumps(m), file_name=model_name+"_model.pkl", mime="application/octet-stream")