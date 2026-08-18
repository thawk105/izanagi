# 段 1 brief — [T-338] 投入 gate (2026-08-18)

wave = dev-wave-t338-submission-gate / branch `worktree-dev-wave-t338-submission-gate`
親 = Claude (dev-wave manager)。実装面は Codex `role=author` (D95)。

## 確定済みユーザー裁定 (2026-08-18 第 7 束)

- **T-338 Q1 = 択 (a)**「投入 gate を 1 単位で完成」。**条件付き** —
  「着手前に規模の見積りを実測で出し、**D205 / D220 の水準に触れるなら同 wave 内で範囲を切り直す**」。
- 保存: 順序 `producer → pilot → validator/consumer → 本走`、`pilot_submission = forbidden`
  (D292)、規律 2 を緩める方向の変更を採らない。
- Q2 (D229 決定 (8) の必須 kill 3 件の帰属段) は**未裁定**。本 wave は producer 段ではないため非閂。
- Q3 は D500 決定 (6) が既に「再利用先の確定は次 wave の段 1 要件」と定めており、本 brief が果たす。

## 実測 (すべて本 wave が一次資料から測った。段 4 の攻撃対象)

| 測った対象 | 値 | 出典 |
|---|---|---|
| 承認済み受領証 schema | 1,326 行 / object schema 106 / property 338 / required 338 / definitions 53 / array 26 | `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json` |
| 承認済み cross-field 制約 | §6 = 10 節・箇条 41 件 | `.../record-items-v2.md` §6 |
| schema 外の validator 必須責務 | §7.1 = 20 項目 (全件) | 同 §7.1 |
| 否定検査 | §8 = 8 field | 同 §8 |
| conformance vector | 正例 1 + §6 各制約に負例 1 本以上 (≥42 本)、digest を manifest が pin | 同 §7 |
| 受領証 1 本の規模 | `planned_execution.runs[]` = 36 × 8 = **288 要素** (pilot の `consumed_cluster_slots` は exact `[1..8]`) | 同 §6.8 / §7.1(5) |
| 既存 validator 密度 A | `qualification/artifacts.py` 1,187 行 ÷ t126 schema 群 property 170 = **6.98 行/property** | 実測 |
| 既存 validator 密度 B | 既存 validator 6 本の 行/raise = 8.9 / 10.3 / 10.5 / 14.3 / 15.3 / 20.9 (中央値 **12.4**) | 実測 |
| repo の test/production 行比 | 286,117 / 131,045 = **2.18** | 実測 |

**見積り (2 尺度が収束):** 固定 semantic validator 1,100〜2,400 行、manifest+resolver+祖先検査
400〜800 行、`PreregBinding`+受領証 writer 250〜450 行、`submit_pilot`/`verify_receipt` 入口
150〜350 行 → **production 1,900〜4,000 行**、テスト込み総計 6,800〜14,200 行。

**D220 は「実見積り production 差分 645〜816 行」を D205 のプロトタイプ基準に照らして過大と
判定した。本件は下限で 2.3 倍、上限で 4.9 倍。裁定の切り直し条件は発動している。**

## 新事実 (承認済み裁定の前提を覆す。段 4 で再裁定する)

1. **B1 は実在する。** 凍結 schema を直接読んだ結果、`arms.*.compile.cmake_cache` は
   `{trace, add_analysis}` の 2 boolean を enum で pin した**申告値 object** であり、
   raw `CMakeCache.txt` の `fileRecord` は schema に**存在しない** (`compile_commands` は
   `fileRecord` として実在する)。§6.3 の 3 者照合の第 3 脚は再読対象を持たず、§8 はその field を
   受理入力に使うことを禁じている。
2. **D320 の「対象外 (不変)」に `正しさゲート (verifier / admission / 変異検査)` が明記されている。**
   T-139 の投入 gate は admission gate であり、gate 本体は D320 の見送り対象では**ない**。
   一方 gate が要求する bytes 級 provenance 部品 (§6.7 の append-only 全履歴検査、§6.10 の
   symlink 拒否・単一 fd、§7.1(19) の schema digest pin、conformance vector index の digest pin、
   T-139 V1 の イ / ウ) は D320 が「新設・維持は既定で見送り」と列挙した当のものである。
   T-139 裁定パッケージ V1 はこの 2 面を分けずに「3 つとも D320 の既定を上書きするか」と問うている。
3. **未実装の要求を実装しないことは「新設の見送り」であって「既存機構の撤去・緩和」ではない。**
   D320 は前者を既定で認め、後者だけを個別裁定に留保している。§6.7 / §6.10 の provenance 脚は
   現在 1 行も実装されていない (実測: `preregistration` package に gate 実装なし、
   `__all__` は 10 名前で 4 禁止名は不在)。

