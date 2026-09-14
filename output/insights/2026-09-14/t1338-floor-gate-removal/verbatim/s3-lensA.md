## 結論 (採否と最重要 3 件)

**現プランのままの採用は不可。B の key ごと撤去と 8c 冒頭追記は採用可能です。**

最重要の所見は次の 3 件です。

1. **real — C の対象が違います。** 親が指定した `floor_pair_driver` は B-4 床値の測定側です。過去 floor の binary を今回の oracle 測定へ強制する経路は、別の `s8b_oracle_driver` に残っています。
2. **real — C 全撤去は correctness に連なる検査まで落とします。** strict validator は `sort_best` の SWO PASS receipt も検査しています。段 2 の「strict receipt・trace が消える」という留保は正しいものの、この具体的な依存を取りこぼしています。
3. **real — A の代替不能と撤去禁止を混同しています。** A の内部整合検査が schedule 検査と同値でないことは事実ですが、D501 決定 8 はその内部整合検査自体を不要としています。完全代替を撤去条件にすると、本 wave の撤去が完了しません。

以下、`M` = `orchestrator/campaign/s8b_oracle_manifest.py`、`F` = `orchestrator/campaign/floor_pair_driver.py` とします。

## must-fix

### 1. real — C の撤去対象を親 brief から訂正する

`F:2–10` は B-4 の対照対測定を行う専用 driver です。`F:1107–1115` は、その spec が指定する binary と build receipt の対応を検査します。receipt が「過去の別 campaign の比較基準」であることを、このコードは要求していません。導入裁定も D501 より後の **D1453** です (`docs/decisions.md:45757–45764`)。

D501 決定 8 が説明した性質に一致する現経路は次です。

- `s8b_oracle_driver.py:1052–1063`: floor receipt の binary hash を取得する。
- 同 `:1778–1782`: それを今回の測定の `expected_perf_sha256` に渡す。
- `pipeline.py:2085–2100`: 今回 build した perf binary と比較し、不一致なら測定前に abort する。

段 2 はこの残存を発見しながら「scope 外」としていますが、親のアンカー自体が検査対象なので、その処理では足りません。

**成果物影響:** F を削っても oracle の過去 binary による拒否は残り、代わりに B-4 成果物の binary と receipt 由来 protocol の対応が失われます (`p3_b4_floor_artifact_issuer.py:775–805`)。

### 2. real — C の helper 全撤去は採らない

`F:1099` の呼出し先には、次の検査があります。

- receipt の構造・canonical hash・source/subject/proof の整合性：`s8b_binary_admission.py:306–399`
- trace-disabled：同 `:351–352`
- **`sort_best` の SWO PASS receipt と cell・entry・binary の束縛**：同 `:424–435`

SWO receipt 側は `classification == "pass"` を要求し、期待 binary 等との一致も検査します (`s8b_sort_swo_receipt.py:116–119,245–260`)。これは anomaly 検出器そのものではありませんが、**correctness の PASS 証跡に連なる受入検査**です。「正しさに連なるものは無い」とは言えません。

**成果物影響:** helper 全撤去では、不正な SWO PASS receipt を持つ `sort_best` record もこの入口で拒否されなくなり、B-4 の受理集合が binary 同一性撤去を超えて広がります。

### 3. real — A の撤去条件を完全代替要求から切り離す

D501 決定 8 は、A が「freeze の floor 節の内部整合だけ」を検査すると明示しています (`docs/decisions.md:20824–20829`)。したがって以下は、名指された A の範囲内です。

- `M:615–631`: per-pair 表の構造・key 集合
- `M:632–670`: 値域・null 相関・最大値との一致
- `M:687–688`: その呼出し

`pairs` の key 検査も floor 対表の内部整合であり、schedule の構成集合凍結とは別です。**代替がないという理由だけで残す案は、撤去対象を残しすぎます。**

残す境界は段 2 のとおり、`M:674–686,689–703` と `M:1070–1084`。新しい検査は不要です。

**成果物影響:** A を残すと、schedule と構成集合が正しくても旧 floor 対表の不整合で manifest が拒否され続け、予定した受理拡大が実現しません。

## real と判定した所見

- **real — `M:1053` は A/B の完全代替ではありません。**
  比較するのは caller の `freeze_sha256` と manifest の記録値です。再読・再 hash をしないことも `M:1049–1055` に明記されています。B は別途、渡された object の floor/budget を hash します (`M:1093–1096`)。**この争点は段 2 が正しい**です。撤去後に API 単体で失われる検出力として明記すべきで、完全代替と報告してはいけません。

