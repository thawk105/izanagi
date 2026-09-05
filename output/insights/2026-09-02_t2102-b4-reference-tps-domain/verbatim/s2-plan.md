## 母集合の評価

親の母集合は事前登録 §5.1.1 と一致しない。`commit.payload.fitness_tps` は参考となる履歴値ではあるが、D1344 が要求する `reference_tps` の母集合ではない。

根拠は次のとおり。

- §5.1.1 の定義は、各 block の precursor から祖先方向へ辿った最初の certified snapshot と、`PerfConfig`・`env_tag` が一致する receipt である（`verbatim-prereg-5-1-1.md:38-45`）。
- 測定スクリプトは全 `wal.jsonl` を無差別に走査し（`measure_reference_tps_domain.py:111-149`）、precursor、祖先関係、snapshot hash、receipt hash、`PerfConfig`、`env_tag` のいずれも照合していない。
- `pipeline.py:1739-1744` の `fitness_tps` は、評価中の variant の bench median を COMMIT に載せた値である。祖先参照点であることは保証されない。
- 親が根拠とした `p3_b4_raw_record_producer.py:1320-1325` は、各 on/off arm の COMMIT から観測 `throughput` を読む箇所である（`p3_b4_raw_record_producer.py:1363-1369`）。`reference_tps` は別経路で、manifest row から取る（`p3_b4_raw_record_producer.py:1538-1549`, `1695-1704`, `2026-2031`）。
- 現行コードは ancestor WAL から `reference_tps` を導出しない。`B4ScheduledAttemptInput.reference_tps` は caller 入力である（`p3_b4_analysis_ledgers.py:123-143`）。issuer も caller の `scheduled_inputs` をそのまま hash・封印する（`p3_b4_prerun_issuer.py:707-780`）。さらに「caller schedule は外部の authoritative population に束縛されない」と明記されている（同 `:12-16`, `:52-64`, `:110-119`）。

D1344 に対する正しい運用上の母集合は、発行対象となる B-4 scheduled batch の `B4ScheduledAttemptInput.reference_tps` である。発行後なら sealed registry の `scheduled_attempts[*].reference_tps` が正本になる。

列挙手順は次のとおり。

1. `scheduled-attempt-registry.jsonl` を `load_scheduled_attempt_registry()`（`p3_b4_analysis_ledgers.py:702-761`）でロードする。
2. canonical 順に正規化済みの `registry.scheduled_attempts` を全行走査する。正規化箇所は同 `:439-468`、封印箇所は `:662-675`。
3. `reference_tps is not None` の全値を `Fraction` として数える。`None` は黙って除外せず、別件数として報告する。特に `reason == SCHEDULED` の行は完全な参照値が必須である（同 `:341-359`）。
4. manifest に実際に入る集合は、eligible 行の先頭 201 件からその値をコピーした `manifest.rows[*].reference_tps`（同 `:1042-1097`）。ただし D1344 は「予定された scheduled input すべて」を要求しているため、201 行だけを母集合の代用にしない。
5. 各既約分母から 2 と 5 を除き、残りが 1 かを exact に判定する。float や JSON decimal への変換は不要である。

brief によれば sealed registry / manifest の実在物は 0 件（`brief.md:58-60`）。したがって現在の結果は「historical COMMIT 852 件では非有限十進 0」であって、「予定された `reference_tps` 全件で 0」ではない。D1344 の実測は未完了と判定する。

## 狭める述語の配置 (file:line)

D1344 の正しい母集合で再測定してゼロだった場合の実装案は次のとおり。

`p3_b4_analysis_ledgers.py:263-276` の `_exact_ratio` 直後に、次の純粋な補助述語を置く。

```python
def _reference_tps_has_finite_decimal(value: Fraction) -> bool:
    denominator = value.denominator
    while denominator % 2 == 0:
        denominator //= 2
    while denominator % 5 == 0:
        denominator //= 5
    return denominator == 1
```

既存の型・正値検査を先に行い、その後にこの述語を適用する。配置は四箇所すべて必要である。

- `_validate_attempt`、現 `p3_b4_analysis_ledgers.py:341-343` の正値検査直後
  in-memory の scheduled input を封印前に拒否する。

  ```python
  if reference is not None and not _reference_tps_has_finite_decimal(reference):
      _fail("reference_tps has no finite decimal expansion")
  ```

