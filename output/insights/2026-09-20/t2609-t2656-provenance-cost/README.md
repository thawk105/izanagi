# [T-2609][T-2656] 全史 provenance 監査 — dispatch 判定の実測と per-commit コスト削減

一次資料。wave: `dev-wave-t2609-t2656-provenance-cost`、基準 main `b7f970dfa507558f7fb669a5ab38958d6c76b57c`、
実装 commit `55068f84e9ce516956920b613f9b99f624a6c565` (Codex author + Claude integrator)。
job dir (repo 外、probe と生ログ): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2609-t2656-provenance-cost/`。
段 1 brief: `s1-brief.md`、段 4 裁定: `s4-ruling.md` (同 dir)。時刻は JST。

## 1. 何をしたか (要約)

- **T-2656 (実装):** 全史 11,769 commit の監査で commit ごとに起動していた git subprocess のうち、実装 path 取得 (`show %P`・non-merge `diff-tree`・
  merge の親別 `diff`) と重複 trailer parse の計 **29,095 本を一括取得へ置き換えた** (判定・findings・rc・公開出力は不変、失敗時は既存経路へ)。
  login の cold 全史 (受領証なし) で **CPU 総量 318〜368 秒 → 95〜105 秒 (−70 %)**、wall は負荷次第で **88〜143 秒 → 69〜126 秒 (−12〜42 %)**、
  ピークメモリ 718〜733 MB → 484〜625 MB。旧版 (`b7f970dfa` blob) との固定全史比較で公開出力は完全一致 (§5)。
- **T-2609 (裁定):** CPU 時間 (負荷) を dispatch 判定に足す案は「不要と確定」ではなく **証拠不足で保留**。本 wave は dispatch 判定・`grant_budget`・
  `--force-dispatch`・`authoritative` 述語・timeout を 1 bit も変えない。根拠と再訪条件は §7。

## 2. 起点と scope

台帳 entry 1487 (T-2609)、1518 (T-2656)、D2148 項 8 (外側 timeout は全区間)。scope は本題 2 件だけ — 新 gate・台帳・一般化は足していない。
既裁定: D2033 (message 一括化、fail-closed の型)、D2045 (受領証による prefix 再利用)、D721 (merge の combined diff 免除なし)、D908 (全史監査は削らない)。

## 3. 段 1 の実測 (改善前)

### 3.1 dispatch 経路の失敗率とキュー待ち (残存する provenance task 受領証 86 件、`probe/provenance_dispatch_stats.py`)

| 結果 | 件数 |
|---|---|
| child rc=0 (新規違反なし) | 78 |
| child rc=1 (真の違反検出) | 4 |
| child rc=2 (実行不能) | 1 |
| infra rc=16 | **3 (3.5 %、Wilson 95 % 区間 1.2〜9.8 %)** |

rc=16 の 3 件はいずれも計算ノード側の監査本体は「新規違反なし」で完走しており、失敗は前後処理 — 08-25 `_SignalAbort: signal 15` (呼び出し側からの SIGTERM)、
09-08 / 09-09 `orphan-hold-release-failed`。「別 wave で rc=16 が 5 回」の残り 2 件は撤去済み worktree の記録で母集合に無い。
`queue_wait_s`: 中央値 5.2 秒、p90 6.8 秒、**最大 537.6 秒** (09-19 23:04)、100 秒超は 3 件 (537.6 / 278.7 / 138.4)。queue は共有で provenance 固有の分布ではない。

### 3.2 計算ノード全史の内訳 (bnode003、48 CPU、32 worker、11,769 commit、受領証なし、`profile-compute-1.table.txt`)

wall 41.7 秒、CPU 288 秒 (子 user 97.8 + sys 153.3、自身 37)。subprocess 累積 1,128 秒 (並列合計) の内訳:

| 種別 | 回数 | 累積秒 | 比率 |
|---|---:|---:|---:|
| `show -s --format=%P` (`_commit_parents`) | 11,308 | 332.5 | 29 % |
| merge の `diff --name-only` × 親 (`_paths_changed_from`) | 8,502 | 235.7 | 21 % |
| `interpret-trailers --parse` repo cwd (`_ai_agent_values`) | 13,993 | 225.8 | 20 % |
| non-merge の `diff-tree --name-only` (`_commit_paths`) | 7,061 | 210.6 | 19 % |
| 隔離 `interpret-trailers` (CAB、tempdir 込み) | 11,315 | 62.4 | 6 % |
| `diff-tree --cc` (merge 候補の検査) | 1,418 | 59.6 | 5 % |
| 祖先索引・pickaxe・一括 message | 5 | 1.4 | — |

関数別では `_commit_paths` 838.9 秒 (worker の `_normal_commit_audit` 累積 1,272.8 秒の 66 %)。起点 T-2656 の順位 (trailer → 隔離 fs → path → 祖先) と逆に、
**実装 path 取得が最大**だった。`_ai_agent_values` の 13,993 回は commit 数 11,769 + 実装 path のある commit での再 parse 2,224 回。

### 3.3 login の走 (正規経路 = headroom 判定 → bounded scope)

| 条件 | wall | CPU (user+sys) | ピーク | load |
|---|---:|---:|---:|---|
| 受領証あり (同 tip、07:25) | 14.9 秒 | 7.5 秒 | 94.6 MB | 17 → 16 |
| **cold 全史・改善前** (受領証無効化、07:30) | **88.1 秒** | **368 秒** (131.4 + 236.7) | 725 MB | 10.9 → 18.9 |

起点の「login 428〜574 秒」は D2045 (09-16) 以前の混雑時観測で、今回の空いた login では 88 秒。CPU 総量 368 秒を 32 スレッドで奪い合うと wall が伸びる
(説明候補。I/O 待ちとの分離は未測定)。headroom は前回ピーク 94.6 MB から 118 MB と見積もり下限 1 GB を予約、実ピーク 725 MB。

### 3.4 受領証再利用が効かない構造 (`probe/receipt_bindings_diff.py`、`probe/new_dir_commit_rate.py`)

- 受領証は環境 digest で **7 partition** に分かれる (checker sha は同一 `5cb709cbca5d`、差は呼び出しシェルの `LANG`/`LC_*`/`GIT_EDITOR`/`GIT_PAGER` と
  config 行数 13/17)。計算ノード job は PBS job 環境を継承する (provenance task は `env_mode="inherit"`、allowlist 空) ので login シェルとは別 partition。
- さらに **attributes fingerprint (`_attribute_fingerprint`) が index の全 path の祖先 directory ごとに `.gitattributes` の有無を数える**ため、新しい祖先 directory を
  持つ tracked path が index に加わると (tracked `.gitattributes` が root の 1 件で 08-23 以来不変でも) 旧 directory 集合の受領証は全部失効する。
  計算ノード probe では同 partition の受領証と `attributes` だけが不一致だった。直近 60 main first-parent commit のうち **30 (50 %)** が新 directory を導入
  (毎 wave の insight dir) → wave 単位では land の全史監査はほぼ毎回 cold。**D2045 の再訪候補 (scope 外、次の一手)。**
- `login_headroom.grant_budget` の入力はメモリ bytes (観測余裕・生存予約・前回ピーク) だけで CPU/負荷を見ない (T-2609 の主張どおり)。

## 4. 段 2〜4 (plan・相談・裁定)

- 段 2 plan (codex): (a) 親表 / (b) non-merge 一括 / (c) merge 親別 batch / (d) values 共有を採用候補、(e) tempdir 共有は見送り。`%(trailers)` 置換と cwd 変更は
  ambient config の等価性証明を要するため見送り (P1)。
- 段 3 相談 A の must-fix: **(c) を porcelain `git diff` から plumbing `diff-tree` に替えると `diff.ignoreSubmodules` (UI config) の扱いが変わり、gitlink が両親と異なる
  merge で判定差** → `diff.ignoreSubmodules` / `diff.relative` が全層で未設定のときだけ (c) を有効化する gate を採用。
- 段 3 相談 B の must-fix: D2148 項 8 の逐語切り出しミス (別 D の項 8 を切っていた、修正済み)、固定全史比較の実行仕様 (旧 blob・同 path 位置・cold・
  内部/公開の両方)、変異 matrix の 5 分予算。P2 (CPU 判定を足さない) は「不要と確定」でなく「保留」。
- 段 4: 所見はすべて real、採否は `s4-ruling.md`。変異 M-1〜M-9 を事前登録 (判定差 kill と契約 kill を分離)。

## 5. 実装と検証

### 5.1 実装 (`tools/check_ai_provenance.py`、+148/−10)

| 候補 | 内容 | fail-closed |
|---|---|---|
| (a) | `_Ancestry.parents`: `rev-list --topo-order --parents` の閉包全体から検証済み親表 (終端 LF・全 token hex・混在なし・重複なし・要求根含む・全親が index 内で子より先) | 検証失敗は親表 `None` → 従来 `show %P`。既存 ancestry の bits/mask は不変 |
| (b) | `_batch_nonmerge_paths`: `git diff-tree --stdin --root --no-renames -r --name-only -z --always`、全 hex token を見出し候補にし要求列と順序・件数込みで一致、path 順は git 出力順 | 不一致・空 stdout・例外は `None` → 全 non-merge を従来 `diff-tree` |
| (c) | `_merge_path_batch_enabled` (`git config --get diff.ignoreSubmodules` / `diff.relative` が両方 rc=1) のときだけ `_batch_merge_parent_paths`: 親番号ごとの batch (`<merge> <parent>` 行、`--diff-filter=ACMRDTUXB --always`)、全 batch 成功後にだけ公開 | 設定あり・失敗は全 merge を従来 `diff` × 親。intersection → `diff-tree --cc` は不変 (D721) |
| (d) | `validate_message` / `validate_implementation_author` に keyword-only `values=None`、`_normal_commit_audit` (ancestry あり) で 1 回 parse | `values is None` のときだけ parse (`[]` は再 parse しない)。oracle は従来 2 回 |

高速経路は authoritative かつ ancestry ありに限る (oracle / `--range` の親・path 取得は従来、values 共有は ancestry のある両経路)。`main`・dispatch 判定・受領証の
束縛/publish は無変更。捕捉例外は `RuntimeError, OSError, UnicodeError, ValueError` (投機取得に限る)。

### 5.2 テストと焦点走

テスト 26 本追加 (`orchestrator/tests/test_check_ai_provenance.py`、+734 行、既存テストの AST 不変)。焦点走 (計算ノード dispatch):
focus-1 (checker + consumer 9 file) **3,427 passed / 1 failed / 7 skipped** (85 秒) → 赤は新規テストの前提 `diff.orderFile` (plumbing は読まない) の誤り → fix1 (Codex、1 行削除) →
focus-2 (checker 単独) **549 passed / 0 failed** (25 秒)。

### 5.3 レビュー (段 6、2 本並列)

A (等価性・fail-closed・到達性) / B (過剰・削除・受理集合・波及): **両方 GO、must-fix / should なし**。nit (記録のみ):
merge gate テストの ambient config 依存、M-4/M-5/M-8 の変異編集を具体化、親表の空行検査は既存 `IndexError` が先で冗長、到達テスト 4 箇所の不足、
values 共有は `--range` でも 2→1 (判定不変)、checker 改版で受領証が全失効する初回 cold 費用の明記、`result.keys()` / `parents.keys()` 検査の冗長。
fix1 は 1 行のテスト前提削除で実装不変のため焦点再レビューは省略した。

### 5.4 固定全史の旧版/新版比較 (段 4 B-M2)

旧 checker = `b7f970dfa:tools/check_ai_provenance.py` (sha256 `5cb709cbca5d…`)、新 = 実装 commit の bytes (`7c02fb2d5fec…`)。独立 clone (main = `55068f84e`、11,770 commit) の
同じ path 位置で旧/新を交互に入れ替え、cold (未知 `GIT_*` env で新 partition、内部は `receipt_state=None`) で走らせ、終了時に `git checkout --` で復元
(`probe/fullhistory_compare.py`)。

| 場所 | 比較 | 旧 | 新 | 一致 |
|---|---|---|---|---|
| login (bounded scope、`compare-login-ab.json`) | 公開 rc / stdout / 静的 stderr、2 ラウンド交互 | 4 走とも rc=0、stdout sha `dd58376c…` | 同左 | **一致** |
| 計算ノード bnode006 (`compare-compute-1.json`) | 内部 `HistoryAudit` (findings 0 / known 56 / corrected 1 / waived 12) + selected 列 + `_normal_commit_audit` 回数 11,770 の digest、2 ラウンド | `5b0fba622a8d…` | `5b0fba622a8d…` | **一致** |
| 同上 | 公開 rc / stdout / 静的 stderr | rc=0、`dd58376c…` | 同左 | **一致** |

呼び出し回数 (計算ノード内部): `_commit_paths` 11,309 → **4,247** (merge だけ従来関数を通り、その親別集合は batch から注入)、`_ai_agent_values` 13,995 → **11,770** (重複 2,225 が消えた)、
`_normal_commit_audit` 11,770 で不変 (重複 selected の監査回数を保つ)。既知違反 56 件 (post-baseline 3) は旧/新で同じ OID・kind・value・順序 (digest 一致に含む)。
bounded scope の予算・ピーク行 (動的診断) は比較対象から除いた。

### 5.5 変異 matrix

独立 clone `mutation-source` (main = `55068f84e`) の固定 commit で `tools/mutation_worktree.py` (計算ノード dispatch、runner = `python3 tools/run_tests.py --force-dispatch
orchestrator/tests/test_check_ai_provenance.py -q -rf`)。probe (全件 SURVIVED 期待、spec sha `f258feee…`) で観測 node を集め、final (KILLED 期待 + 完全集合、spec sha `59e6afd9…`) で本走。
**final: baseline PASSED、M-1〜M-9 = 9/9 KILLED (期待 node 完全一致)、等価変異 E0 = SURVIVED、MISMATCH 0** (`mutation/mutation-final-results.json` は
job stdout 全文と collection 一覧を sha256 で束縛して省略した要約版。原本 (1.07 MB) は job dir、`_summary_of.original_sha256` で照合できる)。

| # | 位置 (関数) と編集 | 種別 | 観測 node 数 / 主 test |
|---|---|---|---|
| M-1 | `_build_ancestry`: 親 tuple を第 1 親だけに (`row[1:2]`) | 契約 (+判定差: merge が non-merge 扱いになり batch へ流れる) | 18 / `test_ancestry_parent_rows_match_show_parents` ほか受領証系 |
| M-2 | `_build_ancestry`: 閉包外親・順序検査を落とす | 契約 | 1 / `test_parent_cache_invalid_rows_fall_back[outside]` |
| M-3 | `_batch_nonmerge_paths`: `--always` を落とす | 契約 | 13 / `test_batch_nonmerge_always_emits_empty_headers` + 破損 fixture 群 |
| M-4 | `_parse_path_batch`: 不一致でも `result` を返す (部分結果公開) | 判定差 | 12 / `test_batch_nonmerge_invalid_output_restores_public_result[missing]` + hex path 群 |
| M-5 | `_parse_path_batch`: 見出しを `token in requested` だけにする (hex 名 path を通常 path に) | 契約 | 6 / `test_batch_nonmerge_hex_paths_discard_entire_batch[*]` |
| M-6 | `_merge_path_batch_enabled`: gate を恒真に | 判定差 | 7 / `test_batch_merge_ignore_submodules_uses_legacy_verdict` + `test_merge_path_batch_config_gate[*]` |
| M-7 | `_batch_merge_parent_paths`: 後段 batch 失敗で `break` (先行結果を使う) | 判定差 + 契約 | 2 / `test_batch_merge_late_failure_discards_all_parent_batches` |
| M-8 | `_normal_commit_audit`: `_ai_agent_values(subject)` (取り違え) | 判定差 | 165 / `test_shared_agent_values_stay_with_their_commit` ほか |
| M-9 | `validate_message`: `values is None` → `not values` | 契約 | 1 / `test_agent_values_none_and_empty_are_distinct` |
| E0 | `_batch_merge_parent_paths`: `list(dict.fromkeys(..))` → `[*dict.fromkeys(..)]` (等価) | positive | 0 / SURVIVED (harness の生存検出の正例) |

各変異は 1 箇所の逐語置換で、赤理由はその編集 1 つ (DW-M01)。「判定差」は監査の finding / rc が変わる変異、「契約」は取得回数・argv・fallback 発火の pin が破れる変異。
所要: probe 16 分、final 22 分 (baseline + 10 変異、各 1 走 = 計算ノード job 1 本、単独 file 25 秒 + dispatch 往復)。

## 6. 性能 (改善前後)

cold 全史 (受領証なし)。「commit 後」は実装 commit 直後の正規 full 監査 (改版で受領証が全失効した初回)。CPU は子 process の user+sys (内部比較は自身も含む)。

| 場所 / 条件 | 版 | wall | CPU | ピーク | load | 出所 |
|---|---|---:|---:|---:|---|---|
| login、07:30 | 旧 | 88.1 秒 | 368 秒 | 725 MB | 10.9 → 18.9 | `login-full-baseline-1.json` |
| login、commit 後 08:20 | 新 | **68.8 秒** | **105 秒** | 484 MB | 8.9 → 10.2 | `login-regular-2.json` |
| login 交互 R1、08:23 | 旧 → 新 | 133.2 → **77.7** 秒 | 318 → **96.6** 秒 | 733 → 625 MB | 7.0 → 44.8 → 19.3 | `compare-login-ab.json` |
| login 交互 R2 | 旧 → 新 | 143.0 → **125.9** 秒 | 305 → **95.3** 秒 | 718 → 604 MB | 19.3 → 25.2 → 11.3 | 同上 |
| 計算ノード bnode006 内部 R1/R2 | 旧 → 新 | 35.8 / 34.8 → **23.7 / 23.8** 秒 | 228 / 226 → **68 / 68** 秒 | parser 133 → 221 MB (RSS) | — | `compare-compute-1.json` |
| 計算ノード bnode006 公開 R1/R2 | 旧 → 新 | 37.5 / 37.5 → **26.0 / 26.1** 秒 | 226 / 226 → **69 / 69** 秒 | — | — | 同上 |

- **CPU 総量は場所・負荷によらず −70 %** (login 305〜368 → 95〜105 秒、計算ノード 226 → 68 秒)。混雑した login で wall が CPU 総量に引かれる場面ほど効く。
- wall は login で −12〜42 % (負荷依存: R2 の新版は他 wave の走行で load 25)、計算ノードで −30〜34 %。残りは逐次部分 (受領証・registry・祖先索引・一括 batch) と
  残存 subprocess (`interpret-trailers` repo 11,770 + 隔離 11,315 + `--cc` 1,418 ≈ 24,500 本)。
- ピークメモリは login の bounded scope で 725 → 484〜625 MB。一括 path list の常駐で parser 側 RSS は +88 MB (計算ノード内部) だが scope 全体では減った
  (子 git の同時常駐が減るため)。
- **同時刻の対照は login 交互 2 ラウンドと計算ノード 2 ラウンド**。1 走ずつの前後比較 (07:30 vs 08:20) は参考値。

## 7. T-2609 の裁定 — CPU 時間を dispatch 判定に足すか

起点 T-2609 は「dispatch 判定がメモリ bytes だけを見て CPU 時間を入力にしないため、混雑した login に留まり 480 秒を超える回が出る」だった。段 1〜6 の実測から:

1. dispatch 基盤の失敗は 3/86 (3.5 %、95 % 区間 1.2〜9.8 %) で、いずれも監査本体でなく前後処理 (SIGTERM、orphan-hold 解放)。
2. queue 待ちは中央値 5.2 秒だが尾は 538 秒。land 側の呼び出しは `_run_provenance_checker` の `timeout=480` を持ち、dispatcher の既定 queue 待ち上限は 900 秒 →
   **dispatch へ倒れると監査本体が正常でも queue 待ちだけで land が先に打ち切る構造**がある (D2148 項 8 = T-2484 の範囲、本 wave では timeout を変えない)。
3. 受領証再利用は login シェルの partition でだけ効きうる (計算ノード job は別 partition)。ただし §3.4 のとおり land の全史はほぼ毎回 cold なので、cold な land では
   dispatch に受領証の「追加損失」は無い (相談 B-S2)。
4. login の cold 全史は空いていれば旧 88 秒・新 69 秒、混雑時 (load 25〜45) でも新 78〜126 秒。CPU 総量が 368 → 105 秒に減ったので、混雑時に wall が
   CPU 総量へ引かれる余地が 1/3 になった。**ただし混雑時の現行値 (起点の 428〜574 秒相当の負荷) は本 wave では観測できておらず、「480 秒に確実に収まる」とは言わない。**

**裁定 (段 4、相談 B の判定を採用): CPU 時間 (負荷) を dispatch 判定の入力に足す案は「不要と確定」ではなく「証拠不足で保留」。**
本 wave は `main` の dispatch 判定・`login_headroom.grant_budget`・`--force-dispatch`・`authoritative = args.rev_range is None`・land の 480 秒 timeout を 1 bit も変えない。
再訪条件: 改善後 (本 commit 以降) の login 全史監査が混雑時に 480 秒を超える観測が 1 件でも出たら、負荷を入力にした実行場所判断 (メモリ予約は維持、dispatch 時の予約解放、
queue 停止時の扱い、`--force-dispatch` の保存) を別 wave で設計する。`os.getloadavg()` の絶対しきい値だけでは host 容量・I/O 待ち・cgroup 制約を区別できない
(相談 B-S1) ので、足すなら期限内完了を予測する材料 (履歴量・cold/warm・過去の CPU 秒と wall・実効 CPU 数) から設計する。

## 8. 限界と次の一手

### 限界
- 混雑時 (load 100 超) の login 全史は本 wave 中に観測できず、改善後の上限は未確定。同時刻対照は login 2 ラウンド + 計算ノード 2 ラウンドのみ。
- 等価性は「固定環境・正常 object」の下で、固定全史 (11,770 commit) の旧/新一致と 26 テストで示した。資源障害 (OOM・timeout) 由来の終了まで同一とは主張しない (D2045 と同じ)。
- 一括 path list の常駐で parser 側 RSS は +88 MB。全史の path 数が増えれば線形に増える (上限は commit 数だけでは決まらない)。
- checker 改版 (本 commit を含む) のたびに受領証の環境 digest が変わり、全 partition の受領証が失効する。改版直後の land は必ず cold 全史。
- 段 1 の dispatch 失敗率 3.5 % は残存 worktree の受領証 86 件の標本値で、撤去済み wave の記録を含まない。
- 候補別 ablation ((a)〜(d) の個別寄与) は取っていない。総量の改善だけを示した。

### 次の一手 (起票候補、本 wave では実装しない)
- **受領証の attributes fingerprint が index の directory 集合に依存し、新 insight dir を足すたびに失効する** (D2045 の再訪)。祖先 directory の候補列挙を tip に依存させない
  形 (例: 実在する `.gitattributes` だけを束縛し、absent 候補を digest から外す) を設計し、cold 率 50 % を下げる。
- **land の `timeout=480` と dispatcher の queue 待ち 900 秒の両立** (D2148 項 8 = T-2484 の範囲)。dispatch へ倒れた監査が queue 待ちで打ち切られる構造を、
  外側 timeout の契約として扱う。
- **混雑時の login 全史監査の観測を集める** (改善後の checker で、load とともに wall/CPU を記録)。480 秒超が出たら T-2609 の再訪条件が発火する。
- 残存 subprocess (`interpret-trailers` 23,085 本、`--cc` 1,418 本) は、隔離 parser の private dir 共有 (plan (e)、見送り) と `%(trailers)` の等価性証明 (P1) が
  前提。取り分は CPU 秒で 1/3 程度 (計算ノード内訳の 26 %) と見積もるが、証明面の拡大を伴う。

## 9. 再現資料 (job dir)

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2609-t2656-provenance-cost/` (repo 外、生ログと probe。campaign 成果物ではない)。

