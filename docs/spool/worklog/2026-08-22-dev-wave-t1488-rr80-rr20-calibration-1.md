---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1488-rr80-rr20-calibration
seq: 1
title: '[T-1488] rr80/rr20 calibrationの計算ノードcertification取得・実測・登録を完了した (コード+テスト、branch worktree-dev-wave-t1488-rr80-rr20-calibration)'
---

## 本文

- D655/D658裁定 (rr80/rr20 calibrationの取得・検証・登録をAI/ツール経路で許可) に基づき着手した。
- rr80の計算ノード実投入で、`orchestrator/holdout_observation.py` (T-523, commit `ebca2947`)
  が課すholdout保護 (rr80/rr20でのccbench実行を正式なholdout admissionなしに一律拒否する設計)
  と、D655/D658裁定が直接衝突する重大な対立を発見した。ユーザーに状況を提示し確認したところ、
  「calibration取得はholdout保護の対象外とする設計変更」を承認された。決定は
  {{D:calibration-holdout-bypass}} を参照。
- 正しさ防壁 (holdout保護) に触れる変更のため、DW-C00の軽量版判断を終了し、2回の敵対相談
  (計4レンズ) で設計を固めた。1回目の敵対相談で9件のreal所見が出たため、親が確定方針を
  示して改訂させ、2回目の敵対相談で実質1件 (両レンズ一致) に収束させた上で実装した。
- 実装後の敵対レビュー2本 (段6) で、さらに2件のreal所見 (numactl/extra_envの検証後再利用
  bypass、未消費sweepを残したままnoise phaseへ遷移できる不具合) を発見し、fixで解消した。
- 実機投入 (rr80) で3件の実装バグを追加発見・修正した (詳細は{{F:certify-python-interpreter-unpinned}}、
  {{F:certify-interpreter-fix-breaks-perf-path}}、{{F:holdout-capability-early-stop-overreject}}
  参照)。3件目 (sweep early-stop誤検出) は2回目のreal所見 (未消費sweep拒否) への修正自体が
  実機の正当な動作を壊す回帰を生んだもので、最終的に「records系列の完全消費、またはearly-stopが
  正当に発動しうる最小観測数 (3点) に達していること」のいずれかを許可する条件に落ち着いた。
- 全修正後、rr80 (request 936025.nqsv) とrr20 (request 936044.nqsv) を計算ノードで実行し、
  両方とも `calibrate_rc=0`・`quality.status=accepted` で `registered/` へcreate-only publish
  された (`calibration-6cfeb65b12970eb6.json`=rr80、`calibration-7e2be8adff051662.json`=rr20)。
  過去の誤投入 (rr80=930578.nqsv、rr20=930579.nqsv) とは無関係の新規allocationであり、
  それらを成果・受入証跡として一切参照・再利用していない。
- **本waveはD655/D658の不変条件どおり、正式H1/H2 launch・g1→g2 activation・D145 decision 5
  再訪・T-424/T-272要求閉包を一切代行しない。** `env_contract.py`のcalibration_ref (g1/g2、
  rr50) はこのwaveでは切り替えていない (2026-08-06のcommit `7e9d4364`と同じ先例)。
