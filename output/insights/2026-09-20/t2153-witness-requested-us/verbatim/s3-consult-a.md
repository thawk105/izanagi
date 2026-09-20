## 所見

**現 plan は条件付き NO-GO です。** 総数の相殺への補正は必要ですが、個別観測の保存・再検証と、補正後の変異帰属が未整合です。指定4資料と参照コードを静的検査しました。編集・pytest・前処理の実走はしていません。

以下、G＝[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/campaign/condition_meaning_gate.py)、T＝[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/tests/test_condition_meaning_gate.py)、plan＝[段2 plan](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/artifacts/dev-wave-t2153-witness-requested-us/plan.md) とします。

1. **real／must-fix：個別観測を追加する計画と、green evidence の契約がつながっていません。**

   plan:98–102 は file・site ごとの `(v,1)` を要求しますが、plan:112–118 の副 row は source metadata のみです。plan:132 の再検証も総数だけです。現物でも G:3191–3200、3378–3394、4039–4062 が運ぶ・検査する観測は総数です。

   したがって実行時に相殺入力を拒否できても、記録から「owner の各箇所1回＋header の各箇所1回」を再検証できません。副 file の `site_count=2` は宣言数であり、観測数ではありません。

   REQUESTED_US 限定の evidence に**主・副双方の箇所識別と両腕の個別観測**を保存し、登録簿から導出した箇所集合と照合する設計まで決めるべきです。既存 dataclass の変更は不要です。

   **放置時の影響：レポートは全4箇所の観測を主張する一方、green record の再検証は総数一致しか裏付けません。**

2. **real／must-fix：m3 の失敗予測は、個別 marker 検査の導入後には成立しません。**

   plan:187 は総数を4→2へ戻すと、missing-include 入力が `_assert…` を通ると予測しています。しかし plan:98–101 の個別検査では、header の completed が各0なので拒否されます。schema を迂回する直接呼出しでも、この別防壁は残ります。

   また plan:101 の「総数を先に検査」と、plan:189 の G:3184–3200 に置く「個別 marker 等値検査」は順序が一致しません。現物では `_compile_time_observation` を G:3328 で呼んだ後、G:3356–3376 で総数検査します。

   m3 は正常な4箇所入力を誤拒否する変異として検出できます。ただし「未 include を通す総数検査の欠陥」を単独検出したとは報告できません。

   **放置時の影響：変異台帳が、別防壁による拒否を総数検査の実効性へ誤帰属します。**

3. **real／must-fix：親の総数による全箇所性は反例が成立します。plan の補正を任意扱いにできません。**

   G:2997–3028 は同じ marker を各箇所へ挿入し、G:3203–3204 はその出現数を数えます。owner の2箇所を外側条件で不活性にし、pragma once のない header を2回展開すれば、静的宣言数は2＋2のまま、総数は `(4,4)/(0,4)` になります。plan:94 の反例は成立します。

   個別のケースでは、header 未 include は completed 2、2回展開は6、3回展開は8、owner の1箇所不活性は3です。しかしこれらを別々に拒否しても相殺は防げません。

   **放置時の影響：未観測箇所を含む入力から REQUESTED_US が未確立一覧から消え、certified-selection の意味確立を過大表示します。**

4. **real／must-fix：header 全体・他 TU への一般化を、成果物の主張から明示的に除く必要があります。**

   実 patch の4箇所は `patches/silo-backoff-requested-us.patch:29,41,60,178` と一致しました。実木の `cc/silo/include/transaction.hh:9` が header を取り込み、`cc/silo/ycsb_silo.cc:8` も同 transaction header を取り込みます。

   今回観測する compile operand は transaction.cc だけです。ycsb_silo.cc の先行 define、include 順、compile argv で同じ結果になることは観測しません。G:12–25 の現在の一般的な主張境界に加え、**副 file の証拠は指定 owner TU・当該 configure の include 文脈に限定する**旨を docstring と成果物の説明へ明記してください。副 row の path/hash だけを独立した header 証明として読ませてはいけません。

   **放置時の影響：レポートが transaction.cc の witness を、他 TU を含む header 全体の意味確立へ拡張して読めます。**

