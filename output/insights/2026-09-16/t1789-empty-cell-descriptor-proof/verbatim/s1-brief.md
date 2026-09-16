# 段 1 brief — dev-wave-t1789-empty-cell-descriptor-proof

wave worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof (base 0c292eff6)

## 研究前進
土台。論文 B-3 (8c 正式系列) の certified 選択を受け取る受入 receipt 検証器 (`verify_acceptance_receipt` / `require_current_verified_receipt`) の正しさ境界。現在これが止めている実測は無い (receipt は全世代 `certifying=false` 固定)。完了判定 = 下記再現 case C2/C3 が拒否され、正規の partial 形 (production shape) は通り続けること。開始根拠はユーザーの直接指示。

## scope (ユーザー指示の逐語要約)
- [T-1789] cells=[] と C02 reason 保持の組み合わせで、実行 descriptor が不在のまま expected digest の自己申告を verified receipt にできる構造を塞ぐ。
- まず反例を実際に再現して成果物にし、**再現された欠陥だけ**を修正する。既存 `test_partial_receipt_cannot_` 系 node と突き合わせる。
- 実装面は Codex author (D95)。規律 2 を緩めない。**仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。**

## 再現済みの事実 (親が login node で実走、probe は Codex author 作成・repo 外)
probe: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/probe/probe_t1789_counterexample.py (sha256 c7b676ba…)
結果: 同 dir run1-result.json (sha256 3edf13a3…)。全 case の report は fixture 既定の `status="complete"`、`do_build=False`。

| case | 変換 | 結果 |
|---|---|---|
| A1 / C1 (v2 / v5) | H2/off report を cells=[]、reason 不変 (= 既存 node の形) | 拒否 `[receipt-mandatory-reasons] c02-arm-binding-unproven was dropped without descriptor proof` |
| A2 / C2 (v2 / v5) | 上 + C02 を reason へ追加 (T-1789 逐語) | **verified**。receipt digest = `_expected_arm_content_digest` (一致 true) |
| A3 (v2) | 6 trial 全部 cells=[] + C02 | **verified** |
| B1 (v2) | H1/on descriptor の read_ratio 80→79 (receipt/run-start は期待 digest のまま) | 拒否 `[receipt-arm-binding] cell descriptor content digest differs from receipt` |
| B2 / C3 (v2 / v5) | B1 の report から cells=[] + C02 | **verified** (矛盾する実行証拠を消すと拒否が受理に変わる) |
| C2 / C3 下流 | `require_current_verified_receipt` | **accepted**。止まるのは `build_accepted_report` の `acceptance receipt が certifying=true でない` だけ |
| A2 下流 (v2) | `require_current_verified_receipt` | 拒否 `[receipt-capability] downstream capability requires the current receipt schema` |
| C4 (v5) | do_build=True + cells=[] + C02 | 拒否 `[receipt-cross-binding] [cross-binding] build report must contain at least one cell` |

## 確定済みの裁定・先例 (覆さない)
- D519: C02 を落とせるのは名指し hash 済み bytes の descriptor から再導出できたときだけ。「descriptor を持たない**部分 report** は理由を残す fail-closed 形」。certifying は構造的 false。
- D1757: legacy v3/v4 は下流 capability に到達しない。到達不能経路への防壁追加は却下した先例。
- D947/D948: 権威 root は verifier 自身の checkout、v2/v3 は固定 V1 authority の legacy として読む。

