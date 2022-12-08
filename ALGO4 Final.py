import requests
import numpy as np
from time import sleep

s = requests.Session()
s.headers.update({'X-API-key': 'BZ5DLXR5'}) # Dektop

MAX_LONG_EXPOSURE_NET = 25000
MAX_SHORT_EXPOSURE_NET = -25000
MAX_EXPOSURE_GROSS = 500000
ORDER_LIMIT = 7500
past_tick = 0
ticker_list = ['RGLD','RFIN','INDX']

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
        gross_position = abs(book[1]['position']) + abs(book[2]['position']) + 2 * abs(book[3]['position'])
        net_position = book[1]['position'] + book[2]['position'] + 2 * book[3]['position']
        return gross_position, net_position

def get_position_tick(ticker):
    resp = s.get('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        position = book[ticker]['position']
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

def is_within():
    gross_position, net_position = get_position()
    return (check_net_position(net_position) and check_gross_position(gross_position))
    
def check_net_position(net_position):
    if (net_position > (MAX_LONG_EXPOSURE_NET - 5000)) or (net_position < (MAX_SHORT_EXPOSURE_NET + 5000)):
        return False
    return True

def check_gross_position(gross_position):
    if gross_position > (MAX_EXPOSURE_GROSS - 100000):
        return False
    return True
        

def reverse_position(ticker):
    print('here2')
    pos = get_position_tick(ticker)
    print(pos)
    if (pos) > 0:
        print(s.post('http://localhost:9999/v1/orders', params = {'ticker': ticker, 'type': 'MARKET', 'quantity': 1000 , 'action': 'SELL'}))
    else:
        print(s.post('http://localhost:9999/v1/orders', params = {'ticker': ticker, 'type': 'MARKET', 'quantity': 1000 , 'action': 'BUY'}))

def total_reverse(ticker_list):
    for ticker in ticker_list:
        if get_position_tick(ticker) > 5000:
            reverse_position(ticker)

def set_prices(ticker_list):
    market_prices = np.array([0.,0.,0.,0.,0.,0.])
    market_prices = market_prices.reshape(3,2)
    for i in range(len(ticker_list)):
        ticker_symbol = ticker_list[i]
        market_prices[i,0], market_prices[i,1] = get_bid_ask(ticker_symbol)                
    return market_prices

def cancel_all(ticker_list):
    for ticker in ticker_list:
        s.post('http://localhost:9999/v1/commands/cancel', params = {'ticker': ticker})
        
def check_position_diff(assets):
    if len(assets) < 2:
        return 0
    a = assets[0]
    for asset in assets:
        if asset < a:
            a = asset
    return a

def main():
    tick, status = get_tick()
    n = 0
    passed = True
    print('atthebeginning')
    s.post('http://localhost:9999/v1/leases', params = {'ticker': 'ETF-Creation'})
    s.post('http://localhost:9999/v1/leases', params = {'ticker': 'ETF-Redemption'})
    past_tick = 0
    while status == 'ACTIVE':
            market_prices = set_prices(ticker_list)
            bidG, askG, bidF, askF, bidI, askI = market_prices[n, 0], market_prices[n, 1], market_prices[n+1, 0], market_prices[n+1, 1], market_prices[n+2, 0], market_prices[n+2, 1]
            gross_position, net_position = get_position()   
            if gross_position < 400000 and net_position < 15000:
                if (askI + 0.0415) < (bidG + bidF):
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RGLD', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'action': 'SELL'})
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RFIN', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'action': 'SELL'})
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'INDX', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'action': 'BUY'})
                elif (askG + askF + 0.015) < (bidI):
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RGLD', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'action': 'BUY'})
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RFIN', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'action': 'BUY'})
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'INDX', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'action': 'SELL'})
                    
                #else:
                    #s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RGLD', 'type': 'LIMIT', 'quantity': 200, 'price': (bidG + sG/2), 'action': 'BUY'})
                    #s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RFIN', 'type': 'LIMIT', 'quantity': 200, 'price': (bidF + sF/2), 'action': 'BUY'})
                    #s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RGLD', 'type': 'LIMIT', 'quantity': 200, 'price': (askG - sG/2), 'action': 'SELL'})
                    #s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RFIN', 'type': 'LIMIT', 'quantity': 200, 'price': (askF - sF/2), 'action': 'SELL'})
                if (tick - past_tick >= 2):
                    past_tick = tick
                    passed = True
                if passed:
                    passed = False
                    resp = s.get('http://localhost:9999/v1/leases')
                    if (askG + askF + 0.015) < (bidI):
                        if get_position_tick(1) == abs(get_position_tick(1)):
                            x = check_position_diff([abs(get_position_tick(1)), abs(get_position_tick(2)), abs(get_position_tick(3)), 100000])  
                            print(x)                    
                            lease_number = resp.json()[0]['id']
                            s.post('http://localhost:9999/v1/leases' + '/' + str(lease_number), params = {'from1': 'RGLD', 'quantity1': x, 'from2': 'RFIN', 'quantity2': x})
                    elif (askI + 0.0375) < (bidG + bidF):
                        if get_position_tick(1) != abs(get_position_tick(1)):                        
                            x = check_position_diff([abs(get_position_tick(1)), abs(get_position_tick(2)), abs(get_position_tick(3)), 100000])  
                            print(-x)
                            lease_number = resp.json()[1]['id']
                            s.post('http://localhost:9999/v1/leases' + '/' + str(lease_number), params = {'from1': 'INDX', 'quantity1': x, 'from2': 'CAD', 'quantity2': int(x*0.0375)})
                            
            sleep(0.3)
            tick, status = get_tick()

if __name__ == '__main__':
    main()



