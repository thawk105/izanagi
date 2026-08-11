# 段 4 裁定 — [T-139] 第 2 波 (dev-wave-t139-manifest-w2、2026-08-11)

**裁定: land 1 の 3 文書を承認可能水準へ直して返す。land はしない。land 2 (manifest + producer +
pilot) は本 wave では実装しない。**

段 3 のレンズ 2 本はともに **NO-GO** (A = blocker 11 / must-fix 4、B = blocker 8 / must-fix 9)。
段 2 プランも NO-GO。**親は下表のとおり裁定する (refuted 2 件、残りは real)。**

## 0. なぜ land しないのか — 承認済み裁定の前提を覆す未見の新事実 (`DW-S04`)

R1 (a) は「文書承認 fold を先に land する」という**順序**を認可した。その裁定の時点で未見だった
次の事実が、**承認対象そのものを承認不能にしている。**

| 新事実 | 実測 (親が独立に算出。両レンズも一致) |
|---|---|
| 凍結 core は較正義務を **2 箇所**に持つ | 221 行と **333 行** (`| a12 | weak null の型 I 誤りを較正する事前 simulation の仕様 |`、`a7852ad9…9952`)。221 行だけを置換すると core が「§7 = stress check、§14 = 較正」の二重状態になる。**草案 erratum-2 と `dfb821a5…678c` は承認可能でない** |
| Draft 2020-12 の検査実体が無い | この環境の `jsonschema` は 3.2.0 で `Draft202012Validator` を持たない。既存経路も Draft 7 |
| 受領証 schema は現文書から一意生成できない | `environment.attestations[]` / `dependency_pins[]` / `actual_runs[]` / `correctness_evidence[].run_scope` / `arms.*.toolchain.dynamic_deps[]` 等の exact key が未定義 |
| 草案が承認後に**自分の承認状態について偽を述べる** | 両草案の `approval_status: draft_unapproved`、「本書は承認されていない」。先例 (承認済み追補 A・erratum-1) には `approval_status` field が無い |
| 草案が**裁定外の受理拡大**を含む | `pre_performance_infra_failure` を marker 不在だけで成立させており、`a04` が post へ写して置換禁止とする attempt を予備置換可能にする |
| pilot が消費する 8 slot の identity が未凍結 | `a09` は slot 1〜13 の schedule を発行するが、pilot がどの 8 本かを定めない。結果を見て選べる |
| `a13` の予約と R1 の同一 land が**因果循環**する | 予約は pilot より前に canonical main へ、受領証は pilot の後に入る必要があり、land は tested tip を 1 度だけ ff/fold する |

**親は不採用にしない。**`DW-S04` に従い、直した文書とともに新事実付きのユーザー再裁定へ返す。
記録項目の確定はもともと D229 決定 (7) と事前登録 §11 段 A が定める**単独の裁定 gate** の対象であり、
R1 (a) が認可したのは land の順序であって、まだ存在しない schema blob の内容ではない。

