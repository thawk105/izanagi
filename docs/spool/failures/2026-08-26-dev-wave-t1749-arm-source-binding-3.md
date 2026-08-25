---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1749-arm-source-binding
seq: 3
---

## 新規

### {{F:parent-placeholder-invites-non-nfc}}. 親が書いた代替表記を子が実文字と推測し、成果物が全損した [手順漏れ] [観測]

- 事象: 段 5 実装子が `codex_exit_code=0` / `validator_rc=0` で完走し、実装も作業ツリーへ
  反映したのに、receipt が `evidence_status=invalid` / `accepted=false` / `launcher_rc=1` になり
  `-o` の成果物が書かれなかった。126 model call・1784 秒。同 wave の段 3 でも 1 本が同じ状態で
  捨てられている (そちらは既知 3 原因のいずれでもなく F540 の型)。
- 根本原因: 親の裁定文書が golden 表の非 ASCII 例を `("e-acute", "nihongo")` という**代替表記**で
  書いていた。親側の編集ツールが NUL を含む literal を保持できず、意味の分かる ASCII へ
  置き換えたためである。子はこれを「実文字を指している」と推測し、確認のため
  結合文字を含む文字列を command へ直接打った。その event 行が非 NFC になり
  `stdout_invalid` が立って全損した。**F223 は発火源を「repo 内の tracked file 2 行」と
  記述しているが、実際には親の prompt / 裁定文書も同じ発火源になる。**
- 恒久対応: 親が子へ渡す文書では、非 ASCII の値を必ず `chr(...)` 表記で書き、
  「非 ASCII 文字を command にも成果物にも literal で打つな」を prompt の禁止事項へ入れる。
  本 wave の fix 子 prompt 2 本と裁定文書はこの形へ改めてあり、以後の子は全損していない。
- 再発検知: `evidence_status=invalid` を見たら `attempt-*.events.jsonl` の各行へ
  `unicodedata.normalize("NFC", line) != line` を当てる。非 NFC 行が子の**自作 command** に
  現れていたら本 F、repo の tracked file 由来なら F223、どちらでもなければ F540。

## 再発

### F518

- **再発: 2026-08-26** — 背景 job の dev-wave で、待ち手が成果物不在のまま完了を返す事象を
  1 セッション内で 6 回踏んだ。うち 1 回は害が出た — 親が「投入ラッパーが落ちた」と誤診して
  ユーザーへ報告し、実際には全走が継続中だった (後に完走し 16,529 passed で戻ったため訂正)。
  終盤は待ち手が数秒で空 exit する状態になり、`.done` の現物確認と harness process の
  直接照合へ切り替えて進めた。F518 の「通知も rc も完了の証拠にならない」がそのまま効いた。

### F598

- **再発: 2026-08-26** — 変異 harness の起動条件で再び時間を使った。今回踏んだのは
  「作業ツリーが固定 HEAD と一致していること」で、段順どおり段 6 で変異へ入ると
  実装が未 commit のため必ず止まる。`--plan-only` の preflight は 1 回で通り、
  F598 の恒久対応が効いた。所要見積りは仮値のまま出すと過大 (24000 秒) になるため、
  焦点走を 1 回実測して差し替えた (実測 62 秒)。
