# 同原因の再試行 — SELF-REVIEW の集約と手当て先 (2026-10-01、記録 wave md_3)

## 0. 何の記録か

2026-09-30〜10-01 に、並行 wave が「同じ原因の失敗を、何も変えずに再試行する」ことを繰り返した。
ユーザー指示「理由Aでダメだからとりあえずやり直してまた理由Aでこけて…こういうのやめさせて。そして自己改善もやらせる」を受け、
land 調整役 (manager: parallel land) が各 wave に自己点検 (SELF-REVIEW) を求めて 11 本を集約した (本数は `common.txt` の「SELF-REVIEW 11 本の集約」)。
本書はその集約 (一次資料 `/work/1/SFC/tanab/tmp/self-review-2026-10-01/summary.md`、repo 外) を写し、
型ごとにどの wave 提案 (md_1・md_2) が手当てするかを 1 行ずつ書く。
land 済み wave の failures 下書き 7 本は、本 wave の fragment
`docs/spool/failures/2026-10-01-dev-wave-selfreview-failures-record-1.md` で台帳へ入れた (§3)。

同日の運用規則 (全並行 session へ通達済み、memory `read-the-failure-before-retrying`):
失敗は本文を読み、原因と前回から変えた点を 1 行で書いてから直す。同じ原因で 2 回失敗したら止めて land 調整役へ `FAIL-2`。
待てば通る型も 3 回まで。各 wave は SELF-REVIEW を送る。

## 1. 型の集約 (summary.md の写し)

### 型 1: 撤去 tool の lock 待ち (rc=75) を固定間隔で再試行

- 回数: md_44 10 回 (23:37〜00:20)・md_35 5 回・codex-astra-ultra 2 回・md_37 は約 1 時間取りそびれた。
- 原因: `tools/dev_wave_cleanup.py` は repo 全体 1 本の flock で、順番待ちの列も保持者の表示も無い。調整役も「数分おいて再試行」と指示し続けた。
- 対処: ユーザー裁定 (10-01 00:2x) で撤去は並列でよい。lock を待たず手動方式へ (memory `worktree-removal-on-lustre-is-slow-dont-parallelize`)。

### 型 1b: 撤去 rc=20 を reason を読まず 12 回再試行 (md_37、ユーザーが見た例そのもの)

- 子木 5 本に同じ `--evidence-dir` を渡し、2 本目以降が `phase=evidence reason=receipt identity mismatch` で拒否された。rc=20 を「他 wave の fold 中」と決めつけ、数字だけで再試行する script を組んでいた (rc=75 も重なった)。
- 調整役自身も「rc=20 (active fold state) なら 2〜3 分おいて再試行」と rc の番号で案内し、reason で分類するよう書かなかった。
- 提案: `DW-O28` の `--evidence-dir` は木ごとに別 dir と明記する。撤去 script は rc でなく reason で分類し、待てば通る型 (removal-lock の busy・active fold state) 以外は再試行しない。

### 型 2: 隔離 session の Bash guard が複合 command を拒否 → 形を変えて 8〜10 回

- md_7・md_11・md_15・md_35・md_39。変数展開・loop・`$()`・`git -C`・`cd &&`・heredoc の同居が拒否される。
- 提案 (md_15・md_11): `DW-O03` に「絶対 path 直書き・git 単独・複数手順は Write で `.sh` を作り `bash <path>` 単独」を足す。memory `git-and-guard-discipline` を入口で最初に読む位置へ。

### 型 3: submodule 初期化の update-no-fetch を同じ argv で再実行 (F810 再発)

- md_15・md_16・md_39 (子木 3 本とも)。md_42 も一過性の I/O で 1 回。
- 提案 (md_16): `DW-O08` を「rc=1 なら再実行の前に `git submodule status --recursive` と木を見る。揃っていれば再実行しない」へ。

### 型 4: 子への投げ文の path・制約の書き漏れで子が停止

