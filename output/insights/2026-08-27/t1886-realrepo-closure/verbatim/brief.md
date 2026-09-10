# 段 1 brief — [T-1886] + [T-1936] real-repo 排他閉包の穴埋めと細分化

## scope

1. **(T-1936)** `real-repo` 排他閉包の穴 3 点を閉じる。
2. **(T-1886)** 閉包が確定した上で、単一 `xdist_group("real-repo")` を衝突クラス単位へ
   細分化し、受入 wall の床を下げる。

1 と 2 は 1 変更単位。2 は 1 の成立を前提にしか正当化されない (D358)。

## 確定済みユーザー裁定

- **D1035** (2026-08-26, ユーザー裁定): 受入 wall の床は**排他閉包の細分化**で下げる。
  個々のテストの短縮は不採用。細分化は排他の意味を弱めない範囲に限る。
- **D532** (2026-08-18): 認めるのは (a) 鎖の短縮 (b) 閉包の細分化 (c) 固定費削減の 3 つだけ。
- **D95**: 実装面の author は Codex。
- 規律: 全体 5 分が絶対上限、直列化と長時間 job は禁止。`check_acceptance_reds.py` は使用停止。

## 親が実測した事実 (この wave で測った。既存 docs を根拠にしていない)

`orchestrator/tests/acceptance_duration_ledger.json` と `REAL_REPO_ACCESS_BY_NODE` を
突き合わせて算出した (`import` は conftest 実体、ledger は現物 JSON)。

| access (parent, ccbench) | node 数 | ledger 合計 |
|---|---|---|
| (read, read)  | 52 | 214.24 s |
| (read, None)  | 28 |  40.92 s |
| (None, read)  |  6 |   3.57 s |
| (read, write) |  3 |   0.00 s |
| (None, write) |  1 |   0.00 s |
| **合計**      | **90** | **258.73 s** |

- **排他鎖の実質全量が共有 (SH) ロックしか取らない node である。** 排他 (EX) を取る writer は
  4 node で ledger 上 0.00 s (3 本は ledger に 0.0 で載り 1 本は不在。growth hold ではない
  `test_slow_*` 系なので、計測走で実際に走ったのか skip されたのかは未確定 — 段 2 で確かめる)。`parent` 資源に write mode の node は 1 つも無い
  (`conftest.py:589-596` の access_groups が `parent` へ `"write"` を割り当てない)。
- 単一 node の最大は 94.00 s
  (`test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment`)。
  同 file だけで 199.71 s = 鎖の 77%。
- 鎖が直列なのは flock ではなく **単一の `xdist_group("real-repo")`**
  (`conftest.py:1752-1757`) が全 real-repo node を 1 worker へ閉じ込めるためである。

## 前提を覆す新事実 (段 4 で再裁定する)

**依頼は実装面を「`tools/run_tests.py` と `orchestrator/tests/conftest.py`」と書いているが、
`tools/run_tests.py` を変更した wave は land できない。**
D838 に従い `tools/dev_wave_land.py:1065-1087` が tested main と tested tip の
`tools/run_tests.py` blob 一致を要求し、不一致は受入拒否になる (現物で確認)。

**目的は run_tests.py を触らずに達成できる。** run_tests.py が real-repo 直列化について
していることは `--dist loadgroup` を渡すことだけ (`tools/run_tests.py:567-571`)。
group 名の決定は `orchestrator/tests/conftest.py`、group→shard の割付は
`tools/acceptance_shards.py:324-390` にあり、後者は blob 束縛されていない
(land/wait のどちらにも `acceptance_shards` の pin が無いことを確認)。
`acceptance_shards.py` は既に**複数 group 名を前提に書かれており**、
`shard_count >= len(group_names)` のとき 1 group = 1 shard へ割り付ける。

## 既存被覆 (性質で archive まで検索した結果) と純増

- D258 / D358 / D600 は「排他機構の変更では受入は速くならない」で 4 波収束している。
  **D358 が却下した 3 案のうち 2 案は本 wave の候補と同型**である:
  「reader を共有ロックで並列化する」「group を file 単位へ割る」。
- D358 の却下理由は 3 本。**本 wave はこれを無視せず、1 本ずつ証拠で退役させる。**
  - (a) 「reader 判定が成立しない (`GIT_OPTIONAL_LOCKS` 無しの `git status` が index lock を書く)」
    → 現在 conftest は少なくとも 1 経路で `GIT_OPTIONAL_LOCKS=0` を渡す (`conftest.py:175`)。
    **全経路の閉包は未確認。これを確認するのが T-1936 の一部である。**
  - (b) 「閉包そのものが未確定」→ まさに T-1936 の 3 穴。
  - (c) 「module fixture の worker 跨ぎ重複支払い」→ receipt memo の prewarm は
    controller 専用で worker では早期 return する (`conftest.py:836-838`)。
    **この理由は既に失効している可能性が高い。**
- D600 の方法論的制約は生きている: **worker span や ledger 合計は因果的な wall 短縮量ではない。**
  細分化の効果を主張するなら A/B が要る。
- **純増**: 上記 (a)(c) の失効可能性を現物で確定させること、閉包 3 穴を閉じること、
  および D1035 の下で初めて許された細分化の実装。

## 変更面 (実アンカー)

