# [T-409] 実装 wave 段 1 brief — trigger 軸 EVOLVE-BLOCK hole 受理文法 v1 の機械 gate 化

基準 main = 6e22c5b (worktree = worktree-wave-t409-impl-trigger-grammar)。設計正本 =
`output/insights/2026-08-04_t409-evolve-hole-allowlist/` (文法 v1・must-fix 8 件・裁定は再導出しない)。

## scope (確定済みユーザー裁定 2026-08-04 /rulings、worklog (171))

- 文法 v1 (BNF、`!` なし、数字なし) の recognizer を**新規モジュール**に実装。判定順
  `type → raw size → character → token count → parse/depth → semantic` を凍結。上限 4096 byte /
  512 token / 深度 64。署名 `check_trigger_gate_implementation(implementation: str) -> GateLanguageResult`、
  `reason_code` は閉じた enum、入力本文・未知 token・文字位置を返さない。
- **択一 1 = (b) 封印済み receipt**: 合格時に receipt を発行し build 境界が要求。既存
  `build_admission.py` の GeneratorReceipt/ReviewReceipt と同じ封印様式で、cache preimage と WAL へ束縛。
- **択一 2 = 再検査**: 既存 cache・WAL・S8B resume 実体は source bytes から再検査 (cold invalidate も overlay もしない)。
- **択一 3 = 契約を狭める**: 数値 literal は文法に入れない。role 定義 (.claude/agents/coder-v4-autonomous-trigger-gating.md) の変更は**裁定で明示承認済み**。B-10 に従い adapter JSON sha 群・manifest・review ledger と同一変更単位。
- **択一 4 = trigger のみ** (backoff は [T-441]、sort は [T-410])。**択一 5 = freeze 回帰テストは [T-442]** — 本 wave に含めない。
- must-fix 8 件 (A2-1/A2-5/A2-8/A2-15+B-1/B-2/B-4/B-6/B-10) を全て閉じる。特に A2-15/B-1: `s1_verify_extime_calibration.py:329-357`・`p3_s4_loop.quarantine()`・`patchharness`・`pipeline.evaluate()`・`buildcache` の全 materializer 面を receipt 要求で閉じる。

## 不変条件 (親実測済み)

- **checked-in freeze (`output/s1-freeze/known_axes_freeze.json`) が live sha を pin するのは
  `axis_trigger_gating.py`・`s8a_trigger_sweep.py`・`s1_known_axes_freeze.py` の 3 本** (親が freeze JSON を実読)。
  この 3 本の bytes は変えない。gate は新規モジュール + 非 pin ファイルの配線だけで実現する。
- 基準 main c642263→6e22c5b の差分は T-340/T-407/reflux_ir 系のみで、gate 関連・role 関連ファイルは不変 (親が diff --stat で実測)。凍結 file:line 参照は有効。
- 旧 blacklist (`SYNTAX_CONTRACT_FORBIDDEN` 5 識別子) は**残す** — 新 gate は真に強い側 (B-7: 新 gate 合格 ⊂ 旧合格)。既存被覆の純増分 = `izanagi_gate_pass = true; pro_set_.pop_back();`、`= 1;` 等の拒否。
- 正例 9 件 (positive-controls.txt の trigger 代入式のみ) が新 gate に合格すること。26 件全部ではない。
- gate 入力の実在 (DW-O13): `CoderProposalTriggerGating.implementation` と calibration target の `gate_predicate` の**両名で同じ値が流れる**。(P1) 親 provisional 裁定: recognizer は「hole 置換文字列」単一概念を検査し、呼び出し面ごとに field 名を明記して二義化を避ける — 攻撃対象。
- semantic 段: `reason=kUnset` 評価が True でなければ拒否 (D48 fail-safe sentinel)。

## 成果物影響 (DW-G05)

gate 未実装のままだと文法外 implementation (workload 縮小系) が certified 選択へ到達しうる —
「gate 済み」認証が偽になる。receipt 束縛が無いと gate 導入前 binary が cache hit で新 gate 合格相当として材料レポートへ混入する。

## 成果物の形・受入

- 新規 recognizer モジュール + receipt 発行/検証 + build 境界の要求 + 再検査経路 + 境界テスト
  (A2-5 の token 境界、A2-4 の 128 truth-table 照合、正例 9/拒否例) + 新 D fragment (D96 手続: 新 D + 境界テスト)。
- 受入 = Pegasus login node から `tools/run_tests.py` (gen_S dispatch)。変異 matrix は段 4 で事前登録。

## 並列分割方針 (段 5)

- 実装子 A (codex author): recognizer モジュール + 境界テスト (新規ファイルのみ、既存面に触れない)。
- 実装子 B (codex author): receipt 発行/検証 + materializer/build 境界の配線 + 再検査 + role/adapter/manifest/ledger 同一単位。
- 所有分離: A = 新規 2 ファイル、B = 配線面。衝突なし。docs (新 D fragment、worklog fragment) は親。

## (P2) 親 provisional 裁定 — 攻撃対象

- (P2) receipt の設計は既存 `build_admission.py` の封印様式 (issued flag + 発行関数限定) を踏襲し、
  grammar version 識別子 `trigger-gate-language/v1` を receipt body・cache preimage・WAL entry に含める。
- (P3) 「再検査」の実装 = cache/WAL/S8B resume の読み出し面で、receipt 欠落実体は source bytes から
  recognizer を再実行して合格なら受理・不合格なら reject (規律 2: 合格したことにしない)。
