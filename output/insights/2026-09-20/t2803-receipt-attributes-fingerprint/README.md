# [T-2803] 全史 provenance 監査の受領証: attributes fingerprint を index の directory 集合に依存しない形にする (D2045 の改訂)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave branch `worktree-dev-wave-t2803-provenance-receipt`、起点 local main `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad`、
実装 commit `4c532aa0b` (初版: absent 除外 + 候補集合の包含検査)、fix commit `00d781372` (最終: 履歴由来候補、包含検査撤去)。
時刻はすべて 2026-09-20 JST。

## 1. 何をしたか (要約)

- 受領証 (D2045) の attributes fingerprint は index の全 path の祖先 directory ごとに `.gitattributes` の状態 (absent を含む) を束縛していたため、
  新 directory を導入する commit (直近 60 main first-parent commit の 50 %) を跨ぐと失効し、land はほぼ毎回 cold だった (§2)。
- **最終形:** (a) digest には absent の候補を入れない (実在する候補だけを束縛)、(b) 候補 directory を「root ∪ index path の祖先 dir ∪ **監査で属性が効く
  merge path (merge と第 1 親の name-only diff) の祖先 dir**」にする。後者は履歴とともに単調増加するので、監査で git が属性を読む directory は受領証時点
  でも候補に入っており、候補集合の変化を別に束縛する必要が無い (§4 の論証、設計判断は {{D:receipt-attributes-history-candidates}} = decisions fragment)。
- 初版 (absent 除外 + 受領証に候補集合を保存して包含検査) は段 6 レビュー A が実 Git で構成した反例 (候補外 dir の untracked `.gitattributes` が root の
  `-diff` を上書きして監査に効き、後で dir が候補入りしつつ file が消える) で受領証なし oracle と判定が食い違うと判明し、最終形へ改めた (§5)。
- 判定 (findings / rc / 公開 record) 不変を、正例・負例テスト 6 本 (各ケースで受領証を消した oracle と rc/stdout/stderr 一致) と変異 matrix (§7) で示した。
- 実測: attributes 束縛単独の隣接失効数は同一 60 遷移で **旧 25/60 → 新 0/60** (§8.1)。実機正例 (独立 clone、新 checker): cold 全史 wall 58.4 秒 / CPU 108 秒 →
  新 directory 導入 commit で warm wall 21.9 秒 / CPU 9.5 秒 → `.gitattributes` 変更で cold wall 62.6 秒 / CPU 96 秒 (§8.2)。
  **これらは cold 率・land wall・時間短縮率ではない** (§8 の限定)。

## 2. 起点と段 1 の実測 (改善前)

起点は entry 1722 (T-2656 wave) の次の一手 [T-2803] とユーザー依頼 (逐語 `verbatim/T-2803-origin.md`)。一次資料は
`output/insights/2026-09-20/t2609-t2656-provenance-cost/README.md` §3.3〜3.4。段 1 brief は `verbatim/s1-brief.md`。

| 実測 (20:5x、wave worktree HEAD f94b61fc8、共有 git-dir の受領証 store) | 値 |
|---|---|
| index の path 数 / 候補 directory 数 | 29,684 / 2,835 |
| 実在する `.gitattributes` (候補内) | root の 1 件 (`orchestrator/tests/fixtures/**/trace_*.log -text`、最終変更 47a457e43 2026-08-23) |
| 受領証 store | 424 件 / 11 partition |
| 直近 8 受領証 (同一 checker sha `7c02fb2d`) の `bindings.attributes` | 8 件すべて異なる (tip ごとに別 = cold 連鎖) |

段 1 で条件表を再評価: DW-O13 (受理形を増やす既存述語の改訂) が成立、入力 field = receipt `bindings.attributes`、上の値域と正負例の到達性を brief に記載。
O08 / O09 / O10 は非成立 (freeze 族・凍結 bytes に触れない)。

## 3. 段構成と時系列

軽量版 + 敵対検証 (受理集合が増えるため独立の敵対検証子を置いた)。段 2 の plan は親が brief に書き、段 3 consult 1 本が攻撃した。

