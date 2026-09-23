## 総括

[起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ud/.t2847-launcher/launch_mutation_run.py:249) の s8a mode を修正しました。骨格 build は従来どおり admission 付きの `_build` を使い、misattr build だけを s2 と同じ直 CMake 経路に変更しました。misattr 側も `_build` と同じ構成引数、site policy の拒否検査、2 つの condition gate を通します。`source_digest` の防壁は変更していません。11 個の check は driver の式を写し、結果を `<out>/s8a_trigger_gating_coverage.json` に保存します。

受動保存では `cmake --build` を `build` event に分類し、YCSB run の要約に混入しないようにしました。meta の `replaced_names` には `main()` を起動器の手順へ置き換えたことを追加しています。従来の compiler、骨格 build 用 `source_digest.resolve_evidence(cxx)`、出力先、`ENV_TAG`、subprocess の差し替えは維持しました。patch 適用、condition gate、verifier の判定関数は差し替えていません。

**実走結果:** `python3 -m py_compile .t2847-launcher/launch_mutation_run.py` は rc=0。`python3 .t2847-launcher/launch_mutation_run.py mutations --job J1|J2|J3|J4 --plan-only` は各 rc=0、`python3 .t2847-launcher/launch_mutation_run.py s8a --plan-only` も rc=0 でした。plan 出力の対象は次のとおりです。

| 出力 | workload | 変異 |
|---|---|---|
| J1 | W1, W2 | V17, V22, V35, V18 |
| J2 | W3, W4 | V19, V23, V20, V24 |
| J3 | W4, W5 | V33, V21, V26 |
| J4 | W6, W7, W8 | V27, V31, V32 |
| s8a | — | `{"mode":"s8a","driver":"s8a_trigger_coverage","CLK":2100}` |

`check_codex_agents.py`、`check_docs.py`、`git diff --check` も rc=0 です。計算ノードでの build・run は未実走のため、今回の修正で misattr build が完走するかは親の本走で確認が必要です。変更は指定の起動器 1 ファイルだけで、commit は作成していません。