# 段 4 裁定 — dev-wave-t2632-b4-prerun-issue-caller

裁定 inbox の再走査: local main は基準 `1042a1bc9` から進んでいない。`docs/spool/` に新規 fragment なし。

## 所見の裁定 (A = レンズ A 正しさ境界、B = レンズ B 裁定整合、P = plan)

| # | 所見 | 判定 | 採否 | 扱い |
|---|---|---|---|---|
| A1 / B(P1) / P | 親 P1「batch に含めた行は `bootstrap_member` 真」は述語を恒真化する | real | 採用 (P1 撤回) | `bootstrap_member` は「出所なし → typed stop」側。何を集合とし、いつ固定するかは裁定パッケージへ |
| A2 / B2 | N5「成功 precursor は registry 行にならない」は誤り。台帳型は SUCCESS を受理し、manifest の適格性で除かれる | real | 採用 (文言訂正) | 訂正: 「既存 7 行から適格候補は得られない」。呼び手が `rejected` だけを候補にするのは依頼が供給源を赤 precursor に限るからで、registry の全件性は本呼び手が証明しない (B3) |
| A3 | 全 campaign が空候補の fixture では「campaign ごとに発行する」誤実装が生存する | plausible | 採用 | 欠落 test の入力を「先頭 campaign は success のみ、後続 campaign に `rejected`」の混在にする |
| A4 | brief の N1〜N6 は証拠の種類 (現物再計数 / command / code 読解 / test 定義) が混在 | real | 採用 (記録の仕方) | insight で種類を分ける。親の brief 前の実測は: N3 は base の 4 行を現物で見て sort/trigger は前 wave README の再計数を引用、N4 は `git check-ignore` を自分で実行 (rc=1)、N1/N2/N5/N6 は code 読解。空 batch の挙動は plan と A8 が code で検算、本 wave の実行で実測する |
| A5 / A6 / A8 / A10 / A11 | 捏造・受理集合拡大・凍結汚染・D1846 代用・N3/N4 誤り | refuted | — | 記録のみ |
| A7 | `issuer._REPOSITORY_ROOT` への private 結合 | plausible | 不採用 (nit) | 結合は fail-closed (発行器 `:218` が名指し不一致を拒否)。parser 複製より小さい |
| A9 | P4 は単一 component ID なら予約と衝突しない。任意 ID の安全性は一般化しない | refuted/限定 | 採用 (限定) | ID 規約は新設しない。fixture の ID は単一 component |
| B1 | 呼び手は非空 batch を組めず、201 赤が揃った日にも無改変では使えない | real | 採用 (scope の言明) | 成果の認定範囲は「現物からの不足報告 + 空 batch での発行器到達」。module docstring と insight にそう書く |
| B4 | N1 の依存列挙 (自然赤 + §5 の 2 欄) は十分条件でない | real | 採用 (文言訂正) | 必要物: 201 適格赤、予定 attempt 集合と attempt/block/走行の対応、初期 proposal の exact value と bootstrap 所属根拠、校正 workload・一意参照点・digest 非受領の根拠、全予定 attempt の planned result path |
| B5 | §6 条件 9 への貢献を過大表現 | real | 採用 (文言訂正) | 「発行器への操作経路を追加した」と書き、条件 9 の充足数は増やさない |
| B6 | tmp の空 batch test は禁止された fixture 実発行ではない | refuted | — | 「実発行器を使う単体試験」と「実 artifact での発行試行」を記録上分ける |
| B7 | 未接続の非空組立て・ID 規約・carrier・resolver は設計メモ止まり (DW-G04)。成功戻り値の stub 試験を実発行可能性の証拠に数えない | plausible | 採用 | 成功経路 test は stub でなく **実発行器** + 201 行 fixture batch (tmp repository root) で呼び手の issue/serialize 半分を通す (F649)。これは実発行可能性の証拠ではなく呼び手の直列化の検査 |
| B8 | 3 driver の対応表は厚くなりうる | plausible | 限定採用 | `campaign.lock.trial` → driver の exact 3 行表だけ。未知 trial は入力解釈不能。複数 driver の発行機構へ一般化しない |
| B9 | `p3_b4_prerun_issue` は `p3_b4_prerun_issuer` と紛らわしい | plausible (nit) | 採用 | module 名を `p3_b4_prerun_caller.py`、test を `test_p3_b4_prerun_caller.py` にする |
| B10 | 候補 0 の実行では 12 field 欠落報告経路を通らない | real | 採用 (記録) | insight に「観測: 候補 0」と「現行保存形式から入力を構成できない理由 (12 field 表)」を併記。架空候補は作らない |
| P | `B4PrerunIssuerError` に `.detail` 属性なし | real | 採用 | `str(exc)` から `reason.value + ": "` 接頭辞を除いて detail とする |

