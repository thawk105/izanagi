# [T-2724] 凍結 v2 g1 の保存枝 chain (X1'/X2) と世代導入 G を main へ取り込む wave (2 回目) — merge・走査・焦点走は緑、受入全走が B-10 の freeze-tree byte pin 1 node で赤になり、chain は land せず記録だけを land する

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-19
- wave: dev-wave-t2724-chain-land-2 (branch `worktree-dev-wave-t2724-chain-land-2`)
- 起点の裁定: D2120 項 2 (a)(b)(d) (ユーザー裁定 2026-09-17)、D2154 (A-3 の実装形、main 着地済み entry 1683)、G wave の裁定 fragment (G wave の保存 commit `229982652` に未 fold のまま保全。「A-3 と test 修正を先に着地させてから chain + G を取り込む」)
- 基準: 着手直前の local main `2ba4000870c63254132410b3002b5298c0c6a210`。取り込み元 = `worktree-dev-wave-t2724-freeze-g1-gen` tip `22998265212c43a6b0f42051d7bf1b49735f77e9`、`freeze-g1-chain-t2724` tip X2 `4d8fb93b7c8d5466e9ad91b1bc5b600a2fdd7ac8`
- **保存枝 (本 wave の成果、land せず):** `t2724-chain-land-2-saved` = `0a799da6c53a9d769cdefa0358e1baecebaeeb8f` (= main `2ba400087` + merge `3440c6620` (229982652) + merge `87dcbe5a4` (X2) + 記録 commit `b217b24a7` + 受入 attempt 1 が作った merge `0a799da6c` (main `a99425b66`))。次 wave はこの枝か、元の保存枝 3 本を当時の main へ再 merge する
- 一次証拠: 同 dir `evidence/` (走査射影・焦点走要約・受入赤の junit 抜粋)。生 log は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-chain-land-2/` (寿命保証なし)、受入 shard は `/work/1/SFC/tanab/.izanagi-acceptance-shards/e818446e399fe09320c86bccd7f27afb/` (同)
- 可逆正規化 (D88 / DW-S07、可視文字不変): `evidence/focus-1-summary.txt` (原文 = 生 log `focus-1.log` から dispatch の状態行と `IZANAGI_DISPATCH_JOB_TRACE` 行を除いたもの、sha256 `2ed498d732273bf3ce492e168ad9571d1451b6a8800bfdbfa17e060e00f9655f`、6,966 byte → 行末空白除去後 `1a9703b27238d2c09c15c36908c1b7c7522215f5f38e22cc3154e454c7f4583f`、6,964 byte)、`evidence/acceptance-1-failure-excerpt.txt` (原文 = junit.xml の failure 要素を `junit-failure.py` で抽出、sha256 `bedf5aac188abb7041101f5db19fd1f8de1cd390376df4726699c2a816015404`、1,360 byte → 除去後 `24f9b5fc99d58223a666838d52d8d1cd61cc5aeb6b46643a5130493b7664ae8a`、1,349 byte)。いずれも `sed 's/[ \t]*$//'`、復元は原文の再抽出
- 前回 wave の記録: `output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md` (merge 準備・45 node 赤)、`output/insights/2026-09-18/t2724-t080-defer-active-v2/README.md` (A-3 と fixture 切離しの着地)、`output/insights/2026-09-18/t2724-freeze-g1-gen/README.md` (G の作成。保存枝にあり main には未着地)

## 0. 結論

| 項 | 状態 |
|---|---|
| chain X1' `cc82edc8c` / X2 `4d8fb93b7` と G `32ba8cae4` の merge | 完了して保存枝 `t2724-chain-land-2-saved` に固定 (§2)。凍結成果物 8 file の blob OID は保存枝と全件一致、gitlink 不変、実装面差分ゼロ、競合なし |
| 三軸走査 (merge 後の木) | rc=1、rr80 / rr20 とも hit 4 (run dir の journal / manifest / result.json + 候補)、他の hit なし (§3)。D2120 (a)(d) の設計どおり |
| 焦点走 8 file (chain + G + X2 を含む木) | **1211 passed / 12 skipped / 0 failed** (369.23 秒、request 10715.nqsv、§4)。前回の非 hold 45 node の赤は再現しない |
| 受入全走 attempt 1 | **赤: 1 failed / 25311 passed / 69 skipped** (§5)。赤は `test_backoff_extended_sweep.py::test_b10_freeze_tree_bytes_match_the_wave_local_gate` 1 node だけ = B-10 job script が事前登録した freeze tree (`output/s1-freeze` + `output/s8b-freeze`) の bytes digest の固定 pin。G の 1 file 追加で digest が変わった (親と相談子 B が独立に検算) |
| 裁定 (§6) | **chain は land しない (択 3)。** pin の更新 (2 file・3 literal) は将来の B-10 起動契約の変更で、本 wave の scope (期待値の変更は scope 外) と依頼 (赤なら land せず記録して終端) の外。次 wave の設計 (Codex author・変異 2 件・記録の形) を §7 に固定 |
| 本 wave が land するもの | 本 insight と spool fragment 2 片 (worklog・failures) だけ (docs-only、entry 1640 と同型)。chain / G / G wave の fragment 3 片は保存枝に残す |
| A / X (人間手番)・W-5 | 本 wave の scope 外。手順は保存枝の `t2724-freeze-g1-gen/README.md` §5 |

本 wave が変えたもの (main に載るもの): docs (本 insight と fragment 2 片) のみ。走査除外・growth hold・test 期待値・実装面は 0 byte。

## 1. 本 wave が判定しないこと

- B-10 の freeze-tree pin を更新するか (§7 の次 wave の裁定。本 wave は「本 wave では更新しない」だけを決めた)。
- A / X の発効、W-4 spec 承認 (T-750 P-1)、W-5 実走。
- (e) T-1851 worktree の残件、保存枝 (`freeze-g1-chain-t2724` / `-merge-prepared` / `freeze-g1-gen-t2724` / `scratch-t2724-chain-check` / 本 wave の `t2724-chain-land-2-saved`) と G 用 worktree 群の削除 (ユーザー指示時のみ)。

## 2. 実施したこと (merge、保存枝上)

### 2.1 topology の実測 (着手時)

- chain: P `3b0b75496` (main 包含) → X1' `cc82edc8c` (official 床値 run dir 5 file + budget input 1 file) → X2 `4d8fb93b7` (候補 1 file)。
- G `32ba8cae4`: 親 X1' ちょうど 1、`output/s8b-freeze/holdout_freeze.v2.g1.json` 1 file (候補と同 blob `15861416f`)。
- G wave 保存 commit `229982652` = 旧 main `d2ebef7a4` + merge G `88d020466` + 記録 2 commit (insight `t2724-freeze-g1-gen/` 12 file + spool fragment 3 片)。FOLDED.md に同 wave の receipt なし = 未 fold。
- `merge-prepared` (b227d0d91) は再利用不要、`scratch` (8298f7430) は X1' + G + 旧実装 tip の系譜で「land しない」。両者は merge 元にしない。
- main に既にあるもの: A-3 (`t080_freeze_migration._holdout_layer2_delegation` / `_verify_holdout_live_scan`)、fixture 切離し、budget approval `output/s8b-freeze-budget-approvals/g1.json`。

### 2.2 merge (21:2x〜21:31 JST、login)

| 順 | commit | 親 | staged | 照合 |
|---|---|---|---|---|
| 1 | `3440c6620` | `2ba400087` + `229982652` | 21 file 全追加 (X1' 6 + G 1 + insight 12 + fragment 3)。競合なし | 凍結 7 file の blob OID を G 木 `32ba8cae4` と全件一致。gitlink `external/ccbench` = `511c9538` |
| 2 | `87dcbe5a4` | `3440c6620` + `4d8fb93b7` | 1 file 追加 (候補 `15861416f`)。競合なし | X2 木と一致、gitlink 不変 |

- message は job dir `merge-1-message.txt` / `merge-2-message.txt` (`check_ai_provenance.py --message-file` rc=0、`commit -F`)、trailer `role=integrator`。`--range 2ba400087..87dcbe5a4` = 8 件違反なし。記録 commit `b217b24a7` 後の全史監査 = 11,625 件・新規違反なし (login bounded local)。
- G wave の未 fold fragment 3 片は `spool_fold.py --dry-run` が `[T-2724]` の base-mismatch で赤になったため、spool 規約に従い削除せず内容を改めた (worklog 片: 本文末尾に現況 1 項、次の一手差分を空に = 旧 base の `更新` と entry 1683 で完了済みの作業を指す `新規 T` を外す。decisions 片: 末尾に現況 3 行。failures 片: 無変更)。改訂後 dry-run rc=0。**この改訂は保存枝 `b217b24a7` に入っている。**次 wave が保存枝を merge すれば fold 対象になる。

## 3. 三軸走査 (21:32 JST、login、`evidence/scan-projection.json`)

| 木 | rr80 hit | rr20 hit | positive control | file 数 | rc |
|---|---|---|---|---|---|
| merge 後 `87dcbe5a4` | 4 | 4 | 218 | 28,547 | 1 |

hit 4 path (両 holdout 同一): run dir `20260916T111925Z-2c8cf9be/` の `journal.jsonl` / `manifest.json` / `result.json` と `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`。G の世代文書は除外 prefix 内で hit しない。記録 docs を含む木 (`b217b24a7`) でも hit 集合は同じ 4 path。

## 4. 焦点走 (計算ノード、request 10715.nqsv、`evidence/focus-1-summary.txt`)

対象 = 前回 wave の chain 有り焦点 7 file + `test_real_repo_serialization.py` の 8 file。木 = `87dcbe5a4` (X1' + X2 + G)。投入 21:34:55、終了 21:41:33 JST。**1211 passed / 12 skipped / 0 failed、369.23 秒。** growth hold 4 node は hold のまま skip。

意味: 前回 wave が実測した非 hold 45 node の赤 (X1' 木で 45 failed / 967 passed) は、A-3 + fixture 切離し (entry 1683) 後の main に X2 候補まで含めた木 (hit 4 / 4) でも再現しない。brief の (P1) は成立。**ただしこの焦点集合は B-10 の pin (§5) を含まず、受入全走で初めて赤が出た。**

## 5. 受入全走 attempt 1 — 赤 1 node (21:48:53〜22:19:12 JST、`evidence/acceptance-1-failure-excerpt.txt`)

- 投入: `dev_wave_wait.py acceptance --wave worktree-dev-wave-t2724-chain-land-2 … -- python3 tools/run_tests.py` (他 wave の acceptance leader 0 本、load 23.8 / 96)。claimed main `a99425b66` (T-2484 の land 後)、受入が作った merge = `0a799da6c` (親 `b217b24a7` + `a99425b66`)。
- 結果: rc=70、**1 failed / 25311 passed / 69 skipped**。受領証は未発行 (赤の受領証は取らない、DW-O18)。
- 赤: `orchestrator/tests/test_backoff_extended_sweep.py::test_b10_freeze_tree_bytes_match_the_wave_local_gate` (assert は 2024〜2026 行、値は 2025 行)。`output/s1-freeze` + `output/s8b-freeze` 配下の全 file (path + NUL + bytes) の sha256 が固定値 `c405c742…` と不一致 (実測 `6a4ee1ef…`)。
- 原因 (親と相談子 B が独立に検算): 全 20 file の digest = `6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415`、G の 1 file `output/s8b-freeze/holdout_freeze.v2.g1.json` を除いた 19 file = `c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3` (旧 pin と一致)。**G の追加だけが原因。** X1' / X2 は `output/env/…` と `output/s8b-freeze-candidates/` に入り、この pin には触れない。
- pin の出所: 導入 commit `ad3ef12a8` (2026-08-26、B-10 格子拡張、Claude manager + Codex author)。以後 pin 値の更新 0 回、`output/s8b-freeze/` の最終変更は 2026-08-17 で、pin 導入後に freeze tree が変わるのは本 wave が初。同 test 1671 行は job script `tools/pegasus/b10_backoff_grid.sh` に `EXPECTED_FREEZE_TREES_SHA256=c405c742…` (22 行) が含まれることも assert。job script は 580〜597 行で同じ算法の digest を起動前に固定値と照合し (`fail 2 "freeze trees do not match the B-10 preregistered bytes"`)、647〜649 行で job 前後の一致を検査し、719 行で `completion.json` に `freeze_trees_sha256` を記録する。
- 旧値の記録: B-10 成果物 (`output/insights/2026-09-10/t2266-formal-1000us/…/completion-*.json` 等の `freeze_trees_sha256`、3 job で一致)、`docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` 120 行。**これらは測定時点の記録であり、pin の更新で変わらない (規律 7)。**
- 判定 (DW-O18): 自分起因・決定的。gate の拒否は正しい (G の追加は事実)。非帰属ではないので再投入しない。hold / skip / 条件付き assert は規律 2 / D532 / DW-O18 に反するので採らない。
- 段 1 の取り逃し: pin 閉包 (brief「pin 閉包」節) は成果物の file 名で `git grep` しただけで、**directory 名 `"output/s8b-freeze"` を丸ごと digest する pin** を引かなかった (F30 型の再発。key 側検索 `rglob` / `freeze_digest` / `EXPECTED_*SHA256` で引けた)。焦点走の 8 file にも `test_backoff_extended_sweep.py` は入っていない。failures 台帳へ再発として記録。

## 6. 裁定 — chain は land しない (択 3)、pin 更新は次 wave (親の裁定、相談 2 本の後)

ユーザー委任「needs input を出さず codex と相談して決める」に従い read-only codex 2 レンズ (`gpt-6-astra` / medium、生成物は job dir `artifacts/dev-wave-t2724-chain-land-2/s3-a.md` / `s3-b.md`) に攻撃させた。

- レンズ A (束縛の意味・権限): **択 3 を推す。** pin が守るのは第一に「将来の B-10 job が要求する凍結 tree の同一性」(job script 595 / 647 行) で、過去の成果物との対応は `completion.json` の記録で保たれ定数に依存しない (CA-3: 「launch pin の更新 = 発効済み事前登録の書き換え」は refuted、D1789 / D1790 の直接対象は事前登録文書と解析器の sha)。しかし旧 tree を拒否し新 tree を受理する変更は**将来の起動契約の変更**であり、D2120 項 2 (b) は G の導入を授権するが周辺 gate の repin までは授権しない (CA-1)。本 wave の brief は「test 期待値の変更」を scope 外と明記し、依頼は赤での終端を指定している (CA-2)。絶対規律 2 の必然的違反とは判定しない。択 1 を別途採るなら、旧値・新値・G の exact blob・追加以外の変更が無い証拠、負例 (別 file の追加・既存 bytes の変更を拒否)、author と独立したレビュー、decisions への契約変更と授権根拠の記録が must。
- レンズ B (実効性・閉包): **択 1 を推す。** 独立検算で G だけが原因 (CB-1)。必須修正は 2 file・3 literal (`test_backoff_extended_sweep.py` 1671 行と 2025 行、`b10_backoff_grid.sh` 22 行を `6a4ee1ef…` へ)。`submit_b10_backoff_grid.sh` の `job_script_sha256` は投入時に動的計算するので追加更新不要、`admission_registry.json` / `test_hooks.py` も literal pin を持たない (CB-5)。更新後も test は別 file の追加・削除・1 byte 変更・G の削除を拒否する (算法から)。複数値受理・prefix 除外は refuted。変異 matrix は登録すべき (test literal だけ旧値へ → tree digest node が赤、job 定数だけ旧値へ → 文字列検査 node が赤) (CB-4)。受入外 consumer: `docs/b10-backoff-static-tail-submission.md` 31 行の投入手順 (test だけ直すと実投入が旧 pin で止まる = 択 2 の反証)、`docs/phase3-8b-restart-runbook.md` 145〜149 / 262 行 (gate-check と clean-scan の運用)、`docs/paper-story/results/…` 120 行と `figures/fig2c_b10_extended_backoff.provenance.json` 170 行の旧値 (過去の記録、更新しない)。段 1 の pin 閉包は不完全 (CB-2)。
- **親の裁定:** 両レンズは事実 (G だけが原因、修正は 3 literal、過去の記録は不変) で一致し、権限の解釈で割れた。本 wave の依頼は「本題の取り込みだけ」「受入が赤なら land せず原因を記録して終端」であり、pin 更新は D2120 (b) の射程外の起動契約の変更で、その授権と記録 (新 D) を赤の直後に同じ主体が同じ wave で作るのは「赤を見た同じ AI が期待値を変えて緑を作る」形に近い。よって**本 wave では pin を更新せず chain を land しない (択 3)。** ただしユーザーへ問いを返すのではなく、次 wave の設計を §7 に固定し、実施はその wave の段 1 (別 context、独立レビュー付き) で行う。択 2 (test だけ) と 択 4 (hold / 除外) は両レンズが refuted。

## 7. 次 wave の設計 (親の推奨、レンズ B の CB-3 / CB-4 と レンズ A の must を統合)

1. **対象:** `[T-2724]` の続き 1 wave。着手直前の main から fresh worktree → 保存枝 `t2724-chain-land-2-saved` (`0a799da6c`) を固定 SHA で merge (merge-base 1 つ、X1' + X2 + G + G wave fragment 3 片 (改訂済み) + 本 wave の旧記録 commit を含む) → Codex author が pin を更新 → 変異 2 件 → 受入 → land。
2. **Codex author の変更 (実装面、D95):** `orchestrator/tests/test_backoff_extended_sweep.py` 1671 行と 2025 行の literal、`tools/pegasus/b10_backoff_grid.sh` 22 行の `EXPECTED_FREEZE_TREES_SHA256` を `6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415` へ。算法・比較・除外集合は変えない。着手時に digest を再計算し (main の他の変更で `output/s1-freeze` / `output/s8b-freeze` が動いていれば値が変わる)、新値は再計算値を使う。
3. **変異 matrix (DW-M01):** (m1) test 2025 行だけ旧値へ → `test_b10_freeze_tree_bytes_match_the_wave_local_gate` が赤、(m2) job script 22 行だけ旧値へ → 1671 行の文字列検査 node が赤。本 wave の受入赤は m1 型の事前証拠だが、更新後の kill とは数えない。
4. **負例 (レンズ A must):** 更新後の test が「別 file の追加」「既存 file の 1 byte 変更」「G の削除」を拒否することを、隔離 worktree で `DW-O19` (即時復元) により 1 回ずつ実測。
5. **記録:** decisions fragment 1 件 (「B-10 の freeze-tree 起動契約を、D2120 項 2 (b) で導入した G を含む tree へ更新する。旧測定の解釈は不変 (規律 7)、変わるのは将来の launch 条件。新 pin は B-10 新 phase の事前登録成立や本走許可ではない」+ 授権根拠 + 却下案 = 複数値受理 / prefix 除外 / hold)。insight の erratum 節 (旧値・新値・G の blob `15861416f` / sha256 `7e1114…`・追加以外の差分ゼロの証拠)。`docs/b10-backoff-static-tail-submission.md` と `docs/phase3-8b-restart-runbook.md` に「chain 導入後の木では clean-scan が hit 4 / 4 で拒否する (設計どおり)」の注意 1 行。`docs/paper-story/results/…` と provenance.json の旧値は書き換えない。
6. **段 6 の独立レビュー 1 本** (レンズ A must: author と独立)。
7. **その後:** A / X (人間手番) → runbook §2 P3 gate-check の実測 → W-4 spec → W-5。

## 8. 実走一覧 (親)

| 時刻 (JST) | 操作 | 結果 |
|---|---|---|
| 21:21 | fresh worktree、submodule init、`check_wave_startup.py --mode fresh --external-handoff` | rc=0 |
| 21:2x | merge 1 `3440c6620` (blob 7 件一致)、merge 2 `87dcbe5a4` (blob 1 件一致) | 競合なし |
| 21:31 | provenance `--range 2ba400087..87dcbe5a4` | 8 件違反なし rc=0 |
| 21:32 | 三軸走査 (merge 後) | rc=1、hit 4 / 4 |
| 21:34 | login `run_tests.py --collect-only -q` | 25,348 collected / 51.75 s |
| 21:34:55〜21:41:33 | 焦点走 1 (8 file、request 10715.nqsv) | 1211 passed / 12 skipped / 0 failed、369.23 s |
| 21:3x | `spool_fold.py --dry-run` (G fragment 改訂前 → 後) | rc=1 base-mismatch → rc=0 |
| 21:46 | 記録 commit `b217b24a7`、全史 provenance | 11,625 件・新規違反なし |
| 21:48:53〜22:19:12 | 受入全走 attempt 1 (claimed main `a99425b66`、merge `0a799da6c`) | rc=70、1 failed / 25311 passed / 69 skipped |
| 22:2x | 親の独立検算 (`freeze-digest-check.py`) | 20 file `6a4ee1ef…`、G 除外 19 file `c405c742…` |
| 22:28〜22:4x | 相談子 A / B (read-only) | A = 択 3、B = 択 1 (§6) |
| 22:4x | 保存枝 `t2724-chain-land-2-saved` = `0a799da6c`、wave branch を main `657e1e5a7` へ戻す | docs-only の記録 commit を積んで受入 → land |
| 22:41:17〜22:41:44 | 受入 attempt 2 (docs-only tip `a71f31e99`) | rc=70 `preclaim-history-provenance` / source_rc=16 orphan-hold: 親が同じ worktree で背景実行中だった全史 provenance 監査の dispatch (request 10854.nqsv) の pending hold に当たった。木の内容とは無関係 (同一 worktree の dispatch 直列規則 DW-C00 を親が破った)。監査終了で hold は自動削除、attempt 3 を直列で投入 |

工数: codex 子 2 本 (相談 A / B)。変異 matrix は免除 (本 wave が main に載せる実装面差分ゼロ)。受入 attempt 2 と land の結果は受領証と land 応答 (job dir) を正本とする。
