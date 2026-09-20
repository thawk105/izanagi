# 段 4 裁定 — [T-2810] (2026-09-20 19:4x JST、wave 木 HEAD = main `800178b39`)

## §1 所見の裁定

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| A-1 binding 無し `reservation-preflight` の多重・順序を無条件に許すのは producer 形より広い | real (should) | 採用 | `reservation-preflight` は任意・**高々 1 件**・**`campaign-start` より前** を要求 (§2-1) |
| A-2 「旧 checkout でも同じ結論しか出ない」は実測から導けない | real (should) | 採用 | brief の P3 文言を撤回。旧 checkout への移植実測は「scope 外・未確認」と記す (§4) |
| A-3 brief 末尾の拒否原因が N1 と矛盾 | real (nit) | 採用 | 記録では「旧 (T-2724 時点) = journal 拒否、現行 main = policy 拒否」と分ける |
| B-1 上限 `i ≤ G` は既存条件 (G tree 実在 + 一意導入) から従う重複検査 | real (must-fix、文言) | 採用 | docstring・comment で「上限は重複検査、独立保証に数えない。追加の制約は一意・非 merge・下限 `C ≤ i`」と明記。検査自体は残す (helper 単体試験で意味を固定) |
| B-2 受理拡張は現物だけでなく区間全体の一般化 | real (must-fix、明示) | 採用 | α の受理集合 = 「各 path の一意・非 merge 導入 i について C ≤ i ≤ G (DAG 上の祖先関係、同一を含む)」と**明示して決定** (§2-2)。δ (`i == frozen_at_head`) は採らない (下記) |
| B-3 効能の限定 | real (must-fix、記録) | 採用 | 完了主張 = 「validator の互換性修復 + 新 main の historical reverify が段階 8 に到達」。live launch 成功・W-4/W-5 の開始許可へ一般化しない |
| B-4 N3 の削除案の帰結を裁定材料に | should | 採用 | 本 wave では削除しない。裁定パッケージ候補として帰結表付きで insight に記録 (§4) |
| B-5 fixture 成功 ≠ loader 込み chain 成功 | should | 採用 | 記録で fixture の証拠範囲を launch core に限定、実 repo の loader 成功は別証拠 |
| B-6 runbook へ現在値を再掲しない | should | 採用 | runbook §2 P3 / §3 W-3 は判定規則 + 観測正本 (worklog 末尾・一次資料) への参照に直す。exact 拒否文字列は runbook に書かない |
| plan 攻撃点 2 (binding 値の一致まで要求) | — | 採用 | producer が同じ binding から両 record を作るので妥当 |
| plan 攻撃点 4 (中間 commit 導入も受理) | — | B-2 で明示採用 | |
| plan 攻撃点 1 (A 導入負例は段階 3 で先に落ちる) | — | 採用 | helper 単体試験に分離、public 経路の証拠と混同しない |

**δ (`i == document["frozen_at_head"]` かつ C ≤ i < G) を採らない理由:** (1) 独立 fixture の `frozen_at_head` は v1 由来 (`2e20d441…`、現行 repo に無い commit) で launch core は V1a を検査しないため fixture の全面変更が要る、(2) D2077 は「候補生成前に commit」を要求するだけで「全 closure の初導入 = captured HEAD」までは要求しない (相談 B)、(3) measurement_closure が将来複数 commit で導入される形を排除する。α の区間受理は現物 (i = C = G^) と fixture (i = G) を同じ述語で受理し、下限・一意・非 merge を追加の制約として残す。

**refuted / 修正不要:** なし (相談 A・B とも must-fix の実装変更は無し、文言・記録・A-1 の構造検査のみ)。

## §2 plan v2 (実装仕様、Codex author への確定指示)

### §2-1 journal allowlist (`_JOURNAL_KEYS` / `_validate_journal`)

