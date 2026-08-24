---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1462-t1464-checkpoint-integrity
seq: 1
---

## 新規

### {{F:codex-jsonl-backslash-unterminated-string}}. backslash付き正規表現リテラルを含むtool出力がcodex JSONL strict parserを「Unterminated string」で落とす [手順漏れ]

- 事象: 段5実装子 (`--stage author`) が `codex_exit_code=0`・392秒・21 model call・
  2004 bytes の完全な出力を生成したにもかかわらず、receiptが`evidence_status=invalid`/
  `outcome=not_accepted`/`launcher_rc=1`になり `-o` の最終成果物が書かれなかった。同waveの
  段6敵対レビュー2本・fix1本でも同型が再発した (合計4回)。さらに 2026-08-24 の再開 context で
  main 取り込み後の合成監査子 (`--stage author`) でも再発し、同 wave 内で計5回になった。
  この5回目は `codex_exit_code=0`・602秒・27 model call・9316 bytes で、
  `check_codex_output.py` rc=0 の健全な出力だった。
- 根本原因: `orchestrator.codex_roles.events.parse_jsonl`を`attempt-0001.events.jsonl`へ
  直接importして実測した結果、子が`sed`/`git diff`で出力した内容 (親のhandoff・段2プラン・
  実装差分) に含まれる`\x00-\x1f`等の正規表現リテラル (backslash付き) が、command_execution
  イベントの`aggregated_output`へ埋め込まれる際にJSON escapeの整合が崩れ、「Unterminated
  string」でJSON parseに失敗する行が生じた。web_searchの重複key (F217) でも非NFC文字
  (F223) でもない別の trigger — backslashを多く含む正規表現/コードスニペットをtool出力
  経由で読ませると再現しうる。
- 恒久対応: 未実施。当面の回避は `attempt-0001.output.md` を`check_codex_output.py`で検収
  (rc=0なら内容は健全) して`-o`の期待パスへ複製するrecover手順 (F223の回避と同型)。
  恒久対応 (parser側でbackslash-escapeを堅牢化する、または子promptで正規表現を含む大きい
  tool出力を避けさせる) は本waveのscope外。
- 再発検知: `evidence_status=invalid`で`codex_exit_code=0`・成果物`check_codex_output.py`
  rc=0のとき、F217 (`web_search`重複key) でもF223 (非NFC行) でもなければ本F。
  `attempt-*.events.jsonl`を`orchestrator.codex_roles.events.parse_jsonl`へ1行ずつ通し
  `EventValidationError`の`"Unterminated string"`メッセージで特定できる。
  子の仕事自体が正規表現リテラルを扱う内容 (本waveの制御文字除去がまさにそれ) のときは
  決定的に再発すると考えてよい。

### {{F:staged-merge-blocks-codex-author-launch}}. 両親が同じ実装面fileを触るmergeで、規約が要求するCodex author子を起動する経路が機械的に存在しない [手順漏れ]

- 事象: local main の取り込みで両親が同じ実装面 file を触ったため、`check_ai_provenance.py` が
  merge commit に Codex `role=author` を要求した (rc=1)。ところが `git merge --no-ff --no-commit`
  を抱えたまま `tools/dev_wave_codex.py` で author 子を起動すると、launcher が
  `docs/dev-wave/operations.md: working tree が authority commit と異なる` で rc=2 拒否した。
  規約が要求する子を、規約が指す状態のままでは起動できない。
- 根本原因: `tools/dev_waves/launch_authority.py` の `snapshot_authority()` は commit 引数を
  省略した live 使用時に authority 文書 2 本の working tree bytes と HEAD の blob を byte 比較する。
  staged merge では authority 文書が main 側の版になっており HEAD と一致しない。authority commit を
  外から与える CLI 経路も無い。DW-O17 は「実装面 path が両親と異なれば Codex `role=author` へ」と
  書くが、その状態で子を起動する手順を持たない。
- near miss: working tree の authority 文書だけを HEAD の版へ書き戻せば gate は通るが、これは
  gate の迂回であり、子が読む authority が実際の HEAD と食い違う。採らなかった。
- 恒久対応: {{D:merge-author-two-commit-split}} — 重なる path を片親の版で確定させた merge commit と、
  clean tree で Codex `role=author` が合成を再適用する commit の 2 本へ分け、分割前の
  `git write-tree` と分割後の `HEAD^{tree}` の一致を照合する。
- 再発検知: merge 直前の `check_ai_provenance.py --message-file` が
  `実装面に Codex role=author がない — paths=...` を出したとき本 F の条件に入る。
  DW-O17 の本文へ手順を統合する案は、L2 単節予算 1000 bytes に対し DW-O17 が既に 974 bytes を
  使っており入らない。予算値の引き上げは自己改善の範囲外 (`docs/skill-self-improvement.md`) のため
  ユーザー裁定へ返す。
