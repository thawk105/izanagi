# [T-2533] T-1998 balanced stock-inline 対の事前登録を実値つきで新設し、consumer の受理条件へ束縛した

- 日付: 2026-09-10
- wave: `worktree-dev-wave-t2533-t1998-prereg-digest`
- 基準 commit: `7f17e1c63` (着手直前の local main)
- authority: none — 本書は設計判断と実測の索引であって、性能の測定原典ではない。
  **本 wave で性能測定は 1 回も走らせていない。**
- 一次資料: `docs/decisions.md` の D1874 / D1790 / D1244 / D1267 / D1525、
  `docs/t1998-balanced-stock-inline-preregistration.md` (本 wave で新設)、
  `output/insights/2026-09-08_t1998-stock-inline-parts/README.md`、
  `output/insights/2026-09-09_t2354-a5-prune-removal/README.md`。

## 0. 何を求められていたか、何をしたか

依頼は「T-1998 の事前登録を、着地後の A-5 job body digest `dff913cb…7aecd8` で作り直す」だった。

**repo 内に T-1998 の事前登録は存在しなかった。** 旧 digest `0ef4d41e…` の hit は過去の
submit / reservation 記録と insight 逐語だけで、live な事前登録は 0 件である
(`2026-09-08_t1998-stock-inline-parts/README.md` §6 が「実値を確定していない」と明記している)。
したがって依頼文が指示した「凍結済みの事前登録を erratum で直す」手順は**発火しない**。
新規作成として作った。

**D1874 (2026-09-09、ユーザー裁定) が正式測定を既に認可している。** 実値を固定することが
認可の前提条件であり、本 wave はその前提条件を満たした。**測定そのものは起動していない。**

## 1. 依頼文の理由付けの誤り (訂正)

依頼文は「旧 digest を指す事前登録のままでは A-5 の別 boot 再取得を開始できない
(A-5 は現在 0 件で、論文の但し書き 3 が外れない)」を理由に挙げていた。**これは一次資料と矛盾する。**

- **D1525 (2026-09-03、ユーザー裁定)** が「A-5 は Pegasus では充足しない。未充足のまま残し、
  その旨を成果物へ明記する」と確定している。元の値は cygnus で取られており、Pegasus で回すと
  「別の起動」と「別の環境」が同時に変わって交絡する。
- 後続の裁定でも「A-5 は再投入しない」と決まっている。

**digest を直しても但し書き 3 は外れない。** 本 wave が閉じたのは別の穴 (D1874 が認可した
stock-inline 対の事前登録) である。成果物は変わらないので、訂正を明示したうえで本題を進めた。

## 2. 親が実測で自分の誤りを 1 件訂正した — target の source digest

段 1 で親は `source_digest.resolve_evidence(genome, "511c953", cxx="g++")` を login node で呼び、
arm 別 source digest を測定なしで先に計算できることを確かめた (DW-G01)。この値を brief と
段 2 plan へ載せた。

**段 3 のレンズ A が「その値は正式 producer が記録する値ではない」と指摘し、real だった。**

- `backoff_sweep.py:410-411` は campaign 全体を
  `patchharness.applied("patches/silo-backoff-fixed.patch", CCBENCH_COMMIT)` の内側で走らせる。
- build 証拠はその状態から解決される (`loop.py:627-630`)。
- 親の probe は patch 未適用の作業木で計算していた (`tracked_clean=true`、`src_token="stock"`)。

親が patch 適用下で測り直した結果:

| arm | patch 未適用 (誤り) | patch 適用下 (正) |
|---|---|---|
| baseline | `2d691b45…a2c6` | `2d691b45…a2c6` (**同値**) |
| target | `6454d9f34b…` | **`678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12`** |

baseline が変わらないのは、patch が `BACKOFF_FIXED` 負値で stock 枝を選び前処理後ソースが原本と
同一になる (inert) 設計だからである。target だけが変わり、`src_token` も合成 token になる。
生出力は `source-digest-unpatched.json` (誤り・参考) と `source-digest-patched.json` (正本)。

**この誤りは、事前登録に載せたまま正式測定を打っていたら `source-identity-unbound` で
全件拒否され、T-1998 の適格値が 1 本も得られないところだった。**

## 3. 段 3 が突いた本体 — 事前登録が受理集合を束縛していなかった

段 2 のプランは「文書を作り、loader を置き、consumer へ渡す」形だった。
**2 レンズが独立に、その形では canonical 文書を 1 度も読まずに consumer を通せることを突いた。**

