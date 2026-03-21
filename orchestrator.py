"""
orchestrator.py
全戦略を評価して最良を選ぶエンジン。
戦略の追加・削除はここを変えなくていい。
"""

import pandas as pd
from typing import List
from strategies import StrategyBase


class Orchestrator:
    """
    登録された全戦略を評価し、スコア最高の戦略を選択する。
    """

    def __init__(self, strategies: List[StrategyBase], eval_window: int = 30):
        self.strategies = strategies
        self.eval_window = eval_window
        self.best_strategy: StrategyBase | None = None
        self.last_scores: dict = {}

    def evaluate_all(self, df: pd.DataFrame) -> dict:
        """
        全戦略をスコアリングして結果を返す。
        """
        scores = {}
        details = {}

        for strategy in self.strategies:
            sc = strategy.score(df, self.eval_window)
            ev = strategy.evaluate(df, self.eval_window)
            scores[strategy.name] = sc
            details[strategy.name] = ev

        self.last_scores = scores

        # スコア最高の戦略を選択
        best_name = max(scores, key=scores.get)
        self.best_strategy = next(s for s in self.strategies if s.name == best_name)

        return {
            "scores": scores,
            "details": details,
            "winner": best_name,
        }

    def get_signal(self, df: pd.DataFrame) -> dict:
        """
        現在の最良戦略でシグナルを生成する。
        evaluate_all を先に呼んでおく必要がある。
        """
        if self.best_strategy is None:
            raise RuntimeError("evaluate_all() を先に実行してください")

        signal = self.best_strategy.generate_signal(df)
        return {
            "strategy": self.best_strategy.name,
            "signal": signal,
        }

    def print_report(self, result: dict):
        """
        評価結果を見やすく表示する。
        """
        print("\n" + "=" * 60)
        print("  戦略評価レポート")
        print("=" * 60)

        details = result["details"]
        scores = result["scores"]

        # スコア順にソート
        sorted_names = sorted(scores, key=scores.get, reverse=True)

        for i, name in enumerate(sorted_names):
            d = details[name]
            marker = "★ 選択" if name == result["winner"] else "  "
            print(f"\n{marker} [{i+1}] {name}")
            print(f"     スコア    : {scores[name]:.4f}")
            print(f"     勝率      : {d['win_rate']*100:.1f}%")
            print(f"     総リターン: {d['total_return']*100:.2f}%")
            print(f"     シャープ比: {d['sharpe']:.2f}")
            print(f"     最大DD    : {d['max_drawdown']*100:.2f}%")
            print(f"     取引回数  : {d['trade_count']} 回")

        print("\n" + "=" * 60)
        print(f"  → 実行戦略: {result['winner']}")
        print("=" * 60 + "\n")
