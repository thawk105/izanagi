---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t663-flaky-truth-table
seq: 3
---

## 新規

### {{F:checkout-restore-wiped-uncommitted-child-work}}. 未 commit の子成果が乗った tree で probe を `git checkout --` 復元し、実装を消した [手順漏れ]

- 事象: 段 6 の fix 子が書いた 1456 行の変更が working tree にあるまま、親が段 1 と同じ
  1 行 probe (既定 wall 予算の縮小) を実編集で行い、`git checkout -- <file>` で復元した。
  同じファイルだったため、probe だけでなく段 5 実装と fix 1 巡目が丸ごと HEAD へ巻き戻った。
- 根本原因: `DW-O19` は「変異前を clean 確認し」て復元することを求めているが、親はその
  precondition を確認せずに復元手順だけを実行した。段 5 の snapshot patch は退避してあったが、
  fix 後の snapshot は無かった。
- 影響: 段 5 は退避 patch から byte 一致で復元でき (799 insertions が一致)、失ったのは
  fix 1 巡目のみ。fix は同じ入力で再実行し、その巡で発見した新所見も併せて閉じた。
- 恒久対応: 親が実編集 probe を行う前に `git status --porcelain` が空であることを確認する。
  空でなければ先に統合 commit を打つ。dev-wave 入口の `DW-O19` 条件へ
  「親の probe でも成立する」ことを明記する (本 wave の改善候補として起票)。
- 再発検知: probe 直後の `git diff --stat` が probe の 1 行だけであること、および
  復元後に `git log --oneline -1` が期待する統合 commit を指すこと。

### {{F:flake-instrumentation-broke-under-the-flake}}. フレークの計装が、そのフレークの発火条件で `DID NOT RAISE` になった [テストフレーク] [恒真ゲート]

- 事象: F57 の launcher フレークを観測するために新設した wiring meta-test が、
  実 launcher の終了コードが 0 になる前提で `pytest.raises` を書いていた。
  F57 が発火して終了コードが 1 になると不一致が消え、`Failed: DID NOT RAISE` で落ちる。
  親が時間予算を 0.30 秒へ縮めて負荷条件を模し、決定的に再現した (23 failed / 56 passed)。
  受入相当の走行でも fix 前に 2 回赤くなり、その後 5 回緑という不安定な挙動を示していた。
- 根本原因: 「正常系は必ずこの終了コードを返す」という、まさに壊れている前提を計装が使っていた。
- 恒久対応: {{D:flake-instrumentation-must-not-depend-on-the-flake}}。実プロセスを起動する
  診断 meta-test は起こりえない期待値を渡し、不一致の成立を無条件にする。
- 再発検知: 時間予算を縮めた probe で診断 meta-test の赤がゼロであること
  (fix 後の同 probe は `DID NOT RAISE` 0 件、診断 meta-test の赤 0 件)。

## 再発

### F57

- **再発: 2026-08-08 ([T-182] wave の受入全走、[T-663] として起票された観測)** —
  `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table` が
  1 件落ち、単独再走と直前の全走では緑だった。台帳の型どおりである。
  **新しい情報は 3 点。**
  (i) 失敗署名 `assert 1 == 0` / 出力空は、production の `accepted` を成す
  **7 条件のどれが欠けても**生じ、区別する receipt は pytest tmp とともに失われる。
  台帳の「未確定」はこの多義性が原因であり、観測不足であって解析不足ではない。
  (ii) 成功期待テストの launcher 実所要は median 0.428 / p90 0.671 秒 (login node、receipt 84 件)。
  既定 wall 予算 3.0 秒に対する余裕は約 7 倍で、単独 file を計算ノード 32 並列で走らせても
  再現しない。再現には数千件規模の全走が要る。
  (iii) 既定 wall 予算を 0.30 秒へ縮めると同じ署名が決定的に再現する。これは
  **正の対照であって原因の証明ではない**。
- **対応 (原因確定ではない)** — 次の再発でどの条件が落ちたかを観測できるよう、
  rc 不一致に受理 conjunct の真理値行・attempt stream の上限つき抜粋・実行環境・
  予算の実値を載せる計装を入れた。時間予算と production の受理集合は変更していない
  ({{D:flake-instrument-before-widening}})。**F57 と原因分離の task は閉じない。**
