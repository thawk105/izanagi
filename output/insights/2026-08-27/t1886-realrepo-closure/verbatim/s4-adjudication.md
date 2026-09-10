# 段 4 裁定と plan v2 — [T-1886] / [T-1936]

親が段 2 plan、段 3 の 2 レンズ、および親自身の実測をもとに裁定した。

## 0. 最大の裁定 — [T-1886] は本 wave で実装しない

**判定: real。ただし本 wave の実装対象から外し、ユーザー裁定へ返す。**

理由は 3 つで、いずれも裁定 (D1035, 2026-08-26) の時点では見えていなかった事実である。

1. **単一 `real-repo` 直列鎖は実行時に存在しない。** `conftest.py:1812-1814` が
   collection の最後に、process memo 4 本を除く全 real-repo node から `@real-repo` suffix を
   除去する。xdist 3.8.0 の `LoadGroupScheduling._split_scope` は suffix の無い nodeid を
   full nodeid scope として扱うので、残りは 1 node = 1 work unit になる。
   既存テストの docstring も
   `Historical name: only the four process-memo nodes remain one work unit`
   と明記している (`test_acceptance_schedule_order.py:722`)。
2. **T-1886 が求めた細分化は D1008 (2026-08-26) が既に実装済みで、D1103 (2026-08-27) が
   実測している。** D1008 は「73 node の全対全排他をやめ、資源別 reader/writer lock と
   suffix 除去へ置き換える」と決定し、対象 21 node で直列 145.79 秒 対 並列 54.83 秒を実測している。
3. **親が因果的に実測した。** ledger 合計 266.32 秒の 90 node 集合を
   `tools/run_tests.py` 経由で走らせた (Pegasus 自動 dispatch、request `951549.nqsv`、rc=0)。
   **52 passed / 41 skipped、pytest wall 74.91 秒。** 総和の 3.6 分の 1 で終わる。直列鎖ではない。
   (先行 arm の raw pytest `-n 48` は rc=137 で controller が殺されたため値を使わない。)

**T-1886 の 210.5 秒 / 258.92 秒 / 266.32 秒はいずれも「marker が付いた node の所要の総和」であり、
直列鎖の長さでも wall 短縮量でもない。** D600 と D1052 がまさにこの型を禁じている。

`DW-S04` に従い、**親は承認済み裁定を不採用にしない。** 新事実を添えてユーザー再裁定へ返す
(下記 §5-C1)。

## 1. [T-1936] は実装する — これが本 wave の成果物

閉包の穴は brief の 3 点では閉じない。段 2 と段 3 が 3 点を追加した。**実装対象は 6 点**である。

| # | 穴 | 判定 | 実装方針 |
|---|---|---|---|
| H1 | T810 live-authority 3 node が無 lock で親 common-dir の linked-worktree registry を読む | real (親も独立確認) | `RealRepoAccess("read", None)` で access map へ登録 |
| H2 | 実親 object を書く session fixture 2 系統が登録外 | real | fixture 所有 lock。setup 中は parent EX、生成後に parent SH を取り直して `yield` |
| H3 | `repository_scan` fixture が登録外 | real | fixture 所有 lock。**access は `("read","read")`** (下記裁定 1-3) |
| H4 | lock key が worktree root 由来で sibling worktree を排他しない | real | Git common-dir 由来へ。**移行期は旧 key も併取** (裁定 1-4) |
| H5 | `current_commit_snapshot` module fixture が登録外 (段 2 が追加発見) | real | fixture 所有 parent SH |
| H6 | suite 全体を subprocess collect する 2 node が登録外 (段 3 レンズ A が追加発見) | real | parent SH reader として登録 |
| H7 | controller prewarm 2 系統が node protocol の外で実 repo resolver を動かす (レンズ A) | real | 実 `prewarm_*` 呼出しを parent SH 内へ入れる |

### 裁定 1-3: `repository_scan` の access は `("read","read")` にする

レンズ A は「scanner が `external/ccbench` を読むなら CCBench writer と排他されない。
射影外なので衝突は未確定」と報告した。**未確定を未確定のまま残さない。**
SH は reader 同士を直列化しないので、`ccbench="read"` を足す費用は実質ゼロである。
「読まないことの証明」を待つより、安全側の 1 行を入れる。

