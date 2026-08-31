---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2075-layer3-bypass-hard-failure
seq: 1
title: [T-2075] 受入が層 3 の鎖を迂回したときを hard failure にした (code + tests + insight、branch worktree-dev-wave-t2075-layer3-bypass-hard-failure、変異 5/5 KILLED)
---

## 本文

- D1289 の実装。受入 `assert_trial_registry_acceptance` が層 3 の鎖を迂回した事実を
  真偽値と reason code `"layer3-chain-absent"` に記録するだけで受領証を出していた形を廃し、
  hard failure で止める形にした。記録だけの経路は制御フロー上に 1 つも残らない。
- **迂回の実体は外側の `continue` ではなく鎖の本体**である。`assert_campaign_layer3_chain` は
  campaign を持たない失敗 cell を `continue` し、読取・再構築・比較を一切せずに正常 return する。
  「関数名を一度呼んだ」ことと「build report を鎖へ通した」ことは同義でない。
- **hard failure の位置は鎖の呼出しの後**とした。段 2 プランは呼出しの前で拒否する設計だったが、
  段 3 の敵対レンズが「それではその report が鎖を一度も実行せず、証拠契約の
  『すべての build report に層 3 検証を実行する』量化を満たさない」と指摘し、段 4 で書き換えた。
- **2 つ目の hard failure (層 3 レポート不在) は現行 tree の安定 artifact では独立に到達しない。**
  段 3 の 2 レンズが別々の下流経路 (手前の腕 digest 検査 / 後段の cross-binding 検査) を根拠に
  同じ結論へ達した。位置としては fail-closed にするが、効いている機構としては数えない。
  変異を登録せず、他の gate を stub して到達させるテストも書かない (規律 3、DW-M01 / F28)。
- `do_build=False` の no-build は hard failure にしない。D536 の「no-build 受理そのものの拒否」却下は
  D1289 に覆されていない。この境界は変異 `reject-no-build` (23 件 kill) で固定した。
- 親の段 1 brief に誤りが 2 件あり、段 3 のレンズが実測で覆した。(a) 層 3 レポートが 7 件実在するから
  DW-O13 の入力実在を充足、という記述は過大で、7 件は探索用 campaign であり正式 6 セルの入力
  (`output/s8c-preregistration/trial-manifest.v1.json`) は現行 tree に不在。(b) 受入の永続書込は
  受領証だけであり、「台帳に残る」は誤り。
- 段 6 の敵対レビュー 2 本は must-fix 0、nit 1。nit は改名したテストの nodeid が所要時間台帳に
  旧名のまま残る件で、**直さない**と裁定した。台帳の値は実測で入るものなので手で書き入れれば
  計測の捏造になる。被覆のメタテストは単独実走で緑を確認した。
- 変異 probe 走が共有木の事後検査で rc=125 になった。並行 wave が共有 checkout の未追跡ファイルを
  書き換えるためで、変異結果自体は 5 件とも収集できていた。本走は独立 clone を `--source-repo` へ
  渡して構造的に断ち、rc=0 / 5-of-5 KILLED を得た。
- 実装子 (Codex author) は Pegasus の投入経路を sandbox から使えず「実装済み・未実走」と報告した。
  テストの実測はすべて親が行った。
- 受入全走 1 回目は `rc=70` / child rc=1 で戻り、赤 26 件がすべて
  `orchestrator/tests/test_codex_reasoning_ab.py` に集中した。**非帰属である。** 赤の本文は repo 外
  `~/.codex/sessions/2026/07/29/rollout-*.jsonl` の `FileNotFoundError` で、本 wave の差分は
  repo 外を作ることも消すこともできない。tested main `24014bdb2` を独立 clone へ checkout して
  同 file を単独走し、`failures=26 / failed=5 / errors=21` が受入の内訳と完全一致することを確かめた。
  署名の一致ではなく assertion 本文と main 単独再現の 2 経路で判定している。
- この赤は本 wave 固有ではなく**この機体の全 wave を塞ぐ**。ユーザーはホームの会話ログを
  ストレージ上限のため定期的に削除しており、pin 先の月が消えたのはその運用の結果である。
  修正は編集面の衝突を避けるため並行セッションの取りまとめで別 wave へ一本化された。
  本 wave は該当 file に触れていない。失敗の記録と再導入タスクは修正を所有する wave が立てるため、
  **本 wave では F を起票しない** (同じ型に F 番号が 2 つ付くのを避ける)。
- 除外台帳での回避は構造的に不可能だと実装から確かめた。`flaky_test_holds.py` は証拠 ID に
  採番済みの `F[0-9]+` と `docs/failures.md` 内の該当節を要求し、さらに `green_run_count >= 1` と
  非空の緑観測を要求する。この 26 件は当該 file が消えて以降この機体で一度も緑になっていないため、
  緑観測を書けば証拠の捏造になる。F の採番は land 時の fold でしか起きず land には緑の受入が要るという
  循環は F766 に同型が記録済みで、今回が 2 例目である。
- 解決策の検討は codex 2 レンズで行い、結論を修正の所有 wave へ渡した。pin の張り替えは D1164 が
  凍結 provenance の書き換えを却下しているため採らない。恒久対応は exact bytes を
  content-addressed な束として repo へ置き、欠落を読み飛ばしでなく hard failure にする形だが、
  元 bytes が機体にも repo にも残っていない (深さ 8 の全探索と `git ls-files` で 0 件)。
- 一次資料は D1289、D863、D536。詳細は `output/insights/2026-09-01_t2075-layer3-bypass-hard-failure/`。

## 次の一手差分

### 完了

- [T-2075] 受入が層 3 の鎖を迂回したときの hard failure 化を実装し、変異 5/5 KILLED で裏取りした。
  remaining: none
  base: 5d23919050e002f16e083b2dc91c3280d97d808acf1c7ff10647aa5aacb9cee5

### 新規

- {{T:c09-called-names-liveness}} **P2・新規 (2026-09-01 [T-2075] 段 3 敵対レンズの実測)**:
  事前登録の条件 9 判定器 `_evaluate_c09` が使う `_called_names` は `ast.walk` で走査し生死を見ないため、
  `if False:` の下に置いた `assert_campaign_layer3_chain` の呼出しも「呼んでいる」と数える。
  実効化するか、契約側の文言を実装に合わせるかを裁定する。一次資料は
  `output/insights/2026-09-01_t2075-layer3-bypass-hard-failure/README.md`。
- {{T:c09-contract-quantifier-and-sink}} **P2・新規 (2026-09-01 [T-2075] 段 3 敵対レンズの実測)**:
  証拠契約 `s8c_preregistration_evidence_contract.v1.json` の条件 9 は「every build report」
  「registry append」と書くが、受入の永続書込は受領証だけである。「受領証発行へ到達する全 build
  report」へ直すかどうかを裁定する。同上。
- {{T:producer-layer3-empty-run}} **P2・新規 (2026-09-01 [T-2075] 段 3 敵対レンズの実測)**:
  producer (`p3_autonomous_workload_trial.py`) と standalone verifier に、受入と同型の層 3 空走が残る。
  campaign を持たない失敗・materialized admission failure・致命的 zero-cell を、層 3 実体ゼロのまま
  診断 report として発行できる。D1289 の逐語は「受入の確認処理」なので本 wave では触っていない。
  acceptance 限定で閉じるか全 verifier へ広げるかを裁定する。広げるなら producer・診断契約・
  発行順序の一体改訂になる。同上。
