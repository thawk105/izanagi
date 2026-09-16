---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2213-inert-abc-measure
seq: 1
title: [T-2213] A+B+C patch stack の inert 要求は既存機構では stock 同等の緑に到達しないことを計算ノードで実測した (docs のみ、branch worktree-dev-wave-t2213-inert-abc-measure、実装面ゼロ・変異 matrix = 登録可能な変異なし)
---

## 本文

- D1936 項 17 の「既存機構で計算ノード実測」を、依頼どおり編集ゼロで行った。D1986 項 8
  (T-2518: 依存供給と CLI 入力をつなぐ最小の入り口を新設しない) は守り、既存 CLI
  (`condition_meaning_gate`) + 既存 generic dispatch + `git clone` / `git apply` + 既存の依存
  install prefix の**使い方**だけで走らせた。glue script は repo にも作っていない。稼働中の
  t548 wave が編集中の PBS には触れていない (probe の PBS を使わない経路)。
- **結果は不到達。** 計算ノード bnode006 / request `1832.nqsv` (queue 待ち 5.2 秒、会計照合済み) で
  `BACKOFF_MAX_US=1000` の inert 要求は supply 腕 **赤 `compile-command-drift`**、meaning
  `unestablished`、admitted=false。login node の生死確認と B / C family の補助実測
  (`BACKOFF_COUNT_WINDOW=0` / `BACKOFF_STEP_POLICY=0`) も同一判定で、前処理 bytes の digest は
  計算ノードと login で一致 (環境に依らない)。
- 不到達の原因は独立に 2 つ (どちらも構造)。(1) 判定器は stock 比較で「要求 macro と同じ
  patch family の define」しか compile command から除外しない (`condition_meaning_gate.py`
  2252–2258 行) ので、3 patch 13 macro を同時に当てた木ではどの macro を要求しても他 2 family の
  `-D` が残り bytes 比較の手前で赤になる。(2) 判定器の関数で再生したところ、13 macro を全部許容
  しても bytes は一致しない — patch A/B/C は `include/backoff.hh` の `Backoff` class を無条件に
  書き換えており (root 正規化後の残差 2 hunk・+72/−5 行)、`stock-inert-mismatch` になる。
  `silo-backoff-fixed.patch` のような `#if … #else <stock 原文>` 構造ではない。
- 改修が要るなら (a) 判定器の family 許容を multi-patch stack へ広げる (共有防壁の改造、負例変異が
  要る) か (b) patch A/B/C を stock 原文を残す `#if` 構造へ作り直す (B10 系列は
  `patch_stack_sha256` に束縛されるため別 stack になる) のどちらか、または両方。(a) だけでは (b) の
  赤が残る。**実装していない。** 規律 2 の射程 (正しさ防壁) なのでユーザー裁定の対象。
- 親が踏んだこと: login で `cmake --build` を guard に拒否され既存 prefix へ切替、`--configure-arg -D…`
  の空白区切りを argparse に拒否され等号形へ、helper script を verbatim へ写して「probe を repo へ
  入れない」規律で除去し scratch へ保全。
- 素材: adaptive const driver の条件関門 3 要素のうち supply 腕は、現行の patch 構造と判定器の
  組み合わせでは機械証拠を持てない。証拠は
  `output/insights/2026-09-16/t2213-inert-abc-measure/README.md`。

## 次の一手差分

### 完了

- [T-2518] D1986 項 8 のとおり最小の入り口は新設せず、A+B+C 適用木と clean stock の supply 比較を
  既存機構の使い方だけで計算ノード実測し (`1832.nqsv`)、「測れていない」から「測った・不到達」へ
  記述を更新した (`output/insights/2026-09-16/t2213-inert-abc-measure/README.md`)。13macro witness
  新設・production 配線は含めていない。残りは [T-2213] へ集約。
  remaining: none
  base: f8e57b6a755882bc3c42a08b5ed99e60f872bdc666ea477735f6c2d36c2dc25b

### 更新

- [T-2213] **P2・実測済み・不到達・改修の要否はユーザー裁定待ち (規律 2 の射程)**: D1936 項 17 の
  計算ノード実測を 2026-09-16 に完了 (`1832.nqsv`、bnode006)。A+B+C stack の inert 要求は
  supply 腕が `compile-command-drift` で赤、原因 1 (判定器の family 単位の許容) を解いても原因 2
  (patch A/B/C の無条件書換で bytes 不一致) で `stock-inert-mismatch`。到達させるには判定器の
  multi-patch stack 対応か patch の `#if` 構造への作り直しが要る。D1856 の繰延べは維持。
  証拠 = `output/insights/2026-09-16/t2213-inert-abc-measure/README.md`。
  成果物影響 = 裁定まで adaptive const driver の certified receipt は supply 腕の機械証拠を持たない
  (現状と同じ)。
  base: 711719175f3ac9c53031df0446d07a1c12c71452abb90269c79ea55f1119f24a
