---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1636-dangling-argv-batch
seq: 3
title: [T-1636] dangling 監査の git grep を上限つき分割実行にする (コード + テスト、branch worktree-dev-wave-t1636-dangling-argv-batch)
---

## 本文

- **本 wave で実測した値と、その測定 regime。** 機体はこの login node、corpus は探索根
  `/work/1/SFC/tanab/dev-wave-jobs` (実測時点で 122,106 entry、path 長の最大 334 byte)、
  対象 repo は本 worktree の main tree。`getconf ARG_MAX` = 2,097,152。
  - 実効 `E2BIG` 閾値: 96 byte pattern で 18,033 本は成功、18,034 本で `OSError [Errno 7]`
    (argv 約 1,785,406 byte)。`ARG_MAX` より低い。
  - **argv 上限内でも死ぬ領域がある**: 67 byte pattern 20,000 本 (argv 1,420,088 byte) は
    72.7 秒走ったのち `rc=-9` (SIGKILL)。
  - `git grep` の RSS は pattern 数に線形: 500 本 108 MB / 2,000 本 415 MB / 8,000 本 1,642 MB
    (約 205 KB/pattern)。上の SIGKILL はこれで説明がつく。
  - 実 repo の所要は約 4.5 ms/pattern でほぼ線形、1 回あたり固定費は約 0.30 秒
    (100 本 0.71s / 500 本 2.37s / 1,000 本 4.18s / 2,000 本 8.99s / 4,000 本 18.87s)。
  - `os.sysconf("SC_ARG_MAX") // (pattern 長 + 1) + 1` 本の argv は、pattern 長 32 / 67 / 96 / 256 の
    いずれでも 0.02 秒以内に `errno=7` を発火する。
  - **これらは 1 機・1 corpus・1 Git 版の局所値であり一般上界ではない。** 段 3 の 2 レンズが
    そろってこの一般化を攻撃し、親は「batch を小さくしても総時間はほぼ不変」という当初の
    一般化を撤回した (固定費 0.30 秒があるため全 singleton 化は総時間を桁で悪化させる)。
- **本番相当の生死確認を実施した。** `/cleanup-branches` §1 が必須とする
  `python3 tools/audit_dangling_commits.py --offrepo-root /work/1/SFC/tanab/dev-wave-jobs` を
  是正後の実装で実走し、**完走して rc=1** を返した。F526 の rc=2 (実行不能・削除停止) ではなく、
  §1 が「所見あり → §5 で報告・救出判断」と定める側である。
  wall clock 2:16:05 (user 7300.81s / sys 1541.57s / CPU 108%)、peak RSS 591,392 KB。
  repo 外の同一実体で 7,050 (commit, path) 対を抑止し、報告は 21,130 行。
  参照確認不能・path 解釈不能・batch rc・実行不能のいずれのマーカーも 0 件だった。
  分割前は 8,000 pattern の時点で RSS が 1,642 MB に達していたことと対照される。
- **却下した設計。** 段 2 プランは「単独で byte 予算を超える pattern を実行前に拒否する」
  fail-closed を含んでいたが、親は採用しなかった。実環境の path 長は最大 334 byte で予算
  131,072 byte に対し到達不能な述語であり (DW-O13)、受理集合と rc 契約を変え、
  F526 と同型の「関門が恒久的に通れない」経路を新設するためである。
  上限を environment 実測から動的に clamp する案も、予算が `SC_ARG_MAX` の 1/16 である以上
  それが問題になる状況ではあらゆる subprocess 起動が壊れるとして却下した。
- **段 3 の敵対相談が受理集合の破れを 1 件見つけた。** `audit()` は既に commit OID を持って
  いるのに `audit_with_offrepo()` がそれを捨てて symbolic ref を渡しており、分割は ref の
  解決回数を 1 回から batch 数へ増やす。混ざった snapshot は「どの単一 snapshot にも存在しない
  参照」を作り、抑止が過剰側へ倒れる。scope 内として是正した ({{D:audit-ref-pinned-to-single-commit}})。
- **段 6 レビューはテストの検出力の穴を 5 件見つけた。** 実装の誤りではなく、
  「この変異を入れても全テストが通る」形である (executor の batch 打ち切り、先頭 batch の
  rc=1 早期 return、最初の `git show` 失敗の見逃し、basename だけの重複排除、
  landed 判定直前の ref 再解決)。fix はテスト側だけを強くし、production を 1 行も変えていない。
