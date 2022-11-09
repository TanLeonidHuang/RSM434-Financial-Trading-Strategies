import requests
import numpy as np
from time import sleep

s = requests.Session()
s.headers.update({'X-API-key': 'BZ5DLXR5'}) # Dektop

MAX_LONG_EXPOSURE = 25000
MAX_SHORT_EXPOSURE = -25000

def get_tick():
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']

def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/book', params = payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']
        
        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]
        
        best_bid_price = bid_prices_book[0]
        best_ask_price = ask_prices_book[0]
  
        return best_bid_price, best_ask_price

def get_time_sales(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/tas', params = payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_position():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return (book[0]['position']) + (book[1]['position']) + (book[2]['position'])
    
def get_position_ticker(ticker):
    resp = s.get('http://localhost:9999/v1/securities')
    if ticker == 'CNR':
        pos = 0
    elif ticker == 'RY':
        pos = 1
    else:
        pos = 2
    
    if resp.ok:
        book = resp.json()
        position = book[pos]['position']
        return int(position)

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get ('http://localhost:9999/v1/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']
    
def set_prices(ticker_list):
    market_prices = np.array([0.,0.,0.,0.,0.,0.])
    market_prices = market_prices.reshape(3,2)
    for i in range(len(ticker_list)):
        ticker_symbol = ticker_list[i]
        market_prices[i,0], market_prices[i,1] = get_bid_ask(ticker_symbol)                
    return market_prices

def main():
    tick, status = get_tick()
    ticker_list = ['CNR', 'RY', 'AC']
    total_list = []
    n = 0
    total = 0
    total2 = 0
    while status == 'ACTIVE':
        for _ in range(0,3):
            market_prices = set_prices(ticker_list)
            bidC, askC, bidR, askR, bidA, askA = market_prices[n, 0], market_prices[n, 1], market_prices[n+1, 0], market_prices[n+1, 1], market_prices[n+2, 0], market_prices[n+2, 1]
            sC, sR, sA = askC-bidC, askR-bidR, askA-bidA
            price_list = [[bidC, askC, sC], [bidR, askR, sR], [bidA, askA, sA]]
            sC_average = []
            sC_average.append(sC)
            
            position = get_position_ticker()
            if position <= 15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price':bidC, 'action': 'BUY'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price': askC - 0.01, 'action': 'SELL'})
            position = get_position()
            if position >= -15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price': askC, 'action': 'SELL'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price': bidC + 0.01, 'action': 'BUY'})
                
                
            if position <= 15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': 2000, 'price':bidR, 'action': 'BUY'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': 2000, 'price': askR - 0.01, 'action': 'SELL'})
            position = get_position()
            if position >= -15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': 2000, 'price': askR, 'action': 'SELL'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': 2000, 'price': bidR + 0.01, 'action': 'BUY'})
                
                
            if position <= 15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': 2000, 'price':bidA, 'action': 'BUY'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': 2000, 'price': askA - 0.01, 'action': 'SELL'})
            position = get_position()
            if position >= -15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': 2000, 'price': askA, 'action': 'SELL'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': 2000, 'price': bidA + 0.01, 'action': 'BUY'})
        

            sleep(0.3)       
        s.post('http://localhost:9999/v1/commands/cancel', params = {'ticker': 'CNR'})
        tick, status = get_tick()
        for i in sC_average:
            total += i
        
        total_list.append(total)
        print(total/len(sC_average))
        total = 0
        for i in total_list:
            total2 += i
        print( "total 2: " + str(total2/len(total_list)))
        total2 = 0
            

if __name__ == '__main__':
    main()



