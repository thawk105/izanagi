# 段 4 裁定 — dev-wave [T-989] / [T-932]

**この文書が段 5 以降の最上位の正本である。** brief・追補・plan・consult より優先する。
食い違うときは本書に従う。

- wave: `dev-wave-t989-t932-snapshot-cost`
- branch tip: `518a87e1` (local main を ff-only 取込済み)
- 裁定: 2026-08-16 14:58 JST — **確定**

---

## 0. 段 3 所見の real / refuted 一覧

親が実測で裁いた。根拠は `measurements.md` の該当節。

| 所見 | 判定 | 採否 | 根拠 |
|---|---|---|---|
| sol 1 `.git/shallow` が seal と verifier の盲点 | **real** | **採用 (scope 内)** | `shallow` の出現数 = 0、`closure_paths` は 6 種のみ |
| sol 2 `remote.pushDefault` と dangling symlink が検出を逃れる | **real** | **scope 外 → 裁定パッケージ** | 既存の穴で、転送方式と独立 |
| sol 3 submodule init 欠落が受理される | **half real** | 変異は殺される / fail-open は起票 | reason 0 件だが `:1155` の assert が false |
| sol 4 build→seal 削除変異が生存する | **refuted** | — | seal 削除は reflog reason で赤 (3 本を保留しない前提) |
| sol 5 measurement 11 件保留で共有 fixture の固定検査も消える | **real** | **採用 (提示の是正)** | collateral の記載不足 |
| sol 6 `copytree` 系 fixture が探索 primitive から漏れている | **real** | **scope 外 → 起票** | 別 file 群 |
| sol 7 `pack-objects` は source サイズに弱く比例する | **real** | **採用 (主張の縮小)** | 0.32s vs 0.065s (6.1 倍の object に対し 4.8 倍) |
| luna 1 wall 短縮は保証されない / worker 上限は 32 | **real** | **採用 (主張の縮小)** | `tools/run_tests.py:62` `_NPROC_CAP = 32` |
| luna 2 測定が D357 を満たさない | **real** | **採用 (再測定済み)** | 静かな窓で撮り直した |
| luna 3 derive は prepared 経路でだけ定数 | **real** | **採用 (記述の限定)** | — |
| luna 4 submodule 帰属の言い直し | **real** | **採用 (記述の是正)** | pack 経路で submodule は全体の約 41% |
| luna 5 snapshot 3 本の全 hold は規律 2 と両立しない / 部分 hold は無意味 | **real** | **採用 (保留しない)** | 1 本でも走れば fixture は構築される |
| luna 6 陳腐化するのは 14 件で digest の動き方が異なる | **real** | **採用** | `_CLONE_REASON` 14 行 |
| luna 7 47 件では閉じない | **real** | **採用 (完了と記録しない)** | 5 file が両 registry の外 |

---

## 1. S1 [T-989] — 転送方式

**採用 = 方式 B**: `git init` → `git pack-objects --revs --stdout` →
`git index-pack --stdin --fix-thin` → `git update-ref refs/heads/<BRANCH> <BASE_COMMIT>`。
`plan-s1b.md` の「採用: 方式 B」「exact な順序」に従う。

方式 A (`git fetch` に生 SHA) は不採用。性能では決められない (3 走の幅が重なる) が、
upload-pack が「到達可能な生 SHA の want」を受ける挙動に依存し、その rc=0 の一意な理由を
親も子も確定できていない。B はその依存を構造的に持たない。

## 2. S1 の不変条件

`brief-addendum-2.md` の不変条件 1' を採用する。加えて実測済みの事実:

- 現行と新方式で `_one_git_closure_reasons` の reason **0 件**、object **8,209**、
  commit **834**、`.git` **35,132 KB**、`commit_graph.present=false`、残留 pseudo ref **0 件**
  — 9 走で一致 (`measurements.md`)。
- literal pin (`CASE_HASHES` / `TRACKED_HASHES` / `ARTIFACT_HASHES` / `CASE_NUMSTAT`) は
  1 つも変えない。
- `oracle["manifest_sha256"]` と `submodule_manifest_sha256` は**実行時導出値で literal
  比較されない**。既定 `_snapshot_spec` の key は branch/case/forbidden/hashes/head/modes/
  numstat/tracked_paths/untracked の 9 個だけである (実測)。
  **これを「凍結 pin が壊れる」根拠にしてはならない。**

## 3. S1 の実装内容 (この 3 件だけ。増やさない)

### 3-1. `_build_snapshot_base` の転送を方式 B へ置換する

`plan-s1b.md` の「採用: 方式 B」1〜4 と「exact な順序」1〜7 のとおり。

### 3-2. `.git/shallow` を closure 検査へ追加する (sol 所見 1)

`_one_git_closure_reasons` の `closure_paths` (`tools/codex_reasoning_ab.py:1347-1356`) へ
`"shallow": git_dir / "shallow"` を追加する。既存 6 種と同じ扱い
(存在して非空なら reason) にする。

