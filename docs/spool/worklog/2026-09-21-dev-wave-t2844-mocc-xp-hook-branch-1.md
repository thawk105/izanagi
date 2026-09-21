---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2844-mocc-xp-hook-branch
seq: 1
title: [T-2844] mocc の X/P 計装を e9e477ca の単一の子 commit C (68106660) として ccbench の local branch izanagi-mocc-xp-instrumentation に載せ、D1603 材料 3 点を揃えた — D297 は GCC 11.4 / 12.3 pass・clang 比較未完了、C 上の正例・負例 compute 1 走は all_pass、波及表 45 件 = 追随 15・据置 29・衝突 1 (コード + test + 計測 JSON + insight、branch worktree-dev-wave-t2844-mocc-xp-hook-branch)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request-t2844.md`): 前 wave (1802) の段 2 plan を流用して段 3 から進め、C の commit・bundle・主 checkout の submodule git dir への fetch、C 上の正例・負例 compute 1 走、D297 (GCC 2 版 + clang)、波及表の点検を行う。push・gitlink と承認定数の更新・再承認の提示・探索開始は scope 外。記録 = `output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md`。設計判断は {{D:mocc-xp-candidate-mode}}。
- **C = `68106660686232781bca3be792a750d3e19d7a8a`** (親 e9e477ca 1 本、`cc/mocc/transaction.cc` +64 行、blob `e393efbf…` = 前 wave の目標、tree `6dc0883c…`)。Codex author A が `patches/instr-mocc-lock-coverage-pin-candidate.patch` を作り、親が独立検算 (旧計装との差 3 行) のうえ wave 木 submodule の一時 worktree で `commit -F` した。自己完結 bundle (sha256 `36080555…`) を job dir に保全し、主 checkout の `.git/modules/external/ccbench` へ branch を非 force で fetch した (21:48:29 JST)。gitlink・submodule HEAD は e9e477ca のまま。GitHub への push は人間手番 (D16)。
- **C の初版 `1035f1e3` は trailer の reviewer 行が抜けていた** (段 4 で 3 行と決めた後に親が message の下書きを更新し忘れた)。下流が参照する前に同じ tree・親で message だけ直して置換し、旧 OID の証拠は job dir `superseded-1035f1e3/` に残した。
- D297 (C に対して): GCC 11.4 / 12.3 とも pass (各 16 context で正規化前処理と include 活性が一致、basis 全件 `exact_identity`)。clang 14 は空入力の環境 prefix 不一致で比較前に止まり比較未完了 (前 wave と同じ既知限界、検査器は直していない)。旧計装 patch そのままの負例対照は include 行不一致で拒否された。
- **計算投入のユーザー確認:** 同日 21:1x のユーザー新指示 (rulings-inbox `2026-09-21-vldb-direction-verdicts.md` 項 4、別 session からの連絡を現物で確認) に従い、compute 1 走は見積り (1 node × 約 2〜3 分、walltime 上限 20 分) を示して「投入してよい」を得てから投げた。直後の追補で確認ラインは「1 タスクの job 合計 2 node 時間以上」になった。本 wave の計算ノード使用は compute 132 秒 + 焦点走 136 秒 + 変異本走 + 受入で、ラインを下回る。
- compute 1 走 (15646.nqsv、1 node、Elapse 132 秒): all_pass、14 check 全真。stock 2 走 certified、single の負例 3 本 (lockskip / permutation-erase / early-unlock) は所定の X / P だけで indeterminate、lockskip_high は cycle 3,525 の non-serializable (単一理由の負例ではない)。TRACE=0 は nm / strings 0・正規化逆アセンブル一致 (`.text` bytes 一致は測らず主張しない)。
- 段 3 相談 2 本の must-fix 3 件 (単一理由性、`.text` bytes の説明、C の OID 変更時の証拠更新順) を段 4 で採用し、plan の 21 key・hot 2 走・`.text` bytes 比較は採らず、識別 (親 = e9e477ca 1 本・raw diff 1 行・blob 一致) を build 前の停止条件にした。相談 B の初回は親の prompt の path 誤りで子が fail-closed 停止し、資料を job dir へ写して再投入した。
- 段 6 レビュー 2 本はどちらも GO・must-fix 0。should (負例 verdict を run 別に書く、floor resolver の選択規則、template 系 preimage の区別、本 wave 追加物の扱い、MP3 / MP4 の kill の帰属) は insight に反映した。nit 1 件 (新 test のコメント) は成果物に影響しないので直していない。fix 子は起動していない。
- 焦点走 (15671.nqsv、1 node、Elapse 136 秒): 787 passed / 5 skipped / 0 failed。変異 matrix (段 4 で事前登録した 15 件、独立 clone の固定 commit `6fa89b563`、dispatch): baseline PASSED、15 / 15 KILLED、期待 node と完全一致 15 / 15。候補 patch の変異 4 件は bytes 一致の assert が最初に落ちたもので、X/P 構造 helper 単独の kill とは数えない (insight §8)。受入全走の結果は land の受領証。
- **受入 attempt 1 (tested main `caf0f8a1a`、tip `c56bdcbd3`、22:32〜22:37) は赤 2 件で rc=70、非帰属と判定して受入を取り直した (DW-O18 の差分到達不能)。**
  赤は shard-1 の `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` (「diagnostic timeout did not interrupt the syscall」、子の結果 pipe への `os.write` が差し替えた 5 秒の hang に当たった時間依存の型で、同日の別 wave の受入と entry 1482 / 1546 に同型の前例) と、
  同じ shard の pytest 内部エラー (xdist loadscope scheduler が消えた worker gw38 で `KeyError`、junit `pytest::internal`)。shard-0 / shard-2 は signal 15 で中断され、request 15834 / 15836 は中断不能の状態で走行を続け、orphan hold 2 file が残った。
  本 wave の差分 (mocc driver の候補 mode・候補 test・候補 patch・候補 JSON・docs) は floor checkpoint の試験と xdist の scheduler から到達しない。取り込んだ main の 5 commit も rulings の記録だけで両者に触れない。
  処置: qdel せず 2 job の終端 (22:47:24) を待ち、hold 3 file を job dir `orphan-holds-acc1/` へ退避・削除し、同じ tip で赤の test を単独再走した (15844.nqsv、Elapse 10 秒): 3 passed で再現しない。hold 登録簿へは登録しない。本項を含む tip で門番から 1 回再投入する。
- **受入 attempt 2 (門番が 23:22 に開いた時点の main `23f21dd9d` を取り込み、待ち手の post-claim merge で main `73b8780b7` まで取り込んだ tip `a44534bbe`、23:22〜23:30) も赤 2 件で rc=70、非帰属と判定した (F633 の再発)。**
  赤は shard-0 の `orchestrator/tests/test_t810_coordinator.py` の `test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir` と `test_prepare_group_rejects_forged_git_identity_before_any_mkdir` で、期待した「work_root is not repository-external」の前に `cannot read worktree registration: file is absent` で落ちた。共有 repo の生きた worktree 登録を読む test で、走行中に別 session が worktree を撤去した型 (F633)。本 wave の 3 つの登録は健在で、差分は t810 と git identity の走査に触れない。
  3 shard は完走し (test 実行 357 / 253 / 219 秒)、他の赤は無い。同じ tip で 2 node を単独再走した (15978.nqsv、Elapse 9 秒): 2 passed で再現しない。本項を含む tip で受入を取り直す。
- 記録前の走査 (DW-S07): 三軸語の走査器 (`s8b_holdout_freeze search`) は rc=1 だが、hit 3 件はいずれも main に既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の file (commit cc82edc8c) で、本 wave の追加 file の hit は 0。逐語 log 5 file は行末空白だけを可逆に除去した (insight `verbatim/NORMALIZATION.md`)。`check_docs.py` 違反なし、fold の dry-run rc=0。
- 記録前に local main 5f25b616b (別 wave の land) を固定 SHA で取り込んだ (merge `803e3a78b`、docs と insight だけの前進、競合なし、[T-2844] の base digest は不変)。
- 変異用独立 clone の 1 回目は、親が対象 commit の完全 SHA を短縮形から推測して渡したため、存在しない object で update-ref が失敗して止まった (副作用なし)。rev-parse の値で作り直した。
- 工数: Codex 子 = consult 3 本 (うち 1 本は親の path 誤りで即停止)、author 2 本、review 2 本。Claude の抽出子 1 本 (sonnet、記憶メモの読み取り)。login: D297 実走 4 回、変異 probe 16 run。計算ノード: compute 1、焦点走 1、変異本走、受入。

## 次の一手差分

### 完了

- [T-2844] mocc X/P 計装の候補 commit C = `68106660686232781bca3be792a750d3e19d7a8a` (ccbench local branch `izanagi-mocc-xp-instrumentation`) を作り、bundle 保全・主 checkout の submodule git dir への fetch、C 上の正例・負例 compute 1 走 (all_pass)、D297 (GCC 11.4 / 12.3 pass、clang 14 は比較未完了を記録)、波及表の点検を済ませた。記録 = `output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md`。
  remaining: none
  base: faf28a0077babd8598766d3723f7e068bf3bb03eef1b4cae75c5de37c363bba3

### 新規

- {{T:mocc-xp-candidate-reapproval}} **P2・新規 (人間手番を含む)**: ccbench の branch `izanagi-mocc-xp-instrumentation` (C = `68106660686232781bca3be792a750d3e19d7a8a`) を GitHub `thawk105/ccbench` へ push するのは人間 (D16)。push 後、D1603 の材料 3 点 (`output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md` §2・§3・§5) を添えて D2114 項 3 の見送り台帳経路で pin 再承認を提示する wave を起こす (提示と承認後の gitlink / `CCBENCH_FULL_SHA` / `CURRENT_PIN` 更新は別 wave、T-2304 の波及を先に見積もる)。clang 比較未完了と I 面 ([T-2295]) の不足は材料に明記済み。
