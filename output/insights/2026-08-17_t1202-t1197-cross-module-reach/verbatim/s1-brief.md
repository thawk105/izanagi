# 段 1 brief — [T-1202] / [T-1197] cross-module 到達判定

wave: dev-wave-t1202-t1197-cross-module-reach / branch: worktree-dev-wave-t1202-t1197-cross-module-reach
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach
作成: 2026-08-17 00:55 JST / base main: 5a19b8ab3280f3ba607a2856c4b6402b3c869f3f

## 確定済みユーザー裁定
2026-08-16 /rulings 全件 第 3 回 択 (ii): **環境契約 条件 12 は評価器の到達判定を cross-module へ
広げる。** 誤報の原因は判定器の射程不足であって条件側ではない。条件を機械検査から戻す (i) も
allocation 節を外す (iii) も採らない。同じ helper を 6 条件の評価器が共有しているので C12 固有の
問題ではない ([T-1197])。到達判定を広げたうえで、**(A) 実在する強制が「不在」と報告されないこと**、
**(B) 実際に不在なものは依然 UNSATISFIED になること** の両方をテストで示す。(B) が抜けると
受理集合が黙って広がる (規律 2)。

## 段 1 前の実測 — 裁定前提を覆す新事実 (段 4 で再裁定対象)
1. `machine_checkable` は C01/C04/C09/C10/C11/C12 で既に **true**。D441 決定 (3) の
   「12 条件すべて false・実 tree で一度も走っていない」は覆っている (D438 / g3 で反転済み)。
2. 実 tree main 5a19b8ab の評価結果 (実行値):
   C01=UNSATISFIED/workload-projection-mismatch、C02..C03=EVIDENCE_UNDEFINED、
   C04=UNSATISFIED/crash-policy-cell-partial、C05..C08=EVIDENCE_UNDEFINED、
   C09=UNSATISFIED/formal-acceptance-layer3-consumer-absent、
   C10=UNSATISFIED/cross-binding-verifier-incomplete、
   C11=EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable、
   **C12=UNSATISFIED/environment-contract-consumer-absent**。
   D441 決定 (4) が「反転すれば出る」と予告した誤報は、**現に出ている**。仮定ではない。
3. C12 の失敗点は第 1 gate ちょうど。`lookup` は env_contract.py に、
   `attest_and_build_receipt` は execution_guard.py に**実在する** (実測: 定義あり)。
   落ちているのは `{"lookup","attest_and_build_receipt"} <= calls` だけで、
   `calls` = `_reachable_calls(workload_supervisor, "run_trial")` は module-local。
4. `single_process_required` は reservation.py に**存在しない** (実在は `check_reservation`,
   `is_reservation_required`, `read_binding` 等)。→ 到達判定を広げても C12 は第 2 gate で
   `allocation-enforcement-consumer-absent` の**真の** UNSATISFIED になる見込み。
   これが (B) の実 tree 側の natural negative control になる。
5. D458 決定 (1): core/evaluator/projection のいずれかで受理集合・拒否理由・射影の意味を変える
   変更は bytes 差の有無に関わらず `DECIDER_VERSION` を bump する。本 wave は C12 の拒否理由を
   変えるので **bump 必須** (`s8c-decider/v1` → `s8c-decider/v2`)。
6. 凍結記録 tip は g3、`schema_version = s8c-prereg-condition-freeze/v1` (legacy、`decider_version`
   key なし)。D458 決定 (3) により**現在すでに `decider-version-unbound` で発効不能**。
   → bump で失われる現用保証はゼロ。ただし `orchestrator/tests/test_s8c_preregistration_core.py`
   の 1535 / 2014 / 2094 行付近が literal `"s8c-decider/v2"` を**不一致 fixture**として使う。
   bump するとこれらが一致側へ回り赤になる。実装子はここを必ず読む。

## scope (と、実装しない場合の成果物影響 — DW-G05)
- **S1: 到達判定の cross-module 化。** `_reachable_functions` / `_reachable_calls` を、
  実際の import 束縛を辿って repo 内 module へ広げる。
  未実装なら: 8c 事前登録の C12 は永久に UNSATISFIED のままで、certified 選択の
  受理条件表に「実在する強制が不在」という**偽の診断**が載り続ける。台帳の reason_code が嘘になる。
- **S2: (A) の positive 証拠。** cross-module に実在する consumer が「不在」と報告されないことを
  テストで示す (合成 fixture + 実 tree の C12 第 1 gate 通過)。
  未実装なら: 広げたことの効果が無検査で、次の改修が黙って戻せる。
- **S3: (B) の negative 証拠。** 実際に不在なものが依然 UNSATISFIED になることを示す。
  最低 2 種: (b1) どの module にも定義が無い、(b2) 定義はあるが **import 束縛が無い別 module**
  にあるだけ (同名衝突)。後者が本 wave の受理集合拡大の主リスク。
  未実装なら: 受理集合が黙って広がり、規律 2 違反の「述語を満たすための細工」を通す。
- **S4: `DECIDER_VERSION` bump と巻き添えテストの是正。** D458 決定 (1) の義務。
  未実装なら: 版が意味を代表しなくなり、発効判定が旧版の受理意味で緑を出しうる。
- **S5: 実 tree golden 表の更新。** `test_s8c_preregistration_predicates.py:118-133` の
  gap ledger を実測値へ更新する (docstring が「他 wave の land 時は意図を再審査して更新する」と
  規定済み)。未実装なら受入が赤。

