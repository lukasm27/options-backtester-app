# Flask backend for the Options Strategy Backtester.
# This serves a REST API that runs the simulation and returns results.

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from py_vollib.black_scholes.greeks import analytical as greeks
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def run_backtest(ticker_symbol: str, strategy: str, min_exp: int, max_exp: int, target_delta: float, risk_free: float, width: int) -> dict:
    #The core simulation engine for the backtester.
    TIME_PERIOD_YEARS = 2
    TARGET_DELTA = abs(target_delta)

    def calculate_greek(row, stock_price, days_to_exp, flag='c'):
        #Helper to calculate option delta via Black-Scholes.
        try:
            S = stock_price
            K = row['strike']
            t = days_to_exp / 365.25
            r = risk_free
            sigma = row['impliedVolatility']
            return greeks.delta(flag, S, K, t, r, sigma)
        except Exception:
            return None

    try:
        yf_ticker = yf.Ticker(ticker_symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=TIME_PERIOD_YEARS * 365)

        hist = yf_ticker.history(start=start_date, end=end_date, interval="1d")
        hist.index = hist.index.tz_localize(None)
        
        trade_days = hist.resample('W-MON').first().index

        total_pnl = 0
        trade_count = 0
        trade_log = []
        chart_labels = []
        chart_data = []
        
        expirations = yf_ticker.options
        
        for trade_date in trade_days:
            log_date = trade_date.strftime('%Y-%m-%d')
            if trade_date not in hist.index:
                continue

            stock_price = hist.loc[trade_date]['Close']

            # Find the first suitable expiration date in our window
            target_exp_str = None
            days_to_exp = 0
            for exp_str in expirations:
                exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
                if exp_date > trade_date:
                    days_to_exp = (exp_date - trade_date).days
                    if min_exp <= days_to_exp <= max_exp:
                        target_exp_str = exp_str
                        break
            
            if not target_exp_str:
                continue

            option_chain = yf_ticker.option_chain(target_exp_str)
            
            if strategy == 'iron_condor':
                puts = option_chain.puts.dropna(subset=['impliedVolatility', 'strike', 'bid', 'ask']).copy()
                calls = option_chain.calls.dropna(subset=['impliedVolatility', 'strike', 'bid', 'ask']).copy()
                
                puts.loc[:, 'delta'] = puts.apply(lambda row: calculate_greek(row, stock_price, days_to_exp, 'p'), axis=1)
                calls.loc[:, 'delta'] = calls.apply(lambda row: calculate_greek(row, stock_price, days_to_exp, 'c'), axis=1)
                puts, calls = puts.dropna(subset=['delta']), calls.dropna(subset=['delta'])

                if puts.empty or calls.empty: continue

                short_put = puts.iloc[(puts['delta'].abs() - TARGET_DELTA).abs().argsort()[:1]]
                short_call = calls.iloc[(calls['delta'].abs() - TARGET_DELTA).abs().argsort()[:1]]

                if short_put.empty or short_call.empty: continue

                short_put_strike = short_put['strike'].iloc[0]
                short_call_strike = short_call['strike'].iloc[0]

                long_put_strike = short_put_strike - width
                long_call_strike = short_call_strike + width
                long_put = puts.iloc[(puts['strike'] - long_put_strike).abs().argsort()[:1]]
                long_call = calls.iloc[(calls['strike'] - long_call_strike).abs().argsort()[:1]]

                if long_put.empty or long_call.empty: continue

                credit = (short_put['bid'].iloc[0] + short_call['bid'].iloc[0]) - \
                         (long_put['ask'].iloc[0] + long_call['ask'].iloc[0])
                
                if credit <= 0: continue

                trade_pnl = credit * 100
                actual_width = long_call['strike'].iloc[0] - short_call['strike'].iloc[0]
                max_loss = (actual_width * 100) - trade_pnl
                
                exp_date = datetime.strptime(target_exp_str, '%Y-%m-%d')
                exp_index = hist.index.get_indexer([exp_date], method='nearest')[0]
                exp_price = hist.iloc[exp_index]['Close']
                
                outcome = "Expired OTM (Max Profit)"
                if not (short_put_strike < exp_price < short_call_strike):
                    outcome = "Expired ITM (Max Loss)"
                    trade_pnl = -max_loss
                
                total_pnl += trade_pnl
                trade_count += 1
                trade_log.append(f"[{log_date}] Trade: Sold Iron Condor on {target_exp_str} for ${credit*100:.2f} credit. Final Profit: ${trade_pnl:.2f}. Outcome: {outcome}")
                chart_labels.append(log_date)
                chart_data.append(round(trade_pnl, 2))

            elif strategy in ['covered_call', 'cash_secured_put']:
                options = option_chain.calls if strategy == 'covered_call' else option_chain.puts
                flag = 'c' if strategy == 'covered_call' else 'p'

                options = options.dropna(subset=['impliedVolatility', 'strike', 'bid'])
                options = options[options['impliedVolatility'] > 0]
                options = options[options['bid'] > 0]
                if options.empty: continue

                options['delta'] = options.apply(lambda row: calculate_greek(row, stock_price, days_to_exp, flag), axis=1)
                options = options.dropna(subset=['delta'])
                if options.empty: continue

                trade = options.iloc[(options['delta'].abs() - TARGET_DELTA).abs().argsort()[:1]]
                if not trade.empty:
                    strike = trade['strike'].iloc[0]
                    premium = trade['bid'].iloc[0]
                    
                    exp_date = datetime.strptime(target_exp_str, '%Y-%m-%d')
                    exp_index = hist.index.get_indexer([exp_date], method='nearest')[0]
                    exp_price = hist.iloc[exp_index]['Close']

                    trade_pnl = premium * 100
                    outcome = "Expired OTM"

                    if (strategy == 'covered_call' and exp_price > strike) or \
                       (strategy == 'cash_secured_put' and exp_price < strike):
                        outcome = "Expired ITM"
                        if strategy == 'covered_call':
                            stock_pnl = (strike - stock_price) * 100
                            trade_pnl += stock_pnl
                        elif strategy == 'cash_secured_put':
                            stock_loss = (strike - exp_price) * 100
                            trade_pnl -= stock_loss
                            
                    total_pnl += trade_pnl
                    trade_count += 1
                    trade_log.append(f"[{log_date}] Trade: Sold {strategy} on {target_exp_str} for ${premium:.2f} premium. Final Profit: ${trade_pnl:.2f}. Outcome: {outcome}")
                    chart_labels.append(log_date)
                    chart_data.append(round(trade_pnl, 2))
        
        return {
            "ticker": ticker_symbol, "trade_count": trade_count, "total_profit": round(total_pnl, 2), "trade_log": trade_log,
            "parameters": f"strategy={strategy}, min_exp={min_exp}, max_exp={max_exp}, delta={target_delta}",
            "chart_data": {"labels": chart_labels, "data": chart_data}
        }

    except Exception as e:
        return {"error": str(e)}

@app.route('/backtest', methods=['GET'])
def backtest_endpoint():
    #API endpoint to handle backtest requests.
    ticker = request.args.get('ticker', default='MSFT', type=str)
    strategy = request.args.get('strategy', default='covered_call', type=str)
    min_exp = request.args.get('min_exp', default=30, type=int)
    max_exp = request.args.get('max_exp', default=90, type=int)
    delta = request.args.get('delta', default=0.3, type=float)
    risk_free = request.args.get('risk_free', default=0.05, type=float)
    width = request.args.get('width', default=5, type=int)

    results = run_backtest(ticker, strategy, min_exp, max_exp, delta, risk_free, width)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)