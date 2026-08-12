---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t725-t694-lease-clean
seq: 1
title: 受入 lease の待ち手へ投入直前の clean 検査と provenance preflight を足した — 裁定 2 件の実体は land 済みで、F191 の安全配線 3 点と逐条照合して残っていた 2 点だけを実装した (コード + docs、変異 6/6 KILLED、branch worktree-dev-wave-t725-t694-lease-clean)
---

## 本文

- **裁定の一次資料。** 2026-08-12 の一括裁定 45 件 (発話「推奨通りでよろしく頼む」)。一次控えは
  `dev-wave-jobs/rulings-inbox/2026-08-12-coarse-provenance-45rulings.md`。[T-725] = 待ち手内
  `--no-ff` merge 許可 + 安全配線 3 点必須、[T-694] = 待ち手を `tools/` へ共通化 (同 wave)。
- **裁定の前提を実測したところ、両項の実体は既に land 済みだった。** [T-725] は [T-732]、
  [T-694] は [T-740] として 2026-08-10 に裁定され、実装は 2026-08-11 に main へ入っている
  (`483682a6` 待ち手内 merge + 所有実装面 overlap 判定、`b365e477` 自己保持、`6905d321` /
  `29bd2bfd` runbook §7.3)。[T-725]/[T-694] は backlog に重複して残っていた項目で、今回の
  一括裁定はその再承認だった。裁定は止めず、F191 の「安全配線 3 点」と実装を逐条照合して
  残差だけを実装した。
- **逐条照合の結果。** 点 1 (親 template へ SHA 差し込み) は充足 —
  待ち手が作った実在 merge commit `ce46e128` の parents を実測し、**取り込んだ main SHA は
  second parent として commit object に不可変に記録される**ことを確認した。message 本文への
  placeholder 置換より強い。点 3a (behind 再検査) も充足。**点 2 と点 3b は未充足だった。**
- **点 2 は親 brief の誤りだった (撤回)。** 待ち手は `git commit --dry-run -F` と行頭
  `AI-Agent:` の存在しか見ておらず、`docs/ai-provenance.md` が commit 前に要求する
  `check_ai_provenance.py --message-file` を通していなかった。実測で 0.097 秒・local 実行
  (dispatch なし) であり、`AI-Agent:` 行の形式違反 (product/model/reasoning/role の順・許可値) を
  実際に落とすことも確認した。
- **段 6 のレビューで親の段 4 裁定を 2 件覆した。** (i) 述語を F191 逐語どおり untracked 込みに
  すると裁定していたが、`output/env/pegasus/floor/attempts/submissions/` と `.../job-staging/` が
  `.gitignore` に無く (`git check-ignore` rc=1)、稼働中の `dev-wave-t748-pilot-path` worktree に
  実在の生成物を 7 件持つことを実測したため、**untracked を述語から外した** — untracked の
  扱いは裁定へ返す。(ii) provenance checker を merge の前に置くと書いていたが、checker が
  `MERGE_HEAD` の有無で検査対象 path を変えるという指摘を受け、**merge の後**へ確定した
  (merge 前だと staged path が空になり検出力が落ちる)。docs を実装へ寄せた。
- **撤回した親 brief の主張は他に 3 件。** 「点 2 は実装済み」「behind>0 は merge 直後なので
  構造上 clean」「land は wave 側を tested_tip の SHA 一致だけで見る」。2 番目は
  `git merge --no-ff --no-commit` + `git commit` が commit するのは index なので、merge と
  衝突しない未 stage の tracked 編集が merge 後も残ることによる。
- **[T-694] の 4 要件は実装済みと判定した。** 「周期固定」は policy range 30〜120・既定 30 で
  充足する (待ち札 TTL 300 秒を超える周期は rc=2 で起動前に落ちるので、起票理由の害は
  構造的に排除されている)。「`trap` による確実な release」は SIGKILL を捕捉できない点で
  shell の `trap` と同等であり、要件としては充足。ただし `_cleanup_lifecycle` が ownership を
  消費してから signal mask を張るまでの窓は real な欠けなので裁定へ返した。
- **段 6 レビューが出した実装面の real 所見 3 件を fix で閉じた。** checker の subprocess が
  argv 先頭 `git` でないため (i) Git discovery 環境の sanitization と (ii) stage timeout の
  どちらも掛かっていなかった (ambient `GIT_DIR` で別 repo を見る / 停止した checker が merge と
  lease を握ったまま待ち手を固める)。(iii) M3/M4 の変異 kill が fake の argv 不一致による赤
  だったため、`DW-M03` の「診断だけの赤を kill にしない」に沿って意味的経路で殺す形へ直した。
- **変異の 1 走目は 4 件 MISMATCH だった。** 事前登録した焦点 node が実測失敗集合の部分集合で、
  期待を過小に書いていた ([T-709] が裁定した部分集合一致の判定枠は未実装)。事前登録 node が
  全 6 変異で実測失敗集合に含まれることを機械検査したうえで完全集合を再導出し、2 走目で
  6/6 KILLED・MISMATCH 0 になった。1 走目の台帳は erratum として凍結した。
- **検査結果。** 焦点走 541 passed (`test_dev_wave_wait.py` + `test_check_docs.py` +
  `test_mutation_fanout.py`)。変異 6/6 KILLED (SURVIVED 0、baseline 緑、anchor は統合 commit)。

