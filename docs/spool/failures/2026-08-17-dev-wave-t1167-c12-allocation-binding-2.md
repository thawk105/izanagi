---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1167-c12-allocation-binding
seq: 2
---

## 新規

### {{F:frozen-generation-collision}}. 並行 wave が同じ凍結世代番号を先に land し、merge では解けなかった [手順漏れ] [ドリフト]

- 事象: 本 wave と [T-1250] が同時に第 4 世代の条件契約凍結 record を発行した。[T-1250] が先に
  land したため、main を取り込んで自分の record を第 5 世代へ作り直そうとしたところ
  `prepare-revision` が `generation-mutated` で停止した。競合ファイルを main 側の内容へ揃えても
  解けなかった。続けて、文書変更を commit 済みのまま再生成しようとして
  `record-protected-mismatch` でも停止した。
- 根本原因: 2 つある。(1) 凍結 chain の世代 record 不変検査は作業木でなく **HEAD から到達できる
  全 commit** を走査し、同じ世代 path に 2 つ以上の blob oid があれば停止する。競合解消で作業木を
  揃えても、自 branch の履歴 commit に旧 blob が残る限り条件は成立しない。(2) `prepare-revision`
  は文書と証拠契約を**作業木**から読み、履歴は `--commit` で検証する。文書変更を commit 済みに
  すると、その commit の tip record が新しい文書と食い違い必ず落ちる。
- 恒久対応: 検査自体が fails-closed の実体である
  (`orchestrator/campaign/s8c_preregistration.py` の `validate_condition_freeze_at` が
  `generation-mutated` / `record-protected-mismatch` を送出し、`prepare_revision` を止める)。
  手順側は memory `frozen-generation-collision-needs-history-rebuild` — 凍結 artifact を発行する
  wave は、(a) land 前に自 branch 履歴が同一世代の別 blob を含まないことを確かめ、含むなら
  merge でなく main 直上の線形形へ組み直す、(b) 再生成は文書変更を**未 commit**の状態で走らせる。
- 再発検知: 上記 2 つの停止コードが本走前に発火する。どちらも rc=2 で世代を進めないため、
  誤った世代 record が commit へ入る経路は無い。

### {{F:truncated-output-as-closure}}. 自ら truncated と明示している出力を、閉包の全件として 2 度続けて読んだ [手順漏れ] [テスト代表性]

- 事象: 受入全走の赤 1 件を直すため、失敗出力に現れた差分 1 件を「変えるべき pin の全件」と扱って
  修正した。焦点走で同じテストがまた赤になり、今度は別の 2 件が差分に出た。`-vv` を付けて撮り
  直したが、その走行も予算で切られており全件ではなかった。最終的に正しい範囲は 4 件だった。
- 根本原因: どちらの出力も**自分が不完全であることを明示していた** (`...Full output truncated
  (N lines hidden)`、`omitted_bytes=450948`) のに、表示された差分を実質的な全件集合として扱った。
  「切り取られた出力を不在・網羅の根拠にしない」という規律を、検索結果には適用していたが
  **テストの失敗出力には適用していなかった**。加えて、実装子の報告 (同じ誤読を含む) を親が
  検証せずに受け取った。
- 恒久対応: memory `truncated-diagnostics-are-not-a-closure` — 閉包の全件性は、
  (a) 台帳側 (期待値を書いてある file) を全文検索して occurrence を数える、または
  (b) 完全一致検査そのものが緑になる、のいずれかでだけ確定する。**描画された差分は根拠にしない。**
  子の報告が閉包を主張したら、親は同じ 2 経路のどちらかで裏を取る。
- 再発検知: 修正後の焦点走が同じ node で再び赤になったら、まず「前回の根拠が切り取られていた
  のではないか」を疑う。出力に `truncated` / `omitted_bytes` が含まれていないかを見る。

## 再発

### F39

- **再発: 2026-08-17** — 8c 事前登録の C12 契約・拒否理由・判定器版・凍結世代を変えた wave が、
  それらを入力に持つ**活性化報告 digest の pin** を閉包から落とした。pin は別サブシステム
  (reflux 互換) の golden 構造の中にあり、key がファイル path ではなく派生 digest 名なので、
  path での閉包検索に原理的に掛からない — F39 の根本原因の逐語再現である。前回 [T-1186] が
  同じ pin を同じ理由で更新していた。検出は受入全走 (land 前、実害なし)。恒久対応は F39 から
  変更しない。運用として、判定器の版・理由コード・凍結世代を変える wave では、それらを入力に
  持つ**再導出 digest** を pin 閉包の既定対象に含める。
