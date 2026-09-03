## 配置の択一

**推奨は択 A、`_validate_attempt` 限定。** provisional 裁定は維持する。ただし、「択 A なら manifest codec へ迂回できない」という説明は誤りで、単独 manifest loader には実在する迂回経路がある。

- 実在する経路は `load_analysis_manifest()` → `_manifest_row_from_payload()` → `_ratio_from_payload()` → `_manifest_row_payload()` である。canonical な `[1,3]` は現状 `_ratio_from_payload` の reduced 検査を通り、manifest として再 canonical 化される。read-only の直接検査でも、第一行を `[1,3]` に変えた canonical manifest を loader が受理した。[p3_b4_analysis_ledgers.py:288](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:288) 同 `:960-989,1100-1129`
- private call の全数は、`_ratio_payload` が `:379,952`、`_ratio_from_payload` が `:428,979`、`_manifest_row_payload` が `:986,1004`、`_validate_attempt` が `:363,436,446` のみだった。
- ただし、この迂回 manifest は**完全な artifact 組としては受理されない**。生成経路は `generate_analysis_manifest()` 冒頭で registry を再検証し (`:1042-1053`)、issuer も manifest 生成前に scheduled hash と seal を行う。[p3_b4_prerun_issuer.py:725](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:725) 同 `:777-798`
- 読取経路も registry を manifest より先に読む。[p3_b4_analysis_path.py:199](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:199) 同 `:217-240`。直接検査では standalone manifest は読めたが、元の registry との `assert_analysis_manifest_complete` は row mismatch で拒否した。
- 択 B は `_ratio_from_payload` の manifest 側呼出し `:979` と `_manifest_row_payload` `:931-957` を狭めるため、standalone manifest reader/writer の wire 受理集合を変更する。loader rejection は `_load_manifest` により `field_missing_or_ill_typed` へ写される。[p3_b4_analysis_path.py:141](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:141)
- §5.1.1 は `reference_tps` を「有限の正」としている。`1/3` は有限で正の exact rational なので、有限十進展開の有無は現在の `reference_value_domain_error` ではない。[preregistration.md:406](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/docs/phase3-b4-reflux-ablation-preregistration.md:406) 同 `:461-476`; [p3_b4_analysis_contract.py:371](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_contract.py:371)

したがって、択 B は事前登録読取器が受け取る値域の意味に触れる。一方、択 A の codec 迂回は完全な registry/manifest 組を成立させない。今回の目的を registry admission の別層に限定し、§5.1.1 と manifest codec を動かさない択 A が適切である。

## M12 の再定義

親の確認は**実質的に正しい**。ただし新検査後の停止点は seal より前になる。

- 現行 M12 は `_publication(..., reference_override=(1,3))` を作り、`publish_b4_attempt_result` の `DECIMAL_NOT_TERMINATING` を期待する。[test_p3_b4_raw_record_producer.py:1138](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:1138)
- `_publication` は `issue_b4_prerun_publication` を呼ぶ。同関数は最初に `scheduled_attempts_sha256` (`issuer.py:725`) を呼び、`_normalize_attempts` (`ledgers.py:476`) → `_validate_attempt` (`:446`) に到達する。
- 有効な batch なら後続の seal (`issuer.py:777`) でも `_validate_attempt` を通るが、`(1,3)` は新検査後には最初の `scheduled_attempts_sha256` で拒否される。したがって `publish_b4_attempt_result` (`producer.py:1725`) には到達しない。

M12 は現在の node 名を維持し、`test_p3_b4_raw_record_producer.py:1138-1149` の本体だけを次の二段検査へ変える。

1. 実物の `P._fraction_token((1,3))` が、正確に `ArithmeticError("reference_tps has no finite decimal expansion")` を送出することを `pytest.raises` で直接検査する。[p3_b4_raw_record_producer.py:341](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:341) 同 `:353-359`
2. 有限十進だけを含む通常の publication と有効な evidence control を作る。その後、既存 import の `mock.patch.object` で `_fraction_token` に `ArithmeticError` を送出させて `_publish` を呼び、production catch `:1543-1549` が次の issue を生成することを検査する。
   - artifact: `"publication"`
   - field: `"reference_tps"`
   - code: `DECIMAL_NOT_TERMINATING`
   - detail: `"reference_tps has no finite decimal JSON representation"`

