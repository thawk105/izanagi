# 段 4 裁定 — [T-1311] arm execution authority

親裁定。2026-08-17 23:50 JST。plan v1 は **不採用**、plan v2 を以下で確定する。

## 0. 裁定 inbox の再走査

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` を再走査。`T-1311` / arm authority /
arm-binding に触れる未裁定項は **0 件**。`2026-08-17-t1202-t1197-decider-version-generation-collision.md`
は `s8c_preregistration_evidence.py` と `DECIDER_VERSION` を触る未 land wave だが、
本 wave はそのどちらも編集しないため file 衝突なし。

## 1. 親自身の実測誤りの訂正

brief の「`output/` の `p3-t178` hit 0 件」は**誤り**である (lensA 所見 10)。狭い path
(`output/s8c-trial-registry/`, `docs/`) しか grep していなかった。実際は tracked 29 file が hit する。
ただし全件が historical report / mutation 台帳であり、current campaign ID の live pin ではない。
**結論は変わらない** (凍結 bytes の巻き添えなし) が、根拠は「hit 0」ではなく
「hit は全て historical、live pin なし」である。実装子は historical output を更新してはならない。

## 2. 最大の裁定 — [T-1310] は前提ではない (両レンズ real、親が独立に裏取り)

plan v1 の「実装順は必ず `T-1310 → A → B → C`」は **refuted**。arm が選ぶ 3 入力は
**今日すべて構成できる**。親の実測:

- `orchestrator/campaign/s8b_holdout_freeze.py:78-102` が H1=rr80 / H2=rr20 の完全定義
  (`skew=0.9`, `rmw=0`, `records=1_000_000`, `threads=48`) を凍結保持し、
  `:102` に `DERANGEMENT = {"rr80": "rr20", "rr20": "rr80"}` を持つ。derangement は既存であり新設不要。
- `orchestrator/campaign/s8b_descriptor.py:208-212` の `descriptor_for_holdout()` が
  その entry を projection + validate して descriptor を返す既存 API である。
- 実体も既に凍結済み: `output/s8b-freeze/selector-runs/payload_rr80_on.json` の
  `descriptor` は rr80 / 1,000,000 records / 48 threads / `source=campaign_search_config_projection`。
  hash は `test_frozen_artifacts.py:70-79` で pin され、
  `payload_rr80_on` = `payload_rr20_swapped` = `f894acc1…`、
  `payload_rr20_on` = `payload_rr80_swapped` = `bedc2c49…` と**交差している**。
  すなわち on/swapped の descriptor 同一性は凍結 bytes として既に実現されている。

[T-1310] が要るのは **実 benchmark の production profile** (`WORKLOADS` に rr80/rr20 を足し
`_campaign_for` / `_perf_for` の 100k/4 を 1m/48 にする) だけであり、arm input の解決には要らない。

**帰結**: 単位 A / B / C はすべて本 wave で実装する。ただし実 benchmark 実走は本 wave の scope 外。

## 3. `off` 中立入力の確定 (plan v1 から変更)

plan v1 の `source="human_declared"` / 262 bytes literal は **不採用**。理由は lensA 所見 2 =
`source` 一 field で role が off を識別でき、対照実験の blind 性が壊れるため。

**確定形**: 既存 projector を通して生成する。

```
project_from_search_config({
    "records": 1_000_000, "threads": 48,
    "ycsb": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
})
```

親が実測した canonical bytes は **281 bytes**、sha256 =
`8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89`。
`source` は `campaign_search_config_projection` となり on/swapped と区別できない。
`validate_descriptor` も通過を実測済み。

**値の非恣意性は 2 本の独立根拠で支える** (どちらか一方でも欠けたら生成器は失敗させる)。

1. 凍結端点 80 と 20 の算術中点が 50 である (`s8b_holdout_freeze.py:78-79`)。
2. 同 module が `_POSITIVE_RATIO = "50"` を `rr50-positive-control` として既に凍結している
   (`:80`, `:594-598`)。skew / rmw も同 module の `_FIXED_SKEW` / `_FIXED_RMW` と一致する。

生成器はこの 2 根拠を実 module から読んで照合し、不一致なら literal を書き換えず**失敗する**。

## 4. digest の定義 (P1 を修正、lensA 所見 4 採用)

**二層とする。** 一層では resolver 退行 (2 arm が同一 bytes を返す) を検出できない。

- `content_digest = SHA256(canonical_execution_input_bytes(selected_descriptor))`
  — arm 名を preimage に含めない。
- `arm_binding_digest = SHA256(domain_separator_v1 || holdout || arm || content_digest)`
  — domain separator は固定 literal。

さらに **pairwise 非同一検査**を必須とする: 同一 holdout の `on` / `off` / `swapped` の
`content_digest` が 3 つとも相異なること。2 つでも一致したら launch を拒否する。
`on(h)` と `swapped(h')` (h≠h') が一致するのは正しい (derangement) ので、これは禁止しない。