| 時刻 | 段 | 内容 |
|---|---|---|
| 20:53 | 開始 gate | `check_wave_startup.py --mode fresh` rc 0 (main が 2 度進んだため ff-only を 2 回) |
| 21:0x | 段 3 | consult A (等価性・fail-closed・実効性): **must-fix 1** = absent 無条件除外の反例 (候補 dir 脱落 + untracked `.gitattributes` 出現) |
| 21:1x | 段 4 | 裁定 `verbatim/s4-ruling.md`: plan v2 = absent 除外 + 受領証に候補集合を保存し包含検査、テスト表、変異 M-1〜M-7 + EQ-1 |
| 21:19〜21:25 | 段 5 | author (unit worktree `.codex/worktrees/t2803-unit-impl`、13 call、379 秒)。sandbox で pytest 起動不能 (rc 16) |
| 21:27〜21:40 | 焦点走 | focus-1 (6 file、計算ノード job 13590): 2738 passed / 5 skipped / 0 failed。単独走 focus-2: 575 passed (549 + 新 26) |
| 21:43 | commit | 実装 commit `4c532aa0b`。commit 後 full 監査 (login、load 72→37): rc 0、12,061 commit、新規違反なし、wall 112.5 秒 (cold) |
| 21:46〜21:5x | 段 6 | review A (等価性): **NO-GO must-fix 1** (§5 の反例)。review B (テスト帰属・変異・実測設計): **NO-GO must-fix 2** (probe の包含再導出、変異の exact 文字列) |
| 21:5x | 段 6 裁定 | `verbatim/s6-ruling.md`: plan v3 = 履歴由来候補、包含検査・候補保存・schema 2 を撤去、変異 v2 = M-1〜M-4 + EQ-1 |
| 21:58〜22:04 | fix1 | plan v3 実装 (10 call、258 秒)。焦点走 focus-3: **2 failed** — 既存 pin `test_path_batches_follow_receipt_final_selection` (`diff-tree --stdin` 接頭) に候補列挙が混入、T-neg-6 が `_commit` helper (`git add -A`) で属性 file を tracked にして前提崩れ |
| 22:12〜22:14 | fix2 | 候補列挙を `git log --no-walk=unsorted --stdin --diff-merges=first-parent ...` へ、T-neg-6 は `git add <path>` 限定。焦点走 focus-5: **1 failed** — 既存 pin `test_path_batches_follow_correction_full_history_fallback` (`log --no-walk=unsorted` 接頭 = D2033 message batch) に混入 |
| 22:19〜22:21 | fix3 | argv 順序を `log --diff-merges=first-parent --no-walk=unsorted --stdin ...` に (fix は 3 巡 = DW-O16 の上限)。焦点走 focus-6: **2718 passed / 5 skipped / 0 failed** |
| 22:24 | commit | fix commit `00d781372` (fix1〜fix3 統合、message file の preflight rc 0) |
| 22:26〜22:27 | 単独走 | focus-8 (test_check_ai_provenance.py): **555 passed** (base 549 + 新 6)。focus-7 は走行中に commit を作った自分起因の非帰属赤 23 件 (§10) |
| 22:28〜22:55 | 変異 probe | 独立 clone (main = 00d781372)、baseline PASSED、M-1〜M-4 kill、EQ-1 SURVIVED (§7) |
| 22:30〜22:49 | E-1 | 旧 25/60 → 新 0/60 (§8.1) |
| 22:30〜22:3x | 焦点再レビュー | **GO、must-fix 0、nit 1** (費用記述: 候補列挙は lookup と publish の 2 回) |
| 22:50〜22:54 | E-2 | cold → warm (同 tip) → warm (新 tip) → cold (`.gitattributes` 変更) (§8.2) |
| 22:55〜23:04 | 変異 final | baseline PASSED、M-1〜M-4 4/4 KILLED (期待 node 完全一致)、EQ-1 SURVIVED、MISMATCH 0 (§7.1) |
| 23:0x | merge | local main 7c0a1c63a を固定 SHA で取り込み (`47fbfd58c`)、merge 後 full 監査 rc 0、12,157 commit、wall 47.4 秒 (cold) |

## 4. 最終形の設計と論証

監査で git が属性を読む操作は merge の `diff-tree --cc -p <merge> -- <path>` (候補 path ごとの combined patch の空判定 = 実装 path の選別) だけである
(レビュー A の経路表 `reviews/s3-consult-A.md` N2)。non-merge の `diff-tree --name-only`、trailer parse、`rev-list`、message 取得は属性の影響を受けず、
pickaxe (`log -S`) の結果は policy / scope_epoch / implementation_epoch / cab_hits として別に束縛される。

