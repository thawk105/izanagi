---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t139-producer-slice
seq: 3
---

## 新規

### {{F:lease-json-matched-as-plaintext}}. 受入 lease の待ち手が JSON 出力を平文パターンで照合し、取得済みの lease を 2 時間見落とした [手順漏れ] [恒真ゲート]

- 事象: 受入 lease の待ち手を `claim` の出力に対する glob `*state=acquired*` で書いた。
  実際の出力は JSON (`"state": "acquired"`) なので**一度も一致しない**。
  取得は 239 回目の試行で成立していたが検出できず、待ち手は上限 240 回まで回って
  「取得できず」で終了した。約 2 時間の待ちが無駄になった。lease 自体は保持したままだった。
- 根本原因: 出力形式を実物で確認せず、`status` サブコマンドが返す
  `state=held holder=... ` 形式 (key=value の平文) が `claim` でも同じだと仮定した。
  同じ tool の別サブコマンドが別形式を返す。
- 恒久対応: 待ち手は `claim` の出力を **JSON として parse** し、`state` field を読む
  (`python3 -c "import json,sys; print(json.load(sys.stdin)['state'])"` 等)。
  文字列の部分一致で状態機械を駆動しない。
- 再発検知: 待ち手が「取得できず」で終わったときに、終了前へ
  `status --wave <slug>` を 1 回入れて `holder_self` を確認する。
  `holder_self=true` なら取得済みの見落としであり、そのまま受入へ進む。
  **`--wave` を渡さない `status` は `holder_self=false` を返す**ため、所有判定には必ず渡す。

### {{F:codex-child-reads-parent-protocol-as-own}}. 実装子が親の役割分担文書を自分への指示と読み、入れ子で agent CLI を起動して 0 行で終わった [手順漏れ]

- 事象: 段 5 の実装子 (Codex `role=author`、workspace-write) が `rc=0` で終了し、
  採用条件の出力検査も通ったが、**編集ファイルは 0 件**だった。報告には
  「隔離 author subprocess が Codex CLI 初期化時に失敗した」とあり、
  自分がさらに author 子を起動する側だと解釈していた。
- 根本原因: prompt が scope を伝えるために親 brief と段 4 裁定を読ませたところ、
  そこに書かれた dev-wave の役割分担 (「実装面は Codex `role=author` の実装子が書く」) を
  自分への指示として受け取った。sandbox は書き込み可能であり、環境の問題ではない。
- 恒久対応: 実装子・レビュー子の prompt 冒頭に立場を明示する —
  「あなた自身がファイルを書く。別の agent CLI を起動しない。
  資料中の dev-wave 手続き規定は親の義務であってあなたへの指示ではない」。
  レビュー子では「ファイルを読む通常の shell コマンドは自由に使ってよい」も併記する
  (この一文を欠いたレビュー子は「読む手段がない」と解釈して 0 所見で停止した)。
- 再発検知: 実装子の完了判定に `git status --porcelain` の非空を加える。
  exit code と出力検査だけでは「何も書かなかった子」を緑と数える。
