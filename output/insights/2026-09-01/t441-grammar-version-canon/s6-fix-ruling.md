# 段 6 fix 裁定 (親) — [T-441]

段 6 の敵対レビュー 2 本 (reviewA = 正しさ防壁・受理集合、reviewB = 充足・取り残し・盛りすぎ) と、
親が login node で実走した焦点走の結果を突き合わせた。

## 2 レンズが独立に一致した所見

- duplicate reader の既存 validator 差し替え (A F-01 / B B-03) — must-fix。親も独立に特定済み。
- 既存期待値 2 件が正本の変更に追随していない (A F-06 / B B-04) — must-fix。親の実走とも一致。
- 旧 cache key への fallback を実 lookup で殺せていない (A F-08 / B B-01、変異 M12) — must-fix。
- R-11 の「一続き」テストが production 配線を通っていない (A F-02 / B B-02) — should-fix。

## 単一レンズの所見のうち、親が実測で裏を取ったもの

- **A F-05 (共有 reject helper の既定が `None` でない)** — **real、must-fix。**
  親が独立に確認した結果、版を渡さない caller が実在する:
  `s6_sort_sweep.py:360`、`p3_s4_loop_sort.py:202,225,231`、
  `p3_s4_loop_trigger_gating.py:486`、`s8a_trigger_sweep.py:462`、
  `p3_b4_wiring_probe.py:1419`。既定が v1 のままでは、これら非 backoff campaign の
  reject variant id が backoff v1 に束縛され、既存 id と分裂する。
  裁定 R-3 の「既定経路は現行と 1 byte も変わらない」に直接反する。**これが本 fix の最重要点である。**
- **A F-04 (明示版と lock 版の不一致が発火しない)** — real、must-fix。
  WAL writer が lock 値を自動挿入するため比較が起きず、variant identity と WAL が別版に帰属しうる。
  裁定 R-2 の「版の producer は 1 本」が、この経路では恒真になっている。
- **A F-07 (変異 M2 が生存)** — real、must-fix。signature と helper の直接検査だけでは、
  `loop.py` / `pipeline.py` から版引数を外しても緑のままである。

## 直さない所見

- A F-03 (canonicalizer の到達不能な防御分岐) — nit。実装結果を変えない。除去は求めない。
- B B-05 (`resolve_evidence` の件数が 28/23 でなく 27/22) — nit。呼び出し漏れではなく監査件数の誤記。
  worklog には正しい値 (27 calls / 22 files) を記録する。
- B B-06 (共有 fixture の call site 20 箇所が完全列挙されていない) — nit。
  実装内容は妥当で、親の実走でもこれらに赤は出ていない。

## 期待値の更新を許可する 2 箇所

D901 条項 1 が同型の場合に「設計正本を優先し、既存テストの側を直す」と明示した先例に従う。
更新は次の範囲だけとし、他の assert は触らせない。

- **X-1:** `test_quarantine_passes_clean_backoff_value` の材料化綴り `20.0` → `20`。
- **X-2:** `test_reflux_off_reject_keeps_wal_and_whiteboard` の `BUILD_START.payload` key 集合へ
  `backoff_grammar_version` を 1 key 追加。ABORT 側は変えない。

## 変異 matrix の中間判定 (DW-M02)

reviewA が 12 件を判定し、M2 と M12 の 2 件が SURVIVE と結論した。
いずれも「所見ゼロ」ではなく実効 gate への再照準が必要な型なので、D-4・D-5 として fix に含める。
fix 後に `DW-M07` に従い anchor を再検証してから本走する。

## 分割

fix 子 1 本。所見が版の producer と identity / WAL / source / cache の consumer という
同じ契約を跨ぐため分割しない。