## 5. sink は 6 でなく 7 (lensA 所見 5 採用)

`provider/payload_*.json` と `envelope_*.json` = 「実際に provider へ送った bytes」が
第 7 の sink である (`claude_projected_provider.py:258-271,341-356`)。現行 completeness は
provenance が非空であることしか要求しない (`autonomous_trial_completeness.py:725-735`)。
ここを塞がないと「台帳は off、実 stdin は on」が通る。C10 契約も
`provider_payload_sha256` / `provider_envelope_sha256` を名指ししている。**scope 内**。

## 6. 恒真化の回避 (lensA 所見 6 採用)

acceptance / completeness 側の再導出は **producer helper (`_campaign_for` / `_descriptor_for`) を
呼んではならない**。persisted campaign lock / config bytes を独立に読み、closed key set と
digest field を直接要求する。producer と verifier が同じ関数を呼ぶ形は定義上恒真である。

## 7. terminal sink (lensA 所見 8 / lensB 所見 6・12 採用)

`enforcement_arm` に digest を詰める案は **不採用**。receipt の field 意味を壊す。
arm label はそのまま保持し、digest は**独立 field**として formal receipt / projection へ追加する。
`OriginProducerInputs.enforcement_arm` は**削除しない** — issued binding から導出した値を
入れる形へ変える (caller 指定 token 検査は削除)。
`reflux_formal_consumer.py` は**単位 A の所有**に加える (plan v1 は owner 不在だった)。
`reflux_result_evidence.py` の launch admission hash 連鎖が動くのは設計上必然の赤。

## 8. report への arm label を入れない (親の追加裁定)

plan v1 は run-start / report の nested `arm_execution` に `arm` を含めるとした。**不採用**。
`arm_execution` は `{input_schema_version, content_digest_sha256, arm_binding_digest_sha256}`
だけを持つ。arm label を report へ戻すと、本タスクが禁じた「宣言値の往復照合」への誘導になる。
label は digest から再解決して得る。既存の
`test_p3_autonomous_workload_trial.py:5417-5429` の `assert "arm" not in report` /
`assert "holdout" not in report` は**そのまま残す**。

## 9. 所有と起動順 (lensB 所見 2・5・8 採用)

- `bind_trial_arm` を `admit_registered_launch` から呼ばない。呼ぶと registry/reflux の
  一時 repository fixture が arm artifact を持たないため一括で壊れる
  (`test_trial_registry.py:130-151,1382-1392,1597,1627,1675,2008,2044`、
  `test_reflux_origin_binding.py:332`)。**p3 launcher が明示的に呼ぶ**。
- `SCHEMA_VERSION` を全体 bump しない。role payload と run-start が同一定数を共有しており
  (`p3_autonomous_workload_trial.py:121-122,1594,3080`)、bump すると role payload 契約まで動く。
  `arm_execution` は version を上げずに nested record として足す。
- 単位 A = `s8c_arm_inputs.py` (新規 leaf、p3 も completeness も import しない) +
  `trial_registry.py` **全体** (acceptance builder `_expected_registered_launch_admission_record`
  と `assert_trial_registry_acceptance` を含む) + `reflux_origin_binding.py` +
  `reflux_formal_consumer.py` + 対応 test。
- 単位 B = `p3_autonomous_workload_trial.py` + 対応 test。7 sink の配線。
- 単位 C = `autonomous_trial_completeness.py` + `layer3_report` 系 test。digest chain 検査。
- **直列 A → B → C**。所有は素集合。

## 10. 凍結世代 (lensB 所見 10 を refuted)

`docs/phase3-8c-preregistration.md:247-259` の改訂手続きが `DECIDER_VERSION` bump を要求するのは
**判定器・評価器・射影それ自体**の意味を変える場合である。本 wave は
`s8c_preregistration_evidence.py`・契約 JSON・規範本文のいずれも編集しないため bump は不要。
評価される production code が変わって verdict が動くのは、評価器が本来行う仕事である。

