---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t787-freeze-crlf
seq: 2
---

## {{D:freeze-crlf-single-call-scope}}. 凍結層の CR/LF 拒否は NUL を保留付きで優先し、NUL 優先の射程は単一 hash 呼出し内に限る

**決定:** evidence contract の hash 関数 (`evidence_contract_sha256`) の既存走査へ CR (U+000D) /
LF (U+000A) の検査を足す。走査対象・検査位置・detail は D281 のまま (key が exact `path` かつ値が
`str`、canonical 化に成功した後・hash を返す前、detail は `repr(JSON pointer)` だけ)。
理由語は新語 `evidence-contract-path-crlf` とし、NUL の `evidence-contract-path-nul` は変えない。

**NUL は見つけ次第 raise し、CR/LF は文書順で最初の pointer だけ保留して走査完了後に raise する。**
両方を含む契約でも、NUL がある限り従来の理由語と従来の pointer を返す。

**NUL 優先が成り立つ射程は単一 `evidence_contract_sha256(raw)` 呼出し内に限る。**履歴検証は
祖先順に各 commit の契約を hash するので、祖先が CR/LF 契約・後続が NUL 契約という履歴では、
祖先の CR/LF が理由語を決める。すなわち**履歴では「祖先順で最初に禁止制御文字を含む契約」が
理由語を決める**。この挙動をテストで固定する。

**理由:**
- CR/LF をその場で raise すると、文書順で後ろに NUL がある契約の理由語と pointer が変わる。
  実測では、前方に CR・後方に NUL を置いた契約を変更前の実装が
  `evidence-contract-path-nul` と後方 NUL の pointer で拒否していた。保留にすればこれが不変になる。
- 履歴全体で NUL を優先するには全祖先を 2 周する必要があり、単一 choke point・単一走査・
  early-return という D281 の設計を壊す。得られるのは診断語の優先順位だけで、釣り合わない。
- 射程を限定しても**受理集合は 1 bit も変わらない**。CR/LF 契約を含む履歴も NUL 契約を含む履歴も、
  変更の前後を問わず拒否される。変わるのは診断語と pointer だけである。
- 該当する履歴は現に存在しない。HEAD 祖先の distinct な契約 blob は 1 個で、その 38 個の
  `path` に CR / LF / NUL は 0 件である。
- 統一語 (`…-control-char`) への改名は、NUL 側の既存診断契約と D281 の参照を壊すので採らない。

**却下した選択肢:**
- 履歴・発行 transaction 全体で NUL を優先する二段検査 — 上記のとおり設計を壊し、受理集合は変わらない。
- CR/LF を発見時に即 raise — NUL 入り契約の診断契約が変わる。
- 契約読込 (`load_contract_bytes`) の流用 — schema 違反まで拒否するので受理集合が変わる (D281 で既出)。
- 制御文字一般 (全 C0) への拡大 — 承認された裁定は CR/LF に限られ、TAB 等を拒否すると
  有効な契約が凍結台帳から落ちる。過剰拒否を検出する正例を変異で登録して塞いだ。
