# [T-244] P3 critic 後置 (U-8) — 段 4 裁定の訂正 (プラン v3)

## 1. 実装子が検出した矛盾 (real、採用)

プラン v2 は「critic を `_run_workload` の外へ出さない」ため、cell の Layer 3 admission 確定も
`_run_workload` 内へ置いた。しかしこれは既存の直呼びテストと両立しない。

- `test_run_workload_other_build_reaches_drive_positive` (`test_p3_autonomous_workload_trial.py:1633`) と
  `test_run_workload_build_passes_exploration_layout_to_trigger` (同 `:1831`) は、fake drive が
  campaign root を mkdir するだけで、`reports/` も WAL も provenance も作らない。
- 実 `_finalize_build_cell_admission` は `reports/` の実在を要求し (`p3_autonomous_workload_trial.py:1207`)、
  `build cell campaign has no reports directory` で送出する。
- 「直呼びだけ finalize を省く」は A5 (critic 抜き経路) の再導入、
  「fixture に fake finalizer を差す」は admission の実在を検査しないテストの甘化であり、どちらも不可。

**判定: real / 採用。プラン v2 §3 の「`_run_workload` 内で admission を確定する」を撤回する。**

## 2. プラン v3 (確定。v2 §3 を置き換える)

**critic と cell admission の確定は `_finish_trial` の「全 workload 実行後のループ」で行う。
`_run_workload` は planner / coder / auditor / harness までを担い、critic を呼ばない。**

`_run_workload` の**引数は 1 つも増やさない**。pending critic は cell dict の私有 key
(`result["_pending_critics"]`) に積んで返す。これで B R-06b (必須引数追加による直呼びの `TypeError`) を
避け、既存の直呼びテスト群を無変更で通す。

1. **`_run_workload` の generation ループ**を planner / coder / auditor / harness までに狭める。
   - harness 結果確定 (`:1739-1741`) の直後に generation を cell へ append し、
     `_partial["generation"] = None` にする。
   - critic 用の最小情報 (generation 番号、`common` payload の copy、outcome の copy、
     metric projection、raw variant) を `result["_pending_critics"]` へ積む。
   - harness terminal stop の break は**消さない** (B R-06a)。その理由を cell の暫定 `stop_reason` に残す。
   - **`_run_workload` は critic を呼ばない。** その結果、direct `_run_workload` 経路は critic attempt を
     持たなくなる (§4 の scope 外所見として記録し、テストで pin する)。
2. **`_finish_trial` の既存 finalize ループ (`:1363-1369`) を、cell ごとの二相処理へ置き換える。**
   この loop は workload loop の `try` の**外**にあるため、finalizer 例外はそのまま伝播する
   (B S-01 は追加の guard なしで満たされる)。cell ごとに:
   1. `do_build` なら `_finalize_build_cell_admission(cell, launch_admission=launch_admission)`、
      そうでなければ `cell["admission_decision"] = {"admission_status": "not-applicable"}`。
   2. `cell.pop("_pending_critics")` で pending を取り出し、**admission 確定後**に順に critic を呼ぶ。
      critic digest 生成と `require_admitted_campaign` もここで行う。
   3. critic が `None` を返したら `cell["stop_reason"] = "role-invalid"` とし、
      **harness 由来の stop より優先**する。admission decision は巻き戻さない。以降の critic は呼ばない。
   4. `supervisor-error` で復元された cell も、完了済み generation の pending critic は同様に呼ぶ
      (現行 report 形の保存)。ただし `stop_reason` は `supervisor-error` のままとする。
3. **`status` の算出 (`:1352-1362`) を、この二相ループの後へ移す。** critic invalid が
   `stop_reason` を変えうるため。式そのものは変えない。
4. **fail-closed 検査を 1 つ足す。** report 構築の直前に、どの cell にも `_pending_critics` が
   残っていないことを確認し、残っていたら `AutonomousTrialError` を送出する。
   消費し忘れた経路を黙って通さないため。
5. **変えないもの (v2 から不変):** `SCHEMA_VERSION` (v3)、`REPORT_SCHEMA_VERSION` (v2)、
   journal event 集合、`_ROLE_ORDER`、`_check_attempt_sequence`、`MAX_APPROVED_GENERATIONS`、
   critic payload の key 集合、`autonomous_trial_completeness.py`。新定数・新 event を作らない。

### 受理集合の変更 (D96 の対象。v2 から不変)

- 1 世代の運転 (承認済み唯一の運転) の受理集合は**不変**。
- cap を上げて多世代 full trial を回した場合だけ、journal 順が report 順と食い違い、
  `assert_autonomous_trial_completeness` が report publish 前に fail-closed で止める。

