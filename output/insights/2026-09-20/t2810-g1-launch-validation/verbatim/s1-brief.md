# 段 1 brief — [T-2810] 凍結 v2 g1 の full launch validation を通す (2026-09-20 19:2x JST、wave 木 HEAD = main `6a3e15809`)

**研究前進:** 凍結 v2 g1 の launch admission (`_launch_validate`) は W-4 (spec 承認) → W-5 (oracle 実走) → 8b 再開 (certified 選択) の土台。止めている実測 = runbook §2 P3 の g1 path が `allowed: false`。最小差分 = launch validator を official 成果物の現物形 (journal 文法・導入 topology) に整合させる 2 修正。完了判定 = (a) fixture 正例で `launch_validate` 成功 + 現物 topology (result を cert と同 commit で導入) の正例が受理される、(b) 実 repo で policy 照合なしの正規経路 `reverify_published_freeze` が段階 4〜7 を通過して段階 8 に到達する、(c) 負例 (未知 event / 片側 binding / 導入が C より前 / G の祖先でない / merge 導入 / G 偽装) が全部殺される。

**brief 前の前提実測で判明した新事実 (段 4 で再裁定の対象):**
- N1: 現行 main (`6a3e15809`、ccbench pin `e9e477ca`、policy epoch `db6bc9ea…`) の live P3 (g1 path) は `manifest-invalid: binaries[rr20::backoff_fixed_best] admission receipt … policy が現行 policy と不一致` で **journal 検査より手前 (段階 4)** で止まる。一次資料 §5 (journal-state-invalid) は T-2304 land 前の実測。D2184 は「live 経路へ `expected_policy=None` を入れない」「旧系列は pin 前進前の固定 checkout から、新 main への移行は T-2812」と決めており、本 wave は policy 照合を触らない。
- N2: journal の不整合は `reservation-preflight` (現物 12 key = producer の binding 付き形) だけでなく **`campaign-start` の binding 2 key (`pbs_jobid` / `submission_nonce`) も** `_JOURNAL_KEYS` (15 key exact) と不一致 (実測 `journal_keys_probe.py`)。producer は両 event とも `external_checkpoint_binding` の有無で 2 形を書く。
- N3: journal + 段階 6 を一時変異 (DW-O19、復元済み) して `reverify_published_freeze` を実 repo に走らせると、段階 4 semantic・5 binding・6 lineage・7 exemption を通過し **段階 8 の full scan で `closure-hit-mismatch` (rr80 未申告 hit = `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、X2 で main に載った未発効候補、世代文書と同 bytes)**。exact exemption は V1・世代文書・approval・pointer の 4 path のみ (設計どおり)。validator 修復では解けない chain 成果物側の問題 → 依頼の「別の不整合が出たら記録して止める」に当たる。
- N4: 現物 topology は cert C = result 導入 = X1' `cc82edc8c` = G^ (G `32ba8cae4`)。一次資料 §5 の α 文言「C < 導入 < G」は厳密には現物を満たさず、現物に合う述語は **C ≤ i ≤ G** (i = 各 path の一意導入 commit)。

**scope (実装、Codex author):** (1) `_JOURNAL_KEYS` の allowlist 追随 — `reservation-preflight` の追加と `campaign-start` の binding 2 key。(2) 段階 6 lineage の改訂 (P1)。(3) test: 正例 (現物 topology fixture、binding 付き journal)、負例 (上記 (c))、既存負例 `test_floor_source_introduction_must_be_exact_generation_commit` の維持。(4) `_ACTIVATED_G1_REFUSALS` を live P3 の実測 (N1 の 2 件) へ更新、comment を現状へ。(5) docs: runbook §2 P3 / §3 W-3 の現在形。
**scope 外 (記録のみ):** policy 照合 (D2184 / T-2812)、候補文書の scan hit (N3、裁定パッケージ候補 = 候補 file の削除 commit か別案)、W-4 / W-5 / certification、仮想リスク向け gate・台帳の追加、旧 pin 固定 checkout への修正 cherry-pick 実測 (P3 参照)。

**provisional 裁定 (攻撃対象):**
- (P1) 段階 6 = α の具体形: result / measurement_closure の各 path について導入 commit i を一意 (`_unique_introduction`)・非 merge とし、**C は i の祖先か同一、i は G の祖先か同一** を要求 (現物 i = C = G^ を受理、fixture i = G を受理)。加えて **世代文書 path (`_gen_path(N)`) の導入集合 == {G} を段階 6 に足す** (現行の「result 導入 == {G}」が担っていた G 偽装検出 (負例 wrong_g = A) を保つ。現物 G は世代文書 1 file を導入する commit なので到達可能)。cert C の条件 (一意・非 merge・C < G 厳密) は不変。docstring の保証境界を「I_entry ⊆ [C, G]」へ書き換える。β (G 作り直し = D2120 項 2 (b) 再裁定) と γ (導入条件を課さない = 受理集合を最も広げる) は採らない。
- (P2) journal = exact 集合方式を保ち、両 event とも **binding 付き形 (`pbs_jobid` + `submission_nonce`) と無し形の 2 形** を受理、ただし **journal 内で binding の claim 状態は両 event で一致** (片方だけ claim は拒否) し、claim 時は非空 str を要求。`reservation-preflight` の他 field の型は `floor_liveness._RESERVATION_BINDING_KEYS` と同じ形 (int > 0 / str 非空 / bool) を課す。fixture (binding 無し) は不変で通る。対案 = binding 必須 (official は PBS 下でのみ走る) — 受理集合は狭いが fixture 全更新が要り、producer が書き得る形を validator が拒否する。
- (P3) 実効性の実測経路 = 実 repo の `reverify_published_freeze` (段階 8 到達) + `assert_g1_floor_selection_identity` (live 経路だけが持つ選択 identity 検査の単独実測) + live `launch_validate` の実測 (N1、`_ACTIVATED_G1_REFUSALS` の新値)。旧 pin 固定 checkout への cherry-pick 実測は同じ結論 (段階 8 の候補 hit) しか出ないので省く。

**不変条件:** 規律 2 — 受理集合を広げるのは現物形 2 点 (binding key・導入 topology) だけで、scan 除外・policy 照合・cert 条件は不変。凍結 bytes pin: 変更 4 file の sha256 pin は 0 件 (DW-O09 実測)、B-10 freeze-tree pin (`output/s1-freeze` + `output/s8b-freeze`) は本 wave で動かない (候補 path も output/ 成果物も触らない)。`_JOURNAL_KEYS['session']` は `test_s8b_terminal_evidence.py` が同一 pin → 触らない。実装子は `orchestrator/` の code / test だけ、docs は親。

**成果物:** 実装 commit (Codex author、code + test) → 記録 commit (docs + insight `output/insights/2026-09-20/t2810-g1-launch-validation/README.md`)。変異 matrix (正例 1 + 負例 ≥ 6、独立 clone、計算ノード dispatch)。焦点走 = `test_s8b_ratified_verify.py`、`test_s8b_oracle_driver.py` (held 6 node は診断 token で)、`test_s8b_binding_driftguards.py`、`test_s8b_terminal_evidence.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`。
**分割方針:** 全 9 段 (設計択一が割れる + 受理集合が変わる + 正しさ防壁 = 3 条件すべて該当)。段 2 plan 1 本、段 3 相談 2 本 (A = 正しさ境界・受理集合の広がり・G 偽装、B = D2077 / D2184 / D2120 との整合・scope・N3 の扱い)、段 5 author 1 本 (所有 = `s8b_ratified_freeze.py` + 3 test file)、段 6 review 2 本 + fix。
**受入・実測環境:** 焦点走・変異・受入は Pegasus 計算ノード dispatch (login は P3 gate-check と probe だけ、所要は一般化しない)。DW-G05: 放置時は g1 の launch admission が旧 pin checkout でも新 main でも段階 4 (journal) で恒久拒否 = W-4 以降が着手不能、certified 選択の受理集合は変わらない (oracle 未実走)。

**変更面アンカー:**
| file | 行 | 内容 |
|---|---|---|
| `orchestrator/campaign/s8b_ratified_freeze.py` | 240–276 | `_JOURNAL_KEYS` (reservation-preflight 追加、campaign-start の binding) |
| 同 | 2039–2130 | `_validate_journal` の campaign-start / reservation-preflight 検査 (binding claim の整合・型) |
| 同 | 3160–3166 | docstring の保証境界 |
| 同 | 3540–3556 | 段階 6 lineage |
| `orchestrator/tests/test_s8b_ratified_verify.py` | 483–700 fixture、2838–2849 負例 | fixture option (result を C と同 commit へ) + 正例・負例 |
| `orchestrator/tests/test_s8b_oracle_driver.py` | 131–147 | `_ACTIVATED_G1_REFUSALS` |
| `docs/phase3-8b-restart-runbook.md` | 161、329–336 | P3 / W-3 の現在形 (親) |
