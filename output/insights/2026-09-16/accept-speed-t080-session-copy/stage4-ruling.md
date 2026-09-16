---
authority: none
default_effect: no-state-change
---

# 段 4 裁定 — t080 e2e fixture の session 1 回複製と node 内派生 (2026-09-16)

親が段 2 plan と段 3 の 2 レンズ (A = 正しさ境界・検出力、B = 費用モデル・実効性) を real/refuted で裁定し、plan v2 と変異事前登録を確定した記録。可変状態の正本ではない。

## 0. 結論

**実装する。** 変更面は `orchestrator/tests/test_s8b_oracle_driver.py` だけ。key 非依存の準備 (proto) を xdist session parent に 1 回だけ組み、key ごとの base は proto の node 内複製 (`.git` 込み) から現行の key 側処理 (descriptor 変更 → `git add -A` → commit → 発行) で派生させる。単独走 (process memo 経路)・runtime source の複製・P3 (複製自体の高速化) は触らない。

効果の採否は D1260 に従い paired full K=3 で判定する (§6)。

## 1. 親 brief の訂正 (両レンズの指摘を採用)

| # | brief の記述 | 判定 | 訂正後 |
|---|---|---|---|
| a | 発行時の全件 scan は最大 5 回 | **real (誤り)** | 正常 active-valid 経路は **13 回** = draft 3 (再構成 searcher + verifier の live scan + pollute 検査) / validate 3 / finalize 4 (内部 validate 3 + 1) / `verify_receipt` 1 / `gate_check` 2 (`_resolve_t080_receipt` + `static_gate_adapter` の live scan)。plan の 12 も gate の 2 回目を落としていた。親が M:1727/1731/1985/2022/2023/2035/2048/2343, D:169/606, M:2490 で確認 |
| b | 「verify_receipt 4.85 秒/回、うち search_repository 5.3 秒/回」 | **real (誤り)** | 包含として成立しない。run1: verify 10 回合計 48.52 秒、search 9 回合計 47.64 秒 (verify 外の呼び出しを含む)。run2: verify 20 回 80.93 秒、search 17 回 89.91 秒 |
| c | 「`git add -A` は build の 8%」 | **real (誤り)** | 9.5 秒は `_run_git` 11 回 (init / config ×4 / submodule add / checkout / add -A / commit) の合計。add 単独は分解できない |
| d | 「temp_roots 19.8 秒 = no-issue key の冷 build。F971 の 20〜24 秒と整合」 | **refuted** | `test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` は実 output の snapshot を前後で取り、builder 3 呼び出しをすべて境界検査で拒否する。build は起きない。no-issue key の初回 build は末尾の g7 (49.07 秒) に含まれる。F971 との整合は撤回 |
| e | 「key 別の複製は 8〜45 秒で振れる」「温 cache でも安定して安くならない」 | **real (根拠不足)** | durations の引き算は本体差を複製に帰属させる。言えるのは profiler 集計 (run1 冷 1 回 52.9 秒、run2 5 回合計 189.7 秒 / 平均 38 秒) まで。温 cache の効果は反復測定まで保留 |
| f | 「受入 200〜222 秒と直列 118 秒の差 80〜100 秒は競合」 | **real (根拠不足)** | 測定範囲差 (base 対 test node、run1 の known-artifact は 132.0 秒で base との差 13.8 秒)・scheduler 待ち・lock 待ち・準備/発行/本体の競合が混在し、分解できない。撤回 |
| g | 「proto は `git init` 済み・index 未作成」 | **real (誤り)** | `submodule add` が `.gitmodules` と gitlink を stage する。proto は index を持つ |
| h | 「非競合の critical path は縮まない」 | **real (不正確)** | 初回 key は派生コピー D の分だけ増える。勝利条件は同時開始なら `max_k(R_k) > R_proto + D` |
| i | 「消える worker 時間 30〜200 秒」「4 × 23k 件の lustre 往復」 | **real (過大)** | 削減量は `ΣR_k − R_proto − ΣD_k` (未測定)。構造効果は「実 repo からの全件取得 4 回を省く」とだけ書く |
| j | 無条件の「受理集合不変」「bytes 同一」 | **real** | §3 の条件付き定義へ |
| k | 「t080 e2e は real-repo lock の対象外」 | real (事実は正しい) | ただし source snapshot 固定の根拠にはならない (既存 lock は session 中の実 repo 変化を排除しない) |
| l | 「fixture の可視集合が実 repo と 1 file ずれている (config.h)」を本 wave で触らない | refuted (懸念として) | proto 化で新しい差は生じない。比較基準は現行 fixture。小型同値性 test に「source では tracked、destination では ignored」の case を含める |

