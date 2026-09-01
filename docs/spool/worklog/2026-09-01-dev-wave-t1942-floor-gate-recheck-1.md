---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1942-floor-gate-recheck
seq: 1
title: [T-1942] 床値 official の投入前ゲートを測り直し、塞いでいるのは compiler input ではなく transport と適格性の矛盾だと確定した (docs のみ、branch worktree-dev-wave-t1942-floor-gate-recheck、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- ユーザー指示の停止条件が成立した。指示は「着手時にまず投入前ゲートを実測し直し、通ることを
  確認してから投入する。通らなければ実測結果を記録して停止し、無理に迂回しない」。
  **投入せず、実装もせずに閉じた。**
- 一次資料は `output/insights/2026-09-01_t1942-floor-official-transport-conflict/`。
- **塞ぎ要因は、依頼が想定していたものと違った。** 依頼は 2026-08-29 に特定した compiler input の
  赤が [T-2027] の着地で解けたかを問うていた。実測すると、それより上流に別の矛盾がある。
  詳細は {{D:floor-official-transport-seam-conflict}}。
- **2026-08-29 のゲート実測は、現行経路の生死を測っていなかった。** あの実測は落ちた job が
  残した manifest を現行 validator へ通したが、その manifest は schema v1 であり、
  v1 は「厳格な read-only 互換形式で移行も緩和もしない」と実装自身が明記している。
  設計として赤のままの入力を測っていた。588 件の内訳も「すべて絶対 path」ではなく
  549 件が絶対 path・39 件が snapshot 相対だった。**歴史的事実 (job が落ちたこと) は変わらない。**
- さらにその job は床値 campaign ではなく別 wave の probe である。したがって「無条件赤」を
  床値 campaign の構成へ一般化してはならない。床値 campaign の構成では、staging 破棄後も
  canonical な根へ再束縛される連鎖が存在する。**ただしこれは読解であり実測していない。**
  測る対象の経路が起動できないためである。
- **親の provisional 裁定が 2 件、実測で覆った。**
  - 入場鍵の判定対象を旧 marker 228 件と読んでいたが、現行の予約経路はそれを明示的に無視する。
    判定の権威は世代 scope の claim である ({{D:floor-fresh-claim-authority}})。
  - 試行登録簿の残枠を予算根拠にしようとしたが、その登録簿は fixture であり、
    consumer の canonical path とも階層が違っていた
    ({{F:test-fixture-wrote-into-shared-durable-admission-root}})。
  どちらも段 3 の敵対レンズが独立に反証し、親がコードで裏を取った。
- **依頼文の前提が 1 件、現状と逆だった。** 依頼は「判定床 0.030 は旧環境の write-heavy /
  balanced 由来で read-heavy を含まない」と書くが、`between_run_noise` の成果物を全件数えると、
  旧環境は 3 workload とも測ってあり、**現行 Pegasus は read-heavy だけがあって write-heavy と
  balanced が無い**。現行 Pegasus の read-heavy は within 0.996% / between 0.223% で
  0.030 を大きく下回る。ただし成果物自身が cold-boot・温度ドリフトを含まない下限だと明記して
  いるので、「read-heavy は較正済み」と無限定に書いてはならない。
  genuine な cross-campaign / between-block floor はどの workload でも未較正である。
- **予算承認の位置も確定した。** 走行の前提ではなく、結果を freeze へ昇格させる段の閂である
  ({{D:floor-budget-approval-is-post-run}})。
- 段 4 で「実装しない」と裁定したので段 5・6 を飛ばした。実装面の差分はゼロで、
  `DW-S04` に従い変異 matrix を免除した。受入全走は免除していない。
- 子は codex-cli の `gpt-5.6-sol` / xhigh を、段 2 plan 1 本、段 3 敵対相談 2 本 (lane sol / luna)
  の計 3 本。全件 `check_codex_output.py` 緑。段 5・6 の子は起動していない。
- qsub・build・性能測定・床値の実測はいずれも行っていない。ノードの単独性確認は発火していない。
- probe は書いていない。実測はすべて read-only の観測とコード読解である。

## 次の一手差分

### 更新

- [T-1942] **P2・ユーザー裁定待ち**: 現行 Pegasus・workload 別の床値を実測する。
  2026-09-01 に投入前ゲートを測り直し、**塞いでいるのは compiler input ではなく
  staged transport と refreeze 適格性の矛盾**だと確定した
  (`output/insights/2026-09-01_t1942-floor-official-transport-conflict/`)。
  official は承認束縛を実装しても起動できない。解消案 3 つを
  {{D:floor-official-transport-seam-conflict}} で裁定へ返した。
  あわせて、依頼文が指す量が (i) 床値 campaign の official 実測か
  (ii) between-run noise floor かの確定もユーザーへ返す。(ii) なら現行 Pegasus で
  欠けているのは write-heavy と balanced であり、既存 driver で今すぐ測れる。
  base: 6bae8b3c4d7ab302197fa8f976f6e152d75ce2d0c855724fa6eed28bb3fadde1