## 次の一手差分
### 完了


- [T-694] 待ち手の正本 wrapper 化は 4 要件とも実装済みと判定し、docs 側の残差 (周期の
  policy range、release の既知限界) を runbook §7.3 へ入れて終端した。本項の射程外で見つかった
  `_cleanup_lifecycle` の二重 signal 窓は {{T:cleanup-signal-window}} として別に起票した。
  remaining: none
  base: 8c5213df13eca7d94e40d3ec6a5beae39d374becdb1e1b7ba3a3aa98a178da50
- [T-725] 安全配線 3 点のうち未充足だった点 2 (provenance preflight) と点 3b (投入直前の
  clean 検査) を実装し、runbook §7.3 を改訂して終端した。述語の untracked 部分は本項の
  設計択一を超えるので {{T:untracked-acceptance-policy}} として別に起票した。
  remaining: none
  base: e90d14c4fa01936832edbc4fde5b2efacf9151368b5c25ebe87199e12d927fde

### 更新


- [T-709] **P3・裁定済み (2026-08-12 /rulings) → 枠を新設**: 波及の広い正例向けに部分集合一致
  (期待 node が実測失敗集合に含まれる) の判定枠を設ける。spec に部分一致を選ぶ理由の明記を必須とする。
  2026-08-12 に `tools/mutation_harness.py` へ未実装であることを実測し、起票を
  {{T:mutation-subset-match-frame}} へ分けた。
  base: 4f868fd9bf6c040b12a6f743253cc528a6eb7d0e722536c5c44aec876c67c5b6
### 新規


- {{T:acceptance-run-window-coverage}} **P2・新規 (裁定パッケージ)**: `prerun-clean` が閉じるのは
  claim から投入までの窓だけで、20〜40 分走る受入 command の**走行中**の変更は覆わない。
  (a) 現状維持 + 正直形の明記 (本 wave 実施済み)、(b) 走行後の `git status` / tree fingerprint
  検査を足す、(c) 受入を固定 commit の使い捨て worktree で走らせる。**親の推奨は (b)** —
  (c) は受入の実行形態と land の tested_tip 束縛の作り替えになる。成果物影響 = 実装しない場合、
  緑の受入結果が land された tip を測ったとは言い切れないまま台帳・レポートへ記録され続ける。
- {{T:acceptance-path-bypasses-waiter}} **P2・新規 (裁定パッケージ)**: `tools/run_tests.py` は
  引数なし起動を acceptance shape と判定し、待ち手を経由しない受入経路が実在する
  (2026-08-12 に waiter deadlock を迂回した実例)。本 wave の gate は掛からない。
  (a) 待ち手経由だけを権威ある dev-wave 受入と定義し直接走は記録不可、(b) `run_tests.py` 側にも
  同等 gate、(c) 現状維持。**親の推奨は (a)** — (b) は稼働中の全 wave の受入へ即座に効く。
  成果物影響 = clean 検査を経ていない受入結果が台帳へ入りうる。
- {{T:cleanup-signal-window}} **P3・新規 (裁定パッケージ)**: `_cleanup_lifecycle` は ownership を
  `NONE` にしてから `_cleanup_after_claim` へ入り、signal mask を張るのはその内側である。
  この間に 2 発目の signal が入ると cleanup が中断し、再入は ownership 消費済みで no-op になり
  lease が TTL 2,400 秒まで残留する。(a) 現状維持 + 既知限界の明記 (本 wave 実施済み)、
  (b) mask を `_cleanup_lifecycle` の入口へ移し ownership 消費をその内側へ、(c) 外部 watchdog。
  **親の推奨は (b)**。窓は µs で TTL 有界だが、[T-694] が求めた「確実な release」の唯一残る
  欠けである。成果物影響 = 稀に lease が最大 2,400 秒残留し他 wave の受入が遅れる。
- {{T:untracked-acceptance-policy}} **P2・新規 (裁定パッケージ)**: 受入の clean 述語が untracked を
  拒否すべきかは、floor の生成物 (`output/env/pegasus/floor/attempts/submissions/` =
  submit receipt、`.../job-staging/` = reservation・qstat raw・job-result) を repo で追跡するか
  repo 外へ出すかと不可分である。前者は receipt を持つので `silo_ladder_rung1/job-staging/` の
  ignore 先例をそのまま当てられない。(a) 両 path を `.gitignore` へ入れ述語を untracked 込みへ、
  (b) submissions は commit・job-staging は ignore、(c) tracked-only を正式裁定として F191 と
  runbook を書き直す。**親の推奨は (b)** — receipt は証拠、staging は再生成可能という区別が
  先例と整合する。成果物影響 = 未裁定のままだと、untracked な test/conftest の混入を受入が
  検出できない状態が残る。
- {{T:mutation-subset-match-frame}} **P3・新規**: [T-709] が裁定した部分集合一致の判定枠
  (期待 node が実測失敗集合に含まれれば KILLED) は `tools/mutation_harness.py` に未実装である。
  本 wave では完全集合を再導出して 2 走した。成果物影響 = 波及の広い変異のたびに 1 走が
  MISMATCH で失われ、変異台帳の 1 走目が erratum として残り続ける。

