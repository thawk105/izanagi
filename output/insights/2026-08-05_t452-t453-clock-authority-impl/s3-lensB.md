静的判定は **NO-GO**。pytest は指示どおり実行していない。

## 所見

### B-1 / 親 brief の artifact 件数と N2 の一般化が誤っている

- **主張:** 論理 JSON は 22 件＝成功 19 件（staging 15、smoke 3、silo 1）＋失敗 3 件である。brief の「smoke 4 件」は誤りで、N2 の canonical-fail も 16 件ではなく成功 19 件すべてに成立する。さらに `.stdout` を含む物理ファイルは 44 件である。
- **file:line:** `brief.md:24-25`、`s2-plan.md:327-352`、`output/env/pegasus/smoke/0:867857.nqsv/observation.json:2-9`、`output/env/pegasus/smoke/0:867860.nqsv/observation.json:3,1372-1425,1500`、`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/attestation-job.json:3,1372-1425,1500`
- **失敗シナリオ:** N2=16 を acceptance の母数にすると、3 件の smoke success は replay だけされ、canonical verdict の移行確認から漏れる。`.stdout` が将来 JSON 側と乖離しても、22 件だけの corpus test では検知しない。
- **成果物影響:** 履歴 replay の完全性と canonical 化の爆風半径を過少報告し、材料レポートが3観測を分類不能にする。
- **強度:** **must-fix**
- **最小の是正案:** brief を「論理22＝成功19（15+3+1）＋失敗3、物理44」に訂正する。corpus test は成功19件すべてについて median=true/canonical=false を固定し、22組の `.json`/`.stdout` が JSON 意味上同一であることも確認する。

### B-2 / T126 の hash preimage 版が evidence に残らない

- **主張:** `observed_profile_sha256` の関数引数を版付きにしても、T126 envelope は同じ `t126-qualification-attestation/v1` のままで、格納されるのは裸の digest だけである。旧4-key preimage と新3-key preimageを replay 時に識別できない。
- **file:line:** `output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:94-104`、`orchestrator/qualification/t126_driver.py:451-455`、`s2-plan.md:50-53,71-73`
- **失敗シナリオ:** 同じ envelope/schema/field 名の hash が、コード世代によって v1 sentinel projection または v2 projectionを意味する。digest 単体からどちらを再構成すべきか決定できない。
- **成果物影響:** T126 qualification evidence の観測 hash を第三者が再計算できず、qualification の証明鎖が版をまたいで曖昧になる。
- **強度:** **must-fix**
- **最小の是正案:** envelope を `t126-qualification-attestation/v2` に上げ、exact field として `observed_profile_projection_schema` を保存する。v1 reader/hash 再現テストを残し、新 digest は fixture への現行値貼り付けでなく独立 preimage から検算する。

### B-3 / probe-output v2 の failure migration が閉じていない

- **主張:** producer には import/success/probe/write の4分岐があるが、プランのテストは success/import failure だけである。また failure の nested `error` exact shape と scalar 型が未規定で、`smoke_probe.sh` も caller 一覧から漏れている。
- **file:line:** `tools/pegasus/run_probe.py:47-99,103-113`、`orchestrator/tests/test_pegasus_tools.py:696-718`、`tools/pegasus/smoke_probe.sh:111-117,120-145`、`s2-plan.md:46-49,64-69,84-85`
- **失敗シナリオ:** success/import だけ v2 化され、probe/write failure は v1 のまま stdout や smoke manifest に封入される。また `ok=1`、bool epoch、余分な error key を「typed failure」として受理し得る。
- **成果物影響:** 新規 job が混在 version の durable artifact を残し、failure replay と運用診断の schema 契約が不定になる。
- **強度:** **must-fix**
- **最小の是正案:** 4分岐すべてについて file/stdout の exact v2 payload を検査する。failure は top-level exact 4 keyに加え、`error == {stage,type,message}`、`type(ok) is bool`、`type(observed_epoch) is int and not bool`、非空文字列を固定する。smoke 経路も acceptance に追加する。

### B-4 / silo が新 parser の例外を既存 failure class に翻訳できない

- **主張:** 新 parser は `env_attestation` に置かれるが、live silo は `DriverError` しか捕捉せず、raw replay の catch tuple にも `AttestationError` がない。既存の retryable parse-failure テストも移行 matrix にない。
- **file:line:** `orchestrator/campaign/env_attestation.py:43-44`、`orchestrator/campaign/silo_ladder_rung1.py:1952-1957,3491-3492`、`orchestrator/tests/test_silo_ladder_rung1_driver.py:731-742`、`s2-plan.md:174-185,222-226`
- **失敗シナリオ:** malformed/duplicate-key JSON が `AttestationError` を送出すると、live run は `InfraFailure(reason_code="parse_failure")` にならず裸の例外で停止する。raw replay も `EvidenceFailure` を返さずクラッシュする。
- **成果物影響:** retry ledger に分類済み infra failure が残らず、`verify-result` が構造化された拒否結果を生成できない。
- **強度:** **must-fix**
- **最小の是正案:** live boundary で parser error を既存 `parse_failure` へ、raw boundary で `EvidenceFailure("raw_bundle", …)` へ明示変換する。malformed、duplicate-key、typed v1/v2 failure の既存期待値を変えないテストを置く。