## 1. 所見の裁定

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| N1 | 両草案が承認後に自己の承認状態について偽を述べる | A-1/A-2 + 親 | real・**採用**。`approval_status` を削除し先例の `authority: none` に揃える。歴史的記述 (「起草時点で `F_s` は存在しない」) は残してよい |
| N2 | RI-B1 前版条項の暗黙継承 | 段 2 / B-blocker / A-refuted | **一般論は refuted** (exact 三つ組による規範的取り込みは有効)。ただし**採用**: v2 は自己完結にし、旧 blob への規範的依存を持たせない。payload は旧 blob を `not_approved_as_record_items_root` と role 付きで名指しする |
| N3 | RI-B2 nested 閉包未完 + 内部矛盾 | 段 2 / A-3 / B | real・**採用**。全 nested を閉じる。矛盾 3 件を解消 — `binary_rehash` は **9 件** (3 arm × 3 点)、`malformed_reason` は malformed のとき**非 null 必須** (validator 再計算値と exact 一致)、`exclusivity.method` の enum を閉じる。`translation_units{}` は `patternProperties` + `additionalProperties:false` で閉じる (例外にしない) |
| N4 | RI-B3 `pre_performance_infra_failure` が `a04` より広い | 段 2 / A-4 / B | real・**採用**。`a04` 準拠へ狭める (性能 run の raw 痕跡または `a03` 不成立証拠があれば pre へ写せない) |
| N5 | RI-B4 `a13` が current tip の重複だけ | 段 2 / A-5 / B | real・**採用**。append-only 全履歴検査 (R3 (a)) と `operational_boundary` の逐語固定を要件へ書く |
| N6 | ER-B1 core 333 行に較正義務が残る | 段 2 / A-6 / B / 親 | real・**採用**。erratum-2 を **221 + 333 の 2 operation** へ。合成 = **`e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c`** (親実測、適用順不変、置換後 core に `較正` 0 件)。**承認済み追補 A は再発行しない** — 825 行の見出しは直後の本文が較正を否定しており legacy label である。**core の逐語を 2 箇所変える点はユーザー裁定へ返す** (Q-B が想定したのは §7 の 1 箇所) |
| N7 | SC-B1 schema 未存在 + dialect 未確定 | 段 2 / A-7 / B / 親 | real・**採用**。**Draft 7 を親の推奨とし、両 dialect で意味が同一の keyword だけを使う** (`definitions` + `#/definitions/...` の JSON pointer 参照、`$defs`・`unevaluated*`・`format` 依存を使わない)。dialect の確定はユーザー裁定へ返す (engine が受理集合を動かす択一のため) |
| N8 | pilot の 8 slot が未凍結 | A-8 | real・**採用**。`a09` の 1-origin・prefix balance (`⌈r/2⌉−⌊r/2⌋ ≤ 1` を任意の prefix `1..r` で満たす設計)・置換は同一 slot 再利用、の 3 点から **pilot = slot 1〜8 に exact 固定**する。**closure decision としてユーザー裁定へ明示的に返す** |
| N9 | `a09` schedule 表の canonical bytes が未定義 | B-blocker | real・**採用**。`schedule_sha256` の対象 bytes を逐語で定義する (validator がゼロから再導出して照合できる形) |
| N10 | land 2 の「台帳 → manifest」第 1 矢印が計画に無い | A-9 | real・**採用 (land 1 へ影響)**。承認 payload を**機械可読**な形で書き、resolver が `F_r:docs/decisions.md` から payload を読んで manifest と exact 一致を要求できるようにする。実装は land 2 |
| N11 | Git trust root が `PATH` 差し替えで迂回できる | A-10 | real・**scope 外 (land 2 必須要件)**。resolver の全 Git 呼出しを絶対 path + identity で固定する |
| N12 | R1×R3 の予約時系列循環 | 段 2 / A-11 / B | real・**ユーザー裁定へ**。レンズ B の (i) 案 (予約 JSONL を land 1 の fold へ同梱) が成立すれば循環は解ける。(ii) は同一 land 要件に反し、(iii) は R3 (b) で裁定と矛盾する |
| N13 | 1 wave 不可の証明 | 段 2 / B | 段 2 の「必ず不可」は **refuted** (session 上限と並列規則が未定義)。ただし **GO も証明できない**。land 2 の session 分割はユーザー裁定へ |
| N14 | symlink/TOCTOU 防止が land 2 の所有面に無い | A-13 | real・scope 外。dirfd walk + 各 component `O_NOFOLLOW` + 同一 fd の `fstat/hash/parse` を次 wave の必須要件に記録 |
| N15 | correctness anomaly の構造化還流契約が無い | A-14 | real・scope 外 (規律 3)。既存 verifier の trx/cycle/edge/reason 構造を受領証・試行台帳・次手へ渡す契約を次 wave の必須要件に記録 |
| N16 | `returncode` を使う否定検査が空振り | A-15 | real・**採用**。`admission_telemetry[]` に `returncode` を持たせない方針を維持し、**否定検査の列挙から `returncode` を外す** (実在 field だけを列挙する) |
| N17 | 変異の単一理由帰属が未証明、M26 が wave 前実コードと非同型 | B | real・scope 外 (land 2 の段 4 で再登録)。承認経路は `require_approved_addendum_a_fields` の固定集合であり caller-selectable でない |
| N18 | `a01` (B) の小計を 2340 と書いた箇所がある | B-must-fix | real・**報告のみ**。実算術は `180+1440+360+360+180+120 = 2640` で、同表本文は 2640。受理集合は phase 別 cap で決まるため変わらない。承認済み blob の算術誤記として package へ記録し、erratum の対象にはしない (scope 爆発を避ける) |
| N19 | 単独性確認は保証にならない (Exclusive submit OFF、foreign process 情報は diagnostics_only) | B-must-fix | real・**採用 (文書化)**。受領証は単独性の**生出力 pointer** だけを持ち boolean を持たない。「単独性を保証した」と書けないことを非保証節へ明記する |
| N20 | `a05` の再利用は既存 probe をそのまま使えない (probe は全 build `CCBENCH_TRACE=0`、compiler は `command -v`) | B-must-fix | real・scope 外 (land 2)。verification 割当てが 6 build の唯一の生成元である契約を次 wave の必須要件に記録 |
| N21 | pilot 1 本の E2E は成果物を変えない (`n_p = 8`) | B-must-fix | real・**採用**。pilot 1 本を「gate が効いた」証拠として報告しない旨を package へ書く |

**refuted は 2 件** (N2 の一般論、N13 の「必ず不可」)。親の (P1)〜(P6) のうち **(P2)・(P3)・(P6) は誤り**
として撤回し、(P1)・(P4) は維持、(P5) は「未確定」の表現のまま維持する。

## 2. プラン v2 — 本 wave の確定 scope

### 2.1 承認候補の文書 (親が単独で書く。branch `worktree-dev-wave-t139-manifest-land1`)

