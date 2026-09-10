単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2`
- **親の段 4 裁定**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 段 6 レビュー B (この所見の出所): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s6-reviewB.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2/CLAUDE.md`

# 段 6 fix 3 — 変異 M6 を殺す単一理由の負例を置く

## 所有する file (これ 1 つだけ。他の追跡下 file を 1 つも変更しない)

```
orchestrator/tests/test_s8b_floor_campaign.py
```

**`git` を一切実行しない。commit しない。** `docs/` と `output/` を触らない。
**production file を 1 行も変更しない。** 新しい file も作らない。

## 実測した穴 (親が変異走行で確認)

親が 13 件の変異を実走した結果、**M6 だけが SURVIVED した** (他は全件 kill された)。

M6 は `orchestrator/campaign/s8b_floor_campaign.py` の `_project_scalepoint()` にある
`complete` 述語から、**最後の連言 `and observation.get("execution_failure") is False` を
外す**変異である。

```python
        complete = (
            set(observation) == {
                "rep_index", "returncode", "counter_status", "missing_perf_events",
                "perf_raw", "throughput", "execution_failure",
            }
            ...
            and derived_status in {"complete", "not_required"}
            and observation.get("execution_failure") is False   # <- これを外す
        )
```

**この連言を外しても、現在どの test も赤にならない。**
つまり「runner が例外を捕捉した rep を complete と数えない」という保証が、
campaign の射影側では**発火していない**。これは正しさ防壁の穴である
(rc=0 のまま実行失敗した rep が qualified throughput に混ざりうる)。

## やること

**この連言だけを殺す単一理由の負例を 1 つ置く。**

負例の入力は、次を**すべて**満たすこと。

- `set(observation)` が exact 7 key (集合検査を通る)
- `rep_index` が exact int で期待位置と一致 (その検査を通る)
- `returncode` が exact int の **0** (その検査を通る)
- `counter_status` が `derived_status` と一致 (その検査を通る)
- `missing_perf_events` が `missing` と一致 (その検査を通る)
- `perf_raw` が 4 イベント完備で `raw_complete` が真 (その検査を通る)
- `derived_status` が `complete` または `not_required` (その検査を通る)
- **`execution_failure` が exact `True`**

つまり **`execution_failure is False` の連言だけが `complete` を偽にする**入力である。
**他の連言が先に偽になる入力を使ってはならない** (それでは M6 を殺せない)。

期待する挙動を exact に固定すること。

- その rep は `complete` にならないので `rep_integrity_failures` に数えられる
- その rep の throughput は qualified に入らない
- `exec_failures` は `execution_failure is True` の本数

`_project_scalepoint()` は `observed_tps != source_throughputs` で `CampaignAbort` を投げるので、
**`ScalePoint.throughputs` と observation の throughput 列を整合させること。**
`execution_failure=True` の rep の throughput をどう置くかは、この整合と、
実 runner の挙動 (例外を捕捉した rep は throughput を持たない) の両方に合わせること。
**実 runner の生成箇所を自分で開いて確かめること。推測で書かない。**

## 禁止

- `git` を実行しない。commit しない。
- `orchestrator/tests/test_s8b_floor_campaign.py` 以外の追跡下 file を 1 つも変更しない。
- **production の挙動を変えない。** production を直したくなったら、直さずに報告して止まる。
- **テストを甘くして緑にしない** (F27)。既存 test の期待値の反転・緩和・skip・削除をしない。
- 期待値へ揮発 payload (hash・時刻・絶対 path) を焼き込まない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix2
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
```

自走 harness が無くて収集 0 件になる場合は、**harness を新設せず**、
新設 test 関数を import して直接呼ぶ最小の一時 script を作業 root 直下に作り、
確認後に削除すること。一時 file を残さないこと。

**さらに、置いた負例が本当に M6 を殺すことを自分で確かめること。**
production を編集せずに確かめる方法として、
`s8b_floor_campaign._project_scalepoint` と同じ計算を、
`execution_failure is False` の連言を抜いた形で test 内に書き下し、
**同じ入力に対して結果が変わること**を示せばよい (production は触らない)。

**緑には実走 nodeid を必ず併記する。** 走らせていないものを緑と書かない。

## 出力形式 (この見出しをこの順で使う)

## 実 runner が例外捕捉 rep で出す形の実測
## 置いた負例 (file:line) とその入力
## 他の連言が先に偽にならないことの根拠
## M6 を殺すことの確認方法と結果
## 実走した nodeid と結果
## 総括
