## 規律 2 と受理集合

所見なし。commit の core 差分は alias 3 行だけです。`_normalize_predicate_results`、三 module の blob 比較、`effective` の四項連言は変更されていません。evaluator/projection の blob も親 commit と一致し、既存テストの変更はありません。

`SATISFIABLE_CONDITION_IDS == {"C10"}` と、C10 以外の `SATISFIED` を `ERROR` に倒す処理も不変です。このため production evaluator では全 12 条件の連言が成立せず、受理集合は空のままです。

## 新設テストの恒真性

所見 1: `--commit` 採用検査は、指定 SHA が同時に `HEAD` なので引数を無視しても緑になる  
深刻度: must-fix  
根拠 (orchestrator/tests/test_s8c_cli_entrypoints.py:51): 1 commit だけ作ってその `HEAD` を `commit` とし、同じ値を CLI へ渡して line 174 で比較している。CLI が `--commit` を捨てて既定値 `HEAD` を使っても全 4 case が同じ SHA を返す  
推奨: oracle 用 commit を保存した後、無関係な tracked file で第 2 commit を作り、`HEAD != commit` を事前 assert する。放置すると実運用で指定 commit ではなく HEAD の判定をレポートし、source commit・判定値・後続台帳参照が別 commit を指しても検査を通る

所見 2: oracle 健全性 assert は既知の一律故障だけを除外し、独立した意味 oracle ではない  
深刻度: nit  
根拠 (orchestrator/tests/test_s8c_cli_entrypoints.py:45): oracle と CLI の双方が同じ live 4 file に追随し、lines 82–89 は理由の多様性と限定された failure code だけを検査するため、非一律な共通意味故障では同じ誤った 12 組を比較して緑になりうる  
推奨: この検査を「CLI と library の transport 等価性」に限定すると明記し、意味の正しさは独立した predicate/invariant tests に委ねる。任意の共通故障まで排除するなら、別所有の固定 invariant が必要

`actual_effective is oracle.effective` は、両方 `False` でも無検査ではありません。JSON の `0` 等を拒否しつつ bool の値を照合します。ただし `assert oracle.effective is False` と `assert actual_effective is False` に分ける方が不変条件は明瞭です。

`returncode == 1` も subprocess の独立した観測なので恒真ではなく、rc=0/2 への破損を検出します。`gate-module` は bootstrap 削除には反応しませんが、共有 report/import/output/rc の破損には落ちる対照として成立しています。

4 file の既存 bytes 変更には自動追随します。一方、新依存 file の追加や非一律な共通意味故障には自動追随して静かに弱くなりうる、という境界があります。

## alias と bootstrap の穴

所見なし。

- `import sys` は alias より前にあり、alias より前の import は標準ライブラリだけです。canonical core が最初に要求される evaluator import より十分前に登録されます。
- ファイルパス起動と `-m` 起動では `__name__ == "__main__"` のため canonical 名が実行中 module を指します。
- 通常 import では alias block は発火せず、通常の canonical module 1 個だけです。
- alias は `__file__` を変えないため、`Path(__file__).read_bytes()` と commit blob の自己検査を迂回しません。
- gate のファイルパス起動では core が canonical import され、core alias は発火しません。evaluator の相対 import も同じ canonical core を再利用するため二重実体化しません。

## scope 逸脱

所見なし。変更は指定された production 2 file と新規 test 1 fileだけです。gate/helper/互換層、凍結成果物、文書、closure、既存テストには変更がありません。

## 総括

blocker はありませんが、`--commit` 採用検査の恒真経路が 1 件あるため、現状は must-fix です。

`DIRECT_BOOTSTRAP` は定数と gate 側で byte-for-byte 一致し、core 側とも一致しました。core 内の出現回数も 1 のままです。pytest は実走していません。