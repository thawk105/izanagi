---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t244-p3-reservation-fsm
seq: 1
---

## {{D:origin-ledger-prequery-reservation}}. origin ledger の予算消費点を予約 event へ移す — 予約を必須の前段にし、放棄は返却せず forfeit として seal まで証明する

**決定:** origin ledger の event FSM へ `BatchReserved` と `BatchReservationAbandoned` を足し、
`Imax` / `Qmax` 検査と `iterations_used` / `queries_used` の加算を `BatchCommitted` 受理時から
**予約受理時**へ移す。相は 5 種から 6 種、event は 4 型から 6 型 (genesis を含めた行列では 7 入力) になる。

- 予約は**必須**である。`IDLE` から `BatchCommitted` を直接受理しない。optional にすると caller が
  予約を飛ばせて、予算束縛が名乗りだけになる。
- 予約後に候補が作られない行の終端は `BatchReservationAbandoned` とし、**commit 前にだけ**受理する。
  commit 済み batch の終端は従来どおり prepare → seal だけである。
- 放棄しても予算は**返却しない**。放棄分は `forfeited_iterations` / `forfeited_queries` へ計上し、
  `sealed_queries` にも `tombstoned_queries` にも入れない。`OriginSealed` の payload へ
  この 2 counter を足し、terminal から iteration / query の内訳を導出できるようにする。
- `forfeited_queries` は**予約した member 行数**であって物理 provider query 数ではない。
  D166 決定 5 の限定をそのまま継承する。
- `OriginSnapshot` に予約の binding (batch ID・iteration・cardinality・query 基点) を公開する。
  これが無いと、予約直後に落ちた caller は再起動後に matching commit も abandon も構成できず、
  origin が `BATCH_RESERVED` のまま永久に seal 不能になる。公開しても漏洩は増えない —
  4 値はすでに公開 event stream に平文で載っている。
- query partition を `queries_used == sealed + tombstoned + forfeited + pending` へ拡張し、
  iteration partition (`iterations_used == batch_count + forfeited_iterations + 予約中 1`) を新設して、
  genesis / 予約 / 放棄 / commit / prepare / seal / origin seal の**全受理枝**で検査する。

**schema ID・domain・runtime path の版は上げない。** 破壊的な意味変更ではあるが、
再解釈される既存 stream が存在しない — 追跡された runtime store は 1 件も無く、production 初期化は
明示禁止のままで、fixture store はテストごとに新規作成される。版を上げると、authority 側だけが
旧版に残って**同じ bytes の受理集合が版境界を跨いで分裂する**。それは避けるべき不整合である。

**予算 feasibility の包絡線が狭まる。** 1 batch あたりの frame 数が 3 から 4 になるため、
origin 上限 bytes の見積りが増え、64MiB の下で受理できる予算の組が狭くなる。これは受理集合の変更なので
境界テストへ literal で固定した。**予算値を決める裁定は、この新しい包絡線を前提にする必要がある。**
本番 authority は entry 0 件のままで、予算 feasibility 自体が走らないため影響を受けない
(変更後も parse できることを正例として固定した)。

**この決定が保証しないこと。**

- **候補生成より前**は保証しない。ledger は provider 呼出しを観測しないため、1 件の予約の下で
  provider を何回呼んだかを区別できない。束縛するのは commit できる member 行数と予算 counter だけである。
- 予約放棄の event があるだけでは、kill 後の生存性は閉じない。上記の公開 binding と、
  caller 側の再開規則が揃って初めて閉じる。
- production provisioning は解禁しない。本番 authority (`origins: []`) と production 初期化禁止は不変。

**却下した選択肢:**

- **予約を optional にする** — caller が飛ばせるため予算束縛が実効化しない。
- **caller の制御流だけを batch 先行にする** — 候補生成後・commit 直前に process を落として
  新しい run-root で引き直す無課金経路を塞げない。予算消費点が commit のままだからである。
- **event / head / state の schema を新世代へ分離する** — 再解釈される既存 stream が無い一方で、
  authority 側を旧版に残すと同じ bytes の受理集合が分裂する。分離の利得より不整合の害が大きい。
- **予約後に落ちた origin を自動で放棄扱いにする** — ledger が caller の意図を推定することになる。
  再起動した caller が明示的に commit か abandon を出す方が、無返却の会計と整合する。
- **放棄行を stock wire で埋めて commit 済みに見せる** — 実行していない候補を実行したと記録することになり、
  正しさゲートを内側から壊す。

## {{D:mutation-attribution-masked-by-earlier-layer}}. 公開経路の変異帰属は、手前の層が相 guard をマスクしうると前提して設計する

**決定:** FSM の相 guard を変異で裏取りするとき、公開 commit 経路だけで帰属を取らない。
公開経路には durable な中間レコードの射影があり、event 種別によっては**相 guard より先に**
その射影が拒否する。射影が先に落とす event については、reducer を直接呼ぶ経路でも
相 guard の拒否を別に固定する。

**理由:**

- 本 wave の実測で、予約中の batch seal は相 guard ではなく中間レコード射影の前提検査で拒否された。
  拒否集合は正しいが、**相 guard を実装から削除しても同じ node が同じ層で赤くなる**ため、
  その node は相 guard の存在を証明していない。帰属が成立しないまま「変異で裏取りした」と
  記録すると、台帳が実際より強い保証を主張することになる。
- 同じマスクは他の event には効かない。予約 / 放棄 / commit / origin seal は射影の対象条件を
  満たさずに reducer へ到達する。したがって「公開経路は常にマスクする」でも
  「常にしない」でもなく、**event ごとに確かめるべき**性質である。

**却下した選択肢:**

- **射影より相 guard を先に走らせるよう実装を並べ替える** — 射影の前提検査は、成立しない状態から
  射影を組み立てないための防壁であり、順序を入れ替えると別の穴が開く。
- **拒否が起きれば層を問わず緑とする** — それは受理集合だけを見る検査であり、
  どの防壁が効いているかを失う。防壁を 1 枚外しても気づけなくなる。

**一般化の射程:** 独立 2 例が揃っていないため族全体への制度化はしない。本 wave の方法として記録する。