**これは受理集合を縮小する変更である。** DW-M01 に従い、
**過剰拒否を検出する正例を必ず登録する** — すなわち「shallow が無い正常な snapshot が
今までどおり reason 0 件で通る」ことを assert する node を用意する
(既存の `test_snapshot_submodule_object_store_is_recursive` が実質これに当たるので、
新設が要るかは実装子が判断し、要らないなら理由を書け)。
併せて「shallow を置いたら reason が出る」負例を新設する。

**採用理由 (親の判断として明記する):** これは本 wave が作った穴ではない。
しかし本 wave の中心的な主張が「object 閉包が BASE 閉包と同一 (834/8,209)」であり、
`.git/shallow` はその主張を**機械検査を通り抜けたまま偽にできる唯一の経路**である
(HEAD・working tree hash・ref を変えずに commit 数だけ減らせる)。
1 行の fail-closed 追加で主張が機械強制になるので、scope に入れる。

### 3-3. `plan-s1b.md` のテスト 2 件

1. **新設** `test_build_snapshot_base_pack_transfers_unreferenced_base_closure_only`
   — ref が指さない commit の閉包だけが転送されることを検査し、`_run` の argv spy で
   `pack-objects` / `index-pack` の存在と `clone` / `fetch` の不在を固定する。
   **`.git/shallow` / `FETCH_HEAD` / `packed-refs` / `remote.*` の不在も assert する。**
2. **拡張** `test_object_info_derived_caches_are_removed_for_root_and_submodule`
   — 有効な commit-graph を root と submodule に作ってから `_seal_git_object_closure` を呼び、
   両方の `objects/info` が空になることを assert する
   (`_remove_git_object_info_caches` の**呼出行**を production から検査するため)。

**object 数 834 / 8,209 を literal として焼き込まない。** 受理条件は object ID 集合の一致とする。

## 4. S1 の変異事前登録 (DW-M01 / DW-M08)

`plan-s1b.md` が挙げた期待 kill node のうち 4 本
(`test_forbidden_commits_are_unreachable_in_both_cases` /
`test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure` /
`test_m3_symbolic_head_is_required` / `test_parent_numstat_controls_remain_pinned`) は
**保留 = 既定 skip** なので使えない (`brief-addendum-4.md`)。親が再照準した。

| # | 壊してはいけない性質 | production 変異 | 期待赤 nodeid | 単一理由性の実測 |
|---|---|---|---|---|
| M1 | repo 全履歴を転送しない | B ブロックを `git clone --no-hardlinks` へ戻す | 新設 node | argv spy が唯一の検出者 |
| M2 | BASE の exact object set だけを転送する | `pack-objects` の stdin を `INTEGRATED_COMMIT` へ変える | 新設 node | 未確認 — 段 6 で確認 |
| M3 | expected branch と symbolic HEAD を保つ | `update-ref` を別 ref へ向ける | 新設 node | 未確認 — 段 6 で確認 |
| M4 | submodule を実際に初期化する | `_init_submodules_from_local_source(repo, base)` の呼出を削る | `test_snapshot_submodule_object_store_is_recursive` | **実測済み**: closure reason は 0 件のまま、`:1155` の `assert submodules` だけが赤 = 単一理由 |
| M5 | cache cleanup が production から到達可能 | `_remove_git_object_info_caches(git_dir)` の呼出だけを削る | 拡張後の `test_object_info_derived_caches_are_removed_for_root_and_submodule` | 未確認 — 段 6 で確認 |
| M6 | seal が production から到達可能 | `_seal_git_object_closure(base)` の呼出を削る | `test_snapshot_submodule_object_store_is_recursive` | **実測済み**: reason は `.: reflog closure is not empty` の 1 件だけ = 単一理由 |
| M7 | shallow を拒否する | 3-2 で追加した `"shallow"` entry を削る | 3-2 の負例 node | 未確認 — 段 6 で確認 |

**期待 node は完全集合**であり、段 6 の fix 後に実観測から再導出する (DW-M08、F33)。
M2 / M3 / M5 / M7 の単一理由性は段 6 で親がコードと実走で確認し、
確認できない変異は登録から外して実効 gate へ再照準する (DW-M01、F28)。

## 5. S2 [T-932] — 保留する node の確定

### 5-1. snapshot 系 3 本は **保留しない**

`test_snapshot_submodule_object_store_is_recursive` /
`test_git_answer_object_reinjection_is_rejected` /
`test_supervisor_launches_pair_and_scrubs_git_environment`。

理由:

1. **規律 2。** この 3 本を保留すると 17 consumer 全てが skip され、
   clean `verify_snapshot` を呼ぶ唯一の既定 node が消える。失うのは
   `_one_git_closure_reasons` の reason 集合 (refs / remote / reflog / replace refs /
   alternates / http-alternates / grafts / packed-refs / pseudo refs / commit-graph verify /
   fsck) 全部と、forbidden object 検査、pair ordering / Git 環境 scrub / sandbox 検査である。
   親が実測したとおり、**M4 と M6 の変異はこの node だけが殺している。**
