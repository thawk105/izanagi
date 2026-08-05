以下は read-only の静的レビューであり、テスト・実機 probe は実行していない。

## 最重要 — 保存済み profile／receipt の consumer がプランから落ちている

**場所**: [orchestrator/campaign/silo_ladder_rung1.py:3403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/silo_ladder_rung1.py:3403)、[orchestrator/campaign/s8b_ratified_freeze.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_ratified_freeze.py:1795)、[orchestrator/campaign/s8b_oracle_report.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_oracle_report.py:1189)

**なぜ危険か**: プランが列挙した live consumer は概ね正しいが、次の再読経路がない。

- `silo_ladder_rung1.py:3407-3465` は保存済み `attestation-job.json` を再 parse し、method を calibration と再度 exact 比較する。
- `s8b_ratified_freeze.py:1803-1808,1869-1878` は journal の保存済み execution receipt を、現在の registry/calibration で再検算する。
- `s8b_oracle_report.py:1202-1208,1371-1380` も材料レポート生成時に同じ再検算を行う。
- `orchestrator/tests/test_env_attestation.py:400-455` は旧 v1 probe corpus を再生する。

live 経路の全体は、calibrator (`cli.py:344-351,528-555,603-616`)、execution guard (`execution_guard.py:315-363`) とその floor/oracle/loop caller、T126 (`t126_driver.py:439-455`)、`run_probe.py:30-72` と certify/smoke/silo shell、silo live (`silo_ladder_rung1.py:1932-2010`) である。他の `s8b_*` に live `probe()` 呼出しはないが、上記2本が receipt consumer である。observed schema を変えると保存済み profile が parse 前に落ち、将来 g2 を current tail にすると保存済み g1 receipt が current lookup で落ちる。

**成果物影響**: 放置すると、既存の silo 証拠・ratified freeze・材料レポートが、測定値不変でも schema/current-generation の都合だけで再検算不能になり、certified 選択の歴史参照が失われる。

**scope 内/外**: consumer/no-touch 分類の追記は本 wave 内の plan must-fix。保存済み bytes は変更しない。g2 後の履歴 resolver 結線は T-506/T-529 側へ返す。

## 「述語不変」でも物理的な受理集合は変わる

**場所**: [output/insights/2026-08-04_t419-probe-causality/ruling-package.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/output/insights/2026-08-04_t419-probe-causality/ruling-package.md:24)、[orchestrator/campaign/execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:183)

**なぜ危険か**: comparator は引き続き `∀i. M[i]∈B` だが、`M[i]=min_k S_k[i]` になるため、単読み `S₁` に対する受理集合とは同じでない。

- `S₁[i]` が高い帯外でも後続1回が帯内なら新方式は受理する。真の高クロック逸脱でも K−1 回まで消せる。
- `S₁[i]` が帯内でも後続1回が低い帯外なら `min` が残して新方式は拒否する。
- 裁定パッケージ自身が α の should-reject を未測定としており、保証できるのは「同じ CPU が全 K 回帯外なら拒否」までである。

R-1 が α の式を承認しているため、この拡大自体は無断ではない。しかし brief の「受理述語不変」を「受理集合不変」の証拠に使ってはならない。プランの正例は reader 高値だけで、非-reader の一過性高値と、後発の低値による新規拒否を固定していない。

**成果物影響**: g2 活性化後は、旧単読みなら拒否された物理軌跡が試行台帳へ accepted として入り、逆方向では旧方式なら通った軌跡が欠測になる。

**scope 内/外**: 本 wave 内で brief/plan の表現を是正し、上記2方向の characterization test を追加すべき。should-reject の実機再測定は裁定済み scope 外。

## pin 閉包は path/SHA だけではない

**場所**: [orchestrator/campaign/env_contract.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_contract.py:256)、[orchestrator/tests/test_env_contract.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_contract.py:62)、[orchestrator/tests/test_silo_ladder_rung1_evidence.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_silo_ladder_rung1_evidence.py:67)、[orchestrator/tests/test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_frozen_artifacts.py:38)

