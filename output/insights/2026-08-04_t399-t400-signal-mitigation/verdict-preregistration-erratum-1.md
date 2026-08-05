# 事前登録 erratum 1 — 会計欠測の下位分類語彙 (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`
- 本文書は `verdict-preregistration.md` の erratum である。初回凍結文は消さない。

## 対象

凍結文「accounting 欠測だけで上記 signal 観測を無効にしないが、`accounting_evidence:false` を
必ず残す」および「`accounting_available=false` のみ...を retry 理由にしない」。

## 追記 (実測後に判明した記録上の必要)

実 probe 走行 (a1、request 887918/887919) で、racctjob / racctreq が
`sudo: パスワードが必要です` により**恒久的に**欠測することが判明した。凍結文の「欠測」は
下位分類を持たなかったため、evidence の機械可読性のために次の 3 語を追記する。

- `permission` — permission marker (sudo 等) を検出した失敗
- `empty` — command は成功したが対象 request の record がゼロ
- `error` — command が非ゼロ終了またはその他の失敗

## 判定への影響

**なし。** 3 語はいずれも「欠測 (accounting_available=false)」の下位分類であり、
凍結済みの判定式 (欠測は観測を無効にしない / retry 理由にしない / evidence へ false を残す)
の適用対象・結論を 1 つも変えない。判定式・閾値・語彙 (UNKNOWN 規約) 自体は不変。
record が**存在する** snapshot への integrity / cause 検査 (foreign ID・件数・因果矛盾で
観測無効) も不変である。available=true の snapshot で integrity / cause が評価不能になる
組合せは malformed であり、欠測でなく観測無効側に倒す (凍結文の「欠測だけで無効にしない」の
「だけ」の射程を明確化するものであり、緩和ではない)。