- 段2b/2c・段3・段3b・段6の詳細プラン・敵対所見・裁定経緯は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1488-rr80-rr20-calibration/stage*.md`
  (repo外job dir) に保全されている。
- 作業中、`git stash push` によりrepo管理下の別waveのファイル (submissions配下204件) を
  誤って一時退避してしまい、直後に `git stash apply` + `drop` で復元した。実害なし。
  その後 `rm -rf` で同じディレクトリを削除した際、上記の復元済みファイルを再度誤って削除して
  しまい、`git checkout --` で再復元した。自分が作成した6件のlogin側submission証跡
  (job-staging側に複製が残るpreflightログの重複コピー) は失われたが、実質的な成果物
  (calibration結果本体) には影響していない。
- **2026-08-23の再開セッションで、段4が事前登録していた変異matrixが未実施のまま残っていたことを
  発見し、実施した。** 実装差分が1424行で非ゼロのため`DW-S04`の免除 (「実装しない」裁定かつ
  実装差分ゼロ) に当たらない。anchorは local main取り込み後のtip `4e74a8b5`。
  M1 (未消費sweep guardの無効化)、M2 (fix3のearly-stop救済を外す過剰拒否の正例)、
  M3 (gatewayの正規化値の再利用を捨てるbypass) の**3/3 KILLED、MISMATCH 0、SURVIVED 0、
  baseline rc=0 / 27.097秒**。M1とM2は同じ3行を逆向きに変異させる対で、guardが受理側・
  拒否側の両方から拘束されていることを示す。逐語は
  `output/insights/2026-08-23_t1488-rr80-rr20-calibration/`。
- local main `c301c4fd` の取り込みでは、両親が触った実装面pathが
  `orchestrator/tests/test_ccbench_spawn_sites.py` の1件だけで合成結果が両親どちらとも
  異なるため、provenance checkerがCodex `role=author`を要求した。競合ゼロでも合成の正しさは
  保証されないので、merge結果の使い捨てsnapshot worktreeでread-onlyのCodex合成監査
  (gpt-5.6-sol / xhigh) を先に走らせ、判定「安全」・危険ゼロを得てからcommitした。
  親の実測は焦点走で58 passed (union file + holdout) と413 passed / 78.34秒
  (直接consumer 6 file)。全史provenance監査は5240件・新規違反なし。
- 段8で`docs/dev-wave/operations.md`を編集した直後のconsumer走は96件赤だったが、94件は
  **docs編集が未commitだったこと自体**が原因である。launcherの`snapshot_authority`は
  `docs/dev-wave/{operations,workers}.md`のworking tree bytesをHEADのblobと比較するため、
  未commitの編集があると起動を拒む。commit後の再走は1203 passed / 2 failedになった。
- 残る2件 (`test_codex_worker_launch.py`の
  `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[True|False]`) は
  単独再走で2 passed / rc=0。32 worker並列下で`timeout=10`のsubprocessがstdoutを空で返す
  非帰属フレークであり、本waveの差分 (DW-O11/DW-O16の散文) からは到達しえない。
  `DW-O18`に従い非帰属として記録する。
- **受入全走 (tested tip `1ac98ed7`) は42 failed / 14564 passed / 268.45秒で赤。受入受領証は
  未発行、受入leaseは解放済み。** 41件は単一原因で、本waveが登録するrr80/rr20 calibration
  成果物10 fileが、T-523のrepo全体holdout走査で三軸一致としてhitする。親が走査を直接実行した
  実測は、現ツリー (14514 file) でrr80=5・rr20=5・rr50陽性対照=85・FAIL、当該10 fileを除外
  (14504 file) でrr80=0・rr20=0・rr50=85・`_assert_search_pass: PASS`。
  **有効なrr80/rr20証明書をrepoに置くことと、repoに三軸表現が1件も無いことは同時に成り立たない。**
  2026-08-22にユーザーが承認したのは実行時admission gatewayの迂回であり、repo内容の走査は
  射程外である。D88の可逆defangも`registered/calibration-*.json`のfilenameが内容のSHA-256
  前置語であるため使えない。正しさ防壁は緩めず裁定へ返した。
- 残る1件は別原因で、in-scopeのmust-fixとして閉じた。
  `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`が
  `unreviewed: orchestrator/holdout_observation.py`で落ちていた。Codex `role=author`がperf面を
  レビューして`_REVIEWED_PERF_FILES`へ1行登録し、親の実走で5 passed / rc=0。列挙側と既存期待値は
  変更していない。

## 次の一手差分

### 更新

- [T-1488] **P1・ユーザー裁定待ち**: rr80/rr20 calibrationの取得・実測・実装・変異検証は完了した
  が、受入全走で成果物10 fileがT-523のrepo全体holdout走査に三軸一致でhitし、登録したまま
  landできないと判明した。有効なrr80/rr20証明書をrepoに置くことと、repoに三軸表現が1件も無い
  ことは同時に成り立たない。正しさ防壁の緩和は行わず裁定へ返した
  (`dev-wave-jobs/rulings-inbox/2026-08-23-t1488-rr80-rr20-artifacts-vs-holdout-freeze-scan.md`)。
  base: c5e67e1e8a5f284fc96a13ea53b1da442c2ae12170f7501efec92a3427d572f3
