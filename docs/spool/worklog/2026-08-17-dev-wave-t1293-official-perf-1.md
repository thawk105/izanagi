---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1293-official-perf
seq: 1
title: official 全経路から perf 実在要求を外し、測定条件タグを verdict まで伝播させた — 台帳の「2 箇所」は 19 面で、うち S8b oracle と T126 だけが実際に開通する (コード + テスト、branch worktree-dev-wave-t1293-official-perf、変異 matrix = baseline PASSED・17/18 KILLED・MISMATCH 0)
---

## 本文

- **依頼が前提にした「この経路が閉じると 4 系列が走れる」は半分成立しない。** 段 3 の敵対レビュー
  2 レンズがそろって指摘した。`orchestrator/campaign/s8b_floor_campaign.py` の
  `_assert_official_permitted` が official mode を perf と無関係に無条件拒否し、その唯一の呼び手が
  `_run_campaign_core` の入口である。fresh refreeze はその floor 成果物を入力とするため連鎖して
  止まる。**ただしこれは未見の新事実ではない** — D86 (2026-07-25) が同 guard を「期限つき
  activation lock」と再分類し、解禁設計 (U-1〜U-4) をユーザーが一括承認済みで、同 D86 自身が
  「本裁定は設計のみで、実装していない (コード 0 byte)」「実装は別 wave」と明記している。
  依頼文がその運用状態に触れていなかっただけなので、ユーザー裁定へ差し戻さず実装を進めた。
  **帰結として本 wave の成果は非対称である** — S8b oracle と T126 qualification は live、
  official floor と fresh refreeze は dormant wiring。既存 degraded floor artifact に対する
  refreeze 検証は通る。D86 実装 wave の生存項が現 worklog に 1 件も無いことを全件検索で実測し、
  新規 ID として起票した。

- **台帳の「実箇所は 2 箇所」は 3 段階で覆った。** 親の実測で 9 面、段 2 プランで 14 面、
  段 3 の敵対レビューで 19 面 (A〜S)。台帳が名指ししていなかったのは、floor contract の
  manifest key 制約 (degrade 証拠を official 成果物へ書けない)、T126 投入時の perf smoke、
  S8b oracle が `pipeline.evaluate` を `use_perf` 無指定で呼ぶ既定、`assemble_result` の
  observation 欠落、`screening_driver` と `s1_direct_comparison` の receipt 無し直呼び、
  layer3 が共有 validator を通らない点である。**repo に閉包を pin するメタテストは存在しない**
  ことも段 2 が実測した。依頼文が「個数の断定は過去 2 回外している」と警告していたのは正しく、
  今回は 3 回目だった。

- **親が段 4 でプランの設計を 3 点変更した。** (1) degraded 分岐を「緩い分岐」ではなく
  「別の厳しい分岐」にした。段 3 レンズ A が、手書きの canonical unavailable receipt が現
  validator を通ることを実証したためである。(2) `perf_claim_allowed` を統計消費前の実効的な
  拒否点にした。(3) T126 の perf 有り判定を今日と exact 同一に保つ順序 (candidate 選択 →
  symlink → PATH 前置 → probe) にした。`probe_perf_availability` は literal `perf` だけを
  probe するため、プラン案の probe 先行は「literal 不在・policy candidate 有効」という今日
  perf 有りとして受理されている入力を no-perf へ付け替えてしまう。

- **段 6 の敵対レビューが親の (1) を反証した。** 「偽造の利得はゼロ」という段 4 の主張は成立
  しない。degraded の 5 条件はすべて同じ成果物内の自己申告値 (receipt・run_cmd・raw counter) から
  再検証されるため、3 つとも偽れば perf 有りで counter が壊れた走を degraded として受理できる。
  **これは実装の欠陥ではなく裁定そのものの構造的帰結である** — wave 前の official は
  `expected_use_perf=True` という成果物の外から与えられた定数を権威にしていたが、
  「official も perf 不在で進める」を満たすにはその定数を捨てざるを得ず、成果物の中に独立した
  権威が無い以上、真の no-perf 走と偽造を成果物だけでは区別できない。同種の限界は D348 が
  既に明文化している。土壇場で権威機構を新設せず、ユーザー裁定へ返す新規項として起票した。

