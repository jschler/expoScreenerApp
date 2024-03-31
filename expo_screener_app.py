import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime,timedelta

def calculate_moving_average(data, window=20):
    return data.ewm(span=window, adjust=False).mean()

def fetch_data(symbols,period="30d",interval="1d",start=None,end=None):
    try:
        data = yf.download(symbols, period=period,interval=interval,group_by ='ticker',start=start,end=end)
        return data
    except Exception as e:
        return pd.DataFrame()
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

    # Set the x-axis limits to display only the last 30 data points
    last_30_index = len(ohlc_data) - 30
    ax.set_xlim(last_30_index, len(ohlc_data))

    ax.set_title(f"{selected_symbol} Stock Price (Candlestick)")
    st.pyplot(fig)

def ind4stock(stock,sp500L,nasdaqL,russell2000L):
    stock=stock.lower()
    ret=""
    if stock in sp500L:
        ret+= "SP500, "
    if stock in nasdaqL:
        ret+= "NASDAQ, "
    if stock in russell2000L:
        ret+=  "RUSSELL2000, "

    return ret

def main():
    sp500=pd.read_csv("./sp500.csv")
    sp500L=[l.lower() for l in sp500["stock"].tolist()]
    nasdaq=pd.read_csv("./nasdaq100.csv")
    nasdaqL=[l.lower() for l in nasdaq["stock"].tolist()]
    russell2000=pd.read_csv("./russell2000.csv")
    russell2000L=[l.lower() for l in russell2000["stock"].tolist()]

    st.title("Stock Data Screener")

    # Date picker for simulation
    simulation_date = st.date_input("Select a date for simulation", datetime.today())

    if 'all_data' not in st.session_state:
        st.session_state.all_data = {}
        st.session_state.trigger_symbols = []

    # Initial stock list
    # initial_stock_list="AAPL,GOOGL,MSFT"
    #initial_stock_list=("SPY,QQQ,IWM,fngu, soxl, tna, fas, arkk, arkb,MSFT,AAPL,NVDA,AMZN,GOOGL,GOOG,META,TSM,TSLA,WMT,XOM,BAC,AMD,KO,DIS,WFC,CSCO,BABA,INTC,VZ,CMCSA,UBER,PFE,ARM,NEE,T,MU,C,BMY,SHOP,CVS,PBR,MO,SLB,CSX,PYPL,FCX,COIN,ITUB,MRVL,NU,PLTR,VALE,ET,SQ,F,GM,KMI,ABEV,NEM,KVUE,JD,CVE,PCG,BCS,CPNG,BBD,GOLD,DKNG,HPE,CCL,WBD,NOK,HBAN,SNAP,ERIC,WBA,HOOD,CNHI,SIRI,KEY,PATH,GRAB,AFRM,RIVN,U,AAL,XPEV,NCLH,PARA,LYFT,SWN,NIO,SOFI,KGC")
    initial_stock_list=("SPY,QQQ,IWM,fngu, soxl, tna, fas, arkk, arkb,MSFT,AAPL,NVDA,GOOG,GOOGL,AMZN,META,TSM,TSLA,WMT,XOM,BAC,AMD,KO,DIS,WFC,CSCO,INTC,BABA,VZ,CMCSA,UBER,PFE,NEE,MU,ARM,T,C,BMY,CVS,PBR,SLB,MO,CSX,PYPL,FCX,COIN,ITUB,MRVL,NU,ET,F,GM,SQ,VALE,PLTR,NEM,KVUE,KMI,JD,CVE,PCG,BCS,CPNG,GOLD,HPE,DKNG,WBD,CCL,HBAN,SNAP,WBA,ERIC,HOOD,CNHI,KEY,PATH,AFRM,RIVN,U,AAL,NCLH,SWN,PARA,LYFT,XPEV,KGC,SOFI,CHWY,AGNC,MARA,M,RIG,COCSF,CLSK,RIOT,RUN,JBLU,SOUN")
    symbols_input = st.text_input("Enter stock symbols, separated by commas",initial_stock_list )
    symbols_input = symbols_input.lower()
    symbols = symbols_input.split(',')

    if st.button("Screen"):
        for symbol in symbols:
            data = fetch_data(symbol, period="60d",end=simulation_date,start=simulation_date-timedelta(days=60))
            if data.empty:
                st.error(f"No data found for symbol: {symbol}. Please check the symbol and try again.")
                continue
            st.session_state.all_data[symbol] = data

        #st.session_state.all_data = {symbol: fetch_data(symbol, period="30d") for symbol in symbols}
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
                    "SP500": symbol in sp500L,
                    "Nasdaq": symbol in nasdaqL,
                    "Russell2000": symbol in russell2000L,
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
