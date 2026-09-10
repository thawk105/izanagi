# [T-2067] 段 4 裁定 — floor 使用測定の事前登録・決定的選択規則

裁定者: 親 (claude)。基準 commit: `6ee1f1413` (main `164e2c355` 取り込み済み、実装面差分 0)。

## 0. 裁定の要になった一次資料

- D1243 (実装すべき規則)、D1241 (実装まで non-certifying 上限)、D1124 / D1125 (観測回数を強制しない)、
  D893 (一回性台帳の失敗)、D95 (実装面は Codex author)、規律 2、規律 7、D1245。
- T-2044 監査 `output/insights/2026-08-28_t2044-holdout-selection-audit/README.md`。
- **D1124 の逐語が本裁定の分岐点である。** 撤廃された機構の実害は
  「途中死した床値 run が 12 cell 全部の key を焼き、床値実測が 5 日完全停止した」ことであり、
  ユーザーは「落ちたら測り直す。復旧に専用機構を要求しない」と裁定している。
  **可用性を人質に取る選択規則は、この裁定の再発である。**

## 1. 規則の確定 (P1 の裁定)

**採用: `earliest-eligible-official-run-id/v1`。** 同一 `(env_tag, proto8)` namespace の official
floor result のうち、path の起動時刻 `<TS>` が最小の**適格**な run を強い主張に使う。

段 2 案 A を採るが、**適格集合の決め方を差し替える**。

### 1a. 「適格」の権威は自己申告ではなく導出 bit (sol の real 所見を採用)

段 2 案は earlier result の `eligible_for_refreeze` を**自己申告のまま**読んで集合から外していた。
これは選ばれなかった run の 1 field を後から書き換えるだけで required run を動かせる。**採用不可。**

代わりに、既存機構をそのまま使う。

- 除外の権威は `s8b_holdout_admission.py:6164` が共有 admission 台帳から**再導出**する
  `derived_eligible_for_refreeze` とする。`s8b_floor_stats.py:1069-1073` は既に
  reported と derived の不一致を検出する。この 2 つが既存の実在機構である。
- earlier run は **derived bit が False のときだけ**競合集合から外す。
- earlier run の `protocol_sha256` を**内容から読んで**除外してはならない。namespace の絞り込みは
  path の `proto8` だけで行う。`proto8` 衝突は過剰包含 (= 拒否側) に倒れるので安全側である。
  sol の「full hash 一致を選択集合に使う」案は、内容を読む分だけ自己申告面を増やすので不採用。

### 1b. 「最も早い result.json をそのまま必須にする」案は却下 (D1124 の再発)

親は一度この単純化を検討したが、**却下する**。`_derive_refreeze_eligibility`
(`s8b_floor_campaign.py:6889-6902`) は `official AND resume_dir is None AND 非既定 seam なし` を
適格とする。すなわち **resume した run は official path に result.json を書きつつ適格ではない**。
resume は D1124 が守った途中死からの復旧経路そのものであり、これを競合として数えると
「1 回落ちたらその protocol では二度と強い主張ができない」という D1124 が撤廃した停止構造が
artifact 側で復活する。**却下理由はこれ一点で十分である。**

なお、途中死そのものは D1124 の記述どおり成果物を残さないため、result.json 不在として自然に
競合集合から外れる。

### 1c. 導出できない earlier run は fail-closed

admission evidence が欠落・破損して derived bit を導出できない earlier run は
`floor-selection-eligibility-underivable` で拒否する。これは攻撃者が作りたい状態そのものであり、
かつ official namespace の正当な artifact なら導出できるはずの状態である。
**残余の可用性費用**: 破損した earlier official artifact 1 件で、その protocol の
強い主張が止まる。1b と違い、これは復旧経路 (resume) を塞がないので D1124 の再発ではない。
費用は insight に明記する。

## 2. 起動時刻の意味を閉じる (sol の real 所見を採用、既存機構の再利用)

**sol の指摘は親が現物で確認した real である。** candidate 経路は `launch_certificate.json` の
中身を一切検証しない (`s8b_holdout_freeze.py:1360` は path 文法の `parse_official_run_path` しか
import しない)。既存 fixture は certificate に `b"{}"` を書いている
(`s8b_v2_freeze_fixture.py:461`)。したがって現状の `<TS>` は**ただの名前**であり、
これを検査せずに「最小 run_id を使う」規則だけを入れても、規則は装飾にとどまる。

**採用**: candidate 境界で selected run の launch certificate を検証し、
`cert.started_utc` と path の `<TS>` の秒一致を要求する。

