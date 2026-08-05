# [T-327] 段 4 裁定 (= プラン v2 差分) — 2026-08-04

段 3 の 2 レンズはいずれも NO-GO (A: blocker 11 / should 2、B: blocker 2 / must-fix 6 / should 2)。
親が real/refuted と採否を裁定し、scope を確定する。**本 wave の看板を訂正する** —
「8c 事前登録の**発効判定層と条件契約の凍結**を実装する」であり、「発効の完全実装」ではない。

## 0. 看板と完了条件の訂正 (レンズ B-1 / レンズ A-8 を real 採用)

- 両レンズが「CLI と invariant test だけでは formal launch を止めない = 実効性がない」と指摘した。
  **real。** ただし launcher / acceptance は並行 wave [T-325] が改修中の同一入口であり、未 land の
  API へ結線すると衝突と二重実装になる (`DW-STOP` の迂回禁止と `DW-G04` の発火条件)。
- **裁定**: scope は維持する ((P6) 継続) が、**完了主張を弱める**。worklog・文書・decisions に
  「本 wave は静的 readiness 層のみ。launch admission と post-run acceptance は未結線であり、
  T-327 を『発効の実装完了』と主張しない」と明記し、結線を後続タスクとして起票する。
- 現 checkout の判定結果は **未発効** であり、未結線でも誤った受理は生じない (発効が false のため)。
  リスクは将来の green 化にあり、それを (裁定 4) の meta-test で縛る。

## 1. real 採用 — 本 wave で実装する

|#|所見|裁定|実装|
|---|---|---|---|
|A-1|`activation_commit = git log -1 -- doc` は「条件が揃った commit」でない。未充足時の測定を後付けで遡及 green にできる|**real・採用**。brief (P2) を**改訂**|発効判定の第一級 API を `effective_at(C)` とし、**C 時点の git blob だけ**から再計算する。HEAD 依存を廃す。manifest が pin する C について `effective_at(C)` が true であることを要求する契約を文書へ書く|
|A-3|凍結対象が §5 欄名 + §6 だけで、§§1–4/§7 の規範本文 (停止規則・全件報告規則) が保護外|**real・採用**|保護 hash を §§1,2,3,4,6,7 の正規化本文 + §5 欄名集合 + 発効ポリシー block + evidence contract へ拡張。§5 の**値**は可変 (記入されるため) と明記|
|B-4|発効式・no-approval・改訂規則を書く H3 節が hash 対象外。同じ generation が二つのポリシーを指しうる|**real・採用**|発効ポリシーを独立した canonical block として文書に置き、保護 hash に含める|
|A-4|chain は「記録付きの条件緩和」を正当な改訂として受理する|**real・採用**|**gN (N≥2) の改訂記録は人間 ruling 参照を必須**とし、その ruling ID が改訂 commit 時点の canonical 台帳に実在することを機械検査する。**都度承認ではない** (実走ごとには何も要らない) ため、ユーザー裁定 (定型コマンドの排除) と両立する|
|A-11 / B-5|C11 が「禁止裁定の存在」を充足と取り違えている|**real・採用**|C11 を compliance predicate 化 (cap lift・三入口境界・critic 還流 consumer・標本設計の事前登録が揃うまで UNSATISFIED)。裁定文 hash は補助証拠に降格|
|A-2 (框)|C01〜C12 は「恒真化」か「発効不能」の二択になりうる|**real・部分採用**|静的層の原則を固定する: SATISFIED の根拠は**実走前に決まる事実だけ**。実走後にしか存在しない証拠を要求する条件は `EVIDENCE_UNDEFINED` (= 未充足) を返す。三段分割の残り 2 層は裁定パッケージ|
|B-2 / A-5|評価器 Python の bytes が無保護。`every` を `any` に変えれば同じ g1 で発効値が反転する|**real・部分採用**|(i) `ActivationReport` に評価器 module の C 時点 blob hash を記録する、(ii) **meta-test**: SATISFIED を返しうる述語は evidence contract で `machine_checkable: true` かつ negative control test が存在することを強制する。evaluator 自体の freeze pin は自己 pin を生むため裁定パッケージ|
|B-6 / A-9|`H` 固定と live import が両立せず、未 commit 編集で証拠を偽装できる|**real・採用**|述語は live import で判定せず **C の git blob から読んだ内容**で評価する。やむを得ず import する経路は module bytes と blob の一致を必須とし、不一致は `ERROR` (= 未充足)|
|B-7|「保護 hash 変化 = 同 commit に gN 追加」と「導入 commit は一意 non-merge」が merge で両立しない|**real・採用**|履歴検査を commit ごとの `(protected_hash, generation)` 状態遷移として定義し、merge は両親同状態または一方が他方の後継のときだけ受理する|
|B-9|8c 文書が `check_docs.py` の `LIVING_DOCS` 外で、参照腐敗を検出しない|**real・採用**|`LIVING_DOCS` に 8c を追加し、不在 path / 腐敗行番号を検出する負例テストを足す|
|A-13 / B|brief・plan が参照する T-325 snapshot が既に stale|**real・採用**|T-325 の API へ pin しない。**capability probing** とし、registry 不在なら `EVIDENCE_UNDEFINED`。T-325 の land 有無に関わらず本 wave を単独で land 可能にする|
|A-12|(P3) の「本文複製は scan を汚染する」は一般化しすぎ|**real・採用**|(P3) の理由を「compact な canonical contract」に限定。汚染の有無は**実 artifact を repo scan にかけるテスト**で実測する|
|B-10|`DW-O09` の記録が path 検索と FROZEN_MANIFEST だけで、規定の key/role 側検索を欠く|**real・採用**|親が key/role 側検索を実施して brief と worklog に query と分類を記録する (本裁定と同時に実施済み)|

