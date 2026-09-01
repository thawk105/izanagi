## 狭める側の受理集合への効果

- **[refuted] 新たに受理される値は生じない。** 段2案どおり、既存の exact-ratio・正値・既約 wire 検査を先に行い、その後で「既約分母から 2 と 5 を除くと 1」を追加する限り、数学的に有限十進有理数だけを残す純粋な部分集合化である。丸め・型変換・fallback はなく、従来 reject された値が accept へ移る経路はない。

  成果物影響: registry / manifest / wire の受理集合は縮むだけで、certified 選択へ新しい値が混入することはない。

- **[real] ただし「registry の受理集合だけを縮める」という説明と4境界案は一致しない。** `_ratio_payload` と `_ratio_from_payload` は registry と manifest の共用 codec、`_manifest_row_payload` は manifest 固有である。4箇所すべてへ入れると、registry admission に加えて standalone manifest の in-memory / wire 受理集合も縮む。

  成果物影響: 以前は `load_analysis_manifest()` が単体で受理した `[1,3]` の manifest も拒否され、拒否地点・理由と生成可能な manifest bytes が変わる。

- **[real] `_validate_attempt` へ無条件に置くと、非適格行も含む全 registry 行が対象になる。** `GENERATION_FAILED`、`DUPLICATE`、`SCREENING_ONLY_RED` 等でも、非 `None` の `reference_tps=(1,3)` があれば batch 全体を封印できない。consumer 到達を防ぐだけなら manifest 候補以外にまで効く。

  成果物影響: §5.1.1 が「全件残す」とした非適格 attempt まで registry から消えるのではなく、registry 自体が発行不能になり、台帳・manifest・後続レポートが一式作られなくなる。

## 狭める箇所の網羅性

`p3_b4_analysis_ledgers.py` には、値が通る経路が実質6系統、後段のコピーが2系統ある。

1. in-memory attempt: `_validate_attempt` → `_normalize_attempts`
2. attempt wire write: `_attempt_payload` → `_ratio_payload`
3. attempt wire read: `_attempt_from_payload` → `_ratio_from_payload` → `_validate_attempt`
4. eligibility: `_attempt_is_eligible`
5. manifest in-memory/write: `_manifest_row_payload` → `_ratio_payload`
6. manifest wire read: `_manifest_row_from_payload` → `_ratio_from_payload` → `_manifest_row_payload`
7. manifest generation時のコピー: `generate_analysis_manifest`
8. contract bindingへのコピー: `build_contract_binding`

call site は `_ratio_payload` が2箇所、`_ratio_from_payload` が2箇所で、別の wire parser はない。

- **[refuted] 4境界案を採った場合、非有限十進が first-201 に入り manifest 生成時まで遅延することはない。** `generate_analysis_manifest()` は先頭で `assert_scheduled_registry_complete()` を呼び、`_build_registry` → `_normalize_attempts` → `_validate_attempt` を通す。したがって forged registry も eligibility 計算前に拒否される。`_attempt_is_eligible` へ同じ判定を足す必要はなく、足すと明示拒否を黙示的除外へ変えかねない。

  成果物影響: `_validate_attempt` が存在する限り、先頭201件の選抜や certified 値は変わらず、非有限十進を含む registry 全体が選抜前に拒否される。

- **[real] 4境界は canonical artifact 経路を閉じるが、dataclass 直接構築を完全には閉じない。** `B4AnalysisManifest` / `B4AnalysisManifestRow` は `__post_init__` を持たず、直接構築した `(1,3)` の manifest を `verify_assignment_schedule()` または `assignment_followed()` へ渡すと reference 値域検査は通らない。ただし `build_contract_binding()`、artifact analysis path、raw producer は completeness または publication reload を要求するので certified 経路には到達しない。

  成果物影響: forged manifest を「schedule は再生成した」と局所的に報告できるが、certified 選択・正式レポート・封印台帳は作れない。これは **nit** に近い限定的 bypass である。

