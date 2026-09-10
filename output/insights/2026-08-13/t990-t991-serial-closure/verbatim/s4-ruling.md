# 段 4 裁定 — [T-990] / [T-991]

裁定時刻: 2026-08-13 02:58 JST / 親 (dev-wave-t990-t991-serial-closure)
入力: `brief.md`, `parent-findings.md`, `s2a-plan.md`, `s2b-plan.md`, `s3-lensA.md`, `s3-lensB.md`
base: main `5519f783`

---

## R1. 閉包の最終集合 = 22 node 追加 (親の 20 は refuted)

レンズ A の所見 1 (`blocker`) を **real・採用**とする。親が自分で裏取りした。

`test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`
(`:4613`) は `prepare_fn=driver.prepare_cell` を渡し (`:4640`)、`driver.prepare_cell` は
`s1_direct_comparison.prepare_cell` の re-export (`s8b_oracle_driver.py:51`) で、
実共有 submodule を `base_dir` に `patchharness.checkout()` を呼ぶ。
さらに `:4625-4630` で実共有 submodule へ直接 `git rev-parse HEAD` を打つ。
**`conftest.py:242` はこの node を「slow oracle canary」と名指しで除外している。**
worklog entry 512 のレンズ A が指した「共有 submodule common-dir を変更する canary」は
**これ**である。親が系統 2 として先に特定した floor canary 2 件は同型の別件だった。

レンズ A の所見 2 (`must-fix`) も **real・採用**とする。親が裏取りした。
`test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e` (`:4175`) は
`_clone_committed_head_with_ccbench()` (`:971-980`) で実 ROOT を
`git clone --no-hardlinks` の source にし、実共有 submodule も複製する。
**系統 3 を「実 repo を clone する reader」として採用した以上、同じ機序のこれを除外する根拠がない。**
一貫性のため採用する。

最終集合 (22 node):

| 系統 | 件数 | 内容 |
|---|---:|---|
| 1 実 submodule source の fixture reader | 1 | `test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control` |
| 2 実共有 submodule の管理領域 writer | 3 | `test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration`, `::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration`, `test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` |
| 3 実 repo clone の module fixture reader | 17 | `test_codex_reasoning_ab.py` の `benchmark_snapshots` 消費 17 node |
| 4 実 repo clone の直接 reader | 1 | `test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e` |

**正本から node を削らない** (不変条件)。レンズ A 所見 10 の「実資源へ触らない 4 node」
(`conftest.py:177` 群) は over-approximation として残す。削るのは規律 2 に反する方向であり、
subset 条件が逆包含を要求しない根拠として記録するに留める。

## R2. `test_sort_swo_oracle.py` の 8 node は本 wave では追加しない — 新規タスクへ

レンズ A 所見 3 は **real**。ただし**採用しない**。親が裏取りした結果、**支配的な接触が
module 直下の `_ENVIRONMENT = O.resolve_oracle_environment(_CCBENCH)`
(`test_sort_swo_oracle.py:17`) で起きる。これは collection 時の import で全 worker が実行する。**
`REAL_REPO_SERIAL_NODES` は「同一 runner invocation 内で node を同じ loadgroup へ閉じ込める」
機構であり、**import 時接触には原理的に効かない。**

したがって 8 node を正本へ入れると「守った」という偽の安心を生む。
規律 2 は「検査を弱めるな」であって「効かない検査を足せ」ではない。
**新規タスクとして起票する (R7)。**

## R3. 段 2B の「案 A+B (AST 固定点解析)」を**不採用**とする

レンズ B 所見 1 (`blocker`) を **real・採用**。親が一次資料で裏取りした。

- **D335 (2026-08-12、authority: user)**: 「repository の成長 (履歴・commit 数・**file 数**・
  台帳やアーカイブの分量) に比例して実行コストが増える構造のテストは (1) 新設しない」。
- **D311**: 「新しい検査を足す wave は、そのコストが O(1) / O(変更量) / O(履歴) のどれかを
  段 1 brief で宣言する。**O(履歴) なら設計をやり直す。**」

段 2B の設計は 425 file / 15.677 MB を AST parse する。これは file 数比例であり
**ユーザー裁定で新設が禁止されている側**である。既存の同型 (`test_s8b_floor_campaign.py:737-741`
等) は既存負債であって新設許可ではない、というレンズ B の整理も支持する。

加えてレンズ A の反例 2・3 (module alias `driver.prepare_cell`、keyword callable `prepare_fn=` の
伝播) は、AST が追うべき edge を 1 本落とすだけで系統 2 が丸ごと消えることを示した。
**実際に落ちていた** — 段 2B の control は floor module の alias しか撃たないため、
親が採用した R1 の 3 件目 (oracle canary、まさに alias 経路) を検出できない。
**設計が現実の欠陥を取り逃す実証がある以上、採用できない。**

## R4. 新設検査を差し替える (plan v2)

