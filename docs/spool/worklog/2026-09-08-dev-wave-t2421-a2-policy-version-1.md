---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2421-a2-policy-version
seq: 1
title: [T-2421] A-2 consumer に policy 文法の版選択を入れた — 先行 wave の 1 件限定 adapter を世代選択へ置き換え、歴史側にも完全な文法を効かせた (コード + テスト、branch worktree-dev-wave-t2421-a2-policy-version、変異 10 件すべて KILLED・期待 node 完全一致)
---

## 本文

- **本題。** producer の policy 文法が締まるたびに過去成果物が読めなくなる構造 (F884) を、
  版選択へ置き換えた。設計は {{D:policy-grammar-generation-selection}}。
- **受理集合は広がらず、狭まった。** 先行 wave の手書き `_historical_policy_view` は
  schema・configure key 集合・protocol hash の 3 assert しか当てておらず、残る文法本体を飛ばしていた。
  これを producer の完全な loader へ一本化したので、`_protocol_preimage` に含まれない
  `tracked_destination` などの検査が歴史側にも効くようになった。変異 M6 がこれを 2 node で捕えている。
- **段 3 の敵対相談が親 brief 自身の不変条件違反を見つけた。** 段 2 プランは公開 `load_policy` へ
  caller 選択の世代引数を足す案だったが、これは「受理集合を 1 件も増やさない」という親の不変条件と
  正面衝突し、`load_policy(path, generation=...)` で 6-key policy 一般が受理される。
  親は blocker として採用し、公開署名を不変にして歴史読みを private entry point へ隔離した。
- **段 3 が「差分定義」の再発を捕えた。** プランは旧世代の key 集合を「現行集合 − FetchContent key」と
  差分で定義していた。次に必須 key が足された時点で旧世代へ混入し、**まったく同じ再発が起きる**。
  両世代を独立した frozenset literal として凍結した。
- **親の裁定に誤りがあり、実装子が上回った (erratum)。** 親は段 4 で「差分定義へ戻す変異は現時点では
  等価変異で kill できない」と裁定した。実装子は producer source の AST を検査して
  `frozenset({...})` の literal であることを構文レベルで要求する形にし、この変異は実際に KILLED になる。
  変異 M9 として登録し、本走で 1 node の完全一致を実測した。初回の裁定は消さず erratum に残した。
- **段 6 レビューが変異の帰属不成立を 3 件出した。** M7 は `source_binding_status` gate が consumer の
  2 箇所にあるため単一変異で殺せず (親が現物で確認)、M6 は共有本体に世代が届かないため
  「歴史世代のときだけ」の一箇所変異にできず、M3 は受け渡し点が 2 箇所あった。
  fix で単一理由の負例 2 本を足し、M3 を M3a / M3b へ分割し、M6 を共有 gate 削除へ再照準した。
  **重複していた 2 つ目の gate は冗長 gate と明記し、単独変異の証拠から外した (DW-M03)。**
  本走で M7 は新設した単一理由テスト 1 node だけを殺し、end-to-end 版は 2 つ目の gate に拾われて
  緑のままだった — 冗長性が実測で裏付けられた。
- **実成果物での完了検査。** 段 1 brief が置いた完了条件は「t2364 成果物を当時の文法の全体で読んで
  figure data を構成できること」だった。測定 root がこの機体に実在することを確かめ、
  `expected_hashes` override なしで `load_measurements` を最後まで通す統合テストを入れた。
  期待値は凍結成果物から読む (cell 順・median・効果値・manifest の file 集合) 形にし、
  当初あった恒真な assert 3 件をレビュー指摘で置き換えた。
- **限界を明記する。** 版選択が覆うのは `trace0_cmake_argv.configure` の key 集合だけである。
  `schema_version`、top-level key 集合、各値制約、`_protocol_preimage` は全世代共有のままなので、
  次の締め付けがそれらに及べば同じことが起きる。**再発を無くしたわけではない。**
  世代ごとの完全な文法契約を作る案は、ユーザーが scope 外と明示した一般化であり、
  DW-G04 の発火条件を満たす既存 artifact path も書けないため実装せず、裁定パッケージへ返す。
- **絶対規律 7 の区別。** 過去成果物を読めるようにすることは、当時の測定を現行の正しさ主張へ
  昇格させることではない。歴史世代で読んだ Policy は plot consumer の 1 経路からしか得られず、
  producer の認証・実行経路へは流れない。status・correctness・`source_binding_status` を再分類しない。
- **エージェント工数。** 段 2 plan 1 本、段 3 敵対相談 2 本、段 5 実装子 1 本、段 6 レビュー 2 本、
  段 6 fix 1 本の計 7 本。いずれも rc=0 で `check_codex_output.py` を通した。
  実装子と fix 子はどちらも sandbox から pytest を起動できず「実装済み・未実走」と正直に申告し、
  実測はすべて親が行った。

## 次の一手差分

### 完了

- [T-2421] A-2 consumer へ policy 文法の版選択を入れて着地した。
  版選択が覆うのは configure key 集合だけで、schema・値制約・protocol preimage は全世代共有という
  限界が残る。
  remaining: none
  base: b8b7e15c486491424f8a0b57cbc86c47c7d2b70cd268d24417603372800abdfb

### 新規

- {{T:policy-grammar-generation-scope}} **P2・新規**: policy 文法の世代選択が覆う次元を、
  configure key 集合から `schema_version` / top-level key 集合 / 値制約 / `_protocol_preimage` へ
  広げるかを決める。**発火条件を満たす既存成果物がまだ無いので、DW-G04 に従い今は設計メモに留めている。**
  次に producer 文法がそれらの次元で締まったとき (= 実際に読めなくなる成果物が出たとき) に着手する。