計算ノードの tempdir: bnode023 で `df -hT` を実測 (request 1788.nqsv)。`/tmp` は root の xfs NVMe (200 GB、空き 129 GB、tmpfs ではない)、`/scr` は 5.4 TB xfs、`/work` は lustre。1 node の実測であり保証ではない。

## 2. 所見の裁定

### レンズ A (正しさ境界)

| 所見 | 判定 | 採否 |
|---|---|---|
| A1 session snapshot 固定は「時間方向の再観測」を失う (実 repo が session 中に変化した場合、後発 key が旧 snapshot から発行できる) | **real** | **採用、明示裁定 (§3 (i))。** ユーザー裁定 2 の「session 1 回」が指示する性質そのもの。fixture の検出責任は「構築時点の実 repo の可視集合」であり、session 中の実 repo 変化の検出はこの fixture の設計目的ではない (それは実 repo を直接 scan する検査の責務)。T:868 の comment を更新する |
| A2 無害な untracked 増減の固定も観測値 (scan 件数・reconstruction hash) を変えうる | real | 採用 — I1 は同一 source snapshot を条件にする |
| A3 「実 repo の ccbench HEAD が pin と不一致なら現行が必ず拒否」は不成立 | refuted (親の前提) | 採用 — brief の例示から外す |
| A4 runtime sibling の session 化は「どの世代の実装か」を変えうる | real | **runtime source の session 1 回化はしない** (レンズ B も同旨)。現行の key ごと複製を維持 |
| A5 I1 は条件付き同値性 | real | 採用 (§3) |
| A6 「小さいが有効な corpus」による receipt 同値性 test は実 basis OID を解決できず実現性未証明 | plausible | **採用 — permanent test にしない。** 実 corpus の receipt 同値性は 1 回限りの probe で示す (§4-3) |
| A7 git launcher (PATH shim) は commit 時刻だけを注入する委譲器なら成立 | plausible | probe 側で `_sanitized_git_env` の monkeypatch により時刻を注入する (PATH shim は使わない)。発行 subprocess 内の活性化 commit は対象外 (receipt は活性化 commit の前に確定するので影響しない) |
| A8 小型同値性 + 既存 e2e + 変異だけでは receipt bytes 同一は未証明 | real | 採用 — §4-3 の probe で補う。permanent test の主張範囲は「派生機構の同値性と既存受理条件の維持」に限定 |
| A9 順序交換は同一入力なら tree・never-issued を変えない。descriptor は holdout closure (`design_source/sha256`) に入る | refuted (懸念) / real (補足) | 採用 — distinct case の比較で descriptor bytes と関連 field を除外しない |
| A10 完成 marker の読取り結果ごとの動作が未定義 | real | 採用 — key marker と同じ semantics (marker 不在 → 残骸削除して再構築。marker 有り → JSON を読んで root を返す。JSON 破損・root 欠損は例外伝播 = fail-closed)。全件 hash gate は追加しない |
| A11 marker は構築完了の証拠であり後発破損の保証ではない | real | 採用 — 保証を「成功後公開・独立コピー」に限定して記す |
| A12 別 ROOT/run_id の proto 混同 | refuted | 新 identity 不要。小型 test では key memo と proto memo を両方 reset |
| A13〜A25 変異 13 件の killer 帰属 | plausible/real | **採用 — §5 の v2 登録で killer を具体化** (proto lock の fd/path 識別、正常 return 前の Pipe 停止、境界検査は新 builder 直接呼び出し、distinct の独立期待 bytes、symlink は非 output 部へ) |
| A26 受入 3 shard は file 単位配置で、この file は 1 shard に閉じる | real | 採用 — 「session 1 回」= 1 xdist run (1 shard process 群) と明記 |
| A27 裁定パッケージ: snapshot 固定を受理契約として採るか | real | §3 (i) で親が採る (ユーザー裁定 2 の射程内)。再検討したい場合の材料を §7 に残す |

### レンズ B (費用モデル)

