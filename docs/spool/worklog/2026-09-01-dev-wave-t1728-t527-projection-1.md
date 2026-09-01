---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1728-t527-projection
seq: 1
title: [T-1728][T-527] 正式 holdout 起動の無条件拒否を二段束縛の条件付き検査へ変え token を campaign loop へ結線した — 「production で関門が発火する」ことは示せず、塞いでいる別の 2 つを特定した (コード + テスト、branch worktree-dev-wave-t1728-t527-projection)
---

## 本文

- 2026-08-25 ユーザー裁定 ([T-1728] と [T-527] を束ねて 1 wave) と D1265 に対する実装 wave である。
  依頼は 3 点だった。(1) `_preflight_workload_profile` の無条件拒否を直す、(2) `loop.py` へ
  admission token を結線する、(3) binding / report / 受入層の関門が production で発火することを
  実データで 1 回示す。**(1) と (2) は着地した。(3) は達成できないと確定した。**

- **依頼の前提を 2 件、着手前の実測で覆した。** [T-527] の carry 本文は「rr80 / rr20 の実
  projection が `WORKLOADS` に無い」と書いているが、これは 2026-08-05 時点の記述であり、
  D559 (2026-08-19) が `FORMAL_WORKLOADS` を freeze 由来 derived として新設した時点で解消していた。
  completeness consumer も `autonomous_trial_completeness.py` の 2 箇所が
  `resolve_workload_entry` を通っており着地済みだった。**残っていたのは campaign consumer
  だけである** — `run_trial` の受理 workload 集合は非認証モードのときだけ `FORMAL_WORKLOADS`
  を足し、認証を伴う `registered-effective` では足していなかった。これは D558 が
  「run_trial のこの gate は直さず前提条件 8 へ残す」と明記して先送りした当のものである。
  既存 fixture が rr80 / rr20 を `WORKLOADS` へ monkeypatch して迂回していたため、
  テストからは見えていなかった。

- **(3) が達成できない理由を現物で確定した。** 正式 (認証) 経路には、依頼が名指しした無条件拒否の
  ほかに独立した意図的 fail-closed が 2 つある。第一に
  `s8c_preregistration_evidence.SATISFIABLE_CONDITION_IDS` は `{"C10"}` であり、評価器は
  C10 以外が `SATISFIED` を返すとそれを `ERROR` へ書き換える。したがって 12 条件の全充足は
  **構造的に成立しえず**、`effective_at` は production では常に `None` である。これは
  「今の repository の状態」ではなく「今の評価器の構造」による恒偽である。第二に
  `_load_s8c_schedule_authority` は引数を捨てて必ず例外を送出するため、`registered-effective`
  かつ build ありの経路は Layer-3 report へ到達しない。親が実測した 12 述語は
  C10=SATISFIED、C03=UNSATISFIED、残り 10 件=EVIDENCE_UNDEFINED であり、C05 の
  `schedule-schema-absent` は第二の理由と一致する。**どちらも activation 契約と C05 正本に属し、
  外すと受理集合が実際に広がるため本 wave では触っていない。** 詳細は
  {{T:activation-satisfiable-allowlist}} と {{T:c05-schedule-authority}} へ送る。
  なお `docs/phase3-s8c-autonomous-trial-runbook.md` の「12 述語の SATISFIED が 0 件」は
  現時点では stale で、正しくは 1 件 (C10) である。結論そのものは変わらない。

- **段 3 の敵対検査が親の当初 brief を 3 点で覆した。** (a) 親は「C08 が未定義だから正式起動は
  拒否される」と書いたが、これが正しいのは `registered-effective` の preflight に限る。
  非認証モードは 12 述語を見ずに rr80 / rr20 を受理する。(b) 親は「T-527 の残余は loop 結線と
  同一」と書いたが誤りで、上記の campaign consumer が別に残っていた。(c) 親は token の出所を
  `CampaignConfig` 経由と書いたが、token は attempt 束縛・消費回数付きの runtime capability で
  あり、config へ入れると canonical preimage と serialization 契約を汚す。keyword-only の
  runtime seam へ改めた。いずれも段 4 で撤回・訂正した。

- **結線には「発行側の呼び手が無い」という残余がある。** 正規 token を発行する経路
  (oracle / n-pilot / floor の durable ticket 消費) はいずれも `run_campaign` を経由せず
  `pipeline.evaluate` や calibrator を直接呼ぶ。8c 自律 trial の経路には token を与える
  production の呼び手が今も無い。発行 adapter の新設は `holdout_observation.py` が宣言する
  「campaign ledger の durable consumption なしに発行しない」境界を変えるため、本 wave では
  作らず {{T:holdout-token-issuer-for-8c}} へ送る。依頼が「結線する」と明示しているので
  鎖は最後まで通した。

