# Options Strategy Backtester

## Overview

This is a full-stack web application that allows users to backtest options strategies for a given stock. The application uses a Python Flask backend to fetch financial data and run the simulation, and a React frontend to provide a user-friendly interface. This backtester is a simulation and not a perfect historical replay. Due to the limitations of the free version of yfinance, the application uses current options chain data and applies it to historical stock prices. The results are therefore a valuable simulation of a strategy's mechanics but are not historically accurate. Due to this reliance on current options data, the backtest can only produce valid trades for the most recent three months. When the simulation looks at older historical dates, it cannot find a suitable future expiration date from today's list of available options.



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