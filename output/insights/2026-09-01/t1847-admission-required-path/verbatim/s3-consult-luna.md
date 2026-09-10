## 所見

静的検査の範囲では、canonical-path 関門の設計そのものに重大な欠陥はない。ただし、射影制約により全テストディレクトリの参照検索と `docs/decisions.md` 現物確認は完了できず、独立検査全体としては条件付き判定になる。

| 層 | 判定 | 実測した file:line | 理由 | 成果物への影響 |
|---|---|---|---|---|
| production factory | 効く | `test_p3_b4_closed_critic.py:1000-1051,1054-1106` | record 検証が executable・artifact・provider より先で、同じ record が最終検査にも渡る | production factory は非 canonical path を通さなくなる |
| certified pair 関門 | 効く | `test_p3_b4_closed_critic.py:1089-1106,1363-1418` | `assert_b4_certified_arm_pair` が admission record を再検証する | 作成後に path 条件を迂回した certified pair は成立しない |
| launcher CLI | 中央関門経由で効く | `s2-plan.md:119-120`、`test_p3_b4_launcher.py:330-343` | `--admission-record` 自体は残るが、bootstrap は driver より先に実 verifier を通る | CLI で別 path を指定できても受理はされない |
| bootstrap | 直接効く | `test_p3_b4_launcher.py:346-373` | record 検証成功後にだけ layout と launch sidecar が作られる | 非 canonical path では起動前に停止する |
| continuation | factory 経由で効く | `test_p3_b4_closed_critic.py:2646-2793` | continuation が record を production pair と launcher context に渡す | continuation も同じ関門へ収束する |
| critic admission sidecar | 間接的に効く | `test_p3_b4_closed_critic.py:1065-1202` | 発行前に検証済み record を要求し、repository path を sidecar に記録する | sidecar の期待値は canonical path へ更新が必要 |
| launcher sidecar | 発行条件にだけ効く | `test_p3_b4_launcher.py:104-122,346-373` | context は record の hash・commit を持つが repository path は持たない | sidecar の出力場所や schema 自体は変わらない |
| test factory | 効かない | `test_p3_b4_closed_critic.py:315-379,2314-2333` | `create_b4_closed_critic_pair_for_test` は admission record を取らない | test-only 経路は従来どおりだが certified へ昇格できない |
| 事前登録文書の規範 | 触っていない | `s2-plan.md:122`、事前登録 `:229-233,793-797` | 文書は driver ごとの発行を要求するが exact path は定めない | コード上の関門は閉じるが、文書が canonical path の正本になったとは言えない |

## 正しさ境界に関わる所見

### 1. 「すべての呼び手が通る」は production 限定なら正しい

- 実測した file:line: 親 brief `:62`、段 2 plan `:14`、`test_p3_b4_closed_critic.py:315-379,2092-2108`。
- なぜ問題か: brief の「3 呼び手すべて」が全 factory を含む表現として読まれると、test factory が verifier を通らない事実と食い違う。段 2 plan は「production の検証呼び出し」と限定しており正確である。test-only receipt は certified gate で拒否されるため production の穴ではない。
- 成果物への影響: brief の表現を「production の 3 呼び手」に限定すべきだが、実装追加は不要。

### 2. 既存の拒否理由を変更する計画にはなっていない

- 実測した file:line: `test_p3_b4_admission_record.py:715-739,742-790,793-858,861-904`、段 2 plan `:133-137,174-180`。
- なぜ問題か: gate を resolver の直後へ置くため、既存の非 canonical regular file は新しい理由で先に落ち得る。plan は sort mismatch を sort の canonical fixture へ移し、untracked を canonical だが HEAD 未登録の fixture に変えることで、従来の失敗原因と exact 署名を維持している。missing、directory、symlink、`.git/HEAD` は resolver が先に拒否するので不変である。
- 成果物への影響: 規律 2 違反は見つからない。既存 exact 署名は変更せず実装できる。

### 3. §5.1 と §10 は driver ごとの 3 canonical path と両立する

- 実測した file:line: 事前登録 `:229-233` は 3 driver の projection を同時に登録し、`:793-797` はその版へ束縛した record を driver ごとに発行すると定める。plan の写像は `s2-plan.md:31-57`。
- なぜ問題か: 全 driver 共通の単一 record を要求する記述はなく、driver ごとに 1 record、1 canonical path とする設計と矛盾しない。ただし exact path は §5.1、§10 のどちらにも書かれていない。
- 成果物への影響: 文書改訂は整合性のためには不要。ただし文書側まで canonical path 規範を閉じたとは報告できない。

### 4. 正例は具体的に存在する

