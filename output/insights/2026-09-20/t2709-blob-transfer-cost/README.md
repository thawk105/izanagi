---
authority: none
default_effect: no-state-change
---

# t080 fixture の index 化を「必要 blob だけの移送」で自己完結させる経路の費用 (2026-09-20)

依頼は [T-2709]: 実 repo の object store を露出せず必要 blob だけを fixture へ移送する費用が、
現行 `git add -A` の削減分を食うかを測る。結論は **測定条件内では食わない (改善候補)。効果は base 1 回あたり
1.7 秒 (15%) で、受入 wall の変化と D357 / D1260 の達否は未測定。** 本 wave は fixture を変えず、
採否はユーザー裁定へ返す (§8)。

## 結論 (最初に読む)

計算ノード bnode007 (local xfs `/tmp`、受入と同じ置き場)、source tip `b7f970dfa`、移送設定 `--window=0 --depth=0` で、
同一 fixture に対し 3 方式を 5 round 交互に測った。

| 方式 | 中身 | base 1 回の合計 (中央値 [min, max]) |
|---|---|---|
| A (現行) | `git add -A` → commit → production 形 status | **10.978 秒** [10.973, 10.982] |
| C1 (採用候補形) | source 側で OID 選定 → blob だけ pack 移送 → `git add -A` → commit → status | **9.296 秒** [9.283, 9.348] |
| C2 (参考費用) | 移送 → `update-index --index-info` (参照 index を無料で使用) → write-tree / commit-tree → `update-index --refresh` → status | 8.919 秒 [8.890, 8.952] |

- 対差 d = C1 − A は 5 round とも負 (−1.631 / −1.686 / −1.674 / −1.682 / −1.690 秒)、中央値 **−1.682 秒**。
  事前登録の規則 (§4) により **改善候補**。15 試行すべてが (i)〜(viii) を満たし、方式ごと 1 回の (ix)(x) も全方式で真、失格 0。
- **起票文の「削減分 79〜191 秒」は login の外乱値だった。** 計算ノードでは A の `add -A` は 10.65 秒で、
  index 化を 0 にしても base 1 回あたり 11 秒しか減らない。
- **「0.61 秒」に相当する index-info + write-tree + commit-tree は 0.26 秒だが、C2 の合計は 8.9 秒である。** C2 は
  複製済み worktree を変更せず、空 stat の index を `update-index --refresh` で保存する経路の参考費用で、refresh 2.09 秒
  (ファイル全件のハッシュ走査 1 回と同程度) と移送 6.5 秒が乗る。他の自己完結経路 (例: `checkout-index -u`) の下限ではない。
- **副産物 (scope 外):** fixture 全体を test 用に `copytree` した複製先で、production 形 status を連続 2 回走らせると
  2.147 / 2.14 秒 (A/C1/C2 とも、方式ごと 1 コピー)。複製で index の stat が外れて再走査する説明と整合するが、再ハッシュ件数・
  実テスト内の status 回数・複製先で refresh した後の時間は未測定 (§8-2)。

## 1. 一次資料

