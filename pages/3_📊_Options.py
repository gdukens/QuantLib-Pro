"""
Options Pricing Dashboard

Week 12: Streamlit page for options pricing, Greeks analysis, and volatility surface.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

from quantlib_pro.ui import components
from quantlib_pro.options.black_scholes import price_with_greeks, implied_volatility
from quantlib_pro.options.monte_carlo import price_european
from quantlib_pro.options.bachelier import BachelierModel, bachelier_call, bachelier_put
from quantlib_pro.utils.types import OptionType

# Page config
st.set_page_config(
    page_title="Options Pricing - QuantLib Pro",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Options Pricing")
st.markdown("Price European options using Black-Scholes and Monte Carlo methods, analyze Greeks, and visualize payoffs.")

# Initialize session state
if "option_results" not in st.session_state:
    st.session_state.option_results = None

# Sidebar controls
with st.sidebar:
    st.header("Option Parameters")
    
    # Option type
    option_type = st.selectbox(
        "Option Type",
        ["call", "put"],
        index=0,
    )
    
    # Underlying parameters
    st.subheader("Underlying Asset")
    
    spot_price = st.number_input(
        "Spot Price ($)",
        min_value=1.0,
        max_value=10000.0,
        value=100.0,
        step=1.0,
    )
    
    strike_price = st.number_input(
        "Strike Price ($)",
        min_value=1.0,
        max_value=10000.0,
        value=100.0,
        step=1.0,
    )
    
    # Time parameters
    st.subheader("Time & Rates")
    
    days_to_expiry = st.slider(
        "Days to Expiration",
        min_value=1,
        max_value=365*2,
        value=30,
        step=1,
    )
    time_to_expiry = days_to_expiry / 365.0
    
    risk_free_rate = st.slider(
        "Risk-free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.1,
    ) / 100
    
    dividend_yield = st.slider(
        "Dividend Yield (%)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
    ) / 100
    
    # Volatility
    st.subheader("Volatility")
    
    volatility = st.slider(
        "Implied Volatility (%)",
        min_value=1.0,
        max_value=200.0,
        value=20.0,
        step=1.0,
    ) / 100
    
    # Pricing method
    st.subheader("Pricing Method")
    
    pricing_method = st.selectbox(
        "Method",
        ["Black-Scholes", "Bachelier", "Monte Carlo"],
        index=0,
        help="Black-Scholes: Geometric Brownian Motion | Bachelier: Arithmetic Brownian Motion (normal model) | Monte Carlo: Simulation-based"
    )
    
    if pricing_method == "Monte Carlo":
        num_simulations = st.number_input(
            "Number of Simulations",
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=10000,
        )
        
        num_steps = st.number_input(
            "Time Steps",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
        )
    
    # Price button
    price_button = st.button("💰 Price Option", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 Pricing",
    "📈 Greeks", 
    "📊 Payoff Diagram",
    "🔍 Implied Vol",
    "📉 Tail Risk Distribution",
    "🌊 Volatility Shockwave",
    "💹 BS Visual Explainer"
])

with tab1:
    st.header("Option Pricing")
    
    if price_button:
        with st.spinner(f"Pricing using {pricing_method}..."):
            try:
                # Convert option_type string to enum
                opt_type_enum = OptionType.CALL if option_type == "call" else OptionType.PUT
                
                if pricing_method == "Black-Scholes":
                    # Black-Scholes pricing
                    result = price_with_greeks(
                        S=spot_price,
                        K=strike_price,
                        T=time_to_expiry,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=opt_type_enum,
                    )
                    
                    option_price = result.outputs["price"]
                    greeks = {
                        "Delta": result.outputs["delta"],
                        "Gamma": result.outputs["gamma"],
                        "Vega": result.outputs["vega"],
                        "Theta": result.outputs["theta"],
                        "Rho": result.outputs["rho"],
                    }
                    
                    st.session_state.option_results = {
                        "price": option_price,
                        "greeks": greeks,
                        "method": "Black-Scholes",
                        "option_type": option_type,
                        "spot": spot_price,
                        "strike": strike_price,
                        "time_to_expiry": time_to_expiry,
                        "volatility": volatility,
                        "risk_free_rate": risk_free_rate,
                        "dividend_yield": dividend_yield,
                    }
                    
                elif pricing_method == "Bachelier":
                    # Bachelier pricing (Arithmetic Brownian Motion)
                    # Convert volatility from percentage to absolute terms
                    sigma_absolute = volatility * spot_price
                    
                    model = BachelierModel(sigma=sigma_absolute)
                    
                    # Use forward price F = S * exp((r-q)*T)
                    forward_price = spot_price * np.exp((risk_free_rate - dividend_yield) * time_to_expiry)
                    
                    # Price the option
                    option_price = model.price(
                        F0=forward_price,
                        K=strike_price,
                        T=time_to_expiry,
                        option_type=option_type
                    )
                    
                    # Calculate Greeks
                    greeks = {
                        "Delta": model.delta(forward_price, strike_price, time_to_expiry, option_type),
                        "Gamma": model.gamma(forward_price, strike_price, time_to_expiry),
                        "Vega": model.vega(forward_price, strike_price, time_to_expiry),
                        "Theta": model.theta(forward_price, strike_price, time_to_expiry, option_type),
                        "Rho": 0.0,  # Bachelier model doesn't have rho (rate-independent)
                    }
                    
                    st.session_state.option_results = {
                        "price": option_price,
                        "greeks": greeks,
                        "method": "Bachelier",
                        "option_type": option_type,
                        "spot": spot_price,
                        "strike": strike_price,
                        "time_to_expiry": time_to_expiry,
                        "volatility": volatility,
                        "risk_free_rate": risk_free_rate,
                        "dividend_yield": dividend_yield,
                        "forward_price": forward_price,
                        "sigma_absolute": sigma_absolute,
                    }
                    
                else:  # Monte Carlo
                    # Create Monte Carlo configuration
                    from quantlib_pro.options.monte_carlo import MonteCarloConfig
                    config = MonteCarloConfig(
                        n_paths=int(num_simulations),
                        n_steps=int(num_steps),
                    )
                    
                    result = price_european(
                        S=spot_price,
                        K=strike_price,
                        T=time_to_expiry,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=opt_type_enum,
                        config=config,
                    )
                    
                    option_price = result.outputs["price"]
                    
                    st.session_state.option_results = {
                        "price": option_price,
                        "confidence_interval": result.outputs.get("ci_lower"),
                        "standard_error": result.outputs.get("std_error"),
                        "num_simulations": num_simulations,
                        "method": "Monte Carlo",
                        "option_type": option_type,
                        "spot": spot_price,
                        "strike": strike_price,
                        "time_to_expiry": time_to_expiry,
                        "volatility": volatility,
                        "risk_free_rate": risk_free_rate,
                    }
                
                components.success_message("Option priced successfully!")
                
            except Exception as e:
                components.error_message(f"Pricing failed: {str(e)}")
                st.session_state.option_results = None
    
    # Display pricing results
    if st.session_state.option_results:
        results = st.session_state.option_results
        
        # Main metrics
        intrinsic_value = max(
            (results["spot"] - results["strike"]) if results["option_type"] == "call" 
            else (results["strike"] - results["spot"]),
            0
        )
        time_value = results["price"] - intrinsic_value
        
        moneyness = results["spot"] / results["strike"]
        if moneyness > 1.05:
            moneyness_label = "ITM (In-the-Money)" if results["option_type"] == "call" else "OTM (Out-of-the-Money)"
        elif moneyness < 0.95:
            moneyness_label = "OTM (Out-of-the-Money)" if results["option_type"] == "call" else "ITM (In-the-Money)"
        else:
            moneyness_label = "ATM (At-the-Money)"
        
        components.multi_metric_row([
            {
                "title": "Option Price",
                "value": f"${results['price']:.2f}",
                "help": f"{results['option_type'].upper()} option price using {results['method']}",
            },
            {
                "title": "Intrinsic Value",
                "value": f"${intrinsic_value:.2f}",
                "help": "Value if exercised immediately",
            },
            {
                "title": "Time Value",
                "value": f"${time_value:.2f}",
                "help": "Premium above intrinsic value",
            },
            {
                "title": "Moneyness",
                "value": moneyness_label,
                "help": f"S/K = {moneyness:.3f}",
            },
        ])
        
        st.markdown("---")
        
        # Detailed parameters
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Input Parameters")
            params_df = pd.DataFrame({
                "Parameter": [
                    "Option Type",
                    "Spot Price",
                    "Strike Price",
                    "Time to Expiry",
                    "Volatility",
                    "Risk-free Rate",
                ],
                "Value": [
                    results["option_type"].upper(),
                    f"${results['spot']:.2f}",
                    f"${results['strike']:.2f}",
                    f"{results['time_to_expiry']*365:.0f} days ({results['time_to_expiry']:.4f} years)",
                    f"{results['volatility']*100:.2f}%",
                    f"{results['risk_free_rate']*100:.2f}%",
                ],
            })
            
            if "dividend_yield" in results:
                params_df = pd.concat([
                    params_df,
                    pd.DataFrame({
                        "Parameter": ["Dividend Yield"],
                        "Value": [f"{results['dividend_yield']*100:.2f}%"],
                    })
                ])
            
            st.dataframe(params_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Pricing Details")
            details_df = pd.DataFrame({
                "Metric": ["Method", "Price", "Intrinsic Value", "Time Value"],
                "Value": [
                    results["method"],
                    f"${results['price']:.4f}",
                    f"${intrinsic_value:.4f}",
                    f"${time_value:.4f}",
                ],
            })
            
            if results["method"] == "Monte Carlo":
                ci = results.get("confidence_interval", [0, 0])
                details_df = pd.concat([
                    details_df,
                    pd.DataFrame({
                        "Metric": ["Simulations", "Std Error", "95% CI Lower", "95% CI Upper"],
                        "Value": [
                            f"{results['num_simulations']:,}",
                            f"${results.get('standard_error', 0):.4f}",
                            f"${ci[0]:.4f}" if isinstance(ci, (list, tuple)) else "N/A",
                            f"${ci[1]:.4f}" if isinstance(ci, (list, tuple)) else "N/A",
                        ],
                    })
                ])
            elif results["method"] == "Bachelier":
                details_df = pd.concat([
                    details_df,
                    pd.DataFrame({
                        "Metric": ["Model Type", "Forward Price", "Absolute Sigma", "Formula"],
                        "Value": [
                            "Arithmetic Brownian Motion",
                            f"${results.get('forward_price', 0):.4f}",
                            f"${results.get('sigma_absolute', 0):.4f}",
                            "dF = σ dW (normal model)",
                        ],
                    })
                ])
            
            st.dataframe(details_df, hide_index=True, use_container_width=True)
        
    else:
        components.info_message("Click 'Price Option' to calculate the option value.")

with tab2:
    st.header("Option Greeks")
    
    if st.session_state.option_results and "greeks" in st.session_state.option_results:
        greeks = st.session_state.option_results["greeks"]
        
        # Plot Greeks
        fig = components.plot_greeks(greeks, height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        # Greeks explanation
        st.subheader("Greeks Interpretation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                f"""
                **Delta ({greeks['Delta']:.4f})**  
                Change in option price for $1 change in underlying.  
                _{abs(greeks['Delta'])*100:.2f}% hedge ratio_
                
                **Gamma ({greeks['Gamma']:.4f})**  
                Rate of change of Delta.  
                _Measures Delta stability_
                
                **Vega ({greeks['Vega']:.4f})**  
                Change in option price for 1% change in volatility.  
                _${abs(greeks['Vega']):.2f} per 1% vol change_
                """
            )
        
        with col2:
            st.markdown(
                f"""
                **Theta ({greeks['Theta']:.4f})**  
                Daily time decay of option value.  
                _${abs(greeks['Theta']):.2f} per day_
                
                **Rho ({greeks['Rho']:.4f})**  
                Change in option price for 1% change in interest rate.  
                _${abs(greeks['Rho']):.2f} per 1% rate change_
                """
            )
            
            if st.session_state.option_results["method"] == "Bachelier":
                st.info("ℹ️ **Bachelier Model**: Rho is not applicable (rate-independent normal model)")
        
        # Sensitivity analysis
        st.subheader("Sensitivity Analysis")
        
        spot_range = np.linspace(spot_price * 0.7, spot_price * 1.3, 50)
        option_values = []
        deltas = []
        
        # Convert option_type string to enum
        opt_type_enum = OptionType.CALL if option_type == "call" else OptionType.PUT
        
        for S in spot_range:
            result = price_with_greeks(
                S=S,
                K=strike_price,
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=volatility,
                option_type=opt_type_enum,
            )
            option_values.append(result.outputs["price"])
            deltas.append(result.outputs["delta"])
        
        sensitivity_df = pd.DataFrame({
            "Spot Price": spot_range,
            "Option Value": option_values,
            "Delta": deltas,
        })
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Option Value vs. Spot Price", "Delta vs. Spot Price"),
            vertical_spacing=0.15,
        )
        
        fig.add_trace(
            go.Scatter(x=sensitivity_df["Spot Price"], y=sensitivity_df["Option Value"],
                      mode="lines", name="Option Value", line=dict(color="steelblue")),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=sensitivity_df["Spot Price"], y=sensitivity_df["Delta"],
                      mode="lines", name="Delta", line=dict(color="orange")),
            row=2, col=1
        )
        
        fig.add_vline(x=spot_price, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_vline(x=spot_price, line_dash="dash", line_color="red", row=2, col=1)
        
        fig.update_xaxes(title_text="Spot Price ($)", row=2, col=1)
        fig.update_yaxes(title_text="Option Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Delta", row=2, col=1)
        
        fig.update_layout(height=600, template="plotly_white", showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif st.session_state.option_results:
        components.warning_message("Greeks are only available for Black-Scholes and Bachelier pricing.")
    else:
        components.info_message("Price option using Black-Scholes or Bachelier to see Greeks.")

with tab3:
    st.header("Payoff Diagram")
    
    # Generate payoff diagram
    spot_range = np.linspace(max(strike_price * 0.5, 1), strike_price * 1.5, 100)
    
    if option_type == "call":
        payoff_intrinsic = np.maximum(spot_range - strike_price, 0)
    else:  # put
        payoff_intrinsic = np.maximum(strike_price - spot_range, 0)
    
    if st.session_state.option_results:
        option_price = st.session_state.option_results["price"]
        payoff_net = payoff_intrinsic - option_price
    else:
        option_price = 0
        payoff_net = payoff_intrinsic
    
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Intrinsic value at expiration
    fig.add_trace(go.Scatter(
        x=spot_range,
        y=payoff_intrinsic,
        mode="lines",
        name="Payoff at Expiration",
        line=dict(color="steelblue", width=2),
    ))
    
    if st.session_state.option_results:
        # Net profit/loss
        fig.add_trace(go.Scatter(
            x=spot_range,
            y=payoff_net,
            mode="lines",
            name="Net P&L (incl. premium)",
            line=dict(color="green", width=2, dash="dash"),
        ))
    
    # Breakeven and strike lines
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=strike_price, line_dash="dash", line_color="red",
                  annotation_text=f"Strike: ${strike_price:.2f}", annotation_position="top")
    
    if st.session_state.option_results:
        if option_type == "call":
            breakeven = strike_price + option_price
        else:
            breakeven = strike_price - option_price
        
        fig.add_vline(x=breakeven, line_dash="dash", line_color="orange",
                      annotation_text=f"B/E: ${breakeven:.2f}", annotation_position="bottom")
    
    fig.update_layout(
        title=f"{option_type.upper()} Option Payoff Diagram",
        xaxis_title="Spot Price at Expiration ($)",
        yaxis_title="Profit/Loss ($)",
        height=500,
        template="plotly_white",
        hovermode="x unified",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Payoff table
    if st.session_state.option_results:
        st.subheader("Key Levels")
        
        if option_type == "call":
            breakeven = strike_price + option_price
            max_loss = option_price
            max_profit = "Unlimited"
        else:
            breakeven = strike_price - option_price
            max_loss = option_price
            max_profit = f"${strike_price - option_price:.2f}"
        
        levels_df = pd.DataFrame({
            "Metric": ["Strike Price", "Breakeven", "Max Loss", "Max Profit", "Premium Paid"],
            "Value": [
                f"${strike_price:.2f}",
                f"${breakeven:.2f}",
                f"${max_loss:.2f}",
                max_profit,
                f"${option_price:.2f}",
            ],
        })
        
        st.dataframe(levels_df, hide_index=True, use_container_width=True)

with tab4:
    st.header("Implied Volatility Calculator")
    
    st.markdown("Calculate implied volatility from observed option prices.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        observed_price = st.number_input(
            "Observed Option Price ($)",
            min_value=0.01,
            max_value=spot_price,
            value=max(0.01, 10.0 if not st.session_state.option_results else st.session_state.option_results["price"]),
            step=0.01,
        )
    
    with col2:
        initial_guess = st.slider(
            "Initial Volatility Guess (%)",
            min_value=1,
            max_value=200,
            value=20,
            step=1,
        ) / 100
    
    calc_iv_button = st.button("Calculate Implied Vol")
    
    if calc_iv_button:
        with st.spinner("Calculating implied volatility..."):
            try:
                # Convert option_type string to enum
                opt_type_enum = OptionType.CALL if option_type == "call" else OptionType.PUT
                
                iv_result = implied_volatility(
                    option_price=observed_price,
                    spot=spot_price,
                    strike=strike_price,
                    T=time_to_expiry,
                    r=risk_free_rate,
                    option_type=opt_type_enum,
                    q=dividend_yield,
                    initial_guess=initial_guess,
                )
                
                components.success_message("Implied volatility calculated!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Implied Volatility", f"{iv_result['implied_volatility']*100:.2f}%")
                
                with col2:
                    st.metric("Iterations", iv_result.get("iterations", "N/A"))
                
                with col3:
                    error = iv_result.get("convergence_error", 0)
                    st.metric("Error", f"${error:.4f}")
                
                # Compare with input volatility
                if abs(iv_result['implied_volatility'] - volatility) > 0.01:
                    st.info(
                        f"ℹ️ Implied vol ({iv_result['implied_volatility']*100:.2f}%) differs from "
                        f"input vol ({volatility*100:.2f}%). This is expected if observed price ≠ theoretical price."
                    )
                
            except Exception as e:
                components.error_message(f"Failed to calculate implied volatility: {str(e)}")

# ============================================================================
# Tab 5: Tail Risk Distribution Morph Engine
# ============================================================================
with tab5:
    st.header("📉 Tail Risk Distribution Morph Engine")
    
    st.markdown("""
    Visualize how return distributions morph from normal (Gaussian) to heavy-tailed (Student-t) under market stress.
    
    **Key Concepts:**
    - **Gaussian (Normal)**: Thin tails, typical in calm markets
    - **Student-t**: Fat tails, captures extreme events (crashes, spikes)
    - **Morphing**: Shows distribution evolution as stress increases
    - **VaR**: Value at Risk - potential loss at 5% probability
    - **ES**: Expected Shortfall - average loss beyond VaR
    """)
    
    # Parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tail_df = st.slider(
            "Degrees of Freedom",
            min_value=2.0,
            max_value=30.0,
            value=8.0,
            step=1.0,
            help="Lower values = fatter tails (more extreme events)"
        )
    
    with col2:
        tail_vol = st.slider(
            "Base Volatility",
            min_value=0.01,
            max_value=0.15,
            value=0.05,
            step=0.01,
            help="Base volatility level (annualized)"
        )
    
    with col3:
        stress_mult = st.slider(
            "Stress Multiplier",
            min_value=1.0,
            max_value=3.0,
            value=2.0,
            step=0.1,
            help="How much volatility increases under stress"
        )
    
    time_steps = st.slider(
        "Time Steps (stress progression)",
        min_value=10,
        max_value=50,
        value=25,
        step=5,
        help="Number of steps from normal to stressed distribution"
    )
    
    if st.button("Generate Tail Risk Morphing", type="primary"):
        with st.spinner("Simulating distribution morphing..."):
            from scipy.stats import norm, t as student_t
            import plotly.graph_objects as go
            
            # Helper functions
            def generate_distribution(x, t_idx, n_steps, base_vol, base_df, stress_mult):
                alpha = t_idx / (n_steps - 1)
                morph_df = (1 - alpha) * 1e6 + alpha * base_df
                morph_vol = base_vol * (1 + alpha * (stress_mult - 1))
                
                if morph_df > 1000:
                    pdf = norm.pdf(x, loc=0, scale=morph_vol)
                else:
                    pdf = student_t.pdf(x / morph_vol, df=morph_df) / morph_vol
                
                pdf = np.clip(pdf, 1e-12, 1e2)
                return pdf, morph_df, morph_vol
            
            def compute_tail_metrics(x, pdf, alpha=0.05):
                dx = x[1] - x[0]
                cdf = np.cumsum(pdf) * dx
                cdf = np.clip(cdf, 0, 1)
                
                try:
                    var_idx = np.where(cdf >= alpha)[0][0]
                except IndexError:
                    var_idx = 0
                
                var = x[var_idx]
                es = np.sum(pdf[x <= var] * x[x <= var]) / np.sum(pdf[x <= var]) if np.sum(pdf[x <= var]) > 0 else var
                return var, es
            
            # X grid: returns
            x = np.linspace(-0.2, 0.2, 400)
            time_grid = np.arange(time_steps)
            z_grid = np.zeros((time_steps, len(x)))
            var_grid = np.zeros(time_steps)
            es_grid = np.zeros(time_steps)
            df_grid = np.zeros(time_steps)
            vol_grid = np.zeros(time_steps)
            
            for t_idx in range(time_steps):
                pdf, morph_df, morph_vol = generate_distribution(x, t_idx, time_steps, tail_vol, tail_df, stress_mult)
                z_grid[t_idx, :] = pdf
                var, es = compute_tail_metrics(x, pdf, alpha=0.05)
                var_grid[t_idx] = var
                es_grid[t_idx] = es
                df_grid[t_idx] = morph_df
                vol_grid[t_idx] = morph_vol
            
            # Metrics display
            met1, met2, met3, met4 = st.columns(4)
            met1.metric("Final VaR (5%)", f"{var_grid[-1]:.4f}")
            met2.metric("Final Expected Shortfall", f"{es_grid[-1]:.4f}")
            met3.metric("Final Volatility", f"{vol_grid[-1]:.4f}")
            met4.metric("Final Degrees of Freedom", f"{df_grid[-1]:.2f}")
            
            # 3D Surface Plot
            fig = go.Figure()
            
            fig.add_trace(go.Surface(
                x=x,
                y=time_grid,
                z=z_grid,
                colorscale="Viridis",
                showscale=True,
                opacity=0.95,
                name="Density Surface"
            ))
            
            # VaR overlay
            fig.add_trace(go.Scatter3d(
                x=var_grid,
                y=time_grid,
                z=[np.interp(v, x, z) for v, z in zip(var_grid, z_grid)],
                mode="lines",
                line=dict(color="red", width=6),
                name="VaR (5%)"
            ))
            
            fig.update_layout(
                title="3D Tail Risk Distribution Morphing",
                scene=dict(
                    xaxis_title="Return Magnitude",
                    yaxis_title="Stress Step",
                    zaxis_title="Probability Density",
                ),
                height=700
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrics table
            with st.expander("📊 Show Detailed Metrics"):
                df_metrics = pd.DataFrame({
                    "Time Step": time_grid,
                    "VaR (5%)": var_grid,
                    "Expected Shortfall": es_grid,
                    "Volatility": vol_grid,
                    "Degrees of Freedom": df_grid
                })
                st.dataframe(df_metrics, use_container_width=True)
                
                # Additional visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    import plotly.express as px
                    fig_var = px.line(df_metrics, x="Time Step", y=["VaR (5%)", "Expected Shortfall"],
                                     title="VaR and ES Over Time")
                    st.plotly_chart(fig_var, use_container_width=True)
                
                with col2:
                    fig_vol = px.line(df_metrics, x="Time Step", y="Volatility",
                                     title="Volatility Evolution")
                    st.plotly_chart(fig_vol, use_container_width=True)

# ============================================================================
# Tab 6: Volatility Shockwave Simulator
# ============================================================================
with tab6:
    st.header("🌊 Volatility Shockwave Simulator")
    
    st.markdown("""
    Simulate random volatility shockwaves and their impact on stock prices and option values.
    
    **Key Concepts:**
    - **Volatility Regime Switching**: Markets alternate between low-vol and high-vol periods
    - **Shockwaves**: Sudden spikes in volatility (e.g., during news events, crises)
    - **Impact on Options**: Higher volatility → higher option prices (via Vega)
    - **Dynamic Hedging**: Positions need to be adjusted as volatility changes
    """)
    
    # Parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        S0_shock = st.number_input(
            "Initial Stock Price ($)",
            min_value=10.0,
            max_value=1000.0,
            value=100.0,
            step=10.0
        )
    
    with col2:
        sigma_low = st.slider(
            "Low Volatility",
            min_value=0.05,
            max_value=0.50,
            value=0.20,
            step=0.05,
            help="Volatility in calm markets"
        )
    
    with col3:
        sigma_high = st.slider(
            "High Volatility",
            min_value=0.30,
            max_value=1.50,
            value=0.60,
            step=0.05,
            help="Volatility during stressed markets"
        )
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        switch_prob = st.slider(
            "Regime Switch Probability",
            min_value=0.01,
            max_value=0.20,
            value=0.03,
            step=0.01,
            help="Probability of switching between regimes"
        )
    
    with col5:
        shock_prob = st.slider(
            "Shockwave Probability",
            min_value=0.001,
            max_value=0.050,
            value=0.01,
            step=0.001,
            help="Probability of sudden volatility spike"
        )
    
    with col6:
        shock_magnitude = st.slider(
            "Shock Magnitude",
            min_value=1.5,
            max_value=5.0,
            value=2.5,
            step=0.5,
            help="Multiplier for volatility during shocks"
        )
    
    sim_steps = st.slider(
        "Simulation Steps",
        min_value=100,
        max_value=500,
        value=250,
        step=50
    )
    
    if st.button("Run Shockwave Simulation", type="primary"):
        with st.spinner("Simulating volatility shockwaves..."):
            from quantlib_pro.options.black_scholes import price as black_scholes_price
            
            # Shockwave simulator
            class VolatilityShockwaveSimulator:
                def __init__(self, S0, mu, sigma_low, sigma_high, T, dt, switch_prob, shock_prob, shock_magnitude):
                    self.S0 = S0
                    self.mu = mu
                    self.sigma_low = sigma_low
                    self.sigma_high = sigma_high
                    self.T = T
                    self.dt = dt
                    self.switch_prob = switch_prob
                    self.shock_prob = shock_prob
                    self.shock_magnitude = shock_magnitude
                    self.reset()
                
                def reset(self):
                    self.time = np.arange(0, self.T, self.dt)
                    self.prices = [self.S0]
                    self.volatility = [self.sigma_low]
                    self.shockwaves = [False]
                    self.current_sigma = self.sigma_low
                
                def step(self):
                    last_price = self.prices[-1]
                    
                    # Volatility regime switch
                    if np.random.rand() < self.switch_prob:
                        self.current_sigma = self.sigma_high if self.current_sigma == self.sigma_low else self.sigma_low
                    
                    # Shockwave event
                    shock = False
                    if np.random.rand() < self.shock_prob:
                        self.current_sigma *= self.shock_magnitude
                        shock = True
                    
                    # Geometric Brownian Motion
                    dW = np.random.normal(0, np.sqrt(self.dt))
                    new_price = last_price * np.exp((self.mu - 0.5 * self.current_sigma ** 2) * self.dt + 
                                                    self.current_sigma * dW)
                    
                    self.prices.append(new_price)
                    self.volatility.append(self.current_sigma)
                    self.shockwaves.append(shock)
                    
                    # Reset shockwave
                    if shock:
                        self.current_sigma /= self.shock_magnitude
            
            # Run simulation
            T = 2.0
            dt = T / sim_steps
            mu = 0.05  # drift
            K = S0_shock  # ATM option
            r = risk_free_rate
            
            sim = VolatilityShockwaveSimulator(S0_shock, mu, sigma_low, sigma_high, T, dt, 
                                              switch_prob, shock_prob, shock_magnitude)
            
            for _ in range(sim_steps):
                sim.step()
            
            # Calculate option prices
            option_prices = []
            deltas = []
            vegas = []
            
            for i, (price, vol) in enumerate(zip(sim.prices, sim.volatility)):
                t_remain = T - i * dt
                if t_remain > 0.001:
                    opt_price = black_scholes_price(
                        S=price,
                        K=K,
                        T=t_remain,
                        r=r,
                        sigma=vol,
                        option_type=OptionType.CALL
                    )
                    
                    # Approximate Greeks
                    h = 0.01
                    delta_approx = (black_scholes_price(price + h, K, t_remain, r, vol, OptionType.CALL) -
                                  black_scholes_price(price - h, K, t_remain, r, vol, OptionType.CALL)) / (2 * h)
                    
                    vega_approx = (black_scholes_price(price, K, t_remain, r, vol + 0.01, OptionType.CALL) -
                                 black_scholes_price(price, K, t_remain, r, vol - 0.01, OptionType.CALL)) / 2
                    
                    option_prices.append(opt_price)
                    deltas.append(delta_approx)
                    vegas.append(vega_approx)
                else:
                    option_prices.append(max(price - K, 0))
                    deltas.append(1.0 if price > K else 0.0)
                    vegas.append(0.0)
            
            # Display results
            shock_count = sum(sim.shockwaves)
            st.info(f"🌊 Detected **{shock_count}** volatility shockwaves during simulation")
            
            # Create visualizations
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=("Stock Price", "Option Price", "Volatility"),
                vertical_spacing=0.08,
                row_heights=[0.35, 0.35, 0.30]
            )
            
            # Stock price with shockwave highlights
            x_vals = list(range(len(sim.prices)))
            fig.add_trace(
                go.Scatter(x=x_vals, y=sim.prices, mode='lines', name='Stock Price',
                          line=dict(color='cyan', width=2)),
                row=1, col=1
            )
            
            # Highlight shockwaves
            for i, is_shock in enumerate(sim.shockwaves):
                if is_shock:
                    fig.add_vrect(
                        x0=max(0, i-2), x1=min(len(sim.prices), i+2),
                        fillcolor="red", opacity=0.2,
                        layer="below", line_width=0,
                        row=1, col=1
                    )
            
            # Option price
            fig.add_trace(
                go.Scatter(x=x_vals, y=option_prices, mode='lines', name='Option Price',
                          line=dict(color='orange', width=2)),
                row=2, col=1
            )
            
            # Volatility
            fig.add_trace(
                go.Scatter(x=x_vals, y=sim.volatility, mode='lines', name='Volatility',
                          line=dict(color='magenta', width=2)),
                row=3, col=1
            )
            
            fig.update_layout(height=900, showlegend=True, title="Volatility Shockwave Simulation Results")
            fig.update_xaxes(title_text="Time Step", row=3, col=1)
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Option Value ($)", row=2, col=1)
            fig.update_yaxes(title_text="Volatility", row=3, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Greeks display
            with st.expander("📈 View Greeks Evolution"):
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_delta = go.Figure()
                    fig_delta.add_trace(go.Scatter(x=x_vals, y=deltas, mode='lines', name='Delta'))
                    fig_delta.update_layout(title="Delta Over Time", xaxis_title="Step", yaxis_title="Delta")
                    st.plotly_chart(fig_delta, use_container_width=True)
                
                with col2:
                    fig_vega = go.Figure()
                    fig_vega.add_trace(go.Scatter(x=x_vals, y=vegas, mode='lines', name='Vega', 
                                                  line=dict(color='green')))
                    fig_vega.update_layout(title="Vega Over Time", xaxis_title="Step", yaxis_title="Vega")
                    st.plotly_chart(fig_vega, use_container_width=True)
                
                # Summary statistics
                st.subheader("Summary Statistics")
                summary_df = pd.DataFrame({
                    "Metric": ["Avg Stock Price", "Avg Option Price", "Avg Volatility", "Max Volatility", 
                              "Min Stock Price", "Max Stock Price", "Shockwave Count"],
                    "Value": [
                        f"${np.mean(sim.prices):.2f}",
                        f"${np.mean(option_prices):.2f}",
                        f"{np.mean(sim.volatility):.2%}",
                        f"{np.max(sim.volatility):.2%}",
                        f"${np.min(sim.prices):.2f}",
                        f"${np.max(sim.prices):.2f}",
                        str(shock_count)
                    ]
                })
                st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ============================================================================
# Tab 7: Black-Scholes Visual Explainer
# ============================================================================
with tab7:
    st.header("💹 Black-Scholes Visual Explainer")
    
    st.markdown("""
    **Interactive Black-Scholes Model** - Visualize option prices and Greeks in 3D space.
    See how option value responds to changes in stock price and volatility.
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("⚙️ Model Parameters")
        
        bs_S = st.slider(
            "Stock Price (S)",
            min_value=10,
            max_value=300,
            value=100,
            step=1,
            key="bs_S"
        )
        
        bs_K = st.slider(
            "Strike Price (K)",
            min_value=10,
            max_value=300,
            value=100,
            step=1,
            key="bs_K"
        )
        
        bs_sigma = st.slider(
            "Volatility (σ, %)",
            min_value=1,
            max_value=100,
            value=20,
            step=1,
            key="bs_sigma"
        ) / 100
        
        bs_T = st.slider(
            "Time to Maturity (days)",
            min_value=1,
            max_value=365,
            value=30,
            step=1,
            key="bs_T"
        ) / 365
        
        bs_r = st.slider(
            "Risk-Free Rate (r, %)",
            min_value=0,
            max_value=15,
            value=2,
            step=1,
            key="bs_r"
        ) / 100
        
        bs_option_type = st.radio(
            "Option Type",
            ["call", "put"],
            horizontal=True,
            key="bs_option_type"
        )
    
    with col1:
        # Helper functions for Black-Scholes
        def bs_d1(S, K, T, r, sigma):
            return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        
        def bs_d2(S, K, T, r, sigma):
            return bs_d1(S, K, T, r, sigma) - sigma * np.sqrt(T)
        
        def bs_price(S, K, T, r, sigma, option_type='call'):
            from scipy.stats import norm
            D1 = bs_d1(S, K, T, r, sigma)
            D2 = bs_d2(S, K, T, r, sigma)
            if option_type == 'call':
                return S * norm.cdf(D1) - K * np.exp(-r * T) * norm.cdf(D2)
            else:
                return K * np.exp(-r * T) * norm.cdf(-D2) - S * norm.cdf(-D1)
        
        def bs_delta(S, K, T, r, sigma, option_type='call'):
            from scipy.stats import norm
            D1 = bs_d1(S, K, T, r, sigma)
            if option_type == 'call':
                return norm.cdf(D1)
            else:
                return norm.cdf(D1) - 1
        
        def bs_gamma(S, K, T, r, sigma):
            from scipy.stats import norm
            D1 = bs_d1(S, K, T, r, sigma)
            return norm.pdf(D1) / (S * sigma * np.sqrt(T))
        
        def bs_vega(S, K, T, r, sigma):
            from scipy.stats import norm
            D1 = bs_d1(S, K, T, r, sigma)
            return S * norm.pdf(D1) * np.sqrt(T) / 100
        
        def bs_theta(S, K, T, r, sigma, option_type='call'):
            from scipy.stats import norm
            D1 = bs_d1(S, K, T, r, sigma)
            D2 = bs_d2(S, K, T, r, sigma)
            if option_type == 'call':
                return (-S * norm.pdf(D1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(D2)) / 365
            else:
                return (-S * norm.pdf(D1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-D2)) / 365
        
        def bs_rho(S, K, T, r, sigma, option_type='call'):
            from scipy.stats import norm
            D2 = bs_d2(S, K, T, r, sigma)
            if option_type == 'call':
                return K * T * np.exp(-r * T) * norm.cdf(D2) / 100
            else:
                return -K * T * np.exp(-r * T) * norm.cdf(-D2) / 100
        
        # Calculate price and Greeks
        bs_price_val = bs_price(bs_S, bs_K, bs_T, bs_r, bs_sigma, bs_option_type)
        bs_delta_val = bs_delta(bs_S, bs_K, bs_T, bs_r, bs_sigma, bs_option_type)
        bs_gamma_val = bs_gamma(bs_S, bs_K, bs_T, bs_r, bs_sigma)
        bs_vega_val = bs_vega(bs_S, bs_K, bs_T, bs_r, bs_sigma)
        bs_theta_val = bs_theta(bs_S, bs_K, bs_T, bs_r, bs_sigma, bs_option_type)
        bs_rho_val = bs_rho(bs_S, bs_K, bs_T, bs_r, bs_sigma, bs_option_type)
        
        # Display price prominently
        st.markdown(
            f'<div style="font-size: 3em; font-weight: bold; color: #00e6e6; '
            f'text-align: center; padding: 20px;">{bs_option_type.capitalize()} '
            f'Price: ${bs_price_val:.2f}</div>',
            unsafe_allow_html=True
        )
        
        # Display Greeks
        st.subheader("📊 Greeks Dashboard")
        
        greek_col1, greek_col2, greek_col3, greek_col4, greek_col5 = st.columns(5)
        
        with greek_col1:
            st.metric("Delta (Δ)", f"{bs_delta_val:.4f}", help="Rate of change of option price with respect to stock price")
        
        with greek_col2:
            st.metric("Gamma (Γ)", f"{bs_gamma_val:.4f}", help="Rate of change of delta with respect to stock price")
        
        with greek_col3:
            st.metric("Vega (ν)", f"{bs_vega_val:.4f}", help="Sensitivity to volatility changes")
        
        with greek_col4:
            st.metric("Theta (Θ)", f"{bs_theta_val:.4f}", help="Time decay of option value")
        
        with greek_col5:
            st.metric("Rho (ρ)", f"{bs_rho_val:.4f}", help="Sensitivity to interest rate changes")
        
        # 3D Surface Plot: S vs sigma vs Price
        st.subheader("🌐 3D Price Surface")
        
        S_range = np.linspace(10, 300, 40)
        sigma_range = np.linspace(0.01, 1, 40)
        S_grid, sigma_grid = np.meshgrid(S_range, sigma_range)
        
        # Vectorized price calculation
        price_grid = bs_price(S_grid, bs_K, bs_T, bs_r, sigma_grid, bs_option_type)
        
        fig_3d = go.Figure(data=[go.Surface(
            x=S_range,
            y=sigma_range * 100,
            z=price_grid,
            colorscale='Viridis',
            showscale=True,
            opacity=0.95
        )])
        
        fig_3d.update_layout(
            title=f"{bs_option_type.capitalize()} Price Surface",
            scene=dict(
                xaxis_title='Stock Price (S)',
                yaxis_title='Volatility (%)',
                zaxis_title='Option Price ($)',
                bgcolor='black',
                xaxis=dict(backgroundcolor='black', gridcolor='#333'),
                yaxis=dict(backgroundcolor='black', gridcolor='#333'),
                zaxis=dict(backgroundcolor='black', gridcolor='#333')
            ),
            template='plotly_dark',
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # Delta curve
        st.subheader("📈 Delta vs Stock Price")
        
        delta_curve = [bs_delta(s, bs_K, bs_T, bs_r, bs_sigma, bs_option_type) for s in S_range]
        
        fig_delta = go.Figure()
        
        fig_delta.add_trace(go.Scatter(
            x=S_range,
            y=delta_curve,
            mode='lines',
            line=dict(color='#00f2fe', width=4),
            name='Delta'
        ))
        
        # Add strike price line
        fig_delta.add_vline(
            x=bs_K,
            line_dash="dash",
            line_color="red",
            annotation_text="Strike"
        )
        
        # Add current stock price line
        fig_delta.add_vline(
            x=bs_S,
            line_dash="dot",
            line_color="yellow",
            annotation_text="Current S"
        )
        
        fig_delta.update_layout(
            title="Delta Curve",
            xaxis_title="Stock Price (S)",
            yaxis_title="Delta",
            template='plotly_dark',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_delta, use_container_width=True)
        
        # Interpretation
        st.subheader("🎓 Interpretation")
        
        col1a, col2a = st.columns(2)
        
        with col1a:
            st.markdown("**Moneyness:**")
            if bs_S > bs_K:
                if bs_option_type == 'call':
                    st.success("✅ In-the-Money (ITM) - Call has intrinsic value")
                else:
                    st.error("❌ Out-of-the-Money (OTM) - Put has no intrinsic value")
            elif bs_S < bs_K:
                if bs_option_type == 'call':
                    st.error("❌ Out-of-the-Money (OTM) - Call has no intrinsic value")
                else:
                    st.success("✅ In-the-Money (ITM) - Put has intrinsic value")
            else:
                st.info("⚖️ At-the-Money (ATM)")
        
        with col2a:
            st.markdown("**Time Value:**")
            if bs_option_type == 'call':
                intrinsic = max(0, bs_S - bs_K)
            else:
                intrinsic = max(0, bs_K - bs_S)
            
            time_value = bs_price_val - intrinsic
            
            st.write(f"• Intrinsic Value: ${intrinsic:.2f}")
            st.write(f"• Time Value: ${time_value:.2f}")
            st.write(f"• Total Premium: ${bs_price_val:.2f}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Options Pricing powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
