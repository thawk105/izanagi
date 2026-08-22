---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1472-provider-init-indeterminate
seq: 3
---

## 新規

### {{F:acceptance-red-check-shares-common-git-config-across-probe-worktrees}}. 受入の赤帰属判定が共有 `.git/config` の書込みロック競合で判定不能になり、正常完走した全走を丸ごと捨てさせる [資源競合]

- 事象: [T-1472] wave の受入全走は `26 failed, 14259 passed, 96 skipped in 224.03s` で
  正常に完走したにもかかわらず、その赤 26 件の帰属を判定する
  `tools/check_acceptance_reds.py` が
  `status=invalid-input` /
  `cache-only submodule URL rewrite failed with rc=255: 'external/ccbench'` で落ち、
  受入全体が `stage=acceptance-red-check rc=70 source_rc=2` になった。
  判定は 26 件 × 約 90 秒 を約 11 分走ったところで落ちており、**テストの赤ではないのに
  受入全走 1 回 (本体 3 分 44 秒 + 判定 40 分見込み) が丸ごと無駄になる**。
  発生時の並行 worktree 数は 31 だった。
- 根本原因: `_probe_node` が `git worktree add --detach` で作る probe worktree に対し、
  `_initialize_submodules_cache_only` が `git config submodule.<path>.url <module_dir>` を
  **`--worktree` スコープ指定なし**で実行する。`git worktree add` が作る linked worktree は
  既定で親 repo と共通の `.git/config` を共有するため、この書込みは実質「repo 全体で共有された
  1 個の config ファイル」への書込みになる。多数の並行 wave がそれぞれの probe worktree で
  同時にこれを叩くと書込みロックが競合し、負けた側が `git config` の rc=255
  (`could not lock config file` の典型的な終了コード) で失敗する。
  高並行下でのみ再現するため単体実行では気づけない。
- **単純再投入では抜けられない (本 wave 実測)。** 2 回連続 (attempt6 / attempt7) で同一箇所・
  同一 rc で落ちた。落ちた時点の実測は **並行 `check_acceptance_reds` プロセス 7 本・
  worktree 34 個**、共有 `.git/config` の mtime は秒単位で更新され続けており、
  stale lock ではなく実時間の競合である。さらに 7 本はいずれも
  `submodule.external/ccbench.url` へ**既に入っているのと同じ値**を書いており、
  内容として無意味な書込みがロックだけを奪い合っている。1 受入あたりこの書込みは
  赤の件数 × probe 数だけ発生するため、衝突は確率的にほぼ確実になる。
  **再投入は自分の成功確率を上げないまま他 wave の競合を悪化させる。**
- 恒久対応: auto-memory `check-acceptance-reds-submodule-config-race` に判別法を固定済み。
  コード側の是正 — `git config` で共有 config へ永続化せず
  `git -c submodule.<path>.url=<module_dir> submodule update --init --no-fetch` の形で
  1 コマンドに畳む (または現在値と一致するときは書込みを省く) — は実装面の変更であり、
  **裁定パッケージとしてユーザーへ返す** (本 wave の scope 外)。
  なお `check_acceptance_reds.py` は `tested_main` 側で走るため、この checker を直す wave は
  自分の修正の恩恵を受けられない (自分の受入も旧版で判定される)。
- **構造的な逃げ道: 赤が 0 件なら非帰属判定そのものが呼ばれず、この競合は発生しない。**
  現在の赤 26 件はすべて `orchestrator/tests/test_sort_swo_oracle.py` であり、
  同 file を受入から恒久除外するユーザー裁定が既に出て実装 wave が動いている。
  それが着地すれば受入は本体 3 分半で緑に返り、本問題は発火しなくなる。
- 再発検知: `stage=acceptance-red-check` かつ
  `cache-only submodule URL rewrite failed with rc=255` の組で機械判別できる。
  `DW-O18` の 3 分類のうち「rc=2 判定不能で非帰属根拠なし」に当たり、no-verdict retry の
  対象外・新規 attempt での再投入が正しい扱いである。
- 独立再現: 2026-08-22 の [T-755] 受入 (同じ `external/ccbench`、同じ rc=255、
  本体は 26 failed / 14245 passed / 96 skipped で正常完走) と、本件 (2026-08-23、[T-1472]) の
  2 例。別 wave・別日・別 tip で同型が出ており、単発のフレークではない。

## 再発

### F333

- **再発: 2026-08-23** — [T-1472] wave の段 9 で、親が `check_ai_provenance.py --range` の
  full-history 監査を**呼び出し側のタイムアウト (2 分) で打ち切った**ため dispatch 親が
  SIGTERM され、PBS job `937261.nqsv` が孤児化した (`receipt.json` の `outcome` は F333 と
  逐語同一の `{"kind":"infra","rc":16,"reason":"_SignalAbort: signal 15"}`)。
  **F333 が記録していない帰結**として、孤児化は当該 worktree へ
  `output/pegasus-dispatch/orphan-hold.json` を立て、以後この worktree からの dispatch を
  全面的に止めた。直後に投入した受入全走が 48 秒で
  `stage=acceptance-command rc=70 source_rc=16 reason=dispatch-attestation-malformed` となり、
  子ログの実体は `Pegasus orphan hold があるため scheduler command を起動しません` だった
  — **受入の赤に見えるがテストは 1 件も走っていない。** 孤児 job 自身は 4 秒で
  `child_rc=0` と `check_ai_provenance: 5 件、違反なし` を書いて正常終了しており、
  失われたのは親側の結果回収だけだった。復旧は hold の `recovery` field に従い、
  手動 qdel をせず (F47 型ラッチを立てないため)、`qstat` で request の不在を確認し、
  source が clean で HEAD 不変であることを確かめてから hold を手動削除した。
  auto-memory `long-running-checks-need-generous-timeouts` に固定。