| 区分 | 所在 |
|---|---|
| 本走の結果 (射影 JSON: 各 git record の stdout hex を落としたもの) | `run1-result.projected.json` (同 dir)。原本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2709-blob-transfer-cost/run1/result.json` (194,809,938 bytes、sha256 は §10) |
| probe の逐語 | `probe-source.md` (同 dir、959 行、sha256 `0e6759231b0e92d082196872288b978ea01ff153cecd77ad701d0de945fcef18`)。repo へは入れない |
| login selftest / hold-session の結果 | `selftest-login-result.json`、`hold-login-result.json` (同 dir) |
| 段 1 親 brief (訂正前。訂正は `stage4-ruling.md`) | `stage1-brief.md` |
| 段 3 敵対相談 (2 レンズ、must-fix 7) | `stage3-consult.md` |
| 段 4 裁定 (判定規則の事前登録・不変条件・plan v2・段 5 後の追記) | `stage4-ruling.md`、`spec-v2.md` |
| 段 5 author 報告 / 段 6 review | `stage5-author-report.md`、`stage6-review.md` |
| 起点 | 台帳 entry 1554 の T-2709、D2068、`output/insights/2026-09-16/t2559-acceptance-floor-t080/`、先例 `output/insights/2026-09-17/t2708-fixture-config-h-gap/` |

## 2. 問い

現行の t080 e2e fixture (`orchestrator/tests/test_s8b_oracle_driver.py` の `_build_t080_stub_free_e2e_repo`) は、
実 repo から `orchestrator/` と git 可視 `output/` を複製したあと `git add -A` + commit で basis を作る。
D2068 は (B) alternates で実 repo の object store を借りる案を「観測が変わる・貸出元の prune で object を失う」
で不採用、(C) 必要 blob だけを fixture 内へ移送する案を「効果の符号が未確認」で採らないと裁定した。
本 wave は (C) の符号と大きさを、受入と同じ計算ノード local `/tmp` で、1 job・1 node・同一 tip の対比較で測る (一般化は §7)。

## 3. 設計 (事前登録、`stage4-ruling.md` §3〜§5)

- **土台 1 回**: held module から builder を enforcing pytest session 経由で呼び (`hold_session`、先例 T-2708)、
  `issue_receipt=False` で fixture を 1 回組む (50.5 秒)。参照値 (tree、index 一覧、到達 object 集合、config) を抽出し、
  `.git` は fixture 外へ退避する。
- **試行ごとの再初期化 (timed 外)**: `.git/modules` (submodule の実体) を rename で退避 → `.git` を削除 → `git init` →
  参照 config を複写 → modules を rename で戻す。再初期化の直後の最初の git 操作が各方式の 1 手目 (無料の refresh/status を挟まない)。
- **timed 区間**: A = add + commit + status1。C1 = 選定 (source の `ls-files -s -z -- orchestrator output`、
  `ls-tree -r <real_basis> -- <in_repo_sources 30 path>` による上書き、`cat-file --batch-check` の存在確認) + 移送
  (`git -C <source> pack-objects --stdout … | git index-pack --stdin`、pipe 両端の外側 wall) + add + commit + status1。
  C2 = 移送 + 不足 blob 生成 + `update-index -z --index-info` (参照 index を逐語) + write-tree + commit-tree + update-ref +
  `update-index --refresh` + status1。status は production と同形 (`t080_freeze_migration._git_env` / `_worktree_status`:
  `-c core.useReplaceRefs=false -c core.fsmonitor=false -c core.untrackedCache=false status --porcelain=v1 -z
  --untracked-files=all --ignore-submodules=none`、`GIT_OPTIONAL_LOCKS=0`)。commit metadata は全方式で固定 (commit OID も一致させる)。
- **不変条件 (試行の失格条件)**: (i) tree OID = 参照、(ii) commit OID = 全試行で一致、(iii) status1 が空、(iv) 到達 object 集合 = 参照、
  (v) `fsck --connectivity-only` 緑、(vi) alternates 不在、(vii) 移送 pack の object が全部 blob で件数一致、(viii) 実 receipt に記録された
  commit 5 件が fixture で missing。方式ごとに 1 回: (ix) 参照を隠して fixture 全体を別 dir へ複製し、複製先で status が空・参照 blob 全件が
  present、(x) 変更検出 (tracked file への追記・mode 変更・submodule 内の変更が status に出て、戻すと空に戻る)。
- **事前実験**: 移送設定 {既定, `--window=0 --depth=0`} を交互 3 回 → 外側 wall の中央値が小さい方を main に使う。
- **順序**: round 1〜5 で A/C1/C2 を巡回 (r1: A C1 C2、r2: C1 C2 A、…)。各 round 先頭でハッシュ走査の参照値
  (`git hash-object --stdin-paths`、書込なし、regular file 26,773 件)。

## 4. 判定規則 (結果を見る前に確定、`stage4-ruling.md` §4・§7b)

round ごとの対差 d_r = C1 − A (5 round)。**改善候補** = median(d) ≤ −1.0 秒 かつ 4 round 以上で d < 0。
**悪化観測** = median(d) ≥ +1.0 秒 かつ 4 round 以上で d > 0。それ以外は **未確定**。成功 round 数 n が 5 未満なら符号の閾値は n − 1、n < 3 は未確定 (本走前の追記、`stage4-ruling.md` §7b)。
C2・副次量・複製先の status は主判定に使わない。改善候補なら採用再検討の裁定パッケージ、それ以外は現行維持で閉じる。
per-base の差を受入 wall の改善へ読み替えない (D357 / D1260 は wall の基準)。

## 5. 実測

### 5-1. 環境と土台

- 計算ノード bnode007 (48 core、affinity 48)、work-root `/tmp/t2709-mwv52hoa` (fstype **xfs**)、git 2.34.1、
  loadavg 0.49 (開始) → 1.08 (終了)。generic dispatch request `11899.nqsv`、Elapse 400 秒、
  2026-09-20 07:58:58〜08:05:32 JST (JSON の `started_at` / `finished_at` を JST に換算)。queue 待ちなし。
- source = wave worktree (`b7f970dfa`、共有 object store `/work/1/SFC/tanab/izanagi/.git`: pack 21 本 480,164 KB、loose 6,105)。
- builder 50.53 秒 (`issue_receipt=False`、参考値。T-2708 の Lustre work-root では 163.8 秒だった)。hold session 2.38 秒 (pytest rc=5)。
- 参照 fixture: index 26,774 entry (regular 26,773、symlink 0、gitlink 1)、regular file の総 bytes **787,740,540**、
  unique blob **19,687** (source に在る 19,686、無い 1 = `.gitmodules`)、到達 object 22,325 (builder commit を除く)、
  loose object 22,326 / 240,892 KB。in_repo_sources 30、recorded commit 5。

### 5-2. 移送設定の事前実験 (`present` 19,686 blob、外側 wall)

| 設定 | 回 | wall (秒) | pack bytes | 子の CPU utime (秒) |
|---|---|---|---|---|
| 初回移送 (既定、cold 未保証) | 1 | 10.690 | 151,549,369 | 33.43 |
| 既定 (delta 探索あり) | 3 | 10.089 / 10.039 / 10.089 (中央値 **10.089**) | 151.6 MB | 32.9〜33.0 |
| `--window=0 --depth=0` | 3 | 6.487 / 6.479 / 6.471 (中央値 **6.479**) | 165,461,538 | 7.7〜7.8 |

main は `--window=0 --depth=0` を採用 (規則どおり)。pack は 14 MB 大きいが wall は 3.6 秒短い。CPU は子プロセスの user 時間
(`cpu_s.utime`、`stime` を含まない) で、33 → 7.7 秒の差は delta 探索の有無と整合する (内部の内訳は未分解)。

### 5-3. main 試行 (15 試行、失格 0)

| round | 順 | A 合計 | C1 合計 | C2 合計 | d = C1 − A |
|---|---|---|---|---|---|
| 1 | A C1 C2 | 10.979 | 9.348 | 8.919 | −1.631 |
| 2 | C1 C2 A | 10.976 | 9.290 | 8.919 | −1.686 |
| 3 | C2 A C1 | 10.982 | 9.308 | 8.890 | −1.674 |
| 4 | A C1 C2 | 10.978 | 9.296 | 8.952 | −1.682 |
| 5 | C1 C2 A | 10.973 | 9.283 | 8.900 | −1.690 |
| 中央値 | | **10.978** | **9.296** | 8.919 | **−1.682** |

位置効果は見えない (各方式の幅は A 0.009 秒、C1 0.066 秒、C2 0.063 秒)。main 初回の C1 (9.348) は同 round の A (10.979) より短い。
外側 wall (python 側の準備を含む) で再計算しても対差の中央値は約 −1.668 秒、5/5 負で判定は変わらない。

### 5-4. 内訳 (中央値 [min, max]、秒)

| 区間 | A | C1 | C2 |
|---|---|---|---|
| 選定 (source `ls-files` + `ls-tree` + `batch-check`) | — | 0.380 [0.355, 0.395] | — (参照 index を無料で使用) |
| 移送 (pack-objects \| index-pack) | — | 6.478 [6.471, 6.503] | 6.503 [6.474, 6.535] |
| 不足 blob 生成 (`.gitmodules` 1 件) | — | — (add が書く) | 0.001 |
| `update-index --index-info` | — | — | 0.029 |
| `write-tree` / `commit-tree` / `update-ref` | — | — | 0.232 / 0.001 / 0.001 |
| `git add -A` | **10.654** [10.649, 10.664] | **2.145** [2.142, 2.149] | — |
| `git commit` | 0.263 | 0.243 | — |
| 明示 `update-index --refresh` | — | — | **2.091** [2.090, 2.092] |
| status1 (production 形) | 0.060 | 0.060 | 0.060 |
| status2 | 0.059 | 0.059 | 0.059 |
| **合計 (status2 を除く)** | **10.978** | **9.296** | **8.919** |
| python 側の準備 (外側 wall − 合計) | 0.000 | 0.014 | 0.014 |

ハッシュ走査の参照値 (`hash-object --stdin-paths`、26,773 file / 787.7 MB、書込なし): 2.119 / 2.093 / 2.094 / 2.093 / 2.093 秒
(中央値 **2.094**)。C1 の add 2.145 秒、C2 の refresh 2.091 秒とほぼ等しい。

### 5-5. object store と副次量

| 量 | A | C1 | C2 |
|---|---|---|---|
| `count-objects`: loose / in-pack | 22,326 / 0 | 2,641 / 19,685 | 2,640 / 19,686 |
| `.git/objects` の file 数 / bytes | 22,326 / 189,650,342 | 2,643 / 166,872,618 | 2,642 / 166,869,663 |
| pack bytes | 0 | 165,439,219 | 165,461,538 |
| `.git` の `copytree` (副次量、中央値) | 0.894 秒 | 0.167 秒 | 0.167 秒 |
| fixture 全体の `copytree(symlinks=True)` (方式ごと 1 回) | 2.35 秒 | 1.61 秒 | 1.60 秒 |
| 複製先での production 形 status 1 回目 / 2 回目 | 2.147 / 2.140 | 2.147 / 2.137 | 2.147 / 2.140 |

C1 の in-pack が 19,685 (C2 より 1 少ない) のは、選定の pathspec `orchestrator output` の外にある operational file
(`docs/phase3-8b-descriptor-design.md`) と `.gitmodules` の 2 path に候補が無く (`no_candidate_paths` = 2)、`add -A` が
その 2 blob を loose に書いたため。missing は 0。

### 5-6. 検査

全 15 試行で (i)〜(viii) が真。方式ごとに 1 回の (ix) (参照 `.git` の退避先を隠した状態で fixture 全体を複製し、複製先で status 空・参照 blob
19,687 件 present。source の object store は可視のままなので「store 不可視化」までは実証していない) と
(x) 変更検出 (content / mode / submodule 内の変更が status に出て、戻すと空) は A / C1 / C2 とも全項目真。
移送 pack の object は `verify-pack -v` で全件 blob、件数は移送 OID 数と一致。recorded commit 5 件は全試行で missing。

## 6. 解釈

1. **計算ノードでは現行の index 化は 11 秒である。** login の 79〜191 秒 (D2068) は外乱を含む別環境の値で、計算ノードの
   判断尺度にならない。D2086 の一次資料 (git 操作 11 回 9.5 秒、直列 cProfile) と整合する。
2. **A と C1 の `add -A` の差は 8.51 秒 (10.654 − 2.145)。** object が pack に既在なら loose 生成を省くという説明と整合し、
   C1 の add 2.145 秒はハッシュ走査の参照値 2.094 秒に近い。ただし JSON はコマンド全体の wall であり、圧縮・書込・ハッシュの
   内部内訳は分解していない。
3. **C2 は参考費用である。** 参照 index を無料で使い、複製済み worktree を変更せず、空 stat の index を `update-index --refresh`
   で保存する経路で、中央値 8.919 秒 (移送 6.503 + refresh 2.091 + index-info/write-tree/commit-tree 0.26)。
   selftest (合成 repo) では「index-info 直後の index は空 stat」「`GIT_OPTIONAL_LOCKS=0` の production 形 status は index を
   書き戻さない」「refresh 後は stat が保存される」を確認した。他の自己完結経路 (blob から worktree を再配置して stat を記録する
   `checkout-index -u` など) の下限ではなく、それらは未測定 (§8-2)。C2 と C1 の差 0.38 秒は選定と commit の差。
4. **移送は wall 6.5 秒、子の user CPU 7.7 秒。** 既定設定 (delta 探索) では wall 10.1 秒・user CPU 33 秒。初回移送 (10.69 秒、既定) と
   反復の中央値 (10.09) の差は約 0.60 秒だが、cache 状態が不明なので cold の効果は評価できない。Lustre 読取りが支配的かどうかも
   この計測からは言えない。

## 7. 主張しないこと・過去値の限定

- **受入 wall の変化と D357 / D1260 の達否は未測定。** 本書は 1 job・1 node (bnode007)・同一 tip の base 計測であり、受入の対比較ではない。
  非競合で同じ per-base 差が保たれる単純な模型 (shard あたり 5 key の base、worker が並列に組む) では wall への効果は小さいと予想するが、
  上限ではなく、48 worker の競合下・別 node・別 tip では測っていない。
- cold cache は作れない。「初回移送」は事前実験の前に取った 1 回で、builder や存在確認が cache を温めた可能性がある。
- 過去値の読み方: D2086 の「git 操作 11 回 9.5 秒」は旧 tip・直列 cProfile の合計 (add + commit 単独値ではない)、
  「`output/` 複製 52.9 秒」は列挙・stat・copy の合計で移送の見積りではない、「base→test 複製 2.85〜3.0 秒」は worktree +
  `.git` 全体の複製で本書の `.git` 単独 0.17〜0.89 秒とは別量、「pack 21 本 480 MB」は source store の時点 inventory、
  「login 79〜191 秒」は判断に使わない、「builder 163.8 秒」(T-2708) は Lustre work-root の値で本書の 50.5 秒 (local xfs) と置き場が違う。
- 「fixture の観測が A と完全に同一」とは主張しない。同一と言えるのは §3 の不変条件 (到達 tree/commit/object 集合、production 形 status、
  変更検出、参照退避先を隠した複製先での status と blob 読出し、recorded commit の不在) で、source の object store を不可視にした検査は
  していない。`count-objects` や `.git` の bytes では当然区別できる。production / test 側に pack・loose の配置を見る検査は見つかっていない
  (段 3 レンズ B の静的確認、repo 全域の不存在証明ではない)。
- 本走の参照 fixture に symlink は無い (symlink 0)。symlink を含む入力での挙動は未被覆。

## 8. 裁定パッケージ (ユーザー裁定)

### 8-1. 本題 — C1 を採用するか

測定条件内では改善候補。効果量は base 1 回 −1.68 秒 (15%)、fixture 全体の test copy 1 回 −0.74 秒。受入 wall への効果は未測定。

| 案 | 内容 | 得るもの | 費用・条件 |
|---|---|---|---|
| (a) 採用 wave | fixture の `add -A` 直前に「選定 → 移送」を挟む (C1)。移送失敗は現行 `add -A` へ fallback | base −1.7 秒、test copy −0.7 秒、`.git` の file 数 22k → 2.6k (測定条件内) | test file の実装差分、変異・正負例 (§8-3)、D357 に従う同一 tip の実受入 3 対の対比較 (wall の効果はそこで初めて分かる) |
| (b) 見送り (現行維持) | 何も変えない。D2068(C) を限定文 (§8-4) で更新 | — | 記録のみ |

**親の推奨: (b)。** 理由: 今回の効果量 (base −1.7 秒、test copy −0.7 秒) に対し、fixture 本体の実装差分・変異登録・実受入の
対比較という検証費用が大きい。wall の基準 (D357 / D1260) の達否は未測定なので、それを根拠にはしない。D2086 の proto 化
(branch `impl-dev-wave-t080-accept-speed`、−5.7%) や §8-2 の候補と効果を合算する案は、合算効果も未検証なので注記に留める。

### 8-2. scope 外の候補 (起票せず記録)

1. **複製先の status 再走査。** 方式ごと 1 コピーで、production 形 status を連続 2 回走らせると 2.147 / 2.14 秒だった (元の fixture では
   0.060 秒)。`copytree` で index の stat が外れて再走査する説明と整合するが、再ハッシュ件数・実テスト内の status 回数 (発行経路
   `_capture_draft_basis` / `_validate_repin_report_git` は base 側で走る)・複製先で `update-index --refresh` した後の時間は未測定。
   複製直後の refresh 1 回で以後が元 fixture 並み (0.06 秒) になるかは仮説であり、fixture の test 側複製 (`_t080_stub_free_e2e_repo` の
   `copytree`) を変える実装差分を伴う。status 回数の実測が先。
2. **移送 + `checkout-index -u -f` で複製そのものを置換する経路。** D2086 §2-1 の base 構築 118 秒のうち `output/` 複製が 52.9 秒 (45%)。
   blob を pack で移送し (本書で 6.5 秒) worktree を `checkout-index` で書き出す形は、Lustre からの 23k file の copytree を pack 1 本の
   読取りに置き換えうる。未測定 (段 3 レンズ A の反例 A5 から)。書込 787 MB の費用と、複製の忠実性 (symlink・mode・attributes) の検査が要る。

### 8-3. (a) を選ぶ場合に採用 wave へ引き継ぐ事項 (段 3 レンズ B5)

- 面: `_build_t080_stub_free_e2e_repo` の `add -A` 直前、選定 (source の `ls-files -s` + basis の `ls-tree` の上書き + 存在確認)、
  移送 (`pack-objects --window=0 --depth=0 | index-pack --stdin`)、失敗時の fallback (半端な pack と外部参照を残さず現行 `add -A` へ、
  理由と費用を記録)、最後の `add -A` が現物を採用する性質の維持。
- 変異・正負例: alternates を作る変異 (production が拒否)、`--assume-unchanged` を使う変異 (内容変更の負例で検出)、
  commit を混ぜて移送する変異 (recorded commit の missing 観測で検出)、移送失敗時に半端な pack が残る変異、破損した転送 (index-pack が
  拒否)、source index と現物の不一致 (distinct / historical blob) で add が現物を採る正例、source に無い blob (missing) を add が書く正例、
  ignored / untracked file が index に入らない正例、symlink・mode・submodule (gitlink) の一致、複製後の独立性 (参照を隠して status と
  blob 読出し)。
- 受入: D357 に従い同一 tip の実受入で対比較する (per-base の差を wall へ読み替えない)。

### 8-4. D2068 (C) への追記文 (限定文のまま転記する)

> bnode007・local xfs・source tip b7f970dfa・移送設定 `--window=0 --depth=0` の C1 は、5 対の中央値差 −1.682 秒、5/5 負で
> 事前登録上の改善候補。受入 wall、cold、48 worker 競合下、他の自己完結経路は未評価。

「符号確認済み・全体不採用」へは更新しない。

## 9. 段 3・段 6 の所見

段 3 (must-fix 7 / should 5 / nit 2、棄却 0) は `stage4-ruling.md` §1、段 6 (must-fix 3 / should 4 / nit 3、全件採用、
本文の記述修正のみで probe 再走なし) は `stage6-review.md` と本書の改訂に反映した。

## 10. 工数・環境・同定

- codex 子 3 本 (consult 1 = 2 レンズ、author 1、review 1、全段 `gpt-6-astra`)。段 2 plan は省略 (軽量版)。段 6 の fix 子は起動せず、review の所見は親が本書の記述で反映した。
- 親の実走: selftest 1 (login pegasus02、rc=0、20 項目緑)、hold-session-only 1 (login、rc=0)、本走 1 (計算ノード generic dispatch、
  request `11899.nqsv`、bnode007、Elapse 400 秒、rc=0)。
- 実装差分ゼロ (probe は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2709-blob-transfer-cost/probe/tools/` に保全)。変異 matrix 免除、
  受入全走は記録 commit 後に実施 (結果は worklog)。
- 原本 JSON `run1/result.json`: 194,809,938 bytes、sha256 `89fe7c8d6c3056c4a27dc01f37eeeeaeb2336ac3cb79202cf1501d97797607ad`。射影 (278,436 bytes、sha256 `63cb9ac2228fe46d2728ccf0646142141bef11bb011b5f953862a2b582d3def5`) は各 git record の `stdout_hex` /
  `pipe_stdout_hex` (1,024 文字超) を長さと sha256 に置き換え、`trials[*].pack_object_types` (blob の list) を型別件数に縮約したもの (他の field は逐語、規則は JSON の `projection`)。
