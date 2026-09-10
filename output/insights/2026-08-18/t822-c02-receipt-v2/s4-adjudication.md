# 段 4 裁定 — [T-822] (ii) 後段 (2026-08-18 14:00 JST、親)

段 3 は 2 レンズとも **NO-GO**。所見は合計 21 件、must-fix は 13 件。
親が全件を real / refuted、採用 / 不採用、scope 内 / 外へ裁定する。

## 1. 最重要の裁定 — 理由落としの根拠を「自己申告の一致」から「bytes からの再導出」へ

**レンズ A 所見 1 = real、採用。** 段 2 プランの receipt v2 は
receipt・report・run-start の 3 者一致だけを見る。3 者はいずれも producer が書いた要約であり、
どれも権威ある実行 artifact ではない。相異なる 6 digest を捏造し binding digest を正しく再計算した
bundle は、プランの検査を全部通る。それで `c02-arm-binding-unproven` を落とすのは、
受理集合を「実行 chain を証明した receipt」から「3 つの自己申告が揃った receipt」へ広げることである。

**採用する形**: 権威ある chain (`autonomous_trial_completeness._check_arm_digest_chain`, :719-870) は
`content_digest` を **cell descriptor の canonical bytes から再計算**している (:830-833)。
receipt verifier も同じ導出を自前で行う。

- receipt v2 は trial ごとに `arm_execution` の 3 field を持つ。
- verifier は既に hash 済みの **report bytes を parse し、その cell descriptor から
  canonical bytes を作って sha256 を計算**し、`content_digest_sha256` と一致することを要求する。
- `arm_binding_digest_sha256` は `SHA256(domain || holdout || arm || content_digest)` で再計算する。
- 同一 holdout の 3 arm の `content_digest_sha256` が相異なることを要求する。
- run-start の `arm_execution` が report と exact 一致することを要求する。

これで落とし条件は「6 件すべてについて、receipt が名指して hash した bytes から導出した digest が
主張と一致し、holdout 内で相異なる」になる。canonical 化は純粋な JSON 正規化 + sha256 であり、
`s8c_acceptance_receipt.py` の module 独立性 (registry / layer3 に依存しない) を壊さない。

**残る限界を明記する (paper over しない)**: bundle を丸ごと捏造する攻撃は依然として receipt 層では
落ちない。これは事前登録 commit 束縛と append-only registry の射程であり、[T-1311] が同型の所見を
refuted と裁定した根拠と同じである。insight と規範文書へ限界として書く。

## 2. real / 採用 (scope 内)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | A-1 | 理由落としが自己申告一致で通る | real・採用 (上記 §1) |
| R2 | A-3 / B-1 | 実名整備が契約 JSON だけで、評価器 literal (`s8c_preregistration_evidence.py:1490,1532`) と token-only fixture (`test_s8c_preregistration_predicates.py:441,462`) に旧名が残る | real・採用 |
| R3 | A-4 | `_called_names` は dead code と nested scope を数える。同 module に `_live_nodes` (:538) が実在する | real・採用。`_evaluate_c02` は `_live_nodes` を使う |
| R4 | A-5 | C02 の undefined 分岐削除で「registry blob 不在」の診断が失われる | real・採用。blob 不在は `TRIAL_REGISTRY_CAPABILITY_ABSENT` を保存する |
| R5 | A-6 | `SATISFIABLE_CONDITION_IDS` は宣言だけで dispatch 後に照合されない (親が :1766 で確認) | real・採用。**実行時 allowlist にする** — 許可外 ID の SATISFIED は fail-closed |
| R6 | A-7 | メタ検査が非 identifier root を黙って skip しうる | real・採用。検査済み `(condition, path, name)` 集合を exact pin する |
| R7 | B-3 | C02 の宣言済み負の対照 `nc_c02_proposal_path_arm_collision` と、プランの call edge 削除変異が別物 | real・採用 (§3) |
| R8 | B-8 / A-9 | 規範文書が T-1311 後の事実と食い違う。衝突 (d) が未解消のまま | real・採用 |
| R9 | A-2 | 負の対照 2・3 が単一理由性を持たない | real・採用。§4 で対照を組み直す |
| R10 | B-6 / B-7 | 並行 wave との凍結世代・test file 衝突 (親が実測で確認) | real・採用 (§5) |

## 3. C02 の負の対照 — 宣言済み ID に実装を合わせる

