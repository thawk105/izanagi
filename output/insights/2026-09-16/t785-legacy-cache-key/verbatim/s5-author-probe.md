## 実装した内容

[t785_legacy_cache_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t785-impl/t785_legacy_cache_probe.py) を作成しました。15,588 bytes。tracked file の差分はなく、add・commit は実行していません。

## 裁定 §3 との対応表

| 要件 | 実装 |
|---|---|
| 2 モード・import 元確認 | `evidence` / `build`、module 実 path を検証 |
| production build | cc/cxx 省略。evidence は build の定義時既定を使用 |
| 差し替え範囲 | `_run` のみ。実コンパイル・ELF 確認、finally で復元 |
| JSON・3 判定 | 指定 field と機械判定。seed 未指定時は null |
| compiler 同一性 | realpath と version 先頭行の双方を比較 |
| 出力保護 | repo 外、既存 out 拒否、seed cache 空確認 |
| 終了コード | 正常 0、期待不一致 3、例外 1 |

## 実行した確認と結果 (実走していないものは「未実走」と明記)

次の CLI 確認はすべて終了コード 0 でした。

```text
python3 t785_legacy_cache_probe.py --help
python3 t785_legacy_cache_probe.py evidence --help
python3 t785_legacy_cache_probe.py build --help
```

構文確認も終了コード 0。所有 path 以外への生成禁止を守るため、通常の `python3 -m py_compile` の代わりに、保存処理を抑止して同じ CLI 処理を実行しました。

```bash
python3 -B -c 'import runpy, sys; from unittest.mock import patch; sys.argv = ["py_compile", "t785_legacy_cache_probe.py"]; p = "importlib._bootstrap_external._write_atomic"; q = "py_compile.os.makedirs"; import py_compile; ctx = patch(p); ctx2 = patch(q); ctx.start(); ctx2.start(); runpy.run_module("py_compile", run_name="__main__")'
```

引数解析の直接呼出も終了コード 0：

```text
PASS: configure argv parsed; duplicate -B, missing cxx, duplicate cxx rejected
```

`evidence`・production `build`・実コンパイルは **未実走** です。

## 既知の限界と親が実走時に見るべき点

- probe を repo 外へ退避し、各相を別 process で実行してください。
- `cached` の期待一致に加え、修正前は `reproduced_false_hit`、修正後は `fix_demonstrated` を確認してください。
- `.comment` の判定には compiler 版の数値部分を使います。生の出力も JSON に保存します。
- 対象 ELF は極小 C++ です。CCBench 全体のビルド成功や性能差は実証しません。

## 総括

probe の作成と静的確認は完了しました。偽 hit の再現・修正実証は未実走であり、親の実測待ちです。