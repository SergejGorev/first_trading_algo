# First Trading Algorithm
Trading algorithm that automatically looks for signals, generated from COT Reports, Seasonality and Price Action, and invests in different markets from the well chosen Market-Universe. Secondly, Portfolio Manager takes over the helm and balances Positions and overall Portfolio, based on Correlation Matrix, Margin and opened Positions.


# Ready to use Backtester
tested and should be bugfree. To run this badboy
   
    python mac.py

# Object Map
Universe(Markets that the Algorithm can choose from for analysis, we can switch for trading to Mini Futures which we will have to map manually)

get_data(Downloading Data, Saving, Check if Data is uptodate, algo that runs on its own)

signals(COT, Seasonality, Price_Trend_Weekly, Price_Trigger_Daily)
 
Portfolio-Manger(Allocation, Margin Check, Correlation Check)

Position-Manager(Strategy that involves specific position management decisions)

Execution(Routing Orders, Handling Errors in execution, choosing Order Types, etc)

# Notes
Sentiment is one of the Signals that require a lot of time and experimental Work, so its gonna be the last thing to do here.