`test_satisfiable_predicate_requires_negative_control` (`test_s8c_preregistration_predicates.py:1827`)
は machine 条件の `negative_control_id` 集合と `NEGATIVE_CONTROL_CASES` の完全一致を要求する。
C02 を machine へ載せる以上 `nc_c02_proposal_path_arm_collision` を実装しなければならない。

**裁定**: 契約 ID を評価器に合わせて改名するのではなく、**評価器を宣言済み ID に合わせる**。

- C02 の `required_evidence` に producer module の行を足す
  (`orchestrator/campaign/p3_autonomous_workload_trial.py`)。
- `_evaluate_c02` は、invocation / proposal の namespace 構成子が arm と digest を消費することを
  要求する (実コードは `p3_autonomous_workload_trial.py:767` の `f"arm-{arm}.exec-{digest}"`)。
- 負の対照 = その構成子から arm と digest を落として 2 arm を同じ proposal path へ衝突させる
  token-only 変異。既存 6 対照と同じ「合成 source + 1 token 変異」の形 (`:594-661`) を踏襲する。

これで事前登録された対照名が字義どおり発火する。ID だけ流用して別物を殺す形は**採らない**
(それこそが本 wave の禁じる恒真化である)。

## 4. 負の対照の単一理由性 (A-2 への対応)

段 2 プランの 3 対照を組み直し、**5 件**にする。各対照は「その 1 点だけが赤の理由になる」ことを
実装時に確認する (`DW-M01`)。

1. **pairwise 衝突** — 同一 holdout の 2 arm を同じ content digest にし、binding digest は正しく
   再計算する。→ pairwise 検査だけが赤。
2. **digest と descriptor の乖離** — report の cell descriptor はそのままに、receipt の
   `content_digest_sha256` だけを別の有効な sha256 へ差し替える。report bytes と `report_sha256` は
   触らない。→ 再導出検査だけが赤。**プランの対照 2 は parse 時の再計算で先に落ちるため差し替える。**
3. **理由 gate の直接削除** — `arm_execution` を**完全に保ったまま**必須理由集合から
   `c02-arm-binding-unproven` を落とす gate を無効化する変異を作り、正例が黙って通らないことを見る。
   **プランの対照 3 は `_V2_TRIAL_KEYS` で先に落ちるため単一理由でない。** key 集合は保ち、
   gate だけを攻撃する形に変える。
4. **run-start 不一致** — report と receipt は一致させ、attempt journal の run-start だけ変える。
5. **v1 逆行** — v2 の bytes に対して v1 必須理由集合を要求する経路が残っていないことを見る。

## 5. 並行 wave の衝突 — 順序で解く (停止しない)

親が実測で確認した事実。

- `dev-wave-t1336-t1337-t1347-refreeze` は成果物に
  `condition-freeze.v1.g6.json` と `docs/phase3-8c-preregistration.md` を明記する。**g6 が正面衝突する。**
  同 wave は実装差分ゼロなので `DECIDER_VERSION` を bump しない。
- `t1333-t1310-workload-profile` は `test_s8c_preregistration_predicates.py` /
  `test_layer3_report.py` / `test_reflux_originless_compatibility.py` / `test_trial_registry.py` を編集する。

**裁定**: 停止条件ではない。世代番号は逐次で `prepare_revision` が exclusive-create するため、
先に land した方が g6 を取り、他方は再生成する。したがって

- **U3 (世代 record の発行) は最後の main 取り込みの直後、受入投入の直前に 1 回だけ行う。**
  それ以前に生成しない。生成済みの record を merge で運ばない
  (凍結世代の衝突は merge では解けない — 全履歴を走る不変検査が落ちる)。
- 先行 land があれば、私の record は g7 として**作り直す** (`supersedes_sha256` が相手の g6 を指す)。
- 共有 test file 4 本は、受入直前の main 取り込みで統合する。相手が先に land したら
  こちらが取り込む側になる。
- `DECIDER_VERSION` は私の wave だけが bump する。相手が先に g6 (v2) を出しても、
  私の g7 が tip になれば `test_s8c_preregistration_invariant.py:188` は緑のまま。

## 6. scope 外 — 裁定パッケージへ返す