これは新機構ではない。同じ束縛は `s8b_ratified_freeze.py:179` の
`("official-path.run_id.ts", "cert.started_utc(second)")` として既に宣言され、
full launch validation (`:3281-3334`) で実際に強制されている。**その述語を candidate へ再利用する。**
sol の代案 (「主張を下げる」) は不採用 — 既存機構の再利用で閉じられるものを主張の切り下げで
処理するのは D1243 の「既存機構の再利用と局所修正」に反する。

**残余**: certificate を後から整合的に再構成する攻撃は閉じない (sol の real 所見)。
これは 5 節の残余として記録し、D1241 の上限維持理由に含める。

## 3. 検査を置く層 (P2 の裁定、luna の過剰実装摘出を部分採用)

| 層 | 置く検査 | 裁定 |
|---|---|---|
| candidate (`build_v2_g1_candidate`、`_validate_floor_inputs` 直後) | 選択 identity + 起動証明書/path TS 束縛 | **採用** |
| loader (`_verify_generation_semantics`) | **投影 equality のみ** | **採用 (限定)** |
| `_launch_validate` (LaunchValidatedFreeze 分岐のみ) | 選択 identity | **採用** |
| loader での選択 identity | — | **不採用** |
| frozen generator blob の版文字列 exact 1 回 scan | — | **不採用** |
| namespace 全体の H/worktree exact 一致 | — | **不採用** |

### 3a. loader に選択 identity を置かない (luna の historical 所見を採用)

`load_ratified_freeze` から `_verify_generation_semantics` を呼ぶ経路には current/historical の
区別が無い (`s8b_ratified_freeze.py:1366`)。一方 `_validate_floor_inputs` は current build admission
policy を無条件で使う (`s8b_holdout_freeze.py:1473`)。loader に選択検査を入れると、
`reverify_published_freeze` が `expected_policy=None` を選ぶ前に current policy で落ちる。
これは規律 7 と D1245 (歴史閲覧を拒否理由にしない) に反する。**loader は H-pure に保つ。**

代わりに `_launch_validate` の **LaunchValidatedFreeze 分岐だけ**に選択 identity を置く
(`s8b_ratified_freeze.py:3195` の既存分岐を使う)。`ReverifiedFreeze` (historical) には課さない —
過去の g1 は規則制定前の成果物であり、規律 7 により現行コードとの差だけを無効化理由にしない。

luna は `_launch_validate` 層を「過剰」としたが、それは loader が選択検査を持つ前提だった。
loader を H-pure にする以上、この層は過剰ではなく**唯一の選択強制点**である。

### 3b. loader の投影 equality は非恒真で必要

`generation.floor == project(floor_source blob の result.floors)` は既存 equality chain
(`s8b_ratified_freeze.py:147-182`) に存在しない (chain の末端は
`sha256(result.raw) == generation.floor_source.sha256`)。sol / luna とも real で一致。
**candidate 側の投影 equality は構造上恒真** (candidate の `floor` は `_validate_floor_inputs` の
戻り値そのもの) なので、candidate 側には置かない。

### 3c. 版文字列 scan は不採用 (luna の D1242 所見を採用)

frozen generator blob に版文字列が exact 1 回あることの確認は、未使用リテラルでも通り、
選択 equality を外しても通る。D1242 が否定した「文字列存在検査」の再発である。**削除。**

luna の代案 (generation document へ `floor_selection_rule` field を足して checker dispatch へ結合)
も**不採用**とする。単一 legal 値の field は dispatch を伴わなければ luna 自身の批判が当たり、
dispatch を伴えば「汎用の選択規則 framework」への第一歩になる。ユーザー引数が明示的に禁じている。
規則版は insight と decisions に記録し、artifact へは出さない。
規則を実装した generator の bytes は、既存の `generator` field
(`s8b_holdout_freeze.py:1731-1733`) が candidate へ自動記録する。

### 3d. namespace 全体 exact 一致は不採用 (luna の過剰拒否所見を採用)

selected より**後**の未追跡 run が 1 件あるだけで、selected を使う既存 consumer を止める。
成果物の値も参照も変わらないのに受理集合だけ狭めるので DW-G05 上は過剰。
**列挙対象は `<TS>` が selected より小さいものに限る。**

### 3e. candidate 側の列挙権威

candidate 側は worktree filesystem を列挙権威とする (選択対象自身がまだ HEAD に無い正常系がある)。
未追跡 earlier run の HEAD 不在は、既存の `_measurement_closure`
(`s8b_holdout_freeze.py:1640-1672`) が captured HEAD blob を要求することで既に閉じている。
**この既存機構に相乗りし、新しい commit barrier を作らない** (luna が D1124/D1125 との緊張を
指摘した namespace 全体 commit 強制は上記 3d で削除済み)。

