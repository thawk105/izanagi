単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3`
- 親の段 4 裁定: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/CLAUDE.md`

# 段 6 fix 4 — 行番号 pin の台帳を新しい行番号へ追随させる

## 所有する file (これ 1 つだけ。他の追跡下 file を 1 つも変更しない)

```
orchestrator/tests/test_ccbench_spawn_sites.py
```

**`git` を一切実行しない。commit しない。** `docs/` と `output/` を触らない。
**production file を 1 行も変更しない。** 新しい file も作らない。

## 親が実測した事象

受入全走で 3 node が赤になった。**親が local main 単独でも同じ file を走らせて 44 passed を
確認しているので、この 3 件は本 wave に帰属する。**

赤の 3 node:

- `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
- `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- `test_define_sink_cross_product_has_no_unreviewed_ungated_member`

**原因は行番号 pin である。** 同 file の `_DEFERRED_GATE_MEMBERS` の期待集合は
`(relative_path, owner, sink_kind, sink_scope, sink_lineno)` の 5 つ組で、
**`sink_lineno` を exact に持っている。**

本 wave は `orchestrator/campaign/s8b_floor_campaign.py` から
`_EXEC_FAIL_RE` と `_count_exec_failures` (14 行) を除去し、代わりに数行を足したので、
**それより下の行番号が差し引き 8 行ずれた。**

## 親が現物で実測した新しい行番号

| sink | 台帳の旧値 | 現物の実測値 |
|---|---:|---:|
| `orchestrator/campaign/s8b_floor_campaign.py` `<module>.build_cells.invoke_build` (`injected-build_fn`) | 4715 | **4707** (`return build_fn(genome, **call_kwargs)`) |
| `orchestrator/campaign/s8b_floor_campaign.py` `<module>.main` (`campaign`) | 8642 | **8636** (`outcome = run_campaign(`) |

**自分でも開いて照合すること。** 親の値と食い違ったら、実測を正として報告すること。

## やること

1. **`s8b_floor_campaign.py` に関する台帳 entry の `sink_lineno` だけを、実測した現物の
   行番号へ直す。**
2. **他の file の entry を 1 つも変えない。** 本 wave は
   `b10_backoff_shape_sweep.py`、`paper_story_a1_paired.py`、`s8b_oracle_n_pilot.py`、
   `tools/pegasus/probes/` のいずれも変更していない。
3. **`owner`、`sink_kind`、`sink_scope`、`relative_path` を変えない。**
   変えるのは行番号だけである。
4. 3 node がすべて緑になることを確かめる。

## 禁止 (とくに重要)

- **台帳から entry を削除しない。追加もしない。** 件数を変えない。
- **期待値の反転・緩和・skip・削除をしない** (F27)。
  行番号以外を直したくなったら、直さずに報告して止まること。
- **production file を変更しない。** production を直せば直るように見えても、
  それは pin の側が現物へ追随すべき場面である。
- `git` を実行しない。commit しない。
- 所有 1 file 以外の追跡下 file を 1 つも変更しない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3
PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py
```

自走 harness が無くて収集 0 件になる場合は、**harness を新設せず**、
対象 3 関数を import して直接呼ぶ最小の一時 script を作業 root 直下に作り、
確認後に削除すること。一時 file を残さないこと。

**緑には実走した関数名・nodeid を必ず併記する。** 走らせていないものを緑と書かない。

## 出力形式 (この見出しをこの順で使う)

## 台帳の構造と行番号 pin の位置
## 実測した現物の行番号 (親の値との照合)
## 直した entry (file:line と旧値 → 新値)
## 変えていないこと (件数・他 file・行番号以外の field)
## 実走した関数と結果
## 総括
