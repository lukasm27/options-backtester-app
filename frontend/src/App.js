import React, { useState } from 'react';
import './App.css';

function App() {
  // State for strategy parameters, including the new strategy selector
  const [strategy, setStrategy] = useState('covered_call');
  const [ticker, setTicker] = useState('AAPL');
  const [minExp, setMinExp] = useState(30);
  const [maxExp, setMaxExp] = useState(90);
  const [delta, setDelta] = useState(0.3);
  
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleBacktest = (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);

    const params = new URLSearchParams({
      strategy,
      ticker,
      min_exp: minExp,
      max_exp: maxExp,
      delta
    });
    
    const url = `http://127.0.0.1:5000/backtest?${params.toString()}`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        setResults(data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching results:", error);
        setResults({ error: "Failed to fetch results from the backend." });
        setLoading(false);
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Options Strategy Backtester</h1>
        <form onSubmit={handleBacktest} className="input-form">
          {/* New Dropdown for Strategy */}
          <div className="form-row">
            <label>Strategy</label>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
              <option value="covered_call">Covered Call</option>
              <option value="cash_secured_put">Cash-Secured Put</option>
            </select>
          </div>

          <div className="form-row">
            <label>Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
            />
          </div>
          <div className="form-row">
            <label>Min Exp Days</label>
            <input
              type="number"
              value={minExp}
              onChange={(e) => setMinExp(Number(e.target.value))}
            />
          </div>
          <div className="form-row">
            <label>Max Exp Days</label>
            <input
              type="number"
              value={maxExp}
              onChange={(e) => setMaxExp(Number(e.target.value))}
            />
          </div>
          <div className="form-row">
            <label>Target Delta</label>
            <input
              type="number"
              step="0.01"
              value={delta}
              onChange={(e) => setDelta(Number(e.target.value))}
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Running...' : 'Run Backtest'}
          </button>
        </form>

        {results && (
          <div className="results-container">
            {results.error ? (
              <p className="error">Error: {results.error}</p>
            ) : (
              <>
                <h2>Backtest Results for {results.ticker}</h2>
                <p><strong>Parameters:</strong> {results.parameters}</p>
                <p><strong>Total Profit:</strong> ${results.total_profit}</p>
                <p><strong>Trades Executed:</strong> {results.trade_count}</p>
                <h3>Trade Log:</h3>
                <ul>
                  {results.trade_log.map((log, index) => (
                    <li key={index}>{log}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;