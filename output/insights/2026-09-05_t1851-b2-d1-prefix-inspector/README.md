# [T-1851] 実装単位 B2 / D1 の非 terminal 部分 — v2 台帳の read-only prefix inspector と、result v5 契約・proof 型・verifier の v4/v5 分岐

2026-09-05。branch `worktree-dev-wave-t1851-unit-a`。**land していない (D1341)。**

- 継承 tip: `fd814b2f0` (A2β の記録 + 追加裁定 3 件)
- 本 wave の commit: `50dbf9158` (local main `61bc6ac69` の取り込み、integrator)、`a0ac63690` (実装)、`b6c5b568d` (記録)、`b54836171` (受入の post-claim merge、local main `8c07ded74`)、受入結果と段 8 の追記 commit
- 実装面の差分: 8 file、+1,749 / −11 (production 4 file +444 / −11、test 4 file +1,316)。codex 子: plan 1、レンズ 2、author 2、review 2、fix 2、再 review 1 = 10 本
- 逐語: `verbatim/s2-plan.md`、`verbatim/s3-lens-a.md`、`verbatim/s3-lens-b.md`、`verbatim/s5-unit1.md`、`verbatim/s5-unit2.md`、
  `verbatim/s6-review-a.md`、`verbatim/s6-review-b.md`、`verbatim/s6-fix1.md`、`verbatim/s6-fix2.md`、`verbatim/s6-rereview.md`。
  brief は `s1-brief.md`、裁定は `s4-adjudication.md`、親の実測は `parent-measurements.md`、変異は `mutation-spec-probe.json` /
  `mutation-probe-out.json` / `mutation-spec-final.json` / `mutation-final-out.json`

## 中身

台帳配線 3 task 閉包の 6 段分割 `B1 → A → B2 → D1 → C → D2` のうち、**B2 (admission 層 read-only inspector) と D1 (契約・proof 型) の
terminal 証拠に依存しない部分**を unlanded checkpoint として積んだ。terminal に依存する部分 (coverage の全単射、`finished_at`、attempts projection の
`attempt_id`)、producer の配線 (単位 C)、consumer 3 面 (単位 D2) は実装していない。

| file | 内容 |
|---|---|
| `attempt_registry_core.py` (+81) | v5 proof の exact 7 field validator。`schema` / `registry_schema` は両方 exact literal、4 digest は hex64、`row_count` は bool を除く正整数、head は zero SHA 拒否。等値の実体は validator の保証にしない |
| `s8b_attempt_registry.py` (+231) | `capture_attempt_registry_prefix` / `inspect_attempt_registry_prefix`。root は `shared_admission_root` だけで解決 (provisioning / `_entry_paths` / write lock / fsync を呼ばない)、`_locked_readonly` 内で expected binding の exact 2 段 path だけを読む (兄弟世代を列挙しない)。v2 schema guard → genesis binding 照合 → 全行 replay の後だけ `len(rows) >= N` と `rows[N-1].event_sha256 == head` を比較 (D1337)。非保証 2 点を docstring に明記 |
| `s8b_floor_contract.py` (+27 / −6) | `LEGACY_RESULT_SCHEMA` (v4) / `RESULT_SCHEMA_V5` / `READABLE_RESULT_SCHEMAS`、schema 別 exact key 集合。**`RESULT_SCHEMA` の値は v4 のまま** (producer は単位 C が切り替える)。`result_keys_for_mode(mode, *, schema=<legacy v4>, perf_preflight)` は既存 12 呼出しと互換 |
| `s8b_floor_stats.py` (+94 / −5) | pure verifier: v4 は `attempt_registry` を exact key で拒否し expected 非 None を caller 契約違反として拒否、v5 は proof shape → `proof.freeze == artifact.freeze_sha256` / `proof.protocol == artifact.protocol_sha256` → 独立 proof との 7 field 等値。live wrapper: v5 のときだけ inspector を局所 import で呼び、binding は外部引数 (freeze / canonical protocol digest / canonical schedule digest) だけから作る。v4 では registry を一切読まない |
| test 4 file (+1,316) | proof 型 19 node、inspector 22 node (正例 N=1/3/4/5、valid append、unsafe 兄弟世代、read-only tripwire と bytes/inode 不変、負例: tail 破損 / chain 切断 / 再 chain 済み head 改竄 / N 超過 / 合成 v1 / binding 差替え / root 不在)、契約 (v4 key set literal pin、v5 = v4 ∪ {attempt_registry})、pure verifier と live wrapper (v4 不変、v5 正例負例、production validator の spy、実台帳 2 世代 A/B) |