- `_ratio_payload`、現 `:279-285` の `_exact_ratio` 成功後、payload 化前
  attempt と manifest の共通 serializer を直接使う経路も拒否する。

  ```python
  if not _reference_tps_has_finite_decimal(exact):
      _fail("reference_tps has no finite decimal expansion")
  ```

- `_ratio_from_payload`、現 `:288-302` の reduced-form 検査後、return 前
  canonical でない比は従来どおり `"wire reference_tps is not reduced"` を先に返し、canonical だが非有限十進の値だけを新しい理由で拒否する。

  ```python
  if not _reference_tps_has_finite_decimal(exact):
      _fail("wire reference_tps has no finite decimal expansion")
  ```

- `_manifest_row_payload`、現 `:931-946` の正値検査直後
  forged/in-memory manifest row を validator 単体でも拒否する。

  ```python
  if not _reference_tps_has_finite_decimal(reference):
      _fail("manifest row reference_tps has no finite decimal expansion")
  ```

`_attempt_is_eligible`（同 `:914-928`）や `generate_analysis_manifest` に判定を足して「非適格として黙って落とす」設計は採らない。違反値は registry 封印前に明示拒否すべきであり、first-201 selection の意味を変えてはならない。

`as_b4_exact_fraction`、`B4ExactRatio`、adapter、純関数 contract は変更しない。これは registry の事前受理集合だけを縮め、§5.1.1 の分析入力検証・理由 enum・判定順序を維持するためである。

## 正例と負例

- 正例: `(1, 10)`
  既約分母は `2 × 5`。`0.1` として有限十進化でき、正値なので受理する。既存 raw-record fixture の `(100_001, 10)` も同じ理由で通る。

- 発火自体を確認する負例: `(1, 3)`
  2 と 5 を除いても分母 3 が残る。registry 封印時に `"reference_tps has no finite decimal expansion"` で拒否する。

- finite decimal 境界に近い負例: `(1, 30)`
  分母は `2 × 3 × 5`。有限十進分母 `10` に素因数 3 を一つ加えただけだが、2 と 5 を除いた残りが 3 なので拒否する。wire 表現 `[1, 30]` は既約かつ canonical であるため、`not reduced` ではなく新しい finite-decimal 検査が確実に発火する。

## 影響するテスト

既存 nodeid で直接壊れるのは次である。

- `orchestrator/tests/test_p3_b4_raw_record_producer.py::test_m12_nonterminating_reference_ratio_has_only_named_rejection`
  現在は `(1, 3)` を issuer が受理し、producer の `DECIMAL_NOT_TERMINATING` まで到達する前提である（同 `:1138-1149`）。変更後は `_publication()` 内の issuer/ledger で先に拒否される。registry の事前拒否を期待するテストへ移すか書き換える。
- `orchestrator/tests/test_p3_b4_raw_record_producer.py::test_mutation_node_mapping_is_complete_and_one_to_one`
  M12 の node 名を変更する場合だけ `MUTATION_NODE_IDS`（同 `:284-303`）も更新が必要。node 名を維持して意味だけ変更するなら編集不要だが、producer mutation を検査するという旧 M12 の意味は再定義が必要である。

`test_p3_b4_analysis_ledgers.py` には次の nodeid を追加する。

- `::test_finite_decimal_reference_tps_roundtrips_through_registry_and_manifest`
- `::test_nonterminating_reference_tps_is_rejected_at_every_sealing_boundary[attempt]`
- `::test_nonterminating_reference_tps_is_rejected_at_every_sealing_boundary[ratio-payload]`
- `::test_nonterminating_reference_tps_is_rejected_at_every_sealing_boundary[wire-ratio]`
- `::test_nonterminating_reference_tps_is_rejected_at_every_sealing_boundary[manifest-row]`

正例には `(1, 10)`、attempt 負例には `(1, 3)`、wire/manifest 境界負例には `(1, 30)` を使う。四経路の拒否文言も exact に pin する。

既存の ledger tests は主に分母 1（`test_p3_b4_analysis_ledgers.py:48`）、raw producer の通常 fixture は分母 10（`test_p3_b4_raw_record_producer.py:115-125`）なので、M12 以外は値域縮小で壊れない見込みである。テスト実走はしていない。

