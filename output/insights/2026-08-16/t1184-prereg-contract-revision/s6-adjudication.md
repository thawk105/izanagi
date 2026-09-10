# 段 6 レビュー裁定 — [T-1184]

親 / 2026-08-16 14:30 JST / 入力: レンズ A (規律 2/3)、レンズ B (凍結手続・consumer)

両レンズとも **NO-GO**。所見を real/refuted・採否・scope 内外へ裁定する。

## 採用 (本 wave で直す)

### A1a — 契約 C11 の `generation_supervisor.field_paths` が実在しない識別子を要求している (must-fix)

**real・採用・scope 内。親が実測で裏取りした。**

`grep -c` で `orchestrator/campaign/p3_autonomous_workload_trial.py` を数えた結果:

| 契約が書く field path | 実在数 |
|---|---|
| `MAX_APPROVED_GENERATIONS` | 3 (実在) |
| `main.generation_cap` | **0** |
| `run_trial.generation_cap` | **0** |
| `_run_workload.generation_cap` | **0** |
| `_run_workload.critic_feedback_consumer` | **0** |

実在するのは `main` の `args.max_generations` (`_validate_generation_budget(args.max_generations)`)、
`run_trial` と `_run_workload` の keyword 引数 `generations`、および `_run_workload` から呼ばれる
`apply_critic_feedback` である。

これは本 wave が持ち込んだ欠陥ではなく**改訂前から契約にあった**。しかし本 wave は
この契約を第 3 世代として凍結するため、**嘘の証拠要求をそのまま凍結することになる**。
D438 決定 (2) は条件 11 の証拠を「実装機構へ差し替える」ことを定めており、
実在しない識別子を残すのはその趣旨に反する。直す。

**成果物影響:** 直さないと、条件 11 の材料レポートと試行台帳が「どの実体を証拠として要求したか」を
偽って参照する。凍結後は世代を上げない限り訂正できない。

### A2 — 規範本文が「証拠が欠ければ条件別の不充足を返す」と過剰に一般化していた (should-fix)

**real・採用・scope 内。親自身の doc の誤りである。**
証拠 blob が存在しない場合、C01/C04/C11/C12 は `UNSATISFIED` ではなく
`EVIDENCE_UNDEFINED / workload-supervisor-absent` を返す。親の M2 は現 HEAD 1 点の snapshot で
あり、一般則へ広げてはならない。**親が doc を修正済み (14:29)。**

### A5 — C08 の exact-parent 規則が prose だけで、境界テストが pin していない (should-fix)

**real・採用・scope 内。** 現行の境界テストは field 集合しか検査しないため、
`consumer_requirement.proof` を exact parent set `{P}` から単なる ancestry 検査へ弱めても通る。
祖先代用の禁止は D438 決定 (4) の中核であり、pin が無ければ次の改訂で黙って失われる。

**成果物影響:** consumer 配線後に、祖先 commit を発効 commit の代用として受理し、
manifest と measurement の proof chain を広げうる。

### B1 — runbook が承認上限 1 を現行仕様として記していた (must-fix)

**real・採用・scope 内。親が実測で裏取りした。** 実装は `MAX_APPROVED_GENERATIONS = 2`、
D410 本文は逐語で「D114 の承認上限 1 を 2 へ上げる」と定め、第二層射影も実装済みである。
runbook は 2 箇所で「上限 1」「2 世代で走らせない」「機構は未実装」を現在形で記していた。
運用正本が凍結契約と正反対であり、これに従うと `G=1` の系列が作られる。
**親が修正済み (14:32)。歴史記述は遡及改変せず、失効を明記する形にした。**

### 実測で見つかった pin 閉包の取り残し 3 件

`test_evidence_contract_hash_accepts_non_path_controls[cr|nul|lf]` が、生きた証拠契約の bytes を
改変して hash する形で literal を持っていた。段 5 実装子と両レンズが見落とし、
**計算ノードでの実走だけが検出した。** brief の M6 (「live pin は 2 箇所」) は誤りだった。

## 不採用・scope 外 (裁定パッケージ / 起票へ回す)

### A1b — 評価器が validator の実引数と consumer edge を検査していない

**real だが refuted (must-fix としては不成立)・scope 外。**
レンズは「`_validate_generation_budget(2)` と定数化しても検出されない」ことを正しく指摘したが、
**その検出を評価器に持たせる案は D96 が名指しで却下済み**である — 「consumer 閉集合の AST 固定は
構文形状しか固定できない (`if False`・alias・`getattr`・例外握り潰しを見逃す一方、
無害な refactor で偽赤になる)」。前 wave の段 4 も同じ理由で P2 を撤回している。
6 評価器の終端が `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままであるのは、
まさに「この証明は機械検査できない」ことを正直に表明しているからである。
契約の `static_only_note` も何を検査するかを限定して書いている。
**深い AST 検査を足すことは、却下済みの決定を再び開くことになる。行わない。**

### A3 — 評価器不在の条件を `true` にすると `commit-blob-read-error` に潰れる

**real・scope 外。** 前 wave の段 4 裁定 §7 が「nit 裁定 (起票のみ、本 wave では直さない)」と
確定済みであり、本 wave で新事実は出ていない。受理集合は変わらず (どちらも `ERROR`)、
診断のみの問題である。新設した境界テストは**現に起きる挙動を正直に固定**しており、
誤った期待値ではない。起票する。

### A4 — reason code が複数 sub-check を畳んでいる

**real・scope 外 (nit)。** レンズ自身が「現在の各 fixture は単一箇所だけを壊しており
過剰決定は見つからなかったため、受理集合への影響はない」と書いている。
`DW-G05` により、成果物影響を書けない所見は must-fix にしない。起票する。

### B2 — `docs/phase3-8c-wiring-design.md` と `docs/phase3.md` も上限 1 のまま

**real・scope 外。** レンズ B 自身が「scope 外・裁定パッケージ候補」と判定している。
`docs/phase3.md` は現行 phase doc であり、編集は独自の更新契約に従う。起票する。
なお同レンズは `phase3-8c-wiring-design.md` の `TrialBinding.prereg_commit` について
「現行実装を説明しており据え置き裁定は妥当」と親の判断を支持した。

## 変異事前登録の更新 (DW-M01)

A1a の修正により、変異 V4 の照準を変える。射影 blob 検査だけでなく、
**契約 field path が実在識別子であることを固定する境界テスト**も撃つ。
また pin 取り残しが実走でしか出なかったため、変異は必ず計算ノードで走らせる。
