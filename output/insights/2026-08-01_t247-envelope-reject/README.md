# 2026-08-01 [T-247] 予約 envelope の恒真な検査を実発火させ、個別 cap を個別値 + 型で凍結する

dev-wave の逐語一式。設計判断の正本は `docs/decisions.md` の D112、状態の正本は `docs/worklog.md` の
末尾エントリ。ここは**その場で生成された逐語**の凍結であり、正本を再掲しない。

## 中身

| file | 段 | 内容 |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。**DW-G05 の因果記述は誤りで、`s4` の D 節が差し替えている** (下記) |
| `s2-plan.md` | 2 | codex プラン起草 (read-only, reasoning=max) |
| `s3-lens-a.md` | 3 | 敵対相談 A (受理集合・正しさ防壁)。NO-GO |
| `s3-lens-b.md` | 3 | 敵対相談 B (bash 実行意味論・偽緑)。NO-GO |
| `s4-adjudication-plan-v2.md` | 4 | 親の裁定 + プラン v2 + 変異事前登録 |
| `s5-impl.md` | 5 | 実装子の完了報告 |
| `s6-review-a.md` | 6 | 敵対レビュー A。NO-GO (blocker 1 / must-fix 2) |
| `s6-review-b.md` | 6 | 敵対レビュー B。NO-GO (must-fix 2) |
| `s6-fix.md` | 6 | fix 1 巡目の報告 |
| `s6-rereview.md` | 6 | 焦点再レビュー (closed/partial/regressed 表)。NO-GO (must-fix 1) |
| `s6-fix2.md` | 6 | fix 2 巡目の報告。production 差分は不変 |
| `s6-harness2.md` | 6 | 変異 harness の実装報告 |
| `s6-harnessfix.md` | 6 | harness の node 抽出バグ修正の報告 |
| `evidence/mutation-ledger.jsonl` | 6 | 変異本走の raw 台帳 35 行 |
| `evidence/mutation-harness.py` | 6 | 本走に使った harness (repo 外で実行、repo には残さない) |

## 段 1 brief の誤りと訂正 (erratum)

`s1-brief.md` の「成果物影響 (DW-G05)」は
「予約 policy の wmax が小さいと member が途中で kill され finalize reserve が消え、attempt ledger に
試行欠落が入る」と書いているが、**これは誤りである**。実測で確認したとおり、job の deadline は
`tools/pegasus/t126_qualification.sh` の `WMAX_FIXED_S=29100` という hardcode から作られ、予約 policy の
`wmax_s` は qstat の下限比較にしか使われない。予約 policy の cap で job の実行時間予算に直接効くのは
prologue cap だけである。実消費される member / attestation / finalize の cap は制御 protocol
(`orchestrator/qualification/t126_control_v1.json` の `timing`) 側にある。

訂正後の成果物影響は `s4-adjudication-plan-v2.md` の D 節が正本であり、D112 にも反映してある。
`s1-brief.md` 自身は当時の記録として原文のまま凍結し、書き換えない。

## 親が実測した主要な事実

すべてログインノード上で、script から verbatim 抽出した fragment の実行、または production 関数の
直接呼出しで確認した。

| 事実 | 修正前 | 修正後 |
|---|---|---|
| submit に `prologue/attestation/finalize = 1500/0/600` (和 29100) | rc=0 で通過 | rc=2 `T-126 reservation policy mismatch` |
| job に `prologue=1500` | rc=0 で通過 (診断は stderr へ出る) | rc=2 `qualification envelope mismatch` |
| job に `walltime=1 / wmax=2 / prologue=3` | rc=0 で通過し全値が下流へ | rc=2 |
| `validate_protocol` に `attestation=1199, finalize=1` | ACCEPT | REJECT |
| submit に NUL 入り walltime (`10:00:` + NUL + `00`) | (HEAD は拒否) | rc=2。command substitution 化による退行を Python 内比較で打ち消した |
| 両側に `attestation_cap_s=600.0` | 通過 | rc=2 `type mismatch` |
| canonical policy | 受理 | 受理 (mapping = walltime 36000 / wmax 29100 / prologue 900) |
