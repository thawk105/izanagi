単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2`
- **親の段 4 裁定 (これが正本)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s1-brief.md`
- 段 3 レンズ A (正しさ境界の所見): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s3-lensA.md`
- 段 3 レンズ B (閉包の所見): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s3-lensB.md`
- 実装子 1 の報告: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s5-child1.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/CLAUDE.md`

# 段 5 実装子 2 — 算出と信頼 gate

裁定の **S2 / S3 / B1 / B2 / B3 / B4 / B6 / B7** を実装する。
**実装子 1 の S1 (runner) は適用済み**である。作業 root の `orchestrator/calibrator/runner.py` は
既に 7 key を出す。**runner を触らない。** 子 3 の所有 file も触らない。

## 所有する file (これ以外の追跡下 file を 1 つも変更しない)

```
orchestrator/campaign/s8b_floor_campaign.py
orchestrator/campaign/s8b_floor_stats.py
orchestrator/campaign/s8b_terminal_evidence.py
orchestrator/tests/test_s8b_floor_campaign.py
orchestrator/tests/test_s8b_floor_stats.py
orchestrator/tests/test_s8b_terminal_evidence.py
```

**`git` を一切実行しない。commit しない。**
`docs/` と `output/` を触らない。**新しい production file を作らない**
(`test_official_perf_closure.py` の exact inventory と `test_t671_source_binding.py` の
63 path 件数 assert が落ちる)。

## 実装内容

### S2 — campaign の算出を構造化 field へ移す

- `_EXEC_FAIL_RE` (`s8b_floor_campaign.py:1879`) と `_count_exec_failures` (`:1882-1891`) を
  **唯一の呼び手 (`:1965`) ごと除去する。** `re` の import は他で使うので残す。
- `_project_scalepoint` は `execution_failure is True` の本数を `exec_failures` とする。
- `complete` 述語 (`:1947` 付近) の exact 集合を 7 key にし、`execution_failure is False` を加える。
- **自然文 note は残してよいが、どの算出の入力にもしない。**

### S3 — 中央 verifier も独立に再導出する

- `s8b_floor_stats.py:64-67` の `_REP_OBSERVATION_KEYS` を 7 key にする。
  `:487` の exact 比較はそのまま維持する。
- `_derive_rep_integrity()` (`:471`) を 4 値
  `(errors, rep_integrity_failures, exec_failures, qualified)` へ拡張する。
- `execution_failure` が exact `bool` でない値 (`0` / `1` / `None` / 文字列) は schema error にする。
- `:897` 近傍と `s8b_floor_campaign.py:8368-8389` の resume gate で、
  top-level の `exec_failures` と再導出値の等値を検査する。

### B1 — terminal の本数式を作り直す (最重要)

`s8b_terminal_evidence.py:856` の
`len(throughputs) + nonfinite_count + exec_failures != reps_expected` は、
`exec_failures` を「欠格 rep の代理」に使っており、契約 3 節が分けろと言う 2 量を再結合している。

**具体的な破れ** (段 3 レンズ A が出し、親が裏取りした):

- `reps_expected=2`、rep0 は rc=0 / throughput=100、rep1 は **rc=7** / throughput=101、
  counter は両方 `not_required` の場合。正しい導出は
  `qualified=(100,)`、`exec_failures=0`、`rep_integrity_failures=1` だが、
  この式は `1 + 0 + 0 != 2` で**正当な分離状態を拒否する**。
- 逆に rep1 の flag だけを偽って `True` にすると `1 + 0 + 1 == 2` で**通ってしまう**。

**作り直しの要件:**

- sink の各 rep を finite / nonfinite / execution-failure / その他 integrity failure へ
  **別々に**分類し、本数を独立に数える。
- **非 execution の integrity failure を持つ session が sealed terminal へ運べるようにする。**
- `exec_failures` を他の欠格要因の代理に使わない。
- 既存の `failure is not None` 側の分岐 (`:862-870`) の意味を変えない。

### B2 — `execution_failure=True` と成功情報の矛盾を拒否する

`execution_failure is True` の rep が qualified / complete になれない条件を置く。
**producer が実際に保証する関係を署名で書く** — 例外を捕捉した rep は
`throughput` を持たない、など、実装子 1 が入れた runner の実挙動と一致させること
(`s5-child1.md` を読んで実挙動を確かめる。推測で書かない)。

**gate の禁止は署名で書き、通る正例を 1 つ添えること。**

### B3 — carrier 欠落の padding に `False` を書かない

`s8b_floor_campaign.py:1898-1913` の証跡 carrier 欠落 padding は、
「runner が例外を捕捉しなかった」を**観測できていない**。ここに `False` を書くと未観測事実の捏造になる。
既存の unavailable projection と同じ向きで **fail-closed** にすること。
`False` を書いた場合に terminal の理由が `launch_failure` から
`nonfinite_or_partial_output` へ変わる経路がある (レンズ A の実測)。これを起こさないこと。

### B4 — `_derive_rep_integrity()` の返値 arity 変更の閉包を閉じる

**`s8b_terminal_evidence.py:1030` が 3 値 unpack をしている。** 追随しないと `ValueError` になる。
test 側の consumer は `orchestrator/tests/test_s8b_terminal_evidence.py:468` と `:479`。
**自分で全 callsite を再走査して、他に無いことを確かめること。**

### B6 — FORMULA_ID の版境界 (**これに触れたら止めて報告する**)

`s8b_floor_stats.py:16-19` は「式を変えるときは FORMULA_ID を改版する」と書き、
式には**セルの有効性契約が含まれる**。`FORMULA_ID = "s8b-floor-stats/v2"` は
`s8b_floor_stats.py:51` と `orchestrator/campaign/s8b_floor_contract.py:44` にあり、
`:476` が一致を要求し、`s8b_floor_campaign.py:1310` が protocol へ書き込む。
その protocol は **`output/s8b-freeze/floor_protocol.json` として凍結され、
`orchestrator/tests/test_frozen_artifacts.py:44-49` の `FROZEN_MANIFEST` が sha256 を pin している。**

**gate:** **producer が実際に出しうる入力すべてで**、
`exec_failures` / `rep_integrity_failures` / qualified throughputs / session median が
**改訂前後で一致する**ことを test で示すこと。

- 一致を示せた場合だけ `FORMULA_ID` を**据え置く**。
- **1 つでも値が動く入力があれば、そこで実装を止めて報告する。**
  **`FORMULA_ID` を書き換えてはならない。** `s8b_floor_contract.py` は所有外でもある。
  凍結成果物の再発行は親がユーザー裁定へ返す。

### B7 — 旧 6-key 入力が拒否されることの負例

改訂後に旧 6-key の observation が**拒否される**ことを負例で固定する。
resume 経路で旧 journal が fail-closed になることは設計どおりである
(受理集合は狭まる方向にしか動かない。D1660 と同じ向き)。

## テスト

**テストを甘くして緑にしない。** fixture へ現行 hash を差し込む形の緑は採らない (F27)。
**機構の正例・負例は実体を名指しし、依存先を stub で置き換えない** (F649)。
**期待値へ揮発 payload (working tree の hash、時刻、絶対 path) を焼き込まない。**
**指示外の受理集合変更をしない。scope に入る前に、現行の受理・拒否挙動を出力へ書くこと。**

`exec_failures` と `rep_integrity_failures` が別の量であり続けることを、次で固定する。

- 実行例外の rep: `exec_failures == 1` かつ `rep_integrity_failures == 1`
- **非 zero rc だけの rep: `exec_failures == 0` かつ `rep_integrity_failures == 1`**
- notes に `"5/5 reps failed to execute"` を注入しても flag が全 `False` なら `exec_failures == 0`
- notes が空でも flag が `True` なら `exec_failures == 1`

## 期待される赤 (直してはならない)

子 3 が所有する fixture / test の observation literal はまだ 6 key である。
そのため次が赤になる。**xfail 化しない。既存の期待値を変えない。**

- `orchestrator/tests/s8b_v2_freeze_fixture.py` 由来の holdout / oracle 系
- `test_s8b_attempt_registry.py`、`test_s8b_floor_attempt_launcher.py`、
  `test_s8b_ratified_freeze.py`、`test_s8b_ratified_verify.py`

**赤の内訳 (nodeid と理由) を完了報告に列挙し、所有外由来か自分の実装由来かを切り分けること。**

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_stats.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
```

