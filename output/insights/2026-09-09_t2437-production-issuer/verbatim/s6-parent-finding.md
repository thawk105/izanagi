# 親が段 6 の焦点走で見つけた回帰 (blocker、fix 対象)

wave HEAD `636e943802cbb309694bf23ed3fe7794087438f4` に対する焦点走 36 file: **赤 3 件**。
3 件とも同一原因。

## 根本原因

`_issue_campaign_result_evidence(...)` の **4 呼び出し点** (`orchestrator/campaign/loop.py:664, 697, 713, 839`)
が、引数を**無条件に評価する。**

Python は呼び出しの前に引数を評価するため、helper 冒頭の

```python
if context is None:
    return
```

では防げない。結果として、**発行 context を渡さない既定 (originless) 経路でも**
`authorized_contract.contract_sha256` と `r.build_attempt_id` を読む。
既存 test はこれらを stub object や `types.SimpleNamespace` で渡しているため `AttributeError` になる。

**これは段 4 裁定の不変条件 2「既定 (originless) 経路の受理集合と意味を変えない」の違反である。**
既定経路が従来読まなかった属性に触れている。

## 赤になった node と assertion 本文

| node | 位置 | 本文 |
| --- | --- | --- |
| `orchestrator/tests/test_paper_story_a2_certification.py::test_official_run_observes_dependency_receipt_after_condition_prebuild` | `loop.py:845` | `AttributeError: 'object' object has no attribute 'contract_sha256'` |
| `orchestrator/tests/test_t1416_backoff_compiler_binding.py::test_run_campaign_forwards_expected_toolchain_to_evaluate_for_each_genome` | `loop.py:842` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'build_attempt_id'` |
| `orchestrator/tests/test_paper_story_a1_paired.py::test_a1_exact_marker_routes_loop_to_dedicated_replay_and_append` | `loop.py:703` | `AttributeError: 'types.SimpleNamespace' object has no attribute 'contract_sha256'` |

**この 3 件は本 wave の変更に帰属する。**非帰属赤でも flake でもない。

## 直し方 (最小)

4 呼び出し点それぞれを、引数の評価ごと `result_evidence_context is not None` で囲む。
helper 内の早期 return はそのまま残してよいが、**それだけでは防護にならない**ことを
code comment に 1 行で書く。

## 直したあとに足す負例

既定経路で issue の引数が**評価されないこと**を検査する node を 1 件足す。
`authorized_contract` と `EvalResult` に、属性アクセスで例外を投げる番人 object を渡し、
`result_evidence_context=None` の `run_campaign()` が最後まで通ることを見る。
これを入れないと、同じ回帰が次の wave で再発しても誰も気づかない。

## 成果物影響 (DW-G05)

放置すると、**発行 context を使わない既存の全 campaign 経路が停止する。**
`paper_story_a1_paired` / `paper_story_a2_certification` / `t1416_backoff_compiler_binding` が
使う実行経路が `AttributeError` で落ちるため、certified 選択の生成そのものが走らない。
