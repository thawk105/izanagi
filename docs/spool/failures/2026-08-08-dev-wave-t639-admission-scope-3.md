---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t639-admission-scope
seq: 3
---

## 新規

### {{F:mutation-expected-nodes-overdetermined}}. 防壁中核の変異が過剰決定になると分かっていながら単一 node で本走し、変異 1 走を空費した [手順漏れ]

- 事象: 段 6 のレビューが「M1〜M10 の `expected_nodes` は単一 node では成立せず、
  registry 中核を戻す変異は多数の既存テストを同時に赤くする」と静的に指摘し、親はこれを real と
  裁定した。にもかかわらず本走 v1 は段 4 の単一 node 登録のまま投入し、10 本中 7 本が
  `MISMATCH` になった。**生存はゼロで実装の欠陥は無く**、観測 node から v2 を作って再走すると
  10/10 `KILLED` になった。空費は変異 1 走 (計算ノード 11 job)。
- 根本原因: `mutation_harness.py` の `KILLED` は `failed_nodes == expected_nodes` の**集合完全一致**
  であり、部分一致を `KILLED` にしない。loader の path 条件や `_pegasus_admission_entry` の分岐など
  **registry 中核**を戻す変異は、literal golden・inventory 同期・sanctioned 導出・
  registry failure matrix を同時に落とす。親は採用した所見を spec へ反映せず、
  「事前登録は段 4 のまま動かさない」ことを優先した。
- 恒久対応: `DW-M01` の事前登録では、**変異位置**を段 4 で凍結し、`expected_nodes` は
  「その変異が到達する層の全 consumer」を静的に列挙して書く。単一 node で足りるのは、
  変異点の下流に consumer が 1 つしかないと**コードで確認できた**ときだけとする。
  レビューが `expected_nodes` の過剰決定を指摘したら、本走前に spec を更新する
  (`DW-M02` の erratum は事後の受け皿であって、既知の指摘を通す口実にしない)。
- 再発検知: harness の `matches_expectation` が false で残る。本件は v1 台帳
  (`mutation-ledger-v1.json`) を erratum として insights に残し、v2 と併置した。
  **恒久対応の `DW-M01` への明文化は、`docs/dev-wave/**` の byte hard ceiling (25,200) に対する
  空きが 1 文にも足りない (本 wave の land 直前で 15 bytes) ため入らない。** F146 / F161 と同じく
  本エントリを恒久対応の所在とし、空きが出たときに `DW-M01` へ 1 文で統合する。

## 再発

### F114

- **再発: 2026-08-08 ([T-639])。** 受入全走が PBS の 30 分 elapse 上限で SIGKILL されたあと、
  wave worktree の `.git/worktrees/<name>/index.lock` が **0 byte のまま残り**、以後の
  `git add` / `git commit --dry-run` がすべて `fatal: Unable to create ... index.lock` で止まった。
  **新しい情報は原因が並行 git 操作ではなく scheduler による強制終了**であること — 台帳既載の
  「全走中に編集・stage しない」規律を守っていても発生する。
  復旧は git 自身が案内する手順どおりで、`fuser` で holder 不在と、
  生きている `codex exec` が別 wave のものであることを確認してから lock を削除した。
  恒久対応は追加していない (受入全走の walltime 側の問題として worklog へ起票した)。

### F57

- **再発: 2026-08-08 ([T-639] 受入全走)。** 全走 (7238 passed / 2 failed / 20 skipped) で
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight` と
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が**同時に**落ち、いずれも `git cat-file timeout` (`ruleops: git-timeout` / `PreregistrationError`)
  だった。2 node の単独再走は 2 passed / 85.06 秒で再現しない。本 wave の差分は admission
  (loader / hook / registry / docs) で当該コードへ到達せず、`DW-O18` により帰属しない。
  **新しい情報は 2 点。** (i) 同一走行で**独立した 2 node が同じ producer (git) の
  wall-clock gate で同時に落ちた**こと。従来の再発はいずれも 1 走 1 node だった。
  (ii) 親は codex 子を 1 本も起動していないが、**別 branch の並行 wave 2 本が同じ repo の
  worktree で稼働中**だった。「親の子 process との競合」ではなく
  **共有 checkout・共有ファイルシステム上の並行 wave との競合**が候補になる。
  恒久対応は F57 既載の失敗 artifact 保存による原因分離のままで、本 wave では変えない。

- **再発: 2026-08-08 ([T-639] 受入全走 1 回目、別型)。** 同 wave の 1 回目の全走は
  テストの赤ではなく **PBS の 30 分 elapse 上限**で SIGKILL された (request `895704`、
  進捗 99% 地点、`Elapse: 1809S`)。`tools/run_tests.py` は `dispatch_compute` の
  既定 walltime (`00:30:00`) を固定で使い、上限を渡す経路を持たない。2 回目は
  1477 秒 (24 分 37 秒) で完走しており、**全走の所要が既定枠の 8 割を超えて
  共有ノードの混み具合次第で上限に届く**状態にある。恒久対応は取っていない
  (walltime の plumbing は本 wave の scope 外)。再発検知 = 受入全走の rc=16 と
  `Exceeded per-req elapse time limit`。
