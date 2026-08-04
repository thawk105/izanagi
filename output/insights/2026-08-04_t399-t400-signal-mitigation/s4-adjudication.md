# 段 4 裁定 — dev-wave t399-t400-signal-mitigation (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`

段 2 プラン (`stage2-plan.md`)、段 3 レンズ A (正しさ境界、blocker 6 / must-fix 2 / nit 1)、
レンズ B (整合・実効性、blocker 3 / must-fix 8 / nit 1) を親が裁定した。親の独立照合:
B-B1 の wave-state (`t362-default` = completed / terminal_proven:false、sessions 0 件) と
軽量ツール実測 (check_codex_agents 0.16 s、check_codex_output 0.03 s) は現物確認済み。

## 所見の裁定 (すべて real、refuted 0 件)

| 所見 | 裁定 | 採否と対応 |
|---|---|---|
| A-B1 安全側 mitigation が qwait rc=9 要求で棄却 | real | 採用。qwait 検査を leg×結末別に: 安全側 = 正常終端 + bound 済み SIGTERM 証拠 + cleanup 完了、危険側 = rc=9 ELAPSE。scope 内 |
| A-B2 racct 丸ごと外しは束縛・因果検査の弱化 | real | 採用。3 分解: `accounting_available` (欠測のみ evidence 側) / `accounting_integrity_valid` (exact request・排他 ID・exact job 数) / `termination_cause_consistent` — 後 2 者は観測/verdict gate に残す。scope 内 |
| A-B3 attempt_safe が費用・hygiene と signal 危険を混同 | real | 採用。`probe_cleanup_outcome ∈ {safe,unsafe,unknown}` を新設し、危険結論は閉じた `unsafe_reason` enum (cleanup_order / canary 系) からだけ導出。budget・qdel・inventory hygiene は別 field。scope 内 |
| A-B4 復元後 canary の独立 readback が無く false-safe | real | 採用。observer が inventory cleanup 前に canary を再読し、bytes/hash を request・nonce へ束縛して保存。読取不能は unknown。scope 内 (observer も driver 内) |
| A-B5 v1 schema のまま意味変更で semantic collision | real | 採用。envelope schema を v2 へ。v1 loader 規則 = legacy true の既存 authority のみ維持 / legacy false・null は terminal closure のみで再認定しない / 未知 `evaluation_model` は拒否。プラン :49 と :156 の矛盾は :156 (completed legacy false は再評価しない) を正とする。scope 内 |
| A-B6 G_usable_lower 未定義 | real | 採用。事前登録文書に mode 別 `first_expected_signal`、採用層 = **Python parent の `finally_exit`** (grandchild heartbeat は下限記録のみで usable grace に昇格させない)、heartbeat 不在時 UNKNOWN、`R_restore_bound=null ⇒ sufficiency=UNKNOWN` を式で固定。scope 内 |
| A-M1 恒真・重複 predicate、test/mutation 欠如 | real | 採用。evaluator 純関数群への fixture test (safe / unsafe / accounting 矛盾 / canary 不一致 / legacy false / unknown model / terminal false) + B-057 変異を下記に事前登録。scope 内 |
| A-M2 / B-M5 retry 語彙が開いている・per-leg 上限なし | real | 採用。retryable infra reason を exact enum で事前登録、per-leg attempt cap = 2 (初回+再試行 1)、raw に signal 安全性の内容がある attempt は理由を問わず置換 retry 禁止 (初回 raw は常に保存)。scope 内 |
| B-B1 resolve→run が投入前に必ず停止 | real (実物確認済) | 採用。stale session なしの completed/terminal-unproven request に対する閉じた migration: 保存 raw (qwait rc=9 receipt 等) と state の対応を再検証してから終端実証へ移行する経路を `resolve` に追加。raw 再検証なしの昇格は禁止。scope 内 |
| B-B2 複合 predicate の丸ごと移動は観測 gate 弱化 | real | 採用。`cleanup_order_valid` と `artifact_inventory_cleanup_valid` を「identity・制御 prefix・証拠完全性」(observation 側に残す) と「cleanup/restore の結末」(safety 側) に分解してから分類。scope 内 |
| B-B3 変異 matrix 対象外 (P3) は契約と衝突 | real | **(P3) を修正**。authoritative 選出 gate の変更なので focused B-057 matrix を実施 (下記事前登録)。全 repo 受入全走は従来どおり対象外 (production 差分ゼロは維持) だが、driver 対象の focused test + 変異は義務。tools/mutation_harness.py + 専用 spec + run_tests.py 経由 (dispatch) で行う |
| B-M1 `.e` 改名順で第三経路が normal で不成立 | real | 採用。終端 proof を改名前に行うか、manifest の original hash/name で `.stderr.raw` bytes を照合して読む。scope 内 |
| B-M2 terminal_proven の canonical field・migration 契約 | real | 採用。canonical = 永続 request の `external_root_terminal_proven`。attempt 内根拠・resolve 由来の書換規則を実装で明記。未知 evaluation_model 拒否は A-B5 と同じ。scope 内 |
| B-M3 brief の 2 field と plan の 3 scalar の不一致 | real | **(P1) を supersede**: 本裁定で 3 分離 (observation_valid / attempt_safe / accounting 系) + A-B2/A-B3 の細分を正とする。`_signal_observation_valid` へ expected mode/request/attempt を明示的に渡し nested nonce と照合。scope 内 |
| B-M4 observer 240 s は worst case 未満 | real | 採用。実装定数から導出した上限 + 余裕 (導出式をコード内に置き、値のハードコード禁止)。scope 内 |
| B-M6 leg 間依存なし、直列投入・3600 s の根拠なし | real | **(P2) を修正**: 両 leg を同一 session で連続投入 (prequeue) してよい。mitigation 未決着でも split-warning を止めない。全体 deadline は per-leg QUE deadline 3600 s を維持しつつ、期限到達 leg は「T-399 partial」として未実測を明記 (両 leg 実測済みと偽らない)。brief の「唯一の未実測経路」は「採択 (a) の実験経路」に訂正 (T-360 には walltime 内完結・外部復元の代替設計が残る、(149)) |
| B-M7 survey が dispatch 面の全数調査でない | real | 一部採用。check_codex_output 0.03 s / check_codex_agents 0.16 s / check_wave_startup 約 1 s を親が実測し除外理由を凍結。worklog には「測った範囲の最大候補」と書き「残る直列費用はそれだけ」とは書かない。mutation harness 内側 pytest 990 s は束ねで消えない (T-357 決定 2) ことも明記 |
| B-M8 投入手順が runbook §8・失敗回収を満たさない | real | 採用。手順書 (verdict-preregistration.md 内) に walltime/node 数記録・OMP 非該当・§7.0 分類 (controller は login 可: 状態機械 + 15 s bounded 外部 command のみ)・単独性 (probe 側は fresh root + nonce 束縛で代替、pgrep は job body が compute 上で実行) ・失敗時 resolve 手順・operator 追跡表・crash 時の凍結先・RESULT 固定パスを列挙。scope 内 |
| A-N1 / B-N1 参照ずれ (F36/F38、行番号 △ 6 件) | real | 採用 (軽微)。実装時に現物行番号で再アンカー。F 番号の混同は段 8 の改善候補へ |

