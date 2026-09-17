## 書いた file と行数

[tools/t2708_fixture_gap_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2708-fixture-config-h-gap/tools/t2708_fixture_gap_probe.py)：361 行。repo 内の変更はこの新規 file のみ。commit なし。

## 実走した検査 (argv・rc)

以下すべて rc=0。

```bash
python3 -B -m tools.t2708_fixture_gap_probe --help

PYTHONPYCACHEPREFIX=/tmp/t2708-author-pycache python3 -m py_compile tools/t2708_fixture_gap_probe.py

python3 -B -m tools.t2708_fixture_gap_probe --source-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2708-fixture-config-h-gap --work-root /tmp/t2708-author-selftest-20260917 --out /tmp/t2708-author-selftest-20260917/result.json --selftest
```

selftest は index 往復・集合差・不存在 path の失敗記録を確認。想定した Git rc=128 を記録し、probe の `failures=[]`。

## 未実走の項目

本走は**実装済み・未実走**。builder、production module import、取り込み計測、scan 対比較、退避後の module 解決は未検証です。

## 波及と既知の限界

所有外 caller、production、test、docs、共有 fixture の変更なし。xdist 変数を除去し、builder を直接呼ぶ構成です。

発行 A/B ではなく、commit 後の index による部分モデルです。取り込み両方式は object cache を共有します。安全でない出力先・書込不能時は JSON を標準出力へ返します。

## 総括

指定の probe を実装し、許可された検査は通過しました。性能・判定同一性の結論は計算ノードでの本走待ちです。