import asyncio
from aiohttp import ClientSession

# example tickers tuple
TICKERS = (
    'XRPUSDT',
    'BTCUSDT',
    'RNDRUSDT',
    'LTCUSDT',
    'GALUSDT',
)


#  ticker tracking handling class
class TickersTracker:

    def __init__(self):
        self.symbols: list = []
        self.prices: dict = dict()
        self.base_endpoint: str = 'https://fapi.binance.com'  # base endpoint for working with binance's API
        self.price_endpoint: str = '/fapi/v1/ticker/price'  # current price data endpoint
        self.kline_endpoint: str = '/fapi/v1/klines'  # k-line data endpoint

    def add_ticker(self, symbol: str):  # add symbol to tracking list possibility
        self.symbols.append(symbol)

    # updating current symbol's price and checking its max hour value ratio
    async def _update_symbol(self, symbol: str, session: ClientSession):

        async with session:
            while True:
                hour_max_price = await self._get_max_hour_price(symbol, session)  # getting symbol maximum hour price
                price = await self._get_current_price(symbol, session)
                self.prices[symbol] = price

                print(f'{symbol}: {price}')

                if price < hour_max_price / 100:
                    print(f'{symbol}: symbol\'s price fell down by 1% from the hour maximum.')

    async def _get_max_hour_price(self, symbol: str, session: ClientSession) -> float:
        # returns one hour k-line data (for the previous line)
        url = f'{self.base_endpoint}{self.kline_endpoint}?symbol={symbol}&interval=1h&limit=1'
        async with session.get(url) as r:
            ret = await r.json()
            return float(ret[0][2])  # returns third line of response with the highest hour price

    async def _get_current_price(self, symbol: str, session: ClientSession) -> float:
        url = f'{self.base_endpoint}{self.price_endpoint}?symbol={symbol}'
        async with session.get(url) as r:
            ret = await r.json()
            return float(ret['price'])

    # gathering coroutine tasks for asyncio.run
    async def _collect_for_tracking(self):
        tasks = []
        async with ClientSession() as session:
            for symbol in self.symbols:
                task = asyncio.create_task(self._update_symbol(symbol, session))
                tasks.append(task)

            return await asyncio.gather(*tasks)

    #  main track function
    def track(self):
        print('Preparing for tracking...')

        # to avoid windows "event loop is closed" error after loop work ending
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        try:
            asyncio.run(self._collect_for_tracking())
        except KeyboardInterrupt:
            print('Force tracking stopping...')

        print('Stop tracking.')


if __name__ == '__main__':
    tickers_tracker = TickersTracker()

    for ticker in TICKERS:
        tickers_tracker.add_ticker(ticker)

    tickers_tracker.track()
