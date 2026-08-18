---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t396-contract-alignment
seq: 3
---

## 新規

### {{F:codex-upstream-two-symptoms}}. codex の同一上流障害が「認証失効」と「枠切れ」の 2 症状で出た [手順漏れ]

- 事象: 2026-08-18 12:56〜13:07 JST、独立した 2 wave の codex 子が同時間帯に即死した。
  本 wave (段 3 敵対相談 2 本) の stderr は
  `HTTP error: 401 Unauthorized, url: wss://api.openai.com/v1/responses` の連打で、
  rc=1・出力 0 bytes・`codex login status` は "Logged in using ChatGPT" のままだった。
  並行 wave は同じ時間帯に events 内の usage limit メッセージとして観測した。
  症状だけでは「サブスクのログイン失効」と「利用枠の取り合い」を判別できない。
- 根本原因: 上流の同一障害が経路によって別の表層症状を出す。`codex login status` は
  credential の存在を見るだけで、API 側が拒否している状態を反映しない。
  401 を見て「ログインし直しが要る」と診断すると、実際には数分待てば回復する事象で
  ユーザー手番を要求してしまう (逆に枠切れと診断すると、本当に失効したとき復旧しない)。
- 恒久対応: memory `codex-auth-expiry-is-fail-closed-stop` へ「症状で原因を断定せず、
  新しい prompt bytes で 1 本だけ再投入して切り分ける」を足す。失敗は数十秒・token ゼロで安価であり、
  切り分けの費用は再投入 1 本より高くならない。判定は `docs/dev-wave/operations.md` の `DW-O01`
  どおり `.done` と exit code で行い、`codex login status` の表示を判定に使わない。
- 再発検知: `tools/check_codex_output.py` の rc≠0 が無出力を成果と誤認する経路を塞ぐ。
  再投入時は job-id が prompt 内容の sha256 で決まるため、prompt 本文を変えないと
  `既存の完全な receipt は上書きできない` で rc=2 になり、上書き事故も同時に塞がれる。
