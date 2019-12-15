# First Trading Algorithm
Trading algorithm automatically looks for signals, generated from COT Reports, Seasonality and Price Action,
and invests in different markets from the well chosen Market-Universe. Secondly, Portfolio Manager takes over the 
helm and balances Positions and overall Portfolio, based on Correlation Matrix, Margin and opened Positions.

The Idea for that infrastructure I took from a book called "Successful Algorithmic Trading". I going to build on that,
since it is just amazing and there are any limitations. I can create whatever I want, how I want.
And even replace or add modules later on.

# What is COT
Commitment Of Traders(COT) Report from the CFTC Commission. It is an american government organisation which
provides summarized information about big positions of market participants in futures and options markets on
a weekly basis. Release date is usually every friday but the reference date is from tuesday to tuesday. I use
aggregated report for my analysis, which contains the positioning of COMMERCIALS, SPECULATORS and NON REPORTABLE.

As a market participant of a curtain size you have to provide information of all your future and option 
positions to CFTC.

COMMERCIALS - Hedgers(buy and sell).

SPECULATORS - Participants who take the risk of the hedgers and profit from price.

NON REPORTABLE - Small participants, with a non relevant size.

So, we can use that information for our analysis. I use only COMMERCIALS, because I assume that they have 
information advantage at least to a curtain degree. Since they buy or sell the cash market, they know better
about their crop condition. It can give me some information advantage too.


# Working Progress
##### Done 
COT Index and price momentum trigger. I need to build a workaround for COT data, because CFTC does not 
publishes release dates of their reports, only a reference date/window (from - to) they calculate the data.
That creates a look ahead bias for my algo. Most dates are tuesdays, which is a calculation date, BUT the report
is published not until friday. And if you iterate over the data, the algo will have data to work with,
which is not available yet...

I interpolated the dates to friday or the next working dates. This state is far from being perfect but at least
I permitted the backtesting algorithm to look into the future.

Momentum Price Trigger is just a condition for the algo. Long, if 18D SMA is crossed and last three closing
prices are above the SMA. For a Short is the other way around. It is quite simple and generates not to much signals.


##### In work
News Sentiment indicator for Twitter, Reddit or Reuters/Bloomberg data with Keras/Tensorflow.
Still not clear where or how to get historical news data.

Correlation matrix, based on the correlation of all assets from the Asset Universe within six months window.

Signal strength, will decide which size to use.


#### 1. Get Data

You need to get data first. In order to do that run get data.

    python get_data.py

#### 2. Run the backtester with the a simple COT Strategy.
tested and should be bugfree. Run this Application with 
   
    python backtester/STRAT_cot_and_trigger.py

Of course it is just a beginning...

To be continued