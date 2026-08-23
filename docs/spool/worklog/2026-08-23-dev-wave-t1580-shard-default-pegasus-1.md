---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1580-shard-default-pegasus
seq: 1
title: 受入全走の計算ノード分割を Pegasus 既定へ切り替え、admission と自動再試行を保ったまま既定 K=2 にした (コード+テスト、branch worktree-dev-wave-t1580-shard-default-pegasus、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **ユーザー裁定 (2026-08-23)**:「queue 待ちというのは基本あまり考えなくて良い。だから計算ノードへ
  分割ジョブを投げて早く終わることを試みるように修正してくれ (pegasus 環境下なら)」。
  D710 が既定無効の根拠にしていた「片方が毎回 queue 待ちを引くので総所要は負ける」を
  設計制約から外した。実装は {{D:shard-default-on-pegasus}}。
- **2 レンズ (段 3) が独立に同じ 2 点を挙げ、親は両方採用して scope を広げた。**
  - 分割経路が login admission と queue 無効時の契約を迂回する点。親 brief の provisional 前提
    (P5「admission 迂回を受容する」) を**取り下げ**、admission-first へ設計変更した。
    ユーザー裁定は「queue 待ちの長さを性能判断から外す」であって「queue が停止していても投げる」
    でも「login の memory admission を無視する」でもない、という読みを採った。
  - 分割走が no-verdict 自動再試行を失う点。親が消費側 (`tools/dev_wave_wait.py` の
    `_retry_evidence_reason()`) と marker producer を一次資料で照合して構造的に成立すると確認し、
    {{F:shard-dispatch-marker-lost}} として台帳化、{{D:aggregate-no-verdict-attestation}} で復元した。
- **数値の一般化を 2 レンズの指摘どおり取り下げた。** brief は D710 の実測から「K=2 は 20〜30 秒
  速い」と書いていたが、これは opt-in の少数走の観測であり既定化後の regime へ転移しない
  (D713 が禁じる一般化に当たる)。決定文では「K=3 は改善せず要求数と故障面だけ増えるので、
  **故障面の小さい保守的な初期値**として K=2 を選ぶ」と書き直した。K=2 が期待値で有利になる
  単発失敗率の上限は概算 11〜19% 未満だが、この失敗率は未計測である。
- **scope 外へ返した real 所見 (実装しない)**: 受入 receipt への shard 証跡 (既存 ID が所有)、
  login collection と compute の env 非対称、共通 conftest / 自動 plugin による縮小を gate 2/3 が
  見ない件、部分失敗時の相方 job と orphan hold、`#PBS -b 2` による 1 要求 2 ノード化、適応 K、
  適格判定後の env 書換え窓。
- **refuted と裁定した所見**: 部分起動から report index gate をすり抜ける経路、gate 失敗後の
  単一走 fallback の混入 (現状も無いことを確認)、焦点走・collect-only・非 LOGIN・内部 shard の
  再帰活性化、`--force-dispatch` が admission を迂回する点 (運用者が dispatch を明示的に選んだ形
  なので仕様どおりと裁定)、bounded scope の cgroup attestation が shard 拒否より先に走るように
  なった点 (rc はどちらも 16 で成果物の値・受理集合・参照は不変なので nit)。
- **変異 matrix は 2 巡走らせた。1 巡目の MISMATCH 1 件は自分の probe の計測汚染だった (erratum)。**
  期待 node を確定する probe を login のローカル bounded scope 経由で取ったため、テスト process
  自身の `_bounded_scope_membership()` が True になり、M3 (LOGIN 条件の削除) で
  `test_explicit_shards_reject_nonlogin_without_fallback[2]/[3]` が eligible=False のまま
  rc=16 を返して pass していた。計算ノードには bounded scope marker が無いため両 node も赤になる。
  1 巡目 = baseline PASSED・KILLED 8・MISMATCH 1・SURVIVED 0 (12.0 分、spec `c8f893b5`)。
  期待 node を dispatch 実測へ直した 2 巡目 = **baseline PASSED・9/9 KILLED・SURVIVED 0・
  MISMATCH 0** (5.2 分、spec `e281623b`、anchor commit `6c7ae156`)。
- **段 8 の自己改善は、実測済みの候補 3 件がすべて docs 予算に阻まれて入庫できなかった。**
  候補は (1) 受入 rc=70 `receipt-main-moved` は main 競走でテストの赤ではない旨の `DW-O27` 統合、
  (2) 受入 preflight が incoming と衝突しない untracked でも止まる旨の `DW-O18` 統合、
  (3) 期待 node の probe は本走と同じ実行経路で取る旨の `DW-M08` 統合。
  実際に編集して `tools/check_docs.py` を走らせたところ、`DW-O18` 1218 bytes > 1000、
  `DW-O27` 1214 bytes > 1000、`docs/dev-wave/**` の L1.5 unique footprint 9739 bytes > 9566 で
  3 件とも違反になった。自己改善契約は「予算に収まらなければ reference へ統合し、それでも
  意味等価にできなければ変更を止めてユーザー裁定へ返す。予算値を上げる変更は独立審査対象」と
  定めているため、**編集を revert して裁定へ返した** ({{T:devwave-docs-budget-blocked}})。
  (1)(2) の一次控えは `dev-wave-jobs/rulings-inbox/2026-08-23-dev-wave-acceptance-race-and-clean-preflight.md`
  に残したままにしてある (次の担当が引き継げるよう fold しない)。
- 子の工数: codex 子 8 本 (plan 1・consult 2・author 1・review 2・fix 2) + 焦点再レビュー 1 本、
  いずれも model=gpt-5.6-sol / reasoning=xhigh / outcome=accepted。段 5 実装子は 48 model call、
  wall 1193.8 秒。
- 親の実測: 焦点走 `orchestrator/tests/test_run_tests_shards.py` = 168 passed / 6.52 秒、
  consumer 9 file = 1191 passed / 1 skipped / 64.93 秒。受入全走はこの記録 commit を含む tip に
  対して投入する。

## 次の一手差分

### 新規

- {{T:login-compute-env-symmetry}} **P2・新規**: 分割走の login collection は `os.environ` の
  全複製で走り、compute 側は task の env allowlist で走るため、collection を変える env が
  両側で食い違うと gate 3 が rc=16 になる。実測では `PYTHONPATH` が login にだけ存在し
  allowlist 外だが、D710 の K=2 実測走は gate 3 を通って緑であり現に発火していない。
  対称化するか、既定経路の適格条件へ「非伝播で collection を変える env が無いこと」を足すかを決める。
- {{T:shard-canonical-universe-authority}} **P2・新規**: 共通 conftest や pytest11 自動 plugin が
  collection 集合を縮めた場合、gate 2 (shard 間一致) と gate 3 (login の独立 collection) は
  同じ縮小集合へ同意する。K=1 にも同じくある canonical oracle 不在の限界だが、既定化により
  全受入がこの限界に依存する。plugin inventory か別 commit 由来の nodeid 台帳を置くかを決める。
- {{T:shard-partial-failure-orphan-hold}} **P2・新規**: 分割の片方が早期 infra failure、
  もう片方が既に RUN のとき、親は worker を止めるが PBS job は継続し、回収は RUN を削除しないため
  orphan hold が残る。hold は同じ checkout の後続 dispatch を止める。回収経路を決める。
- {{T:acceptance-single-request-two-nodes}} **P2・新規**: `#PBS -b 2` で 1 要求 2 ノードを取れば
  queue 要求を 1 回にできる。現 dispatcher は 1 ノード・1 結果・1 ログ前提で、node index・
  個別 artifact・集約 rc・cleanup の新設を伴う。分割の目的により直接的な設計。
- {{T:adaptive-shard-k}} **P3・新規**: 負荷に応じて K を動的に選ぶ。現行の queue 状態は
  可用か否かしか返さず待ち時間を予測しない。本 wave の経路適応 (local=K1 / dispatch=K2) の
  telemetry を貯めてから裁定する。
- {{T:shard-env-toctou}} **P3・新規**: 適格判定の後に `PYTEST_ADDOPTS` を process 内で書き換える
  窓が残る。これを行えるのは `tools/run_tests.py` の import graph に既に入っているコードだけで、
  そこを取れる攻撃者は runner の rc を直接偽造できるため既定化による権限の上乗せはない。
  選択 env の入口 snapshot と全経路への強制を入れるかを決める。
- {{T:devwave-docs-budget-blocked}} **P1・ユーザー裁定待ち**: dev-wave docs の予算が満杯で、
  実測済みの手順 3 件 (`DW-O27` の rc=70 main 競走、`DW-O18` の untracked preflight、
  `DW-M08` の probe 実行経路) を入庫できない。編集して実測した超過は `DW-O18` 1218/1000、
  `DW-O27` 1214/1000、L1.5 footprint 9739/9566。自己改善契約により予算引き上げは独立審査対象で、
  既存文の圧縮は exact pin を壊す既知の失敗型がある。**(a) 予算を上げる、(b) 既存節の圧縮を
  別 wave で審査する、(c) 3 件を入庫しないまま運用する**のいずれかを裁定してほしい。

### 見送り追記

- [T-813] 2026-08-23 に {{D:shard-default-on-pegasus}} で Pegasus LOGIN の受入形に限り既定有効化した (2026-08-11 の「いま入れない」判断は D711 の 6 段 gate 着地で解消済み)。
