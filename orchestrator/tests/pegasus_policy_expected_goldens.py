"""歴史記録は書き換えず、当時の policy binding と現行 bytes を別々に固定する。
無断 drift の検知根拠は、凍結 evidence ではなく現行 bytes の pin が担う。
"""

EXPECTED_CURRENT_PEGASUS_POLICY_SHA256 = (
    "b991c7499fb43802f2910b9f2cfa476643753e929e395877437e7307f07b667e"
)
EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256 = (
    "b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac"
)
