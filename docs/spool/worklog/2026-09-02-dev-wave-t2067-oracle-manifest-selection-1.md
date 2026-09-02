---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2067-oracle-manifest-selection
seq: 1
title: [T-2067] oracle manifest の load-only consumer へ床値選択規則を強制した — 親の「reverify で被覆済み」は偽で、残る未被覆は 3 群でなく増えた (コード + テスト、branch worktree-dev-wave-t2067-oracle-manifest-selection、変異 6/6 KILLED)
---

## 本文

- 依頼は残件 (a) oracle manifest 群への選択強制の実装。D1370 の狭い API を
  `build_approved_manifest` の active 世代読込み直後へ 1 行足し、既存の
  `RatifiedFreezeError` catch がそのまま受ける形にした。production の差分は **1 行**である。
- **親 brief の中核前提が偽だった。** 親は段 1 で「`reverify_published_freeze` は
  `_launch_validate` を通るので oracle report / verdict / oracle judge は被覆済み」と書いたが、
  選択 identity 検査は `result_type is LaunchValidatedFreeze` の条件下にあり、
  historical reverify は通らない。段 3 の 2 レンズが独立に反証し、親が一次資料で追認して
  撤回した。詳細は {{D:historical-reverify-skips-selection}}。
  **この 3 consumer は本 wave では実装せず裁定パッケージへ送る** — 依頼が名指ししたのは
  oracle manifest 群であり、report と judge は manifest の `_GENERATOR_SOURCES` に含まれるため、
  編集すると manifest の generator_versions の byte hash が変わって凍結成果物に波及する。
- **D1241 / D1313 の advisory / non-certifying 上限は解除していない。** 強制点が増えたのは
  実装事実であって主張の水準ではない。現 tree に active な g1 も official な床値も 0 件なので、
  この強制は API を直接呼んだときにだけ効く。「production の最終主張を配線した」とは書かない。
- **段 2 plan の test 追随案を親が却下した。** plan は既存 4 consumer test の合成 freeze を
  `generation_number=2` へ移す案だったが、実 loader では決して成立しない受理集合を test 上に作り、
  g1 の成功被覆を丸ごと失う。既存 4 test は合成 g1 のまま残し、選択 assert を記録 stub にして
  呼出し回数と引数を検査させた。理由は {{D:selection-gate-test-following-keeps-g1}}。
- 段 6 レビュー A の must-fix 2 件のうち 1 件だけ採用した。採用したのは
  「genuine g1 正例が `no-approved-spec` の出所を識別しない」で、例外の cause が
  reviewed spec loader 由来の型であることを固定した。
  **不採用にしたのは「負例が eligibility 導出を stub している」。** 既に landed している
  狭い API 自身の rule-mismatch test も同じ関数を stub しており、被覆は本差分の前後で同一である。
  本 wave が作った穴ではなく、成果物影響を本差分へ帰属できない。裁定パッケージへ送る。
- 段 6 レビュー A は変異事前登録の KILL 帰属も 2 件訂正した。**さらに実測が親の記録を
  1 件訂正した** — レビュー A は M4 (root 省略) が既存 4 test だけを ERROR にすると予測したが、
  probe の実測では genuine g1 の 2 本も落ちて 6 node だった。台帳は実測側を正本にした。
- 変異の検出力で分かったこと: M6 (拒否理由の素通しを定数へ潰す) を殺せたのは genuine g1 の
  負例 1 本だけだった。実 loader と実 callee を通す負例が、拒否理由の保存を担う唯一の検出器である。

### 実測 (親が実走)

- 変異 matrix: anchor `423939266`、baseline PASSED (赤 0)、**KILLED 6 / SURVIVED 0 /
  MISMATCH 0 / TIMEOUT 0**、期待 node 完全一致 6/6。DW-M07 に従い probe 段 (全件 SURVIVED 期待) で
  観測 node を集めてから本走した。spec は
  `output/insights/2026-09-02_t2067-oracle-manifest-selection/` に置いた。
- 変更 test file の単独走: 実装後 104 passed、fix 後 104 passed。
  新規 2 test を名指しで走らせて 2 passed。
- 焦点走 (参照関係で引いた consumer test 12 file): 1046 passed / 8 skipped。
- 受入全走: `child-green`、**19850 passed / 92 skipped**。
  tested_main `9565a09ff`、tested_tip `c44946fbb`。
- AI provenance 全史監査: 実装 commit 後 rc=0、main 取り込み後 rc=0。

### セッション異常

- 受入の初回投入は `prerun-clean` rc=70 で拒否された。親が受入の走行中に spool fragment を
  repo へ書いて作業ツリーを汚したためで、gate の正しい動作である。fragment を repo 外へ
  退避して再投入した。
- fix 子の初回投入は、runner script 内で生の `git submodule update --init` を使ったため
  `transport 'file' not allowed` で失敗し、midflight gate が rc=1 で止めた。
  `tools/dev_wave_submodule_init.py` で初期化し直して再投入した。
- 同 tool は新規 worktree に対する **1 回目の呼出しが必ず `runtime-io-failure` で落ち、
  2 回目で成功する**。本 wave では author 用と fix 用で計 3 回とも同じ挙動だった。
- 起動時の編集面重複検査で、`git worktree list` の各 worktree へ `git status` を
  while ループで回すと git が pipe の stdin を食い、全 worktree を無言で読み飛ばして
  hit 0 件を返した。各 git へ `</dev/null` を付け、既知の編集中 file を対象にした
  正例対照で偽陰性でないことを確かめてから結論した。

工数は子 6 本 (plan 1、敵対相談 2、実装 1、敵対レビュー 2) と fix 1 本。fix の初回投入は
gate で止まったので codex は起動していない。

## 次の一手差分

### 更新

- [T-2067] **P1・一部完了 (設計択一 2 件は D1325 で終端、強制は s8c 床値 verifier / publish と
  oracle manifest まで実装済み)**: 残るのは
  (a) oracle report / verdict / oracle judge への選択強制 — historical reverify は選択 identity を
  実行しないことが本 wave で判明した ({{D:historical-reverify-skips-selection}})。report と judge は
  manifest の `_GENERATOR_SOURCES` に含まれるため、編集すると凍結成果物の bytes が変わる。
  実装するかはユーザー裁定に送る、(b) 「load-only consumer 3 群」という母集合の再確定 — (a) の
  事実により先行 wave の数え方は過少である可能性がある、(c) `build_manifest` / `write_manifest` の
  公開迂回口 — 選択 gate を通さず manifest を構築・保存できる。repo 内の caller は test helper だけで、
  境界を文書で固定するか別 API を設けるかを裁定に送る、(d) 床値選択 eligibility 導出の被覆の穴 —
  実導出を走らせて rule-mismatch を出す test が repo に無く、landed 済みの狭い API 自身の test も
  同じ関数を stub している。「実導出が常に False」の変異は launch 経路でも consumer 経路でも生存する、
  (e) s8c C06 予算群 — C05 schedule authority の着地後に再評価 (D1371)、(f) 起動証明書の実時間性 —
  独立した外部 commitment 無しには閉じられず必要な機構は D1241 が禁じている、
  (g) s8c production final claim 配線 — 前提が連言で不在 (D1371)。
  **いずれも D1241 / D1313 の advisory / non-certifying 上限を解除しない。**
  base: 24835ff46a1546056bf12a57d4b8991611f3b983aa684ac7e39cdd7562ec8ca1
