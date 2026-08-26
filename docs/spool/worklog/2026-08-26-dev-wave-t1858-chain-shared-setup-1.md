---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1858-chain-shared-setup
seq: 1
title: 受入の排他鎖 2 本を共有化で 42% / 36% 短縮し、鎖はもう律速でないことを実測した (コード + docs、branch worktree-dev-wave-t1858-chain-shared-setup、変異 matrix = baseline PASSED・6/6 一致・KILLED 5・SURVIVED 1 (登録どおり)・MISMATCH 0)
---

## 本文

- 依頼は「`s8c-preregistration-candidate` (台帳 97.1 秒) と `s8c-predicate-snapshot` (同 99.7 秒) の
  2 鎖に同じ手を当てる。ほどければ『鎖以外の最遅 worker 149.4 秒』の項が下がる」。
  短縮の手はテストを削る・弱めるのではなく共通の下準備の共有に限る、という裁定付きだった。
- **依頼の前提を 2 つ訂正した。** (1) 97.1 / 99.7 秒は file 合計であって鎖の長さではない。
  xdist group 所属 node だけで集計した鎖は candidate 83.500 秒 (5 node)・
  predicate-snapshot 52.001 秒 (3 node) である。(2) 台帳 15909 entry の総 work は
  **7874.186 秒**で `W/48 = 164.046 秒`、最長単体 node は 140.0 秒。したがって理想 48-way の
  下界は `max(164.046, 83.500, 140.0) = W/48` であり、**この 2 鎖はどちらも律速ではない**。
  「本 wave 後の次の律速はここになる」は現台帳では成り立たない。D747 が使った 5316.9 秒は
  当時の値で、現台帳では再現しない。段 3 レンズ B と親が独立に再集計して一致した。
- **それでも短縮の値打ちは残る。** 総 work が下界を支配している regime では、work を減らすことが
  下界を下げる唯一の手である。詳細と内訳は
  `output/insights/2026-08-26_t1858-chain-shared-setup.md`。
- **段 2 のプランは predicate 鎖を据え置いた。段 3 の 2 レンズが独立にこれを覆し、親が採用した。**
  段 2 の根拠は「2 回目の HEAD 評価は独立再導出そのものが検出力」だったが、共有するのは
  fixture 内の 1 回目だけで、比較の左辺は独立に再導出されたままなので恒真化しない。
  2 回目だけが殺す production の 1 行変異も書けなかった。裁定は {{D:shared-head-eval-not-tautological}}。
- **失う分は安い gate で補った。** fixture が記録した OID と assert 直前の HEAD OID を突き合わせる。
  gate が恒真にならないよう、正例と負例を helper 経由で 1 件ずつ足した。
  **受理集合は前後で同一ではなく、新実装の拒否集合の方が広い** — 旧実装は HEAD が動いても
  評価結果が同じなら通っていた。段 6 レビュー B が実装子の報告のこの過大記述を訂正した。
- **段 6 レビュー A が real な must-fix を 1 件出した。** fixture が `rev-parse` で OID を記録した後、
  `evaluate_all` / `ls-tree` / `archive` はいずれも文字列 `"HEAD"` を渡してそれぞれ独立に
  再解決していた。記録 OID・評価結果・snapshot が別 commit 由来になりうる状態で、gate では
  検出できない。fix は解決済み OID を 3 か所すべてへ渡すこと。裁定は
  {{D:head-bound-ops-need-one-resolved-oid}}。
- **`acceptance_duration_ledger.json` の更新は不採用にした。** 段 3 レンズ B は同 wave での更新を
  推したが、(a) 台帳は scheduling hint として読まれるだけで実所要との照合はなく node 集合も
  件数も変わらないのでどの検査も赤にならない、(b) 更新するなら全 15909 entry の再生成になり
  無関係な差分を本 wave のレビュー対象へ持ち込む、(c) 台帳は既に多数の node で stale で本 wave が
  原因ではない、の 3 点による。次の一手へ起票した。
- **効果の言い方を段 3 の指摘で直した。** 「削減 work / 48」は実 wall 短縮の上限ではなく、
  均衡した work 律速時の下界改善量である。実 wall は tail が別 worker なら 0、短縮した worker が
  tail ならそれ以上にもなりうる。xdist 3.8.0 には完了 worker が次 unit を引く再配分機構が
  実在するが、global queue が尽きた後に既割当 unit を移す機構はない。
- 起動時の編集面重複検査で、`orchestrator/tests/conftest.py` (dev-wave-t1629-ratification-broker、
  dev-wave-b10-overthrottle-grid 所有) と `orchestrator/tests/test_real_repo_serialization.py`
  (dev-wave-b10-overthrottle-grid、dev-wave-flaky-holds-20260826 所有) を非接触と決めた。
  これが「群構成を変えない」という不変条件の実務上の根拠でもある。
- 変異 matrix の投入で、並行 wave が共有木 (`?? .codex/worktrees/` 等) を書き換えるため
  `mutation_worktree.py` の事後検査が 1 度落ちた。独立 clone を `--source-repo` に渡して
  構造的に断った。submodule は file transport が既定で拒否されるため
  `-c protocol.file.allow=always` が要る。
