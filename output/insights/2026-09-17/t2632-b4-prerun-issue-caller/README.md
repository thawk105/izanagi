# [T-2632] B-4 prerun publication の production 呼び手 — 現物では候補 0、発行器は typed に拒否、封印 receipt は未取得

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t2632-b4-prerun-issue-caller` (branch `worktree-dev-wave-t2632-b4-prerun-issue-caller`、
起点 local main `1042a1bc9`) の一次資料を凍結したものである。

- 実測日時: 2026-09-17 01:38 JST (現物への実発行の試行)
- 機体: `pegasus02` (login node)
- 実装 commit: `2d71a0454` (Codex `role=author`、Claude `role=integrator`)
- 現物: `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387` / `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` /
  `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` (wave worktree 内の checkout、相対 path で指定)

## 結論

1. **発行器 `issue_b4_prerun_publication` の production 呼び手が repo に入った** —
   `orchestrator/campaign/p3_b4_prerun_caller.py` (`python3 -m orchestrator.campaign.p3_b4_prerun_caller --campaign-root ...`)。
   本 wave 前は tests 以外の呼び手が 0 件だった。
2. **現物 3 campaign に対する実発行の試行は、発行器まで到達して typed に拒否された。封印 receipt は得ていない。**
   rc=2、`reason = "design_not_feasible"`、`detail = "fewer than 201 eligible scheduled attempts"`、
   `candidate_count = 0`、campaigns = base 4 行 / sort 1 行 / trigger 2 行 (全 `success`)。stderr 空。
   `output/b4-prerun-publication` は実行前後とも不在で、作業ツリーは clean のまま (発行器は manifest 生成の
   拒否が `_publish_bundle` より前に起きるので root を作らない)。
3. **前 wave README (`output/insights/2026-09-16/t2632-b4-red-precursor-stock/README.md`) の「次の一手」項 1
   「封印発行は項 2 と独立に閉じられる」は、封印 receipt の取得については成立しない。** 発行器は適格行が 201 未満なら
   `design_not_feasible` で拒否する (`p3_b4_prerun_issuer.py` の `generate_analysis_manifest` 呼出し直後、
   `p3_b4_analysis_ledgers.py` の `generate_analysis_manifest`、test
   `test_fewer_than_201_eligible_is_typed_before_root_creation`)。適格行には項 3 (自然赤) と項 2 (真偽値の根拠) の
   両方が要る。独立に閉じられたのは **production 経路の実在** だけである。旧稿は書き換えず、本書で追補する。
4. **T-2632 の適格在庫は 0 件のまま増えていない。** 本 wave は在庫確保の軸では前進していない。

## 何が足りないか (現物から `B4ScheduledAttemptInput` を組めない理由)

現物の候補行 (`whiteboard[].result == "rejected"`) は 0 件だが、仮に 1 件あっても、17 field のうち次の 12 は
**現行の保存形式に出所が無い**。checkpoint (`loop_state.json`) の whiteboard 行は
`iteration / direction / magnitude / result / delta_pct` の 5 field だけで、これは D39 決定 3 のリーク遮断として
意図的に落とされている (D1846 が確認)。`runs/wal.jsonl` は genome と src_token を持つが proposal document を持たない。
これは保存形式の既知の制限に基づく静的分類であり、個別 artifact を探索した結果ではない (呼び手の docstring と同じ)。

| field | 出所が無い理由 |
|---|---|
| `attempt_id` | whiteboard の iteration から B-4 attempt 同一性への対応規約が無い |
| `block_id` | precursor を B-4 block へ割り当てる artifact が無い |
| `digest_red_classes` | checkpoint に WAL の digest 証拠へ結合する key が無い |
| `workload` | precursor に校正済み workload が束縛されていない |
| `calibrated_workload_member` | 事前登録 §5 の「校正済み `PerfConfig`」欄が未記入 |
| `initial_proposal_sha256` | whiteboard も WAL (genome / src_token) も proposal document を保持しない。genome からの再構成は D1846 の定義 (document exact value の canonical JSON sha256) と同じ対象でない |
| `bootstrap_member` | 事前固定した bootstrap 集合への所属証拠が無い。**「発行 batch に含めた行は真」とみなす案 (親の P1) は述語を恒真化するので採らない** (段 3 A1、段 4) |
| `reference_tps` / `reference_snapshot_hash` / `reference_receipt_hash` | 祖先 certified snapshot と throughput receipt が一意に特定されていない (§5 の `env_tag` 欄が未記入) |
| `reference_is_unique` | 祖先関係・同着の不存在・`PerfConfig` / `env_tag` 一致の照合根拠が無い |
| `arm_digest_received` | attempt 単位で digest の受領 / 非受領を記録する artifact が無い (lock の `reflux: "on"` は根拠にならない) |

構成可能なのは `schema_version`、`registry_ordinal` (argv 順 × whiteboard 配列順)、`driver`
(`campaign.lock.trial` の exact 3 行表)、`reason = SCHEDULED`、`whiteboard_result` の 5 つだけである。
呼び手はこれらから行を作らず (作っても発行器の `_validate_attempt` で残り 12 が要る)、候補が 1 件でもあれば
`scheduled_input_sources_missing` で止まり発行器を呼ばない。

## 封印 receipt を得るまでに要るもの (依存の書き直し)

段 3 レンズ B の所見 4 のとおり、前 wave README の「自然赤 + §5 の 2 欄」は十分条件ではない。receipt には少なくとも次が要る。

- 凍結述語 (§5.1.1) を満たす 201 件以上の赤 precursor (供給源は合成ループ campaign の whiteboard、D1936 項 8)
- 予定 attempt の集合・順序と、attempt / block / 元の走行の対応
- 初期 proposal の exact value と、事前固定した bootstrap 集合への所属根拠 (**集合の定義と固定時点は未裁定**)
- 校正 workload、祖先の一意な参照点、digest 非受領の根拠 (§5 の 2 欄と、それを precursor へ結合する証拠)
- 全 scheduled attempt (適格 201 行だけでなく発行器へ渡す全行) に対応する planned result path

```text
最小呼び手・不足報告 (本 wave) ─────────────────┐
§5 の校正・環境根拠 ─┐                          │
通常の自然 precursor 供給 ─┼→ 適格性の確認 ───────┤
proposal 等の対応証拠 ───┘        │              │
                                  ├→ 少数: 記述報告まで (D1986 項 4)
                                  └→ 201 適格行 + 全予定入力 → 封印発行 (本 wave の呼び手) → §6 の他条件 → formal 実走