| 用途 | file |
|---|---|
| dispatch 受領証の横断集計 | `probe/provenance_dispatch_stats.py`、`probe/receipt_detail.py` |
| 計算ノード全史の内訳 (改善前) | `probe/provenance_cost_profile.py` (generic dispatch、`probe/dispatch-profile.sh`)、`profile-compute-1.stdout.txt`、`profile-compute-1.table.txt` (`probe/show_profile.py`) |
| login 正規走 (rusage 付き) | `probe/login_regular_run.py`、`probe/login-regular.sh`、`probe/login-full.sh` (受領証無効化)、`login-regular-{1,2}.json`、`login-full-baseline-1.json` |
| 受領証 partition と bindings 差 | `probe/audit_receipts_stats.py`、`probe/receipt_bindings_diff.py`、`bindings-compute-1.stdout.txt` |
| 新 directory 導入率 | `probe/new_dir_commit_rate.py` |
| git 出力形の実験 | `probe/trailer_parse_micro.py`、`probe/difftree_stdin_shape.py`、`probe/difftree_always_shape.py`、対応する `*.txt` |
| 固定全史比較 | `probe/fullhistory_compare.py`、`probe/run-compare.sh` (login)、`probe/dispatch-compare.sh` (計算ノード)、`compare-login-ab.json`、`compare-compute-1.json` |
| 変異 matrix | `mutation-spec-probe.json`、`mutation-spec-final.json`、`run-mutation.sh`、`mutation-{probe,final}-results.json` |
| codex 子の prompt / 出力 | `codex/prompt-*.md`、`codex/s2-plan.md`、`codex/s3-consult-{A,B}.md`、`codex/s5-author.md`、`codex/s6-review-{A,B}.md`、`codex/s6-fix1.md`、`codex/s5-author.patch` |
| 逐語射影 | `verbatim/` (T-2609 / T-2656 起点、D2033 / D2045 / D721 / D908 / D2148 項 8、焦点走の赤) |

独立 clone: `mutation-source` (変異 harness と login A/B)、`compare-source` (計算ノード比較)。いずれも main = `55068f84e`。

本 insight dir 内の写し: `reviews/` (codex 出力 7 本、うち `s2-plan.md` / `s5-author.md` は行末空白を可逆正規化 — 原本 sha256/bytes は
`verbatim-normalization.json`)、`mutation/` (spec 2 本 + results 要約 2 本)、`measurements/` (計測 JSON/txt 12 本)。probe の `.py` / `.sh` は実装面
(所在不問の拡張子契約) なので repo へ写さず job dir を指す。