- **F95 を走行前に引かずに踏んだ。** 変異 spec の期待 node に `@<group>` 接尾辞を書いて
  harness が rc=2 で止まった。接尾辞は並列走行でのみ合成され、実在検査が使う素の collection には
  現れない。F95 は同型を初出 2026-08-04 から 6 例記録しており、**`s8c-predicate-snapshot` group
  そのものについても 2026-08-25 に記録済み**で、そこには回避策 (収集は loadgroup 走、機械照合は
  `-n 0` の直列走) まで書いてある。親は台帳を引く前に投入した。F95 自身が「散文の再発記録を
  これ以上重ねても検知にならない」と 4 例で結論しているので、本 wave は再発行を足さない。
  恒久対応 (harness 側で loadgroup 接尾辞を機械的に扱う) は [T-417] が所有し未実施のままである。
  なお本 wave が採ったのは台帳の 2026-08-25 項と同じ `-n 0` 直列であり、
  古い項が採っていた `--deselect` ではない — `--deselect` は当の group node を走行から外すため、
  鎖そのものを対象にする本 wave では検出力の実証にならない。
- **受入全走は 2 走とも非帰属の赤で、land できていない。**
  2 走とも `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` 1 件だけが落ちた
  (17392 passed / 1 failed / 64 skipped)。assertion は「子が 2 秒以内に pid file を登録しなかった」
  という時間依存の主張で、単独走は 1 passed / 7.15 秒で再現しない。本 wave の差分 (s8c 事前登録の
  test 2 file) はこの経路へ到達しない。F57 の既記録と同一の node・同一の assertion 本文である。
  `DW-O18` が規定する再赤の是正 (flaky hold への登録) は、**経路の file が並行 wave の所有下**で
  実行できなかった。**書き込まずに所有者へ相談したのが正解だった** — 同じ node を別 wave
  (`worktree-dev-wave-t1848-env-coincidence`) が hold ではなく修理で既に閉じており、
  hold を登録していたら着地の瞬間に陳腐化する台帳項目を作っていた。修理は 2 秒の絶対期限を
  除去して判定を launcher 終了後へ移すもので、上限は 1 つも広げていない。
  詳細と恒久対応は {{F:flaky-hold-remediation-blocked-by-ownership}}。
  **実装・記録・変異はすべて完了しており、残るのは当該修理の land 後に受入をもう一度取ることだけである。**
- **land を塞ぐもう 1 つの欠陥は本 wave の外で修理・着地した。** 並行 wave の警告で気づいた。
  `docs/worklog.md` が rotation 閾値に近く、fold が作る archive 名
  `worklog-phase3-0826-1001.md` が `check_docs.py` の分類器に日付範囲と誤読され、
  entry 1001 が全域番号 universe から消えて carry が宙吊りになる欠陥である
  (射程 1001-1031 / 1101-1130 / 1201-1231)。親は分類器を直接叩いて再現を確認し、
  着手していないことを伝えて譲った。main `4c88c3d0` で修理が着地し、
  同じ検査で 1001・1031・1101・1201 がすべて numbered になること、
  日付範囲名 `0801-0802` が unnumbered のままであることを実測で確かめた。

## 次の一手差分

### 完了

- [T-1858] 2 鎖の共有化を実装し、前後比較 (candidate 76.76 → 44.44 秒、
  predicate 44.37 → 28.56 秒) と変異 matrix による検出力保存の実証まで完了した。
  remaining: none
  base: 6080e9f68e53d09b107d4cb7e3d410f955607028a6adbb3758d5f22ef16d75f1
- [T-1571] 排他鎖 2 本の同時短縮と `s8c-preregistration-candidate` 鎖の内訳測定を完了した。
  内訳は insight に逐語で残した。
  remaining: none
  base: 88d8d83453dfdc8019dbb1b1b112920b919bc06657b796be8974272d76d0ed56

### 新規

- {{T:acceptance-duration-ledger-regeneration}} **P2・新規**:
  `orchestrator/tests/acceptance_duration_ledger.json` を変更後の受入 JUnit 群から全再生成する。
  現台帳は本 wave の 8 node を含め多数が stale で、scheduler の投入順が実所要と合っていない。
  手順は変更後の完全な JUnit へ `tools/update_acceptance_duration_ledger.py` を当て、
  同じ入力へ `--check` を付けて byte 一致を確認すること。8 node だけの手編集はできない。
- {{T:acceptance-work-is-the-lever}} **P1・新規**: 受入 wall の律速は総 work
  (7874.186 秒、`W/48 = 164.046 秒`) であって排他鎖ではない。work の上位は
  `test_s8b_floor_campaign.py` 607.3 秒、`test_autonomous_trial_completeness.py` 589.1 秒、
  `test_s8b_oracle_driver.py` 578.2 秒、`test_trial_registry.py` 515.7 秒、
  `test_t126_pegasus_tools.py` 485.2 秒。**次に当てる手はこの上位 file の共有化である。**
  最長単体 node は 140.0 秒
  (`test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`)
  で、これは分割不能な下界の項として別に扱う。
- {{T:head-gate-callsite-not-covered}} **P3・新規**: 本 wave が足した HEAD 不変 gate は、
  helper の恒真化変異は殺せるが、**呼び出し行そのものを消す変異は殺せない** (安定した checkout では
  どのテストも赤にならないため)。変異 matrix へ SURVIVED 期待として登録済み。
  呼び出し配線を検査する形が要るかを別途裁定する。
