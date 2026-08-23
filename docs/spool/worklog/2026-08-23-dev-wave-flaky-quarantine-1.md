---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-flaky-quarantine
seq: 1
title: 環境フレークの登録制隔離を新設し、F57 と F373 は隔離せず修理した (コード+テスト、branch worktree-dev-wave-flaky-quarantine、変異matrix = baseline PASSED・MUT-1〜4 4/4 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー指示は「環境条件で不安定に失敗するテストを除外し、除外したものについて環境条件に
  左右されずに検証できるようにするテスト改善タスクを立てて、そこで再導入する」だった。
  並行 6 セッションから一次資料つきで実測を回収し、対象を切り分けた結果、
  **当初フレークと目されていた対象の大半が決定的な赤か、隔離ではなく修理が適切な対象だった。**
  設計判断は {{D:flaky-quarantine-node-id-registry}} と
  {{D:repair-over-quarantine-for-fixture-budgets}}。
- **隔離した対象は 1 node だけである** —
  `orchestrator/tests/test_mutation_harness.py::test_sigterm_handler_stops_child_and_restores_active_mutation`。
  registry の再導入タスク field は番号でなく slug を保持する設計とした
  (番号は fold が land 時に採るためコードへ書けない)。
  **この entry が指す slug は `flaky-sigterm-sync-point` で、本 fold が採番する新規タスクと
  1 対 1 で対応する。**
- 隔離しなかったもの: `test_sort_swo_oracle.py` (別セッション担当、依存の未構築)、
  `test_spool_fold.py` の 1 件 (main 側 drift)、`test_t338_submission_gate_unit5.py` 3 件
  (失敗本文が digest の byte 予算で省略され理由が取れない)。
- **分類の誤りが 3 セッションで独立に起きた。** 親は `test_dev_wave_land.py::
  test_exploration_external_root_keeps_wave_clean` を計算ノード単独走 1 回の赤で「決定的な実欠陥」と
  分類し、別セッションは clean main で 1 回再現して「決定的」と分類し、
  裁定集約セッションは 5 走 5 一致から「決定的」と分類した。**3 件とも誤りだった。**
  最後のものは `/tmp` の oracle memo キャッシュが失敗を保持していただけで、
  依存の構築が進むと 26 → 10 件へ動いた。**再現は決定性の証拠にならない。**
  決定性を主張するには、非決定性を生みうる条件 (負荷・並行度・キャッシュ・環境変数) を変えた
  対照が要る。この教訓を受けて registry の受理条件へ failure signature の記録を必須に加えた。
- **子は 6 本すべてテストを実走できなかった** (Pegasus の `qstat -Q` 認証失敗および
  sandbox の socket 拒否)。契約どおり全員が「実装済み・未実走」と申告し、実走は親が担った。
  その結果、親の実測が land 前に欠陥を 4 件捕まえた: (1) stale registry 検査が焦点走で誤発火し
  隔離対象 file を含まない走行を全て落とす、(2) 新しい判定が合成 config で例外になり
  既存の配線ガード 2 件を落とす、(3) 新設回帰テスト自身が xdist の出力並びに依存した脆い照合
  (本 wave が修理した F373 と同じ型)、(4) 同テストが絞られた collection を渡していて
  検査したい条件へ設計上到達できない。
- **main 取り込みの合成監査が実害を 1 件検出した** ({{F:merge-narrowing-misread}})。
  両親が `orchestrator/tests/conftest.py` を独立に変更し自動 merge は競合なしで通ったが、
  main 側の認証済み `--ignore` を本 wave 側がユーザー絞り込みと誤認し、
  受入全走のたびに stale 検査を無効化していた。textual に競合しないことは
  意味的に正しいことを保証しない、という既知の型の実例である。
- **並行セッションとの調整で 144 test を守った。** 別セッターが
  `test_codex_worker_launch.py` を file 単位で恒久除外契約へ載せようとしていたため、
  修理済みかつ実走緑 (request `939036.nqsv`、`170 passed in 6.55s`) であることを伝えて撤回を得た。
  なお修理という選択に至れたのは、別セッションが先に
  「予算が薄すぎるテストであって壊れたテストではないのでは」と提起していたためである。
  その提起が無ければ隔離側で処理して 130 node を止めていた可能性が高い。
- 変異 matrix は初回に期待 node がパラメタ化で実在せず fail-closed で停止し、
  次に baseline が dispatch モードで受領証行を取れず停止した。どちらも
  production write の前に止まっており、harness の fail-closed が機能している。
  `DW-M08` に従い probe 走行を erratum として保全 (`mutation-ledger-probe1.json`) し、
  MUT-4 の期待集合を実効 gate へ再照準して再走した。probe で判明したのは、
  negative control の 1 つ `[failure signature-changes1]` が別の層に mask されていることである。
  signature 照合の検出力自体は専用テストが持つため穴ではない。
- 実測: F373 の対照実験は同一 tree・同一コマンド・同一 ambient 環境 (`FORCE_COLOR=3`) で
  修理前 rc=1 / 修理後 rc=0。launcher 全走は request `939036.nqsv` で 48 worker
  `170 passed in 6.55s`。段 6 の検証 7 file 焦点走は `255 passed / 2 skipped / rc=0`。
  provenance 全史監査は 5045 件・新規違反なし。

- **段 8 の自己改善は実施せず裁定へ送る。** 候補は「実測が並行 session へ分散する型では
  brief 前に一次資料を回収する」「他 session の分類をそのまま採らず、割れたら親が自分で測る」の
  2 件で、いずれも `DW-S01` が自然な home だった。しかし追記すると
  `docs/dev-wave/**` の L1 unique footprint が予算 10625 bytes を超える
  (初稿で 11023、1 文へ圧縮しても 10696)。圧縮で意味等価にできる余地が尽きたため、
  自己改善契約の「予算に収まらなければ止めてユーザー裁定へ返す」に従い入口を変更しなかった。
  **教訓自体は失われていない** — 分類の誤り 3 件と「再現は決定性の証拠にならない」は
  F57 の再発項と supersede 行に、設計判断は {{D:flaky-quarantine-node-id-registry}} に
  耐久記録されている。予算値の引き上げは通常の自己改善に含めず独立審査の対象とする。

## 次の一手差分

### 新規

- {{T:flaky-sigterm-sync-point}} **P1・新規**: 隔離した
  `test_mutation_harness.py::test_sigterm_handler_stops_child_and_restores_active_mutation` を
  環境非依存な検証へ作り替えて再導入する。子が「SIGTERM を受け取れる状態に到達した」ことを
  待つ同期点を入れ、子の早期終了と競合しない形にする。負荷をかけた条件で同一 tree・
  同一 collection 条件の走行を複数回行い全て緑であることを示したうえで、
  registry から entry を消す。解除時は positive control で検出力が実際に戻ったことを示す。
  **registry の `reintroduction_task_id` が指す slug はこのタスクである。**
- {{T:launcher-wall-budget-fixed-cost-split}} **P2・新規**: launcher テストの
  `attempt` 本体時間と周辺固定費を切り分けて計測する。F57 の再発項が記録した
  `attempt[1].wall_clock_s=1.329` と `receipt_actuals.wall_clock_s=3.268` の乖離 約 1.94 秒が、
  負荷に比例して膨らむのか特定の段に集中するのかは 1 走行 1 サンプルから分離できていない。
  切り分け結果に基づき、締切を「attempt 本体で測る」か「固定費を予算から除く」形へ変える。
  **予算を一律に増やす形は採らない** (本当に暴走した被験体を捕まえられなくなる)。
- {{T:exploration-external-root-flaky-cause}} **P2・新規**:
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` の非決定性の
  原因を特定する。同一 commit `e8671324` で通ったり落ちたりすることは実測済みで、
  署名は `execution_guard.require_certified_writer_authorization` /
  `numactl=('numactl','--interleave=all')` / `env_contract=None`。
  原因が特定できれば本 wave が作った registry へ entry を 1 つ足すだけで隔離でき、
  機構側の変更は要らない。**原因未特定のまま隔離してはならない。**
- {{T:flaky-quarantine-receipt-binding}} **P2・新規**: 隔離集合を acceptance receipt へ束縛する。
  現状は走行末尾の `IZANAGI_FLAKY_HOLD_SUMMARY_V1` と registry の version 管理でしか
  隔離範囲が辿れず、`child-green` の受領証それ自体からは「何件が隔離されていたか」が読めない。
  `tools/dev_wave_land.py` の受理条件と receipt schema に触るため本 wave の scope 外とした。
- {{T:failure-digest-budget-loses-evidence}} **P2・新規**: 失敗 digest の byte 予算が
  証拠を体系的に捨てている。実測で `failures=60 selected=10 omitted_failures=50
  source_bytes=226327 budget_bytes=49152`。赤が数十件出る走行では失敗本文の 8 割以上が失われ、
  `omitted_manifest_sha256` は残るが manifest 実体が log に無いため理由を復元できない。
  本 wave でも `test_t338_submission_gate_unit5.py` 3 件がこれで理由を取れず登録対象から外れた。