### 裁定 1-4: lock key の移行は両取りにする

レンズ A #6 が指摘したとおり、worktree-root hash から common-dir hash へ**切り替える**と、
移行期に旧コードの session と新コードの session が別 lock file を取り、互いを排他しない。
**旧 key と新 key の両方を、常に (旧, 新) の固定順で同じ mode で取得する。**
順序を固定するのは deadlock を作らないためである。
旧 holder が新 acquisition を阻止することを回帰テストで固定する。

## 2. 段 2 plan の最大の設計判断を却下する

**却下: 長寿命 fixture 15 本を canonical `real-repo` group へ統合する案。**

親が費用を実測した (ledger、instance 正規化後)。

- `s8c-preregistration-candidate` group = 83.5 秒 (named 5 本)
- `s8c-predicate-snapshot` group = 52.0 秒 (3 本)
- campaign scan の consumer 6 本 = 0.09 秒

**現在この 2 group は別 worker で並行に走る (critical path = 83.5 秒)。統合すると
1 worker 上の直列鎖 135.6 秒以上になる。** これは

- D1035 が選んだ方向 (細分化) と逆であり、
- 「全体 5 分が絶対上限」の余裕を半分近く食い、
- D1103 が実測した最遅 shard の pytest wall 160.92 秒へ +52 秒を乗せる。

**代わりに採る案 (plan v2):**

1. **長寿命 fixture ごとに loadgroup を 1 つ持つ。** 既存の
   `s8c-preregistration-candidate` と `s8c-predicate-snapshot` はそのまま残す。
   `repository_scan` の consumer 6 本には**新しい group を 1 つ足す**
   (現在は group が無く、worker ごとに fixture を払っている)。
2. **`tools/acceptance_shards.py` に「衝突辺」の集合を明示的に足し、
   衝突する group 名を同一 shard component へ union する。**
   shard は別 process・別 host で走りうるので、`/tmp` の flock は shard を跨いで効かない。
   衝突する仕事は必ず同じ shard に入れる。**loadgroup 名は分けたまま**なので、
   同一 shard 内では従来どおり別 worker で並行に走る。
3. これでレンズ B #6 の懸念 (別 group が別 shard・別 host へ行くと flock が届かない) を、
   直列鎖を作らずに閉じる。

`tools/acceptance_shards.py` は blob 束縛されていないので変更してよい
(land が blob 一致を要求するのは `tools/run_tests.py` と `tools/dev_wave_wait.py` と判定器だけ。
`tools/dev_wave_land.py:1065-1087` を現物で確認済み)。

## 3. 新設検査の設計 — 恒真化を防ぐ 3 条件

レンズ A #3 が「全対象に同じ marker を付ける設計では、衝突 pair は marker だけで
同一 component になるので gate がほぼ恒真。さらに conflict matrix から辺を消すと
検査対象自体が減るので変異が殺されない」と指摘した。**採用する。**

- **(C1) 衝突辺の独立 exact golden を持つ。** golden は実在の fixture 名・consumer node・
  resource/mode の literal から書き、`conflict matrix == golden` を**先に**検査する。
  その後に component 検査と実 flock の競合検査を行う。
  golden を matrix 自身から導出してはならない。
