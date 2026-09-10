# 段 4 裁定 — [T-524] 実験単位を slot 組へ改める最小形

親が段 2 プランと段 3 の 2 レンズを real / refuted で裁定し、プラン v2 を確定する。

## 1. 所見の裁定

| # | 出所 | 所見 | 裁定 | 根拠 |
|---|---|---|---|---|
| 1 | A-1 | series key へ generation を入れると mixed-generation genesis が別 series として通り、受理集合が広がる | **real / 採用** | 受理集合の拡大は規律 2 とユーザー指示 (既存拒否分岐を弱めない) に直接抵触する。設計を変える |
| 2 | A-2 / B-5 | outer acceptance は既に 6 report・manifest exact・genesis initial・report↔terminal の合成で全 unit 消費を強制している。issuer 内の全列挙 helper は純増でない | **real / 採用** | 2 レンズが独立に同じ file:line へ到達した。F28 の「同じ入力を拒否する層が前後にある」型であり、変異を帰属できない |
| 3 | A-3 | generation は manifest の `prereg_commit` から一意に再導出でき、明示 field 単体は新しい意味束縛でない | **real / 部分採用** | 明示 field だけでは純増でないことを認める。ただし後述 4 と組で downstream 束縛の材料になる |
| 4 | A-8 / B-2 | outer receipt schema が attempt registry を参照せず、verifier は manifest / trial registry / lifecycle しか再検査しない。下流は predeclared receipt の全列挙と消費を独立検証できない | **real / 採用・本 wave の主目的へ格上げ** | D1269 の後半「下流が predeclared receipt の全列挙と消費を検査する」を字義どおり満たす唯一の場所。B が「削る対象ではなく最小要件」と明記した |
| 5 | A-4 / B-4 | `not-consumed` は `report_sha256=null` が必須で、acceptance は全 report の hash 一致を無条件に要求する。混在正例は到達不能 | **real / 採用** | 到達させるには既存 status / hash / report-count 契約を緩める必要がある。**規律 2 により緩めない。** 正例から `not-consumed` を外す |
| 6 | A-5 | schema 分岐が「current なら v2、でなければ v1」なので current を v3 にすると既存 v2 artifact を v1 として誤検査する | **real / 採用** | 読取用に残すと言った集合を実際に失う。schema ごとの明示 map にする |
| 7 | A-6 | classification receipt の generation を capability digest と照合する計画が無い | **real / 採用** | 参照の二義化。ただし 8 と併せ、field は receipt へ複製せず digest 由来に固定する形で閉じる |
| 8 | B-8 | 6 種の row 全部へ generation を複製するのは過剰。slot_id から genesis slot を解決でき、capability digest が slot 全体を束縛する | **real / 採用** | 受理集合を狭めず変更面だけ増える。最小形を超えない側へ倒す |
| 9 | B-3 | `create_attempt_registry_genesis` の production caller が 0 件。正式系列は現状 production から起動できない | **real / scope 外** | 既存の未配線であり本 wave が作った問題ではない。producer 新設は本題の実装を超える。裁定パッケージへ |
| 10 | B-1 / A-2 | 同一 repository の path 面・commit 面 best-of-N は変更前から閉じている | **real / 受容** | 純増はここではないと認める。純増は 4 (下流束縛) と 1 の反対側 (世代混在の拒否) にある |
| 11 | A / B 共通 | 独立 clone / repository を跨ぐ best-of-N は残る | **real / scope 外** | D1269 が全世代一般化を明示的に却下している。裁定パッケージへ |
| 12 | A / B 共通 | 「承認 artifact」を人間承認 authority と読むなら現行 8c 設計と衝突する | **real / scope 外** | 本 wave は「P/C で固定された事前登録 artifact」と読む。人間承認 authority は新設しない。裁定パッケージへ |
| 13 | B-7 | `test_attempt_registry_core_s8b_profile.py` が更新対象から落ちている | **real / 採用** | v2 genesis bytes と署名対称性を exact 比較している。焦点走にも含める |
| 14 | A-7 | 新しい空集合拒否は統合経路では既存 core が先に拒否するので production gate の発火証拠にならない | **real / 採用** | helper 単体の防御的テストとしてのみ残し、production gate の実績として説明しない |
| 15 | A / B 共通 | 親 brief の A3 root key 集合が不完全、A7 の「同一」が過大、A9 の一般化が誤り、DW-G05 の certified 即時影響が誤り | **real / 訂正** | 親の記述を訂正する。現行 receipt は常に non-certifying で certifying consumer は不在。成果物影響は「certified 選択の値」ではなく「下流へ渡る証拠の欠落」である |

**refuted はゼロ。** 2 レンズの所見はいずれも file:line で裏付けられ、親が現物で追認した。

## 2. プラン v1 の判定

**作り直し (A の判定に同意)。** ただし全面ではなく、重心を issuer 側から下流側へ移す。

## 3. プラン v2 (確定)

D1269 の 2 つの半分を、それぞれ**実際に効く層**へ置く。

### (a) 承認 artifact が全 slot と個数を固定する

- attempt registry genesis の slot へ `prereg_generation` を必須 field として足す (schema v3)。
- **series key は変更しない。** 代わりに **root 全体で generation が単一であること**を v3 の全 reader に要求する。
  混在 genesis は拒否する。これが所見 1 への対処であり、受理集合を広げずに狭める向きになる。
