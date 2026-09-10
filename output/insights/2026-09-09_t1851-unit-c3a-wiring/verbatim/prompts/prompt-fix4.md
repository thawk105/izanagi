単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。編集は所有 path だけ)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix4`
- 親の段 4 裁定: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix4/CLAUDE.md`

# 段 6 fix 4 — 変異走が暴いた恒真な検査 1 件を強化する

## 所有 path (編集はこの 1 つだけ)

- `orchestrator/tests/test_s8b_floor_campaign.py`

**production code は変更しない。docs は編集しない。commit しない。`git add` もしない。**

## 親が実測した恒真性

変異 `repetition=round_no - 1,` → `repetition=round_no,`
(`orchestrator/campaign/s8b_floor_attempt_launcher.py` の registry plan 構築) を注入して走らせたところ、
**`test_registry_plan_maps_round_to_zero_based_repetition` は赤にならなかった。**

原因は現在の assertion にある (`orchestrator/tests/test_s8b_floor_campaign.py:14968-14998`)。

- `row["round"] == protocol["n_sessions"]` すなわち**最終 round** の行を選び、
- `(holdout_id, configuration_id, row["round"] - 1, 0, 0)` が slot 集合に**含まれること**だけを検査する。

0 始まり (`round-1`) の集合は `0..n_sessions-1`、1 始まり (`round`) の集合は `1..n_sessions` である。
**最終 round の `round-1` = `n_sessions-1` はどちらの集合にも含まれる。** だからこの検査は
どちらの実装でも通る。名前が謳う「round を 0 始まりの repetition へ写す」性質を守っていない。

(この変異自体は `test_registry_plan_declares_exact_planned_and_retry_slot_closure` など 8 node が
落として KILLED になった。したがって**性質そのものは別の検査で守られている**。本 fix の目的は、
名前が謳う保証を実際に発火させることである。)

## 直す内容

`test_registry_plan_maps_round_to_zero_based_repetition` を、**0 始まりと 1 始まりを判別する**
検査へ直す。少なくとも次の 2 つを含めること。

- repetition `0` を持つ slot が**存在する** (1 始まりでは存在しない)
- repetition `n_sessions` を持つ slot が**存在しない** (1 始まりでは存在する)

`round` と `repetition` の対応を 1 行の等式として書き、最終 round だけでなく**最初の round** も
確かめること。

## 禁止

- production code を 1 行も変えない。
- 他の test を弱めない・削らない・skip しない。
- 所有外 file を編集しない。
- 期待値へ揮発 payload を焼き込まない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。** 自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix4
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
```

さらに、**強化した検査が実際に発火することを自分で確かめる**。
`orchestrator/campaign/s8b_floor_attempt_launcher.py` の `repetition=round_no - 1,` を
一時的に `repetition=round_no,` へ書き換えて当該 test を走らせ、**赤になることを実測**し、
**必ず元へ戻す** (最終差分に production の変更を残さない。`git diff` で 0 行であることを示す)。

## 出力形式

```
## 総括
(3-5 行)

## 直した assertion (file:line と、0 始まり / 1 始まりを判別する根拠)

## 強化後に変異が赤になることの実測
(一時変異の内容、走らせた command、passed/failed の実数、復元の確認)

## 実走結果 (command と passed/failed の実数)

## 残った懸念
```
