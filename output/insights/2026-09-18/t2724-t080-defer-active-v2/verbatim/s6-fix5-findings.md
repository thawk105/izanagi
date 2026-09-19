# 段 6 fix-5 の指示 (親、2026-09-18 14:18 JST)

fix-4 統合 commit `dc9e54e15` の焦点走 (chain 有り scratch `1cbd28aa1`、7 file、request 5685、14:07〜14:15): **1097 passed / 7 failed / 11 skipped、417 秒**。赤 7 はすべて fix-4 で足した新負例 `test_s8b_ratified_freeze.py::test_receipt_emitter_requires_copied_inputs[<7 param>]` で、原因は 1 つ。

## J1. 新負例の assertion 本文の完全一致 (test 側、1 箇所)

```
with pytest.raises(AssertionError) as caught:
    build_production_emitter_g1(tmp_path, receipt_root=tmp_path)
assert str(caught.value) == f"receipt base missing input: {missing}"
```

pytest の assertion 書換えは `assert (root / relative).is_file(), f"receipt base missing input: {relative}"` の失敗 message に `\nassert False\n +  where False = is_file() …` の説明を**追記**するので、`str(caught.value)` は完全一致しない (実測: `"receipt base…json\nassert False\n +  where False = …is_file"`)。fix 子は pytest を走らせられないので、この書換えの逐語を見られなかった (F42 型)。

直し方: 完全一致をやめ、**先頭一致**にする — `assert str(caught.value).startswith(f"receipt base missing input: {missing}")`、または `pytest.raises(AssertionError, match=re.escape(f"receipt base missing input: {missing}"))`。message の主語 (missing の path) を検査する強さは保つ。他は変えない。

## J2. 変えないもの

production・S・登録簿・fix-4 の receipt 接続分岐の fail-closed assert・既存 tracked test の期待値。

## 対応表

J1 を closed / partial / regressed で。直接呼出しで、意図的に 1 file を欠いた tmp root に対して `build_production_emitter_g1(tmp, receipt_root=tmp)` が `AssertionError` を上げ、その `str()` が期待の prefix で始まることを確かめる (pytest なしでも `assert` 文は動く。ただし pytest 外では書換えが無いので、prefix 一致は両方で成立する形にする)。