| 所見 | 判定 | 採否 |
|---|---|---|
| B1 勝利条件 `max_k(R_k) > R_proto + D` | plausible | 採用 (§1 h) |
| B2 5 key 同時開始は 48 worker の受入を説明しない | real | 採用 — 「44 worker と競合」を固定値として使わない |
| B3 118 対 200〜222 の差を競合に帰属しない | real | 採用 (§1 f) |
| B4 発行 53.3 秒不変なら直列 base の理想改善率は 44.8% (複製消去) / 42.2% (D=3)、受入 325.5 秒に対して 16.3% が上限 | real | 採用 — 10% には約 32.6 秒の純短縮が要る |
| B5〜B9 run2 の誤読 (temp_roots / g7 / 8〜45 秒 / 温 cache / F971) | refuted / real | 採用 (§1 d, e) |
| B10 post 3 走 + 同時刻対照は paired K=3 の代替でない | real | 採用 — pre K=3 を実装前 tip で走らせる (投入済み、§6) |
| B11 worker 時間・取得回数の削減だけでは符号不明の変更を採用する根拠にならない。P4 の親例外採用は D1260 と整合しない | real | **採用 — P4 を撤回。** 採否は §6 の基準に従い、基準未充足なら fixture 変更は land しない |
| B12 焦点走 (e2e 11 node、`-n 48 --dist loadgroup`) で critical path を直接測れる | real | 採用 — pre/post 各 3 本 (§6) |
| B13 copy 中の shared lock は不要 (完成 proto は不変) | real | 採用 — exclusive lock + 二重確認だけ |
| B14 process 内 proto memo は不要 | real | 採用 — 単独走は現行の直組み + key memo |
| B15 runtime source の session 化は不要 | real | 採用 |
| B16 最小変更 6 項目 | real | 採用 (§4-1) |
| B17 `/tmp` の実配置は未確認 | real | bnode023 で実測 (§1 末尾)。1 node の値として記す |
| B18 第 2 proto (発行済み・未活性化) は別 wave の裁定候補 | plausible | §7 |

## 3. I1 (bytes 同一) の確定定義

同一の source snapshot・key・Git 設定・commit metadata (author/committer の名前・mail・時刻) を入力とするとき、派生 base と現行 build は次で一致する:
working tree の path 集合・種類 (regular/symlink/dir)・bytes・mode・link target、basis tree OID、basis commit OID、receipt raw bytes と document、発行後 HEAD tree OID。
**除外:** index の stat 情報、reflog、`.git` 内部の timestamp、活性化 commit の OID (時刻を含むが receipt は活性化 commit の前に確定する)。

(i) **session snapshot:** proto は xdist session (= 1 shard の pytest run) の最初の要求時点の実 repo を写し、以後の key はその snapshot を使う。現行の「key ごとに実 repo を読み直す」性質は捨てる。これはユーザー裁定 2 の「session 1 回」が指示する性質であり、fixture の検出責任は「構築時点の可視集合」に限る。session 中の実 repo 変化の検出は実 repo を直接 scan する検査 (`test_s8b_repo_scan_invariant.py` 等) の責務で、この fixture は元々それを設計目的にしていない (T:868 の comment は `_git_visible_output_paths` を memo 化しないことを言っており、その性質は保つ)。

## 4. plan v2

### 4-1. 実装 (変更面: `orchestrator/tests/test_s8b_oracle_driver.py` のみ)

