---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t492-freeze-semantic-membership
seq: 1
title: [T-492] known 軸凍結の生成・検証層へ semantic membership を入れた — 検査点は schema 側に置き、裁定パッケージ 4 件を返す (コード + docs、branch worktree-dev-wave-t492-freeze-semantic-membership)
---

## 本文

- **段 1 の前提実測で、裁定時点で未見だった事実を 1 件見つけた。** 検査の呼び出しは
  凍結物の generator 自身に足すしかないが、その generator の sha256 は freeze 文書の
  `/generator/sha256`、移行 receipt の metadata 定数、driver test の literal に pin されている。
  generator へ 1 行足して freeze 系 7 test file を実走したところ **1 failed / 222 passed /
  1 skipped** で、赤は `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`
  ただ 1 本だった (known-axes leg の期待 refusal が source 不一致から generator 不一致へ変わるため)。
  移行 receipt の active 検証は generator セルを静的再構成比較から除外し、metadata 照合も
  移行基準 commit の blob と行うため、live 編集で壊れない。裁定 (現行凍結物を再発行しない) は
  覆らないので、そのまま実装して赤 1 本を意図を保ったまま是正した。変異は即座に復元した。
- **段 3 の敵対 2 本、段 6 のレビュー 2 本とも NO-GO を返した。** 段 3 は親の provisional 裁定
  (P1) 「生成側 1 箇所で検証層も覆える」を否定した。移行 receipt が active なとき公開 gate は
  static adapter へ委譲し、legacy 検証も文書再構成も呼ばないため、意味検査は schema 検証点に
  置かなければ本番経路に届かない。親は (P1) を撤回した ({{D:freeze-semantic-membership-at-schema}})。
- **親が段 4 で立てた不変条件の文言が不正確で、段 6 のレビューが是正した。** 親は
  「文書構築の出力を一切変えない」と書いたが、generator の自己 hash は生成器 bytes から作るため、
  生成器を編集した時点で既定引数の構築結果はそのセルだけ必ず変わる。AST 不変は値不変の証明に
  ならない。正しい 2 条件と下流影響は {{D:freeze-generator-self-hash-boundary}} に記録した。
  コード側の欠陥ではなかったため実装は変えていない。
- **段 6 のレビューが偽 kill を 3 件見つけた (F113 の同型再発)。** 生成層負例の mock が
  repo 外の相対 path を返しており、検査を消す変異では受理を観測する前に別例外で赤くなっていた。
  harness を走らせる前に検出できたのは F113 の恒久対応どおりレビューのレンズに入れていたためで、
  是正しなければ 1 巡を無駄にしていた。
- **構造的に到達できない範囲を、実装したふりにせず明記する。** 公開 gate の end-to-end で
  非正準述語の負例は作れない。static adapter は known raw bytes が移行定数と一致することを
  先に要求するので、文書を改竄すると別の refusal になるためである。定数を monkeypatch して
  端から端まで通ったように見せることはせず、adapter から schema 検証へ到達する層で負例を固定した。
- **scope 外の real 所見 4 件を裁定パッケージとして返す。** いずれも本 wave の裁定
  (対象を 1 ファイルの trigger 述語面に限定する) の外側にあり、実装していない。
  逐語と根拠は `output/insights/2026-08-05_t492-freeze-semantic-membership/`。
- **段 8 の自己改善は 1 件を既存 F の再発へ畳み、1 件は前 wave と同じ理由で未実装のまま返す。**
  前者は変異事前登録の期待 node 不足で、`docs/dev-wave/` へ新しい規則を足さずに済んだ。
  後者は「worktree 隔離セッションでは redirect 付き複合コマンドが guard に拒まれるので
  起動 script を書く」という手順で、本 wave でも 3 回発火した。置き場である条件節の byte 予算は
  残り 35 bytes しかなく、前 wave が同じ理由で未実装のまま裁定へ返している。予算は上げず、
  安全義務も削らないので **2 回目の発火実績として記録するに留める**。
- **変異は事前登録 6 件 (負例 5・過剰拒否を検出する正例 1) で、是正版は 6/6 kill・node 完全一致。**
  初回走行では正例側 1 件の期待 node が 2 件足りず harness が MISMATCH で止まった。負例は診断文言を
  別 workload / 別 configuration まで含めて完全一致で固定しているため、検査を恒偽化すると常に
  走査の最初の値で落ち、期待文言とずれて道連れで赤くなる。登録側の誤りであって検査側の欠陥ではない。
  初回結果は消さず erratum として insight に残した。受入全走は land 直前の tip で
  6420 passed / 20 skipped (取り込み前の tip では 6348 passed / 20 skipped)。

## 次の一手差分

### 完了

- [T-492] 生成層と検証層へ 32 正準述語の semantic membership を入れ、検証点を schema 側に置いて
  本番の公開 gate 経路まで届かせた。現行凍結物は再発行していない。
  remaining: none
  base: 2d44990f33489512c06a21be412aeb129b471473a67ff1019cc6ce825c7453c7

### 新規

- {{T:freeze-refreeze-generation-transition}} **P1・新規・ユーザー裁定待ち (段 3/6 の独立 2 者が指摘)**:
  **「semantic membership を入れれば次回 refreeze ができる」は偽**である。再凍結すると known の
  raw hash と `/generator/sha256` が変わり、旧 raw hash を定数で固定している T-080 移行 receipt が
  必ず無効になる。measurement / holdout / manifest / ratified も known raw を記録しているため、
  known だけの再凍結も一括再凍結も旧 receipt と不整合になる。旧定数の上書きは過去 receipt の
  意味を後から変えるので採れない。必要なのは新世代 artifact と transition receipt / trust root の
  更新であり、[T-478] の世代移行設計と同じ面である。**次回 refreeze の前提タスクとして裁定を要する。**
- {{T:trigger-name-mask-binding}} **P1・新規・ユーザー裁定待ち**: 今回入れた検査は「32 正準集合の
  外か」しか見ない。`name` が指す mask と述語本文の mask が食い違っても、両 provenance を
  揃えれば通る (例: `g_rl` という名に別 mask の正準述語)。この場合 certified 選択・材料レポート・
  試行台帳の構成名と実際の gate 意味が食い違い、誤 certification まで到達しうる。
  [T-493] の閉じた権威集合と主題は近いが対象軸が異なる
- {{T:holdout-freeze-semantic-closure}} **P2・新規・ユーザー裁定待ち**: holdout 凍結は known 文書を
  直接読んで 6 構成をそのまま複製し、意味検査を通さない。正規の producer 経由なら今回の生成側
  検査で守られるが、別途発行された非正準 known 文書を直接与えると holdout 単体では受理される。
  公開 oracle の sink では拒否されるため誤 certification には至らないが、holdout 台帳と材料参照に
  非正準述語が入る。閉じるには別 producer の編集が要り、その generator hash pin へ同型の巻き込みが出る
- {{T:freeze-membership-authority-provenance}} **P2・新規・ユーザー裁定待ち**: 受理集合の権威
  (正準述語 index とその emitter) が凍結 proof chain に帰属していない。trigger entry の source 記録は
  従来の 2 モジュールだけで、`selection_rules` も membership 規則を記述しない。権威側の連動 drift が
  起きても、凍結台帳には「どの権威で受理したか」の hash が残らない。ただし是正はいずれも
  文書構築の出力を変えるため、{{T:freeze-refreeze-generation-transition}} の世代移行と同時に裁定する