## 3. テスト (v2 §4 を次で置き換える)

1. `test_build_cell_admission_precedes_critic_invocation` — 共有 `order` list に finalizer と
   critic provider が append し、`order == ["admission", "critic"]` を検査する。
   既存 build public-entry test と同じ topology を使ってよいが、**実 `_finalize_build_cell_admission` を
   spy で包めるならそうする**。実 Layer 3 render を fixture で発火できない場合は、その限界を
   test の docstring に明記し、緑と偽らない。
2. `test_post_admission_invalid_critic_marks_cell_role_invalid` — critic 応答だけ malformed。
   `stop_reason == "role-invalid"`、`report["status"] == "partial"`、`admission_decision` が残ることを検査。
3. `test_invalid_critic_overrides_harness_terminal_stop` — harness stop が `continue` 以外でも
   critic invalid が優先することを検査。
4. `test_cell_admission_failure_is_not_converted_to_supervisor_error` — finalizer を失敗させ、
   `supervisor-error` partial ではなく例外で止まり report が publish されないことを検査。
5. `test_multi_generation_deferred_critic_fails_closed` — `MAX_APPROVED_GENERATIONS` を 2 へ
   monkeypatch した full `run_trial` が report publish 前に completeness で止まることを検査。
   **これが受理集合縮小の境界テスト (D96)。**
6. `test_direct_run_workload_defers_critic_to_finish_trial` — direct `_run_workload` が critic を
   呼ばず、`_pending_critics` を cell に残して返すことを検査する。
   **挙動変化を黙らせず可視化するための pin。**
7. **正例 (承認外の過剰拒否の検出、DW-M01):** 既存の 1 世代 build / no-build positive path が
   従来どおり受理され report を publish することを、既存テストの緑を以て確認する。
8. 既存の直呼びテスト (`test_p3:1633, 1831` ほか) と `test_claude_transport.py` の caller は
   **無変更で通るはず**である。通らなければ実装側の誤りとして扱い、期待値を変更しない。

## 4. 変異事前登録 (v2 §5 を次で置き換える)

| # | 位置 | 変異 | 期待 kill node | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `_finish_trial` の二相ループ | finalize と critic 呼び出しの順を交換 | `test_build_cell_admission_precedes_critic_invocation` (新設) | 1 世代では journal/report 順が変わらず completeness は通る。order spy だけが検出する |
| M2 | critic invalid 分岐 | `stop_reason = "role-invalid"` 代入を削除 | `test_post_admission_invalid_critic_marks_cell_role_invalid` (新設) | status 再算出が後段にあるため、この代入だけが cell stop を決める |
| M3 | critic invalid と harness stop の優先順位 | harness stop を後勝ちにする | `test_invalid_critic_overrides_harness_terminal_stop` (新設) | 優先順位だけを変える。他層は同じ入力を拒否しない |
| M4 | `status` 算出の位置 | 二相ループの**前**へ戻す | `test_post_admission_invalid_critic_marks_cell_role_invalid` (新設、`status == "partial"` の assert) | 位置だけを戻す変異。completeness の status 再算出が拒否するため fail-closed 方向の赤になる |
| M5 | report 構築直前の `_pending_critics` 残留検査 | 検査を削除 | (新設 pin なし) | **単一 kill node を持たないため、変異でなく diagnostic sensitivity pin として別枠に記録する (DW-M08)** |

落とした候補: barrier 系 (実装しない)、`_ROLE_ORDER` prefix (本 wave の変更行でなく既存テストが殺す)、
generation 上限行 (D114 gate が先に拒否し後段が mask される)。

## 5. scope 外 real 所見の追加 (裁定パッケージへ)

v2 §6 の 3 件に次を加える。

4. **direct `_run_workload` の contract 変化。** 本 wave 以後、direct 入口は critic を呼ばず
   `_pending_critics` を持つ cell を返す。critic は gate ではなく recipient なので正しさ防壁は
   弱まらないが、「direct 入口で作った材料は critic attempt を持たない」という事実は
   D114 が第 3 入口として扱う面の contract 変化である。この入口を封印するか、
   単一入口へ統合するかは裁定が要る。

## 6. 実装子への追加指示

- **pytest を走らせようとしないこと。** sandbox からは admission 予約台帳
  (`/run/user/<uid>/izanagi-admission`) を更新できず rc=16 で止まる。テスト実測は親が行う。
  静的検査と実装だけを行い、「実装済み・未実走」と報告すること。
