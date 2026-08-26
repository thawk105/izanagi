---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-ccbench-pin-precheck-20260827
seq: 1
title: CCBench pin 前進の影響範囲を実測し、択一をユーザー裁定へ返した (実装差分ゼロ、branch worktree-dev-wave-ccbench-pin-precheck-20260827、変異 matrix = 免除 (実装面の差分ゼロ、D95 決定 2))
---

## 本文

CCBench submodule の pin (`511c9538`) を上げた場合の影響範囲を実測する precheck wave。
**izanagi の pin は 1 bit も動かしていない。** pin を進めた測定はすべて job dir の
使い捨て clone の中だけで行った。裁定パッケージと実測記録は
`output/insights/2026-08-27_ccbench-pin-precheck/` に置いた。

依頼の前提が 2 つ実測で覆った。

- 「上流 master から 3 本ぶん古い」は誤り。pin は master の**祖先ではない**
  (分岐点 `7e268f2a`、`511c9538..master` = 16 commit、`master..511c9538` = 8 commit)。
  pin は izanagi 専用 branch `izanagi-trace-pin-t816` の tip である。
- master には izanagi の TRACE 計装が一切無い (`cc/silo/` に "trace" を含む file が 0 件、
  `include/trace.hh` 不在、`Options.cmake` から `CCBENCH_TRACE` と `TRACE=${CCBENCH_TRACE}` が消える)。
  よって「master 直行」は絶対規律 1 (D14) と規律 3 の土台を壊すため択一から落ちる。

**最大の発見 (親が段 1 で完全に見落とし、段 3 の敵対検証が露出させた)。**
PR #121 が `cc/ss2pl/CMakeLists.txt` の option を literal `DLR1` から CMake 変数
`${SS2PL_DLR_MARKER}` へ変えており、`orchestrator/campaign/source_digest.py` の静的 CMake
parser がこれを解決できず fail-closed で止まる。正例つき実測: 現 pin では
`_assert_proven_repo_absent_macros()` が `frozenset({'MQLOCK'})` を返して緑、取り込み後は
`RuntimeError`。この走査は D297 の pin 前進 gate
(`tools/check_trace0_preprocess_identity.py`、実走 rc=1) だけでなく、
`assert_conditional_macros_covered()` 経由で**本番 campaign resolve 経路**からも呼ばれる。
検査を緩める逃げ道は規律 2 に反するため採らない。`CONTEXT_MACROS` は現在 1 個で
2 個以上は機械停止するため、正攻法の修正は組合せ文脈への再設計を要する。

**選択的 backport は成立しない (実測)。** 使い捨て clone で pin へ cherry-pick すると
`b629dc1` (#120) は通るが `df47e3a` (#122) は競合する。#122 は `#if defined(DLR0)` guard を
外すだけの commit で、その中身を入れたのが #121 だからである。**SIGSEGV 修正は #121 を要求し、
#121 は blocker を必ず持ち込む。**

段 3 の敵対検証 (read-only codex 2 本、異なるレンズ) が親の結論を 5 点覆した。親は指摘を
そのまま採らず全件を実測し直した。覆ったもの: (1) D297 gate の存在、(2) 閉包を 40 桁 pin で
検索していたが正本 `CURRENT_PIN` は 7 桁で、7 桁のみを持つ file 23 件を落としていた
(うち独立 golden 6 file・7 箇所)、(3)「reseal が承認定数を照合する」は誤りで照合は別 API に
しかない、(4)「上げないと SS2PL が着手できない」は誤りで study は現 pin + out-of-tree patch で
2026-08-25 に完走済み、(5) MOCC と silo ladder の pin literal は live 束縛ではなく歴史的実験
identity で、更新してはならない (silo ladder は driver・contract・`patches/ledger.json` の 3 者が
exact 比較で一体、という親の在庫表の矛盾も指摘された)。

**依頼の問い (4) への確定回答: 既存 campaign の E1-stale は 0 件。** E1 epoch は
`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の exact 25 path の blob hash だけで決まり、
25 path に ccbench も `pin.py` も含まれない。E1 とは別に `build_admission` の
`repo_stock_pin` が受理条件に入るが、実測では tracked `output/` 配下の `campaign.lock` 32 件の
うち当該 field を持つのは 2 件だけで、その 2 件は既に旧 pin (`d706650`) を記録しており
現行 pin の下でも既に不一致 (歴史 evidence)。**新規に壊れる live campaign は 0 件。**

床値 protocol は pin bump で確定的に落ちる (実測: `current_count=2 head_exact_count=0`) が、
D444 / D471 / D491 に復旧手順が裁定済みで、**再計測は不要** (不変 16 field の byte-exact 継承)。

段 3 第 1 巡は親の prompt が出力見出しを `###` で指示したため `check_codex_output.py` の
`^## 総括` 要求に合わず `f43_fragment` で不採用になった (親の作成ミス)。出力自体は完成して
いたので保全し、prompt を直して第 2 巡を投げ直した。第 2 巡は 2 本とも rc=0。
子の工数は receipt.json にある (第 1 巡 sol: model_calls 45 / cli_reported 296,630)。

pin の可否と独立に、`.gitmodules` の `branch = izanagi-trace` が upstream で `d706650`
(旧 pin) を指しており、`git submodule update --remote` を実行すると pin が 1 世代巻き戻る
latent な不整合を検出した。

親の推奨は「据え置き」。D790 (2026-08-25) が同じ費用を根拠に同じ選択をしており、
本 wave はその費用が実在することを実測で裏づけた。既裁定を覆す新事実は見つからなかった。
最終判断はユーザー裁定へ返す。

## 次の一手差分

### 新規

- {{T:ccbench-pin-ruling}} **P1・ユーザー裁定待ち**: CCBench pin を上げるかの三択
  (A 据え置き / B SS2PL 修正だけ izanagi 側へ / C 条件を満たして取り込み) を裁定する。
  裁定パッケージは `output/insights/2026-08-27_ccbench-pin-precheck/README.md`。
  併せて (a) 案 C を採る場合の `CONTEXT_MACROS` 組合せ文脈への再設計の可否、
  (b) `.gitmodules` の branch 宣言の是正を先行させてよいか、を決める。

- {{T:source-digest-cmake-var}} **P2・新規**: `orchestrator/campaign/source_digest.py` の
  静的 CMake parser が `ccbench_add_protocol(... OPTIONS ...)` の変数参照を扱えるようにする。
  現状は `${SS2PL_DLR_MARKER}` で fail-closed になり、pin 前進と本番 resolve 経路の両方を止める。
  `CONTEXT_MACROS` の 1 個制限に触るため設計裁定を伴う。pin の可否と独立に価値がある。

- {{T:gitmodules-branch-drift}} **P3・新規**: `.gitmodules` の `branch = izanagi-trace` を
  実際の pin を含む tip へ揃える。現状 upstream の `izanagi-trace` は旧 pin `d706650` を指し、
  `git submodule update --remote` で pin が巻き戻る。
