"""
Confluence Logic - 8-Confirmation Framework

Validates ALL 8 confirmations for Bill Fanter's 0DTE strategy:
1. Candles (direction + conviction)
2. Volume (high conviction)
3. VWAP (trend alignment)
4. 9 EMA (fast momentum)
5. 21 EMA (slow momentum)
6. SPY (market direction)
7. QQQ/Sector (confluence check)
8. Support/Resistance (clear levels)

ALL 8 must pass for valid trade entry.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import pandas as pd


class Direction(Enum):
    CALL = "CALL"
    PUT = "PUT"


class ConfirmationResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass
class MarketData:
    """Current market state for a symbol"""
    symbol: str
    current_price: float
    volume: int
    avg_volume_20: int  # 20-bar average volume
    vwap: float
    ema_9: float
    ema_21: float
    candle_color: str  # "GREEN", "RED", "DOJI"
    candle_body_pct: float  # % of candle that is body (vs wicks)
    high: float
    low: float
    close: float
    open: float


@dataclass
class LevelData:
    """Key support/resistance levels"""
    pdh: float  # Prior Day High
    pdl: float  # Prior Day Low
    pdc: float  # Prior Day Close
    support_levels: List[float]
    resistance_levels: List[float]


@dataclass
class ConfirmationCheck:
    """Result of a single confirmation check"""
    name: str
    result: ConfirmationResult
    reason: str
    details: str


@dataclass
class ConfluenceResult:
    """Complete 8-confirmation analysis"""
    symbol: str
    direction: Direction
    timestamp: str
    confirmations: List[ConfirmationCheck]
    passed_count: int
    verdict: str  # "HIGH_PROBABILITY", "SKIP", "WEAK_SETUP"
    setup_strength: float  # 0.0 - 1.0 (8/8 = 1.0)


class ConfluenceValidator:
    """Validates all 8 confirmations for trade entry"""

    def __init__(self):
        self.required_confirmations = 8

    def validate_all_confirmations(
        self,
        symbol: str,
        direction: Direction,
        market_data: MarketData,
        spy_data: MarketData,
        qqq_data: MarketData,
        level_data: LevelData,
        timestamp: str = None
    ) -> ConfluenceResult:
        """
        Validate ALL 8 confirmations for trade entry

        Returns ConfluenceResult with detailed breakdown
        """
        confirmations = []

        # 1. CANDLES
        confirmations.append(self._check_candles(market_data, direction))

        # 2. VOLUME
        confirmations.append(self._check_volume(market_data))

        # 3. VWAP
        confirmations.append(self._check_vwap(market_data, direction))

        # 4. 9 EMA
        confirmations.append(self._check_9_ema(market_data, direction))

        # 5. 21 EMA
        confirmations.append(self._check_21_ema(market_data, direction))

        # 6. SPY
        confirmations.append(self._check_spy(spy_data, direction))

        # 7. QQQ
        confirmations.append(self._check_qqq(qqq_data, spy_data, direction))

        # 8. SUPPORT/RESISTANCE
        confirmations.append(self._check_support_resistance(market_data, level_data, direction))

        # Calculate results
        passed_count = sum(1 for c in confirmations if c.result == ConfirmationResult.PASS)
        setup_strength = passed_count / self.required_confirmations

        # Determine verdict
        if passed_count == 8:
            verdict = "HIGH_PROBABILITY"
        elif passed_count >= 6:
            verdict = "WEAK_SETUP"
        else:
            verdict = "SKIP"

        return ConfluenceResult(
            symbol=symbol,
            direction=direction,
            timestamp=timestamp or pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            confirmations=confirmations,
            passed_count=passed_count,
            verdict=verdict,
            setup_strength=setup_strength
        )

    def _check_candles(self, data: MarketData, direction: Direction) -> ConfirmationCheck:
        """
        1. CANDLES - Direction and conviction
        CALL: Green candles (close > open), ideally Marubozu
        PUT: Red candles (close < open), ideally Marubozu
        """
        if direction == Direction.CALL:
            if data.candle_color == "GREEN":
                if data.candle_body_pct >= 0.8:  # Marubozu (strong conviction)
                    return ConfirmationCheck(
                        "Candles", ConfirmationResult.PASS,
                        "Strong green Marubozu - bulls dominating",
                        f"Green candle with {data.candle_body_pct:.1%} body"
                    )
                else:
                    return ConfirmationCheck(
                        "Candles", ConfirmationResult.PASS,
                        "Green candle - bullish direction",
                        f"Green candle with {data.candle_body_pct:.1%} body"
                    )
            elif data.candle_color == "DOJI":
                return ConfirmationCheck(
                    "Candles", ConfirmationResult.FAIL,
                    "Doji candle - indecision, no conviction",
                    f"Body only {data.candle_body_pct:.1%} of total range"
                )
            else:  # RED
                return ConfirmationCheck(
                    "Candles", ConfirmationResult.FAIL,
                    "Red candle conflicts with CALL direction",
                    f"Red candle with {data.candle_body_pct:.1%} body"
                )

        else:  # PUT
            if data.candle_color == "RED":
                if data.candle_body_pct >= 0.8:  # Marubozu
                    return ConfirmationCheck(
                        "Candles", ConfirmationResult.PASS,
                        "Strong red Marubozu - bears dominating",
                        f"Red candle with {data.candle_body_pct:.1%} body"
                    )
                else:
                    return ConfirmationCheck(
                        "Candles", ConfirmationResult.PASS,
                        "Red candle - bearish direction",
                        f"Red candle with {data.candle_body_pct:.1%} body"
                    )
            elif data.candle_color == "DOJI":
                return ConfirmationCheck(
                    "Candles", ConfirmationResult.FAIL,
                    "Doji candle - indecision, no conviction",
                    f"Body only {data.candle_body_pct:.1%} of total range"
                )
            else:  # GREEN
                return ConfirmationCheck(
                    "Candles", ConfirmationResult.FAIL,
                    "Green candle conflicts with PUT direction",
                    f"Green candle with {data.candle_body_pct:.1%} body"
                )

    def _check_volume(self, data: MarketData) -> ConfirmationCheck:
        """
        2. VOLUME - High conviction
        Requirement: >1.2x average volume (high conviction)
        """
        if data.avg_volume_20 == 0:
            return ConfirmationCheck(
                "Volume", ConfirmationResult.UNKNOWN,
                "Cannot validate - no volume history",
                f"Current: {data.volume:,}, Average: Unknown"
            )

        volume_ratio = data.volume / data.avg_volume_20

        if volume_ratio >= 1.2:
            return ConfirmationCheck(
                "Volume", ConfirmationResult.PASS,
                f"High volume - {volume_ratio:.1f}x average",
                f"Current: {data.volume:,}, Average: {data.avg_volume_20:,}"
            )
        else:
            return ConfirmationCheck(
                "Volume", ConfirmationResult.FAIL,
                f"Low volume - only {volume_ratio:.1f}x average",
                f"Current: {data.volume:,}, Average: {data.avg_volume_20:,}"
            )

    def _check_vwap(self, data: MarketData, direction: Direction) -> ConfirmationCheck:
        """
        3. VWAP - Trend alignment
        CALL: Price above VWAP (bulls control)
        PUT: Price below VWAP (bears control)
        """
        if direction == Direction.CALL:
            if data.current_price > data.vwap:
                return ConfirmationCheck(
                    "VWAP", ConfirmationResult.PASS,
                    "Price above VWAP - bulls in control",
                    f"Price ${data.current_price:.2f} > VWAP ${data.vwap:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "VWAP", ConfirmationResult.FAIL,
                    "Price below VWAP - bears in control",
                    f"Price ${data.current_price:.2f} < VWAP ${data.vwap:.2f}"
                )
        else:  # PUT
            if data.current_price < data.vwap:
                return ConfirmationCheck(
                    "VWAP", ConfirmationResult.PASS,
                    "Price below VWAP - bears in control",
                    f"Price ${data.current_price:.2f} < VWAP ${data.vwap:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "VWAP", ConfirmationResult.FAIL,
                    "Price above VWAP - bulls in control",
                    f"Price ${data.current_price:.2f} > VWAP ${data.vwap:.2f}"
                )

    def _check_9_ema(self, data: MarketData, direction: Direction) -> ConfirmationCheck:
        """
        4. 9 EMA - Fast momentum
        CALL: Price above 9 EMA
        PUT: Price below 9 EMA
        """
        if direction == Direction.CALL:
            if data.current_price > data.ema_9:
                return ConfirmationCheck(
                    "9 EMA", ConfirmationResult.PASS,
                    "Price above 9 EMA - bullish momentum",
                    f"Price ${data.current_price:.2f} > 9 EMA ${data.ema_9:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "9 EMA", ConfirmationResult.FAIL,
                    "Price below 9 EMA - bearish momentum",
                    f"Price ${data.current_price:.2f} < 9 EMA ${data.ema_9:.2f}"
                )
        else:  # PUT
            if data.current_price < data.ema_9:
                return ConfirmationCheck(
                    "9 EMA", ConfirmationResult.PASS,
                    "Price below 9 EMA - bearish momentum",
                    f"Price ${data.current_price:.2f} < 9 EMA ${data.ema_9:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "9 EMA", ConfirmationResult.FAIL,
                    "Price above 9 EMA - bullish momentum",
                    f"Price ${data.current_price:.2f} > 9 EMA ${data.ema_9:.2f}"
                )

    def _check_21_ema(self, data: MarketData, direction: Direction) -> ConfirmationCheck:
        """
        5. 21 EMA - Slow trend
        CALL: Price above 21 EMA
        PUT: Price below 21 EMA
        """
        if direction == Direction.CALL:
            if data.current_price > data.ema_21:
                return ConfirmationCheck(
                    "21 EMA", ConfirmationResult.PASS,
                    "Price above 21 EMA - bullish trend",
                    f"Price ${data.current_price:.2f} > 21 EMA ${data.ema_21:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "21 EMA", ConfirmationResult.FAIL,
                    "Price below 21 EMA - bearish trend",
                    f"Price ${data.current_price:.2f} < 21 EMA ${data.ema_21:.2f}"
                )
        else:  # PUT
            if data.current_price < data.ema_21:
                return ConfirmationCheck(
                    "21 EMA", ConfirmationResult.PASS,
                    "Price below 21 EMA - bearish trend",
                    f"Price ${data.current_price:.2f} < 21 EMA ${data.ema_21:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "21 EMA", ConfirmationResult.FAIL,
                    "Price above 21 EMA - bullish trend",
                    f"Price ${data.current_price:.2f} > 21 EMA ${data.ema_21:.2f}"
                )

    def _check_spy(self, spy_data: MarketData, direction: Direction) -> ConfirmationCheck:
        """
        6. SPY - Market direction
        CALL: SPY bullish (above VWAP/EMAs, green candles)
        PUT: SPY bearish (below VWAP/EMAs, red candles)
        """
        # Simple SPY bias check based on candle color and VWAP
        spy_bullish = (spy_data.candle_color == "GREEN" and
                      spy_data.current_price > spy_data.vwap)
        spy_bearish = (spy_data.candle_color == "RED" and
                      spy_data.current_price < spy_data.vwap)

        if direction == Direction.CALL:
            if spy_bullish:
                return ConfirmationCheck(
                    "SPY", ConfirmationResult.PASS,
                    "SPY bullish - supports CALL direction",
                    f"SPY: {spy_data.candle_color} candle, ${spy_data.current_price:.2f} > VWAP ${spy_data.vwap:.2f}"
                )
            elif spy_bearish:
                return ConfirmationCheck(
                    "SPY", ConfirmationResult.FAIL,
                    "SPY bearish - conflicts with CALL direction",
                    f"SPY: {spy_data.candle_color} candle, ${spy_data.current_price:.2f} < VWAP ${spy_data.vwap:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "SPY", ConfirmationResult.FAIL,
                    "SPY neutral/mixed signals",
                    f"SPY: {spy_data.candle_color} candle, unclear VWAP relationship"
                )
        else:  # PUT
            if spy_bearish:
                return ConfirmationCheck(
                    "SPY", ConfirmationResult.PASS,
                    "SPY bearish - supports PUT direction",
                    f"SPY: {spy_data.candle_color} candle, ${spy_data.current_price:.2f} < VWAP ${spy_data.vwap:.2f}"
                )
            elif spy_bullish:
                return ConfirmationCheck(
                    "SPY", ConfirmationResult.FAIL,
                    "SPY bullish - conflicts with PUT direction",
                    f"SPY: {spy_data.candle_color} candle, ${spy_data.current_price:.2f} > VWAP ${spy_data.vwap:.2f}"
                )
            else:
                return ConfirmationCheck(
                    "SPY", ConfirmationResult.FAIL,
                    "SPY neutral/mixed signals",
                    f"SPY: {spy_data.candle_color} candle, unclear VWAP relationship"
                )

    def _check_qqq(self, qqq_data: MarketData, spy_data: MarketData, direction: Direction) -> ConfirmationCheck:
        """
        7. QQQ - Confluence check
        QQQ must match SPY direction for index trading
        For individual stocks: sector ETF must match stock direction
        """
        # Check if QQQ matches SPY direction
        spy_bullish = (spy_data.candle_color == "GREEN" and
                      spy_data.current_price > spy_data.vwap)
        qqq_bullish = (qqq_data.candle_color == "GREEN" and
                      qqq_data.current_price > qqq_data.vwap)

        spy_bearish = (spy_data.candle_color == "RED" and
                      spy_data.current_price < spy_data.vwap)
        qqq_bearish = (qqq_data.candle_color == "RED" and
                      qqq_data.current_price < qqq_data.vwap)

        if (spy_bullish and qqq_bullish) or (spy_bearish and qqq_bearish):
            return ConfirmationCheck(
                "QQQ", ConfirmationResult.PASS,
                "QQQ matches SPY direction - confluence confirmed",
                f"SPY: {spy_data.candle_color}, QQQ: {qqq_data.candle_color}"
            )
        else:
            return ConfirmationCheck(
                "QQQ", ConfirmationResult.FAIL,
                "QQQ conflicts with SPY direction - divergence",
                f"SPY: {spy_data.candle_color}, QQQ: {qqq_data.candle_color}"
            )

    def _check_support_resistance(self, data: MarketData, levels: LevelData, direction: Direction) -> ConfirmationCheck:
        """
        8. SUPPORT/RESISTANCE - Clear levels
        CALL: Either clear of resistance OR confirmed breakout
        PUT: Either clear of support OR confirmed breakdown
        """
        current_price = data.current_price

        if direction == Direction.CALL:
            # Check resistance levels
            nearby_resistance = [r for r in levels.resistance_levels if abs(r - current_price) <= (current_price * 0.01)]  # Within 1%

            if not nearby_resistance:
                return ConfirmationCheck(
                    "S/R", ConfirmationResult.PASS,
                    "Clear of resistance - no overhead resistance",
                    f"Price ${current_price:.2f} clear of resistance levels"
                )
            else:
                closest_resistance = min(nearby_resistance, key=lambda x: abs(x - current_price))
                if current_price > closest_resistance and data.volume > data.avg_volume_20 * 1.2:
                    return ConfirmationCheck(
                        "S/R", ConfirmationResult.PASS,
                        "Confirmed breakout above resistance with volume",
                        f"Price ${current_price:.2f} > resistance ${closest_resistance:.2f} on high volume"
                    )
                else:
                    return ConfirmationCheck(
                        "S/R", ConfirmationResult.FAIL,
                        f"Near resistance at ${closest_resistance:.2f} - wait for break or pullback",
                        f"Price ${current_price:.2f} approaching resistance ${closest_resistance:.2f}"
                    )

        else:  # PUT
            # Check support levels
            nearby_support = [s for s in levels.support_levels if abs(s - current_price) <= (current_price * 0.01)]  # Within 1%

            if not nearby_support:
                return ConfirmationCheck(
                    "S/R", ConfirmationResult.PASS,
                    "Clear of support - no support underneath",
                    f"Price ${current_price:.2f} clear of support levels"
                )
            else:
                closest_support = min(nearby_support, key=lambda x: abs(x - current_price))
                if current_price < closest_support and data.volume > data.avg_volume_20 * 1.2:
                    return ConfirmationCheck(
                        "S/R", ConfirmationResult.PASS,
                        "Confirmed breakdown below support with volume",
                        f"Price ${current_price:.2f} < support ${closest_support:.2f} on high volume"
                    )
                else:
                    return ConfirmationCheck(
                        "S/R", ConfirmationResult.FAIL,
                        f"Near support at ${closest_support:.2f} - wait for break or bounce",
                        f"Price ${current_price:.2f} approaching support ${closest_support:.2f}"
                    )


def format_confluence_result(result: ConfluenceResult) -> str:
    """Format confluence result for display"""
    output = []
    output.append(f"\n{result.symbol} {result.direction.value} CONFLUENCE CHECK")
    output.append("=" * 50)
    output.append(f"Timestamp: {result.timestamp}")
    output.append(f"Setup Strength: {result.setup_strength:.1%} ({result.passed_count}/8)")
    output.append(f"Verdict: {result.verdict}")
    output.append("")

    for conf in result.confirmations:
        status = "✓" if conf.result == ConfirmationResult.PASS else "❌" if conf.result == ConfirmationResult.FAIL else "?"
        output.append(f"{status} {conf.name}: {conf.reason}")
        output.append(f"   {conf.details}")

    output.append("")
    if result.verdict == "HIGH_PROBABILITY":
        output.append("🎯 TAKE THE TRADE - All confirmations aligned")
    elif result.verdict == "WEAK_SETUP":
        output.append("⚠️  WEAK SETUP - Consider waiting for cleaner entry")
    else:
        output.append("🛑 SKIP THE TRADE - Missing confirmations")

    output.append("=" * 50)
    return "\n".join(output)


# Example usage and testing
if __name__ == "__main__":
    # Test data
    spy_data = MarketData(
        symbol="SPY",
        current_price=502.20,
        volume=2100000,
        avg_volume_20=1200000,
        vwap=501.80,
        ema_9=501.90,
        ema_21=501.60,
        candle_color="GREEN",
        candle_body_pct=0.85,
        high=502.50,
        low=501.50,
        close=502.20,
        open=501.60
    )

    qqq_data = MarketData(
        symbol="QQQ",
        current_price=380.50,
        volume=1800000,
        avg_volume_20=1000000,
        vwap=380.20,
        ema_9=380.30,
        ema_21=380.00,
        candle_color="GREEN",
        candle_body_pct=0.75,
        high=380.80,
        low=379.90,
        close=380.50,
        open=380.00
    )

    level_data = LevelData(
        pdh=503.00,
        pdl=500.20,
        pdc=501.80,
        support_levels=[500.20, 500.80, 501.00],
        resistance_levels=[502.50, 503.00, 503.50]
    )

    validator = ConfluenceValidator()
    result = validator.validate_all_confirmations(
        symbol="SPY",
        direction=Direction.CALL,
        market_data=spy_data,
        spy_data=spy_data,
        qqq_data=qqq_data,
        level_data=level_data
    )

    print(format_confluence_result(result))