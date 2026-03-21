"""
strategies.py
戦略の基底クラスと、具体的な戦略を定義するファイル。
新しい戦略はここに追加するだけでOK。
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


# ============================================================
# 基底クラス：すべての戦略はこれを継承する
# ============================================================
class StrategyBase(ABC):
    """
    すべての戦略が持つべき共通インターフェース。
    generate_signal と evaluate の2つを必ず実装する。
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        最新データを受け取り、売買シグナルを返す。
        戻り値: "buy" / "sell" / "hold"
        """
        pass

    def evaluate(self, df: pd.DataFrame, window: int = 30) -> dict:
        """
        過去 window 件のデータでシグナルを生成し、
        勝率・損益・シャープ比を計算して返す。
        """
        signals = []
        returns = []

        for i in range(window, len(df)):
            chunk = df.iloc[:i].copy()
            signal = self.generate_signal(chunk)
            future_return = (df["close"].iloc[i] - df["close"].iloc[i - 1]) / df["close"].iloc[i - 1]

            if signal == "buy":
                ret = future_return
            elif signal == "sell":
                ret = -future_return
            else:
                ret = 0.0

            signals.append(signal)
            returns.append(ret)

        returns = np.array(returns)
        trades = [r for r in returns if r != 0.0]

        win_rate = (np.array(trades) > 0).mean() if trades else 0.0
        total_return = float(np.sum(returns))
        sharpe = float(np.mean(returns) / (np.std(returns) + 1e-9) * np.sqrt(365))
        max_dd = self._max_drawdown(returns)

        return {
            "strategy": self.name,
            "win_rate": round(win_rate, 4),
            "total_return": round(total_return, 4),
            "sharpe": round(sharpe, 4),
            "max_drawdown": round(max_dd, 4),
            "trade_count": len(trades),
        }

    def _max_drawdown(self, returns: np.ndarray) -> float:
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / (peak + 1e-9)
        return float(drawdown.min())

    def score(self, df: pd.DataFrame, window: int = 30) -> float:
        """
        評価結果をひとつの数値（スコア）にまとめる。
        オーケストレーターはこの数値で戦略を比較する。
        勝率 × 0.5 + シャープ比正規化 × 0.3 + リターン × 0.2
        """
        result = self.evaluate(df, window)
        s = (result["win_rate"] * 0.5
             + min(max(result["sharpe"], -2), 2) / 4 * 0.3
             + min(max(result["total_return"], -1), 1) / 2 * 0.2)
        return round(s, 4)


# ============================================================
# 戦略 A：移動平均クロス
# ============================================================
class MovingAverageCross(StrategyBase):
    """
    短期MAが長期MAを上抜けたら買い、下抜けたら売り。
    パラメータを変えて A_v1, A_v2 … と複数インスタンス作れる。
    """

    def __init__(self, short: int = 7, long: int = 25):
        name = f"MA_cross(short={short}, long={long})"
        super().__init__(name)
        self.short = short
        self.long = long

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.long + 1:
            return "hold"

        ma_short = df["close"].rolling(self.short).mean()
        ma_long = df["close"].rolling(self.long).mean()

        # 直近2本を比較してクロスを検出
        prev_diff = ma_short.iloc[-2] - ma_long.iloc[-2]
        curr_diff = ma_short.iloc[-1] - ma_long.iloc[-1]

        if prev_diff < 0 and curr_diff > 0:
            return "buy"
        elif prev_diff > 0 and curr_diff < 0:
            return "sell"
        else:
            return "hold"


# ============================================================
# 戦略 B：RSI 逆張り
# ============================================================
class RSIMeanReversion(StrategyBase):
    """
    RSI が oversold_threshold 以下で買い、
    overbought_threshold 以上で売り。
    """

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        name = f"RSI(period={period}, OS={oversold}, OB={overbought})"
        super().__init__(name)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.period + 1:
            return "hold"

        rsi = self._calc_rsi(df["close"], self.period)

        if rsi < self.oversold:
            return "buy"
        elif rsi > self.overbought:
            return "sell"
        else:
            return "hold"

    def _calc_rsi(self, close: pd.Series, period: int) -> float:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])


# ============================================================
# 戦略 C：ボリンジャーバンド 逆張り
# ============================================================
class BollingerBandReversion(StrategyBase):
    """
    価格がバンド下限を下回ったら買い、上限を上回ったら売り。
    """

    def __init__(self, period: int = 20, std_mult: float = 2.0):
        name = f"BB(period={period}, std={std_mult})"
        super().__init__(name)
        self.period = period
        self.std_mult = std_mult

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.period:
            return "hold"

        close = df["close"]
        mid = close.rolling(self.period).mean()
        std = close.rolling(self.period).std()
        upper = mid + self.std_mult * std
        lower = mid - self.std_mult * std

        price = close.iloc[-1]

        if price < float(lower.iloc[-1]):
            return "buy"
        elif price > float(upper.iloc[-1]):
            return "sell"
        else:
            return "hold"
