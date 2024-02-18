# -*- coding: utf-8 -*-
"""Financial indicators .ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xRf9lsnH_7Hy10yUATyP47FLNXsY6fAy
"""

import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import streamlit as st
import plotly
import inotify

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Save the current day
timestamp = pd.Timestamp(datetime.datetime(2020,10,10))
today = timestamp.today().strftime("%Y-%m-%d")

def load_data(ticker: str, start_date="2000-01-01", end_date=today, bollinger_sma_window=20,
              rsi_window=14, k_period=14, d_period=3):

  df = yf.download(ticker, start_date, end_date)

  if len(df) == 0:
    print('Enter a valid ticker')
    return None

  df = df.dropna()

  #Create columns for the Bollinger bands calculations
  df['SMA'] = df['Close'].rolling(bollinger_sma_window).mean()
  df['std'] = df['Close'].rolling(bollinger_sma_window).std(ddof = 0)

  #Create columns for the RSI calculations
  df["Diff"] = df["Close"].diff(1)
  df["Gain"] = df["Diff"].clip(lower=0).round(2)
  df["Loss"] = df["Diff"].clip(upper=0).abs().round(2)

  df["Avg_Gain"] = df["Gain"].rolling(rsi_window).mean()
  df["Avg_Loss"] = df["Loss"].rolling(rsi_window).mean()
  df["RS"] = df["Avg_Gain"] / df["Avg_Loss"]
  df["RSI"] = 100 - (100 / (1 + df["RS"]))

  # Create columns for the Stochastic Oscillator

  df['H14'] = df['High'].rolling(k_period).max()
  df['L14'] = df['Low'].rolling(k_period).min()
  df['%K'] = ((df['Close'] - df['L14']) / (df['H14'] - df['L14'])) * 100
  df['%D'] = df['%K'].rolling(d_period).mean()

  return df

def plot_indicators(df):
  # Create the subplots for the Candlesticks with Bollinger bands, RSI, and SO
  sub_figs = make_subplots(rows = 3, cols = 1, shared_xaxes = True, subplot_titles = ("Daily Candlesticks with Bollinger Bands", "Relative Strength Index", "Stochastic Oscillator"),
                    horizontal_spacing = 0.05, vertical_spacing = 0.1, row_width = [0.2, 0.2, 0.6])

  # Add the Candlestick chart
  sub_figs.add_trace(go.Candlestick(x = df.index,
                             open = df['Open'],
                             high = df['High'],
                             low = df['Low'],
                             close = df['Close'], showlegend=False,
                             name = 'candlestick'),
                             row = 1, col = 1
              )
  # Add the Moving Average for the Bollinger bands
  sub_figs.add_trace(go.Scatter(x = df.index,
                         y = df['SMA'],
                         line_color = '#0018A8',
                         name = 'SMA'),
                         row = 1, col = 1
              )

  # Add the Upper and Lower bounds of the Bollinger bands
  # Upper Bound
  sub_figs.add_trace(go.Scatter(x = df.index,
                          y = df['SMA'] + (df['std'] * 2),
                          line_color = '#BFAFB2',
                          line = {'dash': 'dash'},
                          name = 'upper band',
                          opacity = 0.5),
                          row = 1, col = 1
                )

  # Lower Bound fill in between with parameter 'fill': 'tonexty'
  sub_figs.add_trace(go.Scatter(x = df.index,
                          y = df['SMA'] - (df['std'] * 2),
                          line_color = '#BFAFB2',
                          line = {'dash': 'dash'},
                          fill = 'tonexty',
                          name = 'lower band',
                          opacity = 0.5),
                          row = 1, col = 1
                )

  # Remove range slider and create date gaps so we can remove weekends from the charts
  sub_figs.update(layout_xaxis_rangeslider_visible=False)
  date_gaps = [date for date in pd.date_range(start = start_date, end = end_date) if date not in df.index.values]

  # Create the Relative Strength Index (RSI) chart
  sub_figs.add_trace(go.Scatter(x = df.index, y = df['RSI'],
                                marker_color="#A67B5B",
                                name = "RSI"),
                                row = 2, col = 1)

  # Add horizontal lines at the 30 and 70 marks
  sub_figs.add_hline(y=30, col=1, row=2, line_color='red',
                    line_width=1,
                    line_dash='dot')

  sub_figs.add_hline(y=70, col=1, row=2, line_color='red',
                    line_width=1,
                    line_dash='dot')

  sub_figs.update_yaxes(tickvals=[0, 30, 70, 100], row=2)

  # Create the Stochastic Oscillator (SO) chart

  sub_figs.add_trace(go.Scatter(x = df.index, y=df["%K"],
                                line = dict(color="#ff9900", width=2),
                                name = "Fast (%K)"),
                                row=3, col=1)

  sub_figs.add_trace(go.Scatter(x=df.index, y=df["%D"],
                                line=dict(color="#000000", width=2),
                                name = "Slow (%D)"),
                                row=3, col=1)

  sub_figs.update_yaxes(range=[-10, 110], row=3, col=1)

  # Add horizontal lines at the 20 and 80 marks
  # and at 0 and 100 for the upper and lower bounds

  sub_figs.add_hline(y=0, row=3, col=1, line_color="#660000", line_width=1)
  sub_figs.add_hline(y=100, row=3, col=1, line_color="#660000", line_width=1)

  sub_figs.add_hline(y=20, row=3, col=1, line_color="#db2d43", line_width=1)
  sub_figs.add_hline(y=80, row=3, col=1, line_color="#80ff00", line_width=1)

  # Update the X-axes to remove the weekends and the grids
  sub_figs.update_xaxes(rangebreaks = [dict(values = date_gaps)], showgrid=False)
  sub_figs.update_yaxes(tickvals=[0, 20, 80, 100], row=3, showgrid=False)

  # Add a Volume chart
  vol_fig = go.Figure(go.Bar(x = df.index, y = df['Volume'], showlegend=False,
                            marker_color="#800020"))

  vol_fig.update_layout(height=400, title="Volume", title_x=0.5)

  # sub_figs.show();
  # vol_fig.show()

  return sub_figs, vol_fig

# Streamlit App

st.title("Technical Indicators for Financial Instruments")
text = (
    "The app accepts three arguments:\n"
    "- Ticket symbol (e.g.  'GOOGL', 'XOM', 'CL=F')\n"
    "- Start Date (min value: 2000-01-01)\n"
    "- End Date (min value: 2001-01-01)"
)

st.write(text, font="Arial", font_size=14)

min_date1 = datetime.date(2000,1,1)
min_date2 = datetime.date(2001,1,1)
max_date = datetime.date(2024,1,1)

# Sidebar inputs
ticker = st.sidebar.text_input('Ticker: ')
start_date = st.sidebar.date_input('Start Date',value=datetime.date(2000,1,1), min_value= datetime.date(2000,1,1), max_value=datetime.datetime.today())
end_date = st.sidebar.date_input('End Date', min_value=datetime.date(2001,1,1), max_value=datetime.datetime.today())

# Download data
load_data_button = st.button("Load Data")


if load_data_button:
    df = load_data(ticker=ticker, start_date=start_date, end_date=end_date)
    subs, vol = plot_indicators(df)

    st.plotly_chart(subs)
    st.plotly_chart(vol)
    

