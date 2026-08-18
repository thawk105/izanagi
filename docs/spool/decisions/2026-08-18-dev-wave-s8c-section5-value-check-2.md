---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-s8c-section5-value-check
seq: 2
---

## {{D:section5-value-violation-reporting}}. 8c §5 の値制約違反は記入済み判定を変えず構造化報告と repo 不変検査で塞ぐ

**決定:** `docs/phase3-8c-preregistration.md` §5 の欄別値制約 (現在は反復単位対比の判定パラメータ欄
のみ) を検証する validator を `orchestrator/campaign/s8c_preregistration.py` に置き、production の
parse 経路から到達可能にする。ただし次を守る。

- `_classify_section5_value` が返す `FieldStatus` (記入済み / 未記入 / 不正) と、
  `ActivationReport.effective` の連言式を**変えない**。制約違反値は記入済みのままである。
- 違反は `Section5ValueViolation` (欄名・違反位置・違反軸ごとの理由コード) として
  `MarkdownContract` に載せ、最初の 1 件で打ち切らず全件返す。
- `ActivationReport` と `Section5Finding` の field 集合は変えない (report digest を動かさないため)。
- **実効的な閂は repo の不変検査に置く。** 生きた文書の §5 に制約違反値が入ると受入が赤になる。
  恒真化を避けるため、生き文書の bytes へ 1 軸だけ違反する値を差し込んで production の parse 経路で
  違反が出ることを確かめる positive control を同じ検査 file に置き、置換の空振りも検出させる。
- validator table の key が文書の §5 欄名集合に実在することを meta-test で pin する。
- 8b §10.2 が凍結するのは `n` の整数・2 以上、平均差の下限の有限・正、標本 SD 上限の有限・非負、
  単位と向きの同時固定だけである。`H1` / `H2` の exact key 集合は 8c 側の表現裁定であり、
  表現を変えるときは 8c 側の改訂で行う。単位と向きは非空文字列までを構文的に担保し、実値の
  意味整合 (judge が引く向きと一致するか) は judge の責務とする。上限値の負のゼロは
  「有限の非負」に合致するため受理する。

**理由:**
- 8c の凍結本文は「記入済み」を canonical JSON か否かだけで定義し、続けて
  「欄ごとの型・単位・範囲の検証は本手続きの対象外である」と明記している。違反値を記入済み判定で
  倒す形はこの凍結本文と直接矛盾し、改訂には docs 編集と新世代 record が要る。
- D458 は判定器の受理集合・拒否理由を変える変更に版 bump と新世代 record を要求する。新世代 record の
  裁定参照はその commit 時点の decisions 見出しの実在を要求し、番号は land の fold でしか確定しない。
  並行 wave が複数走る状況で世代番号を先取りすると、衝突を merge で解けない。
- 8c §6 の前提条件 7 は「validator が production 経路から到達可能でなければ充足しない」と名指しで
  要求している。本決定はその必要条件を満たす実体であり、条件の充足判定そのものは変えない。
- 8b §10.2 は「同欄を記入してよいのは、それらを機械検証する consumer が実在するときに限る」と
  述べている。repo 不変検査に閂を置けば、違反値を含む変更は land できなくなり、この順序が実際に
  強制される。

**却下した選択肢:**
- 違反値を不正扱いにして未発効へ倒す — 凍結本文と矛盾し、版 bump と新世代 record を伴う。
  いずれも本 wave の scope 外指定に一致するため、裁定パッケージとしてユーザーへ返した。
- 発効の連言式へ第 4 項を足す — 凍結本文が発効を 3 項の連言として定義しているため同じ矛盾を生む。
- 違反を `ActivationReport` へ載せる — report digest が動く。現在 capability を持つ成果物は無いが、
  D458 の「射影された判定入力の意味」に触れうるため裁定なしには実施しない。
- 単位と向きに固定語彙を強制する — 8b は語彙を凍結しておらず、将来の正当な記入を拒む過剰拒否になる。
