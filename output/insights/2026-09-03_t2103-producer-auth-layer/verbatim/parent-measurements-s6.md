# 親の実測記録 (段 6 時点) — T-2103

## 実行環境

- wave worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer`
- HEAD: `431e0d6d8d411038b9560a7762475053d597197c` (wave 開始後に local main を ff で取り込んだ)
- 実装差分は未 commit の untracked 3 file (段 5 実装子の成果物を所有 path 限定 patch で移送)
- 段 5 実装子は **1 つも pytest node を実走できていない** (scratch root が codex sandbox で EROFS、
  test dispatch が rc=16)。したがって子の報告に緑は 1 つも無い。

## 親が実行した走行

`python3 tools/run_tests.py orchestrator/tests/test_p3_b4_producer_auth_experiment.py -q -rf`

結果: **4 failed / 24 passed** (238.92s、Pegasus request 969514.nqsv、Elapse 245S)

失敗した node は 4 つだけである。

```
FAILED ...::test_candidate_enabled_producer_29_node_non_regression[frozen_consumer]
FAILED ...::test_candidate_enabled_producer_29_node_non_regression[issuer]
FAILED ...::test_candidate_enabled_producer_29_node_non_regression[raw_assembly]
FAILED ...::test_full_baseline_and_prototype_comparison_in_external_scratch
```

**つまり比較実験の数字を出す node と、候補有効時の非後退走が 4 つとも落ちている。**
期待 matrix、W01-W09 対応、callsite 一回性、prereg 再導出などの meta 検査 24 node は緑である。

## 親が特定した赤の原因 (実装の回帰ではない)

4 件とも同一の例外である。

```
orchestrator.campaign.contract_loader_binding.ContractLoaderBindingError:
contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/verifier/core.py
```

機序は次のとおり。親がコードを読んで確定した。

1. `p3_b4_producer_auth_experiment.py:23` の `BASE_COMMIT` は
   `"4ec3eba04354f9ba86117a2dd488c72d007045e6"` という **固定文字列**である。
2. `ScratchTree.__enter__` (同 file `:780` 付近) は `git archive --format=tar BASE_COMMIT` の
   内容を scratch へ展開する。つまり scratch の disk bytes は 4ec3eba04 の内容である。
3. 続いて同 method は scratch へ `.git` file を書き、**source repository の git dir** を指させる。
   その repository の HEAD は現在 `431e0d6d8` である。
4. `contract_loader_binding.capture_contract_loader_binding()` は
   `_REPO_ROOT = Path(__file__).resolve().parents[2]` で scratch を root とし、
   `git -C <scratch> rev-parse HEAD` で `431e0d6d8` を得て、その blob と disk bytes を照合する。
5. `orchestrator/verifier/core.py` は 4ec3eba04 と 431e0d6d8 の間で変更されている
   (main の ff 差分に `orchestrator/verifier/core.py | 31 +-` が含まれる)。よって不一致になる。

**wave 開始時 (HEAD == 4ec3eba04) なら一致していた。** 親が local main を取り込んだことで
BASE_COMMIT と HEAD が乖離し、この赤が出た。実装の欠陥は「base commit を固定文字列で
持っていること」であり、判断値や認証設計の誤りではない。

## 親が確認したその他の事実

- 実装子は既存 tracked file を 1 byte も変更していない (`git status --porcelain` は `??` 3 行のみ)。
- `orchestrator/campaign/p3_b4_raw_record_producer.py` の SHA-256 は
  `55e264f05eef48e466a1ab20c97d9a7d30acba0afe3e76937e58411e17b1c790` で、
  wave 開始時と同一。trust anchor は有効である。
- scratch root `/work/1/SFC/tanab/t2103-scratch/` は走行後に空である
  (`ScratchTree.__exit__` の破棄は動いている)。
- 28 node が collect でき、collection error は無い。
