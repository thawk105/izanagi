単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s3`
- **親の段 4 裁定 (これが正本)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 実装子 1 の報告: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s5-child1.md`
- 実装子 2 の報告 (継続子の分): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s5-child2b.md`
- 実装子 2 の後の fix 報告: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s6-fix1.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s3/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s3/CLAUDE.md`

# 段 5 実装子 3 — fixture と consumer の 7-key 追随

実装子 1 (runner) と実装子 2 (campaign / stats / terminal evidence) は**適用済み**である。
本子は**残った fixture と consumer test を新しい schema へ追随させる**。

## 所有する file (これ以外の追跡下 file を 1 つも変更しない)

```
orchestrator/tests/s8b_v2_freeze_fixture.py
orchestrator/tests/test_s8b_attempt_registry.py
orchestrator/tests/test_s8b_floor_attempt_launcher.py
orchestrator/tests/test_s8b_ratified_freeze.py
orchestrator/tests/test_s8b_ratified_verify.py
orchestrator/tests/test_backoff_extended_sweep.py
```

**`git` を一切実行しない。commit しない。**
`docs/` と `output/` を触らない。**新しい production file も新しい test file も作らない。**

## 実装内容

1. **所有 file 内の rep observation literal をすべて 7 key にする。**
   足す key は `execution_failure` で、型は exact `bool`。
   **正常な rep には `False`** を置く。実行例外を模す rep があれば `True` を置く。
   親が実測した literal の位置は次のとおり (自分で開いて照合すること)。

   - `s8b_v2_freeze_fixture.py:155` 付近
   - `test_s8b_attempt_registry.py:347` 付近
   - `test_s8b_floor_attempt_launcher.py:238`、`:864`、`:868`、`:872`、`:944`、`:1410` 付近
   - `test_s8b_ratified_freeze.py:530` 付近
   - `test_s8b_ratified_verify.py:377` 付近

   **`test_s8b_floor_attempt_launcher.py:864` 付近には tuple / dict の全件等値がある。**
   期待値の更新が要る。**受理集合を変える形の更新をしないこと** — 変えるのは
   observation の key 集合への追随だけである。

2. **B5 — `pipeline.py:2794-2866` が subset consumer であることを test で固定する。**
   同 file は所有外なので**変更しない**。`test_backoff_extended_sweep.py` 側に、
   **7 key の observation でも subset 読みの consumer が壊れない**ことを確かめる test を足す。
   実体を名指しし、依存先を stub で置き換えないこと (F649)。

## 禁止事項 (とくに重要)

- **テストを甘くして緑にしない。** fixture へ現行 hash を差し込む形の緑は採らない (F27)。
- **期待値へ揮発 payload (working tree の hash、時刻、絶対 path) を焼き込まない。**
- **指示外の受理集合変更をしない。** scope に入る前に、現行の受理・拒否挙動を出力へ書くこと。
- **既存の 64hex literal を書き換えない。**
  親と段 3 の両レンズが独立に確かめたところ、`s8b_v2_freeze_fixture.py` の observation は
  `test_s8b_oracle_driver.py` / `test_s8b_oracle_manifest.py` / `test_s8b_oracle_report.py` の
  既存 64hex literal へ**伝播しない** (それらは schedule / spec / generator source の digest で、
  `_synthetic_floor_result()` を使うのは holdout freeze だけであり、そこでは digest を
  その場で再計算する)。
  **もし digest literal を書き換えないと緑にならない箇所が出たら、書き換えずに報告すること。**
  それは親の前提が崩れたことを意味する。
- `git` を実行しない。commit しない。
- 所有 6 file 以外の追跡下 file を 1 つも変更しない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s3
PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_ratified_freeze.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_ratified_verify.py
PYTHONPATH=. python3 orchestrator/tests/test_backoff_extended_sweep.py
```

fixture の consumer も走らせること。

```
PYTHONPATH=. python3 orchestrator/tests/test_s8b_holdout_freeze.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_oracle_driver.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_oracle_manifest.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_oracle_report.py
```

**`run_tests` は使わない (rc=16 になる)。`python3 -m pytest` は guard に拒否される。**
**成長 hold (`GrowthTestHoldBypassRefused`) が出た file は迂回せず、走らせずに報告すること。**
**緑には実走 nodeid・範囲を必ず併記する。** 実走できなかったものは `closed` と申告せず
「実装済み・未実走」と書き、理由を書くこと。

## 出力形式 (この見出しをこの順で使う)

## 変更前の受理・拒否挙動
## 追随した literal (file:line)
## B5 の固定
## 実走した nodeid と結果
## 64hex literal を書き換えずに済んだか
## 残った赤とその帰属
## 所有外への波及可能性 (静的列挙)
## 総括
