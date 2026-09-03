## 総括

比較対象は「producer が申告した hash」ではなく、事前固定した正規 producer の `(path, SHA-256)` とする。現行 bytes の SHA-256 は静的実測で `55e264f05eef48e466a1ab20c97d9a7d30acba0afe3e76937e58411e17b1c790` だった。実験開始時にこの値と一致しなければ結果を作らず停止し、結果を見て期待値を更新しない。

12 負例を issuer、raw assembly、frozen consumer の同じ 3 層へ当てる。事前期待は issuer `3/12`、raw assembly `9/12`、frozen consumer `6/12` KILLED。ただし raw assembly にも post-assembly 改変を拒否できない共通穴が残るため、採否規則は次のように先に固定する。

- 全負例を KILLED する候補が 1 つなら採用候補とする。
- 複数なら後述の変更閉包が最小の候補を選ぶ。
- どれも全件を殺せなければ「3 候補に完全な認証層なし」と結論し、本採用しない。
- 通常 verdict が `protocol_violation` などへ変わっただけでは KILLED と数えない。producer provenance を拒否せず、改変判断値が分析へ到達したなら SURVIVED とする。

この回答は静的調査と plan のみであり、pytest や変異実走は行っていない。

## 候補 3 層の最小認証 prototype

- **issuer 候補**

  - [p3_b4_prerun_issuer.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_prerun_issuer.py:67) の `B4PrerunRejectionReason` に実験用 `PRODUCER_AUTH_MISMATCH` を追加する。
  - [p3_b4_prerun_issuer.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_prerun_issuer.py:110) の `B4PrerunPublication` に `raw_record_producer_path` と `raw_record_producer_sha256` を追加する。
  - [p3_b4_prerun_issuer.py:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_prerun_issuer.py:444) の `_issuer_commitment_payload` に同じ 2 field を封入する。
  - [p3_b4_prerun_issuer.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_prerun_issuer.py:707) の `issue_b4_prerun_publication` 冒頭で、実験側が事前固定した path の bytes を独立に読み、固定 SHA-256 と違えば issuance 前に拒否する。
  - [p3_b4_prerun_issuer.py:1007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_prerun_issuer.py:1007) の loader は封印済み 2 field と固定値を検証するが、現在の source を再読しない。再読すると認証時点が issuer から下流へ移り、比較対象が変わるためである。
  - この prototype が認証するのは issuance 時点の source だけである。issuer の後に別 producer が planned path へ書いた事実は観測できない。

- **raw assembly 候補**

  - 実効関門は [p3_b4_raw_record_producer.py:1894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1894) `assemble_b4_raw_analysis` の入口とする。そこで実験用の独立 verifier が正規 producer file を読み、固定 SHA-256 と照合してから assembly を続ける。
  - producer の出力や attempt artifact から `producer_sha256` を受け取らない。追加するなら [p3_b4_raw_record_producer.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:155) の `B4RawAnalysisAssembly` に診断用 `observed_producer_sha256` を載せるだけとし、受理根拠には使わない。
  - 別 path producer が attempt artifact を書いた場合は、[p3_b4_raw_record_producer.py:1928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1928) の実際の `_derive_b4_attempt_data` と [p3_b4_raw_record_producer.py:1942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1942) の byte 一致を通す。ここを stub に置き換えない。
  - 固定期待値を producer file 自身へ置く案は循環なので採らない。issuer 封印値を期待値にする案は issuer 候補として集計する。

- **frozen consumer 候補**

  - 一時変異で [p3_b4_analysis_path.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_path.py:67) `_SOURCE_CLOSURE_PATHS` と [p3_b4_analysis_prereg_consumer.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98) `_CLOSURE_PATHS` の双方へ `orchestrator/campaign/p3_b4_raw_record_producer.py` を追加する。
  - [p3_b4_analysis_path.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_path.py:503) が作る既存 `B4AnalysisSourceClosureReceipt.members[]` の `path` と `sha256` を使う。新しい自己申告 field は作らない。
  - [p3_b4_analysis_prereg_consumer.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1027) の実 consumer route で receipt を生成し、producer member が存在して固定 SHA-256 と一致することを要求する。
  - [p3_b4_analysis_path.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_path.py:199) `evaluate_b4_artifacts` の実験用一時引数としてその receipt を渡し、不一致は `binding_domain_error` で分析前に fail-closed とする。
  - 現行の [p3_b4_analysis_path.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_path.py:174) `_source_artifacts_match` は source bytes の digest と順序だけを見る。source object 内の判断値と raw record の判断値は照合しないため、この候補単独では別 path producer を認証できない。

3 prototype の一時差分は測定 harness が適用・復元し、成果 commit には残さない。

## 変異集合と層別の期待 KILLED / SURVIVED

判断値は、実アンカーが独立している次の 3 種を使う。

- `P`: `protocol_ok: true -> false`。[producer:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1340) と出力 [producer:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1371)。
- `T`: on arm の `treatment_fired: true -> false`。[producer:1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1234) と出力 [producer:1369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1369)。
- `C`: on arm の `contaminated: false -> true`。[producer:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1235) と出力 [producer:1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1370)。

