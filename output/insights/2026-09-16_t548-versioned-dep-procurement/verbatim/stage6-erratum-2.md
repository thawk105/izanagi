# 段 6 裁定 追補 2 — F1 の shell 変更に伴う凍結 evidence binding の移設 (親が値を確定)

**正本の関係:** `stage6-ruling.md`・追補 1 に続く。衝突したら本書が優先する。

## 発生

fix 単位 F1 が B1 (silo submit + job) と B3 (mocc) を直した。silo の 2 本は凍結 evidence
`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` が `submitter` / `pbs_job` として
sha256 で束縛しており、`orchestrator/tests/test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`
が期待赤になった (F1 の報告どおり)。

## 親が実測・確認した値

**親は F1 の差分 3 本を現物で読んだ。** silo submit / job は「gflags / glog を別列挙で既存ループへ足す
11 行」ずつ、mocc は「既存の hydrate ブロックを gflags 段の前へ移動」で、検査の追加も削除も無い。

| key | path | 歴史値 (凍結 evidence) | 現行値 (F1 後、親算出) |
|---|---|---|---|
| `pbs_job` | `tools/pegasus/silo_ladder_rung1.sh` | `318c2b12fb3fa71b3587c81f201db640393d2adae2214fd6aca4a9222ab2f57c` (追補 5 で歴史化済み) | **`99687368a1fdf10d8f699be3a32afd2814f51d98bcad5fbdf6a1862ca72b456f`** |
| `submitter` | `tools/pegasus/submit_silo_ladder_rung1.sh` | **`e12ac6589f7587540b38d5c528b2561e446031b4ce0ee48443ee4be583d8e9b2`** (= 凍結 evidence の値 = wave tip `99c9b9222` の bytes) | **`6990ad4470aba09b8c62224f33a453c330a0be4fbb913cf1e477bb882659412b`** |

`mocc_trace_pilot.sh` は凍結 evidence に束縛されていない (親が確認)。

## 決定

### (1) `pbs_job` の現行 pin を更新する

既存の現行 pin 定数 (`117b3bb4…`) を **`99687368…`** へ更新する。歴史定数 (`318c2b12…`) は変えない。

### (2) `submitter` を D200 / 追補 5 と同じ形で歴史値へ移す

- `historical_sha256_by_key` に `"submitter"` を足し、値は **`e12ac658…`**。
- `pbs_job` と同型の現行 bytes pin を置き、値は **`6990ad44…`**。
- `binding != current` の assert も残す。診断文は既存の `policy` / `pbs_job` に倣う。
- 定数は既存の `pbs_job` 用 2 定数と同じ場所・同じ書式で置く。

### (3) 検知力を落とさない

移設後も「任意の 1 byte の変更で赤になる」が両 key で成立していること。
凍結 evidence (`output/` 配下) は 1 byte も書き換えない。

### (4) 値を自分で算出してはならない

実装子は編集後 file から sha256 を算出して埋めてはならない。照合に使うのは構わないが、
一致しなければ実装が誤りなので報告して止める。

## 非帰属赤の記録 (DW-O18)

F1 が報告した `orchestrator/tests/test_p3_s4_loop.py` の赤 (TypeError 112・ExecutionGuardError) は、
**F1 の変更が無い wave tip `99c9b9222` (clean) で同 file を単体実走しても 148/263 passed・
TypeError 112・ExecutionGuardError 6 で同じ**だった (親が実測)。自走 harness 単体では
acceptance harness の fixture 注入が無いための構造的な赤であり、**F1 に帰属しない**。
受入全走 (`tools/run_tests.py`) で判定する。
