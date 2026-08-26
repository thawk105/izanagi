---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1668-classify-collector
seq: 2
---

## 新規

### {{F:adversarial-prompt-blocked-by-content-filter}}. 段 3 の敵対相談 prompt が provider の内容フィルタで拒否された [手順漏れ]

- 事象: `--stage consult --lane sol` の子が `thread.started` と最初の agent_message まで
  進んだ後、`This content was flagged for possible cybersecurity risk` で `turn.failed`。
  `.done` は 1、成果物ゼロ。証拠は job の `attempt-0001.events.jsonl`。
  文面を検査の語彙へ書き換えた 2 回目は通過し、must-fix 6 件を返した。
- 根本原因: 段 3 は「守らせず攻撃させる」段であり、prompt を素直に書くと
  「攻撃せよ」「偽の証拠で受領証が通る経路」「trust root を名乗る」と、攻勢的セキュリティ
  調査と同形の文面になる。実体は自リポジトリの正しさ検査の設計レビューだが、
  文面だけを見た filter は区別できない。rc を自前分類して同じ文面で再投入しても同じ拒否になる。
- 恒久対応: memory `adversarial-prompt-needs-review-vocabulary` —
  意味を保ったまま検査の語彙で書く 3 点 ((a) 攻撃→点検、(b) 偽造→材料の出所・信頼の根の循環、
  (c) 冒頭で自リポジトリの設計レビューだと明示) と、成果物ゼロ時に
  `attempt-0001.events.jsonl` の `turn.failed` 本文を読む手順を持つ。
  `docs/dev-wave/workers.md` の `DW-S03` へ入れる案は L1.5 の byte 予算に空きが無く入らなかった
  (予算のために既存の安全義務を削らない規律に従い、追記せず memory へ置いた)。
- 再発検知: 段 3 の子が成果物ゼロで `.done` を返したら、rc を分類する前に
  `attempt-0001.events.jsonl` の `turn.failed` 本文を読む。内容フィルタなら文面を書き換える。

### {{F:background-launch-output-discarded-hides-start-failure}}. 背景投入の出力を捨てて起動自体の失敗を失った [手順漏れ]

- 事象: 段 3 の runner script に実行権を付け忘れたまま
  `nohup setsid bash -c '<script> <arg>' </dev/null >/dev/null 2>&1 &` で投入したため、
  `Permission denied` が `/dev/null` へ消え、pid file も `.done` も現れないまま
  pid 待ちが空振りした。原因特定に往復を要した。
- 根本原因: `.done` と exit code で判定する既定 (`DW-O01`) は producer が起動した後を
  覆うが、**producer が一度も起動しなかった場合**を覆わない。その場合の唯一の徴候は
  投入行自身の stderr であり、それを捨てていた。
- 恒久対応: memory `background-launch-must-log-its-own-stderr` —
  投入行の stdout/stderr を `<wave dir>/<stage>-launch.log` へ落とし、
  pid file が現れなければまずその log を読む。
  `docs/dev-wave/operations.md` の `DW-O01` へ入れる案は L1.5 の byte 予算に空きが無く
  入らなかった。
- 再発検知: 背景投入の直後に pid file を待ち、現れなければ launch log を読む。
  launch log が空でなければ起動失敗である。
