## 所見

以下、`L`＝`orchestrator/campaign/layer3_report.py`、`T`＝`orchestrator/tests/test_layer3_report.py`、`S`＝`orchestrator/tests/test_artifact_admission.py`。静的レビューであり、テスト・変異の実走結果は独立検証していない。

**RB-1 — I5 の現行63成功経路が比較されていない**
- **対象:** `real-probe-summary.md:15–18`、`T:1996,2048`
- **主張・根拠:** 前後比較で report 生成に成功したのは v1 の1本。残る2本は admission 拒否の一致であり、別の63対照も records/threads 検査で停止している。新規テストの decoder 型検査・knowledge helper の等価性検査は、現行63の report 全体の前後比較を代替しない。
- **判定:** **real／must-fix（検証証跡）**。同一の生成可能な現行63 campaign を変更前後で読み、generator SHA256 だけを除いて比較する必要がある。実装不具合を確認したという意味ではない。

**RB-2 — epoch の期待値が実行時に恒真化される懸念は棄却**
- **対象:** `T:1932–1936`、`S:591`、`s5-author-out.md:62–66`
- **主張・根拠:** 両 epoch は test 内の固定文字列。`_expected_pre_t733_fixture_epoch()` を呼ぶ経路は新規 fixture／test にない。62 は既存固定値の転記、24 は author が実 admission で観測したとの報告であり、両方を今回新規観測したわけではない。
- **判定:** **refuted／nit（修正不要）**。24 の「観測した」という履歴自体は報告に依存するが、再計算による恒真化は認めない。

**RB-3 — fixture は実 admission を通す構成。1/1 の assert は限定的**
- **対象:** `T:569–589,1921–1940`、`S:760–838,841–932,3194–3204`
- **主張・根拠:** committed closure repo に実 blob を配置し、binding の参照先をその repo に変更する。rewrite は authority の blob 集合だけを縮小し、canonical JSON を書く。decoder／admission／epoch を返す関数は差し替えておらず、`L:745` の実 admission と固定 E1 検査を通る構成になっている。
  records/threads の `1/1` は入力に対する固定期待値なので恒真ではない。ただし両者の入替えや常時1を返す実装は検出できず、一般的な workload 投影の証明にはならない。
- **判定:** **refuted（fixture 不成立）／nit（1/1 の検出範囲）**。本件の grammar 修正を検査する fixture としては妥当。

**RB-4 — accepted 負例の receipt seam は検査対象の外側**
- **対象:** `T:1950–1962`、`L:932–954`
- **主張・根拠:** monkeypatch は前段の receipt 検証だけ。検査対象の purpose 指定・reader・decoder は実装のままであり、brief が許可した既存 receipt seam に該当する。例外全文と exact cause 型を確認するため、後段 admission で拒否されただけでは合格しない。
- **判定:** **refuted／nit（修正不要）**。DW-O14 違反とは判断しない。ただし receipt 検証そのものや certified 経路全体の実結合試験ではない。

**RB-5 — HEAD fallback 後半は補助的な単体検査として妥当**
- **対象:** `T:2024–2044`、`L:203–217`
- **主張・根拠:** 前半は Git HEAD が取得不能な外部 campaign で、実 admission を経た builder の結果を検査する。後半は記録 authority を固定40桁値に変え、実 reader が返す historical 型から fallback がその値を取り出すことを検査する。架空 commit は blob 検証を通せないため、後半で builder を呼ばない理由は妥当。
- **判定:** **refuted／nit（修正不要）**。後半単独では admission 成功を証明しないが、前半と役割を分けている。

**RB-6 — v1 object は実際に v1。ただし disk 上の v1 campaign 試験ではない**
- **対象:** `T:2051–2078`、`campaign_lock.py:620–662`
- **主張・根拠:** `identity_preimage` は envelope のない identity JSON。通常 decoder の schema 無し分岐で `schema_version="campaign-lock/v1"`、`authority=None` の object になる。disk 上の lock は v2 のままで、比較対象は helper に明示的に渡す object／identity である。
  拒否側は両入力について exact `AttemptTopologyError` と文言一致を検査する。共通実装が同じ誤った文言を返す変異までは検出しないが、要求された表現間の拒否 parity は検査している。
- **判定:** **refuted／nit（修正不要）**。この test を v1 builder 全体の検証と説明してはいけない。

**RB-7 — 既存2テストの receipt 検証意図は保持される**
- **対象:** `T:2441–2495`
- **主張・根拠:** `CERTIFIED_ACCEPTANCE` 指定で従来と同じ通常 decoder／`DecodedCampaignLock` を選ぶだけ。検証済み receipt digest の受理、provenance 読取り後に変更された receipt bytes の拒否という assert は維持されている。この指定自体が certified admission を呼ぶわけでもない。
- **判定:** **refuted／nit（修正不要）**。