5. **refuted／nit：副 mapping の追加自体が factory・旧宣言経路を広げる、という反論は成立しません。**

   G:1018–1028 は主 entry の owner 条件、NOINLINE 特例、`#ifdef` 条件を分離しています。主 entry を維持する plan なら、副 file のために owner 条件を緩める必要はありません。G:678、3475–3477、3933、3952、4284 は旧経路を BACKOFF_FIXED に固定しています。

   条件は、これらの判定を変更せず、副 row を `ConditionalBranchMeaningDeclaration` として発行しないことです。REQUESTED_US の非対値・旧 CLI 拒否を追加する plan は妥当です。

   **放置時の影響：現提案のままなら既存受理集合の拡大は見つかりません。owner 条件の緩和を実装時に加えれば、この結論は失効します。**

6. **refuted／nit：同一 shadow の2 file 計装だけで argv 比較・supply closure が壊れる、という反論は成立しません。**

   G:3128–3132 の `-ffile-prefix-map` は同じ instrumented root を両腕で使います。G:3282–3290 も shadow を1回だけ作ります。G:2157–2164 は対象 define 以外を comparable に残すので、新しい marker 定義を使う場合も両腕で同一なら比較可能です。

   supply closure は元 source を G:2196–2246 で読む別経路です。meaning の計装本文を supply closure へ混ぜる設計にはなっていません。ただし G:3088 の symlink 除外を全計装 file へ広げることは必須です。既存 symlink へ書けば元 header を変更し、この分離を壊します。

   **放置時の影響：plan 通りなら干渉はありません。副 file の symlink 上書き漏れがあれば、元 source と以後の supply digest が変わります。**

7. **real／must-fix〔検証・報告条件〕：既存21 macro 不変の主張を、2 cell の比較だけで満たしたことにしてはいけません。**

   brief:27 は21件の不変を掲げますが、実 TU 比較は SORT／NOINLINE です。plan:203–224 の固定 serialization と同一 source roots の比較を組み合わせる方向は正しいものの、全21件比較が「可能」という記述に留まっています。

   T:1607–1626 の現行 test は SORT の key 集合を検査するだけです。G:817–841 は nested field の値も canonical JSON に含めます。固定期待は変更前実装から採取し、変更後の field 列挙から生成しないこと。supply・meaning・admission の比較範囲も区別してください。

   **放置時の影響：未比較19件を含む bytes 不変が台帳上の実証済み事項になり、互換性の根拠が過大になります。**

## 親 brief への反論

- **P1・P3・P4 は採用可能です。** P4 の意味は「owner TU の数」ではなく「主宣言 file の数」です。NOINLINE の主宣言は header なので、ここを曖昧にしないでください。S1 helper の `test_s1_direct_comparison.py:719–729` は主 N を維持すれば現契約と整合します。ただし REQUESTED_US の副 header は生成しません。本 wave で同 helper を複数 file 対応済みと呼ぶことはできません。

- **P2 は source metadata の整合検査として妥当ですが、個別観測を加えた plan には不足します。** 登録依存の required/unexpected、exact int、row 順序、片側 digest 改変の拒否は有効です。一方、row と `CapturedFileEvidence` の sha256 を同時に同じ別値へ変更し、record digest も再生成すれば、自己整合性だけでは改変を識別できません。これは現行主 source にもある境界です。G:1118–1120、4153 の issuer 契約と区別し、「schema が任意の偽造を検出する」とは主張しないでください。

- **P5 の静的根拠は確認できましたが、実測扱いは不可です。** 実木の `cmake/Options.cmake:20,73` は BACK_OFF の既定1と mapping、`transaction.cc:152–167` は外側条件です。これから3/4を予測できますが、既定値は全 configure の実効値を保証しません。BACK_OFF=0 の red は今後の観測項目です。