`--cc` の候補 = 全親の name-only diff の交わり ⊆ 第 1 親の name-only diff。よって
`AttrDirs(S) := {祖先 dir of p | merge m ∈ S, p ∈ diff(parent1(m), m)} ∪ {root}` は S の監査で属性が読まれる directory の上位集合で、
S(A) ⊆ S(B) (ff-only、同 policy) から `AttrDirs(S(A)) ⊆ AttrDirs(S(B))`。候補 `C(H) = root ∪ dirs(index_H) ∪ AttrDirs(S(H))`、digest `New(H)` を
C(H) の absent 以外の entry (+ info / configured / system / index entry) とすると:
**`New(A) = New(B)` ⇒ ∀d ∈ AttrDirs(S(A)): `state_A(d) = state_B(d)`** (実在なら B 側に同じ entry、absent なら B 側に entry が無く d ∈ C_B なので absent)。
よって S(A) の再監査で git が読む属性入力は A 時点と同一。index 由来の候補は健全性に不要な過剰近似で、既存テスト (index-only path の祖先が候補) を保つために残す。
候補集合の包含検査 (初版) は不要になる。

実装 (`tools/check_ai_provenance.py`、fix commit): `_attribute_candidates(head, *, policy=None)` が `git rev-list --merges <policy>..<head>` +
`--no-walk <policy>` の merge OID を `git log --diff-merges=first-parent --no-walk=unsorted --stdin --name-only -z --format= --no-renames` へ渡し
(1 process、merge 0 件なら呼ばない)、NUL 分割した path の祖先 dir を候補に加える。`_attribute_fingerprint(head, *, policy=None)` は文字列 digest。
`_receipt_bindings` は policy commit を 1 回取って共有。git 失敗は `RuntimeError` として呼び手の except に落ち cold + no publish (fail-closed)。
受領証 schema 1・key 集合・他の 12 束縛・淘汰・dispatch 判定・公開出力は不変。監査 tip の tree は読まない。

## 5. 段 6 レビュー A の反例 (初版を退けたもの) と閉じ方

初版 (`4c532aa0b`) = absent 除外 + 受領証に候補集合 (zlib + base64、32 KB) を保存し「受領証の候補 ⊆ 現在の候補」を検査。段 3 相談 A の反例
(候補 dir が index から脱落 → untracked `.gitattributes` 出現) は閉じるが、レビュー A (`reviews/s6-review-A.md` M1) の反例は閉じない:

1. merge M (Claude author、属性なしでは combined patch 空) の path `tools/retired/shared_lines.py` の最後の tracked file を commit A で削除。
2. A の監査前に untracked root `.gitattributes` = `tools/retired/shared_lines.py -diff`、untracked `tools/retired/.gitattributes` = `shared_lines.py diff` を置く。
   nested が root を上書きするので M の combined patch は空、全史監査は rc 0、受領証発行。nested は候補外 (tracked file の無い dir) で束縛されない。
3. commit B で `tools/retired/README.md` を追加 (dir が候補入り) し nested を削除。root は保持。
4. 初版: 候補は増えるだけ (包含 OK)、新候補は absent、実在 entry の digest 同一 → 受領証を再利用 → M を再監査せず rc 0。
   oracle (受領証なし) と旧形 (候補集合差で cold): root の `-diff` が M に効き Codex author 欠落 → rc 1。**判定差。**

最終形では `tools/retired/shared_lines.py` が M の第 1 親 diff にあるので `tools/retired` は A 時点から候補 → nested が実在 entry として bound → B で消えると
digest 不一致 → cold → oracle と一致。テスト T-neg-6 `test_attribute_retired_directory_reintroduced_falls_back` がこの構成を実 Git で再現し
(属性 file は両方 untracked のまま、`git ls-files` に `.gitattributes` が無いことを assert)、rc 1・finding・oracle 一致を固定する。

段 4 で私 (親) はこの残差を「D2045 の既存限界 (候補外 dir は列挙しない) の内側」と分類していた。旧形が候補集合の変化で偶然 cold になっていたことと、
oracle との判定差は別で、後者が判定基準である。この誤分類はレビューが正した。

## 6. テスト (fix commit、`orchestrator/tests/test_check_ai_provenance.py`)