## (P1)〜(P4) 親の provisional 裁定 — 攻撃対象

- **(P1) 切り直しは「行数」ではなく「検査の階級」で行う。** D205 は「絶対規律と科学的妥当性に
  直接効くものだけを採り、それ以外の防御的堅牢化は既定で見送る」と書いており、行数上限を
  定めていない。よって A 級 (§6.1 参照整合性 / §6.2 planned↔actual 双射 / §6.3 規律 1 の
  trace-perf 分離照合 / §6.4 argv exact 比較 / §6.5 観測窓 / §6.6 schedule 再導出 /
  §6.8 slot 閉包 / §6.9 時間予算 / §8 否定検査 8 件) は全採用、
  B 級 (§6.7 の 8 脚全履歴 byte-prefix 証明、§6.10 の symlink 拒否・単一 fd、§7.1(19)、
  conformance vector digest pin) は D320 の既定に従い**新設を見送る**。
- **(P2) §6.7 は述語を保存し機構を粗くする。** `(family_root, ordinal)` の一意性と
  `k = 1` は**科学的妥当性 (累積有意水準のリセット防止)** に直接効くので採る。
  実装は現 tip の台帳読取 + 予約行の初出 commit が `measurement_checkout.repository_head` の
  祖先であることの確認までとし、8 脚の全世代 byte-prefix 走査は作らない。
- **(P3) B1 は新 approval payload (V1 の イ) を作らずに閉じる。** §6.3 の第 3 脚を
  **拒否専用**として実装する — 受理の根拠は `compile_commands` 実体の再読と `configure_argv`
  の macro 定義の一致だけとし、`cmake_cache` 申告値は不一致なら拒否するためだけに使う。
  §8 が禁じるのは「受理条件の入力」であり、拒否専用の使用はこれに当たらない。
  §6.3 本文自身が「1 つでも食い違えば拒否する」と拒否規則の形で書かれている。
- **(P4) 本 wave の成果物は「gate 完成」を名乗る。** (P1)〜(P3) で採らなかった脚は
  gate の**保証境界**として canonical decision に明記し、`preregistration.__doc__` と
  gate の返す構造化理由に逐語で載せる。恒真 deny stub は作らない
  (正例 conformance vector を受理し、負例を各制約ごとに拒否する)。

## 不変条件 (緩めない)

- `pilot_submission = forbidden` / `main_submission = forbidden` を 1 bit も動かさない。
  gate の完成は投入の解禁ではない。解除権威は D292 のまま。
- 凍結 bytes を変えない。`receipt-schema-v1.json` / `record-items-v2.md` /
  `erratum-core-s7-stresscheck-v2.md` / D282 payload は不変。
  pin 閉包の実測 = `preregistration/approval_payload.py` (`D282_DECISIONS_REF`,
  `APPROVED_BLOB_ROLES`)、`tests/test_t139_approval_payload.py`、
  `tests/test_t139_preregistration_binding.py` の 3 file のみ
  (`tools/dev_waves/*` と `campaign/t080_freeze_migration.py` の `receipt_schema` は別 namespace。実測)。
- 規律 2: 受理述語を弱める変異を採らない。採らない脚は「実装しない」と明記し、
  「検査した」と記録しない。
- D264 の 4 名前 (`resolve_effective_preregistration` / `PreregBinding` / `submit_pilot` /
  `verify_receipt`) は gate 完成と同じ commit でだけ export する。半 export しない。

## 成果物の形

1. `orchestrator/preregistration/` に gate 3 段 (承認 manifest 解決 → 祖先検査 → 受領証照合)。
2. approval manifest の実体 1 本 (D282 の既 land payload を trust root とし、新 payload を作らない)。
3. 固定 semantic validator (A 級 + (P2) の粗い §6.7)。
4. conformance vectors: builder + 正例 1 + 採用した各制約に負例 1 本以上。
5. canonical decision (B1〜B4 の閉じ方 + 保証境界 + 見送った脚の逐語列挙)。

## 並列分割方針

段 5 は編集ファイル所有が素集合になる 3 単位 —
A = manifest/resolver/祖先検査、B = 固定 semantic validator、C = conformance vector builder + 否定検査。
B が最大 (見積り 1,100〜2,400 行) なので B を先行させ、A/C を並列にする。

## 受入・実測環境

Pegasus。受入全走は `python3 tools/run_tests.py` を相対・素の名前ちょうどで背景投入。
lease は `tools/dev_wave_wait.py acceptance` で claim。焦点走は変更した production file の
検査側も含める。