1. `_JOURNAL_KEYS["reservation-preflight"]` = base 10 key `{event, required_s, safety_margin_s, formula, build_cap_per_cell_s, shared_dependency_prebuild, dependency_configure_cap_s, dependency_target_cap_s, verify_cap_per_attempt_s, finalize_reserve_s}`。`campaign-start` の既存 15 key は不変。値型 `dict[str, frozenset]` は不変。
2. `_JOURNAL_BINDING_KEYS = frozenset({"pbs_jobid", "submission_nonce"})` を module 定数に置く。per-record loop で `key in {"reservation-preflight", "campaign-start"}` かつ `_JOURNAL_BINDING_KEYS & set(record)` が非空なら `expected = expected | _JOURNAL_BINDING_KEYS` として `_exact_keys` へ渡す (片欠けは exact 検査で拒否、他 event への binding key は未知 key として拒否)。
3. 型検査 (exact の直後、同 loop): binding claim 時は両値とも `type(v) is str and v != ""` (cause `journal-binding-type`)。`reservation-preflight` は binding 有無に関わらず `formula` 非空 str、`shared_dependency_prebuild` は `type(v) is bool`、残る 7 数値 field は `type(v) is int and v > 0` (bool を拒否、cause `reservation-preflight-type`)。
4. 構造検査 (`campaign-start` 一意性が確定した後): `reservation-preflight` は**高々 1 件** (cause `reservation-preflight-count`)、存在するなら index が `campaign-start` より小さい (cause `reservation-preflight-order`)。binding: `campaign-start` が claim するなら `reservation-preflight` が存在してかつ claim、`reservation-preflight` が claim するなら `campaign-start` も claim (cause `journal-binding-claim`)、両者の `(pbs_jobid, submission_nonce)` が一致 (cause `journal-binding-mismatch`)。
5. reason はすべて `journal-state-invalid`。未知 event は既存 `journal-event`。`_JOURNAL_KEYS["session"]` と他 event の集合は 1 byte も変えない。
6. 受理集合の変化 (明示): 新規受理 = (a) binding 無し campaign + binding 無し reservation 1 件 (campaign 前)、(b) binding 付き campaign + 同値 binding 付き reservation 1 件 (campaign 前)。従来受理 (reservation 無し) は不変。拒否 = 片側 claim、値不一致、key 片欠け、型不正、reservation 2 件以上、campaign 後の reservation。binding は記録内の整合情報であり PBS job の外部認証ではない (docstring にそう書く)。
7. `journal["campaign"]` は binding key を含む record をそのまま保持する (後段の `result.wall_ledger` mirror 比較 `_plain_json` に binding を落とさない)。

### §2-2 段階 6 lineage

1. cert C の検査 (一意導入・非 merge・`C != G`・C が G の祖先) は 1 byte も変えない。
2. result と measurement_closure の各 path について private helper `_assert_artifact_introduction_interval(graph, path, oid, *, cert_commit, gen_commit, root)` (HEAD を再解決しない、捕捉済み `graph` と full OID だけを使う) で: (i) `intro = _unique_introduction(_immutable_introductions(graph, path, oid, root), path)` (既存 reason `history-mutated` / `no-introduction` / `multiple-introduction` は不変)、(ii) `len(graph.parents.get(intro, ())) > 1` → reason `binding-chain-mismatch` cause `artifact-introduction-merge`、(iii) `not _git_ok(["merge-base", "--is-ancestor", cert_commit, intro], root)` → cause `artifact-introduction-before-cert` (detail は「cert C が導入 i の祖先でない」、時刻順を意味させない)、(iv) `not _git_ok(["merge-base", "--is-ancestor", intro, gen_commit], root)` → cause `artifact-introduction-outside-generation` (**comment に「段階 3 の G-tree 実在 + 一意導入から従う重複検査。独立保証に数えない」と書く**)。
3. 世代文書 path `_gen_path(ratified.generation_number)` の導入集合 == {gen_commit} を段階 6 (artifact 検査の後、段階 7 の前) に足す。reason `binding-chain-mismatch` cause `generation-introduction` (既存 cause を維持し、wrong_g=A 負例の期待を変えない)。
4. `_launch_validate` docstring の保証境界を「cert C の一意導入・非 merge・C<G、result / measurement_closure の各 path の一意導入・非 merge・I_entry ⊆ [C, G] (DAG 上の祖先関係、同一を含む)、世代文書 path の導入集合 {G} は捕捉済み H 内の記録順だけを保証する。上限 i ≤ G は段階 3 の G-tree 実在検査と一意導入から従う重複検査で独立保証に数えない。実時間順・履歴再構成への耐性・cert 発行と result 走行の実時間順は保証しない」へ更新。旧「∀i in I_entry: C<i は I_entry=={G} と C<G から従う」は削除。
5. 受理集合の変化 (明示、B-2): 従来 = 全 artifact が G で同時初導入 (かつ C < G から C < i)。新 = 各 artifact が一意・非 merge の commit i で初導入され C ≤ i ≤ G。現物 (i = C = G^)、fixture (i = G)、中間 commit 導入、C 後に分岐して G 前に合流する形を受理。保たれる保証: H 全到達履歴で別 bytes が現れない、導入一意、G/H/worktree の bytes・mode 一致、raw hash・semantic・binding・scan、段階 7 の active chain 再解決との `generation_commit` 一致。

### §2-3 test (`orchestrator/tests/test_s8b_ratified_verify.py`)

