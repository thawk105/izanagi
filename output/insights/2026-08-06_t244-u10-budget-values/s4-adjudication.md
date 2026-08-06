# 段 4 裁定 — [T-244] U-10 値案起草

段 2 プラン (`s2-plan.md`)、段 3 レンズ A (正しさ境界) / レンズ B (整合・実効性) の所見を親が裁定する。
逐語は `/work/1/SFC/tanab/dev-wave-jobs/t244-u10-draft/` に置き、本節は結論だけを持つ。

**両レンズとも NO-GO を返した。**親はこれを受け入れる。ただし「値案を出さない」ではなく、
**成立する部分を確定し、成立しない部分を択一としてユーザーへ返す**形へプラン v2 を変更する。

## 1. 親自身の誤りの訂正

| 対象 | 裁定 | 訂正内容 |
|---|---|---|
| brief (P1) / parent-measured N6 | **誤り。撤回する** | floor の `rounds` と 8c V-3 の `R` は**同じ量** (P6 の independent validation replicate) である。`R_rounds` / `R_replicates` へ分ける案は二重計上を招く。実装の欄名が `rounds` なのが紛らわしいだけで、別軸なのは物理 `reps` (=2) と自動再測定 round 上限 (=3) の方である。根拠 = P6 s2-plan「全 32 mask の独立 validation を `R` replicate」、D166 決定 1 の `replicate_ordinal`。 |
| brief (P4) | **誤り。撤回する** | `R=2` は parser 下限ではない。floor の `rounds` 下限は 1、`2` は `batch_member_row_count_min` の下限である。親は別 field の下限を R の下限と読み違えた。 |
| brief (P5) | **誤り。撤回する** | no-refund は**予約受理後**にだけ効く。予約前の candidate 生成失敗・provider 失敗は現 FSM では課金されない。「全失敗を例外なく forfeit」は現物より強い主張だった。 |
| brief (P7) | **半分誤り。修正する** | 「新規 record が必要」は維持。「現行 `drive()` の戻り値から導出する」は撤回 — 戻り値に per-query evidence も constraint 正本も無い。**物理実行点で発行**し、戻り値は digest/ref だけを運ぶ形に改める。 |
| parent-measured N2 | **不正確。訂正する** | `15650` は literal ceiling であって実効 `K_codec` ではない。実 `OriginSealed` frame の直列化検査が別に走る。 |
| parent-measured N3 | **不完全。訂正する** | 実行検査は origin/head の 2 本だけではない。normal / tombstone / abandon の各 batch frame、class frame、authority 全 origin の共有 head 合算、authority bytes 8MiB も対象である。probe の grid 3 で被覆する。 |
| parent-measured N5 | **一般化しすぎ。訂正する** | 「1 origin = 1 generation = 1 drive」は未結線の現状を超えた一般化。現物は **workload ごとに 1 generation・1 drive** であり、origin はまだ存在しない。 |
| brief (P3) | **覆された。書き換える** | parser/reducer 単体なら成立する tuple は作れるが、**現行 8c が物理的完全性を保って到達する tuple は存在しない**。値案の位置づけを「批准すれば発火する値」から「発火に必要な前提を明示した条件付き値」へ変える。 |

## 2. 所見の real / refuted 裁定

### real として採用 (パッケージへ反映)