**なぜ危険か**: 現登録 bytes と成功 attempt の `calibration.json` は同一で、SHA は `753f535a…e5a49`。その閉包は次の役割で固定される。

- production trust root: `env_contract.py:256-275` の Pegasus g1 `{path, sha256}`。
- 直接 golden: `test_env_contract.py:267-279,1125-1138`。
- 役割 key pin: `EXPECTED_GENERATION_HASHES["pegasus"]` (`test_env_contract.py:69-76,341-349`) の g1 contract SHA `e576e9cd…2c01`。
- 既知例外役割: `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` (`:62-67,840-870`)。
- official-core golden: `test_s8b_floor_campaign.py:3247-3252`。
- 歴史的証拠 identity: path を持たない positional pin `HISTORICAL_SILO_EVIDENCE_IDENTITY` (`test_silo_ladder_rung1_evidence.py:67-72,1190-1210`)。
- 凍結 trust root: `output/s8b-freeze/floor_protocol.json:1` が g1 contract SHA を内包し、その bytes を `FROZEN_MANIFEST` が固定する。
- 発行履歴: `attempts/0_867876.nqsv/final-receipt.json:7-27` が calibration/publish/window-probes の各 SHA を固定する。

したがって path hit だけでは閉包にならない。

**成果物影響**: 部分的な repin は floor protocol、公式 E2E、silo 歴史証拠のいずれかを旧 g1 に残し、certified 選択・材料レポート・台帳で異なる contract 世代を参照させる。

**scope 内/外**: 本 wave 内では全対象を no-touch 検査対象として plan v2 に列挙する。実際の更新はすべて下流 wave。

## method 不一致は確定だが、唯一の拒否理由とは限らない

**場所**: [output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440)、[orchestrator/campaign/env_attestation.py:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:658)、[orchestrator/campaign/execution_guard.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:347)

**なぜ危険か**: g1 の expected は `method="proc-cpuinfo"`、live observed は新 method なので、`_recorded_verdict()` の exact equality により必ず fail する。samples が通り、これだけが失敗なら message は次になる。

```text
attestation comparisons failed: [{"expected":"proc-cpuinfo","field":"effective_clock.method","observed":"proc-cpuinfo-rotating-min/k5/sysfs-affinity-intersection-evenly-spaced-v1","verdict":"fail"}]
```

ただし `compare_profiles()` は全 field を返すので、live samples/TS​C等も外れれば failure 配列は複数になる。「拒否理由が method 不一致へ変わる」は「method 不一致が必ず含まれる」までしか静的には言えない。

経路別には、floor は同じ本文の `FloorCampaignError`、oracle 起動は `execution attestation 失敗: ...`、行ごとは `途中 execution guard 失敗: ...`、loop は `ExecutionGuardError`。silo は共有 comparator を使わず `effective_clock_match=False` から `attestation: environment attestation mismatch: ...`。一方 `run_probe.py` と calibrator は g1 と比較せず、新 method を保存・発行候補化できる。

**成果物影響**: g1 に対する新 execution receipt は発行されず、新 trial 行も生じないが、standalone probe JSON と新較正候補には新 method が記録される。

**scope 内/外**: 本 wave 内で g1＋新 method の統合拒否と wrapper message を固定すべき。凍結 g1 の修正は scope 外。

## P2 が正しい — observed-only の生 K ベクトル追加も採れない

**場所**: [orchestrator/calibrator/schema_v2.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:243)、[orchestrator/calibrator/schema_v2.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:552)、[orchestrator/campaign/env_attestation.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:519)、[orchestrator/calibrator/cli.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/cli.py:528)

**なぜ危険か**: observed 側だけに raw K key を加えても隔離できない。