**RB-8 — consumer の新規分岐到達は本レビューでは未確定**
- **対象:** `autonomous_trial_completeness.py:4666`、`s5-author-out.md:71`
- **主張・根拠:** consumer 本体は射影外なので**範囲外**。historical campaign の fresh build が新たに成功し得ることは builder の変更から分かるが、persisted report 不在時にそこへ到達するか、どの比較・診断へ進むかは確認できない。「影響は generator hash 差分だけ」とは断定できない。
- **判定:** **real（確認範囲の不足）／裁定パッケージ候補**。親側で persisted 不在／存在の分岐順を確認すること。

**RB-9 — probe の通常実行形に campaign への書込みはない**
- **対象:** `t2718_real_corpus_probe.py:28–101`
- **主張・根拠:** campaign 入力は `read_bytes`、reader、`build_report` で読み、`render` は呼ばない。明示的な書込みは93行の `out_json.write_text` のみで、その前に全入力 campaign に対する resolved path の包含検査がある。通常の出力 symlink も検査対象になる。lock/WAL は前後 SHA256 を記録する。
  ただし `unchanged=False` や probe 内の失敗は終了コードを非ゼロにしない。**終了コード0だけでは bytes 不変の証拠にならない**。
- **判定:** **refuted（通常の campaign 書込み）／nit（結果の読み方）**。親の summary は JSON の比較結果を報告しており、その用途には合う。

## 報告と差分の対応

| 項目 | 照合結果 |
|---|---|
| reader、union 型注釈、両 builder の purpose、identity 渡し | 報告と一致 |
| Enum import、歴史 fixture、新規7関数・14ケース、既存2関数の変更 | 一致 |
| 「3ファイル・12 hunks」 | **レビュー patch は2ファイル・11 hunks**。報告にある probe 追加は patch にない |
| probe の所在 | 親 summary が repo 外への退避を明記。上記差異は説明されているが、最終成果報告は2ファイルへ更新すべき |
| 拒否 parity | 専用関数／object・identity の parametrization ではなく、既存の新規関数内で loop。実質的な検査内容はある |
| author の probe・I5 未実施報告 | 親が後で実施した記録と矛盾しない。ただし I5 の不足は RB-1 |
| 差分にあって報告にない変更 | 実質的なものは見当たらない |
| PASSED、AST比較、meta-test 実走 | 報告事項として確認。今回の静的レビューでは追試していない |

## 変異 × test 殺傷表

以下は静的な検出予測であり、KILLED 実測ではない。test 名は `test_` 接頭辞を省略。

| 変異 | 殺す test／具体的な検査 |
|---|---|
| M01 常に通常 decoder | `historical_exact_grammar_build_report[62/24]`：`T:1921` の builder が例外になり、`1936` の固定 epoch assert まで到達できない |
| M02 分岐反転 | 上記に加え `read_campaign_lock_current_and_v1_by_purpose` の `T:2012` exact 返却型 assert |
| M03 常に歴史 decoder | `read_campaign_lock_current_and_v1_by_purpose[CERTIFIED_ACCEPTANCE-*]` の `T:2012`。accepted 負例の `1960–1961` も拒否地点変更を検出 |
| M04 accepted 側を HISTORICAL_RAW | `accepted_report_rejects_historical_exact_grammar_at_lock[62/24]` の `T:1960–1961`。後段拒否では全文／cause が一致しない |
| M05 material 側を CERTIFIED_ACCEPTANCE | `historical_exact_grammar_build_report[62/24]`：`T:1921` で失敗し、固定 epoch assert に到達不能 |
| M06 exact 型検査除去 | `read_campaign_lock_rejects_non_exact_purpose`：正常 lock に対する `T:1986` の `pytest.raises(TypeError)` が成立しない |
| M07 identity を decoded object に戻す | `historical_exact_grammar_build_report[62/24]`：historical object の WAL helper 受渡しで失敗し、`T:1925–1940` に到達不能。WAL 内部の拒否根拠は brief の記述に依存 |
| M08 purpose に既定値 | `read_campaign_lock_requires_purpose` の `T:1967`。省略呼出しが成功して `pytest.raises(TypeError)` 不成立 |
| M09 型検査を read 後へ移動 | `read_campaign_lock_rejects_non_exact_purpose` の missing.lock ケース、`T:1980,1986`。TypeError より先に読取り失敗になる |
| M10 等価変異 | `L:127` を `decoded = campaign_lock.decode_historical_campaign_lock(text)`、`return decoded` に置換。呼出し回数・例外・返却値は同一。**SURVIVED 期待、expected_nodes 空** |

## 総括

must-fix **1件**：現行63の生成成功経路について I5 の前後比較証跡が不足。
**NO-GO（検証完了判定に対して）**。本レンズで実装上の確定不具合は見つからない。
親への要求：同一63 fixture の前後比較を追加し、consumer の persisted 不在分岐を確認すること。
最終報告は repo 内2ファイル・11 hunks と repo 外 probe を区別し、変異結果は実測後に確定すること。