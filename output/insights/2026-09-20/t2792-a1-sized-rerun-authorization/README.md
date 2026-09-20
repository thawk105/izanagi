# [T-2792] A-1 sized attempt-0002 を exact な認可 record で投入可能にする択 1 の実装 (D2172 項 2、rear gate + 公開先 gate + producer + 追補) (2026-09-20)

- authority: none
- default_effect: no-state-change
- ユーザー裁定: D2172 項 2 (2026-09-20、第 24 回 /rulings 項 2、「推奨通りで」)。逐語は `verbatim/T-2792-origin.md` (依頼文) と
  `docs/decisions.md` D2172 項 2。前提の裁定 = D2156 (2026-09-19、gate を緩めずに裁定パッケージへ返す)、一次資料
  `output/insights/2026-09-19/a1-sized-attempt2/README.md` §7 (択 1〜3、推奨 = 択 1 を 1 attempt 限定)。
- 対象 study: `paper-story-a1-20260901-balanced5-sized-v1` (policy sha `a6228bcd…`、事前登録 sha `6047eff0…`)。attempt-0001 は 2026-09-18 に
  bench 到達済みで、現行 gate は同 study の attempt-0002 を拒否する (D2156、本 wave でも read-only 実走で再確認)。
- **本 wave は実装と追補だけを行った。投入・測定・results 稿・図は行っていない** (別 wave)。実 durable base
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement` には 1 byte も書いていない。
- 起点 local main `371674ea685ecb11e08dbcc31d4bf4f2bed0b20b`。実装 commit `886c19259` (Codex author)、追補 commit `ec696308a` (docs)。

## 1. 結論 (1 行ずつ)

1. **rear gate `_assert_no_prior_v3_bench_start` は、durable base の exact な認可 record と driver 側の定数 1 件
   `V3_SIZED_RERUN_AUTHORIZATIONS = {(sized study, "attempt-0002", "attempt-0001", "D2172", 2, "2026-09-20")}` が一致し、record の
   `source_commit` が投入時の HEAD と一致するときに限り、先行 attempt-0001 に対する「bench 到達後の group 再投入禁止」だけを解除する。**
2. **それ以外はすべて従来どおり拒否する** — record 不在、別 attempt 名 (定数側・比較側)、別 study (定数側・比較側)、別 source sha、裁定 3 field の不一致、
   self digest 不一致、symlink / 非 regular、余分・欠落 key、壊れた JSON、attempt-0001 以外の同 study の先行 attempt の bench 到達。
   不一致 record は「無視して従来動作」ではなく**拒否**する。
3. **保存したもの (規律 2):** 先行証拠の完全性検査 (corrupt / unsafe の raise) と study differs の拒否は record の有無・認可の成否と無関係に走る。
   intent / attempt root / 受領証 namespace の再使用拒否、公開先の create-only と親 dir 実在、anomaly 即 reject (materialize の observation
   consumer は公開先 gate より前) は diff 上 1 byte も変わっていない。非認証 lane (`formal=false` / `promotion_prohibited=true`) も不変。
4. **公開先 gate `_exact_materialization_destination` は、一致 record を持つ attempt に限り兄弟 dir
   `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002` を受理する** (record 不在 = 従来の exact leaf のみ、不一致 = 拒否)。
   attempt-0001 の leaf 配下には置かない。
5. **record の producer** = driver の subcommand `authorize-rerun` (`--study-id --attempt-root --expected-head --decision --decision-item --decided-on`、
   全必須)。定数 membership・intent / attempt root / record の不在・既存 base を要求し、`_exclusive_write` で create-only に書く。
6. **事前登録 §6.1 / §6.4 の追補 (別版)** は `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md` (commit `ec696308a`)。
   将来の attempt-0002 一件に限る。元の事前登録・policy・契約 v2・source 追補の bytes、attempt-0001 の判定・限定 L-A1S-4 は不変 (遡及しない)。
   erratum の名で正当化しない。束縛は source commit 経由 (契約 JSON / policy に sha を足さない)。
7. **実測:** 実 base の複製 (job dir、attempt-0001 の intent + barrier/** を path 書換・digest 再計算) に対し、patch 後の gate は record 無し = 拒否、
   exact record = 受理、不一致 9 種 = すべて拒否 (§4.1)。計算ノード焦点走 (11 file、commit `886c19259`) = **1697 passed / 0 failed / 6 skipped** (§4.2)。
   変異 matrix は §5。
8. **投入は本 wave に含めない。** land 後、fresh submit-tree の HEAD を `source_commit` にして `authorize-rerun` で record を置き、`submit` する別 wave が要る
   (順序: 全成果物の land → fresh submit-tree → record → submit)。

## 2. 裁定と scope

- 段 1 brief (`verbatim/s1-brief.md`): P1〜P7 の provisional 裁定。段 4 (`verbatim/s4-adjudication.md`) で確定: P1 は定数に先行 attempt 名を加える (consult A1)、
  P2 は digest helper を別設、P3 兄弟公開先、P4 producer subcommand、P5 解除は候補 = attempt-0001 に限定、P6 不在 = 従来 leaf / 不一致 = 拒否、
  P7 追補は「将来の attempt-0002 一件」「§6.4 本文不変」「遡及なし」「L-A1S-4 は解除しない」「追補専用の実行時検査は無い」を明記。
- scope 外 (触れていない): 投入・測定・results 稿・図・`docs/paper-story/README.md` の表、job shell、policy / 契約 / 事前登録 / source 追補の bytes、
  pilot 経路、formal lane、trial registry、D2096 項 5 (3 study 目の枠組み)、汎用の認可管理 (複数 record・registry・将来 attempt)。

## 3. 実装 (commit `886c19259`、4 file、+611 / −8)

| file | 変更 |
|---|---|
| `orchestrator/campaign/paper_story_a1_paired.py` (+146 / −3) | 定数 (`V3_RERUN_AUTHORIZATION_SCHEMA`、key 集合、`V3_SIZED_RERUN_AUTHORIZATIONS`)、reader `_exact_v3_rerun_authorization` (不在 None / unsafe / corrupt / differs)、`_rerun_authorization_digest`、gate の `source_commit` kwarg と `released` 条件 (末尾 2 箇所だけ)、`_run_submit_v3` の配線、公開先 helper の keyword 3 引数と `_run_materialize_v3` の配線、`run_authorize_rerun` + parser / main |
| `orchestrator/tests/test_paper_story_a1_paired.py` (+396 / −3) | fixture 5 本 (record 生成は producer を使わず独立算出の digest)、gate 11 関数、公開先 5 関数 + 既存 test への assert 追加、producer 4 関数。既存 gate test 3 本は `source_commit=` 追加と docstring のみ (期待値不変) |
| `orchestrator/tests/test_paper_story_a1_job_contract.py` (+73) | submit 配線 2 関数 (`_v3_submit_cli_fixture(study_id=sized, attempt_name="attempt-0002")` を台に、正例は実 `run_submit` → 実 reader / gate → 実 intent 作成 → `_run_qsub` 捕捉 3 回。負例 4 case = record 不在 / 別 source / 一致 record + 既存 intent / + 既存 attempt root は qsub 0 回・intent 非作成) |
| `orchestrator/tests/test_ccbench_spawn_sites.py` (+2 / −2) | deferred gate 台帳の driver sink `<module>.run_measurement` の行番号 pin 7428 → 7545 (挿入への追随、2 箇所)。種類・scope・件数は不変 |

新 test は 22 関数 (静的 52 case)。fixture が stub する層 (配線 test): policy-ready、CCBench、git、durable base、hostname、qsub、qstat visibility →
証明対象は **scheduler 境界までの配線**であり、実 scheduler の受理・fresh submit-tree の全前提・測定成立の証明ではない。

## 4. 実測

### 4.1 実 base とその複製での gate 実走 (login、read-only)

- 現行 gate (patch 前) を実 base に実走: 同 study の attempt-0002 は `prior attempt reached the bench barrier; group rerun is prohibited`、
  別 study は受理 (`verbatim/probe-gate-current.log`)。
- 複製 (`replica-base/`、`verbatim/make_replica_base.py.txt`): 実 base の `attempt-0001.intent.json` と `attempt-0001/barrier/**` を job dir へ複製し、
  `attempt_root` と bench-go の `ready[].path` を複製 path へ書き換え、`intent_sha256` を再計算、bench-go の `ready[].sha256` を書換後の ready file で再計算。
  現行 gate は複製でも同じ拒否 (`verbatim/probe-gate-replica-current.log`) → 先行証拠の field 検査を通ることの証拠。
- patch 後の gate を複製に実走 (`verbatim/replica-dogfood-post-fix1.log`、`verbatim/probe_gate_replica_post.py.txt`): record 無し = 拒否、
  exact record = **ACCEPTED**、別 source / 別 study / attempt-0003 を名指す root / decision item 3 / decided_on 違い / 破損 digest / 余分 key /
  caller 別 study / caller 別 source = すべて拒否 (理由 message は record の field 別)。
- **証明範囲の限定 (review B-N4):** これは gate 単体の受理 / 拒否であり、qsub 到達・materialize 全工程・実 scheduler の証明ではない。
  複製は gate が実際に検証する field を満たすが、completion / materialize の厳密な digest 検査までは満たさない (bench-start の digest は形式検査のみ)。

### 4.2 焦点走 (計算ノード dispatch、gen_S)

| 走 | commit / 状態 | 対象 | 結果 |
|---|---|---|---|
| request 12491.nqsv | 886c19259 相当の未 commit 差分 (author patch 適用) | 変更 3 file + consumer / メタ 8 file (spawn_sites、official_perf_closure、a1_headline、p3_exploration_namespace、p3_build_authority_cli、pegasus_tools、hooks、campaign、a1_non_certifying_marker) | 1695 passed / **2 failed** / 6 skipped (96 秒)。赤 1 = `test_existing_a1_non_touch_manifest_is_empty_from_base` (作業木の未 commit 差分を見る検査、自分起因)。赤 2 = `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` (台帳の lineno pin 7428 が挿入で 7549 へ移動) |
| request 12519.nqsv | **commit `886c19259`** (fix1 込み) | 同 11 file | **1697 passed / 0 failed / 6 skipped** (97 秒) |

- Codex author / fix1 は sandbox 内の dispatch が qstat preflight で rc=16 (`child_started=false`)、login の直接 pytest は guard 拒否 → 「実装済み・未実走」で報告し、
  実走は親が dispatch した (上表)。
- consumer test は変更 symbol (`_assert_no_prior_v3_bench_start` / `_exact_materialization_destination` / `_parser` / `main`) の参照で引いた (DW-O26): 参照は
  変更 2 test file のみ。driver を import / path 参照する test file 11 本を焦点集合にした。

## 5. 変異 matrix (独立 clone `mutation-source` @886c19259、計算ノード dispatch、2 test file 全走)

- spec: probe `mutation-spec-probe.json` (sha `3e3f65e03ea46ca249f7700c110294cf637877e7c4291f7cec9c64cdae2b6708`、全件 SURVIVED 登録で観測 node を収集) →
  final `mutation-spec-final.json` (sha `f271043373ff97f691ada28908d9a1ded25b023172d6d4857ca62a967ae887e0`、期待 node = probe の観測 node の完全集合)。
  生成器 `make_mutation_spec.py` (job dir)、anchor は 15/15 一意 (M11 は context 行で一意化)。runner = `tools/run_tests.py --force-dispatch
  test_paper_story_a1_paired.py test_paper_story_a1_job_contract.py -q -rf`。
- **final: baseline PASSED (32 s)、14/14 KILLED (期待 node 完全一致)、M0 SURVIVED、MISMATCH 0、TIMEOUT 0** (`mutation-final-results.json`、
  schema `izanagi-dev-wave-mutation/v4`、tool sha `5bcc211b…`、runner sha `eb853f77…`)。probe (`mutation-probe-results.json`、sha `6c736503…`) は
  設計どおり負例 14 件が SURVIVED 登録に対し MISMATCH (= 赤 node あり)、観測 node は final と同一。final の spec と結果 JSON (sha `c182d432…`) は
  本 dir `verbatim/` に複製 (原本は job dir)。

| id | 変異 (driver) | 期待 (段 4) | 赤 node (final、完全一致) |
|---|---|---|---|
| M0 | reader の `if not os.path.lexists(path)` を `is False` に (等価) | SURVIVED | — (SURVIVED) |
| M1 | record 不在で `None` の代わりに定数 tuple を返す | rejects_absent_record | paired `rejects_absent_record`、paired `rerun_materialization_rejects_sibling_without_record`、job_contract 配線負例 `[absent]` (3) |
| M2 | 定数 membership から attempt 名を外す | rejects_other_attempt[attempt-0003] | paired `rejects_other_attempt[attempt-0003]` (1) |
| M3 | `attempt_root` の比較を除去 | rejects_other_attempt[attempt-0002] | paired `rejects_other_attempt[attempt-0002]`、`rerun_materialization_rejects_mismatched_record[attempt]` (2) |
| M4 | 定数 membership から study を外す | rejects_other_study[pilot] | paired `rejects_other_study[pilot]` (1) |
| M5 | `study_id` の比較を除去 | rejects_other_study[sized] | paired `rejects_other_study[sized]` (1) |
| M6 | `source_commit` の比較を除去 | rejects_other_source | paired `rejects_other_source`、`rerun_materialization_rejects_mismatched_record[source]`、job_contract 配線負例 `[source]` (3) |
| M7 | 定数 membership から decision id を外す | rejects_other_decision[id] | paired `rejects_other_decision[id-D2173]`、`rerun_materialization_rejects_mismatched_record[decision]` (2) |
| M8 | self digest の照合を除去 | rejects_bad_digest | paired `rejects_bad_digest`、`rerun_materialization_rejects_mismatched_record[digest]` (2) |
| M9 | `released` なら候補 loop を検査前に `continue` (完全性検査 skip) | preserves_prior_integrity | paired `preserves_prior_integrity` (1) |
| M10 | `released` の条件から `prior == base/attempt-0001` を外す (全候補を解除) | rejects_other_prior_reached_bench | paired `rejects_other_prior_reached_bench` (1) |
| M11 | 公開先 helper の `lexists` 拒否を除去 (create-only 解除) | rejects_existing_sibling | paired `rerun_materialization_rejects_existing_sibling`、既存 `test_materialization_is_exact_leaf_and_noreplace_publish` (fix1 で assert 追加) (2) |
| M12 | `attempt` 指定時は record 不在でも兄弟 path を expected に | rejects_sibling_without_record | paired `rerun_materialization_rejects_sibling_without_record` (1) |
| M13 | producer (2 hunk): record の `lexists` 事前検査を除去 + `_exclusive_write` を上書き書込に | authorize_rerun_is_create_only | paired `authorize_rerun_is_create_only`、`authorize_rerun_rejects_existing_namespace[record]` (2) |
| M14 | `_run_submit_v3` が gate へ `source_commit="b" * 40` を渡す (配線) | 配線負例 [source] | job_contract `test_v3_submit_reaches_qsub_with_exact_rerun_authorization`、配線負例 `[source]` (2) |

- 1 理由性: 各変異の赤 node は狙った述語 (record 不在 / attempt 名 定数側・比較側 / study 定数側・比較側 / source / decision / digest / 完全性 / 先行 attempt の限定 /
  create-only / record 無しの兄弟 / producer の再作成 / 配線) に帰属し、同じ理由を consumer 層 (materialize の record 照合、submit 配線) が重ねて検出した分が
  node 数 2〜3 になっている (別理由の過剰決定ではない)。M13 は 2 hunk とも要る (片側除去は `_exclusive_write` / 事前検査に mask される、review B)。
  M11 は destination helper の拒否保存を検証するもので、公開処理 (`_publish_staging_noreplace`) の no-replace 解除の証明ではない (既存 test が別に持つ)。
- 既存 test でも落ちる変異は M11 の `test_materialization_is_exact_leaf_and_noreplace_publish` (fix1 で assert を足した既存 test) だけで、新規検出力には
  数えない (登録時に確認)。

### 4.3 記録前の機械走査

- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、job dir `three-axis-scan-1.log`): **本 wave の file は 0 hit**。走査自体は rc=1
  (rr80 / rr20 の holdout hit 各 4 件) だが、その 4 file は本 wave 以前に main へ入った T-2724 chain の freeze v2 g1 候補
  (`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、`4d8fb93b7`) と official 床値校正 (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/`、
  `cc82edc8c`) であり、本 wave は触れていない (walkthrough: 起点 `371674ea6` に既に含まれる)。defang・erratum の対象は本 wave には無い。
- `tools/check_docs.py` 違反なし (追補 commit 前と記録 commit 前の 2 回)。provenance は message-file 検査を各 commit 前に、range 監査を記録 commit 後に行う。

## 6. 相談・レビューの裁定

- 段 3 consult (`verbatim/s3-consult.out.md`、2 レンズ + 全層到達性): **must-fix 2 = A1 (認可対象は限定されるが解除する先行証拠が限定されていない → 定数に
  `attempt-0001` を固定し、他の先行 attempt は拒否) / B1 (配線 test は intent 前の sentinel でなく `_run_qsub` 捕捉まで)**、should 3 (追補は例外追加を明記、
  保存条件は producer と consumer を分ける + anomaly は既存 test を明示、変異の単位)、nit 3 (行番号補正、brief の実測の限定、並行 wave)。全件採用 (refuted 0)。
  全層到達性: job shell / measure / lock preseed / barrier / complete / materialize に先行 attempt を理由とする他の拒否なし。trial registry 内部は親が読了
  (`_validate_a1_projection_fields` / `issue_a1_registered_noncertifying_projection` は field 検査のみ)。`ident.py` 内部は未読 (output root は attempt 別)。
  「残る拒否層なし」は読んだ範囲での結論であり全層の断定ではない。
- 段 6 review A (正しさ境界) / B (過剰・削除): **must-fix 各 1 = 同一 (spawn-site 台帳の lineno)**、受理集合の逸脱・I3 の緩和・非認証 lane の変更は両者とも
  発見なし。should / nit の裁定と fix1 の対応表は `verbatim/s6-adjudication.md`。焦点再レビュー子は起動せず (must-fix は機械的な lineno 追随 1 件で焦点走 12519 の緑で閉じた)。
- anomaly 即 reject の「不変」の根拠 (review B-B2): 既存 test (paired test の collector anomaly gate と sidecar consumer)、driver の observation anomaly 検査、
  materialize の observation consumer が公開先 gate より前 — いずれも本 wave の diff に無く、認可による早期 return も無い。
- 被覆の限界 (review A): 認可ありでの study differs 各分岐 (旧 2805 / 2848 / 2898 行) は個別 test でなく diff による保存確認。

## 7. 言わないこと・限界

- **投入も測定もしていない。** attempt-0002 の測定値・稿・図は存在しない。A-1 の充足・formal 化・昇格は判定しない。L-A1S-4 は残る。
- 認可 record と self digest は破損検出であって署名ではなく、「認可者が性能値を見た後の選択」を防ぐ装置とは称さない (D2172 項 2)。
- 追補 file 自身を実行時に digest 検査する仕組みは無い (束縛は source commit 経由)。
- 配線 test は scheduler 境界までの証明。実 base への書込・実投入は行っていない。
- 「driver に live な bytes pin 無し」は「変更前 driver の固定 hash に更新不能な形で束縛されていない」の意味に限る (実行時は source binding で
  bytes を記録・照合する)。「別 study は受理」は gate 単体の実測であり、別 study の submit 全体の受理ではない。
- consult の指摘どおり、intent が名指す実在 prior root は barrier が無くても候補になり unsafe で拒否される (brief の「barrier を持たない entry は候補にならない」は
  `.intent.json` の無い entry についてのみ正しい)。

## 8. 一次資料

- 本 dir `verbatim/`: brief、plan (prompt / out)、consult (prompt / out)、段 4 裁定、author (prompt / out)、review A / B (prompt / out)、fix1 (prompt / out)、
  段 6 裁定、依頼文、probe log 3 本、複製・dogfood script (`.py.txt`)、変異 spec (final) と結果 JSON。
- 可逆最小正規化 (D88、`git diff --check` 抵触): `verbatim/s3-consult.out.md` の 183・184 行末の空白 2 個 (markdown の強制改行) を除去した。
  原文 (job dir `codex/s3-consult.md`) の sha256 `087e4009580611b6fa8b442bc2f3c305ada38c72b0b93ab35c47bc02063c096b`・21657 byte、正規化後
  `45039dfb933429a9e88b8cb5ccb224cc33f68f6abb66bc48ead9f9bda438300d`・21653 byte。復元 = 当該 2 行の行末に空白 2 個を戻す (可視文字不変)。
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/` (原本: HANDOFF、launcher、focus log、変異 spec / 結果、replica-base、codex receipt)。
- 実装 patch は commit `886c19259` (unit worktree `.codex/worktrees/t2792-unit-impl`、branch `dev-wave-t2792-unit-impl` → `dev-wave-t2792-unit-fix1`)。
- 裁定: D2172 項 2、D2156、D2120 項 3、D2096、D1993 項 6、事前登録 §6.1 / §6.4 / §7.2。

## 9. 段の記録 (dev-wave)

- 段 1 brief (親、実測: 現行 gate の実 base 実走・pin 閉包・base 走査箇所・公開先 gate) → 段 2 plan (codex read-only) → 段 3 consult (codex、1 本 2 レンズ +
  全層) → 段 4 裁定 (親) → 段 5 author (codex workspace-write、unit worktree) → 段 6 review A / B (codex) + fix1 (codex) + 親の焦点走 2 走 + 変異 →
  段 7 記録 → 段 8 → 段 9。
- codex 子 = plan 1、consult 1、author 1、review 2、fix 1 (計 6 本)。計算ノード job = 焦点走 2 + 変異 (probe + final) + 受入。