- レビューの残り 2 件は real として直した。oracle report が `if observation is not None:` で
  claim gate を掛けていたため **observation を落とすだけで素通り**できた件と、閉包 meta-test が
  事前列挙 path しか走査せず **「production 面を足す」「未登録面を壊す」方向に恒真**だった件で
  ある。後者の調査でレビューが **20 面目** (`calibrator/runner.py` の実コマンド生成と
  `use_perf` forwarding) を特定した。

- **変異走が本物の検査漏れを 1 件見つけた。** 第 1 巡は 15 KILLED / 3 SURVIVED。生存 3 件を
  裁定したところ、`M-C` は親が runner の対象から `test_campaign.py` を外していた取りこぼし、
  `M-VERDICT` は `s8b_verdict.py` の 3 分岐のうち **`else` 枝 (floor も oracle も degraded だが
  観測条件が異なる) が未被覆**という実在の穴だった。`M-CLOSURE` は閉包 meta-test 自身の検査を
  消す変異で、同じ suite では原理的に殺せない (テストのテストが無い) ため SURVIVED を正しい観測
  として登録した。両方向の感度は段 6 fix の実装子が一時変異で個別に確認済みである。

- **実装子 2 体が SIGKILL (-9) で落ちた。** どちらも入力が約 350 万 token に達した時点で
  殺されている。所有 file が素集合という DW-S05-A の条件は満たしていたが、合計 25000 行を
  1 単位に持たせたのが原因だった。所有を 11 単位へ分割し、prompt へ「読んだ合計 2000 行で
  打ち切り、完全な理解より生きて成果物を出すことを優先」と明記して回復した。

- **codex 子は本環境で pytest を 1 度も実走できなかった** (全巡で `qstat -Q preflight rc=1` →
  `rc=16`)。実走は毎巡すべて親が引き受け、子の「実装済み・未実走」を緑と数えなかった。
  この方針は正しく、子が緑を主張しなかった単位でも親の焦点走で赤が出ている。

- main 取り込みで codex 子が起動不能になった。main が持ち込む `docs/dev-wave/` の差分が未 commit
  の間、launcher の authority 検査が止まるためである。ファイル単位の片側採用は本 wave の面 D を
  丸ごと落とすので、merge を中止し **clean な木で本 wave 側の検査位置を main へ寄せてから**
  再 merge した。残った競合は「本 wave 側の純粋な追加 対 main 側の空」になり、`-X ours` で解決
  した。`git diff-tree --cc` は完全な空で、競合解決による新規著作は無い。実装面 9 path は
  Codex author の合成監査が欠落ゼロで引き受けた。

## 次の一手差分

### 完了

- [T-1293] official 全経路の perf 実在要求を外した。台帳が名指しした実箇所は 2 つだったが、
  実測した閉包は 19 面 (A〜S) で、さらに段 6 レビューが 20 面目を特定した。裁定条件
  「perf を要する主張の根拠にしない旨を機械的に記録する」は、degraded observation の
  `claim_scope` (`throughput=eligible` / `perf_required=unsupported`) と、floor 集約前・
  floor source 採用前・member median 採用前・bench TPS 投影前・configuration median 集約前・
  combined verdict 比較前の 6 consumer での `perf_claim_allowed` 消費で満たした。
  degrade の入口は `use_perf_from_receipt` 1 本を維持し、独立 issuer binding は新設していない。
  remaining: none
  base: ecf44f9d1735d651ac0bd1196821bd226a7c4608eca4889462478f5554dc67f4

- [T-1253] official も perf 不在で進める裁定を実装面で履行した。射程は [T-1293] の裁定どおり
  official 全経路と読み、同一 wave で閉じた。条件「degrade した事実が成果物から必ず読める」は
  official manifest / result の `perf_preflight` + `perf_observation`、oracle の degraded 専用
  runtime sidecar、T126 の source-stage evidence と series result で満たした。perf 有りの
  受理集合・argv・成果物 key 集合は exact 不変である。
  remaining: none
  base: 7908891c043b49db391ff0a46eb25107dff3eeb0f522100236f3044b5084bcb6

