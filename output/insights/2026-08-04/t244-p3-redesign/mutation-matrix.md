# 変異 matrix — [T-244] P3 origin ledger prototype (2026-08-04)

対象 commit: e6349be (統合 commit)。harness = `tools/mutation_harness.py`、runner-mode = dispatch
(計算ノード)、baseline = PASSED (21 passed)。

## 最終会計

**24/24 KILLED、SURVIVED 0、TIMEOUT 0。**

- run1 (`mutation-ledger-run1.json`、spec = `mutation-spec-runtime-v1.json`、sha `2b1194a8…`):
  20 KILLED (matching) / 4 MISMATCH (M-N1, M-N2, M-N3, M-N7)
- run2 (`mutation-ledger-run2.json`、spec = `mutation-spec-runtime-v2.json`、sha `ac98fcdf…`):
  上記 4 件を期待 node 集合の是正後に再走し 4/4 KILLED (matching)

## erratum 1 — run1 の MISMATCH 4 件 (`DW-M02`: 初回結果は消さない)

4 件とも**期待 node は実際に赤**で、加えて連鎖赤 (superset) が出た。原因は事前登録の期待
node 集合が狭すぎたこと — 例: M-N1 (origin digest から manifest field を除外) は共有 fixture の
manifest を通じて 16 vector が崩れる。これは変異意味論どおりの過剰検出であり、検出漏れではない。
run2 は期待集合を run1 実測へ広げた再走で、operator・anchor は不変。

## erratum 2 — 凍結 spec と実行 spec の差分

委譲起草の凍結 spec (`mutation-spec.json`、sha `4bdf363d…`) は M-N12 を
category=`diagnostic-sensitivity` と注記したが、harness の許可集合は
{negative, positive, both-layers} の 3 値のため、実行 spec では `negative` へ写像した。
**M-N12 の分類上の扱いは diagnostic sensitivity pin のまま** (`DW-M08` 別枠) であり、
KILLED 23 + pin 1 と読むのが正しい。

## 登録上の限定 (s6-adjudication-r3 の裁定)

- M-A2 は「global flock の除去」operator (登録時の「per-origin 置換」は単一点変異で表現不能、
  erratum 済み)。global 直列化の担保はこの operator + cross-origin vector の範囲に限る
- M-A5 は both-layers (replay gate + exact-continuation の同時除去)。kill が証明するのは
  「altered continuation の受理拒否」まで。別 operation の排他は多層防御であり変異では証明しない
- M-N11 (旧) は Δ4 改訂で operator の前提が反転したため retire。M-N11r が後継
