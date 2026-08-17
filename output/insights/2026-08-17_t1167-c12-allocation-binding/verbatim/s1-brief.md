# [T-1167] 段 1 brief — 8c 事前登録 C12 allocation 節の縮小

## scope

8c 事前登録 §6 条件 12 の allocation 節を「実現可能な allocation binding」へ縮小し、縮小の理由と
**何が保護されなくなったか**を事前登録本文へ注記する。縮小後の binding が実データで発火することを
示す。台帳本文は `docs/archive/worklog-phase3-0816-595-596.md` の [T-1167]。

## 確定済みユーザー裁定

- 2026-08-16 /rulings 全件 第 3 回、**択 (c)**: allocation 節を実現可能な binding へ縮小し、理由を
  事前登録へ注記する。単独性の主張を落とし、PBS job・boot・期限の束縛だけを条件にする。
  択 (a) 全面配線 (D419 却下解除 + 8c 用 launcher 新設の 2 依存が他所有)、択 (b) 節ごと削除は不採用。
- 対の裁定 [T-1202] 択 (ii) (到達判定を cross-module へ広げる) は**別 wave が現在稼働中**であり、
  本 wave の scope 外。

## 親の実測 (段 2・3 はこの値と一般化を攻撃対象にしてよい)

| 事実 | アンカー |
|---|---|
| 契約 C12 の allocation 節は `single_process_required(isolation_policy)` を要求 | `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:495-501` |
| その symbol は production に存在しない。実在は `check_reservation:218` / `is_reservation_required:273` / `read_binding:159` | `orchestrator/campaign/reservation.py` |
| 実 tree の C12 判定は `UNSATISFIED` / `environment-contract-consumer-absent` (allocation 枝へ**到達しない**) | 親 probe 実測 2026-08-17 00:56 JST、commit `5a19b8ab`、`_evaluate_c12` の第 1 関門 `s8c_preregistration_evidence.py:576-584` |
| `field_paths` / `reachable_from` は parse されるだけで汎用強制がない。判定は `_evaluate_c12` の hardcode | `s8c_preregistration_evidence.py:208-251, 564-596` |
| C12 の既存 allocation 被覆は**捏造 module** (`def single_process_required(): pass`) だけ | `orchestrator/tests/test_s8c_preregistration_predicates.py:406-486` |
| 実 tree の reason は gap ledger テストに pin されている | `test_s8c_preregistration_predicates.py:117-132` の `"C12"` 行 |
| 契約 bytes は `evidence_contract_sha256` で凍結され、改訂は同 commit の次世代 record を要する | `s8c_preregistration.py:41-52,389,1406-1506`; `docs/phase3-8c-preregistration.md` 「改訂手続き」 |
| 世代 record の `ruling_reference` は**導入 commit 時点の** `docs/decisions.md` に `## D<N>.` 見出しが要る | `s8c_preregistration.py:1381-1403,1499-1506` |
| 前例 g3 は既存 D438 を引いた (同 commit で decisions.md を触っていない) | `git show --stat 00e1ebdf` |
| 次世代 record は `prepare_revision` が canonical に生成する (schema v2 + `decider_version`) | `s8c_preregistration.py:1837-1900,1809-1834`; CLI は `check` / `prepare-revision` |
| 既存 D441 が C12 の構成上充足不能と択一集合を記録済み | `docs/decisions.md:18421` |

## 不変条件 (破ってはならない)

1. **正しさゲートを緩めない (規律 2)。** C12 を緑に見せる変更を採らない。縮小後も C12 は
   `SATISFIED` を返してはならない。受理集合を 1 bit も広げない。
2. **消える保証を事前登録本文へ明記する。** 縮小で要求しなくなるもの (8c launcher が単独性と
   resume 拒否を launch 前に強制すること) を、注記で名指しする。曖昧化しない。
3. **凍結手続きを迂回しない。** 契約 bytes を変えるなら同一 commit で g4 record を追加する。
   `ruling_reference` は導入 commit で実在する D に限る (新 D は fold 時採番のため構造的に使えない)。