- **P6 は個別観測込みで採用してください。** `#pragma once` は当該 header の再展開を抑制しますが、任意の gate 入力で「必ず1回到達する」証明にはなりません。

- **P7 は帰属の修正が必要です。**

  | 変異 | 判定・条件 |
  |---|---|
  | m0 | mapping 行末の通常 comment なら意味上等価。module bytes は変わるため、全成果物の bytes 等価とは呼ばない。 |
  | m1 | 独立 fixture の2箇所と宣言1の不一致。複数 node の失敗でも同一変更に帰属可能。 |
  | m2 | 元 header 本文を残す変異に固定する。file 削除による include error と区別する。 |
  | m3 | 個別検査による拒否が残る。正常入力の過剰拒否として数えるか、検査単位を分離する。 |
  | m4 | 原案は診断の変化。m4′の相殺入力による検出を採用する。 |
  | m5 | required だけでなく副検証の適用条件を変える plan の補正が必要。 |
  | m6 | fixture の KeyError を避け、factory None／unestablished を観測する。 |
  | m7 | 正しい形式の digest を片側だけ変更し、他条件を通す。両側改変検出の証明ではない。 |
  | m8 | schema による既存正例の拒否を検出する有効な過剰拒否変異。ただし bytes 比較到達前の失敗を bytes pin の成果に数えない。 |

- **P8 の実 TU cell は省略できません。** 今回読んだ実木では、逐語4箇所と `backoff.hh:1` の pragma once を確認しました。しかし `primary-verbatim.md:151–158` の NOINLINE 緑は別 define の1箇所、REQUESTED_US は未確立です。両者を合わせても4箇所同時観測の実証にはなりません。

## 段 5 実装子へ渡すべき条件

1. **主2＋副2を独立期待として固定する。** 主 N、副 N、総 N の用途を分け、実評価と green 再検証の総数は同じ登録情報から導出する。既存 factory・旧宣言条件は変更しない。

2. **総数と個別観測の両契約を完成させる。** 箇所ごとに要求 `(1,1)`／対照 `(0,1)` を検査し、その観測を REQUESTED_US 限定の canonical evidence に残す。欠落・重複・不正個別数・総数との不整合を再検証で拒否する。総数検査と個別検査の順序を固定する。

3. **同一 shadow に全計装本文を書く。** 全計装 path を symlink 作成対象から除外し、元 owner/header の bytes 不変を検査する。未 include、未計装、二重展開、pragma once 付き再 include、不活性、相殺入力を分けて確認する。

4. **schema test の失敗原因を限定する。** 改変後の public record を再構成し `require_issuer=False` で検査する。REQUESTED_US の副 key 欠落と、単 file macro の余分な副 key を両方拒否する。

5. **fixture の代表性を実 TU 観測で補う。** `_SUPPLIED` は `supplied/cc/silo/transaction.cc:12–15` の関数内直接 include で、実木の中継 header、pragma once、class 内の signature／return、BACK_OFF の外側条件、実依存群を再現しません。plan の中継 fixture は改善ですが、fixed patch の EVOLVE-BLOCK と共存する実木の緑は別途必要です。

6. **最終 production で login／計算ノード双方を観測する。** pin、patch 重ね順、official 同形供給、実効 argv を記録し、両腕の総数・個別数、両 source hash、supply closure、green／admitted／未確立空を確認する。BACK_OFF=0 は3/4で拒否することを別 cell で確認する。これは実行時の requested-us 計数値や他 TU の正しさの証明ではありません。

7. **変異台帳を補正後の検査構造に合わせる。** 特に m3、m4′、m8 は、どの検査が落としたかを分ける。個別観測を schema に保存した場合、m4′も schema に遮られ得るため、評価側の直接検査を独立させる。

## 総括

主2-tuple＋副 mapping＋同一の深い shadow という骨格は妥当です。修正必須なのは、**個別観測まで閉じた evidence 契約、m3 の帰属、owner TU に限定した主張、既存21件不変の検証範囲**です。親の静的4箇所は確認できましたが、4箇所同時 green は未実証です。本回答は静的検査のみです。