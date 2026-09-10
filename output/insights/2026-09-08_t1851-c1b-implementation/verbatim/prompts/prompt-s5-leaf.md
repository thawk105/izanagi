単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — **契約の正本。** 特に 1 節 (証拠文書)、1.1〜1.5、2 節 (相互整合)、3 節 (`exec_failures` の射程)、4 節 (E1・E2)、6.1 / 6.3 (発行経路と capability)、9 節 (射程の限界)。**契約に書かれていない条項を自分で足さない。**
2. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/plan-v2.md` — 実装手順。**3 節 (実装子 1 = leaf の plan) が本作業の範囲**である。4 節 (統合) は本作業では実装しない。
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md` — 親の段 4 裁定。**4.1 の変異表 L1〜L18 が本作業の観測対象**である。
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s1-brief.md` — 親 brief。3 節の実測表と 5 節の不変条件。
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/refs/decisions-verbatim.md` — 確定裁定の逐語 (D1113 / D1341 / D1522)。

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf` (branch `impl-dev-wave-t1851-c1b-leaf`、base `8924c0ef3`) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_terminal_evidence.py` (**新設**)
- `orchestrator/tests/test_s8b_terminal_evidence.py` (**新設**)

`attempt_registry_core.py`、`s8b_attempt_profile.py`、`s8b_attempt_registry.py`、`s8b_floor_attempt_launcher.py`、`s8b_floor_stats.py`、`s8b_floor_campaign.py`、既存の test file、docs はすべて所有外である。**所有外に必要な変更が見つかったら実装せず完了報告に書け。** docs の編集と commit はしない。

## 依頼 — C1b の leaf 層 (純関数)

契約 v3.1 と plan v2 §3 に従って `s8b_terminal_evidence.py` を新設する。**これは他の 8 file を import しない純関数層**である。import してよいのは `orchestrator.campaign.attempt_registry_core` の `canonical_json_bytes` と `orchestrator.campaign.s8b_floor_stats` の 2 つだけ (契約 / plan の規定)。標準 library は自由に使ってよい。

### 受理・拒否の現状 (scope 前)

`s8b_terminal_evidence.py` は**存在しない。** 現状 `s8b_floor_attempt_launcher.py` の v2 attempt は adapter 側の無条件拒否 hook で terminal 時に落ちる。本作業はその置き換え先となる純関数層を**新設するだけ**であり、既存の受理集合・拒否集合を 1 bit も変えない (所有 file が 2 本とも新規なので、既存挙動への波及は import 経路以外に無い)。

### 実装の要点 (plan v2 §3.1〜3.2 と契約の対応)

1. **公開 surface は plan v2 §3.1 の署名どおり**にする。`TerminalEvidenceProjection` / `SealedTerminalEvidenceDraft` / `ValidatedTerminalEvidence` の 3 型と、`derive_terminal_projection()` / `seal_terminal_evidence(reservation, opened, terminal)` / `require_sealed_terminal_evidence(value)`。
2. **3 型の唯一の実データは immutable な canonical bytes** にする (契約 6.3)。`document` と `projection` は**アクセスごとに bytes から再生成**する。内部 bytes への参照を外へ返さない。発行台帳への membership を権威にしない。
3. **`require_sealed_terminal_evidence(value)` は既発行 capability の厳密検査**であり、**draft を validated へ昇格させる関数ではない** (契約 6.1)。`type(value) is ValidatedTerminalEvidence` を要求する (`isinstance` では駄目)。**leaf は昇格関数を持たない** — 昇格は実装子 2 が adapter へ置く。
4. **`attempt_binding` は 2 つの exact 集合**を持つ (契約 6.1)。draft は **exact 9 key** で、3 digest の key は **null ではなく key ごと存在しない**。validated は **exact 12 key**。3 digest の綴りは `classification_receipt_sha256` / `classification_event_sha256` / **`observation_event_sha256`** (契約 1.3。`observation_start_event_sha256` は行側の名前であり、ここでは使わない)。
5. **`campaign_record` は exact 30 key** を検査する (契約 1.5)。集合は `s8b_ratified_freeze._JOURNAL_KEYS["session"]` と**集合等値**であることを test で確かめる (production から `s8b_ratified_freeze` を import してはならない — import は 2 つだけの規定。test 側で照合する)。identity は契約 1.5 の **(a) 権威あり / (b) 権威なし / (c) 計測 / (d) 束縛** の 4 群へ分ける。**(b) の 6 語 (`event` `kind` `seq` `round` `trigger` `retry`) は平文へ載せず `unauthored_identity_sha256` 1 本へまとめ、E1 の判定入力に使わない。**
6. **平文と digest の分離は契約 1.1 の表どおり。** 最終 canonical bytes は既存の holdout-safe gate を通る形にする。**専用 bypass を作らない。** `workload` と `run_cmd` の平文を載せない (三軸走査に落ちる)。
7. **非有限値 (契約 1.4):** `throughputs` は有限 float だけの列。非有限の本数は `nonfinite_count`。不変条件は `len(throughputs) + nonfinite_count + exec_failures == reps_expected`。私有 sink を `s8b_floor_stats._derive_rep_integrity()` へ通して `rep_integrity_failures` を得る。**`assess_session()` へは有限のみの列と、元の `reps_expected` を渡す。落とした本数だけ `reps` を減らしてはならない** (減らすと欠測が健全に見える)。
8. **E1 は契約 4.1 の 6 枝を `if/elif` の順序で実装**する。辞書変換や `observed` fallback を置かない。E2 の 4 語は `measurement_environment_conflict` / `measurement_execution_unavailable` / `measurement_sample_incomplete` / `measurement_dispersion_exceeded`。**E1 は `terminal-failure` と `not-consumed` を出さない。** `campaign_record.excluded_reason` が再導出した campaign 語と一致しなければ拒否する。
9. **E1 の入力値域は launcher の捕捉集合** (契約 4.2)。`failure.exception_type` が `RuntimeError` / `subprocess.TimeoutExpired` / `OSError` の **3 語の exact member** であることを検査し、集合外の型名を拒否する。**「campaign が同じ入力で同じ語を出す」とは主張しない** — その旨を docstring へ書く。
10. **相互整合は契約 2 節の 5 条**をすべて実装する。破れたら `TerminalEvidenceError("[s8b-terminal-evidence] ...")` で拒否し、**`observed` へ落とさない。**
11. **digest はすべて再導出して等値検査**する。文書の自己申告値をコピーしない。`raw_output_sha256 == sha256(serialize_session_line(campaign_record))` の関係も検査する。
12. **`expected_use_perf` の新しい直接判定を置かない** (契約 9 節 / 親 brief 5 節)。launcher が発行した snapshot と receipt digest を照合するだけにする。**perf 述語の新しい直接 call を leaf に置くと `test_official_perf_closure.py` の semantic inventory (`:44` の `_REVIEWED_PERF_FILES` exact frozenset、`:531` の AST 走査、`:905` の集合等値 assert) が落ちる。generic helper の背後へ隠して test だけ緑にする逃げ方は取らない。** 落ちると判明したら実装せず報告する。
13. `exec_failures` は `campaign_record.exec_failures` との**等値でのみ束縛**し、「各 rep の実行成否を証明する」とは主張しない (契約 3 節)。docstring に射程を書く。