- consumer の署名は `preregistered: T1998PreregisteredIdentity` を受け取るだけで、
  loader を通ったかどうかを検査しない。
- 呼び手は結果を見た後に成果物から identity を写して手組みできる。
- `repository_commit` は呼び手が渡す期待値なので、成果物と突き合わせても恒真になる。

**段 4 はこれを 1 つの機構で閉じた。** consumer が、既存の artifact 比較をすべて通した後、
`ratio` 計算の直前に次の 3 つを要求する。

1. 作業木の事前登録文書の sha256 が `CURRENT_PREREGISTRATION_SHA256` と一致する。
2. 成果物が記録する `repository_commit` における文書 blob の sha256 が
   `MEASUREMENT_TIME_PREREGISTRATION_SHA256` と一致する。
3. **その measurement blob から**導いた identity が、渡された identity と
   `repository_commit` を除いて完全一致する。

これで `repository_commit` も一意に閉じる。呼び手は任意の commit を渡せない — その commit の
文書 blob が pin 定数に一致しなければ拒否されるからである。

### D1790 の 2 定数をどう割り当てたか

D1790 の逐語は「成果物が記録しているべき事前登録 sha (測定時点の版)」と「解析規則の正本として
渡される文書に要求する sha (現行の版)」を別定数にせよ、である。
段 2 plan と段 1 brief は前者を **job body sha** に読み替えていたが、**それは逐語と違う**と
2 レンズが独立に指摘した。T-1998 の producer は事前登録 sha を成果物へ書かない (schema 拡張は
D1244 の最小 3 部品の外) が、**成果物は `repository_commit` を記録している**ので、
測定時点の文書はそこから一意に復元できる。上記 2 と 1 がその 2 定数である。

**v1 では両者が同値になる。それは正しい状態であり、「値が異なること」を要求する検査は置かない。**
文書を改訂すると解析規則側だけが動き、v1 の下で測られた成果物は成果物側の定数で引き続き解析できる。
互換層は作らない (D1790 の逐語)。

## 4. 段 6 が実装の 4 点を差し戻した

親の焦点走 4 file は 69 passed で緑だったが、段 6 の敵対レビュー 2 本は**その緑が通っていない
入力**を現物で構成した。

1. **identity を測定時点の blob ではなく現行文書から作っていた** (レンズ A)。段 4 裁定の指定と
   違い、2 版が分かれた後に測定時点の事前登録が登録していない identity を受理しうる。
2. **`GIT_DIR` / `GIT_OBJECT_DIRECTORY` / `GIT_ALTERNATE_OBJECT_DIRECTORIES` などで
   `git show` の参照先を別 repository へ差し替えられた** (レンズ A)。canonical 文書を持つ
   別 repo を用意すれば束縛を通せる。`patchharness.py` の `_read_only_git_env()` が同型の先例。
3. **新しい `subprocess.run` 2 箇所が process 起動の exact 台帳に未登録だった** (レンズ B)。
   **親が実走して 2 failed を確認した** —
   `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact` と
   `::test_reviewed_ccbench_measurement_launches_use_bounded_sites`。受入で落ちる回帰だった。
   **親の焦点走の対象集合にこの層が入っていなかった。** module 名の grep では出ない。
4. **3 gate のうち 3 つが単独では殺せなかった** (両レンズ)。とくに measurement sha 比較は、
   「文書が存在しない commit」の負例では blob 取得失敗の分岐で先に止まる。
   「文書は在るが bytes が違う commit」でないと sha 比較の証拠にならない。

4 件すべてを閉じた。4 のために consumer へ keyword-only の `repo_root` を足した
(既定は現行どおりで、受理集合は広がらない — 文書の sha が pin 定数に一致しなければ拒否される)。

## 5. 変異 matrix

事前登録 9 件。spec と report は `mutation/` に置いた。

| 走行 | spec | report | 結果 |
|---|---|---|---|
| probe | `mutation-probe-spec.json` | `mutation-probe-report.json` | baseline PASSED / MISMATCH 8 / SURVIVED 1 |
| 本走 | `mutation-main-spec.json` | `mutation-main-report.json` | **baseline PASSED / KILLED 8 / SURVIVED 1 / MISMATCH 0・期待 node 完全一致 (9/9)** |

probe は観測 node を集めるため全件 SURVIVED 期待で登録した。MISMATCH は probe としては正常である。

