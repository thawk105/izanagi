---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2401-evaluator-reason
seq: 2
---

## {{D:evaluator-diagnostic-outside-report-digest}}. 評価器例外の構造化理由は report digest の外側に置く

**決定:** 8c 判定器が評価器呼び出しの例外を握り潰すとき、捕捉した理由を構造化して残す。
置き場所は `ActivationReport` の**外側**とし、report と並ぶ第 2 返り値
(`activation_report_with_diagnostics_at`) にする。診断は
`callsite` / `exception_type` / `preregistration_reason` の 3 field だけを持ち、
いずれも実装が与える固定 literal か、型・文字種・長さを検査して通した値か、
検査に落ちた場合の診断専用 sentinel のいずれかである。
`str(exc)`・detail・message・traceback・repo path・環境値は載せない。
CLI `check` だけが診断を **stderr** へ 1 件 1 行の compact JSON で出す。
**fail-closed の終端は変えない** — status、`reason_code`、evidence、`effective`、
CLI stdout の bytes、report digest はすべて従来どおりである。

**理由:**

- 規律 3 は「pass/fail でなく、なぜ壊れたかを構造化して返す」ことを求める。判定器は
  12 条件すべてを一律 `ERROR / evaluator-exception` に倒すだけで、真因
  (`PreregistrationError` の `reason`) を捨てていた。F631 ではこのために
  「12 条件すべてが評価不能」という誤った現在地報告が出た。
- `ActivationReport` に field を足すのは採れない。`_activation_report_digest` は
  report の全 field から digest を作り、その値が `EffectivePreregistration` の
  `report_digest_sha256` になり、trial registry の `activation_report_digest_sha256` として
  永続化・再照合されている。field を足すと、**非 null の digest を束縛した
  registered-effective の成果物**が再導出で不一致になる (規律 7)。
  exploratory と formal non-certifying は digest が `None` なのでこの理由では変わらない。
- stdout を変えないのは、CLI と library の等価性を固定している既存検査と、
  stdout だけを保存する消費者の両方を壊さないためである。
- 診断値を固定 literal と検査済み文字列に限るのは、評価器が送出する例外の
  `reason` が設計上**開いた語彙**であり、path や環境値、非文字列、巨大文字列を
  持ちうるためである。診断は外部由来の値をそのまま運ぶ経路になってはならない。
- 診断の生成と出力は、それ自体が失敗しても現行の fail-closed 返却と終了値を変えない。
  診断を足したことで、従来 `ERROR` を返していた評価が未処理例外に変わるのは規律違反である。

**却下した選択肢:**

- **`ActivationReport` へ field を足す** — 上記のとおり永続化済み digest との対応が切れる。
- **`activation_report_at` へ可変 out-parameter を渡す** — 公開 signature を広げ、
  途中失敗時の部分書き込みと aliasing を持ち込む。production の registry 非注入境界も曖昧になる。
- **module 大域の可変状態・`contextvars`・logging** — 呼び出しと診断の対応が暗黙になり、
  thread・task・再入評価で混線する。明示的な返り値で足りる。
- **例外を外へ送出して呼び手に捕まえさせる** — 現行契約は例外を出さず report を返すことであり、
  fail-closed の返却契約と両立しない。
- **診断を CLI の stdout へ混ぜる** — stdout の bytes と JSON の形が変わり、
  CLI と library の等価性を固定している既存検査と衝突する。
- **`reason_code` へ自由文を入れる** — 語彙が閉じている前提を壊し、受理集合の判定を汚す。