| ID | 別 producer の投入位置 | issuer | raw assembly | frozen consumer |
|---|---|---:|---:|---:|
| C0-P | issuance 前に正規 path の source を P 意味論へ置換 | KILLED | KILLED | KILLED |
| C0-T | 同、T 意味論 | KILLED | KILLED | KILLED |
| C0-C | 同、C 意味論 | KILLED | KILLED | KILLED |
| C1-P | issuance 後、assembly 前に正規 path を P 意味論へ置換 | SURVIVED | KILLED | KILLED |
| C1-T | 同、T 意味論 | SURVIVED | KILLED | KILLED |
| C1-C | 同、C 意味論 | SURVIVED | KILLED | KILLED |
| R-P | 正規 source は不変。別 path producer が P 改変済み attempt artifact を planned path へ書く | SURVIVED | KILLED | SURVIVED |
| R-T | 同、T 改変 | SURVIVED | KILLED | SURVIVED |
| R-C | 同、C 改変 | SURVIVED | KILLED | SURVIVED |
| D-P | assembly 後、別 raw producer が raw analysis の P だけを書き換える | SURVIVED | SURVIVED | SURVIVED |
| D-T | 同、T 改変 | SURVIVED | SURVIVED | SURVIVED |
| D-C | 同、C 改変 | SURVIVED | SURVIVED | SURVIVED |

C0 の 3 件は全層 KILLED、D の 3 件は全層 SURVIVED なので、層比較には寄与しない。C0 は source-hash 比較が動く対照、D は 3 候補共通の残存穴を示す対照としてのみ分母へ残す。実際の識別力は C1 と R の 6 件で比較する。

T-2049 の M01〜M18 は既存正しさゲートの非後退 suite として別に維持するが、比較分子へ混ぜない。特に M13 は負例ではなく正例である。比較実験の正例 `POS-1` は正規 source、正規 publisher、正規 assembly、正規 consumer の 201 block publication とし、3 層すべてで受理を期待する。

## 測定 harness

新規 harness は各 `(mutation, candidate)` を別 process、直列で実行する。

1. producer の開始 SHA-256、各 source 置換 anchor の出現数が 1、対象 file に既存差分がないことを確認する。
2. 既存 [test_p3_b4_raw_record_producer.py:921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_raw_record_producer.py:921) の 201-block fixture と [同:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_raw_record_producer.py:1545) の production publisher/assembler 経路を再利用する。
3. issuer 判定は一時 prototype を入れた実 `issue_b4_prerun_publication` を通す。
4. raw 判定は実 `assemble_b4_raw_analysis` を通す。R 変異は、改変 attempt artifact と evidence からの再導出が [producer:1942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1942) で衝突した場合だけ KILLED とする。
5. frozen 判定は実 `generate_verified_analysis_source_closure_receipt` と実 `evaluate_b4_artifacts` を通す。R/D は frozen layer の公開 artifact 境界へ self-consistent な raw/source bytes を渡す。product の material-report 経路や既存 raw gateは変更しない。
6. 各結果に `candidate`、`mutation_id`、`expected`、`observed`、`rejecting_function`、`reason` を保存し、期待と観測の不一致を MISMATCH とする。
7. `finally` で対象 bytes を復元し、開始 SHA-256 と対象限定 `git diff --exit-code` の双方を確認する。復元確認前に次の case や通常 test を走らせない。

frozen で通常の verdict が返った場合は、verdict 内容にかかわらず SURVIVED とする。[adapter:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_adapter.py:209) は bool 判断値をそのまま取り込み、[adapter:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_adapter.py:270) から contract へ渡すためである。

## frozen consumer 候補の測り方 (P1 への回答)

**一時変異で実体を通す案を採る。** 別 path の模擬 module 案は採らない。

理由は、frozen 候補の本体が二重化された membership pin、consumer-owned receipt route、実 evaluator の組み合わせだからである。別 module で「producer hash が一致した」と返しても、[p3_b4_analysis_prereg_consumer.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:752) の tuple 照合や [p3_b4_analysis_path.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_path.py:504) の実 member 読み取りを証明できない。

一時差分は次だけに限定する。

- 2 個の closure tuple への producer path 追加。
- `evaluate_b4_artifacts` へ receipt を渡す最小 prototype。
- 実験終了後の完全復元。

receipt がその場で生成した hash を自分で正しいと判定する形は禁止する。事前固定した SHA-256 と外側から比較しなければ、模擬 pin が自分自身を裁定するだけになり、別 producer の拒否能力を示さない。

## 変更閉包の数え方

結果を見る前に `change-closure.json` へ候補別の path と pin site を固定する。

- **file 数**: 本採用時に bytes が変わる tracked production file の distinct 数。実験 harness、test、report、decision は別欄とし、候補の production file 数へ含めない。
- **test 波及数**: production module 名の `orchestrator/tests/` 検索で得た distinct test file 数。
- **pin 数**: `(producer repository-relative path, expected SHA-256)` を fail-closed に照合する literal site と、同じ producer path を要求する mirrored closure tuple site の物理個数。schema version bump や report の表示 field は pin に数えず、wire変更数として別記する。
- 同じ logical pin が `_SOURCE_CLOSURE_PATHS` と `_CLOSURE_PATHS` に現れれば 2 pin site と数える。

