---
authority: none
default_effect: no-state-change
---

# 段 1 brief — 受入全走の高速化: t080 e2e の内訳を計算ノードで実測し、支配項を fixture 実装で削る (2026-09-16)

wave `dev-wave-t080-accept-speed` (branch `worktree-dev-wave-t080-accept-speed`、起点 main `08d56628e`)。
親の brief であり可変状態の正本ではない。`(P?)` は親の provisional 裁定で段 3 の攻撃対象。

## 研究前進 (1 行)

受入全走は全 dev-wave の周回時間を決める土台であり、最遅 shard (shard-0) の test span 222.5 秒
(2026-09-16 実測、[T-2617] §結論) は t080 e2e 最長 node にほぼ等しい (D2067)。本 wave はその
node の内訳を計算ノードで実測し、支配項の一つ「実 repo (lustre) からの `output/` 複製」を
session 1 回にする最小差分 (test code のみ) を入れる。完了判定は (a) 内訳表が一次資料付きで残る、
(b) 派生 base の bytes 同一を test が示す、(c) 受入全走 K=3 (post) と同時刻対照の分布を併記した報告。

## ユーザー裁定 (引数、確定済み)

1. 計算ノードで t080 e2e 1 本の内訳 (実 repo からの複製 / git add / 発行時の全件 scan 回数と所要 / 本体) を測る。
2. 支配項を実装で削る。第一候補は「実 repo からの複製を session 1 回にし、key を計算ノード内で派生させる形 (bytes 同一)」。
3. 目標は 5 分ではなく受入全走の実時間の短縮。
4. D2068 の「案 C は符号未確認」は本日の対比較 (温 cache で 9.55 秒 対 9.66 秒) で「効かない」と確定 — 訂正を含める (ユーザー報告値。repo 内に一次資料は無い)。

既存裁定で本 wave を縛るもの: D2068 (案 A whitelist / 案 B alternates は不採用 = 受理集合・観測を変えない)、
D747 (test 削除・skip で速くしない)、D1260 (受入短縮の採否は paired full K=3 中央値、1 走比較を効果と読まない)、
F971 (同時刻対照の分布を併記できない主張は成立しない)、項35 (効果を先に測る)。

## 段 1 の前提実測 (計算ノード bnode050、request 1736.nqsv、2026-09-16 19:26〜19:29 JST)

