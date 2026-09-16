## 致命的な所見

**[refuted・静的読解] 計画どおりの変更から certified 最終受理へ到達する経路は、今回確認した consumer では見つからなかった。**

- view は `artifact_admission.py:1542` の exact 型検査で拒否される。
- decision を取り出しても、計画の `historical-not-reclassified` は `layer3_report.py:279,959`、`autonomous_trial_completeness.py:4798` を通らない。
- Layer 3 はさらに `layer3_report.py:966` で certified admission を再実行する。completeness も `autonomous_trial_completeness.py:4965` で再実行し、decision を照合する。
- records は `artifact_admission.py:1498` で immutable projection になる。`admit_persisted_certified_commits` の production 呼出しは同 `:1492` の certified 分岐内であり、歴史 view の発行では呼ばれない。

ただし **epoch の型拒否を policy 差の防壁として数えてはいけない**。現行 closure grammar の歴史入力は通常の `CampaignVerifierEpoch` になる（同 `:1067–1077`）。旧 policy だから `HistoricalCampaignVerifierEpoch` になるわけではない。policy 差を止める責任は現行一致検査に残る。

成果物影響：計画上、旧 policy の certified 選択への流入は確認できない。epoch gate 単独ではその不変条件を保証しない。

## 重い所見

**1. [real・静的読解] P1 の形検査は、偽造 policy による歴史受理を防がない。**

[s2-plan.md:69](/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/s2-plan.md:69) の表どおりなら、例えば次の記録 policy は形検査を通る。

```json
{
  "schema": "build-admission-policy/v1",
  "repo_stock_pin": "0123456",
  "coder_authority": "no-opt-in",
  "generator_registry": ["invented-generator"],
  "review_registry": ["invented-review"]
}
```

有効な非 trigger の v2 campaign を土台に、lock と WAL を整合的に書き換えると、次が可能になる。

- `coder-authored` receipt の authority を `no-opt-in` にする。
- generator／review receipt に上記の架空 ID を入れる。
- stock source・lock の commit を記録 pin に合わせる。
- policy SHA、receipt の canonical SHA、各 stage の伝播 SHA を再計算する。

計画では、現行の `build_admission.py:548,709,718,734` が拒否するこれらの値を、歴史入口が受ける。`wal.py:2157` の receipt 検査、`:2165` の伝播 SHA、`artifact_admission.py:1416` の source commit 照合も、整合的な書換えなら突破する。これは検査の省略ではないが、**外部の登録・authority との照合が自己申告の整合確認へ変わる**。

M7 の「artifact 内 policy を期待値へ流用しない」とは、文字どおり異なる設計である。しかも先例は policy SHA の比較を外しても、`s8b_binary_admission.py:362` で `HUMAN_REVIEWED`／`S8B_FLOOR` を固定している。任意の記録 registry を信じる先例ではない。

内的整合だけになるのは、上記四つの policy 値の比較と `build_admission.py:687` の policy SHA 比較である。campaign 全体が内的整合だけになるわけではなく、記録 commit blob 検証と activation chain 検証は残る（`artifact_admission.py:1051,1173`）。

歴史閲覧として採るなら、保証は「記録 policy と記録 receipt が整合する」までである。「当時実在した policy」「当時承認された generator／authority」の検証とは呼べない。追加の台帳は勧めないが、親の不変条件4の説明はこの限界に合わせて訂正すべきである。

成果物影響：架空 policy を整合的に名乗る記録も材料レポートへ入る。計画の非認証 status が維持される限り、これ自体は certified 受理を与えない。

**2. [real・静的読解] 共有 helper 抽出による現行入口の退行を、計画の負例では十分に切り分けていない。**

[s2-plan.md:195](/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/s2-plan.md:195) の certified 負例は、lock の旧 policy を入口で拒否するテストである。これでは、その後の現行 receipt validator が弱くなっていても検出できない。同 `:197` の現行 policy 正例も拒否集合を検査しない。

具体的な変異は、現行 wrapper が共有 helper に渡す stock 比較値を `CURRENT_PIN` ではなく receipt 自身の source commit にすること。比較は恒真になるが、旧 policy の入口拒否と現行正例は維持される。同様に generator の許可集合を提示された ID から作れば、登録検査が恒真になる。

既存の `test_build_admission.py:163` は `derive_build_admission` の旧 pin 拒否であり、persistent validator のこの変異を直接検査していない。`:268` の receipt 変異も outer SHA 不一致で止まる。

必要なのは今回抽出する比較について、**現行 policy SHA を維持し、digest を整合させた不正 receipt を現行入口へ渡す負例**である。旧 stock pin、未登録 ID、異なる authority を各比較まで到達させる。これは新 gate ではなく、既存拒否集合の固定である。

成果物影響：抽出時に比較対象を誤ると、現行 policy の campaign に不正な build provenance が入り、certified 受理集合が広がり得る。

## 軽い所見

**3. [refuted・静的読解] 指定された構造検査を歴史側だけ落とす指示は、計画にはない。**

対応を一つずつ確認した。

| 検査 | 現行位置と計画上の扱い |
|---|---|
| historical COMMIT contract | `artifact_admission.py:1377`。専用照合を維持 |
| trigger bindings | 同 `:1390`。`require_build_start=True` を維持 |
| trigger provenance | 同 `:1397`。WAL start と provenance entries の対応を維持 |
| source／genome／variant | 同 `:1410,1421`。維持 |
| lock／WAL 再読照合 | 同 `:1430`。維持 |
| knowledge／backoff grammar／contract | `wal.py:2126–2132`。共有抽出範囲に含まれる |

特に historical decoder の identity を topology に渡すと、通常 contract validator は `wal.py:2069` で戻り得る。これを補う `artifact_admission.py:1379` の専用検査は、共有 helper があることを理由に削ってはいけない。