| ID | test | 期待 |
|---|---|---|
| T-pos-1 | `test_attribute_absent_directory_addition_warm_hit` | 新 directory 導入 commit で warm (観測 = その commit だけ)、`_attribute_fingerprint` 同一、`_attribute_candidates` は真に増える、oracle 一致 |
| T-pos-2 | `test_attribute_new_candidate_file_falls_back` | tracked child で候補入りした dir の untracked `.gitattributes` で cold |
| T-neg-1 | `test_attribute_retired_directory_falls_back` | 相談 A の M1 (候補脱落 + untracked 出現) で cold、rc 1、merge finding |
| T-neg-2 | `test_attribute_untracked_file_removal_falls_back` | 実在 file 削除 (候補集合不変) で cold |
| T-neg-3 | `test_attribute_candidate_lstat_unreadable_falls_back` | 候補 path の lstat が PermissionError で cold |
| T-neg-6 | `test_attribute_retired_directory_reintroduced_falls_back` | §5 の反例で cold、rc 1、finding、oracle 一致、`b"tools/retired/.gitattributes"` が候補に実在 |

各ケースで受領証を消した oracle と rc/stdout/stderr の一致を assert する (`_attribute_receipt_oracle`)。base f94b61fc8 の既存テスト関数は AST 比較で変更・削除 0 件
(fix1 / focus1 報告)。初版で足した候補 field の破損 20 型・包含違反テストは機構の撤去とともに削除。既存 `test_attribute_fingerprint_is_independent_of_tip` と
`test_many_commit_delta_warm_hit` は緑を保つが absent 候補差への感度を失う (相談 A N5、裁定どおり記録のみ)。

## 7. 変異 matrix (独立 clone D1009、main = `00d781372`、計算ノード dispatch、`test_check_ai_provenance.py` 単独走)

spec は exact な `old`/`new` 文字列で登録し、各 `old` の出現数 1 を親と焦点再レビューが確認した (`mutation/mutation-spec-probe-v2.json`、`mutation/mutation-spec-final.json`)。

| ID | 変異 (置換対象行) | probe の観測 (失敗 node) | final |
|---|---|---|---|
| M-1 | `if source != {"kind": "absent"}:` → `if False:` (実在 entry も外す) | KILLED、12 node (`test_additional_attribute_sources_fall_back[untracked/nested/modified]`、symlink 2、candidate_directories 2、T-pos-2、T-neg-1/2/3/6) | §7.1 |
| M-2 | 同行 → `if True:` (absent 再包含) | KILLED、1 node = T-pos-1 | §7.1 |
| M-3 | 同行 → `... and source.get("kind") != "unreadable":` | KILLED、1 node = T-neg-3 | §7.1 |
| M-4 | `for name in paths.split(b"\0"):` → `for name in ():` (履歴由来候補を落とす) | KILLED、2 node = T-neg-1 + T-neg-6 (理由は同一: 履歴由来候補の欠落) | §7.1 |
| EQ-1 | `return tuple(sorted(attribute_paths))` → `sorted(set(...))` (等価) | SURVIVED (期待どおり、harness の SURVIVED 検出の正例) | §7.1 |

baseline PASSED (rc 0、48 秒)。probe 走は全件 SURVIVED 期待で観測 node を集める型なので summary は `MISMATCH 4 / SURVIVED 1` と出る (kill の観測)。
M-1 の所要 1,037 秒は dispatch の queue 待ちを含む (runner 自身の所要ではない)。

### 7.1 final 走 (期待 node = probe の観測集合、完全一致だけ KILLED、22:55〜23:04)

spec sha256 `e04dd9cb…` (`mutation/mutation-spec-final.json`)、repo_head `00d781372`。**baseline PASSED (rc 0、53 秒)、M-1〜M-4 = 4/4 KILLED (`matches_expectation` true、
失敗 node は probe の観測集合と完全一致: 12 / 1 / 1 / 2)、EQ-1 SURVIVED (期待どおり)、MISMATCH 0、summary `matching 5 / registered 5`。**
各変異の runner 所要 43〜58 秒 (dispatch 側の report)。要約 `mutation/mutation-{probe,final}-results.summary.json` (artifact 全文を除いた写し、生 JSON は job dir)。

## 8. 実測

### 8.1 E-1: attributes 束縛単独の隣接失効数 (同一 commit 列)