- md_22 (F819 再発: 改名して複写した依頼文、1 行に 2 file の必読)・md_20 (子の sandbox は `run_tests.py` 不可と書かず 2 本停止)。
- 提案: `DW-O02` に「依頼文が参照する file は元の名前で置く・必読は 1 行 1 file の完全 path」、`DW-S05-C` に「子は run_tests・pytest 不可、試験不能で止まらない」。

### 単発の型

- md_43: arXiv の生死確認を `max_results=0` で打ち、同じ 500 を 5 回、本走が 1.5 時間止まった → 生死確認は本走と同じ URL 形 (memory `index-liveness-probe-uses-production-request-shape`、F1094)。
- md_23: 受入門番 rc=70 の再投入が gen_S の待ち行列と orphan hold を見ない (F333 再発) → `run-acceptance-gated.sh` に計数と hold の確認。
- md_7: 縮小受入 plan の名前衝突が 1 file 1 件ずつしか出ず 2 回 → plan が全参照を列挙する / 記録 wave の insight 名に wave 接頭辞 (F1093)。
- md_11・md_42・md_33: Lustre 上の `worktree add` が EINTR / rc=128 (F26 再発、md_33 は 7 回中 3 回・うち 1 回を同じ argv で再試行) → 直列で作る。子木作成 script の雛形に「残骸なしを確かめ、間を置いて 1 回だけ再試行、2 回目は止めて報告」。
- md_33: 計算ノードの SMOKE が 1 投入 1 欠陥で 5 回 (memory `startup-gate-chain-reveals-one-defect-per-submission` の再発、F139) → 計算ノードへ出す前に起動器の BUILD-CHECK (build だけ) を 1 本流し、compile・configure の欠陥をまとめて出す。
- md_44: 撤去の前に `ExitWorktree(keep)` を忘れて rc=21 (F51 再発) → `DW-S09`・`DW-O28` に 1 行 (今は memory にしか無い)。
- md_42: fix 裁定で test の期待値の一部だけを変更許可し、子が同じ型で 3 回停止 (memory `fix-ruling-enumerate-dependent-expectations` の再発) → 期待値の変更を許すときは対象 test 関数の全 assert を裁定に逐語で並べて可否を付ける。

### main 側の flaky (受入を食う)

- `test_plot_b7_fixed5_regression` (図の文字の重なりで赤、単独再走 42 passed)・`test_b5_contrast_launch` (待ちループで赤、単独再走 65 passed): md_42 の受入、記録は md_42 へ依頼済み。
- `test_dev_wave_cleanup` の占有走査 indeterminate (5 件、単独再走 213 passed、md_22 の受入): 並列撤去と同時刻の可能性。

### pin F で外れた壊し正例 4 本 (md_15)

- `broken-mocc-early-unlock`・`broken-mocc-hot-update-unlock`・`broken-silo-corrupt-write-payload`・`broken-silo-published-version-mismatch` が F `25898d00` に `git apply` で当たらない (C では当たる)。現行 pin の consumer は無い。F の上で MOCC・Silo の正しさを検証し直すときに正例が欠ける (規律 2・3)。

## 2. 型ごとの手当て先 (1 行ずつ)

md_1 = 撤去 tool の並列化 (`tools/dev_wave_cleanup.py` と `DW-O28` 周辺)、md_2 = `docs/dev-wave/` の手順の穴を 1 行ずつ埋める。どちらも本 wave の時点で未着地の並行 wave。