方法: custom probe を書かず、標準 profiler で既存 test 4 node を直列 1 process で走らせた
(`python3 -B -m cProfile -o b5-run1.prof -m pytest <b5 の 4 node> -p no:cacheprovider --durations=0 -rA`、
`dispatch_compute.py --task generic`)。xdist 無しなので base は process memo で 1 回組まれ、4 test がそれを複製する。
一次資料: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t080-accept-speed/{b5-run1.prof,izdw-abd9211936.o1736}`。

pytest durations (call): known-artifact **132.04 秒** (base 構築を含む) / ccbench-current 31.39 / holdout-artifact 8.33 /
unknownness-layer2 8.26。4 node 合計 181.2 秒。

`_build_t080_stub_free_e2e_repo` = **118.2 秒** (cProfile cumtime、冷 cache) の内訳:

| 項 | 秒 | 割合 | 中身 |
|---|---|---|---|
| 実 repo (lustre) → node の `output/` 複製 `_copy_git_visible_output` | **52.9** | 45% | `copytree` 37.4 + `is_file()`×23,111 (lustre stat) 9.4 + `git ls-files` 3.4 + 祖先集合 2.2 |
| 発行 subprocess (`subprocess.run` 1 回: draft→validate→finalize→verify_receipt→gate_check) | **53.3** | 45% | 子 process 内は未分解。全件 scan は code 読解で最大 5 回 (draft/validate/finalize の `_assert_receipt_does_not_pollute_scan` ×3、`verify_receipt` の live scan、`gate_check` 内 `verify_receipt`)。本体側実測の 1 scan ≈ 5.3 秒から ≈ 26 秒と推定 |
| `_run_git` ×11 (init/config/submodule add/checkout/**add -A**/commit) | 9.5 | 8% | 引数別には分解できない。ユーザー報告の温 cache `add -A` 9.66 秒と整合 |
| `orchestrator/` 複製 + basis file 42 件 | 2.5 | 2% | |

test 1 本あたり: base→test 複製 (`copytree`) **2.85 秒**、`verify_receipt` **4.85 秒/回** (うち `search_repository` 5.3 秒/回、
`_scan_one` 0.95 秒 ×3)。ccbench-current は `verify_receipt` ×5 + git 操作で 31 秒。

**読み方.** (i) 支配項は「lustre 複製」と「発行 subprocess」が同率で、`git add -A` は 8% に過ぎない → 裁定 4 の訂正と整合。
(ii) 受入 (48 worker、5 key を並行 build) では node あたり 200〜222 秒なので、直列 118 秒との差 ≈ 80〜100 秒は並行時の
競合 (lustre 5 本同時読み・local 書き・CPU) と読める — **ただしこれは推定であり、本 wave は競合の内訳を主張しない。**
(iii) F971 の「build 1 回 20〜24 秒」は出所の記載が無く、本日の計算ノード実測 118 秒と一致しない。F1 に従い本日の実測を根拠にする。
(iv) 2 走目 (request 1752.nqsv、bnode052、5 key 12 node を 1 process、file 順なので no-issue key が冷 build) の結果:

| 項 (5 build 合計 / 平均) | 秒 | 備考 |
|---|---|---|
| `_copy_git_visible_output` ×5 | **189.7 / 38** | copytree 137.0 (27.4) + `is_file()` ×115,558 26.9 (5.4) + `git ls-files` 12.7 (2.5) + 祖先集合 10.9 (2.2)。**温 cache でも安定して安くならない** — durations から逆算すると build ごとに 8〜45 秒で振れる (23k file の open/stat の lustre 往復が支配) |
| 発行 subprocess ×4 | **213.8 / 53.4** | run1 と一致。key 依存の項で不変 |
| `_run_git` ×55 (build あたり 11 回) | 47.5 / 9.5 | 一致 |
| `orchestrator/` copytree ×5 | 6.1 / 1.2 | |
| base→test copytree ×11 | 33.1 / 3.0 | 一致 |

durations (call): no-issue key の冷 build を含む `temp_roots` **19.8 秒** (発行なしの build ≈ 複製 + git ≈ 20 秒 — F971 の「20〜24 秒」はこの発行なし build と整合する)、
発行を含む build を背負った 4 node は 111.0 / 116.6 / 123.5 / 123.5 秒、`g7` 49.1 (no-issue の 2 本目、本体のみ)、
`ccbench-current` 31.5、他 3.1〜10.3。12 node 合計 611.9 秒。一次資料 `run2-all-keys.prof` / `izdw-5d7f44e13b.o1752`。

**読み方の更新.** lustre 複製は build あたり 8〜53 秒で振れ、5 key 分の延べは 190 秒 (run2) — session 1 回化で消えるのはこの 4 回分
(延べ 30〜200 秒の worker 時間と、受入では 44 worker と競合する 4 × 23k 件の lustre 往復)。発行 subprocess 53 秒は key 依存で不変。
(v) `output/pegasus-dispatch/` 配下の receipt (`result.json`: hostname / child_rc / pbs_jobid) が job の一次記録。

模擬/実の差: 直列 1 process・n=1 node・xdist 無し。内訳の**比率**の根拠にはするが、受入 wall の予測値には使わない。
自己 hash・pin・参照は測っていない (F29 の射程外)。

## (P) provisional 裁定 — 段 3 の攻撃対象

- **(P1)** 受入の critical path は「key の base 構築の完了待ち + 複製 + 本体」であり、lustre 複製を session 1 回にすると
  並行 build 5 本の lustre 読み出し (各 640 MB + 23k stat) が 1 本になり、競合分が縮む。**非競合の critical path
  (proto 53 + 派生 3 + add 9.5 + issue 53 ≈ 118 秒) は縮まない**ので、wall 短縮の符号は K=3 + 対照でしか言えない。
- **(P2)** 派生の分割点は「`orchestrator/`・git 可視 `output/`・basis file・`submodule add` まで (key 非依存 = proto)」と
  「`distinct_basis_blob` の descriptor 変更 → `git add -A` → commit → 発行 (key 依存)」。proto は `git init` 済み・index 未作成。
  この分割なら派生 base の working tree bytes と HEAD tree OID・receipt document は現行 build と一致する (bytes 同一)。
- **(P3)** lustre 複製そのものの高速化 (`is_file()` 9.4 秒を `git ls-files -s` の mode 判定へ、`copytree` 37.4 秒の並列化) は
  bytes 同一・意味不変で critical path を直接削る候補だが、**本 wave の第一候補ではない**。段 2/3 で「同時に入れる価値」を
  評価し、段 4 で採否を決める (scope 拡大の既定は不採用、DW-G05)。
- **(P4)** 効果の採否基準: D1260 は同族の配線に「paired K=3 中央値 10% 未満なら採用しない」を課した。本 wave は
  ユーザー裁定 2 で実装を指示されており、bytes 同一・正しさ不変・lustre 読み出し 5→1 の構造効果は test で示せる。
  wall 効果は K=3 (post) + 同時刻対照で分布を併記し、10% 基準の充足/不充足を事実として書く。**不充足でも成果物を捨てず、
  land の可否は段 4 で 2 レンズの所見を見て親が決める** (裁定へ返さない)。
- **(P5)** 発行 subprocess の scan 回数 (最大 5) と `search_repository` の費用は production code (正しさゲート) に属し、
  本 wave では触らない。fixture が写す `output/` の集合も変えない (D2068 A)。

## scope

- **S1 (完了・追記中)** 計算ノードの内訳実測を一次資料付きで insight に残す。
- **S2 (本体)** `_T080SharedBases` / `_t080_stub_free_e2e_repo` / `_build_t080_stub_free_e2e_repo` を、session 1 回の proto
  構築 + key ごとの node 内派生に分ける。xdist session 共有 (lock 規約) と単独走の process memo の両経路で動く。
- **S3 (test)** 派生 base の bytes 同一を示す正例 (現行 build 経路と派生経路の HEAD tree OID・working tree・receipt document 一致)
  と、proto の欠損/破損時に再構築する負例。**受入 5 分上限を悪化させない粒度** (実 repo 全件を 2 回組む test は置かない —
  小さな合成 source root で bytes 同一を示す設計を段 2 で検討)。
- **S4 (docs)** D2068 の erratum (案 C の符号は「効かない」で確定、`git add -A` は build の 8%)、新 D (session 1 回複製の採用理由)、
  worklog fragment、insight README。
- **S5 (計測)** 受入全走 K=3 (post、条件を割って別 node へ同時投入) + 同時刻の他 session 受入 junit を対照に分布を併記。
- **scope 外**: production scan の最適化・発行時 scan 回数の削減 (P5)、test 削除/skip (D747)、案 A/B (D2068)、
  `pre`/`disp` 区間 ([T-2617]/[T-2616] 所有)、hardlink/reflink による複製 (test が破壊的に変異するため共有実体は不可)。

## 不変条件

- I1 bytes 同一: 派生 base の working tree bytes・HEAD tree OID・receipt document が現行 `_build_t080_stub_free_e2e_repo` と一致。
- I2 受理集合不変: fixture が写す `output/` は現行どおり git 可視の全件 (whitelist 化しない)。
- I3 実 repo の object store を fixture に見せない (alternates 禁止)。
- I4 production builder/verifier/gate を stub しない。発行 subprocess は key ごとに現行どおり走る。
- I5 test は独立実体を受け取る。proto は読み取り専用で、派生 copy は key ごと、test ごとの copy は現行どおり。
- I6 実 output 境界の fail-closed (`_assert_t080_temp_root_outside_real_output`) は proto にも掛かる。
- I7 xdist の共有 lock 規約 (最後の退出者が削除、失敗 builder の残骸を完成品にしない) を proto にも適用。
- I8 受入 5 分上限を悪化させない (新 test は軽量)。

## 変更面 (実アンカー、`orchestrator/tests/test_s8b_oracle_driver.py`)

| 行 | 対象 |
|---|---|
| 794 | `_git_visible_output_paths` |
| 827–875 | `_copy_git_visible_output` |
| 896–940 | `_T080SharedBases` (`get` の per-key lock と builder) |
| 943–961 | `_t080_join_shared_bases` |
| 964–1008 | `_t080_stub_free_e2e_repo` (process memo 経路 + test ごとの copytree) |
| 1047–1290 | 既存 shared-base test 群 (builder 呼び出し回数・独立性・lock・cleanup) — 期待値の更新要否を段 2 で列挙 |
| 1326 | AST で `_t080_stub_free_e2e_repo` 呼び出しを数える検査 |
| 1364–1460 | `_build_t080_stub_free_e2e_repo` 前半 (複製〜basis commit) = 分割点 |
| 1460–1660 | 同 後半 (発行 subprocess) = key 依存、変更しない |

関連 (変更しない): `orchestrator/tests/conftest.py` の real-repo access map (t080 e2e は対象外)、
`orchestrator/campaign/s8b_holdout_freeze.py:370,592` (scan)、`orchestrator/campaign/t080_freeze_migration.py:1889,1985,2023,2048,2191`
(発行時 scan の呼び出し点)。

## 既存被覆と純増

被覆: D2067 (対象の再確定)、D2068 (A/B/C 不採用)、D700/F485 (opt-in 化の事故)、D747、D1260、F971、
[T-2617]/[T-2616] (pre/disp)、worklog 1493 (worker 間共有化、効果不検出)。
純増: (a) 計算ノードでの t080 e2e 内訳の実測、(b) lustre 複製の session 1 回化と node 内派生の実装、(c) D2068 の訂正。

## 成果物と分割

- 段 2: read-only codex plan 1 本 (file:line 粒度、proto/派生の分割点、lock 規約、test 設計、既存 test の期待値更新)。
- 段 3: 敵対レンズ A (検出力・受理集合・bytes 同一の検証設計・I1〜I7) / レンズ B (費用モデル・xdist 並行時の critical path・
  失敗時の回復・受入 5 分上限・P3 の同時採用の価値)。
- 段 4: 裁定・plan v2・変異事前登録。
- 段 5: Codex author 1 本 (fixture + test)。段 6: レビュー 2 本 + fix + 変異 matrix + 受入 (K=3 + 対照)。
- 段 7: insight README、spool fragment (worklog 1、decisions 2 = D2068 erratum + 新 D)。

受入・実測環境: 受入は `tools/dev_wave_wait.py acceptance` (計算ノード 3 shard)。内訳実測は `dispatch_compute.py --task generic`
(機体固有情報は `docs/pegasus-runbook.md`)。