「正本リストと実際の資源接触の対応を機械で確かめる」を、AST なしで満たす 2 本立てとする。

### (i) fixture 閉包の完全性検査 — registry も AST も持たない

**性質:** 「正本に載っている node が使う fixture を共有する node は、すべて正本に載っていること。」
すなわち正本が fixture 共有に関して閉じていることを要求する。

- 実装: 既存 `_collect_xdist_group_report()` (`test_real_repo_serialization.py:360-433`) が返す
  per-item 情報へ fixture 閉包 (`item._fixtureinfo.names_closure` 相当) を足し、
  既存 `test_real_repo_group_collection_exactly_matches_canonical_nodes` (`:567`) へ統合する。
  **新しい subprocess を足さない。**
- **登録簿を持たない。** 「実資源 fixture とは何か」を人が書かないので drift しない。
  正本そのものが seed になる。
- node 識別は既存の `canonical_node` (`:381`) を使う。raw nodeid を使わない
  (レンズ A 所見 7 の受入条件)。
- **コスト: O(collected items)。** repo の file 数・履歴・台帳量に比例しない。
  既に必ず走る collection pass への定数倍の追加であり、D335/D311 に抵触しない。
- **既知の gap (正直に記録する):** どの node も正本に載っていない**全く新しい資源 fixture**は、
  この検査では発見できない。seed が無いためである。本 wave が系統 1・3・4 を seed する。
  この gap は (ii) が call 経路で部分的に埋める。埋まらない残余は R7 で起票する。

### (ii) 実接触の runtime fail-closed guard — 系統 2 用

**性質:** 実共有 submodule を `base_dir` として `patchharness.checkout()` が呼ばれたとき、
呼び出し元の test node が正本に載っていなければ **fail-closed で停止する。**

- AST の伝播完全性問題が**原理的に消える**。実行時の実接触を見るため、alias・keyword callable・
  wrapper forwarding・function-local import のどれを経由しても捕まる。
  レンズ A の反例 2・3 はこの設計には当たらない。
- **コスト: O(1)** (呼出し 1 回あたり path 比較 1 回)。
- pytest 外 (production 実走) では発火しない。conftest が正本 node へ付ける印の有無で判定し、
  印機構が不在なら guard は素通りさせる。**production の受理集合を変えない。**
- 規律 1 (観測者効果) には触れない。CCBench の trace build ではなく Python orchestration の
  fail-closed 検査であり、性能計測ビルドの対象外である。

### 規模

段 2B の 200〜260 行に対し、(i) + (ii) で **80〜120 行**を上限の目安とする。
超えるなら設計を疑う。

## R5. [T-991] — 2 箇所 + env 衛生

レンズ B 所見 9 (`blocker`) を **real・採用**する。ただし**性質の訂正を伴う。**

現行 `repo_tree_util.py:20-27` と `source_digest.py:761-770` は `env=` を渡していないので
**既に親 env をそのまま継承している** (`subprocess.run` の既定)。したがって
`os.environ.copy()` は曝露を**増やさない** — 現状と同じである。
しかし同じ行を触る以上、既存の安全実装 `t810_validator.py:334-355` と同形へ揃えるのが正しい。

**採用する是正 (2 箇所):**

1. `orchestrator/tests/repo_tree_util.py:20-27` `_repo_status()`
2. `orchestrator/campaign/source_digest.py:761-770` `_tracked_status_paths()`

各箇所で、`GIT_DIR` / `GIT_INDEX_FILE` / `GIT_WORK_TREE` / `GIT_COMMON_DIR` / `GIT_OBJECT_DIRECTORY`
/ `GIT_ALTERNATE_OBJECT_DIRECTORIES` を除去し、`GIT_OPTIONAL_LOCKS=0` を設定した env を渡す。
理由コメントを `patchharness.py:71-75` と同形で書く。

**規律 2 の判定 (両レンズ独立に refuted、親も支持):** `GIT_OPTIONAL_LOCKS=0` が抑止するのは
status が検査中に更新した stat cache を on-disk index へ書き戻す副作用だけで、
working tree と index の比較および status 出力を作る in-memory refresh は行われる。
mandatory lock も抑止しない。「汚れているのに clean」条件は生じない。
`source_digest` は status 非 0 を拒否し (`:770-776`)、status の clean/dirty と
full tracked diff hash の整合も検査する (`:846`)。**排他の緩和ではなく、読取専用性の回復である。**

**`silo_ladder_rung1.py:963,2084` は本 wave の scope 外とし、R7 で起票する。**
レンズ A 所見 9 とレンズ B 所見 8 が「production の pinned-clean gate なので黙示的除外は不可」と
指摘したのは **real**。ただし段 2A が示したとおり `_ENV_FORBIDDEN_PREFIXES` に `GIT_` があるため
allowlist 追加では効かず、`_run()` の scrub 後注入という**別形の変更**が要る。
これは env 衛生契約そのものに触るので、独立の裁定と敵対レビューに値する。
**「受入で到達しないから」を除外理由にしない** — 起票して明示する。

