単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication.md

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1`
(branch `fix-dev-wave-t1851-c1b-1`、base `d52b2f833`) である。コードはすべてこの worktree の中で
読み書きする。次を上から順に読む。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication.md` — **親の段 6 裁定。本作業の契約。** 2 節の R-1〜R-6 (blocker)、3 節の R-7・R-8 (must-fix)、**5 節の fix 方針**、6 節の停止条件。
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-review-a.md` — レンズ A の逐語 (失敗シナリオの詳細)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-review-b.md` — レンズ B の逐語 (同上)
4. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — **契約の正本**
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/refs/decisions-verbatim.md` — D1113 / D1341 / D1522

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_terminal_evidence.py`
- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/campaign/s8b_attempt_profile.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_terminal_evidence.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
- `orchestrator/tests/test_attempt_registry_core_equivalence.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

`s8b_floor_campaign.py`、`s8b_floor_stats.py`、`s8b_holdout_admission.py`、`s8b_ratified_freeze.py`、
`acceptance_duration_ledger.json`、docs、他の test file は所有外である。
**所有外に必要な変更が見つかったら実装せず完了報告に書け。** docs の編集と commit はしない。

## 依頼 — 敵対レビュー 2 本が出した blocker 6 件と must-fix 2 件を閉じる

**すべて real と裁定済みである。全件を直せ。** 裁定 5 節のとおり、**R-1〜R-4 と R-6 は
1 つの構造変更へ集約して閉じる。個別に潰さない。**

### 中心の構造変更 — 副作用前の private canonical snapshot

現状の穴は 1 つの型である。**launcher が可変で呼び手所有のオブジェクトを未信頼の
`terminal_builder` へ渡し、その後で権威として読み直している。**

1. `protocol`、`perf_preflight_receipt`、`probe_before` / `probe_after`、`failure`、
   `launch_failures`、rep sink、`terminal.campaign_record` を、それぞれ
   **副作用より前に (または生成直後に) 一度だけ** canonical bytes へ固める。
2. `terminal_builder` には **深い複製または read-only view** を渡し、snapshot 自体を渡さない。
3. `seal_terminal_evidence()` はその snapshot だけを読む。**`reservation` を読み直さない。**
   署名を変える必要があるなら変えてよい (leaf も所有 path である)。ただし**契約 6.1 が定めた
   `seal_terminal_evidence(reservation, opened, terminal)` の公開 signature を保つのが望ましい** ので、
   snapshot を `opened` 側へ載せる形を優先して検討しろ。変えるなら理由を報告に書け。
4. `campaign_record` は **一度だけ** strict canonical snapshot へ変換し、
   **launcher の facts 検査と sealer が同一の snapshot を見る。** duck-typed な `Mapping` を
   2 回読む形を無くす (R-4)。
5. 分類 receipt の `external_evidence_sha256` と terminal evidence の各 source digest を
   **再照合する** (R-3)。

### 個別に足す検査

- **R-1 (test seam):** certified wrapper だけが得られる **launcher-origin capability** を
  reserve state と handle fingerprint に束縛し、sealed terminal 発行時にも照合する。
  `_launch_floor_attempt_for_test()` はその capability を取得できない形にする。
  **real adapter へ全メソッドを転送する fake registry を正面から使った負例**を置き、
  それが拒否されることを示せ。
- **R-5 (identity 再束縛):** adapter の `_assert_terminal_durable_identity()` に
  `campaign_record.holdout_id == slot.freeze_holdout_key`、
  `campaign_record.configuration_id == slot.configuration_id`、
  `campaign_record.retry_ordinal == slot.attempt_ordinal` の**明示検査**を足す。
  **発行時と durable replay の双方**に、real observation と偽 structural reservation を組み合わせた
  移植負例を置け。
- **R-6 (capture/count 矛盾):** `_assert_mutual_consistency()` に
  「`failure.stage == "capture"` ⇒ `launch_failures_count == 0`」を足す (契約 1.2)。
  leaf と durable replay の両方に正例・負例の対を置け。
- **R-7 (例外名の正規化):** v2 発行経路で `subprocess.TimeoutExpired` → `OSError` → `RuntimeError` の
  順に `isinstance` で基底カテゴリ名へ正規化する。代表的な `OSError` サブクラス
  (`FileNotFoundError`、`PermissionError`) と `RuntimeError` サブクラスを検査せよ。
  **v1 経路の綴りは 1 bit も変えるな。** open 側が契約外の例外を terminal 化しうるなら、
  捕捉を契約の 3 クラスへ絞るか、terminal 化しない経路として明示しろ。
- **R-8 (pre-probe 競合枝の到達性):** `ScalePoint` 座標検査を
  **「capture を実行した failure 無しの経路」に限定**し、pre-probe competing の統合正例を足せ。
  契約 4.1 の枝 1 と 5.2 の「観測前・競合」行が**実際に sealed terminal になる**ことを示せ。

### 変異の事前登録 (裁定 5 節。実装後にこれで検査される)

F1 snapshot でなく `reservation.protocol` 再読へ戻す / F2 builder へ元の可変 sink を渡す /
F3 `campaign_record` の二重読みへ戻す / F4 adapter の 3 identity 検査を 1 つずつ削除 (3 変異) /
F5 capture stage の count 0 検査を削除 / F6 例外名の正規化を削除 / F7 test seam の
launcher-origin capability 検査を削除。

**各変異について「同じ入力を拒否する層が前後にも内側にも無い」ことを確かめ、
確かめられないものは完了報告にそう書け。冗長 gate による赤を kill に数えない。**

## 禁止 (違反したら差し戻す)

- **既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。赤になったら実装側が誤りである。**
  期待値の側が誤りだと判断したら、実装を変えずに報告して止まれ。
- 親が段 5 で許可した既存期待値の意味変更 **2 箇所**
  (`test_v2_profile_is_rejected_before_any_registry_side_effect`、
  `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell`) **を超えない。**
- **v1 の受理集合を 1 bit も変えない** (event key exact 24、retryable reason 集合 空、
  `failure_reason` と classification の等値、observed / terminal-failure / rejection の既存行列)。
- **`expected_use_perf` の導出は launcher の既存 gate 1 本のまま。leaf に perf 述語の新しい
  直接 call を置くな** (契約 9 節。`test_official_perf_closure.py` の semantic inventory が落ちる)。
- `attempt_registry_core.py` に `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を
  書くな。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定して growth hold を解除するな。** その release token は
  明示的なユーザー指示のためのものである。hold された test の結果が要ると判断したら、
  走らせずに報告しろ。