- **real — C 全撤去で receipt 検査が消えるという段 2 の留保は正しいです。**
  ただし `F:1107–1115` だけの削除も、上記のアンカー訂正なしに D501 の射程内とは断定できません。また、この範囲には後続の trace 検査が使う `subject` の代入が含まれます。狭い削除を行う場合も、代入まで機械的に削除すると `F:1116` が破損します。

- **real — B(a) は旧 manifest の受理を失わせます。**
  `M:58,807–809,1093–1096` の一体撤去は整合しますが、旧 key 付き文書は exact key 検査 `M:1043–1044` で拒否されます。これは単純な受理集合の拡大ではなく、文書形の変更です。段 2 は正しく明記しています。互換層の追加は提案しません。

- **real・nit — 親の「現用条件 3・scale gate が残る」という前提は古いです。**
  現 `s8b_verdict.py:16–18,69` は撤去済みと明記し、実計算も `:717` で条件 1・2 の連言です。D510 は旧保証の撤去を記録しています (`docs/decisions.md:21229–21242`)。本プランに判定式の編集はないため、これ自体を成果物値が変わる must-fix とは数えませんが、完了報告で「旧三条件を維持した」と書くのは誤りです。

- **real・nit — §10 の仕様発効から測定認可を導けません。**
  親 brief 冒頭の理由付けには飛躍があります。`docs/phase3-8b-descriptor-design.md:547–553` と D510 決定 7 (`docs/decisions.md:21257–21260`) は仕様発効と測定認可を区別しています。本 wave の明示的な撤去承認とは別に扱う必要があります。

## refuted と判定した所見

- **refuted — 8c 冒頭追記で protected hash が動く。**
  `_section_bounds` は §1〜§7 の位置から範囲を作り (`s8c_preregistration.py:710–744`)、規範本文は §1・2・3・4・6・7 だけを採ります (`:1032–1058`)。提示文面を `## 0.` の直前へ挿入し、既存 parser でメモリ上の比較を独立に実行しました。**抽出された契約全体が一致**し、protected hash は前後とも以下でした。

  ```text
  1e325f9d9ce483b14d02e2c857f785007afa45005112127312b409d77cfee684
  ```

  C02 契約は arm binding の単射性を要求し (`s8c_preregistration_evidence_contract.v1.json:91`)、評価器の終端も非充足です (`s8c_preregistration_evidence.py:2049–2052`)。追記はこの限界の明記であり、8b の中立 off 入力 (`docs/phase3-8b-descriptor-design.md:163`) と矛盾しません。D911 の据え置きに適合します。

- **refuted — 現計画の編集で generator identity が動く。**
  `M:65–73` の 5 file に予定編集対象はありません。検査も各指定 file 自体の hash を比較します (`M:478–495`)。**この限定された主張は親・段 2 とも正しい**です。manifest 自身の ID/hash が不変という意味ではありません。

- **refuted — D1433/D1434 が T-434 の部分実装を可能にした。**
  D1433 は単一導入 commit と先行順序を維持し (`docs/decisions.md:45475–45481`)、D1434 が閉じたのは所有の問いだけです (`:45491–45497`)。現コードも正常な前段検査後に無条件で `P6Unavailable` を返します (`reflux_formal_consumer.py:1479–1491`)。P1 を覆す材料はありません。

  記録では「所有裁定済み」「P6 充足未実装」「T-434 未完了」を分けて残せば足ります。所有 task は既に起動歴もあります (`docs/phase3.md:1304`)。再裁定や新しい起票は不要です。

- **refuted — A/B 自体が variant の anomaly 判定を緩める。**
  A/B が読むのは floor/budget の形・値・hash です。correctness-red の失格と legacy/S2 の PASS 要求は別に残ります (`s8b_oracle_judge.py:281–296`)。ただし、**C の全削除には前述の SWO 証跡依存があります**。

## scope 外の裁定候補

新しい gate・台帳・互換層・一般硬化の提案はありません。C のアンカー訂正は、既裁定の撤去対象を現コードへ正しく対応づける問題です。

## 総括

**B(a)・8c 冒頭追記・T-434 の記録照合は進められます。A は完全代替を撤去条件にせず、C は親 brief の対象指定から修正が必要です。**

静的読取とメモリ上の hash 比較のみ実施しました。編集・commit・pytest は行っていません。