## R6. 変異事前登録 (DW-M01 / DW-M08)

本 wave はテスト強化を含むので、**新テストと変更前 HEAD 版の双方へ変異を走らせ、
新テストだけが検出する差分を示す** (DW-M08)。

| # | 変異位置 | 期待 | 単一理由性の確認 |
|---|---|---|---|
| M1 | `conftest.py` 正本から系統 1 の 1 node を削除 | KILLED by (i) | 兄弟 10 node が正本に残るので閉包違反が一意 |
| M2 | 同、系統 3 の 17 node から 1 件削除 | KILLED by (i) | 同 fixture の 16 node が残る |
| M3 | 同、系統 2 の oracle canary を削除 | KILLED by (ii) | runtime guard のみが撃つ。(i) は fixture 非経由なので撃たない |
| M4 | (i) の consumer 集約を「最初の 1 件だけ保存」へ壊す | KILLED by detector control | レンズ A 反例 1 への対策。fan-out 欠落を撃つ |
| M5 | (ii) の guard から実 submodule path 判定を外し常に許可 | KILLED by positive control | guard 無効化が一意に赤 |
| M6 | `repo_tree_util.py` の `GIT_OPTIONAL_LOCKS` 設定を削除 | KILLED by 新設回帰テスト | env capture の一意な差 |
| M7 | `source_digest.py` の同上 | KILLED by 新設回帰テスト | 同 |
| M8 | 同 2 箇所の `GIT_DIR` 等除去を削除 | KILLED by 新設回帰テスト | decoy repo 誘導が一意に赤 |

**M4 と M5 は detector 自身への変異**である。レンズ A の「現行の 3 membership control だけでは
detector の完全性を証明できない」に対する最小の応答であり、
**detector edge を全部撃つ完全な matrix は本 wave では作らない (R7 で起票)。**

## R7. 裁定パッケージ / 新規タスク (実装しない)

親の権限では決めない、またはこの wave の scope を超える real 所見:

1. **[新規] `test_sort_swo_oracle.py` の import 時実資源接触** (レンズ A 所見 3)。
   module 直下で実 ccbench を読むため loadgroup では守れない。8 node。
   import 時接触を扱う別機構が要る。
2. **[新規] `silo_ladder_rung1.py:963,2084` の production status** (レンズ A 所見 9 / レンズ B 所見 8)。
   `_run()` の scrub 後注入という env 衛生契約の変更が要る。
3. **[ユーザー裁定] runner 層の排他 opt-out** (レンズ A 所見 12、`blocker`)。
   `tools/run_tests.py:1866-1870` はユーザー `--dist` 後勝ちを警告だけで通し、
   `--dist` は受入全走の形として許容される (`:85`)。
   **pytest 内の閉包検査が緑でも、runner 層で排他を丸ごと無効化できる。**
   D63 の opt-out を変えるためユーザー裁定対象。親は変更しない。
4. **[新規] detector edge ごとの変異 matrix** (レンズ A 裁定候補 5)。
   fixture fan-out / autouse / param 正規化 / import alias / keyword callable / wrapper
   forwarding / 未登録 sensitive-call を 1 edge ずつ撃つ完全 matrix。
5. **[新規] real-but-disjoint の第三分類** (レンズ A 所見 3 / 裁定候補 4)。
   read path と writer path の交差を機械で検査する形。

## R8. 実装分割 — author 1 本を維持

レンズ B 所見 12 は「6 file + AST 200〜260 行で context 過密」だったが、
**R3 で AST を落としたので前提が変わった。** 編集面は次の 5 file、正味 150 行程度に縮む。

1. `orchestrator/tests/conftest.py` — 22 node 追加、誤ったコメント 2 箇所の是正
2. `orchestrator/tests/test_real_repo_serialization.py` — 独立 golden へ 22 node、(i) の閉包検査
3. `orchestrator/campaign/patchharness.py` — (ii) の runtime guard
4. `orchestrator/tests/repo_tree_util.py` + `orchestrator/campaign/source_digest.py` — R5
5. 回帰テスト 2 本 (env capture)

**`test_codex_reasoning_ab.py` と `tools/codex_reasoning_ab.py` は編集しない** (t983 の lane)。
系統 3 は conftest 側の node 名追加だけで足りることをレンズ B が確認済み。

## R9. 訂正された行番号 (レンズ B 所見 6 / file:line 照合)

- brief の `conftest.py:223-226` (priority) → 正しくは `:233-236`。main 取り込みで 10 行ずれた。
- `s2a-plan.md:7` の `patchharness.py:193-199` は `apply_patch()`。`applied()` は `:234-251`。
- `s2a-plan.md:15` の `s1_direct_comparison.py:527` は `cache_root`。`checkout()` は `:528-529`。
- 段 5 の author はこれらを実コードで再確認してから編集すること。