## 2. real だが scope 外 — 裁定パッケージ (U-1〜U-7) としてユーザーへ返す

|ID|所見|理由|
|---|---|---|
|U-1|A-8 / B-1: launch admission と post-run acceptance への結線 (sealed activation を必須引数にする)|[T-325] の稼働面。land 後の独立タスク|
|U-2|A-6: g1 が自己署名で、履歴再構成と正常系列を区別できない (外部 anchor = 署名 tag / remote / transparency log)|AI は push しない規約。運用と権限の設計判断|
|U-3|A-7: C10 の mutable 入力一式同時改変 (外部 append-only ledger が要る)|文書 §7 が既に情報理論的限界として自認。設計択一|
|U-4|A-10: T-325 は未登録 ID の探索実走を許すため、H1/H2 の**事前観測路**が開く (hidden pilot → §5 を結果適合に決められる)|[T-325] の面。**重大**につき優先度高で返す|
|U-5|B-8: canonical manifest/registry authority、同一 trial の一回性、acceptance receipt の下流消費 (best-of-N manifest 差し替え)|[T-325] 自身が残余として記録済み|
|U-6|B-3: C01/C06/C07 が 8b の active ratified generation へ束縛されていない|証拠契約に必須証拠として**記述**はするが、`load_ratified_freeze` 結線は述語 green 化段の仕事|
|U-7|§6 条件 9・12 の診断文が古い (層3 は publish 前に検査済み / Pegasus 拒否は解消済み)。§5 に schedule・標本設計の欄がない|**条件文の改訂**にあたるため、本 wave では触らず g2 改訂案として返す (規範文を親の判断で書き換えない)|

## 3. 不採用 / 降格

- A-2 の「三段分割を本 wave で全実装」= **不採用** (scope 外、U-1/U-3 へ)。
- B-2 の「evaluator raw bytes を gN へ pin」= **降格** (自己 pin と正当な改修の両立が未設計。裁定パッケージ)。
- プラン単位 E (`guard_write` へ s8c namespace の誤操作抑止) = **本 wave では不実装**。
  hook は正しさの層に数えず (hooks/README の s8b 先例)、無記録変更は履歴検査が捕らえる。後続へ。
- プランの「§5 に 2 欄追加」= **不採用** (事前登録の**内容**変更は [T-295] の面。U-7 へ)。
- プランの「§6 条件文の古い診断を g1 前に訂正」= **不採用** (同上、U-7 へ)。

## 4. 実装契約 (プラン v2 の確定事項)