| 単位 | 内容 | 成果物影響 (`DW-G05`) |
|---|---|---|
| **D1 `record-items-v2.md`** | **自己完結**な受領証要件文書。前版の全受理条件を再掲し、Q-A 第三分岐 (`a04` 準拠)、全 nested の exact key 閉包、矛盾 3 件の解消、`a13` 全履歴要件、pilot slot 1〜8、schedule canonical bytes、否定検査の実在 field 化、非保証節を含む | 無いと 2 実装が同じ受領証を適格/拒否に分岐させ、適格 cluster 集合と certified 判定が実装依存になる |
| **D2 `erratum-core-s7-stresscheck-v2.md`** | 221 + 333 の 2 operation。固有検査を「要素数 == 2 / 各 `old_sha256` 一致 / core 中の `較正` 出現ちょうど 2 件かつ両方が operation 行 / 各 `new_text` は 1 行 / erratum-1 の locator {404, 424} と非重複 / 置換後 core に `較正` 0 件」へ更新。合成 `e0b0caea…8e0c` | 無いと core §7 の較正義務が未達のまま、保証していない型 I 誤り制御を保証したことになる |
| **D3 `receipt-schema-v1.json`** | D1 と exact 1:1 の機械可読 schema。Draft 7 (両 dialect 共通 keyword のみ)。全 object に `additionalProperties:false`、全必須 key に `required` | 無いと `PreregBinding` が固定できる schema digest が存在せず、pilot が永久に投入不可 |
| **D4 承認 decision fragment** | **機械可読 payload** (D262 を前向きに supersede、role 分離、`erratum_application_order`、`composed_sha256`、`operational_boundary` 逐語) | 無いと manifest が pin できる trust root が生まれず land 2 が着手不能 |
| **D5 `package.md` + worklog fragment + README + 逐語凍結** | 裁定 7 件をユーザーへ返す。逐語 (s1〜s4 + レンズ 2 本) を凍結 | — |

**D3 は Codex `role=author` が書く** (機械設定にあたるため。所在不問の実装面契約に従う)。D1・D2・D4・D5 は親が書く。

### 2.2 実装しない (land 2、次 wave 群)

承認 manifest / resolver / `PreregBinding` / `verify_prereg_receipt` / `a13` 台帳実装 /
submit_pilot / durable intent / PBS preflight / driver / collector / receipt writer /
iteration 毎 correctness verifier / certified consumer / 材料 report / 試行台帳 consumer。
**pilot は投入しない** (D264 の非 export が機械固定しており、本 wave はそれを緩めない)。

### 2.3 land しない

R1 (a) の land 1 は、承認対象の内容がユーザー裁定を経た後にだけ実行できる。
本 wave は branch を残して終える (第 1 波と同じ形)。**wave 3 の残作業は「ユーザー承認 → main 取り込み
→ 受入全走 → land 1」だけになるよう、blob と fragment を land 可能な形で置いておく。**

## 3. 変異事前登録 (`DW-M01`) — 免除とその根拠

**本 wave の diff には実行可能コード・テスト・gate が 1 行も無い** (docs と JSON data blob のみ)。
変異は「受理集合または fail-closed 挙動が期待方向へ変わる」ことをテストで観測して初めて kill と
数えられる (`DW-M03`) ため、観測面が存在しない。よって `DW-S04` の免除条件
「実装差分ゼロの『実装しない』裁定」に該当し、**変異 matrix は免除する。**

代わりに次を段 6 で行う: (i) 敵対レビュー 2 本を**凍結される文書と schema** へ当てる、
(ii) D1 と D3 の key 集合が exact 1:1 であることを親が機械照合する、
(iii) 3 文書の digest と合成 digest を親が再計算して payload と突き合わせる。

## 4. 受入の扱い

**land しないため受入全走は wave 3 の tip で行う** (第 1 波の引き継ぎ規則 3 と同じ)。
本 wave では、変更 path (`output/insights/…`、`docs/spool/…`) を読むテストを列挙し、
`check_docs.py`・`spool_fold.py --dry-run`・`check_ai_provenance.py` と当該 nodeid を実走して
worklog へ証拠を記録する (docs-only の要否判定の証拠を残す)。

## 5. ユーザー裁定へ返す (package の骨子)

1. **land 1 の 3 文書の内容承認** (D229 決定 (7) / §11 段 A の単独 gate)。
2. **core の逐語を 2 箇所変えてよいか** (N6。221 のみ → 221 + 333)。承認済み追補 A の a12 見出しは
   legacy label として据え置く案を添える。
3. **受領証 schema の dialect** (N7。Draft 7 推奨 / 2020-12 + 依存導入)。
4. **pilot slot = 1〜8 の closure** (N8)。
5. **`a13` 予約と R1 の因果循環の解** (N12。予約 entry を land 1 へ同梱する案が推奨)。
6. **land 2 の session 分割** (N13。1 land を保ったまま複数 session で同一 branch を継承する形)。
7. **scope 外 real の受け取り** (N11 / N14 / N15 / N17 / N20 を次 wave の必須要件として確認)。

## 6. 実行順序

`4 → 5 (D1・D2・D4・D5 は親、D3 は Codex) → 6 (敵対レビュー 2 本 + 親の機械照合) → 7 (記録) → 8 → 9 (land せず終端)`