- **C03 / C08 の `accept_trial` 誤名** (B-2、A-3 の後半)。real である
  (`load_manifest` / `accept_trial` はどちらも実在関数の誤名、`admit_preregistration` は未実装機構の
  将来名で正当)。しかし非機械条件であり評価器が 1 本も読まないため、直しても判定結果は変わらない。
  **本 wave の scope 命令は「問 3 側」= C09 由来の実名整備であり、非機械条件の契約文言改訂は
  別の設計択一 (どの誤名が「将来名」でどれが「誤り」かの線引き) を含む。**
  成果物影響 = 現時点でゼロ、将来 C03/C08 を機械化する wave が同じ穴を踏む。
  → 実装しない。裁定パッケージへ返す。
- **`verify_s8c_cross_binding` の実装** (C10 の充足)。scope 外、[T-822] 問 1 側の射程。
- **role payload の `workload` token 漏洩** ([T-1311] insight §6-1)。scope 外。
  `dev-wave-t1336-t1337-t1347-refreeze` が [T-1347] として持っている。

## 7. refuted / 格下げ

- **A-8 (golden 射影が run-start 不一致を隠す) → 格下げ。** 親が実測したところ、
  production の chain は `dict(start_arm) != dict(report_arm)` で 3 者一致を**既に強制している**
  (`autonomous_trial_completeness.py:762`)。したがって不一致 bundle は producer が作れない。
  射影に 3 者一致を足すのは安価なので**採用するが must-fix ではない** (nit として実装する)。
- **A-9 の「改名が必要」→ 部分採用。** 同名 `C02` の二義化は real な読み手リスクだが、
  恒久的な必須理由を足すと理由落とし自体が無意味になる。**採用する形は命名と文書**である —
  receipt 側の proof field を `arm_execution` と receipt-local に名付け、規範文書と insight に
  「receipt の理由落ち = 受領証が自分の参照 bytes 上で arm 束縛を証明した、であって
  事前登録条件 C02 の充足ではない」と明記する。評価器の C02 理由は変えない。
- **親自身の (P1) は反証済み** (段 2・親 M4 が独立に一致)。additive schema だけでは golden は保てず、
  検証付き逆射影が要る。
- **親自身の (P3) の一部は反証済み** (段 2・レンズ B 所見 5)。g6 の protected preimage は
  証拠契約 hash と docs の 3 hash だけで、U2 の source bytes を凍結しない。
  brief §6 の「g6 の hash が U1/U2 双方の最終 bytes に依存する」は**誤り**。訂正する。
  U3 が最後に来る理由は暗号学的束縛ではなく、契約 bytes と docs bytes の確定待ちである。
- **親自身の (P2) は強化して採用** (§1)。
- **(P4)(P5)(P6) は成立** (両レンズが GO)。

## 8. plan v2 (確定)

### U1 — 契約・評価器 (Codex author)

所有: `s8c_preregistration_evidence_contract.v1.json`、`s8c_preregistration_evidence.py`、
`s8c_preregistration.py`、`test_s8c_preregistration_{predicates,core,invariant}.py`。

1. C02 を `machine_checkable: true`。`entrypoints` を `bind_trial_arm` と
   `assert_trial_registry_acceptance` に。`required_evidence` に producer module 行を追加。
   `reachable_from` を実在経路へ。`field_paths` を T-1311 の実 field へ。
2. C09 / C10 の契約 JSON の `accept_trial` を `assert_trial_registry_acceptance` へ (10 箇所)。
3. `_evaluate_c09` / `_evaluate_c10` の literal (`:1490`, `:1532`) を同じ実名へ。
4. `_evaluate_c02` を新設。`_live_nodes` を使う。blob 不在は
   `TRIAL_REGISTRY_CAPABILITY_ABSENT` を保存。終端は他 6 本と同じ非充足理由。
5. `_MACHINE_EVALUATORS` に `2:` を追加。`_evaluate_undefined` の C02 枝を削除。
6. **`SATISFIABLE_CONDITION_IDS` を実行時 allowlist にする** — 許可外 ID の SATISFIED は fail-closed。
7. `DECIDER_VERSION = "s8c-decider/v3"`。
8. token-only fixture の `accept_trial` を実名へ。`NEGATIVE_CONTROL_CASES` に C02 を追加し、
   `nc_c02_proposal_path_arm_collision` の合成 source と 1 token 変異を実装。
9. メタ検査を新設 — machine 条件について、契約が名指す関数名が当該 module の AST に実在すること。
   検査済み `(condition, path, name)` 集合を exact pin する。wave 前の形 (`accept_trial`) を
   与えて赤になることを負の対照として同じ file に置く。

### U2 — receipt v2 (Codex author)

