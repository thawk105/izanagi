**P7 は must-fix です。存在履歴の検査を先送りするなら、本単位では v3 の `certified=True` を止める必要があります。** identity の基本設計に、表を落とす確定的な欠落は見つかりませんでした。

以下は静的読解による所見です。実装・テスト・変異は実行していません。`plan` は指定の `s2-plan.md`、`brief` は `s1-brief.md`、`設計` は指定 README、コードの短縮名は `orchestrator/verifier/` 配下を指します。

## 所見

| 番号 | レンズ項目 | 所見 | real/refuted の見込み | 重大度 | 根拠 file:line | 成果物への影響 |
|---|---|---|---|---|---|---|
| F1 | A6・P7 | unborn の genesis 読み、DELETE 版の live 読みを認定できる。後述の反例では既存 integrity は全て通る | **real：静的に成立** | **must-fix** | 設計:83–84、plan:354、dsg.py:238–243,650–669、model.py:450–467,518–520 | 本来 indeterminate の v3 が、X/P 証拠が揃うと `certified=True` になる |
| F2 | A6・認定経路 | 「pipeline が tpcc を拒否する」から「本単位の偽認定は使われない」への一般化は成立しない | **real：保護範囲の過大評価** | **must-fix：F1 と同じ修正** | brief:58–61、pipeline.py:434–437、cli.py:70–75,105–110、core.py:373–385 | 通常の tpcc binary の pipeline 投入は止まるが、公開 API／CLI の v3 認定は止まらない |
| F3 | A1(a)(c) | 別表・同一 hex の衝突は、提案された全 lookup を変更する限り不成立。object、compact intern、packed の read-only 解決、tuple worker、復元まで変更対象に入っている | **refuted：不成立** | nit／修正不要 | plan:20–52、parse.py:520–543、dsg.py:405–421,514,650 | `(0,"aa")` と `(9,"aa")` は別 object。表落ちによる辺の混同は設計上閉じている |
| F4 | A1(b)・A4 | table の `1/01/+1/001`、`0/-0` は整数化で同一になる。字句揺れによる分裂は不成立。ただしこの正規化を直接守る受入例が未記載 | **攻撃は refuted、検査不足は real** | should | plan:86,280,350、parse.py:310,315–319 | 設計どおりなら辺は不変。実装が raw table token を intern に使う退行を現計画だけでは明確に検出できない |
| F5 | A2 | v2 の型・intern 順・key 採番・辺追加順を保存する方針は妥当。identity の tuple 化だけで v2 の set 反復順が変わる経路は見つからない | **refuted：不成立、実証は未実施** | nit／方針維持 | plan:54–64,110–142、dsg.py:624–635、test_verifier.py:2583–2594,2647–2674 | v2 の witness、repr、JSON bytes を変える必然性はない。既存 golden の実行は必要 |
| F6 | A3 | failure／NeedsLegacy に最初の C 観測を保存し、sorted path 順に混在を判定する設計は、成功 columns だけの検査の穴を塞ぐ | **refuted：混在受理の攻撃は不成立** | nit／方針維持 | plan:94–104、parse.py:547–600,700–713,827–835 | 混在は last-wins や overflow で隠れず ParseError。P/A／空 file は schema を解除しない |
| F7 | A4 | C/R/W/X/I の token 数、値域、W op、nS/nQ、S/Q、件数・E の扱いは列挙されている。並走返信の正常形式を拒否する確定的な不整合はない | **refuted：不成立** | nit／方針維持 | plan:74–86,279–286、parse.py:402–428、request-t2854.md の返信 | 形式不正は ParseError、件数・終端不正は integrity。I 行の受理も違反として非認定に倒れる |
| F8 | A5 | cycle の tx_type を `_txn_for_id` から採る設計は last-wins と整合する。ただし v3 の「同一 txid・異なる tx_type・勝者が cycle に入る」試験がない | **誤帰属の攻撃は refuted、検査不足は real** | should | plan:152,271,276、parse.py:743–747、dsg.py:764–772、test_verifier.py:3074–3099 | 設計どおりなら勝者の取引種別になる。誤った row から復元する退行の検出が不足 |
| F9 | A5 | 新関数は表・取引種別を構造化できる。一方、既存の公開 `result_to_dict`／CLI／capability digest は v3 情報を落とす | **real、明示された scope 制限** | should | plan:154,193,245–248、report.py:17–40、__init__.py:42、core.py:256 | 新関数経由では保存されるが、既存 JSON では別表の同じ hex を区別できない。本単位で CLI 配線を要求する所見ではない |
| F10 | A1(c)・A7 | v3 の整数 overflow fallback は計画済みだが、parse／edge pool 障害から逐次へ戻る v3 試験は明記されていない | **real：検査不足。表落ち自体は未立証** | should | plan:258–274,308、parse.py:817–820、dsg.py:607–614、test_verifier.py:3299–3371 | 既存 v2 fallback 試験だけでは、新しい table／tx_type／schema 状態の保存を確認できない |
| F11 | A7 | 変異 #5 は親 outcome 走査と merge の二重検査に遮られる。片方だけを外しても同じ混在入力は拒否される | **real：帰属不成立** | **must-fix：変異計画** | plan:96,99,320 | 「赤だから親のその検査が効いた」とは結論できない。未実装を検出する受入の根拠が曖昧になる |
| F12 | A2・親の閉包検索 | repr／JSON pin の指摘は確認できた。ただし「固定 hash hit がない」から「中身の編集では赤にならない」は広すぎる。consumer 無関係の判定も直接 import の有無だけでは足りない | **real：一般化の問題** | should | s1-closure.md:7–14、brief:44–45、core.py:256–264、test_verifier.py:2893–2956 | path を維持しても出力変更は golden／digest に影響する。固定 source hash の不在と互換性保証を分ける必要がある |
| F13 | A4・実アンカー | 「NewOrder/Order の番号が射影本文にない」は誤り。brief に 5／6 が明記されている。また受理試験の「INSERT/DELETE/UPDATE の文字列」は wire の `I/D/U` と区別すべき | **real** | nit | plan:269,281,306、brief:26–27 | 実装を誤らなければ判定への影響なし。文字列をそのまま fixture にすると予定どおり ParseError になる |