- 型 1 (rc=75 固定間隔) → md_1: repo 全体の flock を撤去 wave ごとの lock にし、残る rc=75 には保持者 (pid・wave) を出す。手順書 `DW-O28` 自身が今も「撤去は repo 全体で 1 本ずつ、rc=75 は数分後再試行」と書いており (本 wave の段 6 前に気づいた)、tool の reason も `retry in a few minutes` と言う。この 2 つの是正も md_1 の所有範囲 (`DW-O28` 周辺) に入る。
- 型 1b (rc=20 共有 evidence-dir・reason を読まない) → md_1: 木ごとの証拠 dir を既定にするか衝突を理由の本文で明示し、`DW-O28` 周辺の手順も md_1 が直す。
- 型 2 (Bash guard の複合 command) → md_2: `DW-O03` に 1 行。
- 型 3 (submodule 初期化の同 argv 再実行) → md_2: `DW-O08` に 1 行。
- 型 4 (投げ文の path・制約の書き漏れ) → md_2: `DW-O02` と `DW-S05-C` に 1 行ずつ。
- 単発 md_44 (撤去前の `ExitWorktree(keep)`) → md_2: `DW-S09` か撤去の入口に 1 行。`DW-O28` 周辺に書くなら md_1 の所有。
- 単発 md_42 (fix 裁定の部分許可) → md_2: 段 6 の fix 裁定に 1 行。
- 単発 md_43 (生死確認の request 形) → md_2: 置き場が dev-wave docs でなければ見送り、その旨を md_2 の insight に記録 (memory と F1094 は既にある)。
- 単発: 撤去が core dump を持つ木で rc=137・祖先 process を占有者と数える・submodule reflog の到達性の誤判定・gitattributes・gitlink の owned_paths → md_1 (md_1 の依頼文に列挙)。
- flaky `test_dev_wave_cleanup` の占有走査 indeterminate → md_1 (並列撤去と受入の同時走行を試験で示す)。
- 単発 md_23 (受入門番 rc=70 の再投入) → md_1・md_2 のどちらも扱わない。F333 の再発として記録済み。
- 単発 md_7 (縮小受入 plan の 1 件ずつの理由) → md_1・md_2 のどちらも扱わない。F1093 に「道具側の改善候補: plan が全参照を列挙」として残る。
- 単発 md_11・md_42・md_33 (`worktree add` の EINTR) → md_1・md_2 のどちらも扱わない。F26 の再発 (本 wave の fragment) に「残骸を確かめて 1 回だけ再試行、2 回目は止めて報告」を書いた。
- 単発 md_33 (BUILD-CHECK) → md_1・md_2 のどちらも扱わない。F139 の再発 (本 wave の fragment) に書いた。
- flaky `test_plot_b7_fixed5_regression`・`test_b5_contrast_launch` → md_1・md_2 のどちらも扱わない。記録は md_42 へ依頼済み。
- pin F で外れた壊し正例 4 本 → md_1・md_2 ではなく既存の [T-2854] の残り (2)。§4。

## 3. land 済み wave の下書き 7 本の取り込み

| 下書き | 取り込み先 | 判断 |
|---|---|---|
| md_35 `dev-wave-cicada-between-run-floor/self-review/…-selfreview-1.md` | F1092 再発 (Bash guard 約 9 回)・F1038 再発 (PYTHONPATH を変えて同じ 9 件) | 下書きは新規 F 1 本だったが、2 つの型はどちらも既存 F と同型なので分けて再発にした |
| md_44 `vhash-ro-continuing-2026-09-30/failures-fragment-draft.md` (branch `worktree-dev-wave-vhash-ro-continuing`、fold `c94b79717`) | 新規 F (rc=75 の固定間隔再試行) に束ねた・F51 再発 (rc=21 の自己占有) | rc=75 は 3 wave の下書きが同じ型なので新規 F 1 本に束ねた |
| codex-astra-ultra `draft-failures-cleanup-retry.md` | 同上の新規 F | 同上。当時の対応 (撤去 script の再試行上限を 3 回、rc=75 は 2 回目で止めて調整役に枠を求める) は並列撤去の裁定より前のものとして F に残した |
| md_37 `dev-wave-vhash-hot-block-v2/self-review-failures-fragment-draft.md` | 新規 F (共有 evidence-dir の rc=20)。rc=75 の行数は上の新規 F | failures 本文に `--evidence-dir` の既出は無い (memory にだけ 2 回分) |
| md_33 `dev-wave-cicada-certified-m/self-review-failures-fragment-draft.md` | F26 再発・F139 再発 | 下書きどおり。F139 の (2) `git archive` は F1046 に既着地と注記した |
| md_15 `dev-wave-ccbench-pin-f/draft-followup/failures-fragment-draft.md` | F10 再発 (pin 前進で依存物が腐る構造) | 当初は新規 F にしたが、段 6 レビューの指摘で F10 (2026-09-20 に held test の期待値で再発済み) と同型と裁定した。「外れたものは item に紐付けるか起票する」を残した |
| md_15 `dev-wave-ccbench-pin-f/draft-followup/worklog-fragment-draft.md` | 新規 T は作らない。§4 | [T-2854] の残り (2) が同じ作業を P1 で既に持つ |