## 承認済み裁定との関係

D1880 / D1881 / D1846 / D1936 項 8 / D1986 項 4 / D95 と衝突する所見なし。前 wave README の「1 は 2 と独立に閉じられる」(未裁定の README 記述、D にはなっていない) は本 wave の insight で追補訂正する (旧稿は書き換えない)。

## plan v2 (確定)

- **module:** `orchestrator/campaign/p3_b4_prerun_caller.py`。関数分割: `collect_scheduled_batch(campaign_roots) -> (batch, missing)`、`planned_result_artifacts_for(batch, publication_root)` (P4)、`issue(batch) -> dict` (発行器を 1 回呼び、成功/拒否を JSON 化)、`main(argv) -> int`。
- **argv:** `--campaign-root PATH...` (必須、`nargs="+"`)。publication root・seed・真偽値・proposal hash を上書きする argv は無い。`--publication-root` は argparse が未知引数として拒否 (rc=2)。
- **publication root:** 実行時に `issuer._REPOSITORY_ROOT / "output/b4-prerun-publication"` を組み、発行器の名指し検査に任せる。import 時に別定数へコピーしない。呼び手は `output/`・root・`results/` を作らない。
- **候補:** `loop_state.json` の `whiteboard[].result == "rejected"` の行だけ。`campaign.lock.trial` を exact 3 行表 (`p3-s4-loop`→base、`p3-s5-sort-loop`→sort、`p3-s8a-trigger-loop`→trigger) で driver に写す。未知 trial・lock 不在・checkpoint 不在は入力解釈不能 (typed、rc=2、発行器 0 回)。
- **field の出所:** plan の表のとおり。構成可能: `schema_version`、`registry_ordinal` (argv 順 × whiteboard 配列順)、`driver`、`reason=SCHEDULED`、`whiteboard_result`。出所なし (12): `attempt_id`、`block_id`、`digest_red_classes`、`workload`、`calibrated_workload_member`、`initial_proposal_sha256`、`bootstrap_member`、`reference_tps`、`reference_snapshot_hash`、`reference_receipt_hash`、`reference_is_unique`、`arm_digest_received`。真偽値 4 つ (arm_digest_received を含む) を無根拠に埋めない。
- **処理順:** (1) 全 campaign を読み候補を集める → (2) 全候補の欠落を集計 (最初の field で打ち切らない) → (3) 欠落が 1 つでもあれば `{"reason": "scheduled_input_sources_missing", "missing": [...], "candidate_count": n, "campaigns": [...]}` を stdout、rc=2、発行器 0 回 → (4) 候補 0 なら空 batch で発行器を **1 回** 呼ぶ → (5) 発行器の例外は `{"reason": <reason.value>, "detail": <str(exc) から接頭辞除去>, "candidate_count": 0, "campaigns": [...]}`、rc=2 → (6) 成功時だけ `{"issued": {"receipt_path", "receipt_sha256", "issuer_commitment_sha256", "manifest_row_count"}}`、rc=0。
- **planned result path (P4):** `<publication_root>/results/<attempt_id>.json`。ID 規約は新設しない。
- **docstring:** 「非空 batch は現行の保存形式 (checkpoint 5 field、WAL) から構成できない。本 module は現物からの不足報告と空 batch での発行器到達までを担い、予定 attempt の全件性・bootstrap 所属・201 適格行の調達は証明しない」を明記。
- **test (`orchestrator/tests/test_p3_b4_prerun_caller.py`)、既存 test の期待値は変えない:**
  - T1 `test_success_only_campaigns_reach_issuer_once_with_empty_batch_and_no_root`: 3 driver の lock + 全 success の checkpoint fixture、発行器 `_REPOSITORY_ROOT` を tmp へ (support の `preregistered_publication_root` と同形)、cwd を別 tmp に変え、実発行器を wraps で数える。呼出し 1 回・空 tuple 2 本・rc=2・reason `design_not_feasible`・detail exact・root 不在。
  - T2 `test_mixed_campaigns_report_all_missing_sources_and_never_call_issuer`: 先頭 campaign は success のみ、後続 campaign に `rejected` 1 行 (A3)。発行器 0 回、rc=2、reason `scheduled_input_sources_missing`、欠落 field 集合が上の 12 と exact 一致 (真偽値 4 つを個別 assert)、各欠落に campaign_root / whiteboard index / iteration / 参照 artifact。
  - T3 `test_fail_row_is_not_a_candidate`: `fail` 行は候補にならない (T1 と同じ終端)。
  - T4 `test_publication_root_is_not_an_argument`: `--publication-root` は argparse 拒否、発行器 0 回。
  - T5 `test_issue_half_serializes_real_receipt_for_a_complete_batch`: 201 行の完全 batch (support の行と同形、単一 component ID) を tmp repository root で **実発行器** に通し、rc=0、JSON 4 field、`manifest_row_count == 201`、planned path が P4 規則、`load_b4_prerun_publication` で再検証。stub 不使用。