これにより、分母判定を受理へ変える変異は直接検査が、`ArithmeticError` から拒否 code への写像を削除・変更する変異は publish 経路が殺す。registry rejection への移設にはならない。

`MUTATION_NODE_IDS["M12"]` は既存の `"test_m12_nonterminating_reference_ratio_has_only_named_rejection"` を維持する。[test_p3_b4_raw_record_producer.py:284](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:284) 同 `:296`。関数名を変えないため、全 callable・18 名一意性検査 `:807-810` と duration ledger の nodeid も変更不要である。

M13 の `(10_000,1)` は既約分母が `1` なので新検査を通り、`_fraction_token` も整数 `10000` を返す。read-only の直接検査でも確認した。[test_p3_b4_raw_record_producer.py:1152](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:1152)

## 既存正例の全数

`git grep` と全 `B4ScheduledAttemptInput(...)` 構築点の追跡結果は次のとおり。

| 構築面 | registry を通る値 | 判定 |
|---|---|---|
| production self-check | `1000 + index`。`index=0..201` と `0`。[p3_b4_analysis_prereg_consumer.py:757](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:757) 同 `:776,819-842` | 分母 1 |
| ledger tests | `(10_000+i,1)`。使用 index の和集合は `0..204,300..304,800,900`。[test_p3_b4_analysis_ledgers.py:23](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_ledgers.py:23) 同 `:48,127-165,326-345,374-440,578-631,709-720` | 分母 1 |
| analysis-path tests | `100`。[test_p3_b4_analysis_path.py:77](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_path.py:77) 同 `:107,207-228` | 分母 1 |
| issuer tests | `(10_000+i,1)`。`i=0..200,700,701`。[test_p3_b4_prerun_issuer.py:30](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_prerun_issuer.py:30) 同 `:51,59-62,171-195` | 分母 1 |
| raw-producer tests | `(100_001+10i,10)`, `i=0..200`。[test_p3_b4_raw_record_producer.py:109](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:109) 同 `:119-126` | 既約分母 10 |
| raw overrides | `(1,3)` と `(10_000,1)` だけ。同 `:1145,1156` | 前者だけ非有限十進 |

補足:

- production の `_attempt_from_payload` は literal 値ではなく任意の canonical ratio を読む runtime surface であり、これが今回狭める対象である。[p3_b4_analysis_ledgers.py:387](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:387)
- `reference_tps=None` は `test_p3_b4_analysis_ledgers.py:476-497` で `_attempt_is_eligible` を直接検査するだけで、registry admission を通らない。
- contract/adapter tests と prereg consumer `:881,927` の `Fraction(1)` は純関数側であり、registry census には含まれない。
- tracked test fixture JSON/JSONL に registry 用 `reference_tps` literal は無かった。

非有限十進は M12 の `(1,3)` **1 件だけ**で、これは正例ではなく丸め禁止を検査する意図的な負例である。既存正例で落ちるものはない。

## pin 閉包

`p3_b4_analysis_ledgers.py` の編集により、member digest と closure receipt 全体の digest は動く。

- closure member は [p3_b4_analysis_path.py:67](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:67) と [p3_b4_analysis_prereg_consumer.py:98](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98) に列挙される。
- member SHA は live bytes から `analysis_path.py:504-516` で計算され、receipt 全体は `:523-536` で再計算される。
- 現行 member digest `7476c812...c152` と現行 closure receipt digest `57e84eeb...384c` は、どちらも repository 全域の `git grep` で literal hit 0 件だった。
- path 検索は 61 行、24 file に hit したが、live なものは上記 production tuple と [test_p3_b4_analysis_path.py:52](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_path.py:52)、[test_p3_b4_analysis_prereg_consumer.py:22](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:22) の path/order pin だけである。残りは archived worklog と historical mutation report/spec/verbatim で、closure digest pin ではない。
- path 以外も、schema `"p3-b4-analysis-source-closure/v1"`、receipt type、B-4 role JSON、generic key→canonical path mapping、`members`/`preregistration_section_sha256` key を検索した。serialized ledger、golden、凍結 artifact、role binding に literal closure digest は無かった。