## 文書と構造 assertion への影響

§5.1.1 の literal 一致 assertion は、上記の実装だけなら壊れない。

- 文書の raw/semantic hash pin は `p3_b4_analysis_prereg_consumer.py:47-52` にあり、照合は同 `:394-407`。
- literal 検査は理由 enum、status、順位、score、標本数、判定順序などを確認する（同 `:414-490`）。registry の pre-run 受理値域は検査対象ではない。
- 純関数 contract は引き続き「有限の正」の exact rational を扱う。registry がその上流で有限十進部分集合だけを封印することは、純関数の入力定義、判定順序、`reference_value_domain_error` を変更しない。

したがって §5.1.1 には書き足さない。D1344 の registry admission 裁定は pinned §5.1.1 の外で記録するのが最小変更である。もし親が任意に §5.1.1 へ追記するなら raw/semantic の両 SHA pin 更新が必要になるが、本実装の必須事項ではない。

構造 assertion も壊れない。

- `_assert_contract_function_shapes`（同 `:609-641`）は `evaluate_analysis` と `_evaluate_validated_analysis` の分岐だけを見る。ledger 変更とは無関係。
- `assert_contract_constants_are_source_literals`（同 `:644-675`）は contract の定数・enum と上記 function shape だけを見る。
- `_assert_source_closure_shapes`（同 `:703-754`）が ledger で見るのは `generate_analysis_manifest` の first-201 slice と、violation count が eligibility filtering より前にあることだけである。今回変更する四関数は対象外。
- `_CLOSURE_PATHS` 自体（同 `:98-104`）も変えない。

`p3_b4_analysis_ledgers.py` の source digest は変わるため、新しく生成される closure receipt の member hash と全体 hash は変わる。ただし source bytes の固定 hash assertion はなく、receipt は live bytes から生成される（`p3_b4_analysis_path.py:503-536`）。これは assertion failure ではない。

## 親の前提 P1a / P1b / P1c の評価

- P1a: **否**。
  `commit.fitness_tps` は arm の観測 throughput を含む広い歴史集合で、block precursor の祖先探索も receipt 一致も行っていない。正本は caller-supplied scheduled batch、発行後は sealed registry の `scheduled_attempts[*].reference_tps` である。なお、その値を §5.1.1 の祖先 snapshot から導出・認証する producer は、射影された現行コードには存在しない。

- P1b: **一般命題として否**。
  現行の通常 bench 経路が float であること自体は確認できる。`throughput_tps()` は float を返す（`benchparse.py:53-63`）、median も float 演算である（`model.py:236-242`）、COMMIT はその median を載せる（`pipeline.py:1739-1744`）。したがって有限 float から作られた現行履歴値が有限十進 JSON token になる、という補助証拠にはなる。
  しかし registry の直接上流は float pipeline ではなく、`Fraction | int | tuple[int, int]` を許す caller schedule である（`p3_b4_analysis_contract.py:94`, `p3_b4_analysis_ledgers.py:263-276`）。現行契約上、future producer の exact ratio は正当な入力になりうる。「正当でない」とするには今回の新しい registry admission 裁定が必要であり、既存コードからは導けない。

- P1c: **数学的には是、ただし D1344 の正しい再測定がゼロであることを条件とする**。
  既約分母の素因数が 2 と 5 だけ、という述語は有限十進有理数と正確に一致する。既存の正値・exact-ratio 検査と組み合わせれば、`_fraction_token` の数値上の受理集合（`p3_b4_raw_record_producer.py:341-372`）と一致する。registry では `Fraction` や整数も受けるが、正規化後の数値集合は同じである。

## 総括

親の 852 件・非有限十進 0 件という実測は、現行 float throughput の参考調査としては妥当だが、D1344 が指定した scheduled `reference_tps` の全件列挙ではない。sealed B-4 scheduled input が実在しない現状では、D1344 の「ゼロなら狭める」という条件はまだ成立していない。

正しい scheduled registry の列挙でもゼロになった場合は、`p3_b4_analysis_ledgers.py` に一つの有限十進述語を置き、`_validate_attempt`、`_ratio_payload`、`_ratio_from_payload`、`_manifest_row_payload` の四境界すべてで明示拒否する。純関数 contract、invalid 理由 enum、判定順序、§5.1.1 文書は変更しない。