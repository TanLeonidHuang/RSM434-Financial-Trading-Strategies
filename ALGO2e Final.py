import requests
import random
from time import sleep

s = requests.Session()
s.headers.update({'X-API-key': 'BZ5DLLR6'}) # Dektop

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

def main():
    tick, status = get_tick()
    while status == 'ACTIVE':
        
        best_bid_priceR, best_ask_priceR = get_bid_ask('RY')
        for _ in range(0,7):
            best_bid_priceC, best_ask_priceC = get_bid_ask('CNR')
            
            position = get_position()
            if position <= 15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price': best_bid_priceC, 'action': 'BUY'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price': best_ask_priceC - 0.01, 'action': 'SELL'})
            position = get_position()
            if position >= -15000:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 2000, 'price': best_ask_priceC, 'action': 'SELL'})
            else:
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 1000, 'price': best_bid_priceC + 0.01, 'action': 'BUY'})
            sleep(0.3)       
        s.post('http://localhost:9999/v1/commands/cancel', params = {'ticker': 'CNR'})
        tick, status = get_tick()

if __name__ == '__main__':
    main()