**ただし測定義務を課す**: 実装後に C01〜C12 の status / reason_code を library 経路で取り直し、
着手前 (下記) からの差分を親へ報告する。想定外の変化があれば親が裁定する。
着手前の実測値 (HEAD 2a3b5055): C01=UNSATISFIED/workload-projection-mismatch、
C02=EVIDENCE_UNDEFINED/arm-binding-declared-only、C03/C05/C06/C07/C08/C11=EVIDENCE_UNDEFINED、
C04=UNSATISFIED/crash-policy-cell-partial、C09=UNSATISFIED/formal-acceptance-layer3-consumer-absent、
C10=UNSATISFIED/cross-binding-verifier-incomplete、C12=UNSATISFIED/allocation-enforcement-consumer-absent。

## 11. scope 外と判定した real 所見 (裁定パッケージへ返す)

- **[lensA 所見 2 後半] role payload の `workload` token 漏洩。** `_COMMON_PAYLOAD_KEYS`
  (`p3_autonomous_workload_trial.py:261-265`) が `"workload"` を含み、`_common_payload`
  (`:1589-1606`) が真の workload 名を role へ渡す。off arm では descriptor が rr50 でも
  role は `workload="rr80"` を見るため、descriptor ablation を迂回できる。
  **real。しかし scope 外** — 修正は role payload 契約 (事前登録の凍結範囲に接する) の変更であり、
  digest authority とは別の設計択一である。
  成果物影響: 6 cell の on/off 差と swapped 追従を descriptor 効果として解釈できなくなる。
- **[lensA 所見 11] C02 / C10 の充足と production mode 結線。** C02 は
  `machine_checkable:false` かつ evaluator table に無く、`accept_trial` も不在。本 wave では
  充足しない。成果物影響: 現時点の certifying receipt の受理集合は 1 件も広がらない。
- **[T-1310] の benchmark profile。** 別タスク。本 wave の resolver が読む
  `s8b_holdout_freeze.HOLDOUTS` と、T-1310 が入れる production profile が
  **同一 bytes を指すことを T-1310 側が assert する**必要がある。申し送る。

## 12. 変異事前登録 (DW-M01)

削除変異は使わない (lensA 所見 9)。全て「**有効だが誤った digest**」型とし、単一理由性を確認する。

|#|変異|位置|殺す検査|偽 kill の回避|
|---|---|---|---|---|
|M1|cell descriptor の sealed digest を別 arm の有効 64hex へ差替|単位 B の descriptor sink|digest chain 検査|key 削除による schema 赤を使わない|
|M2|`search_config` から digest だけ省く (署名維持)|単位 B の campaign sink|独立 campaign verifier|既存 campaign golden の kill と区別する|
|M3|proposal の digest を有効だが誤った値へ|単位 B の proposal sink|proposal 再読込検査|同名作成による collision を避ける|
|M4|invocation ID を digest 抜きの正規表現適合 ID へ|単位 B の invocation sink|invocation 検査|provider ID 形式違反にしない|
|M5|run-start の digest を stale な有効 64hex へ|単位 B の run-start sink|run-start 検査|exact key 赤にしない|
|M6|terminal report の digest を stale な有効 64hex へ|単位 A/B の terminal sink|terminal 検査|`enforcement_arm` 非空検査で殺さない|
|M7|provider payload の digest 束縛を外す|第 7 sink|provider payload 検査|provenance 非空検査で殺さない|
|M8|**wave 前の実コード形**: arm 非依存 campaign / `rr80.g1.planner` 形の invocation ID / caller 指定 `enforcement_arm`|各 sink|全検査|—|
|M9|pairwise 非同一検査を外し on/off が同 bytes を返す resolver|単位 A|pairwise 検査|—|

**正例 (過剰拒否の検出)**: H1/on の正規 run 一式が全 7 sink で緑になること。
各変異テストは期待する reason code を固定し、import / TypeError / FileExistsError /
既存 assert による赤を KILLED と数えない。

## 13. 不変条件 (段 5・6 の子へ全文継承)

- `s8c_preregistration_evidence.py`、`s8c_preregistration_evidence_contract.v1.json`、
  `output/s8c-preregistration/condition-freeze/`、`docs/` を編集しない。
- `assert_trial_registry_acceptance` を改名しない。
- `s8c_acceptance_receipt.py` の `MANDATORY_NON_CERTIFYING_REASONS` と `certifying=false` を外さない。
- 既存テストの期待値を反転・緩和・skip・削除しない。historical pin
  (`test_artifact_admission.py:216-223`、`test_reflux_originless_compatibility.py` の
  `_PRE_WAVE_ORIGINLESS_BASELINE`、`test_autonomous_trial_completeness.py:92-219`) を保持し、
  current epoch を**追加**する。
- 宣言値どうしの往復照合を新設しない。
- historical output artifact を更新しない。
