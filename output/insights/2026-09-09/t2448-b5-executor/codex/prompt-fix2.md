単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix2

**あなたの編集対象 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix2` である。**
他の worktree の path を書き換えてはならない。

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage6.md (段 6 裁定)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage4.md (段 4 の実装契約。継承する)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix2/orchestrator/tests/test_axis_b5_search_executor.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix2/orchestrator/axis_b5_search/preflight.py

## 直す欠陥 (親が変異本走で実測した)

`test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal` は、
**実 repo の共有 tree へ `orchestrator/axis_b5_search/__pycache__/axis_b5_registration_probe.pyc` を
書き込み、検査後に消す**作りになっている。

この test は xdist で並行実行されるため、同じ実 repo root を読む別 test
(`test_live_preflight_accepts_exact_30_and_wid_drift_is_evidence_only`) が、
その `.pyc` が存在する瞬間に `registered_path_set_mismatch` で落ちる。

親の実測 (変異走行の 2 回):
- 1 回目 (probe): 赤 node は `test_registration_accepts_...` の 1 件だけ。
- 2 回目 (本走): 赤 node は上記 2 件。worker `gw1` が probe file を作っている間に
  worker `gw27` が実 repo を読んだ。

**つまり赤 node 集合が走行ごとに変わる。** 共有状態への書き込みによる非決定的な相互干渉であり、
受入の全走でもランダムに赤を出す。

## 直し方 (この形で直す)

検査を 2 つに分ける。**共有 tree へ書き込む test を無くす。**

1. **決定的な単位 test (新規または既存の付け替え):**
   `__pycache__` と `.pyc` を除外する走査そのものを、**tmp_path に作った一時 tree** に対して検査する。
   一時 tree に `__pycache__/<何か>.pyc` を置き、走査結果にその path が現れないことを固定する。
   走査関数を直接呼ぶ形でよい。これが **`__pycache__` 除外を落とす変異を単独で赤にする検査**になる。
2. **実 repo の生存確認 test (既存 test の付け替え):**
   実 repo root に対して `verify_registration(HEAD, repo_root=ROOT)` が `passed is True` を返し、
   seal record が schema-valid であることだけを検査する。
   **実 repo の tree へ 1 byte も書き込まない。** `.pyc` を作らない、消さない。
   実 repo は pytest が module を import した時点で `__pycache__` を持つのが通常なので、
   この test は生存確認として意味を持つ。ただし `__pycache__` の存在を前提にした assert は置かない
   (置くと `PYTHONDONTWRITEBYTECODE` の環境で偽の赤になる)。

**この 2 つで、除外の意味論は 1 の決定的な検査が守り、実 repo での gate 生存は 2 が守る。**

## 所有 path (これ以外を編集してはならない)

- `orchestrator/tests/test_axis_b5_search_executor.py`
- `orchestrator/axis_b5_search/preflight.py` (走査関数を test から呼べるようにする必要がある場合だけ。
  **除外の意味論そのものは変えない**)

**編集してはならないもの:** 他の全 file。docs、catalog、fixture、他の test、受入所要台帳を含む。
**commit してはならない。** git の状態を変える操作をしてはならない。外部 network を使ってはならない。

## 禁止 (段 5・段 6 の実装子契約を継承する)

- **既存 test の期待値を変更しない。** 反転・緩和・skip・削除を禁じる。
  上記 2 の付け替えは「共有状態への書き込みを止める」ためのもので、検査する性質は落とさない。
- テストを甘くして緑にしない。恒真な assert を置かない。
- 期待値へ揮発する payload (working tree hash・時刻・host 名) を焼き込まない。
- `__pycache__` 除外の受理集合を変えない。
- test の総数を意図せず増減させない。増減した場合は報告に正確な数を書く。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 実走のしかた

**`tools/run_tests.py` は `rc=16` で失敗し、`python3 -m pytest` は guard に拒否される。
自走 harness を使うこと。**

```
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix2
PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_executor.py -q
PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_parsers.py -q
```

**緑を主張するときは実走した nodeid と範囲を必ず併記する。**

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## 直した内容
## test の増減
## 実走した test
## 波及可能性
## 未実走・未実装
## 総括
