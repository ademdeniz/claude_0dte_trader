"""
Technical Indicators for 0DTE Trading

Implements the core indicators needed for the 8-confirmation framework:
- VWAP (Volume-Weighted Average Price)
- EMA 9 and 21 (Exponential Moving Averages)
- Volume analysis
- Candle pattern recognition
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume-Weighted Average Price (VWAP)

    Args:
        df: DataFrame with columns ['high', 'low', 'close', 'volume']

    Returns:
        Series with VWAP values
    """
    if not all(col in df.columns for col in ['high', 'low', 'close', 'volume']):
        raise ValueError("DataFrame must contain 'high', 'low', 'close', 'volume' columns")

    # Typical price (HLC/3)
    typical_price = (df['high'] + df['low'] + df['close']) / 3

    # VWAP = sum(typical_price * volume) / sum(volume)
    cumulative_volume = df['volume'].cumsum()
    cumulative_price_volume = (typical_price * df['volume']).cumsum()

    # Avoid division by zero
    vwap = cumulative_price_volume / cumulative_volume.replace(0, np.nan)

    return vwap


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average

    Args:
        series: Price series (typically 'close')
        period: EMA period (9 or 21 for our strategy)

    Returns:
        Series with EMA values
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_volume_ratio(df: pd.DataFrame, lookback_period: int = 20) -> pd.Series:
    """
    Calculate current volume as ratio of average volume

    Args:
        df: DataFrame with 'volume' column
        lookback_period: Period for average calculation (default 20)

    Returns:
        Series with volume ratios
    """
    avg_volume = df['volume'].rolling(window=lookback_period).mean()
    volume_ratio = df['volume'] / avg_volume

    return volume_ratio


def analyze_candle_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze candle patterns and body percentage

    Args:
        df: DataFrame with OHLC data

    Returns:
        DataFrame with added columns:
        - 'candle_color': 'GREEN', 'RED', or 'DOJI'
        - 'body_pct': Percentage of total range that is body
        - 'body_size': Absolute size of candle body
        - 'total_range': High - Low
    """
    result_df = df.copy()

    # Calculate candle metrics
    result_df['body_size'] = abs(df['close'] - df['open'])
    result_df['total_range'] = df['high'] - df['low']

    # Avoid division by zero
    result_df['body_pct'] = result_df['body_size'] / result_df['total_range'].replace(0, np.nan)

    # Determine candle color
    conditions = [
        df['close'] > df['open'],  # Green candle
        df['close'] < df['open'],  # Red candle
    ]
    choices = ['GREEN', 'RED']
    result_df['candle_color'] = np.select(conditions, choices, default='DOJI')

    # Refine DOJI detection (body < 5% of total range)
    doji_mask = result_df['body_pct'] < 0.05
    result_df.loc[doji_mask, 'candle_color'] = 'DOJI'

    return result_df


def get_current_market_snapshot(df: pd.DataFrame) -> dict:
    """
    Get current market state from DataFrame (last row)

    Args:
        df: DataFrame with OHLCV data and calculated indicators

    Returns:
        Dictionary with current market state suitable for MarketData class
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    current = df.iloc[-1]

    # Calculate indicators if not present
    if 'vwap' not in df.columns:
        df['vwap'] = calculate_vwap(df)
    if 'ema_9' not in df.columns:
        df['ema_9'] = calculate_ema(df['close'], 9)
    if 'ema_21' not in df.columns:
        df['ema_21'] = calculate_ema(df['close'], 21)
    if 'volume_ratio' not in df.columns:
        df['volume_ratio'] = calculate_volume_ratio(df)

    # Get candle analysis
    candle_df = analyze_candle_pattern(df)
    current_candle = candle_df.iloc[-1]

    # Calculate average volume (last 20 periods)
    avg_volume_20 = int(df['volume'].tail(20).mean())

    return {
        'current_price': float(current['close']),
        'volume': int(current['volume']),
        'avg_volume_20': avg_volume_20,
        'vwap': float(current['vwap']) if not pd.isna(current['vwap']) else 0.0,
        'ema_9': float(current['ema_9']) if not pd.isna(current['ema_9']) else 0.0,
        'ema_21': float(current['ema_21']) if not pd.isna(current['ema_21']) else 0.0,
        'candle_color': current_candle['candle_color'],
        'candle_body_pct': float(current_candle['body_pct']) if not pd.isna(current_candle['body_pct']) else 0.0,
        'high': float(current['high']),
        'low': float(current['low']),
        'close': float(current['close']),
        'open': float(current['open'])
    }