1. `_build_t080_stub_free_e2e_repo` を 2 関数に分ける。`_build_t080_e2e_proto(parent) -> (root, info)`: T:1370–1377 (境界検査・mkdir・init・config) → T:1380–1385 (`orchestrator/`・`_copy_git_visible_output`) → T:1387–1434 (known 読込・closure 抽出・basis file 複製、`current_runtime_sources` を info で返す) → T:1443–1450 (submodule add・config・pin checkout)。`_finish_t080_stub_free_e2e_repo(root, info, *, r_trailer, extra_r_path, issue_receipt, distinct_basis_blob)`: T:1435–1441 (descriptor 変更、distinct のみ) → T:1451–1457 (`add -A`・basis commit・never-issued assert) → T:1459–1630 (発行分岐・subprocess、runtime source は現行どおり key ごとに実 repo から複製)。既存名 `_build_t080_stub_free_e2e_repo(tmp_path, ...)` は互換 wrapper として残し、同 parent へ proto を直組みして finish を呼ぶ (単独走・T:1723 の境界負例・既存 wraps test はこの入口を使う)。
2. `_T080SharedBases` に proto 管理を足す。session parent 直下に `proto/` と `proto.lock`、完成 marker `proto-complete.json` (pending → rename)。`get(key)` は key lock 内で marker miss のとき proto を取得する。取得は `proto.lock` の exclusive + 二重確認: marker 不在なら残骸を削除して `_build_t080_e2e_proto(proto_parent)` を実行し、正常 return 後だけ pending を書いて rename。marker 有りなら JSON を読んで root と info を返す (JSON 破損・root 欠損は例外伝播)。lock 順序は key → proto。コピー中の shared lock は持たない (完成 proto は不変で、削除は session parent 全体の最終退出者だけ)。
3. 派生: `shutil.copytree(proto_root, key_root, symlinks=True)` (destination は未存在を要求) → `_finish_...`。
4. 単独走 (`_T080_SHARED_BASES is None`) は現行どおり wrapper で直組み。process 内 proto memo は入れない。
5. `_assert_t080_temp_root_outside_real_output` を proto parent と派生先に掛ける。lifetime (T:900–916、最終退出者削除) は不変。T:868 付近の comment に session snapshot の性質を 1〜2 行で書く。
6. runtime source の複製・P3・production code は触らない。

### 4-2. permanent test (小型合成 source、実 git を使う、受入 5 分上限を悪化させない)

- (a) `test_t080_proto_derivation_matches_direct_small_source`: 小型 source (tracked regular・実行 bit・untracked regular・ignored・symlink・深い path・「source では tracked だが destination の `.gitignore` に当たる」config.h 型) と小型 submodule に対し、**旧順序を独立に固定した reference 構築** (descriptor 変更 → submodule add の順を test 内に書く) と **proto → 派生** を比較する。比較: path 集合・種類・bytes・mode・link target、`git write-tree` の tree OID、submodule pointer (`external/ccbench/.git` の `gitdir:` と `.git/modules/.../config` の `core.worktree` が相対)、派生後に proto を移動/削除しても派生側の git が動くこと、片方の操作が他方を変えないこと。distinct case の descriptor 期待 bytes は「入力 descriptor + 固定 suffix」から独立導出する。実 repo の `ROOT` を使わず、builder の source root 注入点 (`_copy_git_visible_output(source_root, ...)` と `ROOT` monkeypatch、または proto builder の source 引数) を使う。実 corpus 依存の basis file 複製 (`git show <basis>:<path>`) は小型 source 内の commit で成立させる。
- (b) proto 負例: 小型 builder を Pipe で正常 return 前に停止し、その時点で marker が無いことを親から観測 → 失敗後の再要求で再構築 1 回。pending だけ残った状態 → 再構築。
- (c) 異なる 2 key の要求で proto builder 1 回・key builder 2 回。proto lock の fd/path を識別し、EX 待ちの到達通知を観測 (T:1121 型)。
- (d) proto 入口の境界検査: 新 proto builder を直接呼び、書込み前に拒否。
- 既存 shared-base test 群 (T:1047〜1290) の期待値更新は plan の表に従う。`t080_small_cache_builder` は proto も小型にする。T:1326 の AST 検査 (direct consumer 6 function / 11 node) を増やさない。

### 4-3. 1 回限りの probe (実 corpus の I1、Codex author、repo へ commit しない)

`tools/t080_proto_equivalence_probe.py` (worktree 内に書き、親が実行前に job dir へ退避、`--selftest` を持つ)。同一 process で (1) base commit `08d56628e` の `orchestrator/tests/test_s8b_oracle_driver.py` を `git show` で取り出して別 module 名で exec し、その `_build_t080_stub_free_e2e_repo` で旧経路の base を組む、(2) 新 module の proto → 派生で base を組む。両方で `_sanitized_git_env` を monkeypatch して `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` と名前・mail を固定する。比較: basis tree OID・basis commit OID・receipt raw bytes・発行後 HEAD tree OID・working tree の path/bytes/mode (`.git` 内部は除外)。key は default と distinct の 2 つ。計算ノード 1 本 (`--task generic`) で 1 回走らせ、結果 JSON を insight に記録する。

### 4-4. scope 外 (裁定パッケージ候補、§7)

第 2 proto (発行済み・未活性化)、P3、production scan の最適化、runtime source の session 化。

## 5. 変異事前登録 (v2)