- **変異は 2 走した。** 初回は probe で、`KILLED 7 / MISMATCH 8 / SURVIVED 0 / TIMEOUT 0`。
  MISMATCH は殺し損ねではなく、親が事前登録した期待 node 集合が不完全だったためである
  (期待 node は完全集合で完全一致のみ KILLED と数える規約)。実測した完全集合で再登録し、
  最終走で **15/15 KILLED・期待 node 完全一致・SURVIVED 0・baseline PASSED**。
  段 6 レビューが「全テストを通る」と示した 5 変異は、いずれも**ちょうど 1 node** だけを
  落とした (単一理由性が成立)。初回 probe の結果は erratum として残す。
  なお本数上限を削る変異は 10 node、先頭 batch だけ返す変異は 11 node を落とす過剰決定であり、
  これらは冗長 gate として扱い単独変異の証拠には使わない。
- **DW-M08 の新旧両走は登録していない。** 本 wave は実装差分を伴い、M1〜M15 の対象関数が
  変更前 HEAD に存在しないためである。
- **セッション異常。** 段 6 fix の待ち手 (`tools/dev_wave_wait.py producer`) が、producer 生存中に
  rc=0・出力ゼロで偽完了した。`.done` 不在と `git diff` 未変化で気づき、完了扱いにせず張り直した。
  F24 の同型再発として台帳へ追記した。
- **受入 attempt 1 は F136 の非帰属赤で捨てた。** `test_s8b_floor_campaign.py` の
  `_real_output_snapshot()` 系が 11 件赤 (11 failed / 15,431 passed / 60 skipped)。
  受入 shard が同じ作業木から request `945262` と `945263` を重ねて投入する既知の機序で、
  junit 差分は 11 件とも `first extra item: ('dir', 'task-runs/reports')`。台帳が定める 3 点で
  帰属を否定した (実装面差分に `launch_cert` / `certificate` 参照 0 件、同 file の焦点走が
  451 passed / 2 skipped で緑、junit 差分が `output/task-runs/` の dir 増加)。
  **同日 2・3 例目は docs-only wave だったが本 wave は実装 wave であり、差分の性質は条件でない**
  ことが確定した。
- **子の工数。** codex 子は 7 本 (plan 1、consult 2、author 1、review 2、fix 1)。
  いずれも `gpt-5.6-sol` / `reasoning=xhigh`。子は sandbox の制約で pytest を実走できず、
  テストの実測はすべて親が行った。
- **段 8 の自己改善候補は 2 件挙げて、いずれも文書変更なしと裁定した。** (1) `DW-S05-A` は段 5 を
  `reasoning=xhigh` と書くが launcher は author / fix で `--reasoning` を拒否する。ただし
  `DW-O01` が「effort は段 5 / 6 が docs 権威から導出、caller 指定は不可」と既に正本として
  述べており reference 側に矛盾はないため、満杯の byte 予算を使ってまで補わない。
  (2) 期待 node の完全集合を事前に確定できない wave では変異を probe → 再登録 → 再走の 2 走に
  するのが実際的だが、`DW-M08` が既にその手順を持っている。いずれも新規発火点ではない。
- **scope 外の real 所見をユーザーへ返す。** 外部 copy の検証完了から branch 削除までの
  TOCTOU が残る ({{T:cleanup-suppression-recheck}})。

## 次の一手差分

### 完了

- [T-1636] `_landed_reference_matches()` を argv byte と pattern 本数の二重上限で分割実行し、
  順序保存の重複排除で合流させた。argv 上限を超える母集合でも完走することを、`SC_ARG_MAX` 由来の
  positive control と production executor を通る母集合で pin した。変異 15/15 KILLED。
  remaining: none
  base: 91f1ccf2e44ef41d1cabec9a9c39ff9da149eb6fd8ef0267db664667ea4be297

### 新規

- {{T:cleanup-suppression-recheck}} **P2・新規**: dangling 監査が抑止根拠に採った外部 copy を、
  `/cleanup-branches` の削除直前に再検証する gate を検討する。監査は最終 `fstat` 後に
  descriptor を閉じ、以後は path だけを根拠として保持するため、監査完了から branch 削除までに
  別 process がその実体を削除・変更すると、回収元が無いまま branch が消える。
  上位 cleanup に lock または直前再検証があるかは未確認。