- **[real] 1箇所だけ狭めた場合の具体的な素通しは次のとおり。**

  - `_validate_attempt` だけ: standalone `load_analysis_manifest()` は `[1,3]` を受理する。
  - `_ratio_from_payload` だけ: in-memory の seal / manifest generation は `(1,3)` を受理する。
  - `_manifest_row_payload` だけ: registry は封印され、非有限十進行が eligible first-201 に入り、`_build_manifest()` で初めて落ちる。
  - `_ratio_payload` だけ: canonical serialization は拒否するが、直接構築 manifest の schedule-only public helpers は通る。

  成果物影響: チェック位置次第で「発行前拒否」「first-201 選抜後の manifest 失敗」「standalone loader の受理」が変わり、台帳・manifest の有無とエラー参照先が変わる。

- **[real] M12 の既存テストは恒真になるのではなく、現状のままなら fixture 作成中に失敗する。** `_publication(... reference_override=(1,3))` は issuer の `scheduled_attempts_sha256()` で先に拒否され、producer の `DECIMAL_NOT_TERMINATING` まで到達しない。これを registry rejection 期待へ単純に書き換えて `MUTATION_NODE_IDS["M12"]` に残すと、producer の `_fraction_token` 変異を一切殺さないため、M12 の意味は失われる。

  M12 の防壁は、狭める実装後は registry / issuer admission の変異へ移すべきである。producer の防御を残すなら、既存 M12 を `_fraction_token((1,3))` の直接検査へ再定義しなければ producer 側の防壁にはならない。

  成果物影響: 放置すると mutation report が M12 を KILLED と表示しても、producer の丸め禁止分岐を実際には検査していない恒真保証になる。

## 凍結 closure への帰結

- **[real] ledger は5-file closure の member である。** `p3_b4_analysis_path.py` の `_SOURCE_CLOSURE_PATHS` と `p3_b4_analysis_prereg_consumer.py` の `_CLOSURE_PATHS` の両方に含まれる。bytes を変えれば ledger member SHA と closure receipt 全体の SHA は変わる。この点の親判断は正しい。

- **[refuted] ただし、既存の固定 closure receipt を壊すという意味での「凍結を動かす」証拠はない。** 検索結果は次のとおり。

  - 現行5 member の各 SHA256 の exact match: tracked / docs / tests / output のすべてで **0件**
  - closure schema `p3-b4-analysis-source-closure/v1`: production 定義 **1件**、output artifact **0件**
  - ledger path の tracked 参照: **20 files**
    - closure tuple: 2
    - B-4 tests: 2
    - archive worklog: 1
    - output 内の過去説明・変異資料: 15
  - 現行 ledger hash `7476c812…23c152` の固定値参照: **0件**
  - 固定されているのは §5.1.1 の section hashで、ledger bytes の hash ではない。

  B-4 の2 test file は member SHA を live bytes から動的計算する。receipt の reader / 既発行 receipt との照合経路も射影コードにはなく、生成器だけがある。

  成果物影響: ledger 変更後に新規生成する closure receipt の参照値は変わるが、現存する certified 選択・レポート・台帳を無効化する固定 pin は確認できない。

したがって正確な表現は、「closure identity は変わるが、既存 pin の更新対象は現在ゼロ」である。「凍結物を動かす費用が consumer 改訂と同等」とまでは確認できない。

## 文書との整合

- **[real] §5.1.1 の値域と registry-only finite-decimal admission は同一ではない。** 文書は `reference_tps` を「有限の正」、実装 contract は正の exact rational とし、`Fraction(1,3)` を有効値として扱う。有限十進展開を要求していない。また registry は失敗・重複・screening 等も全件保持すると定める。

  成果物影響: 文書上は有効な共通参照点が registry 発行前に拒否され、母集合・台帳完全性の意味が文書と実装でずれる。

- **[real] 段2の4境界案では「§5.1.1 を変えず registry admission だけを縮める」という切り分けは成立しない。** manifest codec まで狭めるためである。

- **文書節を変えずに済む切り分けは限定的にはある。** finite-decimal を「純関数の reference 値域」ではなく「pre-run registry publication の transport/admission 条件」として D1344 側で明示し、純関数 contract、adapter、manifest codec、`reference_value_domain_error` を維持する形である。この切り分けなら実装点は `_validate_attempt` に収束する。ただし、非適格行も含む全 batch を拒否する方針であることは D1344 の記録で明示する必要がある。

