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
- 変異 spec の期待 node に `@<group>` 接尾辞を書いて harness が rc=2 で止まった。接尾辞は
  並列走行でのみ合成され、実在検査が使う素の collection には現れない。直列走行 (`-n 0`) にして
  接尾辞なしで登録し直した。先例 (2026-08-24 の同じ鎖の wave) も接尾辞なしだった。

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
