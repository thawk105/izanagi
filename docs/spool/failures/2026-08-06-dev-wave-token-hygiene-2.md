---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-token-hygiene
seq: 2
---

## 新規

### {{F:measurement-double-count-reported-to-user}}. 自作の計測スクリプトが二重計上したまま結論をユーザーへ報告した [誤前提] [テスト代表性]

- 事象: 開発ループのトークン消費を測る使い捨てスクリプトで、同一の content block を
  `assistant:tool_use` と `in:<tool>` の 2 系統へ加算し、割合の分母にも両方を入れた。
  その比 (tool_result 33.5% / thinking 26.8% / tool_use input 17.9% / text 2.0%) を
  「文脈の内訳」としてユーザーへ報告した。同じ走査で、観測 model call 数を tool 呼び出し数と
  取り違えた値 (子 1 tool あたり 105,774 tok) も報告した。いずれも敵対レンズが実データで否定した。
  さらに前段では、transcript が 1 応答を content block ごとに複数 record へ割り usage を
  複製することに気づかず、record 単位で数えて応答数とトークンを 2 倍に計上していた
  (これは自分で気づいて訂正した)。
- 根本原因: 計測器そのものに正しさの検査を置かなかった。合成 fixture で
  「期待どおりの値になるか」を確かめないまま、実データの出力の大きさだけを見て納得した。
  母集団 (走査 root・filter・時間窓の判定根拠) も定義せず、単一 encoded cwd の subtotal を
  「6 日間の総量」と呼んだ。
- 恒久対応: 計測を `tools/claude_session_ledger.py` へ固定し、
  `orchestrator/tests/test_claude_session_ledger.py` が合成 fixture で
  dedupe・最終 usage・入力 3 項・母集団報告・model call と tool 呼び出しの分離を検査する。
  台帳は母集団と読めなかった件数を必ず出力へ含める ({{D:claude-session-ledger}})。
- 再発検知: 変異 M1〜M5 (dedupe を外す / 最初の usage を採る / 入力 3 項をそれぞれ落とす) と
  M12 (母集団を報告から省く) が事前登録済みで、3 走目に 12/12 KILLED を確認した。

### {{F:bg-job-idled-without-a-wait}}. 背景 job が子を投入したまま待ちを張らず 6 時間 24 分停止した [手順漏れ]

- 事象: 段 6 の fix 子を投入したあと、完了待ちを張らずにユーザーへ中間報告して turn を終えた。
  子は 14:19 に rc=0 で完了していたが、ユーザーが 20:43 に「動いていますか？」と尋ねるまで
  何も進まなかった。空白は 6 時間 24 分。
- 根本原因: 「待ちは通知に任せて polling しない」という既存規律を、
  「待ちを張らなくてよい」と読み違えた。待ちが存在しないと完了通知が発火しない。
  投入と報告を同じ turn に置き、待ちだけを次 turn へ送る形にしたことが直接の原因である。
- 恒久対応: memory `never-end-turn-with-unawaited-child` — 子の投入と
  `until [ -f <.done> ]` の待ちを**同じ応答に入れる**。中間報告をする場合も、
  報告テキストと待ちを同居させ、報告だけで turn を終えない。
  待ちが tool timeout で背景へ移るのは可 (完了通知が発火するため)。
- 再発検知: ユーザーが概ね 1 時間おきに確認する運用とし、
  **5 時間以上まったく変化がない job は死んでいるとみなして止め、状態と再開コマンドを報告する**
  (2026-08-06 ユーザー指示)。

## 再発

### F87

- **再発: 2026-08-06** — トークン台帳 wave で、事前登録した変異 12 件のうち 1 走目に 6 件、
  2 走目に 1 件が MISMATCH になった。いずれも**変異は検出されていた** (rc=1、複数 node が落ちた)
  側であり、親が登録した `expected_nodes` が実測の真部分集合だったことが原因である。
  今回の新しさは 2 つ。(a) 親が「この変異はこのテストが殺すはず」と考えた node だけを登録し、
  同じ fixture を共有する他テストが正当に道連れで落ちることを勘定に入れなかった。
  (b) 1 走目の SURVIVED (M7) を閉じるためにテストを 1 本追加したところ、
  配分と件数を変える変異 (M9・M11) の failed node 集合が増え、2 走目で新たな MISMATCH を生んだ —
  **テストを足すこと自体が既存の登録を陳腐化させる**。
  対応として 3 走目は実測 failed node をそのまま登録して 12/12 KILLED・MISMATCH 0 を得た。
  v1 / v2 の spec と台帳は消さず erratum として
  `output/insights/2026-08-06_token-hygiene/` に残した。
  恒久対応は F87 本文から変更なし (期待 node は実効ゲートから導き、確認できないものは登録しない)。
