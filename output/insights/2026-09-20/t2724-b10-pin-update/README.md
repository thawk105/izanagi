# [T-2724] B-10 の freeze-tree pin を世代導入 G を含む tree の値へ更新し、保存枝 chain/X2/G を main へ取り込む wave (3 回目) — 3 literal の更新、焦点走 0 failed、変異 3 件 KILLED、負例 3 件 (別 file 追加 / 1 byte 変更 / G 削除) を拒否

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-20
- wave: dev-wave-t2724-b10-pin-update (branch `worktree-dev-wave-t2724-b10-pin-update`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-b10-pin-update`)
- 起点の裁定: D2120 項 2 (a)(b)(d) (ユーザー裁定 2026-09-17)、D2154 (A-3、entry 1683)、entry 1688 の親裁定 (前 wave は pin を更新せず、更新は別 context・独立レビュー付きの次 wave へ)、本依頼 (Codex author が literal を再計算値へ更新、変異 2 件、負例 3 件、decisions fragment、docs 注意 1 行 × 2、旧値は不変、A / X は含めない、scope 外の gate・検査・台帳・一般化を足さない、規律 2 を緩めない)。設計正本 = `output/insights/2026-09-19/t2724-chain-land-2/README.md` §7
- 基準: 着手直前の local main `b7f970dfa507558f7fb669a5ab38958d6c76b57c`。取り込み元 = 保存枝 `t2724-chain-land-2-saved` tip `0a799da6c53a9d769cdefa0358e1baecebaeeb8f` (= main `2ba400087` + merge `3440c6620` (G wave 保存 commit `229982652`) + merge `87dcbe5a4` (X2 `4d8fb93b7`) + 記録 `b217b24a7` + 受入 attempt 1 の merge)
- 本 wave の commit (first-parent、着手時刻順)。**初回の列** (branch `t2724-b10-pin-update-attempt1-saved` = tip `d6cf4b632` に退避、§10): merge `9fa49b0a1` (07:14 JST、保存枝 `0a799da6c`) → docs `b3a431e19` (07:28) → **実装 `0d346d281`** (07:31、Codex author) → docs `16f487936` (07:34、decisions fragment) → docs `ac8bd027f` (07:48、レビュー所見の反映) → 記録 `35876c9a8` (08:08) → 前方 merge `c8f22defa` (08:09、main `efb0dee78`) = 受入 attempt 1 の tested tip → land 時の前方 merge `d6cf4b632` (08:36、main `2361220d4`) = land attempt 1 の landing tip (rc=26 で拒否)。**組み直し後の列** (land する branch `worktree-dev-wave-t2724-b10-pin-update`): main `2361220d4` → merge `629690fdd` (08:46、親 = main + G wave tip `229982652` + X2 `4d8fb93b7`) → **実装 `f7f8918ba`** (同一 blob) → docs `e0d389dea` (同一 blob) → 記録 commit (本 insight と worklog fragment)
- 決定: decisions fragment `docs/spool/decisions/2026-09-20-dev-wave-t2724-b10-pin-update-2.md` (placeholder `{{D:b10-freeze-tree-pin-follows-generation-g}}`、fold で採番)
- 一次証拠: 同 dir `evidence/` (焦点走・負例の要約)、`mutation/` (spec と台帳)、`verbatim/` (Codex author 報告、レビュー A / B、焦点再レビューの逐語)。生 log は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-b10-pin-update/` (寿命保証なし)
- 可逆正規化 (D88 / DW-S07、可視文字不変): `evidence/*.txt` は生 log から dispatch の状態行と `IZANAGI_DISPATCH_JOB_TRACE` 行を除き、行末空白を除いたもの (`make-evidence.py`、job dir)。原文 → 抽出 → 正規化の sha256 / byte: `focus-1-summary.txt` = `6dc14ccb…` (5,490) → `29ad7fc4…` (2,411) → `fb451bc1…` (2,409)、`negative-n1-summary.txt` = `2981d270…` (8,328) → `455027ea…` (5,227) → `aaafdb4f…` (5,203)、`negative-n3-summary.txt` = `3c9fbac2…` (8,322) → `4a6ec7b0…` (5,220) → `652f1dc9…` (5,196)。復元は生 log の再抽出。`verbatim/` の Codex 出力は行末空白だけを除いた (`normalize-verbatim.py`、job dir): `s5-author.md` 原文 `9a913c66…` (8,175 byte) → `9fc7b539…` (8,173)、`s6-review-A.md` 原文 `1a760ce6…` (5,589) → `6ceec855…` (5,583)、`s6-review-B.md` / `s6-focus.md` は原文のまま (`07303e42…` 6,070 / `326d8688…` 3,997)。原文は job dir `codex/`

## 0. 結論

| 項 | 状態 |
|---|---|
| 保存枝 chain/X2/G の merge | 完了 (`9fa49b0a1`、no-ff、23 file 追加、競合 1 = 本 insight の前身 `t2724-chain-land-2/README.md` を main 側 (受入赤の後の records-only 版) で解決、gitlink `511c9538e` 不変、実装面差分ゼロ)。凍結成果物の blob は保存枝と全件一致 (レビュー B が `ls-tree` で独立確認: freeze tree 20 file、指定成果物 8 file、`output/` 差分 524 file は全件 main 側の前進分と同一 blob) (§2) |
| pin の新値 | **`6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415`** (20 file)。旧値 `c405c742…` は G を除いた 19 file の値。親の script、job script 埋め込み算法、Codex author の 3 経路で一致 (§2) |
| 実装 (Codex author) | `orchestrator/tests/test_backoff_extended_sweep.py` 1671 / 2025 行と `tools/pegasus/b10_backoff_grid.sh` 22 行の 3 literal だけ (commit `0d346d281`、2 file / 3 行)。算法・比較・対象 dir・`fail 2`・記録は不変 (§3) |
| 焦点走 (consumer 5 file) | **780 passed / 1 skipped / 0 failed** (request 11854.nqsv、§4) |
| 段 6 レビュー 2 本 + 焦点再レビュー | 実装 3 literal は両レンズとも問題なし。must-fix は docs の主張範囲 2 件 (旧 checkout の拒否保証の過大記述、n2 の期待 node の射程) と should 1 件 (未実走の完了形) → docs fix `ac8bd027f` → 焦点再レビュー **GO** (§5) |
| 変異 (harness、B-10 test 3 file) | probe で観測 node を集め、final で **m1 / m2 / n2 の 3 件とも KILLED、期待 node 完全一致** (§6) |
| 負例 n1 / n3 (独立 clone + dispatch) | 別 file 追加 → digest `74a3f035…` ≠ 新値で赤 1 node、G 削除 → digest = 旧値 `c405c742…` ≠ 新値で赤 1 node。いずれも `test_b10_freeze_tree_bytes_match_the_wave_local_gate` だけが赤 (§7) |
| 受入全走 attempt 1 (初回の列、tip `c8f22defa`) | **child-green、25412 passed / 69 skipped / 0 red** (claimed main `efb0dee78`、08:23〜08:35 JST、§9) |
| land attempt 1 (landing tip `d6cf4b632`) | **rc=26 fold-failed `landed-fold-owned-path`** — 保存枝内の merge `87dcbe5a4` (親 2 つとも main の祖先でない) を両親との diff で検査すると X2 側との diff に main の fold (`FOLDED.md` の M) が現れる。main は 1 bit も変わらず。設計正本 §7 項 1 の代替 (元の保存枝を main へ再 merge) に従い、main の祖先を 1 つ持つ merge 1 つに組み直した (§10) |
| 受入全走 attempt 2・land (組み直し後の列) | 記録 commit の後 (§11、結果は受入受領証と land 応答が正本) |
| A / X (人間手番)・W-4 / W-5 | scope 外。手順は `output/insights/2026-09-18/t2724-freeze-g1-gen/README.md` §5 |

本 wave が変えたもの (main に載るもの): chain/X2/G の 23 file (保存枝の内容そのまま)、実装 2 file / 3 行、docs (submission doc §1 項 6、runbook W-3 の 1 項、旧 fragment 2 片の現況改訂、decisions fragment 1 片、worklog fragment 1 片、本 insight)。走査除外・growth hold・test の skip / 削除・旧測定の記録は 0 byte。

## 1. 本 wave が判定しないこと

- A / X の発効、W-4 spec 承認 (T-750 P-1)、W-5 実走。
- B-10 の次の cohort・帯・phase (事前登録 `cad6f46d8` の bytes は不変、新 phase は別途の登録 commit と裁定)。
- 保存枝 5 本と旧 worktree 群の削除 (ユーザー指示時のみ)。
- 旧 checkout (旧 job script + 旧 tree) からの B-10 投入の可否 — 本更新は旧版を失効させる機構を足していない (レビュー A-2 / B-1)。

## 2. merge と digest 再計算 (07:12〜07:15 JST、login) — 初回の列。組み直し後の merge は §10

- 起動 gate `check_wave_startup.py --mode fresh --external-handoff` rc=0 (worktree は main `b7f970dfa` から手動 `git worktree add`、submodule 3 段初期化、lock)。
- `git merge --no-ff --no-commit 0a799da6c` → 競合 1 file (`output/insights/2026-09-19/t2724-chain-land-2/README.md`、add/add)。main 側 = 受入赤の後に書き直した records-only 版 (entry 1688 で land 済み) を採り、保存枝側 (受入赤の前の稿) は捨てた。`git diff --cached HEAD -- <insight dir>` は 0 行。staged 23 file (X1' 6 + X2 1 + G 1 + G wave insight 12 + spool fragment 4 の内訳は commit message)、gitlink 不変。
- digest 再計算 (merge 後の木、`freeze-digest-check.py` = 前 wave と同じ script): 全 20 file **`6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415`**、G を除く 19 file `c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3` (= 旧 pin)。job script 582〜592 行の埋め込み python をそのまま実行しても `6a4ee1ef…`。G = `output/s8b-freeze/holdout_freeze.v2.g1.json`、blob `15861416f37f08ba72fac0c69b65c1505296ec88`、sha256 `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06`、20,737 byte。前 wave (2026-09-19) の値と同一 = main は `2ba400087` 以降 `output/s1-freeze` / `output/s8b-freeze` に触っていない。
- 段 1 前の閉包 (DW-O09): 旧値の tracked 出現は test 1671 / 2025 行、job script 22 行 (起動契約 3 箇所) と、記録側 (results 稿 cohort 1 `2026-09-16-b10-static-tail-not-observed.md` 120 行 / cohort 2 `2026-09-19-b10-static-tail-cohort2.md` 129 行、insight 6 dir、`completion.json` 6 件、archive entry 1688)。job script 自身の sha256 (`8422011d…`) を pin する test・登録簿は無し (cohort 2 稿の記録のみ)。`docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json` は旧 job script の `job_script_sha256` (`9579690d…`) を持つ測定時点の記録で、freeze digest の literal は持たない (author が確認)。B-10 cohort 2 (D2157) は完走済み (pbs 10752〜10754、`freeze_trees_sha256` = 旧値) で、走行中・待機中の B-10 job は無い。
- 他 worktree の作業ツリー走査 (`overlap-scan.py`、36 root): 対象 4 file を main と異なる bytes で持つ木は全て古い base の checkout (旧 job script `c0635ef3…` 等) で、並行編集は無し。

## 3. 実装 (段 5、Codex author、07:24〜07:29 JST)

- unit worktree `.codex/worktrees/t2724-pin-unit` (branch `dev-wave-t2724-pin-unit`、base `9fa49b0a1`、manifest `child-manifest.json`、所有 path = 対象 2 file)。midflight gate rc=0、dry-run rc=0。`gpt-6-astra` / medium、281 秒、13 model calls、`check_codex_output` OK。
- 差分 (逐語は `verbatim/s5-author.md`): test 1671 行の期待文字列と 2025 行の literal、job script 22 行の `EXPECTED_FREEZE_TREES_SHA256` を `c405c742…` → `6a4ee1ef…`。`git diff --stat` = 2 file / 3 insertions / 3 deletions。他の行・他の file は不変。
- author の検算: 算法の直接実行で 20 file `6a4ee1ef…` / 19 file `c405c742…`、`ast.parse` 成功、`bash -n` rc=0、test 2 関数の直接呼び出し成功 (pytest は sandbox で起動不能)、旧値 grep 0 件 / 新値 grep 3 件。静的列挙は §2 の閉包と一致。`test_b10_backoff_grid_job.py` 420〜425 行の fixture は定数行を含まない snippet に `EXPECTED_FREEZE_TREES_SHA256=fixture-freeze` を前置するので影響なし。
- 親が所有 path 限定 patch を wave worktree へ適用し commit `0d346d281` (trailer: codex author + claude manager)。`check_ai_provenance.py --range b7f970dfa..HEAD` 13 件違反なし。

## 4. 焦点走 (07:32:14〜07:32:51 JST、計算ノード request 11854.nqsv、`evidence/focus-1-summary.txt`)

- 対象 = 変更した test file + 変更した job script を参照する consumer test (DW-O26): `test_backoff_extended_sweep.py` / `test_b10_backoff_grid_job.py` / `test_b10_backoff_grid_submit.py` / `test_hooks.py` / `test_pegasus_tools.py`。tip `0d346d281`。
- **780 passed / 1 skipped / 0 failed (7.89 秒)**。

## 5. 段 6 敵対レビュー 2 本 + 焦点再レビュー (07:36〜07:51 JST、read-only、`gpt-6-astra` / medium、逐語は `verbatim/`)

- レンズ A (過剰・削除・受理集合、156 秒 / 8 calls): 実装は 3 literal の置換だけ、算法・assert・分岐・fallback・skip・xfail・hold の変更なし、受理集合は設計どおり (新値だけと完全一致、prefix 除外なし)、merge 23 file は保存枝の blob と全件一致、scope 外の追加なし、m1 / m2 の期待 node は静的に整合。**must-fix 1:** n2 (`output/s1-freeze/measurement_freeze.json` の 1 byte) は全 suite では `test_s1_9pair_figure_provenance.py` 697 / 852 行の s1 凍結 pin も拒否する → 期待集合の射程を走行範囲で明示せよ。**must-fix 2:** 「G を持たない古い checkout からの投入は止まる」は実装より強い (旧 checkout は同じ checkout の旧 job script で投入するので旧 tree と一致する)。should: decisions fragment の「本 wave はその条件で実施した」は未実走の完了形。nit: 旧 fragment の「codex 子 0 本」は受入前時点の記録。
- レンズ B (束縛の意味・consumer 閉包・負例・記述、195 秒 / 11 calls): pin の束縛と旧成果物の対応 (`completion.json` の記録は定数に依存しない) は成立、解析側 (`b10_backoff_shape_sweep.py` / `b10_backoff_static_tail_formal.py`) に旧値照合の経路なし、job script の bytes を固定 sha で pin する経路なし、docs parser (`_documented_argv`) は §2 だけを読むので §1 追記は無害、負例 n1 / n3 の設計は「指定 test file 内では同 1 node だけが赤」で静的に妥当、D1789 / D1790 の対象外、事前登録は freeze digest も job script sha も束縛していない、merge の完全性 (ls-tree 一致) 確認。**must-fix (A-2 と同じ):** 旧 checkout の拒否保証を「本更新を含む job script が G を欠く tree 等を `fail 2` で拒否する。旧 script + 旧 tree の組は失効しない」に限定せよ。should: 未実走の完了形。nit: 「唯一の形」に条件を付ける、submission doc に clean-scan 注意が無い (runbook 側にはある)。
- 親の裁定: must-fix 2 件・should 1 件・nit「唯一の形」を採用 (全て docs の主張範囲、実装面は不変なので親が編集、commit `ac8bd027f`)。n2 の射程は段 4 事前登録 (job dir `s4-ruling.md`) に「走行範囲 = B-10 test 3 file、全 suite では s1 側の凍結 pin が冗長 gate、n2 の証拠は B-10 pin が s1-freeze の bytes も束縛することに限る」を追記。nit「codex 子 0 本」は当時の稿の本文を保つ方針 (現況 1 項で説明済み) のため不採用。nit「submission doc の clean-scan 注意」は B-10 投入手順に clean scan は現れないため不採用 (chain 導入後の B-10 側の帰結は pin であり、それを項 6 に書いた)。
- 焦点再レビュー (89 秒 / 6 calls): A-1 / A-2 / B-1 / A-3 / B-2 / B nit「唯一の形」= **closed**、残る 2 nit = partial (非阻害)、新規所見・regression なし (docs parser・check_docs 予算・spool frontmatter を静的確認)。**GO**。

## 6. 変異 (DW-M01〜M08、独立 clone `mutation-source`、`tools/mutation_worktree.py --runner-mode dispatch --detached`、B-10 test 3 file)

事前登録 (段 4、`s4-ruling.md`): (m1) test 2025 行の literal だけ旧値へ → `test_b10_freeze_tree_bytes_match_the_wave_local_gate` 1 node、(m2) job script 22 行の定数だけ旧値へ → `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs` 1 node、(n2) `output/s1-freeze/measurement_freeze.json` の `"ccbench_pin": "d706650"` → `"d706651"` (同長 1 byte) → m1 と同じ 1 node。走行範囲 = `test_backoff_extended_sweep.py` / `test_b10_backoff_grid_job.py` / `test_b10_backoff_grid_submit.py` (全 suite では n2 は s1 側の凍結 pin も拒否する冗長 gate、§5)。runner argv = `python3 tools/run_tests.py --force-dispatch <3 file> -q -rf`。

| 走 | commit | spec sha256 | baseline | m1 | m2 | n2 |
|---|---|---|---|---|---|---|
| probe (07:40〜07:48 JST、台帳の更新 07:42〜07:45、全件 SURVIVED 期待で観測 node を集める) | `16f487936` | `8f433608…` | PASSED (27.7 s) | MISMATCH (観測 = 事前登録どおりの 1 node) | MISMATCH (同) | MISMATCH (同) |
| final (07:52〜08:04 JST、台帳の更新 07:54〜08:03、KILLED 期待、観測 node を完全集合として登録) | `ac8bd027f` | `7ebc7667…` | PASSED (351.2 s、queue 待ち込み) | **KILLED** (57.8 s) | **KILLED** (39.7 s) | **KILLED** (30.8 s) |

- probe の MISMATCH は SURVIVED 期待に対する観測 node 非空の意味で、kill と読まない (DW-M08)。観測 node は 3 件とも事前登録の期待と一致した。
- final は fix 後の最終 tip `ac8bd027f` (実装差分は `0d346d281` から不変) で走らせ、3 件とも `failed_nodes == expected_nodes` の完全一致で KILLED。台帳は `mutation/ledger-probe.json` / `mutation/ledger-final.json`、spec は `mutation/spec-probe.json` / `mutation/spec-final.json`。
- 単一理由性: m1 は「実 tree の digest ≠ test literal」だけ (job script 文字列検査は新値のまま通る)、m2 は「job script 内に新 pin 文字列が無い」だけ (tree digest は test literal と一致したまま)、n2 は「digest 不一致」だけ。他の node が赤にならなかったことが台帳で確認できる。

## 7. 負例 n1 / n3 (07:45:22〜07:46:03 JST、独立 clone `negative-n1` / `negative-n3` の作業ツリー、tip `16f487936`、B-10 test 3 file を `run_tests.py --force-dispatch` で各 1 回)

| 負例 | 作業ツリーの変異 (`git status --porcelain`) | request | 結果 | 赤 node の assertion |
|---|---|---|---|---|
| n1 別 file 追加 | `?? output/s8b-freeze/negative-example-extra-file.json` (63 byte、untracked) | 11875.nqsv | 1 failed / 224 passed | digest `74a3f0355b778f5e5fa53f3449f477ca45c8804fc0305ba6295dae9afc656c9f` ≠ `6a4ee1ef…` |
| n3 G の削除 | ` D output/s8b-freeze/holdout_freeze.v2.g1.json` | 11874.nqsv | 1 failed / 224 passed | digest = **旧値 `c405c742…`** ≠ `6a4ee1ef…` |

- 赤はいずれも `orchestrator/tests/test_backoff_extended_sweep.py::test_b10_freeze_tree_bytes_match_the_wave_local_gate` だけ (要約は `evidence/negative-n1-summary.txt` / `negative-n3-summary.txt`)。n3 の digest が旧値そのものになることは、旧値と新値の差が G の追加だけであることの実走による確認でもある。
- これは test 側の検出力の証拠であり、job script 本体の `fail 2` を実走した証拠ではない (レビュー B、焦点再レビュー)。job script の 595〜597 行は同じ算法・同じ定数で比較するので算法上は同じ結果になるが、B-10 job を投入して確かめてはいない。
- 独立 clone は job dir に置いた使い捨てで、wave worktree・共有 checkout は変異させていない (DW-O19 の隔離 worktree 相当)。

## 8. docs の変更 (親、docs-only)

- `docs/b10-backoff-static-tail-submission.md` §1 項 6: 投入 checkout の凍結 tree digest がその checkout の job script の定数と一致すること、G を main に載せた版以降の定数は G を含む値、この版の job script は G を欠く tree・追加・変更を `fail 2` で拒否、旧 script + 旧 tree の組は失効しない、旧 cohort の記録値は不変。§2 の code block (parser の対象) は不変。
- `docs/phase3-8b-restart-runbook.md` W-3「chain 導入後の注意」1 項: clean scan は run_dir 3 file + 候補の hit 4 / 4 で赤 (設計どおり、走査除外は広げない)、official 床値 wave は別 branch から起動、B-10 pin は同じ版で G を含む値へ更新済み。
- `docs/spool/worklog/2026-09-19-dev-wave-t2724-chain-land-2-1.md` (2 回目の取り込み wave が受入赤の前に保存枝へ書いた片): title と末尾の現況 1 項を改め、`[T-2724]` の次の一手差分を空にした (本文の実測値は当時の記録のまま。削除は land verifier が拒否する)。`docs/spool/decisions/2026-09-18-dev-wave-t2724-freeze-g1-gen-3.md` (G wave の決定、fold で採番): 現況 1 項を末尾に追記。`spool_fold.py --dry-run` rc=0。
- 三軸走査 (権威 CLI、本 insight を含む木、07:56 JST と記録 file 全部を stage した 08:07 JST の 2 回): rc=1、rr80 / rr20 とも hit 4 = official 床値 run dir の 3 file + 候補 (前 wave と同じ集合、D2120 項 2 (a)(d) の設計どおり)、file 数 29,140 → 29,143、positive control 228。本 wave の追加 file に hit なし。検索式は D88 に従い収録しない。

## 9. 受入・land (初回の列)

- 受入 attempt 1: 門番 open 08:22:46 (他 wave の acceptance leader 1、load 7) → 08:23:05 detach 投入、tip `c8f22defa` (記録 commit `35876c9a8` + 前方 merge)、claimed main `efb0dee78`。**08:35:23 child-green、25412 passed / 69 skipped、red / flake 0** (受領証 `acceptance-1.json`、tested_main `efb0dee78`、tested_tip `c8f22defa`、lease 未取得 = DW-O27 の既定)。login の `run_tests.py --collect-only -q` は 25,481 collected / 53.7 s。
- land attempt 1 (08:36〜08:43 JST、`land-go.sh`): main が受入後に `2361220d4` (mocc results 稿 wave、docs-only) へ進んでいたため固定 SHA で前方 merge `d6cf4b632` (runner / waiter / land tool の変更なしを merge-base 方向で検査、dry-run rc=0) → `dev_wave_land.py --landing-wave-tip-sha d6cf4b632` → **rc=26 `fold-failed: declared fold verifier が拒否: landed-fold-owned-path`**、`main_before == main_after == 2361220d4`。原因の特定は §10。

## 10. 初回 landing の拒否と組み直し (08:44〜08:50 JST)

- 原因 (`tools/dev_waves/git_state.py` の `_landed_commit_diff` / `_landed_fold_output_path` を読み、job dir `find-fold-owned.py` で verifier と同じ規則を再現): landed 区間 `efb0dee78..c8f22defa` の 17 commit のうち、保存枝内の merge **`87dcbe5a4`** (前 wave が X2 `4d8fb93b7` を `3440c6620` へ merge した commit) は親 2 つとも main の祖先でない (trusted parent 0) ため両親との diff が検査され、X2 側 (`4d8fb93b7`、base = 当時の main `3b0b75496`) との diff に main のその後の fold による `docs/spool/FOLDED.md` の M が現れる。他の 16 commit は hit 0 (merge `9fa49b0a1` / `0a799da6c` / `3440c6620` / `88d020466` は main の祖先を 1 つ持つので trusted parent との diff だけ)。すなわち保存枝の履歴形そのものが land verifier と両立しない (前 wave の受入は verifier を通る前に赤で止まっていたので露見しなかった)。
- 処置 (設計正本 §7 項 1 の代替「元の保存枝を当時の main へ再 merge」): 初回の列を branch `t2724-b10-pin-update-attempt1-saved` (`d6cf4b632`) に退避し、wave branch を現 main `2361220d4` で作り直して **G wave tip `229982652` と X2 `4d8fb93b7` を 1 つの merge `629690fdd` (親 3 つ、main の祖先 1 つ) で取り込んだ**。22 file 追加、競合なし、gitlink 不変。凍結成果物 8 file・G・G wave insight 12 file の blob は初回 tip と同一 (staged tree と `d6cf4b632` の凍結 dir 比較で fragment 以外の差分 0)。前 wave の記録 commit `b217b24a7` は含めないので、受入赤の前の稿だった worklog 片 `2026-09-19-dev-wave-t2724-chain-land-2-1.md` は持ち込まない (改訂の必要も消えた)。G wave の fragment 2 片は初回の列の最終版 (前 wave の現況改訂 + 本 wave の現況 1 項) を docs commit `e0d389dea` で再適用。実装 2 file は初回 commit `0d346d281` と同一 blob (`f51b1c823` / `7736c0afc`) を `f7f8918ba` として再 commit (Codex author trailer は同じ author job-id s5-author-1 の成果)。digest 再計算は組み直し後も 20 file `6a4ee1ef…` / 19 file `c405c742…`。`find-fold-owned.py` で組み直し後の区間 `2361220d4..629690fdd` (7 commit) は hit 0。
- 測定の扱い (規律 7): 焦点走・変異・負例は初回の列の tip (`0d346d281` / `16f487936` / `ac8bd027f`) で測った。組み直し後の木は実装 2 file と凍結 tree の blob が同一で、差は履歴の形と docs (前 wave の stale fragment を含まない、main の docs 前進を含む) だけなので、測定値はそのまま成立する。受入全走は組み直し後の tip で取り直す (§11)。
- 教訓: main の祖先でない branch 同士を merge した履歴 (保存枝の「merge 済み状態」) は land できない。保存枝に残すなら元の枝 (それぞれ main の祖先を base に持つ) を残し、取り込みは main から直接 merge する。

## 11. 受入・land (組み直し後の列)

- 記録 commit の後に実施し、結果は worklog fragment の末尾と land 応答が正本。本節は記録 commit 時点では未実施。

## 12. 実走一覧 (親)

| 時刻 (JST) | 操作 | 結果 |
|---|---|---|
| 07:08〜07:12 | worktree add (main `b7f970dfa`)、submodule init、lock、起動 gate fresh | rc=0 |
| 07:1x | merge `9fa49b0a1` (競合 1 を main 側で解決)、digest 再計算 (2 経路) | 20 file `6a4ee1ef…`、19 file `c405c742…` |
| 07:24〜07:29 | Codex author (unit worktree、job-id s5-author-1) | rc=0、281 秒、3 literal |
| 07:28 | docs commit `b3a431e19` (注意 1 項 × 2、旧 fragment 2 片の現況) | check_docs / dry-run / diff --check 緑 |
| 07:31 | 実装 commit `0d346d281`、provenance `--range b7f970dfa..HEAD` | 13 件違反なし |
| 07:32:14〜07:32:51 | 焦点走 5 file (request 11854.nqsv) | 780 passed / 1 skipped / 0 failed |
| 07:34 | decisions fragment commit `16f487936`、dry-run | rc=0 (採番予定 D2165 = 本 wave、D2166 = G wave) |
| 07:36〜07:45 | レビュー A / B (read-only 並列) | must-fix 2 (docs)、should 1、実装は問題なし |
| 07:40〜07:48 | 変異 probe (`16f487936`) | baseline PASSED、観測 node 3 件 = 事前登録どおり |
| 07:45:22〜07:46:03 | 負例 n1 (11875.nqsv) / n3 (11874.nqsv) | 各 1 failed / 224 passed、赤 = 同 1 node |
| 07:48 | docs fix commit `ac8bd027f` | check_docs / dry-run / diff --check 緑 |
| 07:50〜07:51 | 焦点再レビュー (job-id s6-focus-1) | GO、must-fix / should 全 closed |
| 07:52〜08:04 | 変異 final (`ac8bd027f`、request 11891 / 11892 / 11900 / 11904 / 11905.nqsv) | baseline PASSED、3 / 3 KILLED、期待 node 完全一致 |
| 07:56 / 08:07 | 三軸走査 (本 insight を含む木、2 回目は記録 file 全部を stage 後) | rc=1、hit 4 / 4 (既知集合)、追加 hit なし |
| 08:08 | 記録 commit `35876c9a8` (初回の列) | provenance `--range` 16 件違反なし |
| 08:09 | 前方 merge `c8f22defa` (main `efb0dee78`、peer の landed 通知を契機) | dry-run rc=0 |
| 08:11〜08:12 | login `run_tests.py --collect-only -q` | 25,481 collected / 53.7 s |
| 08:22:46 | 門番 open (leaders 1、load 7) | — |
| 08:23:05〜08:35:23 | 受入全走 attempt 1 (tip `c8f22defa`、claimed main `efb0dee78`) | child-green、25412 passed / 69 skipped |
| 08:36:05〜08:43:45 | land attempt 1 (前方 merge `d6cf4b632` → `dev_wave_land.py`) | rc=26 landed-fold-owned-path、main 不変 |
| 08:44〜08:46 | 原因特定 (`find-fold-owned.py`: `87dcbe5a4` の X2 側 diff に FOLDED.md の M)、branch 退避、組み直し merge `629690fdd`、digest 再計算 | 区間 hit 0、20 file `6a4ee1ef…` |
| 08:47〜08:50 | 実装 `f7f8918ba`・docs `e0d389dea` の再 commit、記録 commit | §11 と worklog fragment |
| 記録 commit 後 | 受入全走 attempt 2 (門番 → detach)、land | 受入受領証と land 応答が正本 (worklog fragment に記録) |