1. 新設 module は `orchestrator/campaign/` に置き、`p3_autonomous_workload_trial.py` /
   `trial_registry.py` / `s8b_*.py` / `test_frozen_artifacts.py` を**編集しない**。
2. `EVIDENCE_UNDEFINED` / `UNSATISFIED` / `ERROR` / `NOT_EVALUATED` はすべて false。
   `NOT_APPLICABLE` を設けない。`approve` / `activate` / `revoke` CLI を作らない。
3. **本 wave の出荷時点で 12 述語のうち SATISFIED を返すものは 0 件**である (C11 を含む)。
   これを invariant test で固定し、将来 green を作るときは negative control test を同時に要求する。
4. g1 は文書確定後に generator で発行する。手入力しない。self hash / 導入 commit /
   activation commit を field に置かない (F36)。
5. 新設 tracked artifact が未既知性 conjunction 検査に hit を増やさないことを実測テストで固定する。

## 5. 変異事前登録 (`DW-M01`。実装前登録、単一理由性は段 6 の anchor 再検証で確認)

|#|変異|期待赤 (kill 判定)|
|---|---|---|
|m01|`effective()` の `every(... SATISFIED)` を `any(...)` にする|`test_effective_requires_all_twelve`|
|m02|`EVIDENCE_UNDEFINED` を真扱いにする|`test_evidence_undefined_is_never_satisfied`|
|m03|述語 registry から C12 を落とし 11 件にする|`test_predicate_registry_is_exactly_c01_through_c12`|
|m04|§6 の各条件を太字先頭句だけで hash する|`test_word_change_changes_condition_hash` (継続行の欠落検出)|
|m05|保護 hash から §5 欄名集合を外す|`test_field_set_change_requires_new_generation`|
|m06|保護 hash から発効ポリシー block を外す|`test_policy_block_change_requires_new_generation`|
|m07|保護 hash から §§1–4/§7 の規範本文を外す|`test_normative_body_change_requires_new_generation`|
|m08|`supersedes_sha256` を前 record の raw bytes hash でなく条件 hash にする|`test_generation_chain_rejects_bad_supersedes`|
|m09|履歴検査を HEAD 比較だけにする (中間の変更 → revert を見逃す)|`test_generation_chain_rejects_unrecorded_change_even_after_revert`|
|m10|gN の既存 path 上書きを許す|`test_generation_history_rejects_mutation_and_delete_readd`|
|m11|改訂記録の ruling 参照必須を外す|`test_revision_requires_existing_ruling_reference`|
|m12|`effective_at(C)` を HEAD 評価へ戻す|`test_effective_at_uses_commit_blobs_not_worktree`|
|m13|module bytes と blob の一致検査を外す|`test_dirty_worktree_evidence_is_error_not_satisfied`|
|m14|merge の状態遷移規則を「両親いずれかが一致」に緩める|`test_merge_requires_compatible_generation_state`|
|m15|table 分割を単純 `split("|")` にする|`test_table_lexer_handles_escaped_pipe_and_code_span`|
|m16|SATISFIED 可能述語の negative control 必須 meta-test を外す|`test_satisfiable_predicate_requires_negative_control`|
|m17 (正例)|文書の空白・改行だけを変える|**赤にならない**こと (過剰拒否の検出。`test_layout_only_changes_preserve_hash`)|

## 6. 実装単位

|単位|所有|依存|
|---|---|---|
|A|`orchestrator/campaign/s8c_preregistration.py` + `orchestrator/tests/test_s8c_preregistration_core.py`|なし|
|B|`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` + `orchestrator/campaign/s8c_preregistration_evidence.py` + `orchestrator/tests/test_s8c_preregistration_predicates.py`|A|
|C (親)|`docs/phase3-8c-preregistration.md` の発効ポリシー block と H3 置換、`output/README.md`|A の正規化契約確定後|
|D|`tools/check_docs.py` の `LIVING_DOCS` 追加 + 負例テスト、`orchestrator/tests/README.md` allowlist、`orchestrator/tests/test_s8c_preregistration_invariant.py`、g1 発行|A→B→C|

順序 = A → B → C(親) → D。同一 worktree で直列 (所有は素集合)。
