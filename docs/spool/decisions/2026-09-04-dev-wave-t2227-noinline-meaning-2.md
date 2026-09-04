---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: dev-wave-t2227-noinline-meaning
seq: 2
---

## {{D:inert-request-contrast-value-branch-witness}}. 要求値が既定値と一致する枝選択 witness は対照値で識別する

**決定:** D1490 の compile-time 枝選択 witness を、要求値が既定値と一致する inert 要求
(`BACKOFF_NOINLINE` の要求 0・既定 0) に対しても発行する。観測は要求値 0 と対照値 1 の両方で行い、
値 1 → (選択 1, 完了 1)・値 0 → (0, 1) のときだけ green、同じなら非識別として red にする。
evidence の `default` slot は「既定値の観測、または要求値が既定値と一致するときは対照値の観測」と
定義し、field は足さない。この拡張は `BACKOFF_NOINLINE` に限り、既存 8 macro の
factory 条件 (要求 1・既定 0) と期待式は変えない。旧 `MeaningWitnessDeclaration` と CLI は
`BACKOFF_FIXED` 固定のまま (D1491)。

**理由:**
- D1569 (ユーザー裁定) は `BACKOFF_NOINLINE` の意味の節を D1490 の witness で確立し、未確立一覧が
  実際に縮む driver へ配線せよと命じた。配線先の A-2 は policy で要求値 0 (既定と同値) を要求する
  (`paper_story_a2_certification.v2.json`)。D1490 の字義どおり「要求値で (1,1)・既定値で (0,1)」を
  求めると、要求 0 の観測は両方とも値 0 で必ず同一になり、宣言しなければ未確立のまま、宣言すれば
  非識別で red になる。どちらも D1569 を満たさない。
- witness の主張範囲「所有 TU でその define の値が宣言した枝の選択を決めている」は、どちらの値を
  要求したかに依らない。観測する値の集合 {0, 1} も不変で、変わるのは要求値に課す制約だけである。
- 受理集合は狭まるだけである。unestablished (admit) が green (admit) か red (reject) になる。
  既存 8 macro には red / unestablished から green へ転じる入力がない。
- D1242 が却下したのは BACKOFF_FIXED のスカラー復号器を他 macro へ流用することであり、
  本決定は復号器を使わない枝選択 witness の要求値制約の緩和である。
- header 所有の指令 (`include/backoff.hh`) を所有 TU の文脈で観測するため、深い鏡像
  (全 directory 実体・file symlink) に計装 header を置き shadow 側の所有 TU を前処理する。
  祖先を symlink で鏡像化する従来形では `..` が実体側へ解決され計装が見えない (toy と実 fixture で
  実測)。

**却下した選択肢:**
- inert 要求を宣言せず unestablished のまま残す — D1569 の本題が直らない。
- 値 0 だけを観測して (0, 1) で green にする — 対照が無く恒真になる。規律 2 に反する。
- 対照値方式を全登録 macro へ広げる — 既存 8 macro の受理形を変える必要がなく、
  `test_compile_time_factory_rejects_nonpaired_values` が pin する契約を崩す。
- 依存 file で計装 header の実読を要求する検査を足す — 読まれなければ両観測 (0, 0) で既存の
  非識別判定が red にする。仮想リスク向けの新防壁であり scope 外。
- 宣言 object の発行元を capability で識別する (D1491 の「factory 以外から発行できない」を
  object 同一性で実装する) — 受理条件は factory の再導出と等値比較で既に factory 条件と一致し、
  受理集合は広がらない。新防壁であり scope 外として記録に留める。