- observed は `env_attestation.py:529-535` で exact 3 keys、probe-output v1/v2 は `:553-594` で同じ parser に入る。必須 key 追加は旧 corpus を読めなくする。
- calibrator は observed dict を `profile` とし、tolerance を足して expected calibration に転用する (`cli.py:528-555`)。raw keyが残れば `_CLOCK_KEYS` exact 検査 (`schema_v2.py:552,598`) で拒否される。
- raw keyを calibrator で捨てれば「較正へ K 回保持」は達成しない。
- observed projection/hash (`env_attestation.py:629-648`) は変わる一方、比較 field (`:651-706`) は明示列挙なので raw K は admission に使われない。
- expected schemaにも足せば g1 は method 比較以前に schema 不正となり、profile hash、artifact digest、登録 filename、contract pinまで動く。

raw MHz だけでは pin target と pre/post processor も証明できず、証拠としても不完全である。

**成果物影響**: 無理に追加すると旧 probe corpus・較正 loader・profile hash・登録 artifact・contract参照を同時に変え、現 certified/material/trial の再読集合を壊す。

**scope 内/外**: P2どおり schema key不変・methodのみが本 waveの正解。K証拠が必要なら probe-output v3等の別 versioned-schema waveへ返す。

## T126 は α consumer として機能していない

**場所**: [orchestrator/qualification/t126_driver.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/qualification/t126_driver.py:439)、[orchestrator/campaign/env_attestation.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:610)

**なぜ危険か**: `compare_profiles()` の expected に `verified.calibration` (`CalibrationV2`) を渡すため、α method の比較へ到達する前に `expected が AttestationProfile でない` で拒否される。これを `.attestation_profile` へ直しても、次の `profile_sha256(observed)` は observed 型を受理せず、別の `profile が AttestationProfile でない` に落ちる。プランは前者だけを記載している。

**成果物影響**: T126 の pre-round/post-series attestation は accepted recordを作れず、qualification 試行台帳に α の観測 profile/hash は一件も載らない。

**scope 内/外**: 既知 fail-closed を直すのは本 wave 外。ただし plan は T126 を「αが届く consumer」と数えず、2段目の型不整合も裁定パッケージへ返すべき。

## α は世代機構と矛盾しないが、g2 の履歴 consumer 結線は未実装

**場所**: [orchestrator/campaign/env_contract.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_contract.py:202)、[orchestrator/campaign/env_contract.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_contract.py:316)、[orchestrator/campaign/s8b_ratified_freeze.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_ratified_freeze.py:1803)

**なぜ危険か**: 現 wave は contract fieldを変えないので g1 SHA、bootstrap fuse、既知例外1件と矛盾しない。将来の g2 は calibration `{path,sha256}` の対だけを変えるため `is_valid_successor()` に適合し、method固有の余計な successor 制約もない。一方、`validate_generations()` は2世代目を明示拒否し、productionで `resolve_by_contract_sha256()` を使う consumerはまだない。ratified freeze、oracle report、floor protocolはいずれも current `lookup()` を使う。

**成果物影響**: 下流が g2をtailへ載せるだけでは、保存済みg1 floor/journal/reportが新current contractとの不一致で拒否され、歴史 certified 選択の参照が切れる。

**scope 内/外**: α実装は本 wave内でそのまま進めてよい。fuse解除、履歴resolver結線、`KNOWN_SELF_INCONSISTENT_CALIBRATIONS`縮小はT-506/T-529側。

## 総括

最も危険なのは、プランが live caller だけで閉じ、保存済み profile/receipt を再検算する silo・ratified freeze・oracle report を inventory から落としている点である。schema不変なら本 waveでは保全できるが、明示しないまま schema/g2へ進むと歴史成果物を失う。

(P2) は、**schema key集合を変えず、方式 identityを `effective_clock.method` のみに載せる**案を採るべきである。生K証拠は本waveには入れず、必要ならversioned schemaの別waveとする。

判定は **NO-GO（現プランのまま段5へ進むことに対して）**。α自体の却下ではない。plan v2で、保存済みconsumer/no-touch閉包、物理受理集合が変わること、g1 method不一致の統合拒否、T126とg2履歴結線のscope外明記を反映すれば再開可能である。