| ID | 内容 | 反映先 |
|---|---|---|
| A1-shape | 既裁定文の「半空間 32 点」は用語が不正確。5-bit universe は 32 点、各座標半空間は 16 点である。座標 cut の証明が 32 run を要するのは**両側 (bad-side / good-side) の全 32 mask を被覆する**ため。**数値 32 は変わらない。** | 値案に erratum として明記 |
| A1-IQ / B-03 | `Imax` は現行 ledger では**予約 batch 数**、既裁定の「追加 I = 32R」は **validation run 数**。`Imax` は上限であって 32R 回の予約を強制しない。`Bmin >= 2` のため 1 行 batch も作れず、run と iteration の 1:1 対応は現 schema で表現不能。 | **択一 1** |
| A2-floor | ledger は evidence digest を dereference しない。`candidate_min = 1` の下では、同一 wire・連番 replicate・同一 outcome・任意 digest の行だけで floor を満たせる。**物理実行 0 件でも certifiable terminal に到達しうる。** | **封じ手を択一 2 に、残余を blocking caveat に** |
| A2-slack | `Qmax = F` に置くと、tombstone / forfeit が 1 行でも出た時点で certifiable terminal へ永久に到達できない。 | 推奨 tuple に crash 余裕を持たせる根拠 |
| A3-evidence | 現行 `drive()` の必須戻り値に canonical な per-query evidence が無く、`outcome` だけからの後付け合成は verifier の構造化 anomaly を落とす (規律 3 違反)。 | **択一 4** |
| A5-K | `Kmax >= 1` は `OriginSealed` へ生の SHA-256 を exact set として公開するため、既裁定の 33 bit outcome 漏洩とは別に class fingerprint 面を開く。 | 択一 3 の caveat |
| A6-free | 予約より前の provider 呼出しは課金されず、invalid/failure ごとに引き直せる。 | **残余として明示** (下記 4 節) |
| B-01 / B-04 | 依頼の 14 項目のうち、authority の field として実在するのは **6 系統** (`Imax` / `Qmax` / `Kmax` / `Bmin` / `candidate_min` / floor tuple) だけ。残る 8 項目は現状 consumer を持たない規則である。 | **値表を 2 層に分ける** |
| B-02 | 表の欄が埋まっていても、`E_min` 未値・`Imax` の意味未決・V-2 schema 未提示で canonical bytes は生成できない。 | 択一化で解消 |
| B-05 / B-06 | 代理 WAL は YCSB-A の内側 drive とだけ shape が一致し、role 時間・B/C・再測定・結線を含まない。`32×` 外挿は上界でも分布でもなく、build 再利用 policy 次第で 70〜91 分と約 4 分に分岐する。 | **費用表に「外挿であり実測でない」と明記** |
| B-07 | 現行の許可経路では live 8c を投入できない。 | **R を実測で決められない理由として明記** |
| B-08 | 値の批准で D201 の 3 阻害要因は **0/3 件**しか解けない。 | **順序の所見としてユーザーへ返す (最重要)** |
| B-09 | 14 項目を独立に批准させると矛盾する組を作れる (`R=2` と floor `R=3` で `F > Qmax` など)。 | **単一 tuple として批准させる形に変える** |
| B-13 | 旧 active 較正は自己 attestation 不合格が実測済み、新較正は未活性。どちらも 8c の動作点と異なる。 | **較正を値の根拠に使わない**と明記 |

### refuted として却下 (追認)

| ID | 内容 |
|---|---|
| A1-32 | 「32 が別軸由来」の疑いは反証。8c の trigger-gating wire は 5 bit で mask は 0〜31、P6 も同じ 5 要因順序を使う。既裁定の下限式は 8c に対応する。 |
| A2-tomb | tombstone 行だけで floor を満たす攻撃は成立しない。tombstone は `sealed_queries` に加算されない (D198 の対策は有効)。 |
| A3-row | 「1 validation drive = 1 non-tombstone row、内部 `reps=2` と最大 3 remeasure round はその行の evidence 内訳」は規律 3 と矛盾しない。これらは verifier の反復ではなく verifier 後の性能測定である。rep ごとに行を作る案は floor の二重計上と停止 topology の漏洩を生む。 |
| B-14 | 2026-08-04 裁定と D205 は衝突しない。D205 は防御的堅牢化だけを見送るもので、科学的妥当性は削らない。**`Q >= 1 + 32R + E_min` を D205 を理由に下げてはならない。** |

## 3. プラン v2 — 成果物の形を変える

「14 個の literal を並べた表」ではなく、次の 6 部構成にする。

1. **層の分離** — authority field として実在する 6 系統と、consumer を持たない 8 規則を分けて示す。
   後者は「批准しても現状は発火しない」と明記する。
2. **既裁定からの導出** — `B0 = 1`、`q_round = 32`、`Q >= 1 + 32R + E_min` は 2026-08-04 の
   ユーザー裁定であり、本 wave はこれを動かさない。導出過程を示す。
3. **制約検算** — parser 制約の全列挙 (閉形式) と、codec feasibility の実走検算 (probe)。
4. **択一 5 件** — 値が一意に決まらない箇所を、推奨付きで返す。
5. **推奨どおりに批准した場合の完全な tuple** — 択一の推奨を採ったときの literal を 1 組示す。
   ユーザーが「推奨どおり」と答えれば値が確定する形にする。
6. **批准が達成しないこと** — D201 の 3 阻害要因、A2-floor、A6-free、B-07 を残余として明記する。

**scope 外として実装しないもの (ユーザーへ返す):** V-2 の result-evidence record の実装、
launch admission の binding 発行、32 mask producer、formal consumer、sanctioned 実行経路。
いずれも real だが、本 wave は docs のみである。

## 4. 変異事前登録 (DW-M01)

**本 wave は実装差分を持たない** (probe は repo 外の使い捨てで land しない)。
したがって**変異 matrix と受入全走は対象外**である。tracked file への変更は
`output/insights/` 配下の docs のみで、コード・テスト・機械設定を 1 行も変えない。
land 前に `git status` と `check_docs.py` で docs のみであることを確認する。

## 5. 親が段 5 で実測すること

- probe による codec feasibility の実走検算 (grid 1〜4)。
- probe 実行後に repo が clean のままであることの確認。
