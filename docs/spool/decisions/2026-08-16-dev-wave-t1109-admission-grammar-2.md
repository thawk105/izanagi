---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1109-admission-grammar
seq: 2
---

## {{D:pbs-jobid-env-grammar}}. PBS_JOBID の受理文法を qsub request-ID authority の optional `0:` 拡張として定義し、qsub 側は不変に保つ

**決定 (2026-08-15 ユーザー裁定 [T-1109] = 択 (a) の実装):**
`orchestrator/campaign/claude_transport.py` の `PBS_JOBID_PATTERN` を
`(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*` とする。D122 決定 (2)(ii) の
「既存 qsub authority と**逐語同一**の文法」を、本 D が次へ supersede する。

1. `PBS_JOBID` は非空で、`(?:0:)?` と qsub request-ID authority
   (`orchestrator/qualification/qsub_binding.py` の `_JOB_ID_TEXT`) の連結に fullmatch する。
2. **qsub stdout parser の受理集合は変えない。** qsub authority は「qsub が印字する request ID」の
   文法であり、環境変数の文法ではない。
3. `orchestrator/qualification/collector.py` の `_JOB_ID` は transport と同一文法とする
   (拡張前から `(?:0:)?` を持っており、実質的に transport が collector へ揃った)。
4. D122 決定 (2) の (i)(iii)〜(viii)、`CLAUDE_ENV_ALLOWLIST` の 5 key、
   従量経路 env 5 key の拒否は不変とする。
5. `PBS_JOBID` は引き続き **cheap witness であって attestation ではない** (D122 決定 (7))。
   文法を広げても防護の主張は増えも減りもしない。

**理由:**

- **実機値が述語を通らなかった。** NQSV が渡す実値は `0:<request-id>` 形 (job index + request ID)
  であり、colon を含まない旧文法を必ず外れる。計算ノードでの role 実行が全面的に塞がっていた。
- **repo 自身が実機値を保持していた。** `output/env/pegasus/calibration/job-staging/` 配下には
  `0:867863.nqsv` 〜 `0:867876.nqsv` 等を directory 名に持つ tracked artifact が
  **526 file** あり、`reservation.json` は `"job_id": "0:867876.nqsv"` を持つ。
  述語が「colon を含まない」と主張し続ける間、repo は同じ値を tracked で抱えていた。
- **qsub 側を広げると防護が減る。** byte 一致を維持するために qsub authority へ `0:` を許すと、
  qsub stdout parser が新たに `0:` 付き出力を受理する。受理集合の非対称性は意図されたものであり、
  境界テストで固定する。
- **新たに拒否される値は 1 件もない。** 旧負例 15 件はすべて拒否のまま
  (colon は先頭 `0:` の 1 形だけが通る)。過剰拡張を防ぐため
  `0:` / `0:0:...` / `0::x` / `00:x` / `1:...` / `0:job:id` を負例へ追加した。

**`job_id` の二義性 (記録すべき事実):** 同名 field が repo 内で 2 規約に分かれている。
qsub-binding record の `job_id` は**接頭辞なし**の request ID が正で、
`0:` 付きを与えると `QsubBindingError` になる。一方 reservation / job-staging record の
`job_id` は**接頭辞あり**の raw `PBS_JOBID` が正である。両者を統一してはならない。

**却下した選択肢:**

- **(b) job script が request ID を切り出して渡す** — gate が検査する env の書き換えであり、
  述語を通すために入力側を細工する迂回に当たる。
- **(c) witness を `PBS_JOBID` 以外の実在証拠へ替える** — D122 決定 (7) が witness を
  attestation でないと明言済みで、置換に見合う防護の増分がない。
- **qsub authority も同時に拡張して byte 一致を維持する** — 上記のとおり qsub stdout parser の
  受理集合まで広がり、防護が減る。

**研究状態への影響:** 計算ノードでの transport admission が実機値で通るようになる。
これは 8c live 実行の**必要条件の 1 つ**であって十分条件ではない
(build 前の attestation と、計算ノード実環境での D122 他条件は本 D の射程外)。

## {{D:fail-closed-admission-positive-control}}. 起動を止める fail-closed admission 述語に、実在 production 値を自分の述語へ通す positive control を義務づける

**決定 (2026-08-15 ユーザー裁定 [T-1111] = 「義務づける。ただし起動を止める型の
fail-closed admission 述語に限定」の実装):**

**族の境界 (public stop point 単位):** provider / build / benchmark / certified writer の
**最初の起動前**に、machine・scheduler・live probe 由来の入力を固定 relation へ通し、
未知・不正・観測不能なら通常の起動を拒否する production gate。
post-run consumer、内部 capability / schema の再検証、dispatch への切替、
診断だけの gate は含めない。

