"""
main.py
エントリーポイント。
ここを実行すると「戦略評価 → 最良選択 → シグナル生成」が動く。

使い方:
  python main.py              # ダミーデータで動作確認
  python main.py --live       # 取引所からリアルデータを取得
"""

import argparse
from data_fetcher import fetch_ohlcv, fetch_demo_data
from strategies import MovingAverageCross, RSIMeanReversion, BollingerBandReversion
from orchestrator import Orchestrator


def build_strategies():
    """
    使う戦略を登録する。
    戦略・パラメータを増やしたいときはここに追記するだけ。
    """
    return [
        # --- 戦略 A: 移動平均クロス（パラメータ違いで3種）---
        MovingAverageCross(short=5,  long=20),   # A_v1: 短期設定
        MovingAverageCross(short=7,  long=25),   # A_v2: 標準設定
        MovingAverageCross(short=10, long=50),   # A_v3: 長期設定

        # --- 戦略 B: RSI 逆張り（閾値違いで2種）---
        RSIMeanReversion(period=14, oversold=30, overbought=70),  # B_v1: 標準
        RSIMeanReversion(period=7,  oversold=25, overbought=75),  # B_v2: 敏感

        # --- 戦略 C: ボリンジャーバンド ---
        BollingerBandReversion(period=20, std_mult=2.0),  # C_v1
        BollingerBandReversion(period=20, std_mult=2.5),  # C_v2: 広めのバンド

        # ここに新しい戦略 D, E を追加するだけで自動比較される
        # XGBoostStrategy(...)      ← 次のステップで追加予定
        # PairTradeStrategy(...)    ← その後追加予定
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="取引所からリアルデータを取得")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--exchange", default="bybit")
    parser.add_argument("--eval-window", type=int, default=50, help="評価に使う過去データ件数")
    args = parser.parse_args()

    # --- 1. データ取得 ---
    if args.live:
        print(f"📡 {args.exchange} から {args.symbol} ({args.timeframe}) を取得中...")
        df = fetch_ohlcv(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=200,
            exchange_name=args.exchange,
        )
        print(f"   取得完了: {len(df)} 本")
    else:
        print("📊 デモデータで動作確認中（--live で取引所接続）")
        df = fetch_demo_data(n=300)

    # --- 2. 戦略を登録 ---
    strategies = build_strategies()
    print(f"\n🔧 登録戦略数: {len(strategies)} 件")

    # --- 3. オーケストレーターで評価・選択 ---
    orch = Orchestrator(strategies, eval_window=args.eval_window)
    result = orch.evaluate_all(df)

    # --- 4. レポート表示 ---
    orch.print_report(result)

    # --- 5. 最良戦略でシグナル生成 ---
    signal_info = orch.get_signal(df)
    print(f"📌 現在のシグナル: {signal_info['signal'].upper()}")
    print(f"   （使用戦略: {signal_info['strategy']}）\n")

    # --- 6. 実際の注文はここで行う（今はコメントアウト）---
    # executor = Executor(api_key="...", api_secret="...")
    # if signal_info["signal"] == "buy":
    #     executor.place_order("buy", amount=0.001)
    # elif signal_info["signal"] == "sell":
    #     executor.place_order("sell", amount=0.001)


if __name__ == "__main__":
    main()