- **変異 matrix (事前登録、DW-M01):** M0 comment のみ (対照、SURVIVED 期待)、M1 候補選別 `== "rejected"` → `!= "success"` (T3)、M2 欠落があっても発行器を呼ぶ (T2)、M3 `bootstrap_member` を True 固定して欠落から除く (T2)、M4 `arm_digest_received` を False 固定 (T2)、M5 campaign ごとに発行器を呼ぶ (T2、T1)、M6 root を cwd 基準にする (T1、T5)、M7 拒否時も rc=0 (T1)、M8 候補 0 なら発行器を呼ばず成功扱い (T1)、M9 成功 JSON から `manifest_row_count` を落とす (T5)、M10 planned path の attempt_id を別の行のものにする (T5、発行器の mapping 不一致)。実位置は author 完了後に記入。単一理由性は実装後に確認。
- **焦点走:** 新 test file + `test_p3_b4_prerun_issuer.py`、`test_p3_b4_raw_record_producer.py`、`test_p3_b4_material_report.py`、`test_p3_b4_producer_auth_experiment.py` + `tools/check_docs.py`、`tools/check_codex_agents.py`。受入全走は `dev_wave_wait.py acceptance`。
- **実発行の試行 (親、段 6 後):** wave worktree で `python3 -m orchestrator.campaign.p3_b4_prerun_caller --campaign-root <3 campaign>` を 1 回。stdout / stderr / rc を job dir と insight へ。実行後 root 不在を確認。
- **no-touch:** 発行器、台帳、事前登録、`p3_s4_loop*`、既存 test。

## 裁定パッケージ候補 (ユーザーへ返す、実装しない)

1. **本 wave の成果の認定範囲:** 「現物からの不足報告 + 空 batch での発行器到達」まで。非空発行経路の完成・条件 9 の充足・T-2632 達成には数えない (推奨どおりなら新しい許可は不要 — 依頼の不成立分岐)。
2. **bootstrap 集合の定義と固定時点:** 「batch 所属」でも「publication 不在」でも決まらない。実際に非空入力を扱う時点で裁定する。今回は carrier も台帳も作らない。
3. **proposal・走行・参照点の対応証拠の出所:** 現存資料で閉じられるかを先に扱う。耐久 carrier 新設や D39 決定 3 の変更が要るなら別裁定。D1936 / D1986 で不採用の供給増加基盤・n 削減は再提案しない。
