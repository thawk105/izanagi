単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2`
- **親の段 4 裁定**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 直前の子の報告 (B6 が不成立と判定した根拠): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s5-child2b.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/CLAUDE.md`

# 段 6 fix 1 — B6 の gate test を真の characterization test へ書き換える

## 所有する file (これ 1 つだけ。他の追跡下 file を 1 つも変更しない)

```
orchestrator/tests/test_s8b_floor_stats.py
```

**`git` を一切実行しない。commit しない。** `docs/` と `output/` を触らない。
**production file を 1 行も変更しない。** 新しい file も作らない。

## 何が起きたか (親が実走で確認済み)

`test_formula_v2_outputs_are_unchanged_for_every_producer_outcome_class` は
「改訂前後で値が変わらない」と主張するが、**その主張は偽である**。
親の独立実走 (674 passed / 1 failed) で、赤はこの 1 node だけだった。

```
assert (1, 1, (100.0, 101.0)) == (1, 0, (100.0, 101.0))
                 ^                       ^
At index 1 diff: 1 != 0
```

tuple は `(exec_failures, rep_integrity_failures, qualified_throughputs)` である。

- `exec_failures` は**変わらない** (1 == 1)
- qualified throughputs は**変わらない** ((100.0, 101.0) == (100.0, 101.0))
- **`rep_integrity_failures` だけが 0 から 1 へ変わる**

変わるのは `post_spawn_execution_exception` の class、すなわち
「subprocess は rc=0 で終わったが、その後の stdout 解析で例外を捕捉した rep」である。
旧実装はこれを complete と数えていた (throughput が `None` でも rc=0 と counter 完備だけで
complete としていた)。改訂後は `execution_failure is False` が必要なので integrity failure に数える。
**受理集合が狭まる向きの訂正である。**

## やること

**この test を、偽の主張を捨てて、実際の差分を正確に固定する形へ書き換える。**

新しい test は、producer が出しうる全 outcome class の直積について、次を**すべて**主張すること。

1. **`exec_failures` は改訂前後で一致する。**
2. **qualified throughputs は改訂前後で一致する。**
3. **したがって session の有効性判定と median は改訂前後で一致する。**
   (有効性は `excluded_reason` と `exec_failures` と throughputs だけで決まる。
   `orchestrator/campaign/s8b_floor_stats.py` の該当 docstring を自分で読んで確かめること。)
4. **`rep_integrity_failures` は、`execution_failure is True` の rep を含む combination で
   ちょうどその本数だけ増え、それ以外の combination では一致する。**
   「増えることがある」という緩い主張にしない。**増分を exact に固定すること。**

test 名も内容に合わせて変える (例: 変わらない量と変わる量を両方名指しする名前)。
**「変わらない」とだけ主張する名前を残さない。**

### 守ること

- **production の値を test に合わせて変えない。** production file は所有外である。
- **テストを甘くして緑にしない** (F27)。差分を `pytest.approx` や部分一致でぼかさない。
- **機構の正例・負例は実体を名指しし、依存先を stub で置き換えない** (F649)。
- 期待値へ揮発 payload (hash・時刻・絶対 path) を焼き込まない。
- 直積の網羅範囲 (outcome class の一覧と rep 数) を**縮めない**。
  `post_spawn_execution_exception` を一覧から外して緑にするのは**禁止**である。

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2
PYTHONPATH=. python3 -c "import sys" 2>/dev/null || true
```

この file には `__main__` 自走 harness が無く、直接実行では収集 0 件になる
(前の子が実測済み)。**その場合は「自走 harness が無いので単独実走できない」と書き、
harness を新設しないこと** (所有 file の末尾へ harness を足すと、
新規 node 名の登録簿追随が所有外で発生しうる)。

**代わりに、書き換えた test 関数を直接呼び出して緑を確かめること。**
例: `PYTHONPATH=. python3 -c` は guard に拒否されるので、
`PYTHONPATH=. python3 - <<` も使わず、**小さな一時 file を作業 root の外へは作れないため、
関数を import して呼ぶ最小の一時 script を作業 root 直下に作り、確認後に削除する。**
一時 script を残さないこと。

**緑には実走した関数名と結果を必ず併記する。** 実走できなかったものは
「実装済み・未実走」と書き、理由を書くこと。**走らせていないものを緑と書かない。**

## 禁止

- `git` を実行しない。commit しない。
- `orchestrator/tests/test_s8b_floor_stats.py` 以外の追跡下 file を 1 つも変更しない。
- production の挙動を変えない。
- outcome class の一覧を縮めない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う)

## 旧 test が主張していたこと
## 新 test が固定すること (変わらない量 / 変わる量)
## 網羅した outcome class の一覧
## 実走した関数と結果
## 残した一時 file (無ければ「無し」)
## 総括