事前見積りは次のとおり。

| 候補 | production file | producer pin site | 主な理由 |
|---|---:|---:|---|
| issuer | 1 | 1 | issuer dataclass、commitment、issue/load |
| raw assembly | 1 | 1 | assembly 入口の独立期待値照合 |
| frozen consumer | 3 | 3 | 2 closure tuple、期待 digest、material-report から receipt 接続 |

frozen の 3 production file は `p3_b4_analysis_path.py`、`p3_b4_analysis_prereg_consumer.py`、[p3_b4_material_report.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_material_report.py:183) である。実験では後者を恒久変更せず、直接 evaluator probe で測る。

## 新規 file と行数見積り

- `orchestrator/campaign/p3_b4_producer_auth_experiment.py`: 約190行。固定 trust anchor、候補結果型、3 層の最小 guard、canonical report serializer。
- `orchestrator/tests/p3_b4_rogue_producer_support.py`: 約90行。別 path から P/T/C を生成し、attempt artifact と raw/source bytes の双方を作る実 rogue producer。
- `orchestrator/tests/test_p3_b4_producer_auth_experiment.py`: 約320行。12 負例、POS-1、期待 matrix、実 API 通過、復元検査。
- `output/insights/2026-09-03_t2103-producer-auth-layer/mutation-prereg.md`: 約120行。
- 同 `comparison.json`: 約100行。
- 同 `README.md`: 約100行。
- 同 `verbatim/` 配下の D1345、一次資料 §4、T-2049 表: 入力逐語どおり計約63行。
- `docs/spool/decisions/2026-09-03_t2103-producer-auth-layer.md`: 約30行。

既存 file の恒久変更は **なし**。3 production prototype の変更は測定中だけ適用し、5-file pin の恒久拡張を commit に含めない。

## 既存テストへの波及

production module 名を `orchestrator/tests/` で静的検索した結果は次のとおり。

- `p3_b4_raw_record_producer`
  - `test_p3_b4_raw_record_producer.py`
  - `test_p3_b4_material_report.py`
- `p3_b4_analysis_path`
  - `test_p3_b4_raw_record_producer.py`
  - `test_p3_b4_analysis_path.py`
  - `test_p3_b4_analysis_prereg_consumer.py`
- `p3_b4_analysis_prereg_consumer`
  - `test_p3_b4_analysis_path.py`
  - `test_p3_b4_analysis_prereg_consumer.py`
- `p3_b4_prerun_issuer`
  - `test_p3_b4_raw_record_producer.py`
  - `test_p3_b4_prerun_issuer.py`
- `p3_b4_material_report`
  - `test_p3_b4_material_report.py`
  - `test_real_repo_serialization.py`

特に frozen の一時 tuple 変更中は [test_p3_b4_analysis_path.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_analysis_path.py:52) と [test_p3_b4_analysis_prereg_consumer.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:27) の 5-file literal が意図的に旧値となる。したがって一時変異中は比較 node だけを走らせ、復元後に親が通常 suite を実測する。

## 親 brief への指摘

- 「5-file pin」は現状では固定期待 digest との照合ではない。[p3_b4_analysis_path.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_path.py:481) は現在の bytes を読み hash 化し、consumer は [p3_b4_analysis_prereg_consumer.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1070) で path tuple を照合するだけである。外部固定値と比較しない receipt 単独では source 改変を拒否できない。
- closure receipt は現行 material-report/evaluator 経路へ接続されていない。[p3_b4_material_report.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_material_report.py:224) は receipt なしで `evaluate_b4_artifacts` を呼ぶ。producer path を tuple に追加するだけでは frozen consumer の拒否を実測したことにならない。
- P2 の「raw assembly の拒否能力ゼロ」は広すぎる。同一 source mutationを producer と rederivation の双方が実行すればゼロだが、別 path producer が planned attempt artifact を変えた場合は現行 [producer:1928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1928) から [producer:1948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/campaign/p3_b4_raw_record_producer.py:1948) の再導出が実際に拒否できる。この非ゼロ能力を R 変異で測るべきである。
- 「M01〜M18 は 18/18 KILLED 実測済み」は、射影された一次資料だけでは確認できない。提供表の M13 は明示的な正例であり、[test_p3_b4_raw_record_producer.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer/orchestrator/tests/test_p3_b4_raw_record_producer.py:284) は ID と test node の対応を持つが、mutant の exact 置換や 18/18 の実走結果は持たない。比較 report では既実測と断定せず、親が一次測定記録を提示した場合だけ参照する。
- raw assembly 後の判断値改変について、consumer は source artifact の digest を検査するが、source object の `raw` と raw-analysis arm の値を相互照合しない。このため D-P/D-T/D-C は静的には全層 SURVIVED 予想となる。ここを普通の `protocol_violation` verdict で KILLED と誤集計してはいけない。