## 親の provisional 裁定 (攻撃対象)
- (P1) 欠陥の核 = 「`status="complete"` を名乗る report が cells=[] のまま D519 の『部分 report』扱いを受け、C02 保持で verified になり v5 capability gate を通る」。根拠: 本番 driver は `status="complete"` を `len(cells)==len(selected)` かつ fatal_error なしのときだけ付ける (`p3_autonomous_workload_trial.py` の status 式、completeness `_check_status_projection` が同式を検査)。したがって本番 producer が complete + cells=[] を出す経路は無い (読解・未実測)。
- (P2) 修正の形 = `verify_acceptance_receipt` で、descriptor 証明の無い trial の `status == "complete"` を fail-closed で拒否する。**既存 mandatory-reasons 判定の後**に置き、既存 node (C02 を落とす形) の期待文言を 1 文字も変えない。partial + cells=[] + C02 保持 (producer が `test_p6_one_cell_partial_terminal_outcome_passes_acceptance` で発行する正規形) は通し続ける。
- (P3) v5 では status が attempt registry の最終 terminal と `complete⇔observed / partial⇔terminal-failure` で束縛済み (`_assert_attempt_registry_consumption`)。complete→partial へ書き換えて逃げるには登録簿側も terminal-failure でなければならず、そのとき receipt は実行を名乗らない。証拠を消した後の report bytes は正規の partial 形と区別できないので、検証器単独で使える信号は status だけ (読解)。
- (P4) 適用世代 = v2〜v5 共通 (既存の `descriptor_proofs` 計算が既に v2+ 共通で、版分岐を足さない)。D1757 との関係 (legacy は到達不能) は攻撃対象。対になる案は v5 限定。
- (P5) scope 外: producer `trial_registry.py` の変更 (稼働中 wave `dev-wave-t1957-manifest-replicates` が編集中、かつ producer は complete+cells=[] を出さない)、`require_current_verified_receipt` への C02 検査追加、schema v6、fatal_error の field 検査、partial 形の追加制約。

## DW-O13 実測 (gate 入力の実在)
- 実在する trial report (top-level に trial_id / status / do_build / cells) は `izanagi/output` 全域で 0 件 (find 完走、`output/exploration/autonomous-trials/` 自体が不在)。`/work/SFC/tanab` 直下にも campaign/trial/s8c 系 dir は 0 件。`dev-wave-jobs` は 120 秒で走査が終わらず部分探索で 0 件 (不在の証明ではない)。
- よって status の実環境値域は実測できない。status 値は producer 式 (driver は `complete` / `partial`) と、v5 の `_assert_attempt_registry_consumption` が受ける 2 値 (`complete` / `partial`) で読む (読解)。正例の値 `partial` + cells=[] は producer テスト `test_p6_one_cell_partial_terminal_outcome_passes_acceptance` が発行する形 (親が焦点走で実測する)。

## 不変条件
- 受理集合は狭める方向だけ。正例 (partial + cells=[] + C02 保持の v5 receipt が verified) を必ず添える。
- 既存テストの期待値・関数名・node 名を変えない。`s8c_acceptance_receipt` は `trial_registry` / `layer3_report` に依存しない。
- receipt / report / journal の保存 bytes・exact key 集合・schema 版を変えない。repo に tracked receipt は 0 件 (過去記録の無効化なし)。
- subprocess 呼出し数を変えない (`test_ccbench_spawn_sites.py` が `campaign/s8c_acceptance_receipt.py <module>._git: 1` を pin)。

## 変更面 (実アンカー)
| 位置 | 事実 |
|---|---|
| `orchestrator/campaign/s8c_acceptance_receipt.py` `_verify_v2_trial_arm_execution` | cells=[] のとき `descriptor_proven=False` を返すだけで status を見ない |
| 同 `verify_acceptance_receipt` の `receipt-mandatory-reasons` 判定 | C02 が残っていれば descriptor 証明の有無を問わず通す |
| 同 `_assert_attempt_registry_consumption` | v5 で trial.status と最終 terminal を対応づける |
| `orchestrator/tests/test_s8c_acceptance_receipt_v2.py` `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof` | 突き合わせ対象の既存 node (C02 を落とす側だけ) |
| 同 `_upgrade_to_current(..., terminal_failure_trials=...)` | v5 の partial 正例を作れる既存 helper |
| `orchestrator/campaign/trial_registry.py` 受入 producer (`descriptor_proofs.append(len(cells)==1)`) | cells が 1 件でない trial があると C02 を付ける。触らない |

## 成果物影響 (DW-G05)
放置すると、標準 verifier と v5 capability gate の受理集合に「実行 descriptor が期待と食い違う complete trial から証拠を消した receipt」が残り、certifying を有効化する世代で B-3 の certified 選択が実行未証明の arm に乗る。現 checkout の成果物の値は変わらない (certifying=false で `build_accepted_report` が拒否)。

## 分割方針
軽量ではない (正しさ防壁の受理集合を変える): 段 2 plan 1 本、段 3 敵対相談 2 レンズ、段 5 実装子 1 単位 (production 1 file + test 1 file で所有は素集合にできない)、段 6 レビュー 2 本、変異 matrix、受入全走。
実測環境: 焦点テストは Pegasus dispatch (`tools/run_tests.py`)、受入全走は `tools/dev_wave_wait.py acceptance`。
