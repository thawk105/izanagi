## 変更の要約

`scratch/t2812_old_series_probe.py` に 2 点を追加しました。

- `K2-LOCK-PAIR`: 現行 codec の例外を `current_codec` に保持し、`decode_historical_campaign_lock()` の結果を `historical_codec` に記録。
- `POLICY-SERIES-PIN`: 指定位置に追加。production decoder で正規化し、`pin_full`・`pin_short`・全 `preimage`・`sha256`・`comparison` を記録。

## 不変の確認

既存 check の呼出し・kwargs、`--out` の create-only 処理は維持。policy の発行・保存・適用は追加していません。実走で `READONLY: ok`、既存 check の ok/err は前回と同一でした。

## 実走結果

`py_compile`、`check_codex_agents.py`、`check_docs.py`、差分検査は成功。[実走 JSON](/tmp/t2812-probe-fix-series-pin.json)

```text
K2-PIN-NEW: err
K2-PIN-H: ok
POLICY-CURRENT: ok
K2-LOCK-PAIR: err
A1-BOUNDARY-NEW: err
A1-BOUNDARY-H: ok
A1-SOURCE-NEW: err
A1-SOURCE-H: ok
A1-IDENTITY: ok
G1-LOAD: ok
G1-LAUNCH: err
G1-BINARIES: ok
G1-BIN-HIST: ok
G1-BIN-CURRENT: err
B4-PROTOCOL: err
B4-RECORD-HIST: ok
B4-RECORD-CURRENT: err
B4-W1-HEAD: ok
READMIT-STOCK: ok
POLICY-SERIES-PIN: ok
READONLY: ok
```

K2 は現行 codec が拒否、歴史 codec は成功。旧系列 pin では G1 全 12 receipt・B4 の SHA と A1 preimage が一致し、K2 preimage は不一致でした。現行 pin では現行 policy SHA と K2 preimage が一致しました。

## 未了・懸念

実装・実走の未了なし。テスト・docs の追加、commit は行っていません。

## 総括

指定の 2 点を実装・実走済みです。現行 codec の拒否を保持し、系列 pin による一致・不一致を記録できました。