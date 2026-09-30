## 変更内容 (file:line)

- [core.py:55](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/core.py:55): 正規化済み source の引用形 include を `cc/silo/` から解決し、実ファイルが `include/ycsb.hh` と一致するときだけ D5 を成立させました。
- [test_verifier_gate_witness.py:35](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/tests/test_verifier_gate_witness.py:35): fixture を実物の相対 include に変更し、誤った解決先の負例を追加しました。

## 実物の source での D5 の自己確認 (command と結果)

`python3 -c` で一時ディレクトリに U1 の `ycsb.hh`・`transaction.cc` と実走 archive の `ycsb_silo.cc` をコピーし、`_gate_d5(root)` を実行しました。結果は **`pass`**。include を `#include "ycsb.hh"` に替えて再実行した結果は **`fail`** でした。`python3 -m py_compile` も成功しました。

## 追加・変更した test node id

- 追加: `orchestrator/tests/test_verifier_gate_witness.py::test_gate_wrong_include_target_d5_fails`
- fixture 変更に伴う正例: `orchestrator/tests/test_verifier_gate_witness.py::test_gate_real_u1_emitter_names_d5_pass`

## 総括

差分は合計 27 行で上限内です。小さい Python 確認では、正しい include が `D5=pass, certified=True`、誤った include が `D5=fail, certified=False` でした。pytest は指示どおり実行していません。