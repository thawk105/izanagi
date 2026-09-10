# [T-971] 床値 sort_best の SWO oracle infrastructure-unavailable — 変異台帳と実測

wave branch: `worktree-dev-wave-t971-swo-oracle-floor`
実装 anchor commit: `80caf743389a35cdd9a946f7414bd41610b51095`

## 構成

| file | 内容 |
|---|---|
| `mutation-spec.json` | 事前登録 10 変異 (再登録後の確定版)。spec sha256 = `a694cdc8a3327a80d2cb0a76d23b56c4f2223961d8509df0a07d0e11b77f7398` |
| `mutation-ledger.json` | **fix 後の最終 commit `80caf743` での本走**。10/10 KILLED、rc=0 |
| `mutation-ledger-probe.json` | 初回 dispatch 走 (probe)。期待 node の完全集合を導出するために使った |

## 変異結果 (最終走)

`{"KILLED": 10, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0}`

**SURVIVED は 0。** 登録した検査はすべて、壊すと必ずテストが赤くなる。

| # | 変異位置 | 変異内容 |
|---|---|---|
| M01 | resolver の detail_code 3 分岐 | 最終 else を compiler 側へ倒す |
| M02 | resolver の dependency 候補列 | 候補記録を空 tuple にする |
| M03 | 診断の `result is None` 判定 | 判定を恒偽にする |
| M04 | 診断失敗時の終了コード | `return 1` を `return 0` にする |
| M05 | durable 射影 | `as_dict()` を `private_dict()` に差し替え full path を流す |
| M06 | compiler の明示注入 | `compiler=` を落として ambient に選ばせる |
| M07 | masstree HEAD 照合 | 比較を恒偽にする |
| M08 | `config.h` の regular file 検査 | 検査を恒偽にする |
| M09 | phase marker の create-only | `O_EXCL` を `O_TRUNC` にする |
| M10 | preflight エラーの文言 | 日本語メッセージを言い換える |

## probe 走で分かったこと (erratum)

初回走は期待 node が不完全で 4 件 MISMATCH になった。**いずれも SURVIVED ではなく、
検出そのものは効いていた。** 内訳:

- **M02 / M07 は親の予測より検出が強かった。** M02 は予測 4 件に対し実測 5 件
  (`test_explicit_compiler_binding_never_falls_back_to_ambient` が追加で赤)。
  M07 は予測 1 件に対し実測 2 件。
- **M04 は予測より弱かった。** `test_stdout_failure_records_diagnostic_emission_failure_on_stderr`
  は終了コードを検証していない。ただし同じ保証は他 2 本が押さえている。
- **M06 は予測と別のテストが捕まえた。** 親は
  `test_floor_sort_cell_injects_verified_cxx_and_dependency_into_oracle` を期待したが、
  このテストは `prepare_cell` を fake に差し替えており「床値 → prepare_cell の受け渡し」
  だけを検証する。M06 が変異させた「prepare_cell → resolver」の脚は
  `test_s1_sort_best_runs_same_oracle_before_source_materializer` が担当していた。
  **恒真テストではない** — 担当範囲が違うだけであることをコードで確認した。
- **M10 は正例として登録したが検出された。**
  `test_floor_oracle_dependency_compares_head_and_hashes_regular_config` が
  **日本語のエラーメッセージ文言そのものを pin している**。正しさには影響しないが、
  文面を変えるだけで赤くなる脆さの発見である。事実に合わせて negative へ再登録した。

## 走行環境

- runner-mode = `dispatch` (計算ノード)。argv に `--force-dispatch` を含む。
- **ログインノードの bounded local では完走しない。** 並行 wave が同時にテストを走らせると
  cgroup scope を attest できず `dispatcher infrastructure failure` になり、
  harness が「赤なのに失敗 node を確実に抽出できない」で fail-closed 停止する
  (rc=16 / collection=0)。local で 2 回、それぞれ M04 到達時と collection 時に停止した。
  計算ノードへ切り替えてからは 3 走とも一度も落ちていない。