**義務:** この族の member は、**実在の production 値を自分の述語へ通す positive control** を持つ。
新規 member の追加と既存 member の変更は、同じ変更単位で control を伴う。
control の期待値を実行時 `os.environ`・production 定数・戻り値自身・loader から作ってはならない
(D122 決定 (6) が同型の退化を却下している)。

**member inventory (本 D 時点):** 各 member は停止点・実在値の正本・**positive nodeid**・
充足状態を持つ。nodeid 欄が本義務の拘束点であり、member を変更する改修はこの nodeid を
同じ変更単位で追随させる。

| # | 停止点 | 実在 production 値の正本 | positive nodeid | 充足状態 |
|---|---|---|---|---|
| 1 | Claude transport admission (`claude_transport._preflight_source_env`) | tracked `reservation.json` の `0:867876.nqsv` | `orchestrator/tests/test_claude_transport.py::test_recorded_compute_pbs_jobid_passes_transport_and_receipt_admission` | 充足 |
| 2 | runtime attestation (`execution_guard` / `env_attestation`) | 登録済み較正 `calibration-753f535a8d024727.json` | (無し) | **unmet — D143 のユーザー裁定待ち。真正面に書けば現在は赤である。skip / xfail / 期待反転で緑に見せてはならない** |
| 3 | measurement site admission (`p3_s4_loop_trigger_gating`) | 同較正の hostname | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_recorded_pegasus_hostname_reaches_measurement_site_admission` | 充足 |
| 4 | 8c build site opt-in (`p3_autonomous_workload_trial`) | 同較正の hostname | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_recorded_compute_site_and_opt_in_pass_build_site_admission` | 充足 |
| 5 | certified-writer environment (`certified_writer_admission`) | tracked `reservation.json` の nonce と job ID | `orchestrator/tests/test_campaign.py::test_certified_writer_environment_accepts_recorded_pegasus_identity` | 充足 |
| 6 | reservation admission (`reservation.check_reservation`) | 同 `reservation.json` の全 field | `orchestrator/tests/test_reservation.py::test_recorded_pegasus_reservation_passes_live_admission` | 充足 |
| 7 | competing-bench admission (`calibrator.runner.classify_competing_probe`) | tracked `isolation.txt` の raw triple (6 file / 53 記録が同一) | `orchestrator/tests/test_calibrator.py::test_recorded_competing_bench_probes_pass_admission` | 充足 |
| 8 | provider live env / receipt 一致 (`claude_projected_provider`) | (未取得) | (無し) | **unmet — 実在 production 値を未取得** |

**member 6 (reservation) の射程を限定する。** この control は
`t126_driver` / `s8b_floor_campaign` / `s8b_oracle_driver` の停止点を守るが、
**8c の launch path には配線されていない。**
8c の事前登録証拠契約 (`s8c_preregistration_evidence_contract.v1.json`) は
`run_trial -> reservation.single_process_required -> campaign launch` を要求するが、
コード上の到達は確認できなかった (契約と実装の乖離)。
**member 6 の control が緑であることを、8c launch の allocation provenance が
保護されている証拠として読んではならない。** 配線の要否は別途裁定する。

**恒真化の禁止 (member 3/4 で実測された退化):** 受理側が `OTHER` と `PEGASUS_COMPUTE` の
双方を受理するため、実 hostname を admission へ通すだけの control は
**分類器が壊れていても緑になる**。site 系の control は
「分類結果そのものを独立 literal で先に固定し、その分類値で admission が通ることを確認する」
2 段で書く。条件付き機能は受理側と拒否側を対にする。

**機械的完備性は主張しない。** member を機械列挙する registry gate は本 D では新設しない。
D96 は AST 案 1 件を却下したのみで独立 2 例と再裁定があれば再提案可能だが、
現時点で member 2 と 8 が unmet であり、今 registry を作ると**偽の完備性**を与える。
発見経路は decisions 索引と本 D とする。

**理由:** F97 (登録済み較正が自分自身の attestation 述語を通らない) と
`{{D:pbs-jobid-env-grammar}}` の実機 `PBS_JOBID` は、別 producer / 別 consumer の独立 2 例であり
`DW-G03` の族一般化閾値を満たす。どちらも「**誰かが実際に走らせるまで発見されない**」型で、
発見時には live 実行が全面的に塞がっていた。値の側でなく述語の側を実物で撃つ検査が要る。

**却下した選択肢:**

- **member を機械列挙する registry gate を今作る** — 上記のとおり偽の完備性を与える。
- **義務を dev-wave docs へ書く** — 同 docs は byte 予算と exact pin の制約下にあり、
  全 wave 共通の短い義務以外を置く場所ではない。
- **unmet member に skip / xfail / 期待反転を置いて緑に見せる** — 規律 2 に反する。
  unmet は unmet として台帳に残す。

**研究状態への影響:** 受理集合そのものは変えない。変わるのは、この族の述語を
新設・変更する改修に課される検査義務である。