## 4. 所見の real / refuted 一覧

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| 1 | candidate は launch certificate を検証しない | sol | **real・採用** (親が現物確認、2 節) |
| 2 | earlier の自己申告 field が集合 membership の権威になる | sol | **real・採用** (1a) |
| 3 | candidate 側の投影 equality は恒真 | sol | **real・採用** (3b) |
| 4 | 既存正例は result 1 件なので選択 equality は恒真、非恒真性は負例依存 | sol | **real・採用** (6 節) |
| 5 | 壊れた earlier の fail-closed は可用性人質 | sol | **real・限定採用** (1c、費用を明記) |
| 6 | loader へ current policy を持ち込むと historical が壊れる | luna | **real・採用** (3a) |
| 7 | 版文字列 exact 1 回は意味を証明しない | luna | **real・採用** (3c) |
| 8 | namespace 全体 exact 一致は過剰拒否 | luna | **real・採用** (3d) |
| 9 | `_launch_validate` 層は過剰 | luna | **refuted** — loader を H-pure にする裁定の下では唯一の強制点 (3a) |
| 10 | fixture の `floor` 追随は緩和でなく正規形修正 | luna | **real・採用**。ただし期待値は test-local な独立投影で作り、production helper を oracle にしない |
| 11 | 削除された earlier run は閉じられない | sol / luna | **real・scope 外** (5 節) |
| 12 | g2 以降が未被覆 | luna | **real・scope 外** (5 節) |
| 13 | s8c production final claim の配線 0 件 | sol | **real・scope 外**、本 wave の対象ではない |
| 14 | 通常 candidate の複数 run と `{G}` introduction 契約の矛盾 | luna | **refuted (本 wave の設計では発生しない)** — 本裁定の正常系は「最初の適格 run を選ぶ」であり、selected より早い非 selected artifact を先に HEAD へ入れる運用を要求しない |
| 15 | main が `164e2c355` へ進んだ | sol | **real・処理済み** (`6ee1f1413` で取り込み) |
| 16 | 親 brief の「稼働 wave は 2 件だけ」の一般化は未確認 | luna | **real・nit** — 名指した 2 worktree との重複 0 は実測。全稼働集合の完全性は主張しない |

`refuted`: 「run_id が値より先に決まらない」という一般否定。正規 producer 内では
`started_at` から run_id・certificate が測定前に作られる (`s8b_floor_campaign.py:7157,7267`、
luna が確認)。閉じないのは**再構成攻撃**であって、正規経路の時刻先行ではない。

## 5. scope 外・ユーザー裁定へ返す項目

本 wave では実装しない。insight と worklog に裁定パッケージとして残す。

1. **削除された earlier official run を集合へ戻す authority。** 台帳・署名を禁じた条件下では、
   値を見た後に earlier A を削除してから g1 を作る経路は閉じない。
2. **g2 以降の選択・投影。** `_launch_validate` は generation 1 だけを受理する一方、
   loader と s8c は g2 を受理する。g2 以降を non-certifying のままにするか、同じ規則を課すか。
3. **load-only consumer への選択強制。** historical 経路と両立しないため loader は投影のみとした。
   `verify_floor_bytes` 経由の s8c publish metadata は選択規則を強制しない。
4. **launch certificate の実時間性。** 整合する certificate/journal/admission を再構成する攻撃。
5. **s8c official table の production final claim 配線** (公開関数の production callsite 0)。

## 6. D1241 の扱い

**維持する。** 本 wave が landed しても advisory / non-certifying 上限は解除しない。
sol / luna が独立に同じ結論に達し、親も同意する。

本 wave の land 後に**追加で安全に主張できるのは次だけ**である。

- 同一 `(env_tag, proto8)` namespace で、admission 台帳から導出した適格性が真である
  earlier official run が存在するとき、それ以外を g1 candidate へ渡すと拒否される。
- selected run の path 起動時刻は、その run の launch certificate の `started_utc` と秒一致する。
- g1 の `generation.floor` は、記録された `floor_source` blob の `floors` 投影と一致する。

**解除できない残余**: 5 節の 5 項目すべて。

## 7. 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」ことを author/fix 段で
コードで確認し、確認できないものは登録せず実効 gate へ再照準する。
parametrize id は ASCII のみ。

