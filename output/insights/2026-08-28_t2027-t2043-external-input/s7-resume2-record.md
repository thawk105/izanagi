# [T-2027]/[T-2043] 回収 wave (2026-08-29) の記録

2026-08-28 の wave が受入全走の手前で中断した完成済み branch を回収し、land まで運んだ回の記録。
実装は書き直していない。本文の要約は worklog、失敗の型は F480 の再発と新規 F を正本とする。

## 規律 6 の内容監査 — 自分が作っていない差分の受入前検査

対象: `2e35a2596` (production 4 file + test 4 file、1447 挿入) と `104954a30` (変異 erratum)。

確認した不変条件:

- v2 は `{root, path, sha256}` の exact field 集合を要求し、root は
  `snapshot` / `fetchcontent-masstree` / `filesystem` の 3 値に限る。
- external root を持つ manifest は descriptor input policy を必須にする
  (`input_policy is None and any(root != "snapshot")` で停止)。
- `fetchcontent-masstree` entry があるのに current root が渡されなければ停止する (fail-closed)。
- `filesystem` root は live path が snapshot / current masstree / その親の配下でないことまで検査し、
  root tag による偽装を拒否する。
- v1 は `LEGACY_MANIFEST_SCHEMA` として構造互換のまま残り、absolute path の実在と hash を
  従来どおり要求する。migration も cache-miss fallback も無い。
- 新しい `_hash_relative_nofollow` / `_strict_root` は、component ごとの no-follow open、
  `st_dev`/`st_ino` の前後一致、hash 中の size・mtime・ctime 不変まで確認する。
  旧経路の `_file_sha256` + `_compiler_input_entry` より厳しい。
- `_collect_compiler_inputs` から、policy 非対応 collector の結果へ `input_policy` を
  後付けする分岐が削除された。捏造された policy 印が消えたので受理集合は狭まっている。

**結論: 変更はすべて受理集合を狭めるか保つ方向で、絶対規律 2 を緩める箇所は無い。**

非阻害の所見 2 件 (記録のみ、本 wave では直さない):

1. `buildcache.py` が `s8b_compiler_input._strict_root` を module 跨ぎの private 名で呼ぶ。
2. `s8b_floor_campaign.py` は dependency binding のある全 cell へ
   `current_compiler_input_masstree_root` を渡すようになった。従来 `build_kwargs` が
   非空になるのは `dependency_bound_sort` の枝だけで、その枝は `build_fn is buildcache.build_v2`
   を要求していた。注入された非既定 `build_fn` が当該引数も `**kwargs` も持たない場合
   TypeError になりうる。official mode は `build_fn` 注入を拒否するので到達経路は非 official に限られ、
   受入全走は緑である。

## main 取り込みの合成検査

- 着手直前の local main = `d03855e92`、merge-base = `73a437e67`、その間 220 commit。
- main はこの区間で orchestrator/tools の 103 file を変えたが、本 wave の 8 file との
  **ファイル重複は 0 件**。
- 103 file 全部を走査し、`collect_compiler_input_manifest` /
  `validate_compiler_input_manifest` / `s8b_compiler_input` /
  `issue_binary_admission_receipt` を参照する file が **0 件**であることを実測した。
- main 側で唯一の `buildcache.build_v2` 呼び手 (`backoff_requested_us.py`) は
  `source_snapshot_sha256` を渡さないため、改修した compiler-input 経路へ入らない。
- `test_ccbench_spawn_sites.py` の関数単位 spawn pin は buildcache.py の 5 関数を数えるが、
  本 wave の追加は subprocess を 1 つも増やしていない。
- merge は競合 0、submodule pin は main と同一 (`511c9538e4e8efa54b45cda62e72389ed3b706ec`)。

## 変異 matrix を再走しなかった理由

前 wave の corrected spec (6 件、baseline 6 passed、6/6 KILLED) の期待 node は全件が
本 wave の 4 test file 内にある。

| 変異 | 期待 node の所在 |
|---|---|
| M1-SCHEMA-PIN-OMITTED | test_buildcache_v2.py |
| M2-FETCH-ROOT-AS-FILESYSTEM | test_s8b_compiler_input.py |
| M3-CURRENT-BASE-IGNORED | test_buildcache_v2.py |
| M7-ROOT-CANONICALITY-SKIPPED | test_s8b_compiler_input.py |
| M8-RECEIPT-RECHECK-OMITTED | test_s8b_binary_admission.py / test_s8b_floor_campaign.py |
| M10-NON-SORT-CURRENT-ROOT-OMITTED | test_s8b_floor_campaign.py |

本 wave が足した唯一の実装面変更は `test_growth_test_holds_contract.py` の 1 呼び出しへの
`timeout=120.0` であり、どの anchor 逐語にも期待 node 集合にも触れない。main 取り込みも
4 production file を 1 行も変えていない。よって spec の再検証だけを行い本走はしていない。

## 親が実測した値 (すべて merged tip `2d5d967c3` 以降)

| 対象 | 結果 |
|---|---|
| 焦点走 (変更 4 test file) | 716 passed / 3 skipped / rc=0 / 80.65 秒 |
| `test_growth_test_holds_contract.py` 単独 (fix 適用後) | 83 passed / rc=0 / 6.22 秒 |
| 赤だった node 単独 (fix 適用前) | 1 passed / rc=0 / 4.25 秒 |
| `check_docs.py` | rc=0 (違反なし) |
| `check_codex_agents.py` | rc=0 |
| `check_ai_provenance.py` 全史 | rc=0 |

## 子の逐語 — Codex `role=fix` の総括

受領証: outcome=accepted、launcher_rc=0、codex_exit_code=0、validator_rc=0、
recorded_model=`gpt-5.6-sol`、recorded_effort=`xhigh`、sandbox=workspace-write。

子は指定コマンドを 1 度実行したが `qstat -Q` preflight が rc=1 で失敗し、dispatch driver が
rc=16 / `child_started=false` / `child_rc=null` を返したため、**implemented, not run** を
正しく申告した。実測は親が行った (上表)。

子が報告した accept/reject 集合の確認 (逐語):

> 成功終了し、出力に `1 skipped` と hold marker があり、bypass-refusal marker がない結果を
> 受理します。非ゼロ終了、必要な文字列の欠落、または bypass-refusal marker の出現を拒否します。
> 経過時間は assertion の対象ではなく、変更したのは anti-hang guard の待機枠だけなので、
> この意味上の受理・拒否集合は不変です。

子が報告した波及リスク (逐語):

> 外部 caller、共有 fixture、consumer test、環境構築には変更がありません。唯一の実行上の影響は、
> このノードの subprocess が真に停止した場合、失敗確定までの最大待機時間が10秒から120秒へ
> 延びることです。120秒後には引き続き fail-closed します。

子は同 file の他 11 呼び出しを静的に列挙し、いずれにも `timeout=` を足していないこと、
helper 既定の 10.0 秒が維持されていることを報告した。親が `git diff` で同じ結論を確認した。