- 実測した file:line: 段 2 plan `:155-172`。
- なぜ問題か: 各 driver について、正しい record を canonical path に commitして成功させ、同じ bytes の `admission.json` を拒否し、同一 repository state で canonical record を再度成功させる手順まで固定されている。
- 成果物への影響: 無条件拒否だけを増やす gate にはならない。

## 親 brief への所見

- D1332 と依頼 (1) は、射影された逐語記録上は同一主題である。`rulings-verbatim.md:15-29` は「§5 の残り 9 欄の型検査」を明示的に見送り、負例追加も却下している。したがって依頼 (1) を scope 外にした結論は妥当。
- D1050 と T-1847 も同一主題である。`rulings-verbatim.md:3-14,76-86` は、複数 path からの選択を「正となる置き場所 1 本」で閉じる同じ問題を記録している。別主題の取り違えはない。
- (2) は (1) に依存しない。型検査が既存の限定範囲に留まっても、受理可能な repository path を狭めれば path shopping は独立に閉じる。
- ただし親 brief `:18` の「§5 は 1 欄も未記入」は現物と食い違う。事前登録 `:160` は `n = 201` を記入済みで、`:167` も実行責任者を部分記入済みである。D1332 の拘束は変わらないが、この補助理由は削除または訂正が必要。
- `docs/decisions.md` 自体は必読射影に含まれないため読んでいない。上記は `docs/decisions.md` からの逐語抜粋と明記された資料に基づく判定であり、依頼された「現物確認」そのものは未完了。

## 整合・実効性に関わる所見

### 1. 直接追随する既存テストは 6 件、fixture factory は 2 箇所

- 実測した file:line:
  - fixture factory: `test_p3_b4_admission_record.py:191-229`、`test_p3_b4_closed_critic.py:670-787`
  - 既存テスト: `test_p3_b4_admission_record.py:664-712,715-739,742-790,793-842`
  - 既存テスト: `test_p3_b4_closed_critic.py:1054-1202,1956-2009`
- なぜ問題か: 更新対象は合計 8 source unit。旧 `admission.json` の変更対象は 10 occurrence (`218,220,699,781,811,830` と `757,767,1170,2007`) である。`test_p3_b4_admission_record.py:890` の文字列は directory-symlink 攻撃入力なので変更してはならない。
- 成果物への影響: 段 2 plan の列挙に漏れは見つからない。

launcher 側は `test_p3_b4_launcher.py:28-31` で shared fixture を import し、`183-186,222,249,280,349,388-392,434,528-531` がその `record_path` を使うため、配置変更のためのソース修正は 0 件だが焦点走対象には含める必要がある。

### 2. 射影された consumer test はすべて plan に含まれるが、全体検索は未完了

- 実測した file:line: module import は admission test `:21-22`、closed-critic test `:31-33`、launcher test `:16-18`。plan は `s2-plan.md:128-152` で 3 file すべてを扱う。
- なぜ問題か: 単独段 dispatch の射影はこの 3 test file に限定され、要求された `orchestrator/tests/` 全体の module-name 検索は実施できない。したがって射影外 consumer の不存在は証明できない。
- 成果物への影響: 既知 consumer の漏れはないが、全 consumer inventory を完了したとは報告できない。

### 3. D1050 に不要な機構追加は見つからない

- 実測した file:line: 段 2 plan `:31-57,74-100,113-122,182-187`。
- なぜ問題か: 追加は 3 literal の driver-to-path mapping と中央関門だけで、新台帳、一般化 resolver、互換 flag、警告降格はない。既存 CLI flag の維持も迂回にはならない。`MappingProxyType` は小さな防御だが、新しい解決層や将来抽象には当たらない。
- 成果物への影響: 削るべき過剰実装はない。

### 4. 焦点走の consumer 名は揃うが、実行指示は明文化されていない

- 実測した file:line: plan `:128-152` は 3 test file を列挙し、`:17` は未実走を明記する。
- なぜ問題か: consumer file の列挙は揃っている一方、具体的な焦点走コマンドは書かれていない。
- 成果物への影響: nit。実装段では 3 file 全てを焦点走対象として明記すれば足りる。

## 総括

- 設計上の最大の注意点は、canonical path が効くのは production admission 系であり、test factory と文書規範そのものには効かないこと。
- driver ごとの 3 canonical path は事前登録 §5.1、§10 と両立し、文書改訂は必須ではない。
- 直接追随は fixture 2 箇所と既存テスト 6 件で、plan の列挙漏れや既存拒否理由の変更は見つからない。
- 親の scope 縮小は妥当だが、「§5 は 1 欄も未記入」という根拠は現物と不一致。
- 全 consumer 検索と `docs/decisions.md` 現物確認が射影不足で未完了なため、実装移行はその 2 点の確認後なら可。テストは実行していない。