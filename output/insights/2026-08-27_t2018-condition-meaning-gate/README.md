# T-2018 condition meaning gate

## 結論

`BACKOFF_FIXED` について、供給と意味を単一 pass bit に潰さない driver 非依存の
call-scoped gate を実装した。production driver への接続は 0 本である。

- supply arm: `assert_backoff_fixed_supply()` が source owner に対応する CMake cache-to-TU
  mapping と要求値の exact 一致を再導出する。
- meaning arm: `assert_backoff_fixed_meaning()` が適用後 source から抽出した decoder を
  standalone TU で実 compiler 評価し、`start=1/2` の各 cell を canonical float64 bits で
  pointwise 比較する。
- proof kind は standalone TU / finite pointwise witness に限定する。actual target TU、
  dynamic reachability、exact post-configure build input は証明しない。
- `driver_integration="none"`。現行 `EXTENDED_SWEEP_US` の 1000 点は未保護のままである。

D1198 は wave 開始後に main へ land し、T-1999 は「裁定待ち」から
「driver 群へ義務化することが裁定済み・実装待ち」へ変わった。本 wave ではユーザーが明示した
scope 外を維持し、次の T-1999 実装残件を開始していない。

## 他 AI 作業物の監査

元 Claude worktree `worktree-dev-wave-t2018-condition-meaning-gate` の tip は
`8d014c748286c6fec497d0afa10a395f159861b1`、tracked clean、未追跡は段1 brief と親実測の
2 file だけだった。T-2018 を指す live process は無く、manual lock だけだった。

2 file は source/D/F 正本と照合してから resume worktree へ移した。段3で次を訂正した。

- define-decode 候補は 9 個でなく 8 個。v1 は `BACKOFF_FIXED` だけを扱う。
- 親実測の 1500/2500 の witness/列は再現可能な golden でないため採用しない。
- 「上端 999 だけでは本 axis も閉じない」は過大。0..999 制約なら現 fixed-magnitude 軸は
  閉じるが、define-decode 族全体は閉じない。格子/符号化は変更していない。
- driver 配線 0 なので「次の投入を止める」とは主張しない。

## review と fix

段6の2レビューは初版を NO-GO とした。Codex fix 2巡で exact result type、dirfd +
`O_NOFOLLOW` capture、compiler 3-phase identity/hash、F707 pre-compiler 順序、単一理由 marker
fixture、process/identity test の mask を修正した。focus 2巡目は blocker 0 / GO。

Codex author 初回の最終 message は内容が有効だったが `## 総括` が無く F43 validator rc=1。
同じ dirty worktreeを別 author 子が監査し、wrong-RHS identity境界を追加確認して accepted outputを
再発行した。破損 output を採用していない。

## 実測

- 実装 commit: `13f9c1b5067bda82b19861127a53d90b79a9e207`
- 新 test file: 29 passed / 7.02s (bounded local)
- source_digest / sort wrapper 焦点: 5 passed / 4.09s
- plain-runner / duration-ledger coverage meta: 4 passed / 40.35s
- commit 前 provenance: 6718 commits、新規違反なし
- commit 後 provenance: 6719 commits、新規違反なし、Pegasus request `953723.nqsv`、child rc=0

### 受入で露出した consumer 取り残し

最初の全走は shard 1 の queue-wait-timeout と shard 2 の signal abortでbinding reportが2/3となり、
test childの判定前にinfra赤。per-request/generic orphan holdをrequest不存在・source clean確認後に
recoveryした。generic holdを消し忘れた再投入は3 shardともchild未起動であり、結果に数えない。

次の実全走は18,389 collected、18,326 passed、61 skipped、2 failed。新しい
`condition_meaning_gate._run_process` がcross-cutting process inventoryへ未登録だった。
Codex fixがexplicit non-CCBench siteへexact 1件を追加し、当該2 nodeは親実走で2 passed / 6.57s。
production gateの受理集合は変えていない。

## 変異 matrix

段4の初版登録はmask/過剰決定があり、probeを全件 SURVIVED 期待で走らせて失敗 node の
完全集合を採取した。probe は baseline PASSED、8件すべて MISMATCH（実際は全件 failure nodeあり）。
これを erratum として final spec へ再登録した。

final は fixed commit `13f9c1b50`、baseline PASSED、KILLED 8、SURVIVED 0、MISMATCH 0、
TIMEOUT 0、expected node完全一致 8/8。最終 wrapper は独立 common-dir の local cloneを
sourceに使い、`shared_snapshot_matches=true`、`teardown_completed=true`、child rc=0。

受入でprocess inventoryのtest-only fixを入れたため、DW-M07に従いfix commit
`16685229a989c7910599c7475b4524621616d09a` でも同じmatrixを再走した。postfixも
baseline PASSED、KILLED 8、SURVIVED 0、MISMATCH 0、TIMEOUT 0、expected完全一致8/8、
wrapper child rc0 / shared snapshot一致 / teardown完了である。

最初の final 2走は child 自体が8/8 KILLEDだったが、共有 primary checkout の
`.codex/worktrees/` 集合/並行 landで wrapper事後検査が rc125 となり不受理。結果を採用せず、
F537/F618 の既存手順どおり独立 cloneへ切り替えた。

## 成果物

- `verbatim/`: 段1〜6の brief / plan / review / fix / focus
- `mutation-spec-preregistered.json`: 段4初版
- `mutation-spec-probe.json`, `mutation-probe-report.json`: erratum probe
- `mutation-spec-final.json`, `mutation-final-report.json`: 最終 matrix
- `mutation-final-wrapper-receipt.json`, `mutation-final-attempts.json`: 採用 wrapper / scheduler証拠
- `mutation-postfix-{report,wrapper-receipt,attempts}.json`: acceptance fix後の再走証拠
- `mutation-final-race{1,2}-wrapper-receipt.json`: 不受理にした共有木race
- `verbatim/acceptance-inventory-fix.md`: 最終受入が露出したprocess inventory fix

### 逐語末尾空白の可逆正規化

`git diff --check` のため、可視文字を変えず行末の ASCII space 2 bytes だけを除いた。

- `verbatim/s3-consult-luna.md`: 原文 22,486 bytes、SHA-256
  `a4e443de0dc5f49d979b5c3814b41791db3d3f98822f2a627bf78067905255f4`。
  原文物理行 18, 20, 22, 80, 186, 188, 190, 192, 196 の各末尾へ `0x20 0x20` を戻せば復元できる。
- `verbatim/s6-review-luna.md`: 原文 13,081 bytes、SHA-256
  `03bd8742c09350f527316c573fc57ef5ce3258ebaaa82f004ceff9590e7974c2`。
  原文物理行 83, 84, 85, 88, 89, 90, 93, 94, 95, 98, 99, 100, 103, 104, 105 の
  各末尾へ `0x20 0x20` を戻せば復元できる。

## scope 外

- D1198/T-1999 の driver 群への必須接続
- patch / ledger / freeze bytes
- `EXTENDED_SWEEP_US`、符号化式、格子定数
- `BACKOFF_FIXED` 以外 7 macro の semantic-shape別一般化

push と remote branch 操作は人間に残す。