新規 F にせず再発にした根拠 (failures の型タグ・見出し・本文の検索で照合):
Bash guard の複合 command は F1092・F1095・F1096 が既存。`worktree add` の作成側の中断は F26 に複数の再発があり、EINTR は 2026-09-18・09-29・09-30 の再発に明記されている。
実機の前提の欠陥が投入ごとに 1 件ずつ出る型は F139 の 2026-09-22・09-29・09-30 の再発にある。背景 session の cwd が撤去対象の中にある型は F51 (2026-09-15 の再発あり)。
pin 前進で依存物が腐る型は F10 (2026-08-16・09-20 の再発あり)。
撤去の rc=75・`removal-lock`・`receipt identity mismatch`・`--evidence-dir` は failures 本文に 0 件だったので新規にした。
rc=75 の固定間隔再試行は F333 の (b) と根が近いが、F333 は dispatch の孤児 job の占有が主題で再発検知も別なので、別 F にした。

下書きの数値は撤去 log で数え直した。md_44 は rc=75 が 10 行・rc=21 が 1 行 (00:15)、md_35 は rc=75 が 5 行、codex-astra-ultra は rc=75 が 2 行で、下書きと一致した。
md_37 は run1 の log に `removal-lock` 12 行・`receipt identity mismatch` 12 行、後続の `cleanup-all.log` に `removal-lock` 15 行。
下書きの「rc=75 を計 13 回」とは数え方が合わないので、fragment には log の行数を書いた。

summary.md が名指す型のうち、各 wave が自分で着地させ済みのもの (本 wave では書いていない):
F810 の再発 (md_15・md_16・md_39)、F819 の再発 (md_22)、F333 の再発 (md_23)、F1093 (md_7)、F1094 (md_43)、F1046 の再発 (md_33 の `git archive`)。

## 4. 壊し正例 4 本の作り直し — md_15 の下書きから写した完了条件

md_15 は新規 T の下書き (仮名 `rebuild-positive-controls-on-pin-f`、P2) を置いたが、
[T-2854] の残り (2) が同じ作業 (F で `git apply` が外れる壊し patch 4 本の作り直し) を既に持つので、重複する item は作らなかった。
F10 の再発 (本 wave の fragment) の対応はこの残り (2) を指す。下書きの中身は次のとおりで、残り (2) を進める wave が読む。

- 対象と外れる位置: `broken-mocc-early-unlock` (`cc/mocc/transaction.cc:1257`)・`broken-mocc-hot-update-unlock` (同 1257)・`broken-silo-corrupt-write-payload` (`cc/silo/transaction.cc:655`)・`broken-silo-published-version-mismatch` (同 657)。F の writePhase の clang-format 14 整形と TPC-C の trace v3 で文脈が変わったため。
- 現 consumer: MOCC の 2 本は e9e477ca に独立束縛の `s3_mocc_lock_coverage.py`・`s3_mocc_mutation_proof.py` と MOCC 系 test。Silo の 2 本は `condition_meaning_gate.py` の define ↔ patch の静的登録と、[T-2847] の一回限りの変異走。
- 完了条件: 4 本が F (と、[T-2917]・[T-2919]・[T-2945] の束ねた tip を対象にするならその tip) に厳密適用で当たり、未定義で pin と一致 (inert) し、定義したとき判定器が壊れ方を検出・帰属する (壊れ方が発火する経路に置く)。condition gate の exact な `#if` 行数を変えない。変異を外して緑にしない (規律 2)。
- 根拠: `output/insights/2026-09-30/ccbench-pin-f/README.md` §2・§8、`output/insights/2026-09-29/silo-intra-txn-fix/README.md` の表「D: F でも当たらない」。
