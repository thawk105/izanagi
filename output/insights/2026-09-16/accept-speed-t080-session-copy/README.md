---
authority: none
default_effect: no-state-change
---

# 受入全走の高速化 — t080 e2e の内訳を計算ノードで実測し、実 repo 複製を xdist session 1 回の proto にした (2026-09-16)

wave `dev-wave-t080-accept-speed` (branch `worktree-dev-wave-t080-accept-speed`)。依頼は
「計算ノードで t080 e2e 1 本の内訳 (実 repo からの複製 / git add / 発行時の全件 scan 回数と所要 / 本体) を測り、
支配項を実装で削る。第一候補は実 repo からの複製を session 1 回にし key を計算ノード内で派生させる形 (bytes 同一)。
目標は 5 分ではなく受入全走の実時間の短縮。D2068 の『案 C は符号未確認』は本日の対比較 (温 cache で 9.55 秒対 9.66 秒) で
『効かない』と確定したので訂正を含める」。

## 結論 (最初に読む)

1. **内訳 (計算ノード bnode050、直列 1 process、冷 cache): base 構築 118.2 秒 = 実 repo (lustre) → node の `output/` 複製 52.9 秒 (45%) + 発行 subprocess 53.3 秒 (45%) + git 操作 11 回 9.5 秒 (8%) + その他 2.5 秒。** test 1 本あたりは base→test 複製 2.85 秒、`verify_receipt` 1 回 ≈ 4.9 秒。発行経路の全件 scan は正常 active-valid 経路で **13 回** (draft 3 / validate 3 / finalize 4 / verify 1 / gate 2)。
2. **実装した: key 非依存の準備 (proto) を xdist session parent に 1 回だけ組み、key ごとの base は proto の `.git` 込み node 内複製から派生させる** (`orchestrator/tests/test_s8b_oracle_driver.py` のみ、commit `bdfa49950`)。実 corpus の probe で default / distinct の両 key について basis commit・basis tree・発行後 HEAD tree・receipt raw/document・working tree が旧経路と**完全一致** (bytes 同一、§4)。変異 matrix は負例 9 件すべて KILLED (期待 node と観測 node が完全一致)、等価変異 1 件 SURVIVED。
3. **非競合の critical path は縮まらない** (同一 node の xdist `-n 12` 焦点走: 旧 136.7 / 136.3 秒 対 新 133.3 / 133.1 / 150.2 秒)。**受入の同時刻ペア 3 組では最遅 shard が −10.7% / −1.9% / −5.7% (中央値 −5.7%)** で、D357 / D1260 の 10% 基準の内側 (§5)。
4. **fixture 変更は land しない (段 4 裁定 §6)。** 実装 commit `bdfa49950` は branch `impl-dev-wave-t080-accept-speed` に保存し、採用の可否を裁定パッケージ (§7-5) として返す。docs だけを land する。
5. D2068 の訂正: 案 C (index 化) は「効かない」で確定。本 wave の実測でも git 操作は build の 8% で支配項ではない。

## 1. 一次資料