## 1. 段 1 の brief が誤っていた 2 点と、plan・レンズが訂正した (P) 5 件

brief の件数 2 点が誤りだった (`result_keys_for_mode` の呼出しは 22 でなく **12** — insight 文書を含めて数えていた。`RESULT_SCHEMA` の production 6 file は
定義元を除いた raw word 数で、うち 2 file は別成果物の同名定数、意味的な閉包は 5 file)。段 2 plan が訂正し、両レンズが独立に確認した。

親の provisional 裁定 6 件のうち、(P1) producer は v4 のまま / (P4) `schema` は kw-only default = v4 で D2 の file を触らない / (P6) file 所有 2 本 は
そのまま採用、(P2) は「API を `s8b_attempt_registry` に置く」だけ採用され「admission が呼ぶ」は循環 import と direct import 禁止 meta-test
(`test_s8b_attempt_registry.py:1729-1775`) のため却下、(P3) は「genesis + start まで」が過小で **N=1 / 3 / 4 / 5 まで production adapter で到達可能**
(classification と observation-start に v2 拒否は無い) と訂正、(P5) は「1 wave」は維持しつつ実装子を 2 本並列にした (段 6 で後半が閉じなければ前半だけを checkpoint にする条件付き)。

## 2. レンズ 2 本が独立に見つけた blocker 3 件は、plan v2 が閉じた

1. **proof と artifact header の相互束縛が無かった** (A-1 / B-3)。現行 pure verifier は artifact の `freeze_sha256` / `protocol_sha256` を外部値と照合していない
   (親が現物で確認)。v5 で proof の 2 digest を header と直接比較する検査を足した (変異 M16)。
2. **read-only の root 解決が未規定で、自然な再利用先 `_entry_paths()` は root を provisioning して lock inode を作る** (A-3 / B-2)。
   `shared_admission_root` だけで解決し、provisioning / `_entry_paths` / write lock / fsync の tripwire と bytes / inode 不変 test を置いた (変異 M18)。
3. **兄弟世代の列挙は無関係な世代の破損で current prefix を拒否する** (B-1)。exact 2 段 path だけを読む形にし、unsafe な兄弟世代下でも受理する正例を置いた。

対立した 1 件: レンズ A は D1340 の世代横断予算 replay を inspector に入れよ (blocker)、レンズ B は世代列挙をやめよ (blocker)。親は **B を採り、A は scope 外**と裁定した —
D1340 は writer の規則で、既存 production reader も他世代を seed しない。検証時の再導出は要求外の gate (DW-G05)。非保証として docstring と本 README に明記し、
裁定パッケージへ送る (decisions fragment seq 10 の D 候補 `prefix-inspector-reads-exact-generation-only`)。

## 3. codex の子は 1 本も pytest を走らせられず、赤は親の実走で 1 度だけ出た

実装子 2 本・fix 子 2 本とも runner infrastructure `rc=16` (`child_started=false`) で未実走 (A2α と同型)。親が統合 tree で消費側 20 file を 3 回走らせた:
段 5 統合後 2,264 passed / fix1 統合後 **1 failed** / fix2 統合後 2,267 passed。唯一の赤は fix1 が新設した実台帳 2 世代 test の fixture が、世代 B の admission を
A と同じ campaign identity で予約して claim digest が衝突したもの (`measurement generation claim identity was unexpectedly reused`)。fix2 が B に固有 identity
(`run-b`) を与え、同じ claim directory に A / B の claim file が実在することを assert した。production は段 5 のまま (fix 2 巡は test 側のみ)。

## 4. 段 6 レビュー 2 本は production を「裁定どおり」と判定し、所見は全件 test 側だった