2. **費用の帰属が違う。** 提示された `output_artifacts` 軸の実測は
   `prepare_cases(golden derive)` = **0.13〜0.21 秒**であり、35 秒を占めるのは
   S1 が消す `commits` 軸である。0.2 秒の軸のために上記の防壁を消す取引は成立しない。
3. **部分保留は無意味** (luna 所見 5)。1 本でも走れば module fixture は丸ごと構築される。

`output_artifacts` 軸の残余 (session corpus の `rglob`) は消えない。これは
**repo 外の成長**であり [T-886] (ユーザー裁定待ち) の領域なので、本 wave では触らない。

### 5-2. 残り 27 件を登録する

`plan-s2.md` の `hold` 30 件から上記 3 件を除いた 27 件。
D335 と先例 (worklog 483 = 29 件を登録 + 提示) に従い、
正しさゲート該当は**登録したうえで一覧をユーザーへ提示する**。事前承認待ちにはしない。

**sol 所見 5 の是正を必須とする。** module fixture を共有する群
(`test_s1_measurement_freeze.py` の 11 件、`test_s1_known_axes_freeze.py` の 9 件) には、
`collateral_note` へ **「共有 module fixture が起動しなくなるため、各 test body に無い
fixture 内の固定検査 (full SHA 形式・`CURRENT_PIN` prefix・独立 golden・
`K.verify_document`) も同時に止まる」**旨を書く。
個別 test body の説明だけで済ませない。

### 5-3. (P5) 陳腐化する理由文 — 訂正する

`_CLONE_REASON` を持つ **14 行** (16 ではない) の `hold_axis` を
`commits` → `output_artifacts` へ、reason を snapshot corpus 由来の文へ変える。
**解除はしない** (先行 wave の合意 `dev-wave-growth-tests.md:112`)。

luna 所見 6 の分析を実装の指針とする: reason だけの訂正では key digest / row digest は動かず
`test_hold_inventory.py` の reason 完全 oracle と human 出力だけが赤になる。
axis も変えるなら row digest が動く。行追加で count / key digest / held-module literal も動く。
**実装子はこれらを全部更新すること。検査を外して緑にしてはならない。**

## 6. scope 外だが real — 裁定パッケージ / 起票へ回す

本 wave では実装しない (DW-S04)。

1. **`verify_snapshot` の submodule fail-open** (sol 所見 3)。既定 `_snapshot_spec` が
   `submodule_manifest_sha256` を pin しないため、submodule 未初期化の snapshot が
   reason 0 件で受理される。**本 wave が作った穴ではない。**
2. **`remote.pushDefault` と dangling symlink の抜け道** (sol 所見 2)。
   `git remote` は named remote しか列挙せず、cleanup / verifier は `exists()` / `is_file()` を
   使うので dangling symlink を不在扱いする。
3. **母集合の残り** (luna 所見 7 / sol 所見 6 / `brief-addendum-1.md`)。
   `test_s8b_ratified_verify.py` / `test_check_docs.py::test_real_repo_clean` /
   `test_s8c_preregistration_invariant.py` / `test_silo_ladder_rung1_evidence.py` /
   `test_silo_ladder_rung1_driver.py` は両 registry の外。
   さらに `shutil.copytree` で実 repo subtree を複製する fixture
   (`test_dev_waves_checker.py` / `test_codex_agents.py`) が探索 primitive から漏れている。
   silo 2 件は先行 wave が t816 land 後の再測定へ**意図的に繰り越した**ので、
   回収前に必ず worklog / archive を確認する。
   **本 wave の 27 件を「全成長比例テストの完了」と記録してはならない。**

## 7. 測定と主張の範囲 (D357)

**主張してよいこと:**

- `_build_snapshot_base` および fixture 全列の前後比較を、
  **静かな窓 (自分の他 job ゼロ) の 3 走中央値**で述べる。前値は確定済み
  (fixture 全列 **43.72 s**、`_build_snapshot_base` **35.02 s**)。
- ノイズ床は静かな窓でも中央値比 −5% / +30% ある。**10% 未満の差は「変化なし」**とする。
- 「**33.64 秒の支配的な線形項 (`repack -Ad` の全 object 再圧縮) を除去した**」。

**主張してはいけないこと:**

- 「commit 数から完全に切り離した」— `pack-objects` は source の object 数に弱く比例する
  (実測 0.32s vs 0.065s)。正しくは「**残る比例項は係数が約 100 分の 1**」。
- 「受入 wall が N 秒短縮された」— 別 worker が最長なら wall は動かない (luna 所見 1)。
  worker 上限は 32 (`tools/run_tests.py:62`)。
  受入 wall は**取得できた走行数を明記して併記**し、D357 の 3 走中央値に満たなければ
  「満たない」と明記する。改善の主張は fixture 側に置く。
- 「derive は定数」— `prepared_golden` を渡す fixture 経路でだけ base 部分が定数である
  (luna 所見 3)。
- 「submodule が支配項」— pack 経路で submodule seal は全体の約 41% だが絶対値は約 2 秒で、
  izanagi の成長に依存しない固定費である (luna 所見 4)。
