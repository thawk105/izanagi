## 所見

**1. 不変条件 8 項目に対する違反は見つからない**

- 主張 — 実装が裁定の不変条件を破り、既存の schema、非 certifying 構造、発行式、計算式、aggregate、legacy 受理集合のいずれかを変更している。
- 原典 — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1748-receipt-leaf-binding/s6/s4-adjudication.md:79-91`、`orchestrator/campaign/s8c_acceptance_receipt.py:31-39`、`:56-108`、`:285-297`、`:751-780`、`:858-866`、`:1048-1055`、`:1381`、`:2026-2038`、`:2053-2074`、`orchestrator/campaign/trial_registry.py:6167-6175`、`:6305-6308`、`:6319-6341`、`orchestrator/campaign/autonomous_trial_completeness.py:4165-4214`、`:4217-4261`、`:4566-4589`
- 判定 — **refuted**。8 項目を個別に照合した結果は次のとおり。

  1. v5 version、top-level/trial field 集合、canonical JSON plus LF 検査は不変。
  2. `certifying is False` と必須理由コード検査は不変。
  3. 発行側は従来どおり `verify_s8c_cross_binding` の `receipt_sha256` を leaf とし、それを aggregate 化する。no-build、build-failure、build の三式も変更されていない。
  4. 新 helper に subprocess 呼出しはなく、直接起動点は従来の `_git` 一箇所。
  5. completeness import は helper 内の `:1381`。
  6. leaf 検査後にも既存 aggregate 検査が残る。
  7. 新 leaf 検査は `SCHEMA_VERSION` のみ。v3/v4 は従来の aggregate 検査だけを通る。
  8. production 追加は裁定対象の helper と v5 leaf 比較だけで、別 gate、台帳、互換層はない。
- 深刻度 — **nit**（修正不要）
- 成果物影響 — forged v5 leaf の受理集合だけが意図どおり縮小し、legacy 受理集合、certified 選択、既存 proof 参照値は変わらない。

**2. 新しい leaf 照合は全 current v5 trial で発火する**

- 主張 — leaf 照合が `rederive_arm_execution` block の内側、または早期 return の後ろにあり、任意 leaf を通す v5 経路が残っている。
- 原典 — `orchestrator/campaign/s8c_acceptance_receipt.py:1999-2008`、`:2008-2038`、`:2039-2077`、`orchestrator/campaign/autonomous_trial_completeness.py:4225-4230`、`:4232-4261`
- 判定 — **refuted**。比較は trial loop 内かつ `if rederive_arm_execution` と同じ深さにあり、report/journal digest と arm 検査の成功後、各 v5 trial に対して実行される。no-build と build-failure の内部 return は digest を helper へ返すだけで、その後 `:2033` の比較を通る。先行検査や例外で到達しない経路は、その時点で verifier 自体が失敗し、`VerifiedAcceptanceReceipt` を返さない。関数の正常 return は全 trial、aggregate、attempt registry 検査より後の `:2077`。
- 深刻度 — **nit**（修正不要）
- 成果物影響 — 先行 gate を通った全 v5 trial が leaf 照合を受けるため、任意 leaf を含む受領証が受理集合へ残る経路はない。

**3. 差分は既存防壁や test の検出力を弱めていない**

- 主張 — 既存検査または期待値が削除・緩和され、特に `_fixture` の `"do_build": False` が従来検査を迂回させている。
- 原典 — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1748-receipt-leaf-binding/s6/implementation.diff:5-84`、`:89-164`、`:169-178`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:232-272`、`:492-528`、`:1039-1089`、`:1328-1389`、`orchestrator/tests/test_trial_registry.py:1823-1909`、`orchestrator/campaign/s8c_acceptance_receipt.py:1414-1507`
- 判定 — **refuted**。production の既存行は docstring 以外削除されず、aggregate gate も維持される。test 差分にも既存 assertion や期待する拒否文言の変更はない。`do_build=False` は新 completeness 計算の no-build mode を選ぶが、従来の report identity、arm cell、descriptor、arm digest、journal run-start の検査は `do_build` を条件にせず継続する。合成 leaf を実式へ置き換えた fixture と、materialized-build 正例の追加は検出力を下げない。
- 深刻度 — **nit**（修正不要）
- 成果物影響 — 既存の拒否集合と proof 検査は維持され、新しい負例だけが leaf 差替え受理を検出する。

**4. helper 入力による恒真化はない**

- 主張 — `report_bytes`、`journal_bytes`、`run_root`、`output_root` のいずれかが stored leaf の宣言値から作られ、比較が自己照合になる。
- 原典 — `orchestrator/campaign/s8c_acceptance_receipt.py:929-960`、`:1141-1163`、`:1976-1987`、`:2008-2033`、`:1366-1394`、`orchestrator/campaign/trial_registry.py:6081-6085`、`:6123-6138`、`:6167-6173`、`:6286-6308`、`orchestrator/campaign/autonomous_trial_completeness.py:4225-4261`、`:4270-4277`
- 判定 — **refuted**。

  - `report_bytes` は `report_path` の現物を読み、`report_sha256` と照合した戻り値。
  - `journal_bytes` も同様に journal 現物を読み、宣言 digest と照合した戻り値。
  - `run_root` は receipt の `attempt_journal_path` の親だが、その path は tracked receipt bytes に含まれ、repository 内・非 symlink の同一 path を `_assert_digest` が直前に検証している。発行側も同じ journal path の親を使用するため十分であり、stored leaf は関与しない。
  - `output_root` は report 現物の `do_build` と `run_root` から導出される。materialized build では発行側が campaign roots の output root と `run_root.parent.parent` の一致を検査し、completeness 側も campaign roots から再導出した root と比較する。no-build は双方 `None`、build-failure は output root を参照する前に専用式を返す。
  - stored leaf は helper 入力ではなく、最後の `:2033` でのみ再導出値と比較される。
- 深刻度 — **nit**（修正不要）
- 成果物影響 — leaf と aggregate だけを差し替えた受領証は拒否され、現物から再導出した proof 参照に一致する leaf だけが受理される。

**5. `AutonomousTrialCompletenessError` は握りつぶされず、cause も保持される**

- 主張 — completeness 違反が変換時に消失し、leaf 不一致を拒否せず処理が継続する。
- 原典 — `orchestrator/campaign/autonomous_trial_completeness.py:443-448`、`orchestrator/campaign/s8c_acceptance_receipt.py:1383-1394`
- 判定 — **refuted**。対象例外は `AcceptanceReceiptError` として必ず再送出され、`raise ... from exc` により cause が保持される。例外後に digest を返す経路はない。
- 深刻度 — **nit**（修正不要）
- 成果物影響 — completeness 違反を持つ trial は受理されず、certified 選択や proof 参照を生成しない。

**6. filesystem race の `OSError` は別例外型のまま漏れうる**

- 主張 — `verify_s8c_cross_binding` が投げる全失敗が `AcceptanceReceiptError` に正規化される。
- 原典 — `orchestrator/campaign/autonomous_trial_completeness.py:4232-4234`、`:4273-4277`、`orchestrator/campaign/s8c_acceptance_receipt.py:1383-1394`、`:2077-2085`、`orchestrator/campaign/layer3_report.py:917-924`
- 判定 — **real**。`run_root.resolve(strict=True)` と `output_root.resolve(strict=True)` は `AutonomousTrialCompletenessError` への変換外にあり、検査中に directory が消えるなどすれば raw `OSError` が helper 外へ漏れる。helper は completeness 固有例外だけを捕捉し、下流も `AcceptanceReceiptError` だけを変換する。ただし例外は握りつぶされず、正常 return には到達しないため、防壁の受理意味は変わらない。
- 深刻度 — **nit**
- 成果物影響 — filesystem race 時の外向き例外型は変わるが、受領証、certified 選択、受理集合、proof 参照はいずれも生成されない。

## 総括

must-fix は **0 件**。裁定の 8 不変条件、新 leaf の発火位置、既存防壁、4 入力の独立性、例外による fail-closed 性に違反はない。

real は raw `OSError` が `AcceptanceReceiptError` に正規化されない nit 1 件だけで、成果物の受理には影響しない。判定不能として残した点はない。pytest は指示どおり実走しておらず、本結論は静的レビューによる。