4. `docs/decisions.md` / `docs/worklog.md` / `docs/failures.md` は直接編集せず spool fragment を書く。
5. 実装面 (コード・テスト・JSON) は Codex `role=author` が書く。親は docs 本文だけ編集する。

## 判断が割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1) 縮小の形。** allocation 節が要求する symbol を `single_process_required` から、実在する
  reservation binding (`read_binding` = PBS job id、boot id、`check_reservation` = 期限) へ差し替え、
  `single_process` 属性の要求を落とす。`allow_resume` の扱いは未決 —
  「PBS job・boot・期限だけ」と読めば落とすが、resume 拒否は単独性の主張ではない。段 2 が裁定材料を出す。
- **(P2) 「実データで発火する」の実現形。** allocation binding 判定を独立に呼べる helper へ切り出し、
  **実 repo の blob** (`reservation.py` / `p3_autonomous_workload_trial.py` の HEAD bytes) に対する
  verdict をテストで pin する。env gate の短絡順序は**変えない** (それは [T-1202] の面)。
- **(P3) 実 tree の C12 総合 verdict は変わらない。** env gate が先に落ちるため
  `environment-contract-consumer-absent` のまま。gap ledger テストの pin は不変。これを
  「発火していない」と読むのは誤りで、発火するのは allocation 節の判定であって C12 総合ではない。
- **(P4) `ruling_reference` は D441 を引く。** D441 は C12 の構成上充足不能と択一集合を記録した
  既存決定であり、本改訂の直接の前提。新 D (択 (c) の記録) は同 commit に存在しえない。
- **(P5) 編集面の衝突。** 稼働中の `dev-wave-t1202-t1197-cross-module-reach` が
  `s8c_preregistration_evidence.py` の到達判定と C12 テストを触りうる (2026-08-17 00:55 JST 実測、
  branch は main と同一 sha で未 commit)。受入直前に main を取り込む。

## 純増検出力 (テスト増設分)

既存被覆は「捏造 module に対する negative control 1 件」だけで、**production に存在しない symbol 名でも
緑になる**。増設分が新たに検出するのは「契約 allocation 節が要求する binding が実 production module に
実在しないこと」— 名前の綴りだけで恒真化する経路 (D441 決定 3 の型) を塞ぐ。

## 成果物影響 (DW-G05)

- 実装しない場合: 8c の certified 選択結果に付く allocation provenance は、契約側が充足不能の
  requirement を掲げ続け、C12 の reason が実在の欠落 (allocation 未配線) ではなく誤診断
  (`environment-contract-consumer-absent`) を指し続ける。受理集合は変わらないが、事前登録が
  「検査すると謳って発火しない保証」を 1 件持ったまま正式系列へ入る。
- 実装する場合: 受理集合は不変 (C12 は依然 UNSATISFIED)。変わるのは、allocation 節が
  実装可能な要求になり、恒真化経路が塞がることと、消えた保証が本文に名指しされること。

## 環境

受入・実測はこの worktree の login ノードで `python3 tools/run_tests.py` (bounded local)。
計算ノード dispatch は使わない。

## 分割方針

- 段 2: read-only codex 1 本 (plan)。file:line 粒度で (a) 縮小後の節の JSON 具体形、(b) `_evaluate_c12`
  の分解形と実 blob 判定 helper、(c) negative control ID と期待 reason の再設計、(d) g4 record の生成手順と
  `ruling_reference`、(e) 受入で赤になる既存 nodeid の列挙。
- 段 3: 敵対 2 本。レンズ A = 正しさ境界 (規律 2、恒真化、受理集合の拡大、消える保証の記述漏れ)。
  レンズ B = 整合・実効性 (凍結 pin 閉包、g4 の chain 検証、T-1202 との編集面衝突、(P2) の実現性)。
- 段 5 以降: Codex author = D95。
