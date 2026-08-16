# [T-1223] snapshot oracle が submodule 未初期化を reason 0 件で受理していた穴

- wave: `worktree-dev-wave-t1223-snapshot-submodule-gate`
- 実施日: 2026-08-16 (JST)
- 起票元: worklog entry 591 の scope 外 real 所見 (先行 wave が作った穴ではない)
- 逐語: `verbatim/`、変異台帳: `mutation-spec.json` / `mutation-result.json`

## 何が問題だったか

`tools/codex_reasoning_ab.py` の `verify_snapshot` は、snapshot の submodule manifest を必ず作り
`submodule_manifest_sha256` を必ず計算していたが、**照合するのは caller が spec で
`submodule_manifest_sha256` を渡したときだけ**だった。既定 spec (`_snapshot_spec`) が pin するのは
case / head / branch / tracked_paths / hashes / numstat / untracked / modes / forbidden の 9 key で、
submodule 系を 1 つも含まない。したがって既定経路では照合節が常に不発になり、
CCBench の作業木を持たない snapshot が reason 0 件で正規と認定された。

manifest 層は未初期化を正直に `initialization="uninitialized"` として記録しており、
closure 検査も reason を出さない。つまり**記録は正しく、判定だけが fail-open** だった。

## 何をしたか

verifier 層に無条件の gate を 1 つ足した (production 差分は 3 行)。

- manifest の**全行**を走査し、`initialization != "initialized"` の行ごとに
  `submodule is not initialized: <path>` を reasons へ積む。
- `expected` を参照しない (caller が spec で緩められない)。
- `enforce_closure` 分岐の外に置く (`git_object_closure=False` で迂回できない)。
- oracle document の key 集合は不変 (`manifest_sha256`・schedule 突合・replay bytes 比較に影響なし)。

設計判断は本 wave の decisions エントリ
「snapshot oracle は submodule の初期化を無条件に要求する」に記録した (番号は land 時の fold が付ける)。

## 深さを限定しなかった理由 (親の初期案の撤回)

親は段 1 brief で「深さ 1 の submodule だけ initialized を要求する」を provisional 裁定として置いた。
根拠は `DW-O20` の起動手順が非再帰 init であることだった。段 3 のレンズ B がこれを反証し、
親が一次資料で裏取りした。

| 資料 | 内容 |
|---|---|
| `tools/dev_wave_wait.py` の `_submodule_readiness_preflight` | 受入 claim 前に再帰 status の未初期化 (`-`) / 未解決 (`U`) を rc=2 で拒否する |
| `docs/pegasus-runbook.md` | 受入投入前の `git submodule update --recursive` を要求する |
| `docs/archive/worklog-phase3-0815-558.md` ([T-1124]) | 非再帰 init で入れ子 submodule が残り、独立 2 wave が受入停止を踏んだ |

正当に運用された作業木は全深度が初期化済みであり、全深度要求は正規の運用を壊さない。
副次効果として深さ算術が不要になり、兄弟 path (`deps/a` と `deps/ab`) を祖先と誤認する型の
欠陥が構造的に排除された。

## 恒真ではないことの実測

「新しい検査が既定の受入走行で一度も発火しないなら恒真な保証である」という段 3 の指摘に対し、
変異注入で実測した。判定式を反転する変異 (M01) と恒真化する変異 (M06) では、合成テスト 6 件に
加えて**実 repo 由来の 3 node が error になる**。

```
orchestrator/tests/test_codex_reasoning_ab.py::test_git_answer_object_reinjection_is_rejected@real-repo
orchestrator/tests/test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive@real-repo
orchestrator/tests/test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment@real-repo
```

この 3 件は変異ハーネスの `FAILED` 行抽出には現れない ([T-1225] の同型)。本 wave は
`-rfE` で親が別途採取した。ハーネスの期待 node 集合には含めていない。

## 変異 matrix

事前登録 6 件 (negative 5 + positive control 1)、**6/6 KILLED、MISMATCH 0、SURVIVED 0**、
baseline PASSED。runner は `tools/run_tests.py --force-dispatch` の dispatch recipe。

| ID | 変異 | 期待して落ちる node 数 |
|---|---|---|
| M01 | 判定式を `== "initialized"` へ反転 | 5 |
| M02 | gate を削除 (fail-open へ戻す) | 4 |
| M03 | gate を `if enforce_closure:` の内側へ移す | 2 |
| M04 | 全行走査を先頭行のみへ変更 | 1 |
| M05 | reason を積まず oracle へ key を足して記録する | 5 |
| M06 (正例 control) | 判定を恒真化し全 submodule を拒否 | 1 |

期待 node 集合は**設計上の対応表から転記せず、各変異を一時注入して実測で再導出した**。
初回登録では M01 / M03 / M06 の集合が誤っており、段 6 のレビューが本走前に指摘した (F28 の再発)。

## 残した穴 (本 wave の scope 外、起票済み)

- `initialization == "initialized"` は**内容の実在を保証しない**。`_submodule_worktree_state` は
  「submodule path が Git top-level」かつ「HEAD == gitlink」で initialized を返し、
  `.git` marker と期待 admin dir の束縛、index と `HEAD^{tree}` の一致、worktree bytes と index の
  一致を検査しない。親 repo 側で `submodule.<name>.ignore=all` を設定すれば root の status も汚れない。
  つまり「正しい HEAD を持つ空の CCBench」は今も通る。
- 中間成果物層 (`collect_run` / `make_packets` / append・freeze・reveal CLI) は snapshot を再検証せず、
  launch receipt の oracle SHA を転記するだけである。正規 supervisor 経路の certified decision は
  閉じるが、receipt・材料 packet・verdict freeze は未認証 snapshot 由来でも生成できる。

## 親 brief の訂正

brief は「`tools/codex_reasoning_ab.py` の bytes を pin する台帳は無い」と書いたが誤りだった。
検索を `--include=*.py` に限ったため、tracked artifact
`output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` の `tool_sha256` を落とした。
実測では同 pin の値は `58f1176e…`、現行 HEAD の tool は `64045cfa…` で**本 wave 以前に既に乖離**しており、
Python からの live consumer も 0 件である。pin は歴史記録として不変のまま残し、本 wave は触らない。
T-1223 後の tool は T-181 certified rerun の装置 identity とは別物である。