| id | 変異 | KILL する負例 | 単一理由性 |
|---|---|---|---|
| `min-to-max` | 選択規則の `min` を `max` へ | 適格 A/B、selected=B | 前後層なし |
| `drop-candidate-selection` | candidate の選択検査を削除 | 同上 | candidate だけを呼ぶ node に限定 |
| `drop-launch-selection` | `_launch_validate` の選択検査を削除 | 直接組んだ g1 (B) を launch validate | loader は選択を見ない |
| `drop-loader-projection` | loader の投影 equality を削除 | `floor_source=A`、`floor=project(B)` の g1 | 既存 chain に辺なし |
| `use-reported-eligible` | derived bit を reported bit へ差し替え | earlier A の reported を False、derived を True にした fixture | 1a の核。既存 chain は candidate 経路でこの earlier を読まない |
| `drop-cert-time-binding` | `cert.started_utc` と path `<TS>` の秒一致を削除 | cert 時刻が directory 名と食い違う selected | candidate では他に cert を読む層が無い |
| `underivable-to-skip` | 導出不能 earlier を fail-closed から `continue` へ | admission evidence を壊した earlier A | baseline reject / mutant accept |
| `historical-policy-leak` | 選択検査を `ReverifiedFreeze` 分岐にも適用 | historical reverify の既存テスト | 3a の核 |

**正例 (承認外の過剰拒否を検出する)**: 受理集合を縮小する wave なので DW-M01 に従い登録する。

- `positive-single-run`: official run が 1 件だけの既存 fixture 経路が通り続ける。
- `positive-resumed-earlier`: derived 適格性が False の earlier run (resume 由来) が存在しても、
  later の適格 run から candidate を作れる。**これが 1b の却下理由を機械で守る正例である。**

luna が除外を勧めた `drop-launch-check` (契約外の手作り `RatifiedFreeze`)、
`drop-rule-version-pin` (版文字列)、および mask される `skip-untracked-results` /
`ignore-enumeration-shift` は**登録しない**。段 2 案の `trust-reported-eligible` は
`use-reported-eligible` / `underivable-to-skip` の 2 件へ再照準した。

## 8. plan v2 (実装子への指示要約)

1. `s8b_holdout_freeze.py`
   - private な official run 列挙器を追加。selected の path から `(env_tag, proto8)` を取り、
     `<TS>` が selected 未満の `<TS>-<proto8>/result.json` だけを worktree から nofollow で列挙する。
   - 各 earlier について admission 台帳から derived 適格性を導出し、True なら競合として拒否、
     導出不能なら fail-closed。内容から `protocol_sha256` を読んで除外しない。
   - selected の launch certificate を検証し、`started_utc` と path `<TS>` の秒一致を要求する。
     `s8b_ratified_freeze.py:3281-3334` と同じ述語を共有 helper 化して再利用する
     (公開 API 面は増やさない)。
   - `_validate_floor_inputs` の既存 gate 順序と戻り値の意味は変えない。投影は
     `_project_floor_for_freeze()` として切り出し、批准側と共有する。
   - 検査は `build_v2_g1_candidate` の `_validate_floor_inputs` 直後、closure 構築と document 投影より前。
2. `s8b_ratified_freeze.py`
   - `_verify_generation_semantics` に投影 equality だけを追加する (H-pure、policy 不使用)。
   - `_launch_validate` の `LaunchValidatedFreeze` 分岐にだけ選択 identity を追加する。
     `ReverifiedFreeze` には課さない。
   - `EQUALITY_CHAIN_ADJACENCY` (`:147-182`) は変更しない。
3. fixture / test
   - `s8b_v2_freeze_fixture.py` の `launch_certificate.json` を実 certificate へ直す。
   - `test_s8b_ratified_freeze.py` / `test_s8b_ratified_verify.py` の g1 fixture の `floor` を
     **test-local な独立投影**で `result["floors"]` から構築する (production helper を oracle にしない)。
   - 7 節の負例・正例を実装する。
4. 禁止事項 (個別に列挙)
   - 既存の資格検査を 1 つも緩めない。skip / xfail / 期待値の反転・削除を使わない。
   - `output/s8b-freeze/floor_protocol.json` と `holdout_freeze.json` の bytes を変えない。
   - `_PROTOCOL_KEYS`、`_RESULT_KEYS`、`V2_TOP_LEVEL_KEYS`、`EQUALITY_CHAIN_ADJACENCY` を変えない。
   - 新しい公開 CLI・新しい artifact 種別・新しい schema version を作らない。
   - 署名・nonce・一回性台帳・予約番号・墓標を作らない。
   - docs を編集しない。commit しない。
