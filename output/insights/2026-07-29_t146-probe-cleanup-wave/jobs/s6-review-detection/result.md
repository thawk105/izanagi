判定は **NO-GO** です。テストは実走しておらず、author の pass 件数も検証済み green とは扱っていません。

## Real findings

### R1 — P1 / blocker: M‑T146‑B が SURVIVE する

M‑T146‑B の anchor は構文上1箇所にできますが、意味上の検出力がありません。

- mutation 対象: [test_dev_waves_integration.py:1146](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1146)
- EPERM/EIO injection: [test_dev_waves_integration.py:1277](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1277)
- assertions: [test_dev_waves_integration.py:1316](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1316)
- 事前登録: [s4-adjudication-plan-v2.md:56](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s4-adjudication-plan-v2.md:56)

静的再現:

1. `except FileNotFoundError` を `except OSError` に変更する。
2. EPERM/EIO injection は pathname を削除せず例外を投げる。
3. mutated handler の nofollow `stat()` は `.s` の存在を確認する。
4. bare `raise` が元の型・errnoを再送出する。
5. 現在の EPERM/EIO assertions はすべて通る。

したがって「FNF-only分類」をテストしておらず、「pathname が残っていれば再送出」をテストしているだけです。

成果物影響: M‑T146‑Bを KILLED と証明できず、mutation台帳とtest-acceptance証明が偽緑になります。product artifact値は不変です。

最小fix: EPERM/EIO injectionも `real_unlink()` 後に元例外を投げ、両nodeでは `pathname_state is None` を期待する。これなら広い `except OSError` は例外を抑止し、EPERM/EIO nodeだけが赤になります。

### R2 — P1 / blocker: `-rf -rs` は failed-node記録を失う

plan は [s4-adjudication-plan-v2.md:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/output/insights/2026-07-29_t146-probe-cleanup-wave/s4-adjudication-plan-v2.md:18) で `-rf -rs` を要求しますが、DW-M08 は [mutation.md:51](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/docs/dev-wave/mutation.md:51) で `FAILED <node>` の取得に `-rf` を要求します。

この組合せは既に、後の `-rs` が勝って `FAILED` 行を失う事故として記録されています: [worklog archive:37](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/docs/archive/worklog-phase3-0727-26-0728-32.md:37)。

さらに plain runner は [test_dev_waves_integration.py:1972](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1972) で `-q` だけです。

成果物影響: mutationの失敗node単一帰属とSKIP理由を記録できず、KILLED/OFF-TARGET/SURVIVEDの裁定が無効になります。

最小fix: targeted mutationは単一指定の `-rfs` を使うか、failed-node取得とskip監査を分離走する。full runnerは通常の受入形で別走し、mutation台帳にはrc・FAILED node・SKIPPED node/reasonを別々に保存する。

### R3 — P2 / recording nit: 7 parameterは同じ種類の新規検出力ではない

| parameter | 旧helperの静的挙動 | 正しい分類 |
|---|---|---|
| `partial-bind` | bind後例外では`created`未設定のため残留 | 本当の穴 |
| `fnf-after-real-unlink` | cleanup FNFが予定された`True`を上書き | 本当の穴 |
| `no-op-unlink` | `True`を返しpathnameを残す | 本当の穴 |
| `eperm` / `eio` | 元の型・errnoを既に送出 | 新FNF分岐のregression guard。ただしR1により現状は無効 |
| `regular-file` / `broken-symlink` | `False`を返すがidentityは既に保存 | identity部分は既存挙動の再固定。`FileExistsError`とsocket未生成は新policy |

成果物影響: 5 pre-fix failuresを5件の旧cleanup欠陥として記録すると、検出力を過大表示します。

最小fix: 段7台帳で「旧穴3、regression guard 2、既存identity再固定＋新policy 2」と分離する。コード変更はR1以外不要です。

### R4 — P2 / non-blocking: 変更量は大きいが、直接観測を削る縮退は不適切

差分は `+210/-16`、net `+194` 行です。P2 nitとしては大きい一方、fault testは helper結果・例外・nofollow pathnameをtest finalizer前に揃えており、preexisting testもidentityを期待例外のassertより先に回収しています。

任意の最小縮退は [_UnboundAliasSocket:1204](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1204) を既存double＋局所bind patchへ置き換える程度です。直接pathname/identity観測や外側finalizerを削る縮退は採るべきではありません。成果物影響がないため段6 blockerではありません。

## Refuted findings

- **M‑T146‑Aの先行kill懸念: refuted。** [line 1131](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1131) を無効化しても、partial-bindではclose、例外なし、`False`が先に通り、直接pathname不在assert [line 1311](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1311) だけが落ちます。最小fix不要。
- **M‑T146‑Cの帰属懸念: refuted。** post-unlink block [line 1155](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1155) は一意にできます。無効化時はno-op nodeの例外assertだけが効き、既存positive gateのreal unlinkは通ります。
- **test-doubleだけの恒真性: refuted。** `closed`はdouble自己申告ですが、単独oracleではありません。fault matrixはnofollow pathnameを [line 1300](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1300)、preexisting matrixはnofollow identityを [line 1347](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_integration.py:1347) でtest recovery前に直接観測します。
- **node到達・marker・mock leakage: refuted。** ASCII文字列parameterは7個の一意nodeidになります。plain runnerはファイル全体をpytestへ渡し、isolation metaは`socket.socket`への推移閉包とmarker集合を完全一致させます [isolation contract:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:70)、[同:118](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/orchestrator/tests/test_dev_waves_isolation_contract.py:118)。patchはcontext内で復元され、finalizerは保存済みreal unlinkを使用しています。
- **full runner到達漏れ: refuted。** default targetは全`orchestrator/tests` [run_tests.py:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/run_tests.py:42)、xdist時は`loadgroup` [run_tests.py:285](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t146-probe-cleanup/tools/run_tests.py:285) です。R2のreporting不足とは別問題です。

## Scope外候補

- hostile concurrent writerに対するpathname identityの原子的保護。
- arbitrary socket-close/dirfd-close複合例外。
- production `tools/dev_waves` のpartial-bind一般化。
- `tools/run_tests.py`全体へreporting flagを恒久追加する変更。T-146ではtargeted mutation commandの是正で足ります。

## 総括

**NO-GO。**

段6で必須なのは次の3点です。

1. EPERM/EIO fixtureを「real unlink後に非FNFを投げる」形へ直し、M‑T146‑Bを実効化する。
2. `-rf -rs` をやめ、`-rfs`または分離走でFAILED/SKIPPED nodeとreasonを保存する。
3. fix後commitでA/B/Cのexact anchorを再確認してmutation matrixを実走し、既存gate、新規7 node、long-path、isolation、2 test file、full runnerを親環境で再走する。

author artifact自身がlong-pathとfile全体を赤と記録しており、repository全走も未提示です。原因の静的経路はplanと整合しますが、赤をgreenへ読み替えることはできません。親環境でも同じ赤ならSKIPへ戻さず、段4再裁定で停止すべきです。