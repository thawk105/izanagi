---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-cicada-promotion-uaf-fix
seq: 3
---

## 新規

### {{F:cicada-bad-alloc-attributed-without-axis-control}}. TPC-C の異常終了を genome の promotion 軸へ帰属させ、その軸だけを外した対照を置かなかった [手順漏れ] [テスト代表性]

- 事象: 前 wave (2026-09-29、CCBench の build 修理) は INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1 の genome で TPC-C M・R2 が `std::bad_alloc` で落ちるのを観測し、「promotion 有効の 8 genome は失格」とまとめた。2026-09-30 の診断 (gdb の catch throw と一要因対照) で、原因は promotion ではなく INLINE_VERSION_OPT=1 の `Tuple::init` が insert の版を無視する欠陥で、promotion 無効の OPT=1 genome (T0p) でも同じく落ちると分かった。失格の範囲 (8 genome) と原因の帰属 (promotion) がともにずれていた。
- 根本原因: 観測した genome が 2 つの軸 (OPT と PROMO) を同時に 1 にしており、異常の帰属先を後から付いた軸 (promotion の build が初めて通った) に置いた。「その軸だけを外した genome (OPT=1・PROMO=0) でも起きるか」の対照を置かず、送出点の backtrace も取らないまま、切り分けの対象を計装の有無と前 wave の自分の変更 (重複登録の除去) に限った。
- 恒久対応: 異常を genome の軸へ帰属させる記録は、(a) 送出点・最初の報告 (gdb の catch throw、ASan) と、(b) 疑う軸だけを外した genome の対照の両方を取ってから書く。md_32 の一次資料 (`output/insights/2026-09-30/ccbench-cicada-promotion-uaf-fix/README.md` §4) で帰属を訂正し、段 4 の事前登録 (追補 1) に「T0p (OPT=1・PROMO=0) も落ちる」を採否条件として置いた。memory `hub-evidence-and-check-design` に 1 行を足す。
- 再発検知: 段 3 の相談で「帰属先の軸だけを外した対照があるか」を正しさ境界レンズの確認項目にする (DW-S03 の「親自身の実測値とその一般化」の具体例)。

## 再発

### F546

- **再発: 2026-09-30** — VHash md_32 wave の段 5 で、CCBench の修理を Codex author に「submodule の作業木に実装せよ」と指示し、`cc/cicada/include/transaction.hh` への直接編集が guard_write に拒否された (子は迂回せず正しく停止、author 1 本を空費)。F546 の恒久対応 (使い捨て clone を編集面にし親が適用) が入口・reference に無く、親が prompt に書き忘れた。子木内の使い捨て clone (`md32-scratch/ccb`) で修理して差分を出す形で投げ直した。

### F100

- **再発: 2026-09-30** (near miss、実害なし) — VHash md_32 wave の親が、段 5 の診断 job の `--dry-run` を `cd <計測用の detached 子 worktree> && /usr/bin/python3.10 … --dry-run` で打ち、harness の追跡 cwd が子 worktree へ移って以後の Bash が拒否された。`EnterWorktree(path=<自分の wave worktree>)` で 1 回で復帰 (login の load 約 20)。以後の dry-run は `cd` を前置せず `--repo-root` の絶対 path で打った。書き込みは発生していない。
