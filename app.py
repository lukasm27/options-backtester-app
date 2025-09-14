import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from py_vollib.black_scholes.greeks import analytical as greeks
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def run_backtest(ticker: str, strategy: str, min_exp: int, max_exp: int, target_delta: float, risk_free: float) -> dict:
    """Runs a backtest for a given ticker and strategy."""
    TIME_PERIOD_YEARS = 0.25
    # For puts, delta is negative, so use the absolute value for the target
    TARGET_DELTA = abs(target_delta) if strategy == 'cash_secured_put' else target_delta

    def calculate_greek(row, stock_price, days_expiry, greek='delta', flag='c'):
        #Helper function to calculate option greeks using Black-Scholes.
        try:
            S = stock_price
            K = row['strike']
            t = days_expiry / 365.25
            r = risk_free
            sigma = row['impliedVolatility']
            if greek == 'delta':
                return greeks.delta(flag, S, K, t, r, sigma)
            # Can add other greeks like gamma or theta here later
        except Exception:
            return None

    try:
        ticker_obj = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=TIME_PERIOD_YEARS * 365)
        stock_history = ticker_obj.history(start=start_date, end=end_date, interval="1d")
        stock_history.index = stock_history.index.tz_localize(None)
        trade_days = stock_history.resample('MS').first().index

        total_profit = 0
        trade_count = 0
        trade_log = []
        
        expirations = ticker_obj.options
        
        for trade_date in trade_days:
            if trade_date not in stock_history.index:
                continue

            stock_price = stock_history.loc[trade_date]['Close']
            suitable_exp = None
            days_expiry = 0
            for exp_str in expirations:
                exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
                if exp_date > trade_date:
                    days_expiry = (exp_date - trade_date).days
                    if min_exp <= days_expiry <= max_exp:
                        suitable_exp = exp_str
                        break
            
            if not suitable_exp:
                continue

            # STRATEGY LOGIC
            option_chain = ticker_obj.option_chain(suitable_exp)
            if strategy == 'covered_call':
                options_df = option_chain.calls
                option_flag = 'c' #call
                outcome_condition = lambda expiry_price, strike: expiry_price > strike
            elif strategy == 'cash_secured_put':
                options_df = option_chain.puts
                option_flag = 'p' #put
                outcome_condition = lambda expiry_price, strike: expiry_price < strike
            else:
                return {"error": "Invalid strategy selected"}
                
            options_df = options_df.dropna(subset=['impliedVolatility', 'strike', 'bid'])
            options_df = options_df[options_df['impliedVolatility'] > 0]
            options_df = options_df[options_df['bid'] > 0]
            
            if options_df.empty: continue
            
            options_df['delta'] = options_df.apply(lambda row: calculate_greek(row, stock_price, days_expiry, 'delta', option_flag), axis=1)
            options_df = options_df.dropna(subset=['delta'])
            
            if options_df.empty: continue

            # For puts, delta is negative, so find the closest absolute value
            target_option = options_df.iloc[(options_df['delta'].abs() - TARGET_DELTA).abs().argsort()[:1]]

            if not target_option.empty:
                strike_price = target_option['strike'].iloc[0]
                premium = target_option['bid'].iloc[0]
                
                try:
                    exp_datetime = datetime.strptime(suitable_exp, '%Y-%m-%d')
                    expiry_index = stock_history.index.get_indexer([exp_datetime], method='nearest')[0]
                    expiry_row = stock_history.iloc[expiry_index]
                    expiry_price = expiry_row['Close']
                except KeyError:
                    continue

                trade_profit = premium * 100
                outcome = "Expired OTM"
                
                # Check outcome condition
                if outcome_condition(expiry_price, strike_price):
                    if strategy == 'covered_call':
                        stock_profit = (strike_price - stock_price) * 100
                        trade_profit += stock_profit
                    elif strategy == 'cash_secured_put':
                        stock_loss = (expiry_price - strike_price) * 100
                        trade_profit += stock_loss
                    outcome = "Expired ITM"
            
                total_profit += trade_profit
                trade_count += 1
                trade_log.append(f"Sold {strategy} on {suitable_exp} with strike ${strike_price:.2f}. Profit: ${trade_profit:.2f}. Outcome: {outcome}")

        return {
            "ticker": ticker, "trade_count": trade_count, "total_profit": round(total_profit, 2), "trade_log": trade_log,
            "parameters": f"strategy={strategy}, min_exp={min_exp}, max_exp={max_exp}, delta={target_delta}"
        }

    except Exception as e:
        return {"error": str(e)}

@app.route('/backtest', methods=['GET'])
def backtest_endpoint():
    """API endpoint now also accepts a 'strategy' parameter."""
    ticker = request.args.get('ticker', default='MSFT', type=str)
    strategy = request.args.get('strategy', default='covered_call', type=str)
    min_exp = request.args.get('min_exp', default=30, type=int)
    max_exp = request.args.get('max_exp', default=90, type=int)
    delta = request.args.get('delta', default=0.3, type=float)
    risk_free = request.args.get('risk_free', default=0.05, type=float)

    results = run_backtest(ticker, strategy, min_exp, max_exp, delta, risk_free)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)