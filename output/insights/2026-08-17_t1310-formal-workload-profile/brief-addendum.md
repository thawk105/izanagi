# 段 1 brief 追記 — 親の実測で判明した新事実 (段 4 で再裁定する)

計測時刻 2026-08-17 23:00〜23:05 JST、worktree `t1310-formal-workload-profile` (main `2a3b5055` 同値)。

## 実測 1 — ratified (v2) 経路は現在動かない

library 経路の probe (`orchestrator.campaign.s8b_ratified_freeze.load_ratified_freeze(root)`) は例外で終わる。

```
RatifiedFreezeError: [no-active] live active pointer が無い (v2 未発効)
  raise 位置 orchestrator/campaign/s8b_ratified_freeze.py:1274 (resolve_active_generation)
```

CLI ではなく library 経路で採った診断である。

## 実測 2 — v1 凍結には正式 holdout が実在する

`output/s8b-freeze/holdout_freeze.json` (schema `8b-holdout-freeze/v1`、27942 bytes) は次を持つ。

- `holdouts.rr80` の field: `candidate_id` = `H1`、`ycsb.ycsb_zipf_skew` = `0.9`、
  `ycsb.ycsb_rratio` = `80`、`ycsb.ycsb_rmw` = `0`、`records` = `1000000`、`threads` = `48`
- `holdouts.rr20` は同形で `ycsb.ycsb_rratio` が `20`

> **defang 記録 (D88)。** この 2 項は当初 inline JSON の正規形で書いており、その形が
> `s8b_holdout_freeze` の三軸 conjunction に一致して repo scan invariant を 0 hit から 1 hit へ
> 壊した (親が `holdout_conjunction_hits` で実測)。原文 bytes の sha256 =
> `1390508f59c26def1022a88e52cd68869d0ded6f5adab449fe1072e68e5719b5` (2872 bytes)。
> 変換は「inline JSON の `"key": "value"` 表記を `` `key` = `value` `` の並記へ開く」だけで、
> 値・単位・意味は 1 つも変えていない (可逆)。
- v1 loader は `orchestrator/campaign/s8b_freeze_io.py:41` `load_verified_freeze(path, expected_hash=None)`

## 実測 3 — 直接構築を禁じる設計テストがある

`orchestrator/tests/test_s8b_ratified_freeze.py:2232`
`test_no_production_module_constructs_ratified_freeze_directly` は production module が
`RatifiedFreeze` を直接構築することを禁じる。実装は必ず loader を経由しなければならない。

## これで brief の (P1) は「値の出所」を確定していないと判明した

追加の択を立てる。

- **(P1a)** 値も世代 identity も ratified 経路のみから採る。v2 発効まで正式 profile は fail-closed で
  停止する。C01 の静的要求 (call の到達可能性・`sha256`/`holdouts` 参照) は満たされるが、実走は不能。
- **(P1b)** 値は v1 (`load_verified_freeze`)、世代 identity は ratified 経路から採る。v2 未発効でも
  正式 profile が走るが、値の出所が二源になる。
- **(P1c)** ratified を既定とし、v1 を明示 opt-in の暫定源として許す。

**親の暫定裁定 = (P1a)。** 理由 = 二源は「どちらの値で測ったのか」を成果物から判別できなくし、
正式 scale を偽る余地を作る。ただし **(P1a) は「C01 を静的に満たすが実走は一度も成立しない」形であり、
恒真な保証の一形態である。**段 3 のレンズはここを正面から攻撃せよ。

## 成果物影響 (この追記の分)

(P1a) を採ると、本 wave 単独では**正式受理集合は空のまま**である。したがって本 wave の記録に
「[T-822] (i) の受理集合が非空になった」と書いてはならない。塞いでいる前提が
「producer に rr80 が無い」から「v2 世代が未発効」へ移ったことを worklog に書く。