blocker は両者とも M14 の実台帳 2 世代 test の欠落 (段 4 裁定が段 6 で足すと定めたもの)。must-fix は unit2 の v5 test が production validator を常時 stub していた
(D1522 partial)、契約の不変 pin node への行追加、M10 が recovery policy gate に遮られる、M13 が validator に遮られる、複数 gate に掛かる負例。fix1 が 7 件を閉じ、
焦点再レビューは **closed 7 / partial 0 / regressed 0**。再レビューの残り must-fix 2 件は工程項目 (fix1 patch と最終 tree の 42 行差 = fix2 の delta、commit から
総和 patch を再生成 / M15 の赤 node 完全集合は probe で実測)。

## 5. 変異 matrix — 17 変異、本走 rc=0、**17/17 KILLED**、期待 node 集合と完全一致

checkout `a0ac63690`、`tools/mutation_harness.py` (dispatch、D612 上書き 3600/600)、runner = 所有 test 4 file `-q -rf`。
probe (全件 SURVIVED 登録) で観測 node の完全集合を集め、本走は KILLED 期待 = その集合 (DW-M08) で走らせた。
probe 第 1 走は M9 で dispatch の queue 待ち 900 s (rc=16) に当たり harness が停止、`--resume` (sidecar を attempt-2 へ複写、wrapper-attempt 2) で残り 10 件を回した。

| ID | 変異 | 結果 | 観測 node 数 (代表) |
|---|---|---|---|
| M1 | proof validator の exact key 検査を削除 | **KILLED** | 2 (`test_attempt_registry_prefix_proof_rejects_extra_key` ほか) |
| M2 | validator の freeze_sha256 を hex64 検査なしで通す | **KILLED** | 2 (`test_attempt_registry_prefix_proof_rejects_each_field_type[digest-freeze-sha256-int]` ほか) |
| M3 | row_count > 0 を >= 0 へ | **KILLED** | 1 (`test_attempt_registry_prefix_proof_rejects_zero_row_count`) |
| M4 | zero head 拒否を削除 | **KILLED** | 2 (`test_attempt_registry_prefix_proof_rejects_zero_head` ほか) |
| M5 | 最初の parse 失敗で止まる寛容 decode (tail 破損を無視) | **KILLED** | 1 (`test_attempt_registry_prefix_rejects_malformed_tail_after_n`) |
| M6 | chain 検査なしの decode-only replay | **KILLED** | 3 (`test_attempt_registry_prefix_unrecomputed_prefix_tamper_reaches_chain_gate` ほか) |
| M8 | rows[N-1] の head 比較を削除 | **KILLED** | 2 (`test_attempt_registry_prefix_rejects_reported_head_tamper` ほか) |
| M9 | rows[N-1] → rows[-1] (末尾一致) | **KILLED** | 1 (`test_attempt_registry_prefix_inspection_accepts_valid_later_append`) |
| M10 | v2 schema guard を v1/v2 許容へ緩和 | **KILLED** | 1 (`test_attempt_registry_prefix_rejects_synthetic_v1_at_generation_path`) |
| M11 | v5 key set から attempt_registry を落とす | **KILLED** | 13 (`test_v5_rejects_artifact_header_freeze_tamper` ほか) |
| M12 | pure verifier の reported/expected 等値比較を削除 | **KILLED** | 3 (`test_v5_rejects_reported_prefix_head_tamper` ほか) |
| M13 | live wrapper の v5-only guard を削除 | **KILLED** | 2 (`test_live_verifier_rejects_result_v4_unexpected_top_level_key` ほか) |
| M14 | expected binding を reported proof から採る | **KILLED** | 2 (`test_live_v5_calls_inspector_and_compares_reported_to_independent_proof` ほか) |
| M15 | v4 key set へ attempt_registry を足す | **KILLED** | 52 (`test_official_perf_present_keeps_legacy_exact_shape` ほか) |
| M16 | proof.freeze == artifact.freeze の検査を削除 | **KILLED** | 2 (`test_v5_rejects_artifact_header_freeze_tamper` ほか) |
| M17 | registry_schema の literal 検査を緩和 | **KILLED** | 1 (`test_attempt_registry_prefix_proof_rejects_wrong_registry_schema`) |
| M18 | root 解決を provisioning 入口 (_entry_paths 同型) へ | **KILLED** | 3 (`test_attempt_registry_prefix_rejects_unavailable_root_without_provisioning[lock]` ほか) |