所有: `s8c_acceptance_receipt.py`、`trial_registry.py`、`test_trial_registry.py`、
`test_s8c_acceptance_receipt.py`、`test_layer3_report.py`、
`test_reflux_originless_compatibility.py`、新規 `test_s8c_acceptance_receipt_v2.py`。

1. v1 を `LEGACY_SCHEMA_VERSION` として保存。v2 を新設。v2 の必須理由は
   `t468-approval-authority-absent` のみ。`certifying` は両版とも構造的に `False`。
2. v2 trial に `arm_execution` (3 field exact) を必須化。
3. verifier が **report bytes を parse して cell descriptor から content digest を再導出**し、
   主張と一致することを要求 (§1)。binding digest 再計算、pairwise 非同一、run-start 一致。
4. producer を v2 発行へ。`AcceptanceSummary.arm_binding` を `execution-bound` へ。
5. 負の対照 5 件 (§4) を新規 test file に置く。**自走 harness を付ける** (F: 偽緑ガード)。
6. `_project_t822_receipt_v2_to_v1` を追加。値ごと消費してから旧 view へ落とす。
   receipt / report / run-start の 3 者一致も確認する (A-8 の nit)。巨大 golden literal は編集しない。

### U3 — 凍結・docs (親、最後)

1. `docs/phase3-8c-preregistration.md` の §6 条件 2、衝突 (d)、「現在地」を実測へ更新。
   §1 の「receipt の理由落ち ≠ 条件 C02 の充足」を明記 (A-9)。
2. 最終 main を取り込む。
3. `prepare_revision` で世代 record を **1 回だけ** 発行。先行 land があれば g7。
4. contract hash pin (`test_s8c_preregistration_core.py:1158-1161`) を更新。
5. spool fragment (worklog / decisions) を書く。**fold は land が行う。**

## 9. 変異事前登録 (`DW-M01`)

実装前に登録する。各変異は「前後の層が同じ入力を拒否しない」ことと「無効化時の赤理由が 1 つ」を
実装時にコードで確認する。確認できなければ登録せず実効 gate へ再照準する。

| ID | 位置 | 期待 |
|---|---|---|
| `t822.m1-c02-live-nodes` | `_evaluate_c02` の `_live_nodes` を `ast.walk` へ | KILLED |
| `t822.m2-content-digest-rederive` | receipt verifier の descriptor 再導出を削除 | KILLED |
| `t822.m3-pairwise-distinct` | pairwise 非同一検査を削除 | KILLED |
| `t822.m4-reason-drop-gate` | 証明なしで `c02-arm-binding-unproven` を落とせるようにする | KILLED |
| `t822.m5-binding-digest-rederive` | binding digest の再計算を削除 | KILLED |
| `t822.m6-runstart-equality` | run-start と report の一致検査を削除 | KILLED |
| `t822.m7-c09-prewave-name` | `_evaluate_c09` の literal を `accept_trial` へ戻す (**wave 前の実コードの形**) | KILLED |
| `t822.m8-meta-silent-skip` | メタ検査が非 identifier root を黙って skip する | KILLED |
| `t822.m9-satisfiable-allowlist` | 評価器が許可外 ID へ SATISFIED を返す | KILLED |
| `t822.m10-negative-control-map` | `NEGATIVE_CONTROL_CASES` から C02 を外す | KILLED |
| `t822.m11-decider-version` | `DECIDER_VERSION` を v2 のまま新世代を出す | KILLED |
| `t822.m12-blob-absent-reason` | blob 不在を edge 欠落と同じ理由へ潰す | KILLED |
| `t822.m13-c02-prewave-contract` | 契約の C02 を `machine_checkable: false` へ戻す (**wave 前の形**) | KILLED |

期待 node は probe 走行 (全件 SURVIVED 期待) で観測集合を集めてから完全集合として再登録する
(`DW-M08`)。

## 10. 成果物影響 (`DW-G05`)

実装しない場合、8c 正式受入 receipt は arm authority が実装済みでも
`c02-arm-binding-unproven` を恒久に掲げ、証拠契約は実在しない関数名を名指ししたまま残る。
本 wave 後も **certified 選択の値・proof 参照は 1 件も変わらない** — 変わるのは
(a) 受領証が掲げる非認証理由の集合、(b) 判定器が C02 を dispatch するか、
(c) 許可外 SATISFIED が実行時に落ちるか、の 3 点である。