**`run_tests` は使わない (rc=16 になる)。`python3 -m pytest` は guard に拒否される。**
**緑には実走 nodeid・範囲を必ず併記する。** 実走できなかったものは `closed` と申告せず
「実装済み・未実走」と書き、理由を書くこと。

制約 meta-test を自分で洗い出して走らせること。少なくとも
`orchestrator/tests/test_official_perf_closure.py`、
`orchestrator/tests/test_campaign_import_invariant.py` を確認する。

## 禁止

- `git` を実行しない。commit しない。
- 所有 6 file 以外の追跡下 file を 1 つも変更しない。
- `docs/` と `output/` を触らない。新しい production file を作らない。
- **`FORMULA_ID` を書き換えない。**
- 既存テストの期待値を変えない。xfail を足さない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 出力形式 (この見出しをこの順で使う)

## 変更前の受理・拒否挙動
## S2 の実装 (file:line)
## S3 の実装 (file:line)
## B1 — 本数式の作り直し
## B2 — 矛盾条件と通る正例
## B3 — padding の fail-closed 化
## B4 — 返値 arity の閉包 (全 callsite)
## B6 — FORMULA_ID gate の判定
## B7 — 旧 6-key の負例
## 実走した nodeid と結果
## 期待どおりの赤 (所有外由来)
## 所有外への波及可能性 (静的列挙)
## 総括