- `reference_value_domain_error` 自体は壊れない。これは分析入力の非正値・型違反を表し、新しい ledger error は実走前 admission の別層である。ただし両者を同じ「reference 値域」と説明すると意味が衝突する。

  成果物影響: 層を明記しないと、同じ `(1,3)` が contract では有効、manifest wire では無効、registry では発行不能となり、レポートの拒否理由がどの契約を指すか不明になる。

## 択一の逆側の再検討

- **[real] 実測0件でも exact-ratio consumer 側が設計上優る筋はある。** §5.1.1 の exact-rational domain、registry の全件保持、M12 の「丸めず名指し拒否」という transport 境界を維持できるためである。

- ただし今回はその方向を提案しない。current raw schema の受理集合を広げる変更になるうえ、D1344 の正しい母集合で本当に0件と確認できた場合に採れば決定文と矛盾する。

- **[real] 現在の0件は D1344 の条件を満たす0件ではない。** `measurement-1.json` が数えた集合は `commit.fitness_tps`、`bench.median_tps`、`bench.tps_series` の3つだけで、scheduled input / sealed registry は含まれない。射影された production codeにも ancestor snapshot から `B4ScheduledAttemptInput.reference_tps` を導出する producer はなく、直接上流は caller-supplied batch である。sealed batch が存在しない状態の空集合を、production 値域の「0件」と扱うことはできない。

  成果物影響: このまま (a) を確定すると、実測していない caller-supplied 値域を根拠なく縮め、将来の正当な scheduled batch を発行不能にする。

したがって exact consumer 側を選ぶべきという結論ではなく、**D1344 の択一はまだ消えていない**という結論になる。

## 親の scope 判断

- **[refuted] 本 wave で狭める実装まで行うべきではない。** brief は成果物を実測と択一確定までと明記しており、実装を次 wave へ渡す読みは妥当である。
- さらに、正しい母集合の実測が成立していないため、現時点で実装へ進む根拠もない。

- **[real] 問題は scope ではなく「択一を確定できる」とした点である。** 本 wave で出せるのは、historical float 系3集合では非有限十進0件だったこと、scheduled input の実在物0件、D1344 の指定母集合は未測定、という結論までである。(a) の確定 decision を記録してはいけない。

  成果物影響: 誤って確定すると次 wave が unsupported な受理集合縮小を実装し、registry・manifest・M12 の意味を連鎖的に変える。

## real / refuted の一覧

- **real:** `measurement-1.json` は D1344 の scheduled-input 母集合を測っていない。
- **real:** 4境界案は registry-only ではなく manifest / wire も縮める。
- **real:** `_validate_attempt` の無条件検査は非適格行を含む batch 全体を拒否する。
- **real:** dataclass 直接構築から schedule-only helpers へ値域検査なしで入れるが、certified 経路には届かない（nit）。
- **real:** M12 を registry rejection へ単純移動すると producer mutation の防壁ではなくなる。
- **real:** ledger 変更で新規 closure receipt の member SHA / 全体 SHA は変わる。
- **real:** §5.1.1 の exact-positive domain と finite-decimal admission は別契約である。
- **real:** exact consumer 側を支持する設計上の筋は残るが、今回は採用提案できない。
- **real:** scope 外として実装しない判断は正しいが、択一確定は未達である。
- **refuted:** 適切に追加した有限十進述語が受理集合を広げる。
- **refuted:** 4境界案なら非有限十進 attempt が first-201 選抜後まで残る。
- **refuted:** 現行 M12 がそのまま恒真になる。実際には issuer fixture 生成時に先に失敗する。
- **refuted:** ledger bytes を固定値 pin した現存 artifact / docs / test がある。
- **refuted:** 本 wave で狭めるコードまで実装すべきである。

## 総括

親の (a) 確定は支持できない。historical throughput 5,928観測で非有限十進0件という事実は有用だが、D1344 が指定した caller-supplied scheduled inputs の実測ではない。

次 wave の4境界案も過剰である。canonical artifact を閉じる一方、registry-only という説明を破り、manifest wire domain、非適格行の保持、M12 mutation 防壁まで変える。文書 §5.1.1 を維持するなら、finite-decimal 制約を pre-run registry admission の別層として明示し、実装位置と影響対象を再設計する必要がある。

静的検査のみ実施し、pytest は実走していない。