**帰属は単一理由で成立した。** m1 / m1b / m2 / m3 / m6 / m8 はそれぞれ専用テスト **1 本ずつ**で
殺されている。m4 / m5 は事前登録文書の値を変える変異なので、正例 9 本が同時に落ちる。

### 登録した SURVIVED 1 件 (m7)

`CURRENT_PREREGISTRATION_SHA256 = MEASUREMENT_TIME_PREREGISTRATION_SHA256` へ統合する変異は
**期待どおり SURVIVED した。** v1 では両者が同値なので等価変異であり、
**「2 定数の値が異なること」を要求する検査は D1790 に反するため置かない。**
D1790 が禁じるのは同一定数への統合と複数版 allowlist であって、初版で値が一致することではない。
静的な統合を検出する検査は本 wave の依頼の外なので足さなかった。**この限界は主張しない。**

## 6. 検査

- 焦点走 (fix 前、4 file): **69 passed** (dispatch、request 988697.nqsv)
- 焦点走 (fix 後、5 file): **116 passed**
- `test_ccbench_spawn_sites.py` 単独 (fix 前): **2 failed, 42 passed** — レビュー B の指摘の実測
- 変異本走: baseline PASSED (83 passed)、KILLED 8 / SURVIVED 1 / MISMATCH 0
- 受入全走 attempt 1: **9 error + 1 failed / 22,318 passed** — 下記のとおり非帰属
- 受入全走 attempt 2: **22,348 passed / 68 skipped、rc=0 (`child-green`)**、
  claimed main `693c915b64da0dd58c25351777620398774af3a1`
- `python3 tools/check_docs.py`: rc=0
- `python3 tools/check_ai_provenance.py` (全監査): **9288 件、新規違反なし**
- `git diff --check`: rc=0

### 受入 attempt 1 の赤 10 件は変更に帰属しない

落ちたのは `test_t1259_qsub_env_delivery_probe.py` の 9 件 (setup error) と
`test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` の 1 件で、
いずれも本 wave の変更面 (t1998 consumer / spawn sites / docs) の外である。

**同じ木で 2 file を単独走させると `test_t1259_qsub_env_delivery_probe.py` は全件 passed になり、
`test_codex_worker_launch.py` は別の node (`test_manifest_is_appended_while_correlated_session_is_running`)
が落ちた (261 passed / 1 failed)。** 失敗する node が走行ごとに入れ替わるので、
負荷と並行 codex session に依存する非帰属赤である。受入をやり直して緑を得た。

## 7. 確定していないこと・限界

- **compiler の同一性は証明していない。** arm 別 source digest は login node の `g++` で導いた。
  計算ノードの `g++` が同じ前処理結果を与えることは示していない。版はどちらも GNU 11.4.0 だが、
  版の一致は header 閉包の一致ではない。食い違えば `source-identity-unbound` で fail-closed に
  落ちる。**偽の緑は生まれないが、そのときは測定が成立しない形で現れる。**
- **consumer を呼ばずに人が数値を主張する経路は塞いでいない。** 閉じたのは consumer を通る解析だけ。
  production の CLI / submitter への loader 不可避化は scope 外。
- **producer schema は拡張していない。** 成果物が事前登録 sha を直接記録する方が強い束縛になるが、
  D1244 の最小 3 部品の外である。
- **正式測定は 1 回も走らせていない。** 認可は D1874 が与えており、投入は人間手番。
- **A-5 (論文の但し書き 3) は未充足のまま。** D1525 により Pegasus では充足しない。

## 8. 逐語の erratum

`verbatim/s2-plan.md` の 2 箇所に、job body digest の**壊れた literal** がそのまま残っている
(`dff913cb1044858bilho6f25721f2d0aac…` と `dff913cb104485_CTX8b56f25721f2d0aac…`)。
段 2 の子自身が直後の行で正しい 64 桁を書き直しており、親は値の正本を job dir へ別途置いて
実装子と段 3 / 段 6 の子へ射影した。**逐語は当時の出力のまま保存する (書き換えない)。**
正しい値は `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` である。

## 9. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **正式経路への loader 不可避化。** consumer を通る限り抜け道は無いが、
   「consumer を呼ばずに主張する」経路は塞いでいない。どの entry point を正式経路とするかは裁定が要る。
2. **producer schema へ事前登録 sha を書くか。** 今回は `repository_commit` 経由で復元する形で
   閉じた。成果物が直接記録する方が強い。
3. **login と compute の compiler identity の証明。** 現状は fail-closed に頼っている。
4. **正式測定の投入。** D1874 が認可済みだが、投入は人間手番として返す。
