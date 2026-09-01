---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-knowledge-rich-synthesis
seq: 2
title: 合成の既定を知識ありへ倒し、知識の遮断を防壁から実験条件へ移した (docs のみ、branch worktree-dev-wave-knowledge-rich-synthesis、実装面 0・変異 matrix 免除)
---

## 本文

- **ユーザー直接裁定 (逐語):** 「この研究・izanagi はいくらでも web 検索やリポジトリにある試行錯誤の
  知識を見ても良いと変更する。roadmap とかも。そういうのがあるなしでは、なしの方が CC 自動合成は
  難しいはずであり、まずは簡単なところから実現しにいく」。設計判断は
  {{D:knowledge-rich-synthesis-default}}。roadmap の協議改訂 4 箇所 (§1 の入力契約・主張の階層、
  §2 の入力図・システム合成要件) を伴う。
- **D568 の待機条件を今回の裁定が supersede した。** D568 は「まず最小拡張 1 本を実装・観測してから
  既定変更の要否を判断する」として全面再定義を却下していた。実装 (`policy_hint`) と投入経路
  (`--policy-hint`) は存在するが、`output/campaigns` 配下に記録は 0 件で、context 出力と実 iteration の
  provenance 束縛も無い。観測は未達のままである事実は隠さず、主張の境界として書いた。
- **段 3 の 2 レンズが親の実測 3 件のうち 2 件を訂正した。親はどちらも現物で確認して受け入れた。**
  (1) C5 の遮断対象は「診断数値のみ」ではなく、凍結された diagnostics の束全体 (status・design_choice・
  文章の effect・既知百分率・機序帰属・indicators) の除去である。それでも「一般知識の遮断ではない」
  という結論は変わらない。(2) `policy_hint` について「走行をまだ回していないから」は証拠より強い。
  言えるのは記録と束縛の不在までである。(3) 並行 wave の編集面重複 0 件は committed / dirty の
  snapshot に限る。書き始めていない wave の編集予約は repo 外の job directory にしか現れない。
- **レンズ B が、親と段 2 plan の両方が持っていた同じ誤りを捕まえた。** 両者は凍結事前登録を
  「その実験固有」と再分類しようとしていたが、同文書は冒頭で自らの射程を「後続段 4 以降の coder の
  性能主張はすべて本設計に従う」と定めている。bytes に触れないまま意味だけ狭めるのは事前登録の
  差し替えに当たる。確定文面では射程を縮めない書き方へ直した。
- **親 brief のもう 1 つの誤り。** brief は C5 を「現 headline の endpoint S-3」としていたが、
  2026-07-16 の Holm 判定表で S-3 は非有意 (p = 1.0)、縮小主張 S' の headline も不成立と確定済みで、
  生きた headline ではない。遮断アームを残す理由は「凍結された歴史的契約の保存」と
  「K0/K1 対照の材料」に直した。
- **親の部分却下と、段 6 レビューによるその是正。** レンズ A は「manifest 束縛が実装されるまで
  K2 の走行を non-certifying と宣言せよ」を求め、親は「certified な選択そのものは従来どおり出せる」
  として部分却下した。段 6 レビューがこの却下を過大と判定し、親は**確定文面で certified を 2 段に
  割った** — 個々の候補がゲートで得た判定は束縛が無くても有効、K2 を条件とする certified な最終選択は
  知識水準と投入知識源が proof chain に結ばれるまで主張しない。何を見て選んだかを再検証できない
  選択は evidence-bound ではないという既存要求そのものからの帰結であり、新しい gate ではない。
- **親が維持した却下。** 知識源の許可リスト・機械的 leak 判定・既知候補との類似度 gate の新設は
  見送る。効果が未実証の段階で分類機構を足すのは絶対規律 5 に反する。**ただし当初これを
  「D568 が同型の案を却下済み」と書いたのは一次資料と食い違っていた** — D568 が却下したのは
  信頼される人間の方針ヒントに対する leak 判定・許可リストであって、外部由来の知識源や
  類似度 gate は対象外である。段 6 レビューが捕まえ、先例の主張を削って規律 5 単独の理由に直した。
- **refuted:** 「K2 化で correctness・identity・performance gate まで緩む」。「C5 は K0 と同じ」。
  「roadmap 改訂に凍結済み事前登録の編集が必要」。「知識を使うこと自体が常に HARKing」。
  「roadmap 改訂セレモニー (版上げ・history 凍結) が必要」— 協議改訂に当たる。
  「変更 path が凍結 bytes の閉包と交差する」— レンズ B が S1 freeze / measurement freeze /
  exact manifest 23 件 / `selector-8b` role pin / R33 identifier pin を列挙し、交差は空だった。
