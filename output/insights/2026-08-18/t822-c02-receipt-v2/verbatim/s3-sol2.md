### 所見 1

- **主張:** receipt v2 の full verifier は実行入力 bytes ではなく自己整合した receipt・report・run-start だけを照合するため、実 arm と無関係な捏造 bundle でも `c02-arm-binding-unproven` を落とせる。

- **根拠:** 計画が追加する検査は binding digest の再計算と report/run-start との等号までである [s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:118)、[s2-plan.md:125](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:125)。現 verifier は receipt のみ HEAD blob と一致させ、report/journal は非 tracked の working bytes でも hash 一致だけで通す [s8c_acceptance_receipt.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_acceptance_receipt.py:596)、[s8c_acceptance_receipt.py:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_acceptance_receipt.py:603)、[s8c_acceptance_receipt.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_acceptance_receipt.py:619)。実入力 descriptor、campaign lock、proposal、invocation、provider payload を読む独立 chain は別に実在する [autonomous_trial_completeness.py:719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/autonomous_trial_completeness.py:719)。静的論証では、任意の相異なる六 digest、正しく再計算した binding digest、同値の report/run-start、対応 hash を持つ tracked receipt を構成すれば計画された検査を通る。

- **成果物影響:** receipt verifier の受理集合が「実行 chain を証明した receipt」から「三つの自己申告が一致する receipt」へ広がり、非認証理由・summary・将来の proof 参照が虚偽になる。

- **GO / NO-GO:** **NO-GO**

### 所見 2

- **主張:** 負の対照 3 種は正例到達性を持つ一方、2 番と 3 番が理由落とし分岐への単一理由性を証明せず、協調偽造を一件も殺さない。

- **根拠:** originless fixture は六 trial を実行して実 producer を呼ぶため正例は到達可能である [test_reflux_originless_compatibility.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_reflux_originless_compatibility.py:38)、[test_reflux_originless_compatibility.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_reflux_originless_compatibility.py:65)。対照 1 の pairwise 診断は帰属可能だが、対照 2 の「binding field」が content digest または binding digest なら parse 時の再計算で先に落ち、`input_schema_version` なら計画に `"8b-v1"` の literal 検査がない [s2-plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:153)。対照 3 は理由の有無に関係なく `_V2_TRIAL_KEYS` で落ちるため、理由 gate を削除する変異を検出しない [s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:159)。三者を同時に改変し、実 descriptor/provider bytes だけを不一致にする対照もない。

- **成果物影響:** mutation matrix が 3/3 KILLED でも実際の理由落とし bypass が残り、receipt の理由集合を誤って安全と記録する。

- **GO / NO-GO:** **NO-GO**

### 所見 3

- **主張:** 実名整備は contract だけでは完結せず、評価器本体と既存正例 fixture の旧名 pin を更新しなければ C09/C10 は将来も実装へ追随しない。

- **根拠:** 計画の C09/C10 編集列挙は contract JSON に限られる [s2-plan.md:20](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:20)。評価器は現在も `functions.get("accept_trial")` を独立 literal として持つ [s8c_preregistration_evidence.py:1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:1490)、[s8c_preregistration_evidence.py:1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:1532)。さらに C09/C10 の token-only 正例も旧関数名を定義しており、M7 が落とした間接 pin である [test_s8c_preregistration_predicates.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_preregistration_predicates.py:439)、[test_s8c_preregistration_predicates.py:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_preregistration_predicates.py:460)。M2 の「現 HEAD の結果は同じ」は正しいが、潜在バグ修正が実効化するとの一般化は成立しない。加えて C03/C08 に同じ誤名が残ることを親自身が後から確認している [parent-measurements.md:102](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/parent-measurements.md:102)。

- **成果物影響:** 現在の C09/C10 値は変わらないが、後続実装後も旧名検索で UNSATISFIED のままとなり、契約と判定レポートが再び乖離する。

- **GO / NO-GO:** **NO-GO**

### 所見 4

- **主張:** `_called_names` と `_strings` を使う C02 評価器は dead branch、return 後、nested function に置かれた token だけでも通り、欠落した consumer を拒否できない。

- **根拠:** 計画は `_called_names` を指定する [s2-plan.md:33](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:33)。同 helper は無条件の `ast.walk` で nested scope と dead code も数える [s8c_preregistration_evidence.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:298)。一方、同 module には nested scope と静的 dead statement を除外する `_live_nodes` が既にある [s8c_preregistration_evidence.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:538)。予定負例は一辺の削除だけで、`if False: resolve_arm_input()` や未呼出 nested 関数への移動を扱わない [s2-plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:76)。

- **成果物影響:** 壊れた C02 が `UNSATISFIED/arm-binding-consumer-unreachable` にならず completion-proof 理由へ進み、判定レポートと台帳が「静的 consumer 実在」を誤記する。

- **GO / NO-GO:** **NO-GO**

### 所見 5

- **主張:** C02 専用 undefined 分岐の削除は evidence blob 不在と構造的 edge 欠落を同じ UNSATISFIED 理由へ潰す計画であり、既存診断を保存していない。

- **根拠:** 現行は registry blob 不在を `EVIDENCE_UNDEFINED/trial-registry-capability-absent`、存在するが証明不能な場合を別理由に分ける [s8c_preregistration_evidence.py:1668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:1668)。計画はこの枝を削除し、「いずれかの関数または edge が欠ける」ときの一理由しか定めず、missing blob の回帰テストも列挙していない [s2-plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:45)、[s2-plan.md:53](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:53)。これは計画文からの推測であり、実装時に明示的な blob 不在分岐を残せば解消する。