### B-5 / silo から canonical predicate へ渡す exact projection が未記述

- **主張:** canonical predicate は expected exact 2 key、observed exact 1 keyを要求する一方、silo の現在値は method/governor を含む full clock mapである。プランは「置換」としか書かず、射影を明示していない。
- **file:line:** `s2-plan.md:147-160,174-185`、`orchestrator/campaign/silo_ladder_rung1.py:1962-1976,3401-3419`
- **失敗シナリオ:** 実装子が `effective_clock_comparison_passes(expected["effective_clock"], actual["effective_clock"])` と直結すると、余分な `method/governor` のため、帯域内の正常観測もすべて false になる。これを直すため exact-key gate を緩める誘惑も生じる。
- **成果物影響:** silo trial が全拒否になるか、逆に canonical consumer の forged-key 防壁が緩む。
- **強度:** **must-fix**
- **最小の是正案:** 2箇所とも expected=`{samples_mhz,tolerance_pct}`、observed=`{samples_mhz}` を明記して構築し、method/governor は従来どおり別の exact 比較にする。spy で predicate に渡った key 集合を固定する。

### B-6 / golden 移行の記述が相互矛盾し、public negative control を失い得る

- **主張:** プラン本文は既存18 vectorsを private math helperへ移すとしているが、matrix は全 vector の canonical outcome も記載する。本文どおりなら malformed/型異常 vector が public predicateから消える。また brief の「期待値を反転しない」は、裁定済みの受理集合縮小と両立しない。
- **file:line:** `orchestrator/tests/test_execution_guard.py:360-482`、`s2-plan.md:198-200,273-292,303-311`、`brief.md:48`
- **失敗シナリオ:** 実装子が既存 loop を private helper 専用に変え、public predicate の mapping/list/bool/empty negativeを削る。または brief を守るため旧 CLI/current-silo の受理期待を残す。
- **成果物影響:** forged receipt や malformed clock map の拒否退行がテストを通過するか、撤去対象の入力面・旧 current eligibility が残る。
- **強度:** **must-fix**
- **最小の是正案:** 18 vectorsを `math_want` と `canonical_want` の二重 assertionにし、既存 `want` は数学 helper側で一つも変更しない。brief は「期待値の緩和禁止。明示済み受理集合縮小は旧意味の独立 assertionを残した上で許可」と訂正する。

### B-7 / B/A/C は worker の「実装単位」にはできない

- **主張:** プラン自身が所有ファイルの重複を認め、直列投入としている。並列競合は計画していない点は正しいが、dev-wave の実装単位契約は編集所有の素集合を要求する。
- **file:line:** `s2-plan.md:5-21`、`docs/dev-wave/workers.md:19-24`
- **失敗シナリオ:** 段5が表のB/A/Cを別 worker と解釈すると、同じ `schema_v2.py`、`env_attestation.py`、silo/testsを複数 worktree が所有し、後段 patch が先段を上書きする。
- **成果物影響:** parser、policy gate、consumer closure の一部だけが落ち、統合後に受理集合が層ごとにずれる。
- **強度:** **must-fix**
- **最小の是正案:** B/A/Cを一人の author が持つ「単一実装単位内の直列 phase」と明記するか、実際に素集合となるファイル所有へ再分割する。

### B-8 / caller census は不完全だが、静的には境界互換

- **主張:** プラン未列挙 caller として `probe_hardware` alias、loop、floor/oracle/freeze/report consumer がある。これらは現状、observed dataclassやprobe-outputを直接読まず、loader/issuer/receipt境界だけを使うため直ちには壊れない。
- **file:line:** `orchestrator/campaign/env_attestation.py:447`、`orchestrator/calibrator/cli.py:345-352`、`orchestrator/campaign/loop.py:86-98`、`orchestrator/campaign/s8b_floor_campaign.py:2762-2784`、`orchestrator/campaign/s8b_oracle_driver.py:781-803,934-944`、`orchestrator/campaign/s8b_ratified_freeze.py:1803-1809,1869-1879`、`orchestrator/campaign/s8b_oracle_report.py:1202-1208,1371-1379`
- **失敗シナリオ:** loader例外型やreceipt再検算の細部が変わっても、列挙済みの直接テストだけでは report/freeze/loop の例外翻訳退行を検知しない。
- **成果物影響:** campaign journal や ratified replay が、同じ拒否を異なる terminal classとして記録し得る。
- **強度:** **backlog**
- **最小の是正案:** コード変更対象にはせず、`test_campaign.py`、`test_s8b_oracle_report.py`、`test_s8b_ratified_verify.py` を no-edit consumer regression として acceptance 範囲へ明記する。`smoke_probe.sh` は B-3 の must-fix 対象。