- **(C2) 正例は実在の呼び先を名指しする** (レンズ A #5)。
  `repository_candidate_commit` / `repository_scan` / `current_commit_snapshot` の
  実 fixture を実行し、builder / read / yield / teardown が期待した lock context の中に
  居たことを記録する。helper を作って helper を検査する形にしない。
- **(C3) fixture 集合と resource node 集合が素であることを検査する。**

## 4. 変異事前登録 (DW-M01)

実装後に親が走らせる変異。parametrize id は ASCII のみ。

| id | 変異 | 殺す nodeid |
|---|---|---|
| `t810-live-reader-unregistered` | access map から T810 の 1 本を削除 | `test_real_repo_serialization.py::test_real_repo_closure_mutations[t810-live-reader-unregistered]` |
| `invariant-candidate-write-downgraded` | invariant candidate fixture の setup mode を `write` から `read` へ | 同 `[invariant-candidate-write-downgraded]` |
| `predicate-candidate-lock-removed` | predicates candidate fixture から lock context を除去 | 同 `[predicate-candidate-lock-removed]` |
| `campaign-scan-lock-removed` | scan fixture の lock を `nullcontext` へ | 同 `[campaign-scan-lock-removed]` |
| `parent-key-uses-worktree-root` | common-dir 解決を repo root 返却へ | 同 `[parent-key-uses-worktree-root]` |
| `legacy-key-not-acquired` | 移行期の旧 key 併取を外す | 同 `[legacy-key-not-acquired]` |
| `conflict-edge-removed` | shard 衝突辺から candidate-writer 対 parent-reader を削除 | 同 `[conflict-edge-removed]` |
| `prewarm-lock-removed` | controller prewarm の SH を外す | 同 `[prewarm-lock-removed]` |
| `nested-collection-node-unregistered` | suite 全体 collect の 2 node を access map から外す | 同 `[nested-collection-node-unregistered]` |

各変異について実装子は、**同じ入力を拒否する層が前後に無いこと**と
**無効化時の赤理由が 1 つに絞れること**をコードで確認し、報告する。
確認できない変異は登録せず、実効 gate へ再照準する。

## 5. scope 外だが real — ユーザー裁定へ返す

- **C1: [T-1886] の退役。** D1008 / D1103 で先行達成しており、本 wave に新規の性能介入は無い。
  台帳から落とすか、別の具体的操作を新たに裁定するかを決めてほしい。
  上記 §0 の実測 (74.91 秒 対 総和 266.32 秒) が根拠である。
- **C2: D358(a) の未抑止 Git 経路。** real-repo node から `GIT_OPTIONAL_LOCKS=0` 無しで
  起動される git が 6 family 残る (`test_s8b_protocol_builder.py:70-80`、
  `s1_known_axes_freeze.py:186-193`、`s1_measurement_freeze.py:104-113`、
  `test_sort_swo_oracle.py:725-733`、`tools/codex_reasoning_ab.py:428-453,3598-3611`、
  S8C writer 群)。
  **本 wave では直さない。** 理由は (a) これは D1008 が出荷した設計の既存性質であって
  本 wave が作る欠陥ではないこと、(b) `test_s8b_*` は稼働中の t1805 wave の編集面であること。
  選択肢は「(A) 全 live Git 経路へ抑止を入れて T-1936 を拡張する」か
  「(B) D1008 が D358(a) を supersede したとして受容する」の二択。
- **C3: cross-host / 別 invocation の排他。** `/tmp` の flock の保証は同一 host・
  同一 filesystem までである (D1008 が逐語で射程を限定している)。
  並行 acceptance を別 host で許す運用のままにするか、共有 filesystem lock または
  worktree 隔離へ進むかは別裁定。

## 6. 不変条件 (実装子はこれを破ってはならない)

- **`tools/run_tests.py` を 1 byte も変更しない。** D838 により land が拒否される。
- 既存テストの期待値を反転・緩和・skip・削除しない。
- 直列鎖を新しく作らない。長寿命 fixture group を統合しない (§2)。
- テストの削除・skip・selection 縮小で速くしない。
- 受理集合を指示外に広げない。

## 7. 親の provisional 裁定の決着

- P1 **反証**。細分化は既に実装済み。新規介入は無い。
- P2 支持 (process memo 4 本と writer 4 本は互いに素)。
- P3 採用。ただし移行の両取りを足す (裁定 1-4)。
- P4 **不十分**。fixture 所有 lock + scope 縮小 + shard 衝突辺まで要る。
- P5 支持 (suite 内に親 registry の writer は無い)。T810 は parent SH。
- P6 **反証**。D358(a) は生存 (§5-C2)。(c) は「重複は存在するが、wall 悪化という却下理由は
  D1008 が実測で退役させた」と分けて記録する。
- P7 修正。性能 A/B は成果条件から外す (§0 で T-1886 を実装しないため)。
  §0 の 74.91 秒は「直列鎖ではない」ことの反証実測であって、wall 短縮量の主張ではない。
- P8 **修正**。`tools/acceptance_shards.py` は変更する (§2)。
