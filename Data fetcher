"""
data_fetcher.py
取引所からローソク足データを取得するモジュール。
ccxt ライブラリを使うので Bybit・Binance どちらでも動く。
"""

import pandas as pd
import ccxt


def fetch_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 200,
    exchange_name: str = "bybit",
) -> pd.DataFrame:
    """
    取引所から OHLCV（ローソク足）データを取得して DataFrame で返す。

    Args:
        symbol      : 取引ペア（例: "BTC/USDT", "ETH/USDT"）
        timeframe   : 時間足（"1m", "5m", "1h", "4h", "1d"）
        limit       : 取得本数（最大500程度）
        exchange_name: "bybit" or "binance"

    Returns:
        columns: timestamp, open, high, low, close, volume
    """
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class({"enableRateLimit": True})

    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    df = df.astype(float)

    return df


def fetch_demo_data(n: int = 300) -> pd.DataFrame:
    """
    API キーなしでテストしたい場合用のダミーデータ生成。
    正規分布に基づくランダムウォークで BTC 価格を模倣する。
    """
    import numpy as np

    np.random.seed(42)
    price = 30000.0
    prices = [price]

    for _ in range(n - 1):
        change = np.random.normal(0, 0.01)
        price = price * (1 + change)
        prices.append(price)

    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    df = pd.DataFrame(index=dates)
    df["close"] = prices
    df["open"] = df["close"].shift(1).bfill()
    df["high"] = df["close"] * (1 + abs(np.random.normal(0, 0.005, n)))
    df["low"] = df["close"] * (1 - abs(np.random.normal(0, 0.005, n)))
    df["volume"] = np.random.uniform(100, 1000, n)

    return df