- **成果物影響:** 受理集合自体は広がらないが、activation report の status/reason と証拠欠落の帰属が変わり、レポートと凍結改訂理由が誤診断になる。

- **GO / NO-GO:** **NO-GO**

### 所見 6

- **主張:** `SATISFIABLE_CONDITION_IDS = frozenset()` は実行時 allowlist ではなく、評価器が SATISFIED を返せば core はそのまま受理する。

- **根拠:** 定数は宣言されるだけで [s8c_preregistration_evidence.py:1659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:1659)、dispatch 後の result に照合されない [s8c_preregistration_evidence.py:1766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:1766)。core は十二 result の status だけで `all_satisfied` と `effective` を計算する [s8c_preregistration.py:1729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration.py:1729)。計画された C02 終端と candidate の zero-satisfied test は現 wave の直接拡大を止めるが、空定数そのものを防壁として数える説明は誤りである。

- **成果物影響:** C02 または将来評価器の一行退行で predicate 受理集合を広げられ、全条件実装後には preregistration の effective 判定まで変わりうる。

- **GO / NO-GO:** **NO-GO**

### 所見 7

- **主張:** AST メタ検査の旧 `accept_trial` 対照は赤になるが、hop ごとの検査集合を exact pin しないため、一部または大半の名前を黙って skip しても緑になりうる。

- **根拠:** current `trial_registry.py` に `accept_trial` はなく実名だけがあるため、計画の C09 mutation は確かに欠落 tuple を作る [trial_registry.py:2556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/trial_registry.py:2556)、[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:67)。また entrypoint list の空は schema parser が拒否する [s8c_preregistration_evidence.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_preregistration_evidence.py:181)。しかし root 検査は「path が consumer と同一かつ先頭 hop が identifier」の場合だけであり、それ以外を failure にせず skip する [s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:63)。検査済み `(condition,path,name)` 集合の exact 期待も production path 制約もないため、root を非 identifier 化する、別 path へ移す、entrypoint を別 chain の第二 hop にだけ残す変異が生存する。

- **成果物影響:** 「契約が名指す実名を全て検査した」というメタ保証が部分走査でも緑になり、将来の契約名 drift を再び凍結 record へ入れる。

- **GO / NO-GO:** **NO-GO**

### 所見 8

- **主張:** M4 の「追加 field を値ごと消費する」は run-start の `arm_execution` について偽であり、予定 projector もその穴を引き継ぐ。

- **根拠:** 予定 `_project_t822_receipt_v2_to_v1` は receipt と report だけを一致させ、その後 T-1311 projector に report/run-start の削除を委ねる [s2-plan.md:183](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:183)。現 T-1311 projector は report 値を descriptor/proposalへ一部照合するが [test_reflux_originless_compatibility.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_reflux_originless_compatibility.py:596)、run-start 側は key 集合だけを確認して値を捨て、report との等号を要求しない [test_reflux_originless_compatibility.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_reflux_originless_compatibility.py:633)。したがって receipt=report、run-start だけ異なる bundle は射影後に旧 golden と一致しうる。

- **成果物影響:** originless golden が report/run-start 不一致を隠して緑になり、逐語 baseline は不変でも互換性保証の受理集合が広がる。

- **GO / NO-GO:** **NO-GO**

### 所見 9

- **主張:** P2 は receipt-local な arm execution 証明と事前登録 predicate C02 の状態を同じ `C02` 名で表すため、D75 が記録した同名識別子混同型に該当する。

- **根拠:** receipt は `c02-arm-binding-unproven` を落とす一方 [s2-plan.md:123](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:123)、静的 C02 evaluator は引き続き `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable` で終わる [s2-plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s2-plan.md:45)。規範上の条件 2 は arm の各識別子への配線までを指す [phase3-8c-preregistration.md:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/docs/phase3-8c-preregistration.md:181)。D75 自体の裁定対象は freeze 設計だが、同じ `H` を二つの commit 意味に使った失敗を明記している [decisions.md:3033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/docs/decisions.md:3033)。従って同型回避には receipt-local reason 名への改名、または schema/docs 上の claim namespace 分離が必要である。

- **成果物影響:** receipt は「C02 の理由なし」、activation report は「C02 未証明」という二義的な proof chain になり、利用者が condition-level 充足と誤読する。

- **GO / NO-GO:** **NO-GO**

## 総括

**NO-GO。**

must-fix は次の 8 点である。

1. receipt verifier が七 sink の実 bytes を独立再検証し、自己整合した report/journal だけでは理由を落とせないようにする。
2. producer helper の共有を禁止し、固定 known-answer と協調偽造の負例を追加する。
3. 負の対照 2・3 を単一理由化し、理由 gate を削る変異が必ず赤になる形にする。
4. C09/C10 の evaluator literal と既存 fixture を実名化し、C03/C08 の既知誤名を直すか明示裁定する。
5. C02 は live scope の callだけを数え、missing blob の既存 status/reason を保存する。
6. SATISFIABLE 集合を実行時 allowlist にするか、防壁ではないことを明記して SATISFIED 変異を殺す。
7. メタ検査の検査済み tuple と production path を exact pin し、silent skip を拒否する。
8. golden 射影で receipt/report/run-start の三者一致を確認し、receipt-local claim と predicate C02 を別名で表す。

本レビューは read-only の静的検査であり、pytest・受入検査は実走していない。