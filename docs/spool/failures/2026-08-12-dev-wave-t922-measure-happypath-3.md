---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t922-measure-happypath
seq: 3
---

## 新規

### {{F:focus-review-mustfix-transcription-loss}}. 焦点再レビューの must-fix が台帳へ写されるとき 1 件落ちた [手順漏れ]

- 事象: 段 6 焦点再レビューの逐語
  (`output/insights/2026-08-12_t810-harness-s2/verbatim/s6-focus.md`) は
  must-fix を **7 件**挙げていたが、台帳の後続タスク項へ写されたのは **6 件**だった。
  落ちたのは「node の repo_absence 4 boolean 固定と ready barrier の判定が非互換で、
  正規 wrapper の preflight が必ず拒否される」という **blocker** で、
  しかもそれは残り 1 件目 (正例経路を通す) の**達成条件**だった。
  後続 wave が段 1 で現行 main を測り直した結果その 1 件は既に閉じていたため、実害は出ていない。
- 根本原因: 焦点再レビューは所見対応表と must-fix 一覧という 2 つのリストを持つ。
  台帳へ写す作業に**件数の照合が無く**、写した側だけを見ても欠落が分からない。
  `DW-O16` は「所見ごとの closed / partial / regressed 対応表を要求する」までしか定めておらず、
  **その表から台帳への転記が完全であること**を要求していない。
- 恒久対応: 焦点再レビューの must-fix を台帳へ写すときは、**逐語の件数と台帳の件数を突き合わせ、
  一致しなければ写した側を直す**。後続 wave が起票内容を実行するときは逐語を一次資料として開き、
  台帳の要約だけを根拠にしない (memory `primary-source-includes-failures-ledger` の規律を
  焦点レビューへ広げる)。
- 再発検知: 逐語と台帳の件数照合 (目視)。機械化は未実装で、
  逐語の must-fix 見出しが定型でないため lint 化には形式の固定が要る。

## 再発

### F63

- **再発: 2026-08-12** — 同型が **codex 子の側**で起き、敵対レンズ 1 本が丸ごと失われた。
  段 3 の read-only 子が攻撃例の bytes の hash を実際に計算して示すために
  `python3 - <<'PY' ... Path('tools/pegasus/t810_pbs_wrapper.py') ... PY` を組み立て、
  `guard_bash` が「Pegasus unknown 実行体」として rc=2 で拒否した。子は回復せず
  codex が rc=1 / output 0 bytes で終了し、model_calls 45・約 1,080 秒を空費した。
  拒否されたのが書き込みでなく**読み取り専用の hash 計算**である点まで F63 と同じで、
  **防壁は設計どおり働いたが、子に通る書き方が prompt へ書かれていなかった。**
  親側の同型 (login で `perf stat` を probe できず実測が計算ノード job まで遅れる) が
  同日 20:39 に別 wave で独立に記録されており、親子で独立 2 例になった。
  恒久対応は read-only 子の prompt 定型 —「防護パスを含む shell を書くな・読取ツールで読め・
  hash の実値計算は結論に不要」の 3 点。再投入で回収できた。
  **`docs/dev-wave/operations.md` の `DW-O05` へ 1 行足す形は機械拒否された** —
  `check_docs.py` が `L1.5 unique footprint 9682 bytes > 予算 9566 bytes` で赤になり撤回した。
  予算引き上げは自己改善に含めないため恒久化は本記録に留める。
  同じ理由での自己改善停止はこれで**独立 3 例目**である。