したがって本 wave で既存 pin の repin は行わない。path tupleも変えず、実装後に既存の live receipt generation testsが新 member digestを再計算することを確認するだけでよい。

§5.1.1 の raw/semantic digest は動かない。両 digest は document section bytesだけを pinする。[p3_b4_analysis_prereg_consumer.py:47](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47) 同 `:394-407`。closure assemblerも sectionを文書から独立に hash する (`analysis_path.py:518-525`)。本計画は文書 bytes を変更しない。

## テスト設計

`test_p3_b4_analysis_ledgers.py` の permutation/seal 検査直後、現在の `:155-158` 付近へ次を追加する。

- 正例 `(1,10)`: `_attempt(0)` を `replace` し、`_seal` が成功して registry 内にも `(1,10)` が残ることを確認する。これにより述語の反転や分母 10 の過剰拒否を殺す。
- 負例 `(1,3)` と `(1,30)`: parameterize し、まず `ledgers._ratio_from_payload([n,d]) == (n,d)` を確認する。特に `[1,30]` が既存の `"wire reference_tps is not reduced"` を通過することを固定する。その後 `scheduled_attempts_sha256((candidate,))` が新検査だけで失敗することを確認する。
- registry 拒否署名は `_fail` に従い、`B4LedgerError` と exact message `reference_tps has no finite decimal expansion` にする。[p3_b4_analysis_ledgers.py:247](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:247)
- `_validate_attempt` では既存の exact-rational/正値検査 `:341-343` の直後に、`reference.denominator` から 2 と 5 をそれぞれ割り切り、残りが 1 でなければ上記 `_fail` を呼ぶ。既存の型・非正値 rejection が先に発火する順序は維持する。
- M12 は前節の二段検査へ変更し、raw producer の拒否署名も artifact、field、code、detail の全項目で固定する。

## 変更面 file:line

- [orchestrator/campaign/p3_b4_analysis_ledgers.py:341](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:341) — `_validate_attempt` 内へ独立した分母 2/5 除去判定と `_fail` を追加。helper 共有、codec、contract、adapter は変更しない。
- [orchestrator/tests/test_p3_b4_analysis_ledgers.py:155](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_ledgers.py:155) — `(1,10)` 正例、`(1,3)`・`(1,30)` 負例、`[1,30]` codec control を追加。
- [orchestrator/tests/test_p3_b4_raw_record_producer.py:1138](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:1138) — M12 を `_fraction_token` 直接分岐検査と production rejection mapping 検査へ再定義。
- 同 `:296` — M12 node 名は変更しない。`acceptance_duration_ledger.json` も変更不要。
- `p3_b4_analysis_contract.py`、`p3_b4_analysis_adapter.py`、`_attempt_is_eligible`、`generate_analysis_manifest`、manifest codec、§5.1.1 は変更しない。

## 残る不確実性

- 制約に従い pytest は実行しておらず、緑は主張しない。実施したのは検索、call graph追跡、read-only の直接関数検査だけである。
- 編集後の member/closure digest の具体値は最終 bytes が決まるまで確定しない。ただし literal consumerが無いことは全域検索済みである。
- repository 外に独自の standalone manifest callerや未追跡の closure receiptが存在する可能性は、repository の `git grep` では判定できない。択 A はその外部 reader の受理集合も変更しない。

## 総括

- 択 Aを採り、有限十進述語は `_validate_attempt` だけへ置く。
- standalone manifest loaderには `[1,3]` の迂回が実在するが、完全な registry/manifest 組としては成立しない。
- 択 Bは manifest readerの値域と §5.1.1 の「有限の正」の意味に触れるため採らない。
- M12は同じ node 名のまま、実 `_fraction_token` 分岐と producer rejection mappingの二段検査へ変える。
- 既存正例はすべて既約分母が 1 または 10で、落ちる正例はない。closureの literal repinも不要である。