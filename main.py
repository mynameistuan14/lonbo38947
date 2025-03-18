```python
import ccxt.async_support as ccxt_async
import asyncio
import json
from websocket import create_connection
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Khởi tạo Bitget API
exchange = ccxt_async.bitget({
    'apiKey': 'bg_651140de3425d668241ad6726b63ae17',       # Thay bằng API Key của bạn
    'secret': '75311c7cb43a6702daef5977fbdeca2f57844f0a29200dd2e244ca0b6ac22f9b',    # Thay bằng Secret Key
    'password': '123456789',  # Thay bằng Passphrase
    'enableRateLimit': True,
})

# Danh sách cặp giao dịch để kiểm tra
pairs = [
    ('BTC/USDT', 'ETH/BTC', 'ETH/USDT'),  # Cặp gốc
    ('BTC/USDT', 'XRP/BTC', 'XRP/USDT'),  # Thêm XRP
    ('ETH/USDT', 'SOL/ETH', 'SOL/USDT'),  # Thêm SOL
    ('BNB/USDT', 'BTC/BNB', 'BTC/USDT'),  # Thêm BNB
    ('ADA/USDT', 'ETH/ADA', 'ETH/USDT'),  # Thêm ADA
]

# Lưu trữ giá real-time
price_data = {
    'BTC/USDT': {'bid': 0, 'ask': 0},
    'ETH/BTC': {'bid': 0, 'ask': 0},
    'ETH/USDT': {'bid': 0, 'ask': 0},
    'XRP/USDT': {'bid': 0, 'ask': 0},
    'XRP/BTC': {'bid': 0, 'ask': 0},
    'SOL/USDT': {'bid': 0, 'ask': 0},
    'SOL/ETH': {'bid': 0, 'ask': 0},
    'BNB/USDT': {'bid': 0, 'ask': 0},
    'BTC/BNB': {'bid': 0, 'ask': 0},
    'ADA/USDT': {'bid': 0, 'ask': 0},
    'ETH/ADA': {'bid': 0, 'ask': 0},
}

# Kết nối WebSocket để lấy giá real-time
def start_websocket():
    ws_url = "wss://ws.bitget.com/spot/v1/stream"
    ws = create_connection(ws_url)
    logging.info("Đã kết nối WebSocket")

    # Đăng ký nhận giá cho tất cả các cặp
    for pair in price_data.keys():
        subscribe_msg = {
            "op": "subscribe",
            "args": [{"channel": "ticker", "instId": pair.replace('/', '')}]
        }
        ws.send(json.dumps(subscribe_msg))

    # Nhận và cập nhật dữ liệu giá
    while True:
        try:
            data = json.loads(ws.recv())
            if 'data' in data and 'instId' in data['data']:
                inst_id = data['data']['instId']
                pair = f"{inst_id[:3]}/{inst_id[3:]}"
                if pair in price_data:
                    price_data[pair]['bid'] = float(data['data']['bestBid'])
                    price_data[pair]['ask'] = float(data['data']['bestAsk'])
        except Exception as e:
            logging.error(f"Lỗi WebSocket: {e}")
            break

# Hàm kiểm tra arbitrage
async def check_arbitrage(pair_set, start_amount=1000):
    base_quote, inter_base, inter_quote = pair_set
    try:
        base_ask = price_data[base_quote]['ask']
        inter_bid = price_data[inter_base]['bid']
        final_bid = price_data[inter_quote]['bid']

        if base_ask == 0 or inter_bid == 0 or final_bid == 0:
            return

        # Tính toán lợi nhuận
        base_amount = start_amount / base_ask
        inter_amount = base_amount * inter_bid
        final_amount = inter_amount * final_bid
        profit = final_amount - start_amount
        profit_percent = (profit / start_amount) * 100

        # Phí 0.3% (0.1% x 3)
        fee = start_amount * 0.003
        net_profit = profit - fee

        if net_profit > 0:
            logging.info(f"{base_quote} → {inter_base} → {inter_quote}: "
                         f"Lợi nhuận {net_profit:.2f} USDT ({profit_percent:.2f}%)")
            await execute_trades(base_quote, inter_base, inter_quote, start_amount)

    except Exception as e:
        logging.error(f"Lỗi tính toán: {e}")

# Thực thi giao dịch
async def execute_trades(base_quote, inter_base, inter_quote, start_amount):
    try:
        base_ask = price_data[base_quote]['ask']
        inter_bid = price_data[inter_base]['bid']

        base_amount = start_amount / base_ask
        await exchange.create_market_buy_order(base_quote, base_amount)

        inter_amount = base_amount * inter_bid
        await exchange.create_market_buy_order(inter_base, inter_amount)

        await exchange.create_market_sell_order(inter_quote, inter_amount)
        logging.info("Hoàn tất giao dịch!")

    except Exception as e:
        logging.error(f"Lỗi giao dịch: {e}")

# Chạy bot
async def main():
    import threading
    threading.Thread(target=start_websocket, daemon=True).start()
    await asyncio.sleep(2)  # Chờ WebSocket khởi động

    while True:
        tasks = [check_arbitrage(pair_set) for pair_set in pairs]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)  # Kiểm tra 10 lần/giây

if __name__ == "__main__":
    asyncio.run(main())
```