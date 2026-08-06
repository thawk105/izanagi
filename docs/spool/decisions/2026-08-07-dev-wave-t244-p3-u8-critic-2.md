---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t244-p3-u8-critic
seq: 2
---

## {{D:critic-after-cell-admission}}. 8c 自律 trial の critic 呼び出しを cell の Layer 3 admission 確定後へ後置する

**決定:** 8c 自律 trial の generation ループを planner / coder / auditor / harness までに狭め、
critic の呼び出しを workload ごとの cell admission 確定後へ移す。critic 用の最小情報は cell の
私有 key へ積んで持ち越し、admission 確定の直後にまとめて消費する。
これは裁定 U-8 (2026-08-05 批准、「critic を Layer 3 admission・ledger seal・proof 書き込みの後へ移す」)
のうち、**8c に実在する唯一の anchor である Layer 3 admission への後置だけ**を実装したものである。

**射程の限定 (名乗りの上限):** 本決定は U-8 を完了させない。ledger seal は D201 が
8c への結線を実装しないと裁定済みであり、proof 書き込み (origin-proofs sidecar / report v3) は
前 wave が却下済みである。critic は依然 ledger seal と proof issuance より前に metrics を受け取る。
名乗ってよいのは **「8c 非認定 pilot の critic 呼び出しを cell の Layer 3 admission 確定後へ後置した」**
までであり、commit-reveal を閉じた・P3 充足・漏洩ゼロは名乗らない。
certified 選択、材料レポート、試行台帳の現在値と参照は不変で、D114 の cap=1 と承認上限 1 世代も不変である。

**受理集合の変更 (D96 の同一変更単位):**

- 承認済み唯一の運転である **1 世代の受理集合は不変**である。journal の role attempt 順は
  planner / coder / auditor / critic のままで、report の平坦化順と一致する。
- **generation 上限を上げて多世代を回した場合だけ**、後置により journal 順が
  `g1:P,C,A → g2:P,C,A → g1:critic → g2:critic` となり、report の平坦化順と食い違う。
  完了性検査の attempt 順検査が report publish 前に fail-closed で止める。
  この帰結は新しい定数や新しい gate を足さずに既存検査だけで成立する。境界テストを同じ変更単位に含めた。
- **例外から復元された cell が完了済みの持ち越しを持つ場合**も、journal が
  `supervisor-error → critic → run-finish` となり、terminal event は `run-finish` 直前という
  完了性検査の要求に反するため fail-closed になる。承認上限 1 世代では到達しない。
- **direct 入口は critic を呼ばなくなる。** critic は gate ではなく recipient なので正しさ防壁は
  弱まらないが、入口の contract 変化であるためテストで固定した。

**例外境界:** admission finalizer の失敗は回復させず伝播させ report を publish しない。
持ち越し critic 側 (digest 構築・admitted view 取得・provider 参照・invoke) の失敗は、
従来どおり supervisor-error へ回復する。critic の応答が不正なら cell を role-invalid とし、
harness 由来の停止理由より優先する。admission decision は巻き戻さない。
trial status の算出は全二相処理の後へ移した。report 構築の直前に、持ち越しの消費漏れと
admission decision の欠落をそれぞれ止める fail-closed 検査を置いた。

**理由:**

- U-8 は批准済みであり、8c に実在する anchor は Layer 3 admission だけだと実測で確定した。
- 承認上限 1 世代では critic の出力を読む先が記録だけであり、制御流へ還らないため、
  後置による挙動変化は承認運転では生じない。
- 多世代の fail-closed は既存の完了性検査だけで成立し、新しい統治を足す必要がない。

**却下した選択肢:**

- **順序の目印となる新しい journal event を足す** — 裁定射程外の新設統治であり、かつ同一 producer 由来の
  自己申告なので durable な順序を証明しない。敵対 2 レンズが独立に同じ判定を返した。
- **role/trial schema の版を上げる** — 当該定数は全 role の payload と共用されており、上げると
  全 role の入力 bytes と payload hash が変わり、既存の旧版 artifact が verifier と台帳の受理集合から
  外れる。目印を足さないなら版上げも不要である。
- **後置専用の generation 上限定数を新設する** — D114 の「上限は 1 定数、解除はその定数と境界テストの
  同時変更だけ」と衝突し、上限を正当に引き上げた後に承認外の過剰拒否になる。
  新定数なしでも多世代は既に fail-closed である。
- **critic を上位関数へ持ち上げ、cell を跨いでまとめて呼ぶ** — 複数 workload で journal 順が壊れ、
  既存の正常系が赤くなる。workload ごとの二相処理が正しい。
- **後始末で「admission が無い cell は未処理」と推測して再確定する** — admission decision を消す変異が
  推測経路で復元されて生存する。cell ごとに 1 回だけ処理し、欠落は検査で止める形へ改めた。