F4 の補足として、key の `"01"` と `"0001"` は異なる **bytes** です。table 番号の先頭ゼロと違い、これを同一化してはいけません。大文字 hex 等は既存 `_check_key` により integrity 不良になります。空白も `split()` の区切りとして扱われ、整数化後の table に残りません。

## P7 の具体的な反例

次は plan を実装した場合の静的予測です。現在の v2 parser で実行した結果ではありません。

**初期不存在の key を genesis から live に読む例：**

```text
C 0 0 2 1 0 1 0 0 1
W 0 5 aa I 2 1
E 0
C 1 0 2 2 1 0 0 0 2
R 1 5 aa 1 0
E 1
```

最初の committed write が INSERT なので、設計 §3.3 では `(5,aa)` に genesis の live 値はありません。しかし既存の辺構築では genesis 読みを orphan にせず、`1→0` の rw だけを作ります。cycle、欠番、版不一致、件数不一致はありません。

**DELETE 版を live に読む例：**

```text
C 0 0 2 1 0 1 0 0 1
W 0 5 aa D 2 1
E 0
C 1 0 2 2 1 0 0 0 2
R 1 5 aa 2 1
E 1
```

こちらは producer が存在するため orphan にならず、`0→1` の wr だけです。DELETE の意味を検査しなければ認定条件を通ります。

いずれも X/P の proof surface が認定条件を満たす source context と、必要なら一致する `expected_commits=2` を与えると、plan のままでは `certified=True` になります。source context 未指定なら既存の別条件で indeterminate になるため、**反例試験では必ず X/P 条件を満たす必要があります**。既存 test の wrapper もその条件を与えています（`test_verifier.py:58–62`）。

これは隠れた G2 cycle を実証した例ではなく、**設計が明示的に非認定とする存在履歴を誤認定する例**です。

pipeline の allowlist は通常の `tpcc_*` binary を拒否しています。その狭い主張は正しいです。ただし検査対象は binary の basename であり、verifier の schema ではありません。CLI はその allowlist を通らず、capability の内部呼出しにも v3 非認定条件はありません。既存 ladder の呼出しは YCSB 証拠の再検証ですが、それを公開 API 全体の保護と一般化できません。

## 変異候補ごとの帰属