```

これは新規 campaign 起動や耐久 carrier 新設の認可ではない (D1936 項 8 / D1986 項 4 で不採用の供給増加基盤・n 削減は再提案しない)。

## 呼び手の形 (段 4 裁定 plan v2、段 6 で fix)

- argv は `--campaign-root PATH...` だけ。publication root は実行時に発行器と同じ checkout
  (`issuer._REPOSITORY_ROOT / "output/b4-prerun-publication"`) から解決し、呼び手は選べない (D1881)。
- 候補は `result == "rejected"` の exact 一致だけ。`fail` / `success` は候補にしない。`rejected` だけを候補にするのは
  供給源を赤 precursor に限る依頼によるもので、registry が SUCCESS を受理しないからではない
  (前 wave の親 brief N5「成功 precursor は行にならない」は誤りで、台帳型は SUCCESS を受理し manifest の適格性で除く)。
- 候補 ≥ 1 → 12 field × 候補数の欠落を全件集計して `scheduled_input_sources_missing` (rc=2、発行器 0 回)。
  候補 0 → 空 batch で発行器を **ちょうど 1 回** 呼ぶ。発行器の例外は `reason` / `detail` (`str(exc)` から
  `"<reason>: "` 接頭辞を除去。`B4PrerunIssuerError` に `.detail` 属性は無い)。成功時だけ rc=0 で
  `receipt_path` / `receipt_sha256` / `issuer_commitment_sha256` / `manifest_row_count`。
- checkpoint / lock の不在・JSON 不正 (深い入れ子の `RecursionError` を含む)・whiteboard 非 list・未知 `trial`・
  行の `result` / `iteration` 欠落は `campaign_input_unreadable` (rc=2、発行器 0 回)。未使用の
  `direction` / `magnitude` / `delta_pct` は要求しない (段 6 B1)。
- 欠落記録の `artifact_path` / `artifact_key` は null — その field の出所として参照した artifact が無いため
  (段 6 A1。候補の所在は `campaign_root` / `whiteboard_index` / `iteration`)。
- 真偽値 4 つ (`calibrated_workload_member` / `bootstrap_member` / `reference_is_unique` / `arm_digest_received`)
  を無根拠に埋めない。発行器・台帳の受理集合は変えない。呼び手は `output/` / root / `results/` を作らない。
- 走査 framework、sidecar 入力、ID 規約、carrier、resolver、新 gate は作らない (DW-G04 / G05)。

## 証拠の種類 (段 3 A4 の指摘に従い分ける)

| 事実 | 種類 |
|---|---|
| 現物 7 行全て `success`、`rejected` 0 | 現物再計数 (段 3 の 2 レンズが各自再計数、親は base の 4 行を現物で見て他 2 campaign は前 wave README の再計数を引用。本 wave の実発行試行の `campaigns` 出力で 4 / 1 / 2 行・rejected 0 を機械的に再確認) |
| `output/b4-prerun-publication` は gitignore されない | command (`git check-ignore`、rc=1。段 3 A が `--no-index` 付きでも rc=1 を再確認) |
| 発行器は 201 未満で `design_not_feasible`、root を作らない | code 読解 + 既存 test 定義 + **本 wave の実発行試行で実測** (root 前後不在) |
| whiteboard 5 field / WAL に proposal document 無し | code 読解 (D39 決定 3 / D1846) + 現物の key 集合の確認 (段 3 A) |
| planned result path は root 配下でも可 | 既存 test 定義 (`test_other_future_result_path_below_publication_root_is_allowed`) + T5 で実発行器に 201 行を通して実測 |

## 記録上の限定

- 本 wave は §6 条件 9 (分析契約を実行する経路の実在) の充足数を増やしていない。発行器への操作経路を 1 本足しただけである。
- 呼び手は非空 batch を組めない。201 の適格赤が別の場所に揃った日にも、対応証拠の保存形式と結合規則が決まるまで無改変では使えない。
- T5 (201 行の合成 batch を実発行器へ通す test) は呼び手の issue / serialize 半分の検査であり、現物から非空 batch を組めることの証拠ではない。tmp の repository 複製で発行器を `design_not_feasible` まで走らせる test は、禁じられた「fixture 行での実発行」ではない (段 3 B6)。

## 裁定パッケージ候補 (ユーザーへ返す、本 wave では実装しない)

1. **本 wave の成果の認定範囲:** 「現物からの不足報告 + 空 batch での発行器到達」まで。非空発行経路の完成・条件 9 の充足・T-2632 達成には数えない。推奨どおりなら新しい許可は不要 (依頼の「組めなければ何が足りないかを実測で書いて返す」分岐)。
2. **bootstrap 集合の定義と固定時点:** 「batch 所属」でも「publication 不在」でも決まらない。実際に非空入力を扱う時点で裁定する。今回は carrier も台帳も作らない。
3. **proposal・走行・参照点の対応証拠の出所:** 現存資料で閉じられるかを先に扱う。耐久 carrier 新設や D39 決定 3 の変更が要るなら別裁定。

## 変異 matrix (container worktree `2d71a0454`、`run_tests.py orchestrator/tests/test_p3_b4_prerun_caller.py -q -rf --force-dispatch`、計算ノード dispatch)

3 段で回した。probe (全件 SURVIVED 期待、観測 node の収集) → 観測 node を期待 node にした本走。
probe の観測 node 集合は段 6 焦点再レビューの静的予測表 (15 node × 11 変異) と完全に一致した。
本走: **baseline PASSED、負例 10/10 KILLED、等価対照 M0 SURVIVED、MISMATCH 0、期待 node 完全一致 (matching 11/11)**、
harness rc=0。spec sha256 `f2ec609e8b8b3ad63ce4bbf0086bafe4bfff1362b49ffc9b34ff4e31db419193`
(`verbatim/mutation-spec-final.json`)。dispatch 13 走 (collection + baseline + 11)、02:08〜02:21 JST。
生の結果 JSON (136 KB、job 側 path を含む) は job dir に残し repo へは複製していない。

| ID | 変異 | 期待 = 観測 node | 分類 |
|---|---|---|---|
| M0 | comment 本文だけ変更 | ∅ (SURVIVED) | 等価対照 |
| M1 | 候補選別 `== "rejected"` → `!= "success"` | T3 | fail-closed |
| M2 | 欠落があっても発行器を呼ぶ (`if missing and False:`) | T2, Tmin, Tall | fail-closed |
| M3 | `_MISSING_SOURCES` から `bootstrap_member` を削除 | T2, Tmin, Tall | **診断感度 pin** |
| M4 | 同 `arm_digest_received` を削除 | T2, Tmin, Tall | **診断感度 pin** |
| M5 | campaign ごとに空 batch で発行し最初の拒否で返す | T1, T2 | fail-closed |
| M6 | publication root を cwd 基準にする | T1, T3, T5 | fail-closed (発行器の名指し検査) |
| M7 | 発行器拒否時も rc=0 | T1, T3 | fail-closed |
| M8 | 候補 0 なら発行器を呼ばず成功扱い | T1, T3 | fail-closed |
| M9 | 成功 JSON から `manifest_row_count` を落とす | T5 | **診断感度 pin** |
| M10 | planned path を全行同名にする (`attempt.json`) | T5 | fail-closed (発行器の path 重複拒否) |

T1 = `test_success_only_campaigns_reach_issuer_once_with_empty_batch_and_no_root`、
T2 = `test_mixed_campaigns_report_all_missing_sources_and_never_call_issuer`、
Tmin = `test_minimal_rejected_row_is_a_candidate`、T3 = `test_fail_row_is_not_a_candidate`、
T5 = `test_issue_half_serializes_real_receipt_for_a_complete_batch`、Tall = `test_all_candidates_have_all_missing_fields`。
`test_publication_root_is_not_an_argument` と `test_unreadable_campaign_never_calls_issuer[*]` 8 本はどの変異でも赤にならない
(argparse / 入力解釈の段で止まり変異点に到達しない)。

**M3 / M4 / M9 は DW-M08 の診断感度 pin であり、fail-closed の検出力に数えない** (段 6 A3)。M3 / M4 で変わるのは欠落報告の
内容だけで、残る 11 field が発行を止める。M9 は構造化出力の key だけを変え、発行内容も受理集合も変えない。
fail-closed の検出力として数えるのは M1 / M2 / M5 / M6 / M7 / M8 / M10 の 7 件。

## 走行と検査の記録

- 焦点走 (login、`tools/run_tests.py`): 新 test 15 + `test_p3_b4_prerun_issuer.py` 42 = 57 passed。
- consumer 焦点走 (計算ノード dispatch、request 2284.nqsv、Elapse 155 秒): `test_p3_b4_raw_record_producer.py` /
  `test_p3_b4_material_report.py` / `test_p3_b4_producer_auth_experiment.py` / `test_p3_exploration_namespace.py` /
  `test_p3_b4_analysis_path.py` = 202 passed。
- `tools/check_docs.py`、`tools/check_codex_agents.py`、全史 provenance 監査 (`check_ai_provenance.py`、10809 件) rc=0。
- 受入全走は docs-only の記録 commit の後、tested tip で単独に投入する (結果は land の受領証が持つ)。

## 本書が閉じないこと

- 封印 receipt。201 の適格赤 precursor と、proposal・走行・参照点の対応証拠、bootstrap 集合の定義が揃うまで得られない。
- 自然赤の発生率と、新しい base campaign で赤が出るか (前 wave と同じく未実施)。
- 呼び手が将来の非空 batch をそのまま扱えるか。対応証拠の保存形式と結合規則が決まった時点で改版が要る。

## 収録物

| file | 内容 |
|---|---|
| `verbatim/stage1-brief.md` | 親の段 1 brief (訂正前。P1・N5 は段 4 で倒れた) |
| `verbatim/stage2-plan.md` | 段 2 plan (codex read-only)。空 batch の到達順と field の出所表 |
| `verbatim/stage3-lens-a-correctness.md` | 段 3 敵対相談 (正しさ境界・凍結契約) |
| `verbatim/stage3-lens-b-rulings.md` | 段 3 敵対相談 (裁定整合・実効性・依存図) |
| `verbatim/stage4-ruling.md` | 親の段 4 裁定 (所見の real / refuted、plan v2、変異事前登録、裁定パッケージ候補) |
| `verbatim/stage6-review-a.md` / `stage6-review-b.md` | 段 6 敵対レビュー 2 本 |
| `verbatim/stage6-ruling.md` | 段 6 の所見裁定と fix 単位、変異 matrix v2 |
| `verbatim/stage6-focused-rereview.md` | fix 後の焦点再レビュー (closed 表、変異ごとの期待 node 完全集合) |
| `verbatim/live-issue-attempt.stdout.json` / `live-issue-attempt.meta.txt` | 現物への実発行試行の生 JSON と実行条件 |
| `verbatim/mutation-spec-final.json` | 変異本走の spec (期待 node 完全集合) |

### 逐語の可逆最小正規化 (`git diff --check` 抵触分、可視文字不変)

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes | 復元法 |
|---|---|---|---|---|
| `verbatim/stage3-lens-b-rulings.md` | `7326e5d7f2299c7c1181890c9c07553ed7d38390f5d7206c98a911775191ad0f` | 15,620 | 15,554 | 行末の空白 2 個 (Markdown の改行記法) を 33 行から除去。各行末へ 2 個の空白を戻す (対象行は原文 = job dir `artifacts/.../s3-b.md` の `grep -n ' $'`) |
| `verbatim/stage6-review-b.md` | `371e7bfa5a33ef099a6d881e90ed3b817eeda1b264638b2ae02ae2e8e117559a` | 13,095 | 13,079 | 同上、8 行 (原文は job dir `artifacts/.../s6-b.md`) |
| `verbatim/stage1-brief.md` | `0d17b3be2e4edb134c1f6c0a1af48a6d3ddfdc9c9b1b29805354eb7127beed1e` | 5,980 | 5,979 | 末尾の空行 1 行 (`\n\n` → `\n`) を除去。末尾に `\n` を 1 つ戻す |
