import React, { useState } from 'react';
import './App.css';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function App() {
  const [strategy, setStrategy] = useState('covered_call');
  const [ticker, setTicker] = useState('AAPL');
  const [minExp, setMinExp] = useState(30);
  const [maxExp, setMaxExp] = useState(90);
  const [delta, setDelta] = useState(0.3);
  const [width, setWidth] = useState(5);
  
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
      delta,
      width
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

  const chartData = {
    labels: results?.chart_data?.labels || [],
    datasets: [
      {
        label: 'Profit per Trade ($)',
        data: results?.chart_data?.data || [],
        backgroundColor: results?.chart_data?.data.map(profit => profit >= 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)'),
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Weekly Trade Profit/Loss' },
    },
  };
  
  return (
    <div className="App">
      <header className="App-header">
        <h1>Options Strategy Backtester</h1>
        <form onSubmit={handleBacktest} className="input-form">
          <div className="form-row">
            <label>Strategy</label>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
              <option value="covered_call">Covered Call</option>
              <option value="cash_secured_put">Cash-Secured Put</option>
              <option value="iron_condor">Iron Condor</option>
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
          {strategy=='iron_condor'&&(
            <div className="form-row">
              <label>Wing Width ($)</label>
              <input
                type="number"
                value={width}
                onChange={(e) => setWidth(Number(e.target.value))}/>
            </div>
          )}
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
                <div className="chart-wrapper">
                  <Bar options={chartOptions} data={chartData} />
                </div>
                
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