### test の要点 (plan v2 §3.3)

- exact schema、canonical bytes、全 digest、30-key trust root、identity の 4 群分離、draft 9 key / validated 12 key、非有限値、**E1 全枝**、`OSError` を含む捕捉集合、相互整合、immutable bytes、**constructor / `dataclasses.replace` 攻撃**を純関数レベルで閉じる。
- 30-key 集合は `s8b_ratified_freeze._JOURNAL_KEYS["session"]` との**集合等値**を検査する。
- **holdout-safe の正例と負例を対で置く。** `workload` または `run_cmd` の平文を戻した変異が既存 scanner (`assert_holdout_safe_bytes`) に拒否されることを示す。
- **親裁定 4.1 の変異 L1〜L18 を観測する node を必ず含める。** 各負例は「他の gate に遮られない」形にする (他の入力は valid にする)。**冗長 gate による赤は kill に数えられないので、負例ごとに「この入力を拒否する層が前後にも内側にも無い」ことを確かめ、確かめられない変異は完了報告にそう書け。**
- **D1522:** 上流が拒否する形でも、下層の実体 (E1 の枝関数、正規化関数、相互整合検査、digest 再導出) を**直接呼ぶ検査**を置く。
- **新規 test file なので自走 harness を必ず付ける。** 既存 file と同形式で、末尾に `if __name__ == "__main__": raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))` を置き、先頭で `_REPO_ROOT` を `sys.path` へ入れる。

### 規模上限

production 800〜900 行、test 650〜900 行。**超えそうなら止めて報告する。** 途中分割はしない。

## 検査・報告 (DW-S05-C)

- 実走は `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-leaf && PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py` (自走 harness) を使う。**`run_tests` は使うな (rc=16 になる)。`python3 -m pytest` は guard に拒否される。**
- **緑には実走 nodeid・範囲を併記する。** 実走不能なら `closed` と申告せず「実装済み・未実走」と書き、理由を書け。
- **テスト新設の単位は、親の名指しを網羅と見なさず制約 meta-test を自ら洗い出して走らせる。** 少なくとも `orchestrator/tests/test_pytest_collection_config.py` (test file 名の glob 走査がある)、`test_official_perf_closure.py`、`test_campaign_import_invariant.py` を確認する。新 test file 名を登録する必要がある登録簿を見つけたら**所有外なので実装せず報告する。**
- **fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。** 機構の正例・負例は実体を名指しし、依存先を stub しない。
- **期待値へ揮発 payload (working tree hash、時刻、絶対 path 等) を焼き込まない。**
- 完了報告に、**所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。**
- **指示外の受理集合変更をしない。**
- **契約 v3.1 の条項が実体化できないと判断したら、回避策を自作せず止めて報告しろ。** 前 wave は契約 v2 でこの型を踏み、実装 0 行で終わっている。「どの条項が、どの consumer の何に阻まれるか」を現物の file:line で書け。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。

## 総括

最後に `## 総括` 節を置き、次を書く。

- 実装した公開 surface の一覧 (signature)
- 実走した nodeid の範囲と結果 (緑 / 赤 / 未実走)
- L1〜L18 のうち「単一理由で殺せる」と確かめられた変異と、確かめられなかった変異
- 所有外への波及可能性 (静的列挙)
- 契約のうち実体化できなかった条項 (あれば file:line つき)
- production / test の実行数 (行数)
