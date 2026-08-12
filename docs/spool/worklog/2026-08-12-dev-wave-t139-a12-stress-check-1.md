---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t139-a12-stress-check
seq: 1
title: a12 事前 simulation を実装して完走させ、pilot 前提 #3 を充足へ動かした — 全 60 セル pass、名目の 15.6% (コード + docs、受入 9838 passed / 65 skipped / rc=0 / 112.79 秒、変異 12/12 KILLED、branch worktree-dev-wave-t139-a12-stress-check)
---

## 本文

第 3 束裁定 (authority: user、2026-08-12) の R1 (a) に従い、追補 A `a12` の
`stress_check_simulation` を独立 wave で実装し完走させた。scope は実装と完走までで、
投入経路 (Q4 scope) には触れていない。

**結果は `pass`。** 全 60 セル (J=4..13 × W1/W2 × N/H/G)、B=1,000,000、
Clopper-Pearson 上界の最大は `J=12 W2:G` の `U = 0.003900439` で、名目 `α₁ = 0.025` の
**15.6%** だった。計算ノード `bnode013` で 48 worker / 5.32 秒。transcript は
`output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json`。

**pilot 前提 #3 が未充足から充足へ動いた。** ただし残り 7 件 (#1 認可解除の canonical fold、
#4 受領証 schema の digest 固定、#5 approval manifest、#6 resolver と receipt writer、
#7 `submit_pilot`、#8 driver と collector、#9 slot identity の発火点) は未充足のままであり、
**pilot は依然として投入できない。** `a12` 完走は core §7 の較正義務を満たさない
(追補 A の逐語がそう定め、第 2 erratum は未承認)。主張できるのは「事前固定した empirical
stress model のもとで名目水準を超えないことの確認」だけである。

**仕様が一意に決めていない自由度を段 4 で凍結した** — PRNG の byte grammar (棄却は byte 255 のみ、
counter 0 始まりの uint64 big endian、cell key ごと独立 stream、chunk 境界で未消費 raw byte を
持ち越す、抽選順は dataset → cluster → block position)、empirical support は workload ごとの 5 点、
`D_g ≡ D = mode1`。**このうち 2 件は結論を左右しないことを実測した** — 棄却規則を
`>= 250` に変えても、support を 10 点に pool しても、判定は `pass` のまま
(最悪 false-pass 率 0.00377 対 0.00432、いずれも α₁ の 6 分の 1 以下)。

**独立実装との一致を 4 段で確認した。** 親が repo 外に別ソースで書いた oracle と、
(1) `q(J, α₁)` の 10 値が厳密一致、(2) `U(x=0, B=1e6) = 1.1002039318325741e-05` が段 3 敵対レンズの
独立算出値と一致、(3) PRNG stream が 4 セルの先頭 5,000 抽選と分割取得で完全一致、
(4) **正本の本走と親 oracle の false-pass 件数が全 60 セルで一致**。

**敵対レビューが事前登録した変異の生存を静的に見抜いた。** レビュー A は、テストが helper を
直接呼んでおり production 呼び出し側の変異 (`ddof=0`・dataset 再中心化・PD filter・棄却規則) を
迂回すると指摘し、V8 と V10 が生存すると判定した。fix 後に親が実測して 12 件すべて KILLED、
生存ゼロを確認した。レビューが提示した golden hash は親が独立実装で再現して採用した
(実装の現在値を焼き込む循環を避けた)。

**ゼロ分散は実際に起きる。** J=4 で全 cluster が同値になる確率は `2.031409e-06`、うち正平均は
`9.056693e-07` で、B=1e6 あたり期待 0.89〜1.14 件。PD filter を掛けず false-pass として数える
設計を段 4 で明示固定した。

**段 4 で親が書いた login fallback は成立しなかった** — `hooks/guard_bash.py` が未登録 Pegasus
実行体を拒否するため、本走の経路は `qsub` の 1 本だけである。admission registry への登録は
本 wave の scope 外とした。

**受入全走は 2 回。** 1 回目は `3 failed / 14 errors`。うち本 wave 起因は 2 件だけで
(`tools/pegasus/` 追加分の admission registry 未登録、新テストの自走 harness 不足)、
**残る 15 件は ccbench submodule の HEAD が `pin.CURRENT_PIN` と不一致**という環境要因だった。
受入中の main 取り込み (50 commit) で superproject が進んだのに submodule を更新していなかった
ためで、`git submodule update --init --recursive` で解消した。2 回目は
**9,838 passed / 65 skipped / rc=0 / 112.79 秒**。

**3 回目の受入 (記録 commit 込みの最終 tip) で `test_codex_worker_launch.py` の 1 件が赤になったが、
負荷起因のフレークである。** 単独再走を 2 回追加して計 3 回走らせたところ、**毎回別のテストが
落ちた** (`test_codex_argv_has_exact_trust_bypass_without_sandbox_bypass` →
`test_limit_stop_is_never_accepted` → `test_all_v3_stages_reject_prior_invalid_attempt[consult-sol]`)。
本 wave の差分 12 ファイルに同 test も `tools/codex_worker_launch.py` 本体も含まれず、
2 回目の受入では同ファイルを含めて全件緑だった。実行時は並行 wave の codex 子が 9〜10 本
走っており、落ちた test はいずれも子 process の起動と終了検証を実測する種類のものである
(`termination_verified=False`、子の `wall_clock_s=0.16`)。

registry 登録には 2 つの同期先が芋づるで付く — `docs/pegasus-runbook.md` §7.0 の投影表
(`check_docs.py` が集合完全一致を検査) と `test_hooks.py` の literal golden。後者は
「テストの期待値を変更するな」に触れるため fix 子が正しく escalate し、親が
「registry を逐語 pin する golden の同期であって弱体化ではない」と裁定して別 commit で行った。

工数の異常: 段 2 の codex 子が 1,332 秒 / 12 model call を空費して全損した ({{F:codex-nfc-evidence-loss}})。
PBS script の規約違反 4 点は静的レビュー 4 本を通り抜け、親が実際に `qsub` して初めて判明した
({{F:pbs-directive-violations-need-submission}})。

## 次の一手差分

### 更新

- [T-139] **P1**: `a12` は完走し前提 #3 は充足。**pilot は依然投入不可** — 残る 7 件
  (#1・#4〜#9) はすべて Q1 / Q2 の下流であり、その 2 問が未裁定のまま。次は Q1 / Q2 の裁定を
  取り、投入経路 session を Q4 scope で組む。
  base: 660cac9f80a3ce9f9db9f0a0f1fc1536519353b99a2d3f71707997ab7c5fb214

### 新規

- {{T:a12-grammar-promotion}} **P3・新規**: `a12` の PRNG byte grammar と golden vector を、
  wave 側の記録から事前登録 core または追補へ昇格するかを裁定する。現状は段 4 裁定と
  transcript が正本であり、事前登録文書は grammar を持たない。
- {{T:a12-runner-admission-registration}} **P3・新規**: `tools/pegasus/run_t139_a12_stress_check.py`
  を `tools/pegasus/admission_registry.json` へ登録するかを裁定する。未登録のため login 実行が
  hook に拒否され、queue 停止時の fallback が無い。