成果物影響：計画に明示された検査脱落はない。専用 contract 検査を削る実装変異では、COMMIT と lock authority の不一致が材料へ入る。

**4. [refuted・静的読解] 形検査が恒真になる、という攻撃は現プランには当たらない。**

独立 key literal／schema literal を使い、空 WAL でも malformed policy を検査する設計である（`s2-plan.md:48,58,196`）。余分 key や schema 違いは実際に偽となる入力を構成できる。変異3・4はその検査を狙っている。

ただし「現行 literal と一致する」というテスト自体は authenticity の証拠ではない。所見1の偽造 policy は、形検査を正しく実装しても通る。

成果物影響：形検査は malformed object の受理を防ぐが、架空の policy 値の材料投入は防がない。

**5. [refuted・静的読解＋履歴参照] P1 が実在の旧 policy の形を拒否する実例は確認できなかった。**

M4 が挙げた `.../p3-t178-ycsb-a-workload-conditioned-autonomous-0a11751c/campaign.lock:1` と `...-9785aec6/campaign.lock:1` は、旧 pin `d706650` でも同じ五 key／schema literal を持つ。`git show a21bf413e:orchestrator/campaign/build_admission.py` の `_new_policy` も同じ形だった。

この二件は v1 かつ M4 によれば WAL 不在なので、今回の v2 成功例には使えない。将来 schema が変わる仮想例を、実在の旧 policy の拒否例として提示することもしない。

成果物影響：確認した旧 preimage について、形制約が歴史閲覧を塞ぐ証拠はない。

**6. [refuted・静的読解] 新 classification と schema の相殺は、指定位置なら対で効く。**

`layer3_schema.json:22` は `admission_decision` を必須とし、`:290` は classification を必須にする。したがって `:12` の `then.properties.admission_decision.properties.classification` に従来二値を置けば、全体 enum の新値追加を `certifying_input=true` に限って相殺できる。

変異9は、既存の有効な certifying report の classification だけを新値へ替え、historical marker を持たせない schema 単体負例なら検出できる。アプリ側 status 拒否で代用すると、この相殺の実効性は証明できない。

classification は epoch object の外なので、D1365 の nested object／reason enum／`current-closure-unavailable` 不変更にも抵触しない。D259 の downgrade、D1653／D1770 の別入口・別型も計画は維持する。D1841 は別の attempt 選別の裁定であり、記録 registry の真正性を保証する根拠にはならない。

成果物影響：相殺を欠く実装では、新 classification の certifying report が schema 単体では受理される。

## 親 brief と実測への指摘

**7. [real・静的読解] M10 は必要条件を、最終昇格経路の成立へ一般化している。**

[parent-position.md:24](/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/parent-position.md:24) の「返すと certifying input の条件を満たす」は、status 条件については正しい。しかし前述の certified 再 admission が残るため、「実経路がある」とする見出しは立証過剰である。

`CampaignAdmissionDecision.admitted` の production 直接参照として確認したのは、中央入口 `artifact_admission.py:1482` と `backoff_requested_us.py:521`。後者の値は `:518` の certified 固定 `classify_campaign` 由来である。他の確認した campaign driver の `.admitted` は condition-meaning gate の別型だった。歴史 decision のこの property だけで昇格する経路は確認していない。

成果物影響：現状の最終受理変更は未立証。status 非認証化の理由と、最終 certified gate の保証を混同すると、後者を不要として削る危険がある。

**8. [real・静的読解] M4・M5 の結論は測定範囲を超える。**

- `measured-facts.md:58–60` は pin 一致だけを報告する。しかし比較対象は registry／authority／schema を含む全 preimage（`build_admission.py:456`）。pin 一致から「今日は発火していない」は導けない。外部20件は今回の許可範囲外で、再検証していない。
- 同 `:77–84` は未 commit 編集面を未確認と明記する。「重複なし」は予定対象の比較までに限定すべきである。さらに本プランは build admission、WAL、schema に編集面を広げている。
- brief の「編集面が1 module」は成立しない。旧 stock pin は `build_admission.py:709` でも止まるためである。
- M2 の「版上げは2事象」は網羅的ではない。authority／schema の変更も SHA を変える。
- M9 の「test からしか到達しない」は公開 API の直接呼出しまで否定している。`wal.py:2821` は policy 省略を許す。今回の歴史 admission が `_replay` を通らない、という狭い主張は読解で確認できる。

成果物影響：既存材料の停止件数と統合時の競合範囲を過小評価し得る。新しい受理集合の根拠には使えない。

**[real・nit] 参照精度にも訂正が要る。** M1 の topology 呼出しは `:1368`、policy 引数は `:1370`。plan の既存 policy 型は `build_admission.py:243`、`:258` は型本体ではない。また plan 冒頭が M6 に帰属させる「純増は policy 層の1箇所だけ」は、提示された M6 本文にはない。成果物の値への直接影響はない。

M3 の `fb5e74a17` による pin 前進は Git 履歴参照で確認した。M7 の逐語と M8 の内的整合という説明は実装に一致する。任意参照した `orchestrator/tests/test_wal.py` は存在せず読めなかったため、そのファイルの被覆は根拠にしていない。

## 総括

実装前に直すべき点は、**記録 policy の形検査を真正性の保護と扱わないこと**と、**共有 helper の現行入口を、現行 policy・整合 digest の負例で検査すること**である。

計画から certified 最終受理への具体的な突破は確認できなかった。一方、架空の policy 値を持つ整合記録が歴史材料へ入ることは、計画から導ける。その受理を「歴史上の認証の再検証」と表現してはならない。

全所見は静的読解と読み取り専用の履歴参照による。テスト・変異実行・ファイル書込み・commit は行っていない。