対象行は現行アンカー。実装後に新行番号へ対応付け、DW-M08 の期待 node 完全集合は実装後の焦点走で確定して spec を段 6 で最終化する (未確定なら初回を probe と明記)。

| # | 変異 | 対象 | 期待 killer |
|---|---|---|---|
| M1 | proto の output コピーから固定 path 1 件を落とす | `_copy_git_visible_output` 呼び出し (T:1385 の移設先) | (a) — 明示集合に当該 path を含める |
| M2 | distinct の descriptor 追記を削除 | T:1435–1441 の移設先 | (a) distinct case (独立期待 bytes)。既存 T:1735 は killer と数えない |
| M3 | 派生コピーから `.git` を除外 | 新派生コード | (a) — tree 比較前に派生側が独立 repo であることを確認 |
| M4 | submodule pointer を proto の絶対 path に固定 | T:1443–1450 の移設先 | (a) — 派生後に proto を移動/削除して git が動くこと |
| M5 | proto lock (EX) を外す | 新 proto 管理 | (c) — proto lock の fd/path 識別、EX 待ち観測 |
| M6 | builder 正常 return 前に marker 公開 | 新 proto 管理 | (b) — Pipe 停止時点で marker 不在 |
| M7 | key 側 finish 途中の例外でも key complete を公開 | T:929–938 | 既存 key 負例の拡張 (copy 後の finish 失敗) |
| M8 | 派生コピーの `symlinks=True` を落とす | 新派生コード | (a) — 非 output 部に symlink を置く |
| M9 | cache identity から distinct field を落とす | T:980 | 既存 T:1186 |
| M10 | 最初の close で session parent を削除 | T:903–916 | 既存 T:1203 (小型 proto payload の first close 後の存在) |
| M11 | proto 入口の境界検査を削除 | 新 proto builder 入口 | (d) — 新 builder を直接呼ぶ case |

外した変異: process proto memo 関連 (入れない)、runtime snapshot 関連 (入れない)。fixture の単一理由性 (DW-M03) は実装後に親が確認する。

## 6. 計測と採否

- **pre K=3:** 実装前 tip (`01bcdf239` + 受入時の main merge) で `dev_wave_wait.py acceptance --lease-optional` を逐次 3 走 (pre-1 は 2026-09-16 21:22 JST 投入済み)。
- **post K=3:** 最終 tip (記録 commit 込み) で 3 走。うち 1 走が land 用受入。
- **焦点走:** e2e 11 node を `-n 48 --dist loadgroup --durations=0` で 1 node、pre/post 各 3 本 (`dispatch_compute.py --task tests`)。
- 指標: 最遅 shard の junit `testsuite time` (中央値)、shard-0 の span と最長 node、e2e 11 node の durations、receipt の canonical wall。同時刻の他 session の受入 junit を外乱対照として併記 (paired とは呼ばない)。
- **採否 (P4 v2):** D1260 に従い、paired K=3 の最遅 shard wall 中央値が pre 比 **10% 以上**短縮 → fixture 変更を land。10% 未満・符号不明 → fixture 変更は land しない (branch と成果物は保存し、§7 の裁定パッケージへ数値を添えて返す)。docs (内訳実測・D2068 erratum・本裁定) は結果によらず land する。
- 変異 matrix は §5。受入全走は免除しない。

## 7. 裁定パッケージ候補 (scope 外の real 所見)

1. **共有資源削減を別目的として例外採用するか** (レンズ B B11): wall 効果が 10% 未満でも「実 repo からの全件取得 4 回を省く」構造効果を理由に land するなら D1260 とは別の明示裁定が要る。
2. **第 2 proto (発行済み・未活性化)**: default / codex-trailer / extra-r-path の 3 key は basis commit が同じで draft→validate→finalize (10 scan) の結果が同一。共有すれば延べ約 80 秒の削減候補だが「production 発行を key ごとに走らせる」現行 e2e の性質を変える。distinct と no-issue は別扱いで、distinct が床なら wall は変わらない。
3. **session snapshot の受理契約** (レンズ A A27): 本 wave は §3 (i) で採ったが、「key ごとの再観測を維持する」案を再検討する場合の材料として残す。
4. **P3 (複製自体の高速化)**: `is_file()` は index と実体の不一致検査であり削れない。copytree の並列化は bytes 不変で最大 28 秒級の上限モデルだが lustre の帯域・MDS が律速なら悪化しうる。
