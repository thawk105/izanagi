単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2`
- **親の段 4 裁定 (これが正本)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 前の子へ渡した投げ文 (作業内容の定義): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/prompt-s5-child2.md`
- 実装子 1 の報告: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s5-child1.md`
- 段 3 レンズ A: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s3-lensA.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/CLAUDE.md`

# 段 5 実装子 2 の継続 — 実走と仕上げ

**前の子は wall-clock 上限に当たって SIGTERM で落ち、報告を 1 byte も書けずに終わった。**
**しかし作業 root には差分が残っている。** あなたはその続きをやる。

**前の子の作業は信用しきらず、自分で現物を読んで確かめること。**
説明と実装が食い違っていたら、実装を正とし、食い違いを報告すること。

## 所有する file (これ以外の追跡下 file を 1 つも変更しない)

```
orchestrator/campaign/s8b_floor_campaign.py
orchestrator/campaign/s8b_floor_stats.py
orchestrator/campaign/s8b_terminal_evidence.py
orchestrator/tests/test_s8b_floor_campaign.py
orchestrator/tests/test_s8b_floor_stats.py
orchestrator/tests/test_s8b_terminal_evidence.py
```

**`git` を一切実行しない。commit しない。** `docs/` と `output/` を触らない。
**新しい production file も新しい test file も作らない。**

## 親が既に現物で確認した状態 (再確認は要らないが、誤りと判れば指摘すること)

| 裁定項目 | 現状 |
|---|---|
| S2 (notes regex の除去) | `_EXEC_FAIL_RE` と `_count_exec_failures` は**除去済み** |
| S3 (7 key 化と 4 値返却) | `_REP_OBSERVATION_KEYS` は 7 key、`_derive_rep_integrity()` は `tuple[list, int, int, tuple]` |
| B1 (本数式の作り直し) | `s8b_terminal_evidence.py` の本数式は `other_integrity_failures` を分離し、`exec_failures > rep_integrity_failures` を拒否する形へ**変更済み** |
| B2 (矛盾条件) | `execution_failure=True` かつ `throughput` 非 null を error にする条件が**入っている** |
| B3 (padding) | carrier 欠落 padding は `False` ではなく `None` を置いている |
| B4 (返値 arity の閉包) | `s8b_terminal_evidence.py` の 2 箇所 (`:642` と `:1047` 付近) が追随済み |
| B6 (FORMULA_ID) | **`FORMULA_ID` は変更されていない** |

## あなたがやること

### 1. 未完の実装を仕上げる

前の子が終えられなかった部分を洗い出して仕上げる。とくに次を自分で確かめること。

- **B7 — 旧 6-key の observation が改訂後に拒否される負例**が置かれているか。
  無ければ置く (受理集合は狭まる方向にしか動かない。D1660 と同じ向き)。
- resume gate (`s8b_floor_campaign.py` の `_derive_rep_integrity` を呼ぶ箇所) が
  top-level `exec_failures` と再導出値の等値を検査しているか。
- `_derive_rep_integrity()` の callsite が**全部**追随しているか (自分で再走査する)。

### 2. B6 の gate を実際に判定する (**最重要**)

**producer が実際に出しうる入力すべてで**、
`exec_failures` / `rep_integrity_failures` / qualified throughputs / session median が
**改訂前後で一致する**ことを test で示すこと。

- 一致を示せた場合だけ `FORMULA_ID` を**据え置く**。
- **1 つでも値が動く入力があれば、そこで実装を止めて報告すること。**
  **`FORMULA_ID` を書き換えてはならない。** `s8b_floor_contract.py` は所有外である。
  凍結成果物 `output/s8b-freeze/floor_protocol.json` の bytes に届くため、親がユーザー裁定へ返す。
- 判定の根拠を、**どの入力集合をどう網羅したか**まで書くこと。「変えていないから同じ」では足りない。

### 3. 実走する (前の子は 1 度も走らせられていない)

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_stats.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
```

**`run_tests` は使わない (rc=16 になる)。`python3 -m pytest` は guard に拒否される。**
**成長 hold (`GrowthTestHoldBypassRefused`) が出た file は迂回せず、走らせずに報告すること。**
**緑には実走 nodeid・範囲を必ず併記する。** 実走できなかったものは `closed` と申告せず
「実装済み・未実走」と書き、理由を書くこと。**走らせていないものを緑と書かない。**

赤が出たら直す。ただし**所有外由来の赤は直さない**。
子 3 が所有する fixture / test の observation literal はまだ 6 key なので、
`s8b_v2_freeze_fixture.py` 由来の holdout / oracle 系、`test_s8b_attempt_registry.py`、
`test_s8b_floor_attempt_launcher.py`、`test_s8b_ratified_freeze.py`、
`test_s8b_ratified_verify.py` は赤のままでよい。**xfail 化しない。期待値も変えない。**

### 4. 時間配分

**wall-clock は 7200 秒ある。前の子は 3600 秒で落ちた。**
**実走と報告を最優先にすること。** 実装の磨き込みで時間を使い切ってはならない。
**残り時間が少ないと感じたら、その時点の結論を下の出力形式どおりに書いて終わること**
(無出力が最悪であり、前の子はそれで 1 時間を無駄にした)。

## 禁止

- `git` を実行しない。commit しない。
- 所有 6 file 以外の追跡下 file を 1 つも変更しない。
- `docs/` と `output/` を触らない。新しい file を作らない。
- **`FORMULA_ID` を書き換えない。**
- テストを甘くして緑にしない (F27)。機構の正例・負例は実体を名指しし依存先を stub しない (F649)。
- 期待値へ揮発 payload (hash・時刻・絶対 path) を焼き込まない。
- 指示外の受理集合変更をしない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う)

## 前の子の実装で確かめたこと・食い違い
## 仕上げた箇所 (file:line)
## B6 — FORMULA_ID gate の判定と網羅の根拠
## B7 — 旧 6-key の負例
## 実走した nodeid と結果
## 期待どおりの赤 (所有外由来)
## 所有外への波及可能性 (静的列挙)
## 総括