| plan §8 | 判定 | 帰属を成立させる条件・修正 |
|---|---|---|
| #1 object helper の table 削除 | 成立見込み | legacy の参照辺集合を直接比較する。compact 比較だけで終わらせない。主 fixture は表を落とすと余分な ww が増えるため有効 |
| #2 compact intern を raw hex 化 | 条件付き | 最初に **異表の token ID が異なる**ことを検査する。後段の version-dup や anomaly 復元例外だけを赤の根拠にしない |
| #3 packed read-only 解決の table 削除 | 条件付き | 別 file に同表の writer を置く。単に tuple map を raw str で引く変異と、表を無視して別表へ接続する変異は分ける。前者だけでは「表の混同」の control にならない |
| #4 tuple builder／worker の table 削除 | 分割必要 | builder だけ、worker だけ、両方の変更を別変異にする。片側だけでは identity 型不一致による orphan／辺消失でも赤になる |
| #5 親の file 跨ぎ schema 検査削除 | **現記述では帰属不能** | outcome 走査と merge のどちらを外すか明示する。両方が独立防壁なら、各層の直接試験と「両方を外す組合せ変異」を区別する |
| #6 failure 全件先行処理 | 成立見込み | 両実装とも拒否するので `raises(ParseError)` だけでは殺せない。早い混在の path・行・メッセージを exact 比較する |
| #7 tx_type 範囲検査削除 | 成立見込み | `0`／`6` の独立した正常 frame を使う。`x`／`1.0` は字句検査が拒否するため範囲検査の control ではない |
| #8 nS/nQ 非ゼロ受理 | 成立見込み | S/Q 行を付けず、nS または nQ **だけ**を `1` にする。未知 tag や字句違反との複合例では帰属できない |
| #9 `_reasons` の raw key 化 | 条件付き | graph は正常のまま、ww/wr/rw の理由をそれぞれ直接比較する。同一 txn が異表の同じ hex を書く例も加え、辞書で一方が潰れる退行を捕える |
| #10 tx_type 固定／table 出力省略 | 分割必要 | 復元の変異と出力の変異を別々にする。異なる tx_type の節点を持つ cycle を使い、型付き anomaly と新 dict を別々に検査する |

不足している control は、少なくとも次です。

- table の字句検査・値域検査・整数化を別々に外す変異。R/W/X/I を独立した fixture にする。
- `01` と `1` の正規化を外して、同一 object の依存辺が消える変異。
- v3 の parse／edge pool 障害 fallback と、legacy 復元で metadata を落とす変異。
- 同一 txid の別 file 版から古い tx_type を選ぶ変異。
- X/I の違反収集または core への配線を外す変異。循環・他 integrity 違反のない frame を使う。
- F1 の存在履歴検査、または暫定の v3 非認定条件を外す変異。

## plan への修正提案

1. **P7 を修正する。** 本単位で §3.3 の存在履歴を実装するか、未対応の間は v3 を明示的に非認定にする。後者でも parse、辺集合、cycle、構造化 anomaly は受け入れられる。存在履歴の実装そのものは単位 5 に送れても、偽の `certified=True` は送れない。notes の追加だけでは `Integrity.clean()` は変わらない点に注意する。

2. **字句契約を確定する。** plan の案を採るなら、新整数 field は `[+-]?[0-9]+` の全体一致後に整数化し、全経路でその整数を使用する。先頭ゼロ・符号付きゼロ・不正な underscore・空白の試験を明記する。canonical 表記だけを要求する根拠は現資料にはない。

3. **受入を補強する。** v3 の pool 障害 fallback、同一 txid の勝者 metadata、同一 txn 内の異表同 hex、表番号の表現揺れを追加する。X/P 不足が別の不具合を隠さないよう、認定に関する各試験の source context を明示する。

4. **変異 #5 の二重防壁を明記し、#4／#10 を分割する。** 各変異に「到達する層」「最初に失敗すべき assertion」「それ以前に拒否されない条件」を付ける。

5. **出力と閉包検索の説明を限定する。** 本単位の v3 構造化出力点は `core.result_to_dict_v3` と明記し、既存 serializer の v3 対応完了とは扱わない。source hash の検索結果も、全 consumer の互換性を証明したとは記さない。

## 総括

- must-fix は、存在履歴未検査の v3 に認定を返す P7 と、変異 #5 の帰属の曖昧さです。
- unborn の genesis 読みと DELETE 版の live 読みは、plan のままでは認定条件を通ります。
- pipeline の tpcc binary 拒否は確認できましたが、公開 API／CLI の認定を保護しません。
- 存在履歴を後続へ送るなら、本単位で v3 の非認定を保証してください。
- `(int(table), key_hex)` と全 lookup の変更方針では、表衝突・表記揺れによる分裂攻撃は不成立です。
- schema 混在、厳格 parse、v2 の順序・型・bytes 保存の基本方針は妥当です。
- v3 fallback、last-wins metadata、整数正規化の受入と変異 control を補強する必要があります。
- 本レビューは静的読解のみで、変更・テスト実行・変異の実測は行っていません。