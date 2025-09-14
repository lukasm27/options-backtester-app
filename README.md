# Options Strategy Backtester

## Overview

This is a full-stack web application that allows users to backtest options strategies for a given stock. The application uses a Python Flask backend to fetch financial data and run the simulation, and a React frontend to provide a user-friendly interface.



## Features

-   **Dynamic Backtesting:** Users can input any valid stock ticker.
-   **Customisable Parameters:** Strategy parameters like min/max expiration and target delta can be adjusted.
-   **Full-Stack Architecture:** Demonstrates a decoupled frontend and backend communicating via a REST API.
-   **Manual Calculations:** Implements the Black-Scholes model to calculate option 'delta'.

## Technology Stack

-   **Backend:** Python, Flask, Flask-CORS
-   **Financial Data:** yfinance
-   **Calculation Libraries:** Pandas, NumPy, py_vollib
-   **Frontend:** JavaScript, React

## How to Run

### Backend (Flask)
1.  Navigate to the root project folder.
2.  Create and activate a virtual environment:
    py -m venv venv
    venv\Scripts\activate
3.  Install dependencies:
    pip install -r requirements.txt 
4.  Run the server:
    flask run
The backend will be running at http://127.0.0.1:5000.

### Frontend (React)
1.  Navigate to the frontend directory:
    cd frontend
2.  Install dependencies:
    npm install
3.  Run the application:
    npm start
The frontend will be available at http://localhost:3000.