- **段 6 は 2 巡した。** 1 巡目 (確定差分のレビュー) が must-fix 5・nit 2 を出し、反映漏れは 0 件だった。
  親が 5 件すべてを是正し、1 巡目の射影から漏れていた worklog fragment を加えて焦点再レビューへ掛けた。
  2 巡目の対応表は must-fix 4 closed / 1 partial、nit 1 closed / 1 partial、regressed 0 件。
  残った 2 件はいずれも文言の食い違いで、(a) decisions の却下案に「certified な選択そのものを止める
  理由がない」という旧境界が残り本文と衝突していた、(b) roadmap の短縮記述が `tools: []` を D45 に
  帰属させるようにも読めた。レビューが受理条件を逐語で示していたので、親がそのとおり是正して
  closed と裁定した (3 巡目は回していない)。
- **凍結束縛の実測。** `output/s1-freeze/known_axes_freeze.json` は `docs/phase3-main-experiment.md` の
  sha256 を 1 件 pin しており、pin 値は現物の sha256 と完全一致した。1 byte でも変えれば照合が破れる。
- **エージェント工数** (receipt.json より): 段 2 plan 10 model call / 315 秒、段 3 レンズ A 25 / 454 秒、
  段 3 レンズ B 47 / 601 秒、段 6 レビュー 20 / 343 秒、段 6 焦点再レビュー 19 / 265 秒。
  合計 121 model call。段 3 の 2 本は並列。
- 実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず、tip 確定後に親が実走し、
  その受領証で land する。

## 次の一手差分

### 新規

- {{T:k2-arm-minimum-liveness}} **P1・新規**: 知識水準 K2 のアームを 1 本だけ端から端まで生死確認する。
  固定 workload と既存の bounded `EVOLVE-BLOCK` 1 箇所を使い、repo 内の過去試行 artifact を
  少なくとも 1 件含む知識 manifest を commit と path または artifact identity と digest で固定する。
  人間の方針ヒントへ hole や具体実装を混入させず、知識入力を descriptor とヒントから区別できる
  最小の境界を設ける。外部由来の内容はデータとして合成 role へ渡す。候補の provenance に知識水準・
  manifest digest・実際に投入した source identity を束縛し、stock と identity の異なる候補を
  少なくとも 1 件生成して既存の compile・identity・correctness gate へ投入する。
  **run card として固定するもの:** 対象 workload、対象 source と hole、知識 manifest の入力形式、
  campaign 識別子、出力 path。着手前に決め、走行後に変えない。
  **完了条件:** 知識 manifest の受領証、候補との provenance 束縛、stock と異なる identity、
  既存 gate が返した terminal verdict を保存する。correctness reject・性能差なし・stock 選択は
  いずれも有効な終端であり、gate の緩和や改善値を完了条件にしない。
  **主張境界:** この 1 本から言えるのは human-supervised な K2 入力経路と評価経路の生死だけである。
  この走行は pilot として比較集合から除外し、K0/K1 との比較を主張するときは新しい holdout で
  K2 を含む全アームを事前登録して再走する。知識水準と投入知識源が proof chain へ束縛されるまでは、
  K2 を条件とする certified な最終選択も主張しない (個々の候補のゲート判定は有効)。知識の因果的寄与・
  K0/K1 への優越・de novo な軸発見・新しい CC・LLM 固有寄与・無人自律は主張しない。
  最初の一歩を既知の勝ち筋を引く retrieval の positive control に置く場合は、それが選択・再現の
  配線の生死確認であって合成の証拠ではないと明示し、非 stock 候補の走行とは別項目に分ける。
- {{T:knowledge-provenance-binding}} **P2・新規**: 材料レポートと試行台帳へ、知識水準と
  「参照を許した範囲 / 実際に投入した知識源」の 2 段を記録し、campaign identity へ束縛する最小の欄を
  足す。これが入るまで K2 を条件とする certified な最終選択は主張できないので、本項は
  {{T:k2-arm-minimum-liveness}} の後段で成果物の主張を開くための前提になる。
  `policy_hint` の既存記録経路 (`orchestrator/campaign/layer3_report.py`) に相乗りできるかを先に測り、
  相乗りできないときだけ新しい欄を設計する。Web 由来の入力は URL と取得時点に加えて取得内容の
  digest または snapshot identity を持たせる (内容が可変で、URL と時刻だけでは再検証できない)。
  実取得・投入 bytes・モデル側の引用まで分ける必要があるかは、{{T:k2-arm-minimum-liveness}} で
  曖昧さが実際に律速になったときに判断する (先回りして機構を足さない)。