## plan v2 (段 2 プランへの差分命令)

1. schema v2 (`split-v2`)。3 scalar + 細分 field。v1 互換規則は A-B5 のとおり
2. qwait / accounting / cleanup / inventory の各複合 predicate を分解し、観測有効性側の
   基準を 1 つも落とさない (brief 不変条件 2 を維持したまま A-B1〜B-B2 を実装)
3. migration (B-B1) → resolve → `run --signal-legs-only` (対象 = mitigation, split-warning の
   閉集合、両 leg 連続投入、per-leg cap 2、retry enum 事前登録)
4. observer: 復元後 canary の独立 readback + 導出式による bounded finalization
5. evaluator 純関数の fixture test 一式を driver 配下 `test_run_probes_evaluator.py` に新設。
   canonical 全走には含めず、targeted 実行 + 変異 matrix の対象にする
6. 事前登録文書 `verdict-preregistration.md` は親が本裁定と同時に確定する (実測前凍結)

## 変異事前登録 (B-057、DW-M01。anchor は実装後 DW-M07 で確定)

runner = `python3 tools/run_tests.py <driver test nodeids> -p no:cacheprovider` (dispatch)。
各変異は単一理由 kill を fixture 側で確認してから matrix に載せる。

| # | 変異 (署名) | 期待 kill |
|---|---|---|
| G1 | authority 選出の `observation_valid and terminal_proven` → `or` | authority fixture |
| G2 | legacy `admissible:false` → `observation_valid:true` へ読替 | legacy fixture |
| G3 | `accounting_integrity_valid` を verdict gate から除去 | 会計矛盾 fixture |
| G4 | `unsafe_reason` enum 外からの危険結論許可 (hygiene 混入) | false-danger fixture |
| G5 | 安全側 mitigation 受理に rc=9 を要求 (A-B1 の逆変異) | safe-mitigation fixture |
| G6 | 未知 `evaluation_model` の受理 | unknown-model fixture |
| G7 | per-leg attempt cap の除去 | retry-cap fixture |
| G8 | migration の raw 再検証省略 (state だけで終端実証) | migration fixture |

## gate の禁止 (署名) と正例

- **禁止**: authoritative 選出は `observation_valid is True and terminal_proven is True`
  以外の組合せを受理しない。**正例**: mitigation 安全走 (observation_valid=true,
  terminal_proven=true, attempt_safe=true, accounting_available=false) は authoritative になる
- **禁止**: `evaluation_model` が「欠落 (=legacy)」「`split-v2`」以外の記録は拒否する。
  **正例**: split-v2 の新記録は受理される
- **禁止**: 危険結論 (`attempt_safe=false` の safety 帰属) は閉じた `unsafe_reason` enum
  以外から導出しない。**正例**: cleanup_order 不成立による unsafe は危険結論になる

## scope 外へ返すもの

- [T-402] (T-361 の Execution Host 照合による dangerous 確定) — 本 wave は触れない
- [T-401] のうち会計反映遅延幅の実測と bounded retry 設計 — 本 wave は欠測の分類まで
- T-360 の代替設計 (walltime 内完結・外部復元) の要否 — T-399 の実測結果と同時に判断