1. `_build_independent_launch_repo` に `artifacts_at_certificate=False` option: True なら cert bytes は従来どおり先に作り、C の commit を「result / closure / journal / manifest / protocol が確定した後・世代文書を書く前」まで遅らせ、**cert と run artifacts と closure を同じ commit C** に入れる。続く G は世代文書だけを導入。`cert_at_generation=True` との併用は `ValueError`。topology に `C` / `G` を返す。default (False) の bytes・commit 構成は不変。production emitter fixture (`test_s8b_ratified_freeze.build_production_emitter_g1`) は触らない。
2. journal の変形は既存 `mutate(state)` 経路で行う (commit 前)。binding 付き正例では `result["wall_ledger"]` の campaign-start にも同じ binding を入れる (producer が campaign record 全体を転記する形に合わせる)。
3. 正例 (public `launch_validate` が `LaunchValidatedFreeze` を返す): (P-a) default fixture (i = G、不変)、(P-b) `artifacts_at_certificate=True` (i = C = G^)、(P-c) (P-b) + binding 付き `reservation-preflight` (campaign 前) + binding 付き `campaign-start` + wall_ledger 同期、(P-d) (P-b) + binding 無し `reservation-preflight` 1 件。
4. 負例 (reason / cause を exact に固定し、無変異の対照が通ることを同 test か隣接 test で示す): (N-1) closure80 を base commit で同 bytes 導入 → `artifact-introduction-before-cert`、(N-2) C 後に両 parent とも path を持たない分岐を merge M で初導入し G に世代文書 → `artifact-introduction-merge`、(N-3) C 後に同 bytes を導入・削除・再導入 (G/H 同 bytes) → `multiple-introduction`、(N-4) 既存 wrong_g=A (`test_floor_source_introduction_must_be_exact_generation_commit`) を**維持**し cause `generation-introduction` が新検査で出ることを確認、(N-5) 既存 C=G (`cert-lineage`) 維持、(N-6) 未知 event → `journal-event`、(N-7) 片側 claim (campaign のみ / reservation のみ、両方向 parametrize) → `journal-binding-claim`、(N-8) binding key 片欠け → exact key 拒否 (既存 detail 形)、(N-9) binding 型不正 (`""` / int、各 event × 各 key) → `journal-binding-type`、(N-10) 値不一致 → `journal-binding-mismatch`、(N-11) reservation field 型不正 (数値に 0 / bool / str、formula に `""` / int、bool field に int) → `reservation-preflight-type`、(N-12) reservation 2 件 → `reservation-preflight-count`、(N-13) reservation が campaign-start の後 → `reservation-preflight-order`、(N-14) helper 単体: 実 Git の小 DAG で path を G の子孫 (A) に初導入し `_assert_artifact_introduction_interval` を直接呼ぶ → `artifact-introduction-outside-generation` (**「重複検査の単体試験」と docstring / comment に明記**、public 経路の証拠にしない)。
5. `orchestrator/tests/test_s8b_oracle_driver.py:131–147`: `_ACTIVATED_G1_REFUSALS` の第 1 要素 (layer-2 hit) は 1 字も変えず、第 2 要素を `"v2-execution: launch-validate: [manifest-invalid] [manifest-invalid] binaries[rr20::backoff_fixed_best] admission receipt が不正: receipt admission policy が現行 policy と不一致"` へ。comment は「T-2304 / D2184 の ccbench pin 前進で admission policy epoch が `db6bc9ea…` へ移った後の実 repo の live P3 真値 (T-2304 統合時に追随すべき期待値を T-2810 で補完)。T-2810 の journal / lineage 修復後も live 経路は段階 4 の現行 policy 照合で拒否される。historical reverify (`reverify_published_freeze`) は段階 8 の未発効候補 hit まで到達する」の趣旨。
6. `orchestrator/tests/test_s8b_binding_driftguards.py` は共用定数を参照するだけなので**編集しない** (所有には含めるが差分ゼロ)。
7. 既存 test の期待値を変えない (N-4 / N-5 の reason / cause を含む)。fixture へ現行 hash を差し込まない。新 test 名は ASCII、parametrize id も ASCII (変異 harness の期待 node 登録のため)。

### §2-4 docs (親)

runbook §2 P3 の「2026-09-20 時点の実測は …」と §3 W-3 の「発効」段落の現在値を、判定規則 + 「現在値の正本は worklog 末尾と一次資料」の参照へ置換 (exact 拒否文字列は書かない)。一次資料 `output/insights/2026-09-20/t2810-g1-launch-validation/README.md` を作る。

### §2-5 規模上限

production `s8b_ratified_freeze.py` +100〜200 行 (削除含む)、test +350〜650 行。超えるなら理由を報告。

