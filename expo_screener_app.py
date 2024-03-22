import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt

def calculate_moving_average(data, window=20):
    return data.ewm(span=window, adjust=False).mean()

def check_trigger(data):
    # Ensure the data is sorted in ascending order
    data = data.sort_index(ascending=True)

    # Calculate EMA10 and EMA20
    ema10 = calculate_moving_average(data['Close'], 10)
    ema20 = calculate_moving_average(data['Close'], 20)

    # Condition 1: EMA10 > EMA20 on the last day
    condition1 = ema10.iloc[-1] > ema20.iloc[-1]

    dayY = -1
    dayZ = -1

    # Iterate to find days Y and Z
    for i in range(1, 11):  # Loop over last 10 days
        if dayZ == -1 and data['Close'].iloc[-i] > data['Open'].iloc[-i] and dayY == -1:
            dayY = i
        if dayY != -1 and data['Low'].iloc[-i] < ema10.iloc[-i] and dayZ == -1 and i > dayY:
            dayZ = i
        if dayZ == -1 and data['Close'].iloc[-i] > data['Open'].iloc[-i]:  # Update dayY if a new green candlestick is found
            dayY = i

    # Conditions based on day Y and Z
    condition2and3 = dayY <= 2
    condition5 = dayZ <= 10 and dayZ > dayY

    # Condition 6: No green candlestick between Z and Y
    condition6 = True
    if dayY > 0 and dayZ > 0 and dayZ - dayY > 1:
        for j in range(dayY + 1, dayZ):
            if data['Close'].iloc[-j] > data['Open'].iloc[-j]:
                condition6 = False
    else:
        condition6 = True

    # Condition 8: From day Z+1 backwards, EMA10 should be higher than EMA20
    condition8 = True
    for z in range(1, dayZ + 2):
        if ema20.iloc[-z] >= ema10.iloc[-z]:
            condition8 = False
            break

    # Final condition
    all_conditions = condition1 and condition2and3 and condition5 and condition6 and condition8

    #return all_conditions
    return all_conditions, ema10.iloc[-1], ema20.iloc[-1]

def plot_data(selected_symbol, data):
    # Filter data for the selected symbol
    ohlc_data = data[['Open', 'High', 'Low', 'Close']]

    # Rename columns to match mplfinance requirements
    ohlc_data.columns = ['Open', 'High', 'Low', 'Close']

    # Define moving averages
    ema_colors = {'10': 'darkgreen', '20': 'orange'}

    # Create the candlestick chart
    fig, ax = plt.subplots(figsize=(10, 5))
    mpf.plot(ohlc_data, type='candle', ax=ax, style='yahoo',
             show_nontrading=False,
             update_width_config={'candle_linewidth': 1.0, 'candle_width': 0.8},
             ema=(10,20),  # 20-day exponential moving average
             volume=False,
             mavcolors=[ema_colors['10'], ema_colors['20']],
             ylabel='Price')

    ax.plot([], [], color=ema_colors['10'], label='10-Day EMA')
    ax.plot([], [], color=ema_colors['20'], label='20-Day EMA')
    ax.legend()

    ax.set_title(f"{selected_symbol} Stock Price (Candlestick)")
    st.pyplot(fig)

def main():
    st.title("Stock Data Screener")

    if 'all_data' not in st.session_state:
        st.session_state.all_data = {}
        st.session_state.trigger_symbols = []

    symbols_input = st.text_input("Enter stock symbols, separated by commas", "AAPL,GOOGL,MSFT")
    symbols = symbols_input.split(',')

    if st.button("Screen"):
        st.session_state.all_data = {symbol: yf.download(symbol, period="30d") for symbol in symbols}
        st.session_state.trigger_symbols = []

        for symbol, data in st.session_state.all_data.items():
            trigger, ema10, ema20 = check_trigger(data)
            if True: #trigger:
                last_row = data.iloc[-1]
                st.session_state.trigger_symbols.append({
                    'Symbol': symbol,
                    'Open': last_row['Open'],
                    'Close': last_row['Close'],
                    'High': last_row['High'],
                    'Low': last_row['Low'],
                    'Volume': last_row['Volume'],
                    'EMA10': ema10,
                    'EMA20': ema20,
                    "Triggered": trigger
                })

    if st.session_state.trigger_symbols:
        st.write("Triggered Symbols:")
        trigger_df = pd.DataFrame(st.session_state.trigger_symbols)
        st.dataframe(trigger_df)

        # Layout for button and dropdown
        col1, col2 = st.columns([1, 2])
        if col2.button("Show Chart"):
            selected_symbol = col1.selectbox('Select a symbol to view chart',
                                             [row['Symbol'] for row in st.session_state.trigger_symbols])
            data = st.session_state.all_data[selected_symbol]
            plot_data(selected_symbol,data)
        else:
            selected_symbol = col1.selectbox('Select a symbol to view chart',
                                             [row['Symbol'] for row in st.session_state.trigger_symbols])

        # Add chart button for each symbol
        # for index, row in trigger_df.iterrows():
        #     if st.button(f"Show Chart for {row['Symbol']}", key=row['Symbol']):
        #         data = st.session_state.all_data[row['Symbol']]
        #         plot_data(row['Symbol'],data)
        #
        # # for index, row in trigger_df.iterrows():
        #     cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
        #     cols[0].write(row['Symbol'])
        #     if cols[-1].button('Show Chart', key=row['Symbol']):
        #         data = st.session_state.all_data[row['Symbol']]
        #         plot_data(row['Symbol'],data)

if __name__ == "__main__":
    main()

#%%
