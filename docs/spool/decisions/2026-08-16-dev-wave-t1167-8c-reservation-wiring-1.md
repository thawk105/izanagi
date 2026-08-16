---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1167-8c-reservation-wiring
seq: 1
---

## {{D:s8c-c12-unsatisfiable-by-construction}}. 8c 事前登録 C12 は構成上充足不能であり、配線でも単純削除でも閉じない

**決定 (1): 「8c launch path へ配線する」「契約から明示的に外す」の二択を、どちらも本 wave では
実装しない。** 二択の前提が実測で覆ったため、択一そのものを裁定パッケージとしてユーザーへ返す。

**決定 (2): C12 は未配線なのではなく、構成上充足不能である。** 実測は 2 点。

- 契約が要求する `single_process_required` は `reservation.py` に存在しない。同 module が持つのは
  `check_reservation` と `is_reservation_required` である。
- 評価器の到達判定は**同一 module 内の top-level 定義しか辿らない**
  (`s8c_preregistration_evidence.py` の `_reachable_functions`)。C12 は
  `p3_autonomous_workload_trial.py` の `run_trial` から `lookup`・`attest_and_build_receipt`・
  allocation 検査の 3 名すべてが到達可能であることを要求するが、これらは設計上いずれも別 module に
  ある。したがって**正しく cross-module 実装しても C12 は永久に充足できない。**

**決定 (3): C12 の現在の緑は、捏造した被検体に対する緑である。** 契約は 12 条件すべてを
`machine_checkable: false` としており、実 tree に対して `_evaluate_c12` は一度も走っていない
(実測: 現在値は `EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable`)。
C12 の既存テストは `def single_process_required(): pass` だけを持つ捏造 module に述語を撃っている。
これは「検査すると謳って発火しない保証」の型である。

**決定 (4): `machine_checkable` を反転すると、C12 は誤った診断を出す。** 実測 (契約 row を
in-memory で反転し実 HEAD の blob に対して評価器を実行) では
`UNSATISFIED` / `environment-contract-consumer-absent` を返す。しかしこの reason が指す
`lookup` と `attest_and_build_receipt` は**実際には 8c で走っている**。

- `lookup` は `p3_s4_loop_trigger_gating.py` の `_lookup` 別名経由で `_admit_env_contract` が呼ぶ。
- `attest_and_build_receipt` は `loop.py` の `_authorize_measurement` が呼ぶ。
- 実行 chain は `run_trial` → `_run_workload` → `_drive_s8c_generation` →
  `p3_s4_loop_trigger_gating.drive_iteration` → `loop.run_campaign` → `_authorize_measurement`。

したがって反転は単に赤を出すのではなく、**実在する強制を「不在」と誤って報告する**。
この値は契約を改訂する側が反転前に知る必要がある。

**決定 (5): 実際に欠けているのは allocation 検査だけである。** reservation は
`p3_autonomous_workload_trial.py` / `p3_s4_loop_trigger_gating.py` / `loop.py` のいずれにも無い。
8c は `_perf_for` 経由で実測するので、確保証跡の関門を持たないまま計測する。
**ただし `attestation_mode` が `required` なのは pegasus 契約だけで、linux-baremetal は `none` かつ
`single_process=False` である。** 「8c は attestation を通る」は pegasus 経路に限った主張であり、
無条件に一般化してはならない。

**決定 (6): 配線側の実装可否は本決定では開かない。** D419 は「強制だけを先に入れる」を却下し、
その解除を**ユーザー手番**と明記した。8c 用 tracked wrapper の新設も同決定が
他タスクの所有境界とした。実測でも `IZANAGI_RESERVATION_*` を供給する production launcher は
床値 campaign と t126 の 2 本だけで、8c 用は存在しない。よって今 fail-closed 検査を置けば、
捏造 fixture だけが通り正当な計算ノード実行は落ちる。

**決定 (7): 外す側を採る場合に消える保証を明記する。** ユーザー指示に対する回答である。

- **現に成立している保証は 1 つも消えない。** D431 member 6 は 8c launch を保護対象外と既に明記し、
  member 6 の control は t126 と床値・oracle 経路だけを守る。
- 消えるのは**事前登録された意図**である。すなわち「正式 8c の受理条件が allocation・PBS job・
  boot・期限の証拠と single-process / resume 禁止の証明を要求する」という宣言。
  外した後は、予約期限を越えて開始した世代や、他プロセスと同居した計測が
  8c 側のどの検査でも拒否されなくなる。
- あわせて負の対照 1 件が現在の意味を失う。

**決定 (8): reservation 述語自身の権威不足は本決定の所有ではない。** `check_reservation` が
`host` / `script_sha256` / `nonce` を何とも照合していないことは実測したが、これは既に裁定済みの
別タスクが所有する。本決定はその境界を開かない。

**理由:**
- 二択のまま片方を実装すると、どちらでも誤った台帳が残る。配線側は「保護した」と読める gate を
  実際には保護しないまま置き、外す側は「乖離を閉じた」と読めるが構成上の充足不能を隠す。
- 充足不能の原因は名前の不一致ではなく述語の表現力である。名前を合わせる改修は
  規律 2 が禁じる「述語を満たすための細工」に落ちる。
- 反転後に誤った診断が出ることは、契約を改訂する側が反転前に知らなければ、
  実在する強制を消す方向の改修を誘発する。

**却下した選択肢:**
- `single_process_required` を正本 def にし `is_reservation_required` を委譲 wrapper にする —
  C12 の AST が FunctionDef を要求するから名前を作る、という理由であり保証の実体を伴わない。
  加えて名前を揃えても module-local の到達判定が塞ぐため C12 は充足しない。
- 契約から allocation 節を単純削除する — 充足不能の原因が allocation 節だけではないため、
  削除しても `lookup` / `attest` 節の誤診断が残る。
- 本 wave で契約 JSON・評価器・凍結世代を改訂する — 稼働中の別 wave が同一面を所有しており、
  凍結 hash と世代鎖を二重に進めることになる。
- 実測 sink へ無条件の reservation 検査を置く — linux-baremetal の正当な計測を fail-closed で
  落とし、供給側 launcher も無いため計算ノード実行も落ちる。