## 移行 matrix の全行判定

Canonical 18 vectors（`s2-plan.md:273-292`）は、次の判定になる。

| 行 | 判定 |
|---|---|
| `odd-all-inside` | 期待値不変。 |
| `even-inclusive-boundaries`、`mean-drift-same-median-inside`、`near-zero-tolerance-inside`、`zero-tolerance-exact`、`hundred-tolerance-boundaries` | 数学結果を保存し canonical だけ false にする正当な受理集合縮小。 |
| `pegasus-shaped-one-outlier`、`mean-drift-same-median-outside`、4件の mapping/list 異常、2件の empty、`tolerance-bool`、`nonnumeric-sample`、`near-zero-tolerance-outside`、`hundred-tolerance-outside` | 負例不変。ただし B-6 のとおり public predicateでも同じ負例を実行することが条件。 |

Fixture/literal matrix（`s2-plan.md:298-323`）の全行判定は以下。

- `:298-299,309,323`: schema/history/scope の期待を維持しており正当。
- `:300-308,315,317,319-320`: 非policy値や旧入力面を拒否する正当な accepted-set 縮小。緩和ではない。
- `:310-311`: legacy true を保存し current false を別 assertion にするため正当。
- `:312-314,316,318`: verdict不変の型/schema移行。`run_probe` 行だけは B-3 の failure分岐追加が必要。
- `:321`: all-green fixture の入力変更は、元の median-only outlier を `s2-plan.md:264` の負例として残す限り正当。負例を落とせば「fixtureを緑に合わせた」だけになる。
- `:322`: T126 の型移行自体は必要だが、hash版を envelope に残さないため B-2 のままでは不成立。

計画内に skip・xfail・削除はない。`s2-plan.md:228-231` の digest は「現行 tree hash の差し込み」ではなく committed historical identity の固定なので妥当である。

## 実測で反証しなかった点

- 登録較正は `tolerance_pct=2.0` かつ outlier `3080.935` である（`calibration-753f535a8d024727.json:1484,1493`）。
- `contract_sha256` は contract dataclass fieldから導出され（`env_contract.py:145-160`）、本案は登録path/SHAを動かさないため frozen pin不変という brief の主張は正しい。
- `grep -rn "tolerance_pct"` の in-scope hit はプランに対応していた。未変更なのは明示的scope外の `test_t419_probe_causality.py:173,527,533` と `tools/pegasus/probes/t419_probe_causality.py:81-119,2618`。
- T-453 の median 再導出は production 2箇所（`silo_ladder_rung1.py:1962-1965,3401-3415`）と test 1箇所（`test_silo_ladder_rung1_evidence.py:944-963`）で、brief の「3箇所」は正しい。
- 正しく実装すれば test の legacy verdict は歴史説明に限定され、collect/verify-result は raw＋current bindingを必ず加える（`silo_ladder_rung1.py:4713,4767-4776,4817-4826`）。台帳も `research_goal_eligible=false` のため、二つの current verdict は残らない（`patches/ledger.json:6-17,35`）。

## scope 外の real 所見

### X-B-1 / [T-419] campaign 閉鎖が運用宣言だけである

- **主張:** current loader はpolicy一致だけなら自己不整合な登録較正を受理する。cleanなlive観測ならissuer/consumerを通り得るため、T-419 U-2前のcampaign閉鎖は機械的には保証されない。
- **file:line:** `orchestrator/campaign/env_attestation.py:674-693`、`orchestrator/tests/test_env_contract.py:58-63,436-463`、`calibration-753f535a8d024727.json:1484,1493`、設計README `:141-153,216`
- **失敗シナリオ:** authority landing後、再較正前に利用者がcertified campaignを起動し、既知self-fail artifactと偶然帯域内のlive観測でreceiptを得る。
- **成果物影響:** T-419完了前のtrialが新authority準拠として台帳へ混入する。
- **強度:** **backlog — scope 外の real 所見 [T-419]**
- **最小の是正案:** 本waveのproduction codeへ混ぜず、handoff/release gateでcampaign閉鎖を明示し、T-419 U-2＋pin closure完了を再開条件として機械化する。

[T-478] と [T-477] の実装面へ踏み込む scope creep は見つからなかった。

## 総括

- **(a) NO-GO。**
- **(b-1)** brief の corpus 内訳と canonical-fail 母数が誤り、物理44件の対応検査もない。
- **(b-2)** T126 hash版がevidenceに残らず、run-probe/silo parser移行にも未被覆分岐と例外境界がある。
- **(b-3)** canonical exact projection・public negative control・worker所有が実装可能な粒度まで閉じていない。
- **(c)** 実装子が最初に間違えそうなのは、siloのfull clock mapをcanonical predicateへ直接渡し、全観測をfalseにする点である。