probe `t2803_receipt_attr_cold_rate.py` (Codex author 作、job dir `probe/`、repo 外実行) — 独立 clone `rate-source` (local main f94b61fc8 を clone) で
first-parent 直近 61 snapshot (60 遷移、初回は別計上) を古い順に checkout し、**同一 checkout** で旧 checker (`f94b61fc8:tools/check_ai_provenance.py`、
sha256 `7c02fb2d…`) と新 checker の `_attribute_fingerprint` を評価、隣接 digest の不一致を数える。新形の判定は実装の関数をそのまま呼ぶ (再導出なし)。

| 走 | 新 checker | 旧 不一致 | 新 不一致 | 新 dir 導入遷移 | dir 削除遷移 | `.gitattributes` 変更遷移 |
|---|---|---|---|---|---|---|
| e1-1 (初版、包含検査込み) | `1acbb496…` (4c532aa0b の file) | 25/60 | 0/60 (包含違反 0) | 25 | 0 | 0 |
| e1-2 (最終) | `2b72e1d5…` (00d781372 の file) | 25/60 | **0/60** | 25 | 0 | 0 |

読み方: **attributes 束縛単独の失効指標**であり、実監査の cold 率・land wall・時間短縮率ではない。他の束縛 (checker sha、registry manifest、CAB hit、環境 partition)、
partition の差、受領証の探索は測っていない。旧 25/60 は起点の「新 dir 導入率 50 %」の流用ではなく旧関数の実測値。生データ `measurements/e1-{1,2}.json`
(遷移ごとの行、両 checker の sha256、環境、git config)。

### 8.2 E-2: 実機正例 (独立 clone、新 checker、受領証 store は clone の `.git` 配下)

`rate-source` を wave tip `00d781372` (checker sha256 `2b72e1d5…` = wave worktree と一致) へ移し、正規経路 `python3 tools/check_ai_provenance.py`
(login pegasus02、headroom → bounded local) を走らせた。所要は `/usr/bin/time -v` の値 (`measurements/e2-*.time`)。

| 走 | 状態 | rc | 監査件数 | wall | CPU (user+sys) | 受領証 (走後) |
|---|---|---|---|---|---|---|
| cold | tip A、store 空 | 0 | 12,062 | 58.35 秒 | 108.4 秒 | 1 |
| warm (同 tip) | tip A、index に新 dir の file を staged (commit 失敗の副産物) | 0 | 12,062 | 23.43 秒 | 9.4 秒 | 1 |
| warm2 | tip B = A + 新 directory 導入 docs-only commit (`bc9d8a0d9`) | 0 | 12,063 | **21.91 秒** | **9.5 秒** | 2 |
| attr-cold | tip B、root `.gitattributes` に 1 行追加 (uncommitted) | 0 | 12,063 | 62.60 秒 | 96.4 秒 | 2 |

読み方: 公開出力は不変 (受領証の再利用は stdout に現れない) ので、再利用の証拠は CPU (108 → 9.5 秒) と受領証 file の増加 (tip B の受領証が発行された) である。
warm の 22 秒は候補列挙 (履歴 merge の diff、§9) を 2 回含む。load 6〜14 の login 1 回ずつの値で、一般の wall・混雑時・計算ノードの値ではない。
`.gitattributes` を戻した後の clone は tip B のまま (land しない)。

### 8.3 候補列挙の費用 (login pegasus02、wave worktree、S = policy..HEAD の merge 4,369 件、観測 21:50〜22:10、load 9〜16)

| 方式 | wall | 出力 | unique path / 祖先 dir |
|---|---|---|---|
| `diff-tree --stdin -m` (全親) | 6.88 秒 (2 回目 5.71) | 36.2 MB | 40,569 / 3,813 |
| `diff-tree --stdin -c` (全親から変わった path = `--cc` 候補そのもの) | 6.82 秒 (2 回目 5.30) | 235 KB | 347 / 69 |
| `diff-tree --stdin` の merge 第 1 親 pair | 2.17 / 2.44 / 1.90 秒 | 22.9 MB | 36,359 / 3,704 |
| `git log --merges --diff-merges=first-parent ... policy..HEAD` (graph walk) | 5.89 / 6.05 秒 | 22.8 MB | 36,359 (pair 版と完全一致) |
| **`git log --diff-merges=first-parent --no-walk=unsorted --stdin ...`** (採用) | 3.48 / 1.73 秒 | 22.8 MB | 36,359 (完全一致) |
| `rev-list --merges policy..HEAD` | 0.52〜0.65 秒 | — | 4,369 merge |

