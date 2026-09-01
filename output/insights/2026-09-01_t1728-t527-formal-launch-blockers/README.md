# 正式 holdout 起動を塞いでいる層を、どこで止まるかで確定した

- 日付: 2026-09-01
- wave: `worktree-dev-wave-t1728-t527-projection` ([T-1728] / [T-527])
- 測った checkout: 統合 commit `4695e120464c12ed0420809563acf470c2866785`
- 位置づけ: 依頼は「binding / report / 受入層の関門が production で発火することを実データで
  1 回示す」ことだった。**発火は示せなかった。** 代わりに、各層がどこで止まるかを実測して
  確定した。これが本 wave の実証成果である。

## 何を測ったか

正式 (認証) な H1 / H2 起動が production で通るまでに、いくつの独立した関門があるかを、
現物のコードと実行で 1 つずつ確かめた。

## 結果 — 独立した関門は 3 つあり、依頼が名指ししたのは 1 つ目だけだった

| # | 関門 | 実体 | 本 wave の扱い |
|---|---|---|---|
| 1 | 正式 profile の無条件拒否 | `p3_autonomous_workload_trial._preflight_workload_profile` が selector を見た時点で常に例外 | **直した。** 二段束縛を実際に問う条件付き fail-closed へ置き換えた |
| 2 | activation 評価器の allowlist | `s8c_preregistration_evidence.SATISFIABLE_CONDITION_IDS` が `{"C10"}` で、C10 以外が `SATISFIED` を返すと `ERROR` へ書き換える | **触っていない。** 受理集合を実際に広げるため裁定へ返す |
| 3 | C05 schedule 正本の不在 | `_load_s8c_schedule_authority` が引数を捨てて必ず例外を送出する | **触っていない。** 同上 |

さらに、関門とは別に **token の発行側に production の呼び手が無い**。

## 実測値

現 HEAD で 12 述語を評価した結果は次のとおり。

- `C10` = SATISFIED (`cross-binding-readiness-satisfied`)
- `C03` = UNSATISFIED (`manifest-registry-proof-undefined`)
- 残り 10 件 = EVIDENCE_UNDEFINED (`C05` は `schedule-schema-absent`、`C08` は
  `prereg-binding-proof-undefined`、他 8 件は `completion-proof-not-machine-checkable`)

`activation_report_at` の他の field は `freeze_reason_code=valid`、
`condition_freeze_valid=True`、`decider_version_matches=True`、`freeze_generation=13`、
`section5_findings=9` であり、**freeze も decider も健全で、止めているのは述語だけ**である。

## 重要な区別 — 「今の状態」ではなく「今の構造」による恒偽

関門 2 は repository の内容が変われば通る類のものではない。評価器は C10 以外の条件が
`SATISFIED` を返した場合、その結果を `ERROR` / `EVALUATOR_INTERNAL_ERROR` へ**書き換える**。
したがって 12 条件の全充足は構造的に成立しえず、`s8c_preregistration.effective_at` は
production では常に `None` を返す。

この区別は記録上重要である。「今は述語が足りない」と書くと、証拠を積めばいずれ通るように
読めるが、実際には allowlist を広げる裁定なしには決して通らない。

## この結果が意味すること

- 関門 1 を直したことで「拒否が導出されるようになった」が、「通る道ができた」とは書けない。
  正例の枝は production では到達不能である。本 wave の記録はこの限定形で書いた。
- 逆に、関門 1 を直さなければ関門 2 / 3 を外しても何も起きない。順序としては 1 が先で正しい。
- `registered-formal-non-certifying` (非認証) の経路は 12 述語を見ないため、rr80 / rr20 は
  今でも受理され binding / report / 受入層は動く。ただし測定層の holdout gate は
  発行側の呼び手が無いため動かない。**「関門が動くか」は認証・非認証で答えが違う。**

## 副産物 — 既存文書の 1 箇所が stale

`docs/phase3-s8c-autonomous-trial-runbook.md` は「現 repository は 12 述語の SATISFIED が
0 件」と書いているが、実測では 1 件 (C10) である。同文書の結論
(「正式 H1/H2 起動が通ることを期待してはならない」) は変わらないため、本 wave では
本文を書き換えず、この差分を記録に残すだけにした。

## 再現手順

repository root で次を実行する。

```
python3 -c "from pathlib import Path
from orchestrator.campaign import s8c_preregistration as sp
r = sp.activation_report_at(Path('.'), 'HEAD')
print(r.effective)
for p in r.predicates: print(p.id, p.status, p.reason_code)"
```