- 要求外の gate・検査・台帳・互換層・一般化・防御的な追加コードを足すな。
- 期待値へ揮発 payload (working tree hash、時刻、絶対 path 等) を焼き込むな。
- commit しない。docs を編集しない。

## 検査・報告 (DW-S05-C を継承)

- 実走は自走 harness を使う。
  `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-fix1 && PYTHONPATH=. python3 orchestrator/tests/<file>.py`
  の形で、**所有 5 test file すべて**を走らせろ。**`run_tests` は使うな。**
- **緑には実走 nodeid・範囲を併記する。** 実走不能なら `closed` と申告せず「実装済み・未実走」と書け。
- **変更した production file を参照する consumer test も自分で引いて走らせろ**
  (名前の推測でなく参照関係で引く。private symbol は symbol 名で production 全体を grep しろ)。
  親は `test_trial_registry` `test_p3_autonomous_workload_trial` `test_s8b_holdout_admission`
  `test_s8c_acceptance_receipt_v2` `test_ccbench_spawn_sites` `test_s8b_scheduler_accounting`
  `test_official_perf_closure` が base で緑であることを実測済みである。**回帰させるな。**
- 機構の正例・負例は実体を名指しし、依存先を stub しない。**テストを甘くして緑にしない。**
- 完了報告に、所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。
- **契約の条項が実体化できないと判断したら、回避策を自作せず止めて報告しろ。**

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。

## 総括

最後に `## 総括` 節を置き、次を書く。

- **R-1〜R-8 の対応表 (closed / partial / 未実施)。** partial と未実施は理由を file:line つきで
- 中心の構造変更で何を snapshot にしたか、`seal_terminal_evidence()` の signature を変えたか
- 実走した nodeid の範囲と結果 (緑 / 赤 / 未実走)。赤はその内訳と帰属
- F1〜F7 のうち単一理由で殺せると確かめられたものと、確かめられなかったもの
- 所有外への波及 (実際に変更が要ると判明したものは file:line つき)
- production / test の差分行数