- 段 4 の事前登録から外したのは M7 (長さ検査単独の削除は直後の添字アクセスで拒否が残り単一理由にならない)。M2 は共有 `_digest` でなく validator 内の 1 field 呼出しへ再照準した (共有 helper の変異は完全集合が広すぎる)。
- M15 (v4 key set 変異) の 52 node は v4 verifier 全体が早期 key mismatch で赤になる完全集合であり、下層契約の受理集合拡大が上層だけに帰属しないことを示す (D1522、レンズ A の must-fix 7)。
- M11 の 13 node、M12 の 3 node、M13 の 2 node、M14 の 2 node (fake inspector 版 + 実台帳 2 世代版) は、段 6 レビュー B の帰属表と再レビューの再照準 (M10 は production scheduler authority の合成 v1、M13 は validator seam) どおり。
- 過剰拒否の正例 (DW-M01): M9 (末尾一致へ退行) は valid append の正例 1 node だけで KILLED。v4 artifact の受理不変は M13 / M15 の観測集合が `test_live_v4_does_not_call_attempt_registry_inspector` 等の v4 正例を含むことで裏取りした。

## 6. 検査の実測

`parent-measurements.md` が一次資料。要点: 焦点走 20 file は fix2 統合後 2,267 passed / rc=0。受入全走 (tested_tip `b54836171`) は **child-green、20,699 passed / 68 skipped**、fingerprint 一致、lease は release 済み。全史 provenance は実装 commit 後 8,246 件・受入後 8,259 件とも新規違反なし。

## 7. 閉じていない窓

- **他世代の予算超過は inspector が検査しない。** writer (単位 A の横断予算) の防壁に委ねる。検証時の再導出は裁定パッケージ 1。
- **台帳の削除後に同一 bytes で再作成されると検出しない (D1533)。** inspector の docstring に明記。成果物側への明記の所有者は単位 C (裁定パッケージ 3)。
- **v5 の gate は production で発火しない。** producer は v4 のまま、`launch_floor_attempt()` の production 呼び手は 0 件。D1114 / D1341 が予定する状態であり「効いている」と書いてはならない。
- journal の TOCTOU 窓、`marker.use(action=...)` 例外時の staging 残置、合成 2 段 v1 残骸の受理、B1 の 5 件は前 wave から未裁定のまま。

## 8. ユーザーへ返す裁定パッケージ

1. 検証時に freeze-wide の予算超過を再導出するか (レンズ A の blocker 4)。本 wave は writer の防壁に委ね、非保証として明記した。
2. coverage の exact signature は単位 C の terminal 証拠契約の後に固定する (レンズ A の裁定候補 10)。段 2 plan の signature は意味要件に格下げした。
3. D1533 の非保証範囲を成果物 (`result.md`) へ載せる所有者を単位 C の brief に置く (レンズ A の裁定候補 11)。
4. D2 が candidate を v5-only にするとき、`s8b_v2_freeze_fixture.py:340` / `test_s8b_ratified_verify.py:460` の動的 `RESULT_SCHEMA` 参照を legacy v4 へ固定するか v5 proof を組み立てるか (レンズ B)。
5. 単位 C が supersede する pin: `test_s8b_floor_contract.py:180` (v4 → v5)、`test_s8b_floor_campaign.py:6552` (producer v5 正例)。`test_s8b_floor_stats.py:596` は legacy 正例として維持。
6. A1' / A2α / A2β から持ち越した裁定パッケージ (合成 2 段 v1 残骸、B1 の 5 件) は未裁定のまま。

## 9. 次 wave の出発点

- **次段は単位 C (起動層の実際の呼び手を v2 台帳へ繋ぐ)。** C の brief は terminal 証拠の契約 (A2β 7 節の 2) を先に固定し、その後に B2 / D1 の terminal 依存部分
  (coverage の全単射、`finished_at`、attempts projection) と D2 (consumer 3 面) を置く。producer capture は `capture_attempt_registry_prefix` を launcher の thin wrapper から呼ぶ。
- branch `worktree-dev-wave-t1851-unit-a` を継承し、main を取り込んでから着手する。継承元の状態は本 README が正本で、job dir handoff ではない。
- 6 段すべてを積んだ後に D1341 に従って 1 変更単位で land する。
