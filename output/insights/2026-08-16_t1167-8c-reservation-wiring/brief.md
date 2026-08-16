# [T-1167] 段 1 brief — 8c launch path の allocation provenance

## scope

8c 事前登録証拠契約 C12 が要求する `run_trial -> reservation.single_process_required -> campaign
launch` と、実コードの乖離を閉じる。「8c launch path へ配線する」か「契約から明示的に外す」かを
裁定し、決めた側を実装する。台帳本文は `docs/archive/worklog-phase3-0816-572.md` の [T-1167]、
留保元は `docs/decisions.md:17908` 付近 (D431 member 6 の射程限定)。

## 親の実測 (段 2・3 はこの値と一般化を攻撃対象にしてよい)

実アンカー:

| 事実 | アンカー |
|---|---|
| `check_reservation` の実 call site は 3 箇所 / 2 系統 (t126, 8b) | `orchestrator/qualification/t126_driver.py:901`, `orchestrator/campaign/s8b_oracle_driver.py:921`, `orchestrator/campaign/s8b_floor_campaign.py:4858` |
| 8c launch path に reservation 参照はゼロ | `orchestrator/campaign/p3_autonomous_workload_trial.py` 全体で `reservation` の grep hit 0 |
| 契約が要求する関数名 `single_process_required` は repo に存在しない | `orchestrator/campaign/reservation.py` の def は `check_reservation:218`, `is_reservation_required:273` |
| C12 は `allocation_consumer` = `reservation.py`, `workload_supervisor` = `p3_autonomous_workload_trial.py` | `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の `required_evidence` |
| C12 を実 tree で評価すると **最初の関門で落ちる** (`lookup` / `attest_and_build_receipt` が `run_trial` の到達 call 179 件に無い) | `orchestrator/campaign/s8c_preregistration_evidence.py:588-598` |
| 契約は 12 条件すべて `machine_checkable: false`。`_evaluate_c12` は実 tree に対して一度も走っていない | 同 `.json` 全条件、dispatch は `s8c_preregistration_evidence.py:702-710` |
| C12 の既存テストは **捏造した `reservation.py`** (`def single_process_required(): pass`) にだけ述語を撃つ | `orchestrator/tests/test_s8c_preregistration_predicates.py:403-486` |
| `run_trial` は `_perf_for` に到達する = 8c は実測する | `p3_autonomous_workload_trial.py:2726` (run_trial), `:675` (`_perf_for`) |
| `_called_names` は attribute call も拾う → 通常 import でも述語は充足可能。到達不能は実装の不在であって述語の不能ではない | `s8c_preregistration_evidence.py` の `_called_names` |
| ただし `_reachable_functions` は **同一 module 内**しか辿らない → pipeline/loop 経由の間接強制は原理的に見えない | 同 `_reachable_functions` |

この実測から、C12 の 3 要求は性質が 2 種に割れる:

- **(A) 見えないだけで実在する強制** — `env_contract.lookup` と
  `execution_guard.attest_and_build_receipt` は `orchestrator/campaign/loop.py:68,78` で実際に走る。
  述語が module-local なので `p3` の AST に映らない。
- **(B) 本当に存在しない強制** — reservation の allocation 検査。8c は実測するのに確保証跡の
  関門を持たない。

## 確定済みユーザー裁定・上位裁定

- D431 member 6 は「member 6 の control が緑であることを 8c launch の allocation provenance が
  保護されている証拠として読んではならない。配線の要否は別途裁定する」と既に留保済み。本 wave が
  その裁定。
- ユーザー指示: 契約から外す側を採るなら、外した結果**どの保証が消えるか**を decisions fragment
  に明記する。

## 不変条件 (破ってはならない)

1. **証拠契約 JSON と凍結世代記録は本 wave の編集面に入れない。** 稼働中の
   `dev-wave-t1184-prereg-contract-revision` が現在所有している
   (2026-08-16 13:58 JST 実測、worktree 実在)。
   対象は `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` と
   `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g{1,2}.json`。
   触る必要が生じたら実装せず裁定パッケージとして返す。
2. 契約 JSON は semantic hash で凍結されている (`s8c_preregistration.py:374`
   `evidence_contract_sha256`, pin は `:1392,1445,1484,1759`)。bytes を変える案は凍結世代の
   繰り上げを伴い、それは T-1184 の所有。
3. 正しさゲートを緩めない。C12 を「緑に見せる」ことを目的にした変更を採らない。述語を満たすことと
   保証が実在することは別で、後者だけが目的。
4. 8c launch を fail-closed で壊さない。reservation admission は PBS 環境変数と
   `reservation.json` を要求するため、それらが無い正当な起動文脈があるなら無条件配線は
   8c 全体を止める。**配線する側を採るなら発火条件を実アンカーで書けること (DW-G04)。**

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1) 「配線する」を採る。** 根拠: 8c は `_perf_for` に到達して実測し、D431 member 4 が示すとおり
  compute site opt-in を持つ。実測する launch path が確保証跡の関門を持たないのは、
  F3 (外乱下の計測) を機械で検出できないことを意味する。「外す」は実在しない保証を
  文書から消すだけで、8c の allocation provenance は依然 unprotected のまま残る。
- **(P2) 実装面は production 側 (`p3_autonomous_workload_trial.py` + `reservation.py`) に限り、
  契約 JSON へ触らない。** これは不変条件 1 の帰結でもあるが、独立の設計判断として攻撃対象。
  この選択の代償は「C12 述語は本 wave 後も UNSATISFIED のまま」であり、乖離の**契約側半分**が
  残る。残余を [T-1167 の残余] として別 ID へ分離するかを段 4 で裁定する。
- **(P3) (A) と (B) を同じ裁定で扱わない。** (A) は述語の module-local 限界に起因する
  **偽の乖離**であり production の欠陥ではない。(B) だけが実欠陥。段 2・3 はこの二分自体を攻撃せよ。
- **(P4) 発火条件。** reservation admission を 8c へ置くなら、`is_reservation_required(isolation_policy)`
  (`reservation.py:273`) が既に条件分岐の seam を持つ。これを使えば isolation policy が要求する
  ときだけ発火し、不変条件 4 を満たせる **と親は読んでいる**。この seam が本当に 8c の
  isolation policy と接続できるかは未実測 — 段 2 が実アンカーで確かめること。

## 成果物影響 (DW-G05)

- 配線しない場合: 8c の certified 選択結果に付く allocation provenance は、確保が単独占有だった
  ことを機械で言えないまま残る。外乱下で取れた 8c 実測値が受理集合に入りうる。
- 配線する場合: 8c launch は確保証跡が無い環境で拒否される。受理集合が狭まる方向で、
  誤って通っていた試行が落ちる。

## 分割方針

- 段 2: read-only codex 1 本。file:line 粒度で (a) 8c launch の実行文脈棚卸し (PBS 環境の有無、
  dispatch 経由か直接か)、(b) `is_reservation_required` seam の接続可否、(c) 配線案と de-scope 案の
  両方の実装形、(d) 受入で赤になる既存 nodeid の列挙。
- 段 3: 敵対 2 本。レンズ A = 正しさ境界 (規律 2/3、恒真化、C12 を緑に見せる誘惑、(P3) の二分)。
  レンズ B = 整合・実効性 (T-1184 との編集面衝突、凍結 pin 閉包、fail-closed 破壊、(P4) の未実測)。
- 段 5 以降: Codex author = D95。実装面は親が触らない。