## §3 変異の事前登録 (DW-M01、production 変異、独立 clone @ 統合 commit、計算ノード dispatch、probe → final)

| ID | category | 変異 (production `s8b_ratified_freeze.py`) | 殺す test (期待、probe で node を実測) |
|---|---|---|---|
| M0 | positive (等価) | `_JOURNAL_BINDING_KEYS` 定義行の直上に comment 1 行 | SURVIVED (harness の正例) |
| M1 | negative | `_JOURNAL_KEYS` から `reservation-preflight` entry を削除 (旧 allowlist) | P-c / P-d が `journal-event` で赤 |
| M2 | negative | binding key の optional 拡張 (§2-1 項 2) を外す | P-c が exact key で赤 |
| M3 | negative | claim 一致検査 (§2-1 項 4) を削除 | N-7 が通って赤 |
| M4 | negative | binding 型検査を削除 | N-9 が通って赤 |
| M5 | negative | 値一致検査を削除 | N-10 が通って赤 |
| M6 | negative | reservation field 型検査を削除 | N-11 が通って赤 |
| M7 | negative | reservation 件数 ≤ 1 検査を削除 | N-12 が通って赤 |
| M8 | negative | reservation 順序検査を削除 | N-13 が通って赤 |
| M9 | negative | 下限 (`cert_commit` が `intro` の祖先) 検査を削除 | N-1 が通って赤 |
| M10 | negative | 非 merge 検査を削除 | N-2 が通って赤 |
| M11 | negative | `_unique_introduction` を `introductions[0]` に置換 | N-3 が通って赤 |
| M12 | negative | 世代文書導入 == {G} 検査を削除 | N-4 の cause が `generation-introduction` でなくなり赤 (段階 7 で別 cause) |
| M13 | negative | 上限 (`intro` が `gen_commit` の祖先) 検査を削除 | N-14 (helper 単体) が通って赤 |
| M14 | negative | 段階 6 を旧 `set(introductions) != {gen_commit}` に戻す | P-b / P-c / P-d が `generation-introduction` で赤 |

各変異は実装後に「同じ入力を拒否する層が前後にも内側にも無く赤理由が一つに絞れる」ことを確認し (F820)、できなければ登録から外して記録する。

## §4 scope 外 (実装しない、insight に記録、裁定パッケージ候補)

1. **N1 / T-2812:** 新 main の live 経路は段階 4 の policy 照合で止まる。policy 照合の除去・`expected_policy=None` の live 導入・receipt 張り替えは D2184 で却下済み。移行は T-2812 (② 登録・identity、③ driver pin、⑤ successor protocol、admission の整合)。
2. **N3 候補文書の scan hit:** 第一候補 = 候補 file `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` だけを削除する commit (scan 除外は広げない、B-10 pin 対象外、G/A/X・floor_source bytes は不変、`_active_chain_exempt_exact` 不変)。帰結: `V2_CANDIDATE_REL` の create-only 存在拒否が消える (再生成されれば hit が復活)、`_ACTIVATED_G1_REFUSALS` の候補を含む hit 列挙が変わる、削除後に load / reverify をやり直す、候補 bytes と来歴は X2 の履歴 blob と世代文書で保持。D2077「痕跡を消してよかったことの証明ではない」に照らし削除の根拠は別裁定。
3. **旧 pin 固定 checkout への修正の移植・実測:** 未実施・未確認 (A-2)。歴史再開に本修正を使うなら移植した別 checkout の検証が要る。
4. **W-4 spec 承認、W-5 実走・certified 選択:** 不変。本 wave は測定値・認証結果・certified の受理集合を更新しない。

## §5 受入条件・実測 (親)

- 実 repo (wave 木、統合 commit 後、無変異): (a) `reverify_published_freeze` → `closure-hit-mismatch` (rr80 未申告 = 候補 path) = 段階 4〜7 通過の証拠、(b) `launch_validate` → `manifest-invalid` / `binary-admission`、(c) runbook P3 gate-check (g1 path) → `allowed: false`、拒否 2 件 exact (= 更新後 `_ACTIVATED_G1_REFUSALS`)、v1 path → 既知 4 件 exact、(d) `assert_g1_floor_selection_identity` → None、(e) `load_ratified_freeze` → generation 1 / sha `7e1114…`。
- 焦点走 (計算ノード dispatch): `test_s8b_ratified_verify.py`、`test_s8b_oracle_driver.py` (held 6 node は診断 token)、`test_s8b_binding_driftguards.py`、`test_s8b_terminal_evidence.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、`test_s8b_ratified_freeze.py`。
- 変異 matrix §3、受入全走、全史 provenance 監査、`check_docs`、`git diff --check`。
