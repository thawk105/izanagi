---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t1948-registry-parse-fallback
seq: 1
title: [T-1948] attempt registry の読取失敗を旧経路の認可へ変換する穴を塞いだ (コード + docs、branch worktree-dev-wave-t1948-registry-parse-fallback)
---

## 本文

- 受理集合が変わる wave なので軽量版は採らず、段 2 プラン 1 本・段 3 敵対相談 2 本・
  段 5 実装 1 本・段 6 敵対レビュー 2 本の 6 子構成で回した。工数は codex 子 6 本 (`gpt-6-astra`
  / `medium`)、うち rc 非 0 で死んだ子はゼロ。
- 段 2 のプランが、brief が「既に分離できている」と書いた前提の欠落を 1 件見つけた。
  `_read_floor_registry_candidate_rows` の `except FileNotFoundError` が `lstat()` と
  `read_bytes()` の両方を包むため、存在しない対象への symlink が「registry 不在 = 候補 0 件」へ
  化けていた。**穴は 2 箇所ではなく 3 箇所だった。**
- 段 3 のレンズ A が、そのプランの是正案 (「非 regular / symlink 検査を読取前へ移す」) を
  **受理集合を広げる**として拒否した。`lstat` 後に symlink へ差し替わる順序では、
  現行の読取後検査が拒否するものをプランの reader は返してしまう。親は
  「`try` を 2 つに割るだけ・読取後の検査は 1 文字も動かさない」最小形を採用した。
  設計判断は {{D:registry-read-failure-not-legacy-authorization}}、失敗の型は
  {{F:unreadable-registry-counted-as-zero-candidates}}。
- **refuted**: 「二つの fallback 除去そのものが受理を広げる」「4 つの拒否 message が実在しない」
  「テスト改名に受入台帳の更新が必須」「既存変異 2 件が恒真化・帰属不成立になる」
  「campaign が拒否を握り潰すので consumer 修正が要る (certified 経路については誤り)」。
- **一般化しすぎの是正**: 親は凍結 pin 閉包を「両 file の sha256 / blob hash 検索で 0 件」と
  書いたが、段 3 のレンズ A が「hash 検索は非 hash の拘束を数えない」と指摘し、
  正規表現 pin・変異 spec の literal・adapter 非 import の AST 検査・spawn site 件数 pin の
  4 種を独立に列挙して、いずれも本差分の対象外であることを確かめた。根拠を hash 検索だけに
  置かない形へ直した。
- **段 6 の唯一の実務所見**: 過剰拒否の正例の期待 node 集合が不足していた。レンズ A は
  静的に 6 件と読み、自ら「完全集合と断定せず親の matrix で確定せよ」と限定した。親が
  probe 走を回して実測すると **7 件**で、静的予測に無い 1 件が加わった。静的レビューだけで
  確定していたら本走が MISMATCH で止まっていた。probe 相は erratum として残した。
- 変異本走: baseline PASSED、**KILLED 4 / 4、SURVIVED 0、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0**。
  逐語と spec は `output/insights/2026-09-14/t1948-registry-parse-fallback/`。
- 親の実測: 変更 test file 単独走 179 passed。consumer 焦点走 9 file で 1475 passed / 11 skipped。
  全史 provenance 監査 9750 件・新規違反なし。いずれも rc=0。
- scope 外と裁定した real 所見 2 件を新規 item として起票した。どちらも本 wave が作った穴ではなく、
  certified 受理集合を広げるものでもない。
- dev-wave 改善候補は 1 件挙げて**不採用**にした。`tools/check_wave_startup.py --mode midflight` へ
  `--external-handoff` を渡して rc=2 で 1 投入を無駄にしたが、段 5 の手順は midflight の argv を
  そのまま書いており、`--external-handoff` を要求しているのは開始 gate の記述である。docs の欠落・
  曖昧ではなく親が開始 gate の記述を midflight へ広げた読み落としなので、手順は変更しない。

## 次の一手差分

### 完了

- [T-1948] 読取・候補導出が失敗した事実を旧 `valid=False` 経路の認可へ変換する fallback を
  3 箇所とも塞ぎ、負例 3 (query / 消費 / 最終検査) と正例 2 (不在で旧経路が通る /
  存在しない対象への symlink を不在扱いしない) を同じ変更単位に置いた。変異 4 件が全 KILLED。
  remaining: none
  base: 53bc5346b5b7dad8a157d6b465ef5385279a9a7f3cafac928bef1189f69d6e31

### 新規

- {{T:floor-query-legacy-used-trigger-asymmetry}} **P2・新規**: 床値 retry の query 側で、
  recovery 収集は使用済み trigger を除外するのに legacy 集合は除外しない非対称を閉じる。
  その trigger の recovery 候補を数えずに legacy 認可を返しうる。既存の穴であり、
  消費と最終 evidence 検査は対象 trigger を再取得して両候補を拒否するため certified 受理集合は
  広がらない。query の認可返却と retry 起動準備だけが非対称に残る。
- {{T:floor-noncertified-abort-swallowed}} **P2・新規**: 非 certified の床値 campaign 経路で、
  `CampaignAbort` が `RuntimeError` 継承のため測定側の `except` に捕まり、即時停止でなく
  `launch_failure` の session へ変換される件を閉じる。certified 経路と最終 inspection は
  この catch を通らないので受理集合は変わらない。変わるのは journal の試行行・retry 枠・
  terminal 診断である。
