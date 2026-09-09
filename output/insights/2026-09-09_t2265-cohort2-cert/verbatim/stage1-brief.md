# 段 1 brief — [T-2265] cohort 2 の seed 別実行体と 24 スレッド条件の直列性認証

基準: local main `cbcdb6c91bd2eced76bd6a82650204c357c1b299`。
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert`
(branch `worktree-dev-wave-t2265-cohort2-cert`)。

## 研究前進

cohort 2 の反実仮想 ITT の主判定 (`recommended_direction_superior`、+4.900%、95% CI
[+3.316%, +6.509%]、worklog 1393) は、**認証されていない実行体で得た性能値**に立っている。
事前登録 §3 が「本試験は未認証」と書いており、D1643 / D1814 は未認証腕の値を headline に
昇格させることを禁じている。認証が通れば、この主判定を論文の主張として使えるようになる。

**完了判定:** cohort 2 が使う policy 2 の 12 本の seed 別実行体について、group receipt が
`complete = true`・certified serializable 24/24・anomaly 0 件で発行されること。加えて 24 スレッド
条件の認証経路が実測で 1 group 通ること。覆えていない範囲が成果物に job 数つきで書かれること。

## 確定済みユーザー裁定と、それが覆す既存裁定

ユーザーの直接指示 (本 wave の command 引数) が対象・規模・分割方針を定めている。これは
**D1852 の却下欄「認証 mode へ seed を通す — 受理形が広がり、job 数が 13 倍になる」を上書きする。**
D1852 の却下理由は費用 (「312 job になり、現実的でない」) だけであり、ユーザーはその費用を
承知のうえで 312 job を指示している。D1814 の「認証は headline へ昇格させたくなった時点で、
選定した腕だけについて改めて諮る」にも合致する。段 7 で D1852 を追記訂正する新 D を起こす。

## scope

- **(S1) 受理形に 2 軸を足す。** `--mode certify` が (i) cell が `cw-as-dyn-c2-p2` のときに限り
  事前登録の 12 seed のいずれかを `--step-policy-seed` で受理し、(ii) thread 数 24 と 48 を
  受理する。どちらも **exact な閉表**とし、1 つ外れた literal (13 番目の seed、threads=23/25/47/49)
  が拒否されることを検査する。
- **(S2) 束縛を新 2 軸へ通す。** raw allowlist、parsed membership、row、group receipt、claim、
  namespace、PBS の各検査が `CERT_THREADS[0]` と `CERT_STEP_POLICY_SEED_BY_CELL` の固定値では
  なく、その request の実 thread 数・実 seed と exact 一致することを要求する。claim 文には実際の
  thread 数と seed を書き、それ以外を認証したと読めない文言にする。
- **(S3) PBS driver** の `certify mode cannot be combined with step policy seed` (111 行台) を、
  閉表の範囲でだけ通す。
- **(S4) 認証走行。** 下の格子を group 単位で投入し、receipt を収集する。
- **(S5) 記録。** insight に覆えた範囲・覆えていない範囲を job 数つきで書く。

**scope 外** (ユーザー指示「本題の認証走行と記録だけ」に従う):
事前登録 doc の書き換え (bytes を 6 箇所が pin。erratum 相当)、`cw-as-dyn-c2-p0` の認証、
D1656 が非保証と明記した既発行 receipt 再検証の閉包 (前 wave の裁定 §9-1)、性能測定、
仮想リスク向けの gate・検査・台帳・一般化。

## (P1) 対象格子 — 親の provisional 裁定・攻撃対象

1 group = 3 workload x 8 slot = 24 job。cohort 2 は p0/p1/p2 x 3 workload x threads {24,48} を使い、
seed 別実行体を持つのは policy 2 だけ (事前登録 §9「policy 0 / 1 は seed を使わないので既定 seed の
genome を保つ」)。既認証は p1@48 と p2@既定 seed@48 の 2 group。

| 波 | 対象 | group | job | 位置づけ |
| --- | --- | --- | --- | --- |
| 1 | p2 x 12 seed x 48 threads | 12 | 288 | **必須。** 主層 (policy 2 / write-heavy / 48t) を直接支える |
| 2 | p1 x 既定 seed x 24 threads | 1 | 24 | **必須。** 24 スレッド軸を実測で開く |
| 3 | p2 x 12 seed x 24 threads | 12 | 288 | 余力があれば。副次層の被覆 |

波 1+2 = **312 job** でユーザー指定の規模に一致する。波 3 まで含めた完全被覆は 600 job。
波 3 を走らせない場合、覆えていない範囲は「p2 x 12 seed x 24 threads (288 job) と p0 全体」と明記する。

## 不変条件

- **規律 1:** 認証は trace-enabled build。本 wave は性能値を 1 件も測らない。既存の性能成果物
  `dynamic-backoff/perf/stage1-rep0-0_985871.nqsv.json` は identity 束縛として参照するだけ。
- **規律 2:** anomaly が 1 件でも出た cell は即 reject し、その group を certified と書かない。
  受理形を広げる変更が、既存の拒否を 1 つも消さないことを負例で示す。
- 既存 4 cell のうち `tuned` / `cw-as-dyn` の束縛と、既定 seed x 48 threads の受理形を
  **1 文字も変えない。** 既発行の 2 receipt を無効化しない。
- 事前登録 doc の bytes を変えない (`MEASUREMENT_PREREGISTRATION_SHA256` ほか 6 箇所の pin)。
- 受理形の拡張は cell 別に閉じる。p1/p0 に seed 軸を開かない (seed を使わない腕)。

## 成果物

- `output/insights/2026-09-09_t2265-cohort2-cert/README.md` — group ごとの receipt path・sha256・
  certified 数・anomaly 数の表、覆えた範囲と覆えていない範囲、変異台帳、逐語。
- group receipt: `izanagi-job-evidence/dynamic-backoff/certify/<attempt>/group-receipt.json`。
- `docs/spool/` fragment (worklog 1 件、decisions 1 件 = D1852 の追記訂正)。

## 並列分割方針

- 実装は Codex `role=author`。編集面は `tools/pegasus/probes/t2187_adaptive_const_probe.py`、
  同 `.pbs`、`orchestrator/tests/test_t2187_adaptive_const_probe.py` の 3 file。
  受理形 (probe python + test) と PBS driver で unit を分けられるが、閉表定数を共有するため
  **1 unit 直列**を既定とする (所有の重なりを作らない)。
- 投入は group 単位。queue に自分の滞留を **48 job 以下**に保ち、peer wave を飢えさせない。
  gen_S は wave 開始時 TOT 31 / RUN 17 / HLD 14 で、他 wave も投入中。
- 認証 job の実行中に、変異 matrix と受入全走を親側で並行して進める (待ちは 1 本)。