def calculate_prior_day_levels(df: pd.DataFrame) -> dict:
    """
    Calculate Prior Day High, Low, Close from yesterday's data

    Args:
        df: DataFrame with OHLC data (last row = yesterday's data)

    Returns:
        Dictionary with PDH, PDL, PDC levels
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    yesterday = df.iloc[-1]

    return {
        'pdh': float(yesterday['high']),
        'pdl': float(yesterday['low']),
        'pdc': float(yesterday['close'])
    }


def find_support_resistance_levels(df: pd.DataFrame, min_touches: int = 2, tolerance_pct: float = 0.5) -> Tuple[list, list]:
    """
    Find support and resistance levels based on price reversals

    Args:
        df: DataFrame with OHLC data
        min_touches: Minimum times a level must be touched
        tolerance_pct: Tolerance as percentage of price for grouping levels

    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    if len(df) < 10:  # Need minimum data
        return [], []

    # Find local highs and lows
    highs = df[df['high'] == df['high'].rolling(window=3, center=True).max()]['high']
    lows = df[df['low'] == df['low'].rolling(window=3, center=True).min()]['low']

    def group_similar_levels(levels, tolerance_pct):
        """Group levels that are within tolerance of each other"""
        if len(levels) == 0:
            return []

        levels = sorted(levels)
        grouped = []
        current_group = [levels[0]]

        for level in levels[1:]:
            # Check if this level is within tolerance of current group average
            group_avg = sum(current_group) / len(current_group)
            if abs(level - group_avg) / group_avg <= tolerance_pct / 100:
                current_group.append(level)
            else:
                # Start new group
                if len(current_group) >= min_touches:
                    grouped.append(sum(current_group) / len(current_group))
                current_group = [level]

        # Don't forget the last group
        if len(current_group) >= min_touches:
            grouped.append(sum(current_group) / len(current_group))

        return grouped

    resistance_levels = group_similar_levels(highs.tolist(), tolerance_pct)
    support_levels = group_similar_levels(lows.tolist(), tolerance_pct)

    return support_levels, resistance_levels


# Example usage and testing
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='5min')
    np.random.seed(42)  # For reproducible results

    # Generate realistic OHLC data
    close_prices = 500 + np.cumsum(np.random.randn(100) * 0.5)

    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.randn(100) * 0.2,
        'high': close_prices + abs(np.random.randn(100) * 0.8),
        'low': close_prices - abs(np.random.randn(100) * 0.8),
        'close': close_prices,
        'volume': np.random.randint(100000, 2000000, 100)
    })

    # Ensure high >= close >= low and high >= open >= low
    sample_data['high'] = sample_data[['open', 'close', 'high']].max(axis=1)
    sample_data['low'] = sample_data[['open', 'close', 'low']].min(axis=1)

    print("Sample OHLC Data:")
    print(sample_data.tail())

    # Calculate indicators
    sample_data['vwap'] = calculate_vwap(sample_data)
    sample_data['ema_9'] = calculate_ema(sample_data['close'], 9)
    sample_data['ema_21'] = calculate_ema(sample_data['close'], 21)
    sample_data['volume_ratio'] = calculate_volume_ratio(sample_data)

    print("\nWith Indicators:")
    print(sample_data[['close', 'volume', 'vwap', 'ema_9', 'ema_21', 'volume_ratio']].tail())

    # Get current market snapshot
    snapshot = get_current_market_snapshot(sample_data)
    print(f"\nCurrent Market Snapshot:")
    for key, value in snapshot.items():
        print(f"  {key}: {value}")

    # Find support/resistance
    support, resistance = find_support_resistance_levels(sample_data)
    print(f"\nSupport Levels: {[f'{s:.2f}' for s in support]}")
    print(f"Resistance Levels: {[f'{r:.2f}' for r in resistance]}")

    # Prior day levels (using second-to-last row as "yesterday")
    yesterday_data = sample_data.iloc[:-1]  # Exclude today
    pd_levels = calculate_prior_day_levels(yesterday_data)
    print(f"\nPrior Day Levels:")
    for key, value in pd_levels.items():
        print(f"  {key.upper()}: ${value:.2f}")