| 穴 / 対象 | file:line |
|---|---|
| (i) 無 lock の linked-worktree registry reader | `orchestrator/tests/test_t810_coordinator.py:1104-1150` → `tools/pegasus/t810_coordinator.py:1512-1521`, `:701-712` |
| (ii) 登録外 session fixture (実親 repo へ候補 object を書く) | `orchestrator/tests/test_s8c_preregistration_invariant.py:190-214,361-364`; `orchestrator/tests/test_s8c_preregistration_predicates.py:3873-3913` |
| (ii') 登録外 session fixture (実作業木を走査する) | `orchestrator/tests/test_campaign_import_invariant.py:1073-1097` (consumer `:1078-1101,1218-1253`) |
| (iii) lock key が worktree root 由来 | `orchestrator/tests/conftest.py:989-1007` (`_ACCEPTANCE_DURATION_LEDGER_REPO_ROOT` = `parents[2]`) |
| group 付与 (細分化の主編集面) | `orchestrator/tests/conftest.py:1746-1757` |
| suffix strip / process memo 例外 | `orchestrator/tests/conftest.py:1702-1718` |
| shard 閉包検査 (group 名 `"real-repo"` を exact 要求) | `orchestrator/tests/conftest.py:1670-1699` |
| access 分類 | `orchestrator/tests/conftest.py:576-623` |
| group→shard 割付 (変更不要かを確認する) | `tools/acceptance_shards.py:290-410` |
| lock 取得 | `orchestrator/tests/conftest.py:1065-1130` |

**exact pin 閉包 (`"real-repo"` / `"@real-repo"` を literal で要求する consumer)**:
`orchestrator/tests/test_real_repo_serialization.py:237,1199,1364,1383,1390,1396,1436,1473,1483`、
`orchestrator/tests/test_acceptance_schedule_order.py:767,794,805,820,842,1474,1531`、
`orchestrator/tests/test_growth_test_holds_contract.py:344,368`、
`orchestrator/tests/test_dev_waves_isolation_contract.py:153`、
`orchestrator/tests/real_repo_ratified_memo.py:30-31`、
`docs/decisions.md` D63 / D358 / D532 / D1035 本文。

## 不変条件 (緩めてはならない)

- **排他の意味を弱めない** (D1035)。細分化後も、実 repo/実 submodule へ同時に触れて
  結果が変わりうる node 対は、同一 worker か flock のどちらかで必ず排他される。
- `tools/run_tests.py` を 1 byte も変更しない (D838)。
- `tools/check_acceptance_reds.py` を走らせない。
- テストの削除・skip・selection 縮小で速くしない (D532 却下項、規律 2)。
- 受入全走は免除されない。変異 matrix は baseline 緑必須。

## 親の provisional 裁定 (P。攻撃対象)

- **(P1)** 細分化の単位は「access class × 資源衝突」であり、file 単位ではない。
  SH しか取らない node 同士は並列でよい。
- **(P2)** `REAL_REPO_PROCESS_MEMO_NODES` 4 本は同一 group に残す (同一 process 要求)。
  **EX writer 4 本とは別集合であり (親が実測。両者は互いに素)、EX writer は
  `(read,write)`×3 + `(None,write)`×1 = `test_slow_*` 3 本 +
  `test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding`。
  process memo 4 本はいずれも `(read,read)` かつ growth hold で skip されている。**
- **(P3)** lock key は Git common-dir (`git rev-parse --git-common-dir` の realpath) から導く。
  CCBench 側も同様に共有 submodule の common-dir から導く。
- **(P4)** 登録外 session fixture は、`REAL_REPO_ACCESS_BY_NODE` へ consumer node を登録する
  のではなく、fixture 自身が対応する flock を取る形で閉じる。
  (fixture の生存期間が node protocol より長いため、node lock では覆えない)
- **(P5)** `test_t810_coordinator.py` の registry reader は `parent` を SH で取れば足りる。
  linked-worktree registry の**書き手**は本 suite 内に存在しない。
- **(P6)** D358 の却下理由 (a) と (c) は現時点で失効している。
- **(P7)** 細分化の効果は、real-repo subset に絞った同一機上の A/B (単一 group vs 細分化) で
  示す。受入全走の 2 回反復はしない。
- **(P8)** `tools/acceptance_shards.py` は変更不要。

## 成果物影響 (DW-G05)

- 穴 (i)(ii)(iii) を閉じない場合: 受入の赤/緑が実 repo への同時アクセスで決まりうる。
  前 wave では実際に rc=1 の偽赤が出た。**certified 選択結果を載せる commit の着地可否が、
  測定内容と無関係に変わる。** 台帳 (`docs/worklog.md` の受入欄) にも偽の赤が記録される。
- 細分化しない場合: 受入 wall の床が 5 分上限へ張り付き、shard 分割や計算ノード dispatch が
  恒久的に必要になる。着地までの往復が伸び、campaign の試行台帳の更新頻度が落ちる。

## 成果物の形

- `orchestrator/tests/conftest.py` の変更 (group 付与 / lock key / fixture 登録)
- 上記 3 穴それぞれの負例テスト (穴が開いていれば赤になる)
- 細分化前後の A/B 実測値 1 組
- 変異 matrix、受入 receipt、worklog / decisions fragment

## 並列分割方針

- 段 2: read-only codex plan 子 1 本。
- 段 3: 敵対相談 2 本 (レンズ A = 閉包の完全性と偽緑、レンズ B = D358/D600 との整合と計測の因果性)。
- 段 5: Codex author 1 本 (編集面が conftest に集中しているため分割しない)。
- 段 6: 敵対レビュー 2 本 + fix 1 本。