- 段 6 のレビュー 2 本と親の実走が 4 件を出し、すべて fix で閉じた。(a) 条件付き関門が
  非認証モードにも接続されていた (裁定より広い受理)。(b) **事前登録した変異の負例が他層に
  mask されていた** — balanced と token の同時指定を拒否する検査を削っても、直後の
  「balanced は 2 arm 必須」が同じ入力を拒否するため、落ちる理由が「受理された」ではなく
  「例外の文言が変わった」になっていた。実発行 rr80 admission と妥当な 2 arm 入力へ組み直した。
  (c) allowance 枯渇が balanced 以外にも及ぶ。静的に判る複数 genome だけ閉じ、
  `bench_max_rounds` の再測定は guard しなかった (実行時条件であり、下流の allowance 検査が
  既に fail-closed で止めるため)。(d) **新設テストが呼出し回数を 2 と決め打ちしていた** —
  親が実走したところ実際は 4 だった。推測した定数を期待値にせず、
  「1 回以上あり全呼出しの trial_id が一致する」という性質へ置き換えた。子は sandbox で
  pytest を走らせられないため、この種の誤りは親の実走でしか出ない。

- **非帰属赤を 1 件着地させた。** `test_campaign.py` が走行ごとに 3 件 → 1 件と異なる件数で赤に
  なり、原因はすべて `official output_root は repository 外でなければならない` だった。
  3 件を単独再走すると緑で再現しない。本 wave は `layout.py` を触っておらず失敗地点も差分の
  外である。祖先判定が `/tmp` を lstat するため、並行稼働している他 wave と `/tmp` を
  共有していることによる外乱と判定した。fix 後の再走でも再現しなかった。

- **変異 matrix は計算ノードの混雑で走らせられなかった。** 変異機構は login node での
  local 実行を機構側が拒否するため dispatch 一択だが、`qstat` は実行中 1 件 (経過 2.3 時間) と
  待機 7 件がすべて並行 wave のもので埋まっており、baseline の投入が queue 待ちで timeout して
  pytest が 1 度も起動しなかった (収集 0 件)。9 件の変異 spec は逐語 anchor の一意性を
  機械検査済み (9/9) で job dir に保全してあり、queue が空いた時点でそのまま走らせられる。
  **テストが落ちたのではなく走れなかった**という失敗である。

- 実装子は pytest を 1 度も走らせていない (sandbox から dispatch できず rc=16)。緑の主張は
  すべて親の実走による。工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1)。
  すべて `gpt-5.6-sol` / `xhigh`。

## 次の一手差分

### 完了

- [T-527] projection と completeness consumer は D559 の時点で着地済みだったと実測で確認し、
  残っていた campaign consumer (`run_trial` の受理 workload 集合が `registered-effective` で
  `FORMAL_WORKLOADS` を足さない) を閉じた。
  remaining: none
  base: 367f59c65fe2dc3c88605a0bab391a170d58c1b686d731e1357fabf037a1390b

### 更新

- [T-1728] **P2・実装済み (無条件拒否と結線)、残余は裁定待ち**: 無条件拒否は二段束縛の
  条件付き検査へ置き換え、token は `p3_s4_loop_trigger_gating` から `run_campaign` を経て
  `pipeline.evaluate` まで結線した。**「関門が production で発火することを実データで示す」は
  達成できないと確定した** — activation 評価器の allowlist と C05 schedule 正本が独立に塞いで
  いる。残りは {{T:activation-satisfiable-allowlist}}、{{T:c05-schedule-authority}}、
  {{T:holdout-token-issuer-for-8c}} の 3 件に分けた。
  base: 2142ed72c24611b7bf8ddfe7c9351293dc7c32274b791701d9b396b610dc1d26

### 新規

- {{T:activation-satisfiable-allowlist}} **P2・新規・裁定待ち**: activation 評価器の
  `SATISFIABLE_CONDITION_IDS` が `{"C10"}` に固定されているため、`effective_at` は production で
  構造的に常に `None` になる。正式 H1/H2 を将来通すには、この allowlist をどう広げるか
  (条件ごとの機械検査を実装するのか、別の発効経路を作るのか) の裁定が要る。
  受理集合を実際に広げるため、実装ではなく裁定パッケージとして返す。
- {{T:c05-schedule-authority}} **P2・新規・裁定待ち**: `_load_s8c_schedule_authority` が
  引数を捨てて必ず例外を送出するため、`registered-effective` かつ build ありの経路は
  Layer-3 report へ到達しない。C05 の schedule 正本を新設するかどうかの裁定が要る。
- {{T:holdout-token-issuer-for-8c}} **P3・新規・裁定待ち**: 8c 自律 trial の driver には
  正規 holdout token を与える production の呼び手が無い。`AttemptSlotCapability` から
  token を発行する adapter を作るかどうかは `holdout_observation.py` の発行境界を変えるため
  裁定が要る。
- {{T:t1728-mutation-matrix}} **P3・新規**: 本 wave の変異 matrix (9 件) を計算ノードが
  空いた時点で走らせる。spec と逐語 anchor 検査済みの資材は job dir に保全してある。