- [T-967] perf 有無の測定条件タグを oracle manifest・実行・verdict まで伝播させた。
  台帳が挙げた 4 値それぞれへの到達を段 6 レビューが個別に確認している — floor 判定は
  `s8b_floor_stats` が observation を検証、`scale_state` は条件不一致時に専用の
  `measurement-conditions-mismatch` へ、最終 verdict は `structural_indeterminate` を経由して
  terminal status を変え、certified 選択は同じ combined verdict の status に従う。
  approved `8b-oracle-manifest/v1` 本体は変更せず、degraded のときだけ create-only の
  runtime sidecar を書く形にした (実行前 manifest では availability が実測不能なため)。
  remaining: none
  base: f7e47520b0de0e1ff038b9b932736234d3fb5c469ba3793866cc2486c19815eb

### 新規

- {{T:official-activation-unlock}} **P1・新規 (ユーザー裁定は D86 で取得済み・実装が未着手)**:
  D86 (2026-07-25) が `_assert_official_permitted` を期限つき activation lock と再分類し、
  解禁の最小案 (U-1〜U-4) をユーザーが一括承認したが、**実装は 0 byte のままである**。
  現 worklog に生存項が 1 件も無いことを全件検索で実測した。本 wave で official 経路の
  perf 依存は 19 面すべて閉じたので、**official floor と fresh refreeze の production 実走に
  残っている閂はこれだけである。** D86 の (6) が挙げた 3 件の real 所見 (script_sha256 の
  自己申告性、activation 手順の cert C 欠落、guard 付き wrapper が唯一の production caller)
  を実装 wave が引き継ぐ。

- {{T:degraded-evidence-authority}} **P1・新規 (ユーザー裁定待ち)**: degraded official 成果物の
  受理判断が、成果物内の自己申告値 (perf preflight receipt・run_cmd・raw counter) だけに
  依存している。段 6 の敵対レビューが、3 つとも偽れば perf 有りで counter が壊れた走を
  degraded として受理できることを具体的入力で実証した。**これは実装の欠陥ではなく
  [T-1253]/[T-1293] の構造的帰結である** — 成果物の外に権威が無い以上、真の no-perf 走と
  偽造を成果物だけでは区別できない。同種の限界は D348 が既に明文化している。
  親の推奨案は「refreeze の入口が期待測定条件を**成果物の外から** (操作者の明示入力または
  freeze protocol の欄として) 受け取り、既定を perf 必須にする」で、署名機構を新設せずに
  外部アンカーを回復できる。択一は (a) 推奨案、(b) 現状維持で限界を記録に留める
  (D348 と同じ扱い)、(c) degraded 成果物を evidence-only に落とす (ただし refreeze が進まなく
  なるため [T-1293] の目的と衝突する)。

- {{T:certify-calibration-no-perf}} **P2・新規**: `tools/pegasus/certify_calibration.sh` が
  policy 候補の perf smoke 全滅時に `exit 2` する。calibration 認証系列は official floor /
  refreeze / S8b oracle / T126 のいずれでもないため本 wave の scope 外としたが、
  perf 不在ノードでは同系列も止まる。段 6 レビュー B が real・scope 外と判定した。

- {{T:floor-scoping-no-perf}} **P3・新規**: `tools/pegasus/floor_scoping.sh` も perf が無いと
  fail する。certified consumer へ接続されていない別系統なので優先度は低い。
  段 6 レビュー B が real・scope 外と判定した。

- {{T:closure-metatest-selftest}} **P3・新規**: 閉包 meta-test
  (`orchestrator/tests/test_official_perf_closure.py`) の検出力が、同じ suite の変異では
  検証できない (テストのテストが無いため `M-CLOSURE` は原理的に SURVIVED になる)。
  現状は段 6 fix の実装子が一時変異で両方向 (登録済み predicate の削除 / 未登録 production
  file の追加) を手で確認しただけである。自動化するかは費用対効果で裁定する。