- `create_attempt_registry_genesis` は `prereg_generation` を必須引数に取り、全 slot の同名 field と
  exact 一致を要求する。slot 側への自動補完経路は作らない (D539: 対象側から導出しない)。
- `replicate_slot` は新設せず既存 `replicate_index` を保存名として使う。`slot_count` も新設せず、
  canonical `slots` 配列と `attempt_index==0` の件数が個数の唯一の正本である。
- **generation を 6 種の row へ複製しない** (所見 8)。capability digest に含めて束縛し、
  classification receipt には値を置かない (所見 7 をこの形で閉じる)。
- schema 分岐は「current なら v2」ではなく schema ごとの明示 map にする (所見 6)。

### (b) 下流が predeclared receipt の全列挙と消費を検査する

- outer acceptance receipt schema を v5 へ上げ、**attempt registry の path・prefix hash・
  slot projection (generation・全 unit・個数)** を receipt 本体へ束縛する。
- `verify_acceptance_receipt` が、その projection を現物の attempt registry と再照合し、
  **predeclared な全 unit に final terminal が 1 件ずつあること**を独立に検査する。
- 期待集合は genesis 側から作り、terminal 側から導出しない (D539)。期待集合が空なら拒否する。
- final terminal は `observed` / `terminal-failure` を数える。`retryable-failure` は中間として数えない。
  **`not-consumed` は正例から外す** (所見 5。既存 status / hash 契約を緩めないため)。
- 性能値・fitness を読む分岐は作らない。

### (c) 作らないもの

- issuer 内の全列挙 helper (所見 2。既存合成検査と重複し、変異を帰属できない)。
- production genesis producer (所見 9)。
- 全世代台帳・revocation・expiry・check registry・汎用 core への一般化。
- 人間承認 authority。
- `replicate_index>0` の受理拡大。

## 4. 変異事前登録 (DW-M01)

**F28 に従い、issuer 内 helper へは変異を登録しない。** 同じ入力を既存層が先に拒否するため
赤理由を 1 つに絞れない。実効 gate へ再照準した結果、登録する変異は次の 3 件である。

| M | 位置 | 無効化する述語 | 同じ入力を拒否する前後層 | 期待する赤 |
|---|---|---|---|---|
| M1 | v3 reader の root 単一 generation 検査 | generation 混在の拒否 | **無し** (v3 以前は field 自体が無く、series key も分けない) | 混在 genesis を受理してしまう負例が赤 |
| M2 | genesis 作成時の `prereg_generation` ↔ 全 slot exact 一致 | 引数と slot の不一致拒否 | **無し** (現行に generation field が無い) | 不一致 genesis を受理する負例が赤 |
| M3 | `verify_acceptance_receipt` の attempt registry 再照合と全 unit 消費検査 | 下流の全列挙・消費拒否 | **無し** (現行 verifier は attempt registry を一切参照しない。B-2 が 4 手順で経路を実証) | attempt registry 欠落・unit 欠落の receipt を verified にしてしまう負例が赤 |

受理集合を縮小する wave なので、**承認外の過剰拒否の正例**も登録する。

| M | 過剰拒否の正例 |
|---|---|
| P1 | 単一 generation・6 unit 全消費・`observed` と `terminal-failure` 混在の正規 receipt が verified になること |
| P2 | `retryable-failure` の後に同 series の次 attempt が正常終端した形が受理されること |

## 5. 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **正式系列に production genesis producer が無い。** 現状 `create_attempt_registry_genesis` の
   caller は全てテストで、正式 run は out-of-band の Python 呼び出し無しには開始できない。
   これは別タスクとして起票すべき実在の欠落である。
2. **独立 clone / repository を跨ぐ best-of-N は残る。** 閉じるには全世代を一元管理する一般化が要り、
   D1269 が明示的に却下している。閉じるかどうかは新しい裁定が要る。
3. **`not-consumed` を最終消費として outer receipt へ運ぶか。** 運ぶなら既存の report-count・status・
   hash 契約の改訂が要る。本 wave は規律 2 により緩めなかった。
4. **「承認 artifact」を人間承認 authority と読むか。** 現行 8c は承認 record も active pointer も
   採らない設計で、receipt は approval authority 不在を必須にする。読み替えるなら発効設計の変更になる。

## 6. 親 brief の訂正

- A3 の root exact key 集合の記載は不完全だった (`schema_version` / `event` / `freeze_id` /
  `manifest_path` と v2 の chain field を落としていた)。
- A7 の「本 wave が狙う穴と同一」は過大。§7 の穴は未登録 run・別 run-root・report 前 crash を含む。
- A9 の「専用関数が不在」は文字列検索として正しいが、「全件保証が無い」への一般化は誤り。
- A1 は過大評価。genesis creator 自体は非空・slot ID 一意・attempt index 連続性だけを見る。
  manifest に対する完全性は後段 acceptance で初めて検査される。
- DW-G05 の成果物影響を訂正する。現行 receipt は常に non-certifying で certifying consumer は不在
  なので、certified 選択の値が今すぐ変わるわけではない。**放置時に変わるのは、下流へ渡る証拠から
  「事前に固定された全 slot を全部消費した」という事実が欠落したままになること**である。
- (P1)(P2) は反証された。(P3) は精密化のうえ一部不採用 (`not-consumed`)。(P4) は支持。