## 不変条件 (破ったら失格)
- **証拠契約 JSON (`s8c_preregistration_evidence_contract.v1.json`) を編集しない。** 裁定は
  「評価器を広げる」。JSON を触ると `evidence_contract_sha256` pin が動き凍結世代 g4 が要る。
- **`docs/phase3-8c-preregistration.md` を編集しない** (`protected_sha256` /
  `normative_body_sha256` / `section6_*` の pin 対象)。
- 述語を**通すために**名前を作らない・委譲 wrapper を新設しない (D441 却下済み)。
  reservation.py に `single_process_required` を生やす改修は本 wave の scope 外・禁止。
- 到達判定は**実際の import 束縛**に基づく。同名だからという理由で別 module の定義を到達と数えない。
- traversal は repo 内に閉じ、visited 集合と上限を持ち、解決不能は fail-closed (到達扱いにしない)。
- 評価は commit の blob を読む (dirty worktree を読まない) 既存性質を保つ。
- C01/C04/C09/C10/C11 の status/reason が変わるなら、それが**正しい方向の変化**であることを
  1 条件ずつ根拠付きで示す。無説明の変化は失格。

## 親の provisional 裁定 (攻撃対象)
- **(P1)** 裁定「評価器を広げる」は契約 JSON 不変を含意する、と読む。よって traversal は
  `required_evidence` の宣言 path に閉じず、import 束縛から解決した repo 内 module へ広がる。
  ← 反論候補: 宣言外 module を読むのは契約の証拠範囲を評価器が独断で広げる行為ではないか。
- **(P2)** C12 の chain は静的に辿れる。`run_trial` の**既定引数**
  `drive: Callable[...] = trigger.drive_iteration` (`p3_autonomous_workload_trial.py:2402`) と
  module-level alias `_lookup = env_contract.lookup` (`p3_s4_loop_trigger_gating.py:102`) を
  解決すれば届く。← 反論候補: 既定引数を辿るのは呼び出し側が差し替えうる値を「必ず走る」と
  みなす不当な仮定。高階引数の追跡は偽陽性を作る。
- **(P3)** `DECIDER_VERSION` bump の現用被害はゼロ (tip が legacy v1)。← 反論候補: 他の
  consumer (trial_registry / reflux_origin_binding / p3_autonomous_workload_trial の test) が
  版一致を前提にしている。
- **(P4)** 本 wave は受入全走が要る (実装面あり)。docs-only 免除は成立しない。

## 実アンカー表
| 面 | path:line | 内容 |
|---|---|---|
| 到達判定 | `orchestrator/campaign/s8c_preregistration_evidence.py:341-359` | `_reachable_functions` / `_reachable_calls` (module-local) |
| 関数抽出 | 同 `:280-286` | `_functions` は `tree.body` の top-level のみ |
| C12 | 同 `:564-593` | 第 1 gate = `{"lookup","attest_and_build_receipt"} <= calls` |
| C01 | 同 `:412-439` | `reached` / `_reachable_calls` を使う。ただし整数 gate が手前 |
| C04 | 同 `:442-456` | `calls` のみ |
| C09 | 同 `:459-478` | `_reachable_calls(producer,"run_trial")` |
| C11 | 同 `:517-561` | `_called_names` 直接。到達判定は未使用 |
| probe | 同 `:362-397` | `read_kind` / `python_kind` は contract 宣言 kind しか読めない |
| 版定数 | `orchestrator/campaign/s8c_preregistration.py:50` | `DECIDER_VERSION = "s8c-decider/v1"` |
| 版検査 | 同 `:1735-1750` | 厳密型 + `str.__eq__` |
| chain 起点 | `orchestrator/campaign/p3_autonomous_workload_trial.py:2402` | `drive=trigger.drive_iteration` 既定引数 |
| chain 中継 | 同 `:1202-1240` | `_drive_s8c_generation` が `drive(...)` を呼ぶ |
| alias | `orchestrator/campaign/p3_s4_loop_trigger_gating.py:102` | `_lookup = env_contract.lookup` |
| 実 tree golden | `orchestrator/tests/test_s8c_preregistration_predicates.py:118-133` | 12 条件の status/reason 表 |
| 負の対照 | 同 `:534-543` | 条件別 mutated reason 表 |
| 版 fixture | `orchestrator/tests/test_s8c_preregistration_core.py:1535,2014,2094` | literal `"s8c-decider/v2"` |

## 既存被覆と純増検出力
既存: 実 tree golden 表 1 本 + 条件別 negative control 6 本。いずれも **single-module fixture**
であり、cross-module の到達も同名衝突も 1 件も検査していない (実測: `reachab` / `cross.module`
検索で該当テスト 0 件)。純増は (a) cross-module 到達を数える、(b) import 束縛の無い同名定義を
数えない、(c) alias 経由を数える、(d) 実 tree C12 が第 2 gate の真の不在へ進む、の 4 性質。

## 成果物の形
- `orchestrator/campaign/s8c_preregistration_evidence.py` の到達判定 helper 群 (+ 必要な probe 拡張)
- `orchestrator/campaign/s8c_preregistration.py` の `DECIDER_VERSION` bump
- `orchestrator/tests/test_s8c_preregistration_predicates.py` の (A)/(B) テスト追加と golden 更新
- `orchestrator/tests/test_s8c_preregistration_core.py` の版 fixture 是正
- 変異 matrix による検出力実証

## 並列分割方針
編集ファイル所有が素集合にならない (評価器と述語テストは同時に触る) ため、段 5 は
**単一実装子**とする。段 3 敵対相談は 2 レンズ並列、段 6 レビューも 2 レンズ並列。