| 区分 | 所在 |
|---|---|
| job dir (repo 外、profile・pytest 出力・受領証・spec・probe 結果・運転 script) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t080-accept-speed/` |
| 段 1 brief | `stage1-brief.md` (訂正前の記述を含む。訂正は `stage4-ruling.md` §1) |
| 段 2 plan / 段 3 レンズ A・B / 段 5 author / 段 6 レビュー A・B | `verbatim/` (§8 に原文 hash) |
| 段 4 裁定 | `stage4-ruling.md` |
| 計測台帳 | `measurements.md` |
| 変異 spec (実走と同一 bytes) と台帳 | `mutation-spec-probe.json` / `mutation-spec-probe2.json` / `mutation-spec-final.json`、`mutation-probe-ledger.json` / `mutation-probe2-ledger.json` / `mutation-final-ledger.json` |
| probe 結果 (実 corpus I1) | `probe-real-result.json` |
| 受入成果物 (repo 外) | `/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/shard-N/{report.json,junit.xml}` (session ID は `measurements.md`) |

probe 本体 `tools/t080_proto_equivalence_probe.py` (200 行、Codex `role=author` が作成) は repo へ commit せず job dir に保全した
(sha256 `b57a80433f128d149ca6bf208b90c09343f6b06997100a27f67d23af02806b9d`、8008 bytes)。

## 2. 内訳の実測 (段 1)

方法: custom probe を書かず、標準 profiler で既存 test を直列 1 process で走らせた
(`python3 -B -m cProfile -o <out>.prof -m pytest <node…> -p no:cacheprovider --durations=0 -rA`、`dispatch_compute.py --task generic`)。
測った checkout は wave worktree (main `08d56628e` 時点、実装前)。

### 2-1. run1 (bnode050、request 1736、b5 の 4 node)

| 項 | 秒 | 割合 |
|---|---|---|
| 実 repo (lustre) → node の `output/` 複製 (`_copy_git_visible_output`) | **52.9** | 45% (copytree 37.4 + `is_file()` ×23,111 の lustre stat 9.4 + `git ls-files` 3.4 + 祖先集合 2.2) |
| 発行 subprocess (draft→validate→finalize→verify_receipt→gate_check、13 scan) | **53.3** | 45% (子 process 内は未分解) |
| `_run_git` ×11 (init / config ×4 / submodule add / checkout / add -A / commit) | 9.5 | 8% |
| `orchestrator/` 複製 + basis file 42 件 | 2.5 | 2% |

durations: known-artifact 132.0 (base 構築込み) / ccbench-current 31.4 (`verify_receipt` ×5) / holdout-artifact 8.3 / unknownness-layer2 8.3。
test 1 本: base→test 複製 2.85 秒、`verify_receipt` 10 回合計 48.5 秒 (`search_repository` 9 回合計 47.6 秒、verify 外の呼び出しを含む)。

### 2-2. run2 (bnode052、request 1752、5 key 12 node)

複製 5 回合計 189.7 秒 (平均 38 秒; copytree 137.0 + stat 26.9 + ls-files 12.7 + 祖先 10.9)、発行 4 回合計 213.8 秒 (平均 53.4)、git 55 回 47.5 秒、base→test 複製 11 回 33.1 秒 (平均 3.0)。
12 node 合計 611.9 秒。**温 cache の効果は反復測定まで保留** (5 回平均 38 秒は冷 1 回 52.9 秒と同じ桁)。
`temp_roots` 19.8 秒は境界検査 (build しない)、no-issue key の初回 build は g7 49.1 秒に含まれる。

### 2-3. 受入 (48 worker) との差

受入 pre の shard-0 では発行あり e2e 10 node が 212〜265 秒 (§5)。直列 118 秒との差は測定範囲差・scheduler 待ち・lock 待ち・準備/発行/本体の競合が混在し、分解できない (段 4 裁定 §1 f)。

## 3. 設計 (段 4 裁定 §4 plan v2)

- `_build_t080_stub_free_e2e_repo` を `_build_t080_e2e_proto(parent)` (init / config / `orchestrator/` と git 可視 `output/` の複製 / basis file / submodule add・pin checkout) と `_finish_t080_stub_free_e2e_repo(root, info, …)` (distinct の descriptor 変更 / `add -A` / basis commit / never-issued assert / 発行 subprocess) に分けた。descriptor 変更を submodule add の後へ移す順序交換は最終 `add -A` の前なので tree を変えない。既存名は互換 wrapper (単独走・境界負例はこの入口)。
- `_T080SharedBases`: session parent 直下 `proto/` + `proto.lock` (exclusive、build 中だけ) + `proto-complete.json` (pending→rename)。key lock 内で marker miss のとき proto を取得し、`copytree(proto, key_root, symlinks=True)` → finish。lock 順序 key → proto。copy 中の shared lock は持たない (完成 proto は不変、削除は session parent 全体の最終退出者)。marker 有りの JSON 破損・root 欠損は例外伝播 (黙って再構築しない)。
- 単独走 (process memo 経路)・runtime source の key ごと複製・P3 (複製の並列化・stat 削除)・production scan は触らない。
- **I1 (bytes 同一) の定義:** 同一の source snapshot・key・Git 設定・commit metadata の下で、working tree の path/種類/bytes/mode/link target、basis tree OID、basis commit OID、receipt raw/document、発行後 HEAD tree OID が一致。除外: index stat、reflog、`.git` 内部 timestamp、活性化 commit OID。
- **session snapshot:** proto は xdist session (= 1 shard の pytest run) の最初の要求時点の実 repo を写し、以後の key はその snapshot を使う。「key ごとに実 repo を読み直す」性質は捨てる (ユーザー裁定の「session 1 回」が指示する性質。session 中の実 repo 変化の検出は実 repo を直接 scan する検査の責務)。

新 test 9 node (小型合成 source、実 git、独立 reference): 派生機構の同値性 (default/distinct)、proto の未完成公開・pending-only の再構築、proto lock の識別付き EX 待ち、marker 破損の例外伝播、finish 失敗時の key marker 非公開、proto 入口の境界検査。計算ノードで合計 1 秒未満 (小型焦点 24 node が 18.6 秒、うち `temp_roots` 17 秒)。

## 4. 検証

- **実 corpus の I1 probe** (request 1950): base `08d56628e` の旧 module を `git show` から exec し、両 module の `_sanitized_git_env` で commit metadata を固定。default: basis commit `d2adeeb1…` / basis tree `9857c0c7…` / HEAD tree `bea790d3…`、distinct: `e4a93ef1…` / `d81b1a27…` / `d4c4cef1…` — **旧新で全項目一致**。proto 35.2 秒、旧 build 89.3 / 88.6 秒、新派生 + finish 63.9 / 64.0 秒。probe の 1 回目 (request 1948) は `python3 tools/<probe>.py` 起動で `sys.path[0]` が `tools/` になり conftest が `orchestrator` を import できず collection rc=3 で落ちた。`python3 -m tools.<probe>` で通った。
- **e2e 13 node の xdist `-n 12` 焦点走** (新 code: bnode067 133.3 秒 / bnode080 133.1 / bnode007 150.2、旧 code: bnode067 136.7 / bnode006 136.3。すべて 13 passed)。
- **小型焦点 24 node** (bnode012、request 1965): 全緑 18.6 秒。
- **段 6 敵対レビュー 2 本: must-fix 0 件** (nit: M1 の固定 path を `output/tracked.txt` に、説明の訂正 3 点)。
- **変異 matrix** (container worktree `bdfa49950`、runner は `run_tests.py … -k <小型 + shared-base + 境界 + 可視集合> -q -rf --force-dispatch`、25 node): 本走は baseline PASSED、**負例 9 件 (M1〜M5、M7〜M10) すべて KILLED で期待 node と観測 node が完全一致**、等価変異 M0 は SURVIVED (harness の正例)。probe 走 2 本 (全件 SURVIVED 期待) で観測 node を集めてから本走した。
  - **M6 (proto marker を build 前に公開) は probe 走で hang した。** hang したのは `test_t080_proto_incomplete_build_is_rebuilt[False]` (`-v` の 6 分 job で特定): 親の `assert not marker.exists()` が Pipe で子を止めたまま失敗し、`finally` の `terminate → join` が戻らない。欠陥は timeout で検出されるが「きれいに赤にならない」nit。DW-M06 に従い dispatch の本走から外した (hang_timeout 1500 秒で harness が orphan hold 中止、wave worktree に変異が残留 → job の walltime 終端後に `git checkout --` で復元し hold を削除した)。是正案は §7。
  - **M11 (proto 入口の境界検査を削除) は登録から外した。** `temp_roots` 経由で test 対象 checkout の実 `output/` へ書き込む (killer は `test_t080_proto_boundary_rejects_before_write` と `temp_roots` だが、後者は checkout を汚す)。

## 5. 受入 wall の効果 (同時刻ペア、D1260)

pre = 実装前 tip (51d4fec75 + merge main、旧 code)、post = 実装 tip (bdfa49950 + merge main)。ペアは別 worktree から同時刻に投入した (対照 worktree は `--wave control-…` で lease を分ける)。値は最遅 shard の junit `testsuite time`。詳細は `measurements.md`。

| ペア | pre (旧) | post (新) | 差 | 条件 |
|---|---|---|---|---|
| 1 | pre-4 shard-0 **331.977** | post-1 shard-0 **296.472** | **−35.5 秒 (−10.7%)** | 両側緑。e2e 10 node 238〜261 → 203〜226 (各 −36 秒)、`temp_roots` 104.6 → 23.6、g7 65.1 → 19.4 |
| 2 | pre-5 shard-0 333.317 (最遅 shard-2 410.232) | post-2 shard-0 573.210 | 不成立 | post-2 の shard-0 node (bnode050) だけ git subprocess 30 秒 timeout ×29 (F945 型非帰属赤)。同時刻の pre-5 shard-0 (bnode009) には無い |
| 3 | pre-6 shard-0 474.446 (error 16) | post-3 shard-0 465.459 (error 17) | −9.0 秒 (−1.9%) | 両側が同型の F945 赤 (git timeout 11〜12 + git archive timeout 4 + real-repo lock 1)。lustre 飽和下 |
| 4 | pre-7 shard-0 **326.709** | post-4 shard-0 **308.071** | **−18.6 秒 (−5.7%)** | 両側緑。e2e 10 node 233.4〜256.3 → 217.1〜239.9 (各 −16 秒)、`temp_roots` 100.0 → 40.6、g7 70.2 → 19.5 |

非ペアの pre: pre-1 326.189 / pre-2 336.855 (shard-0、緑)、pre-3 491.348 (error 6、F945 型)。

**読み方.** 比較可能な 3 ペア (1・3・4) はいずれも新 code が速いが、差は −10.7% / −1.9% / −5.7% で**中央値 −5.7%**。
D357 (差 10% 未満は変化なしと扱う) と D1260 (paired K=3 中央値 10% 未満なら採用しない) の基準の内側であり、
**受入 wall の短縮は確立していない。** node 単位では e2e 10 node が各 −16〜−36 秒、proto 経路を通らない `temp_roots`
(実 output の lustre 走査 ×2) と g7 が 2.5〜4 倍速く、旧 code の 5 本並行 lustre 複製が shard 全体の lustre 操作を
遅らせていたことと整合するが、D357 のとおり node 秒は wall の代理にならない。lustre が飽和して git subprocess が timeout する
regime (ペア 3) では旧新とも 465〜475 秒で差が無い。

**採否 (段 4 裁定 §6 に従う):** fixture 変更 (commit `bdfa49950`) は **land しない**。実装は branch `impl-dev-wave-t080-accept-speed`
(tip は `bdfa49950` + 受入時の merge main) に保存し、docs (本 insight・D2068 訂正・計測結果) だけを land する。採用の可否は
§7-5 の裁定パッケージとしてユーザーへ返す。

## 6. 主張しないこと

- 「受入全走が 5 分を切った」とは主張しない (post-1 の最遅 shard 296.5 秒は 1 走)。
- 温 cache の効果、受入 200 秒級と直列 118 秒の差の内訳は主張しない。
- 実 corpus の I1 は同一 source snapshot・固定 commit metadata の条件付きで、別走間の receipt 完全一致は主張しない。
- lustre 飽和 regime での改善は主張しない (ペア 3)。

## 7. 裁定パッケージ候補 (scope 外の real 所見、段 4 裁定 §7 + 段 6)

1. **第 2 proto (発行済み・未活性化)**: default / codex-trailer / extra-r-path の 3 key は basis commit が同じで draft→validate→finalize (10 scan) の結果が同一。共有すれば延べ約 80 秒の削減候補だが「production 発行を key ごとに走らせる」性質を変える。distinct と no-issue は別扱いで、distinct が床なら wall は変わらない。
2. **session snapshot の受理契約を再検討する場合の材料** (レンズ A A1/A27)。本 wave は §3 の定義で採った。
3. **P3 (複製の並列化)**: bytes 不変で上限 28 秒級だが lustre 律速なら悪化しうる。`is_file()` は index と実体の不一致検査で削れない。
4. **`test_t080_proto_incomplete_build_is_rebuilt[False]` の hang (M6)**: `finally` で子へ `"fail"` を送ってから `terminate`、`join(timeout)` + `kill` にすれば欠陥下でも即赤になる。Codex author の小さな fix 1 件。
5. **実装 `bdfa49950` (proto 派生) を land するか。** 受入 wall の中央値 −5.7% は D357 / D1260 の 10% 基準の内側だが、3 ペアとも同方向 (最悪でも −1.9%、退行なし)、e2e node 単位で −16〜−36 秒、lustre 飽和外では sibling test が 2.5〜4 倍速い。bytes 同一・変異 9/9 KILLED・レビュー must-fix 0・受入緑 (post-1 / post-4) は済んでいる。採用するなら D1260 とは別の明示裁定 (「共有資源削減を別目的として採用」または「10% 基準の緩和」) が要る。実装は branch `impl-dev-wave-t080-accept-speed` にあり、land は同 branch の tip を最終受入にかければよい。

## 8. verbatim/ の原文

`verbatim/` と `stage4-ruling.md` は行末空白だけを `sed 's/[ \t]*$//'` で除去した (可視文字不変、`git diff --check` のため)。原文は job dir `artifacts/dev-wave-t080-accept-speed/` にあり、SHA-256 と byte 数で同定できる。

| verbatim/ の file | 原文 | 原文の SHA-256 | bytes |
|---|---|---|---|
| `s2-plan.md` | `s2-plan.md` | `0c12adb021f9eae8eb4323fd28ce2a9cc855d50df1b4edd010823536f128dc5d` | 26433 |
| `s3-lensA.md` | `s3-a.md` | `756fb7dcb04a6dd3443bcc4e49467f80541f4181bfe2541c568f2eed2e96ce3d` | 27018 |
| `s3-lensB.md` | `s3-b.md` | `14fa8711d325f977d706a5f819820b7bbcbeaa2f4ae9a19bef7d48d4c2d601ba` | 18198 |
| `s5-author.md` | `s5-author.md` | `f30b2f638a71c48da29862a46c730afff04ee0479c24409f296b9bdb9896ec07` | 8874 |
| `s6-reviewA.md` | `s6-a.md` | `2e83017dbda7f0eef69c543a3fcdfe4bf694522fa34c45dffcd76e617954f5bf` | 16025 |
| `s6-reviewB.md` | `s6-b.md` | `e661067cd3fcd633a04af94632ffcf17e476f6cd4797a4644cc00aeffcaffc9c` | 14751 |

段 4 裁定の原文は job dir `s4-ruling.md`。