`-c` は候補そのものだが「全親から変わった path」の git 側の定義と checker の交わりの一致を証明していないので、上位集合が自明な第 1 親 diff を採った。
script は job dir `time-*.sh` (親作、read-only の計測)。数値はこの login 1 回ずつの値。

## 9. 限界と言わないこと

- `attr.tree` / `--attr-source`、bare、`GIT_ATTR_*` の全経路、errno の揺れは従来どおり (相談 A N1 / N3)。
- 受領証時点で候補外だった dir の untracked `.gitattributes` が監査に効く経路は、最終形では「監査対象 merge の path の祖先」が候補に入るので閉じるが、
  候補列挙は第 1 親 diff の上位集合であり `--cc` 候補の定義そのものではない。
- 候補列挙は merge 数に比例して増え (4,369 merge で 1.7〜3.5 秒)、lookup と publish の 2 回走る。warm 走の wall 22 秒のうち何秒かは未分離。
- E-2 は login 1 回ずつ、E-1 は 60 遷移 1 列。混雑時・計算ノード・実 land の連鎖は未観測 (実 land は改訂直後 checker sha が変わるので cold)。
- 「50 % → 0 %」は attributes 束縛の隣接失効数の比であって時間短縮率ではない。
- 既存テスト 2 本が absent 候補差への感度を失う点は記録のみ (期待値不変)。

## 10. 事故 (自分起因) と近接失敗

- **走行中 commit (F558 の同型再発):** 単独走 focus-7 (計算ノード dispatch) の走行中に wave worktree で fix commit を作り、実 repo HEAD を読むテスト 23 件が
  `known provenance violation data HEAD changed while loading: start=4c532aa0b end=00d781372` で赤。固定 tip で focus-8 を再走 (555 passed)。損失は
  単独走 1 本 (約 1 分)。failures fragment に F558 の再発として追記。
- **E-2 の commit 失敗:** 独立 clone に author identity が無く newdir commit が失敗したまま warm 走を投げた (同 tip・staged の走として §8.2 に残す)。
  identity は clone の config に書くと環境 digest (`git config --list`) が変わり partition が別になるので、`git -c user.name/email` で commit だけに与えた。
- **既存 argv 接頭 pin との衝突 2 回 (fix2 / fix3):** 既存テストが D2169 (`diff-tree --stdin`) と D2033 (`log --no-walk=unsorted`) の batch を argv 接頭で識別しており、
  新しい git 呼び出しが誤って数えられた。実装子 prompt の検査項目に「同 file の既存 subprocess argv pin を列挙し接頭が重ならないこと」を足す (dev-wave 改善候補、段 8)。

## 11. 裁定パッケージ候補 (起票しない、scope 外)

- 候補列挙の拡張 (`attr.tree` / `--attr-source` の束縛、bare) — 相談 A N1。
- errno の正規化 — 相談 A N3。
- 候補列挙結果の 1 走内 memo 化 (lookup と publish で 2 回 → 1 回) — 焦点再レビュー nit N1 の派生。費用 1.7〜3.5 秒 × 1 回分。

## 12. 工数

codex 8 本 (gpt-6-astra / medium): consult 1 (5 call、226 秒)、author 1 (13 call、379 秒)、review 2 (6 + 7 call)、fix 3 (10 + 6 + 6 call)、focus 1 (7 call)、計 60 call。
計算ノード job: 焦点走 7 (focus-1/2/3/5/6/7/8) + 変異 probe 6 走 + final 6 走。login 走: full 監査 1、E-1 2、E-2 4、費用計測 script 5。

## 13. 再現資料 (job dir、repo 外)

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/` — codex prompt / 出力 / patch (`codex/`)、probe (`probe/`、Codex author 作)、
独立 clone `rate-source` (E-1 / E-2) と `mutation-source` (変異)、launcher と計測 script (`*.sh`、親作)、変異 spec / results JSON、E-1 / E-2 の生ログ。
本 insight の写し: `reviews/` (codex 出力 8 本、`s6-focus1.md` は行末空白を可逆正規化 — `verbatim-normalization.json`)、`verbatim/` (brief・裁定 3 本・prompt 8 本・起点)、
`measurements/` (E-1 JSON / log、E-2 と full 監査の time / log)、`mutation/` (spec 2 本)。
