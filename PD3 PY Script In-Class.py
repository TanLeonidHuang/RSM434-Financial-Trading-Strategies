import requests
from time import sleep
import numpy as np

s = requests.Session()
s.headers.update({'X-API-key': 'BZ5DLXR5'}) # Make sure you use YOUR API Key

# global variables
MAX_LONG_EXPOSURE_NET = 25000
MAX_SHORT_EXPOSURE_NET = -25000
MAX_EXPOSURE_GROSS = 100000
ORDER_LIMIT = 500

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
        gross_position = abs(book[0]['position']) + abs(book[1]['position']) + abs(book[2]['position'])
        net_position = book[0]['position'] + book[1]['position'] + 2 * book[2]['position']
        return gross_position, net_position

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

def get_news(estimates_data,news_query_length): 
    resp = s.get ('http://localhost:9999/v1/news')
    x = np.random(low = -1.0, high = 1.0, )
    if resp.ok:
        news_query = resp.json()
        news_query_length_check = len(news_query)
        
        if news_query_length_check > news_query_length:
            news_query_length = news_query_length_check
            
            newest_tick = news_query[0]['tick']
            start_char = news_query[0]['body'].find("$")
            newest_estimate = float(news_query[0]['body'][start_char + 1 : start_char + 6])
                        
            if news_query[0]['headline'].find("UB") > 0:
                estimates_data[0,0] = max(newest_estimate - ((300 - newest_tick) / 50), estimates_data[0,0])
                estimates_data[0,1] = min(newest_estimate + ((300 - newest_tick) / 50), estimates_data[0,1])
           
            elif news_query[0]['headline'].find("GEM") > 0:
                estimates_data[1,0] = max(newest_estimate - ((300 - newest_tick) / 50), estimates_data[1,0])
                estimates_data[1,1] = min(newest_estimate + ((300 - newest_tick) / 50), estimates_data[1,1])
            
        estimates_data[2,0] = estimates_data[0,0] + estimates_data[1,0]
        estimates_data[2,1] = estimates_data[0,1] + estimates_data[1,1]
                
        return estimates_data, news_query_length, newest_estimate

def trade(price, ticker, direction, quantity):
    s.post('http://localhost:9999/v1/orders', params = {'ticker': ticker, 'type': 'LIMIT', 'quantity': quantity, 'price': price, 'action': direction})

def con_int(upper, lower, estimate, conf):
    upper_diff = upper - estimate
    lower_diff = estimate - lower
    
    u = upper_diff * conf
    l = lower_diff * conf
    
    return (u+estimate), (l+estimate)
    
def main():
    tick, status = get_tick()
    ticker_list = ['UB','GEM','ETF']
    market_prices = np.array([0.,0.,0.,0.,0.,0.])
    market_prices = market_prices.reshape(3,2)

    news_query_length = 1
    estimates_data = np.array([40., 60., 20., 30., 60., 90.])
    estimates_data = estimates_data.reshape(3,2)
    n= 0
    while status == 'ACTIVE':        

        for i in range(3):
            
            ticker_symbol = ticker_list[i]
            market_prices[i,0], market_prices[i,1] = get_bid_ask(ticker_symbol)
        
        estimates_data, news_query_length, newest_estimate = get_news(estimates_data, news_query_length)
        gross_position, net_position = get_position()
        
        print(estimates_data)
        
        
        if gross_position < MAX_EXPOSURE_GROSS:
            
            market_prices = set_prices(ticker_list)
            maxU, minU, maxG, minG = estimates_data[0,0], estimates_data[0,1], estimates_data[1,0], estimates_data[1,1]
            conUUB, conLUB = con_int(maxU, minU, estimates)
            bidU, askU, bidG, askG, bidE, askE = market_prices[n, 0], market_prices[n, 1], market_prices[n+1, 0], market_prices[n+1, 1], market_prices[n+2, 0], market_prices[n+2, 1]
            sU = askU-bidU
            sG = askG-bidG
            if (bidU + sU/3) > estimates_data[0,1]: 
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'UB', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[0, 0], 'action': 'SELL'})
                ub_length = news_query_length + tick
                if tick - ub_length >= 0:
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'UB', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[0, 1], 'action': 'BUY'})                    
                                
            elif estimates_data[0, 0] < (askU - sU/2): 
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'UB', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[0, 1], 'action': 'BUY'}) 
                ub_length_2 = news_query_length + tick
                if tick - ub_length_2 >= 0:
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'UB', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[0, 0], 'action': 'SELL'})                
                
            if (bidG + sG/3) > estimates_data[1, 1]: 
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'GEM', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[1, 0], 'action': 'SELL'})
                gem_length = news_query_length + tick
                if tick - gem_length >= 0:
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'GEM', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[1, 1], 'action': 'BUY'})    
            elif estimates_data[1, 0] < (askG + sG/2): 
                s.post('http://localhost:9999/v1/orders', params = {'ticker': 'GEM', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[1, 1], 'action': 'BUY'})                               
                gem_length_2 = news_query_length + tick 
                if tick - gem_length_2 >= 0:
                    s.post('http://localhost:9999/v1/orders', params = {'ticker': 'GEM', 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': market_prices[1, 0], 'action': 'SELL'})    
        sleep(0.5)
        for i in range(3):
            
            ticker_symbol = ticker_list[i]          
            s.post('http://localhost:9999/v1/commands/cancel', params = {'ticker': ticker_symbol})
        
        tick, status = get_tick()

if __name__ == '__main__':
    main()



