# D162 決定 (10) 発火条件の項目別監査 (2026-08-16)

`authority: none` / `default_effect: no-state-change`

本書は D162 決定 (10) が置いた 3 つの発火条件を、**連言の各項ごとに artifact の field を名指しで**
照合した記録である。この粒度は F157 の恒久対応が要求したものである — 同事故では
「probe が 3 arm で事前登録を実走前に commit し pin と checkout を持つ」という**全体の印象**から
(ii) を成立と判断し、レンズが `env_tag` / `attestation` の 0 hit で倒した。

対象 commit: `330f67d0` (main、2026-08-15 時点) → 記録時点で `9096cef8` へ ff。
計測対象: request `892042.nqsv` =
`output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/`

## 条件 (i) — 3 arm を持ち、事前登録を実走前に commit した計測が 1 本以上存在すること

**成立。**

| 項 | 証拠 |
|---|---|
| 3 arm | `verdict.tsv` の `W1` / `W2` 行が `all_samples_mode1_lt_modeX_lt_stock` を持つ。arm は stock / mode1 (劣化版) / modeX (回復候補) の 3 本 |
| 事前登録の存在 | `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md` |
| 実走前 commit | 同文書冒頭が「本書は**走行前に凍結する事前登録**である」「**結果を見てから本書を書き換えてはならない** (D126 決定 (4))」と宣言。`preregistration-witness.tsv` の `preregistration_sha256` = `a01fb93554630bf1d66102bd974f5fd9c6d4ee8fc3ccea7e89955c48ab21f257` が計測側から当該文書を束縛する |

**注意 (この計測が何でないか):** 同事前登録は
`study_label: engineering_screen / J=1 / uncalibrated / nonqualification` を自ら宣言し、
「本書は適格性 (qualification) の主張ではない」と明記する。したがって (i) を満たす計測が
実在することと、その計測が正例 artifact であることは**別である**。D162 決定 (8) は
既存 receipt の遡及昇格を禁じており、本監査もそれを主張しない。

## 条件 (ii) — その計測が環境タグ・測定 checkout・pin・attestation を持つこと

**不成立。4 項の連言のうち 2 項が欠ける。**

| 項 | 判定 | 実測 |
|---|---|---|
| 環境タグ (`env_tag`) | **欠** | artifact dir 全体で `grep -rl "env_tag"` が **0 file** |
| 測定 checkout | 実質あり | `preregistration-witness.tsv` の `repo_head` = `425ed1908dfd78cda97c48c2b248cdf6b83b1e91`、`ccbench_head` = `d706650cdb31e442bef45b9b4216951d4fb40969`。ただし `checkout` という語の hit は 0 file であり、field 名としては存在しない |
| pin | あり | 同 witness の `runtime_pbs_sha256` / `t139_positive_control.patch_sha256` / `t139_positive_control_probe.sh_sha256` / `t139_positive_control_probe.pbs_sha256` / `policy_sha256`。加えて `dependency-witness.tsv` が `expected_pin` と `observed_head` の一致 (`clean=1`) を依存ごとに記録 |
| attestation | **欠** | artifact dir 全体で `grep -rl "attestation"` が **0 file** |

**別計測の attestation を合成してはならない。** `orchestrator/qualification/contract.py` の
Pegasus 環境契約 (`env_tag: "pegasus"` / `attestation_mode: "required"`) は T-126 の別機構であり、
`892042` の証拠ではない。D162 決定 (8) が T-126 artifact の遡及昇格を禁じている。
D229 決定 (6) は「pilot 自身を発火条件 (i)(ii) を満たす計測にできる」と書いており、
**(ii) がここで初めて成立する**というのが裁定側の設計である。

## 条件 (iii) — 判定を読む consumer の実 hook が実在すること

**不成立。**

`orchestrator/` と `tools/` を対象に、RF 判定を読む側が必ず持つ語
(`recovery_fraction` / `rf_acceptance` / `pairing_valid` / `weak_denominator` / `fieller` /
`Fieller`) を `--include=*.py` で検索して **0 行** (`head` で切らず全件計数)。
Q11 自身も「RF を消費する経路が無い」と明記し、
`output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md` も consumer 0 件と記録する。

## 連言としての結論

(i) は成立し、計測 ID (`892042.nqsv`) と artifact path を書ける。しかし (ii) と (iii) が
不成立であるため、`DW-G04` が要求する「発火条件を満たす既存 artifact path か計測 ID」は書けない。
**したがって production code・schema・test の機械化は発火しない。**

この結論は F157 が 2026-08-07 に確定させた事実認定 (「成立していたのは (i) だけである」) と
一致する。1 年でも 1 日でもなく **9 日後の再監査で同じ結論**になったことは、
(ii)(iii) を動かす計測 (pilot) がその間に 1 本も実走していないことを意味する。

## pilot が実走していないことの機械的根拠

- `docs/decisions.md` の運用状態 block が `pilot_submission = forbidden` /
  `main_submission = forbidden` / `source_main_run_gate = not_implemented` を保持し、
  解除権限は canonical decision だけが持つ。
- `orchestrator/preregistration/stress_check_simulation.py` の `claim_scope` は
  `pilot_ready: False` と `remaining_unmet_pilot_prerequisites: [1, 4, 5, 6, 7, 8, 9]` を持つ。
  **ただしこれは状態表示であり admission gate ではない** (同 module 冒頭が明記)。
  投入を止めている正本は上の decision 側である。
