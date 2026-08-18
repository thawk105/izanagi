# 段 4 裁定 — [T-338] 投入 gate (2026-08-18 13:20 JST)

親 = Claude (dev-wave manager)。入力 = 段 2 プラン (NO-GO)、段 3 レンズ A (NO-GO、blocker 4 / must-fix 3)、
段 3 レンズ B (NO-GO、blocker 6)、親の独立実測 4 本。
裁定 inbox を段 4 直前に再走査した — wave 開始 (12:22) 後の新規は
`2026-08-18-t688-codex-quota-exhausted.md` (13:00) 1 件のみで、T-338 の authority に無関係。

## 1. 所見の real / refuted

### real (採用)

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| R1 | **(P2) は累積有意水準のリセットを許す。** 台帳を truncate / 削除して過去の使用を現在集合から外し、同じ `(family_root, ordinal)` を再作成すれば、現 tip の `k = 1` も初出 commit の祖先性も成立する | プラン、レンズ A、レンズ B が**独立に 3 本とも** | real。**(P2) を撤回**し §6.7 の 8 脚をすべて実装対象とする |
| R2 | 承認済み文書自身がこの穴を既知として逐語で記録している (「前版の現 tip 検査は過去行を削除して同じ `(family_root, ordinal)` を再利用した履歴を受理した」§0.2) | プラン | real。親が §0.2 を読まずに (P2) を書いた実測不足 |
| R3 | **(P1) の階級分けは誤り。** §6.7 / §6.10 / §7.1(14)(17) は A 級。B 級は §7.1(19) と conformance vector index の digest pin の 2 件のみ | プラン (全 63 件を独立分類)、レンズ B | real。**(P1) を撤回**し全 63 制約を実装対象とする |
| R4 | **`read_regular_file_with_identity` は §6.10 を満たさない。** 承認済み要件は「path の各 component を `O_NOFOLLOW` で辿る」だが実装 (`artifacts.py:89`) は最終 component だけ | レンズ A | real。**親が直接照合して確認**。component 走査は `_mkdir_parents` (`:360-375`、書込経路) にしか無い |
| R5 | **`load_json_strict` は流用できない。** duplicate key 拒否に加え canonical bytes と末尾 LF を要求する (`:553`) が、承認済み T-139 契約が canonical bytes を要求するのは `schedule_table` (§6.6) / `argv_raw` / a13 JSONL 行 (§6.7 脚 5) だけで受領証本体には無い | レンズ A | real。**親が全文検索で確認** (`grep -n canonical` の 11 hit を全件確認)。流用すると受理集合を承認なしに狭める |
| R6 | **(P4)「gate 完成」は名乗れない。** §7 は §6 と §7.1 の全項目を semantic validator の必須責務とする | プラン、レンズ A、レンズ B | real。**(P4) を撤回** |
| R7 | **6 層 (producer / resolver / validator / selector / 材料 report / 試行台帳 sink) が未列挙で consumer 0 件** | レンズ B | real。未結線 leaf は D147 決定 (3) / D163 決定 (1) / D500 が却下した型 |
| R8 | **`series_id` / `parent_series_id` の authority と intent discovery の閉集合が未解決**で、これが無いと §6.1 の「durable submission intent の全 attempt を exact 被覆」が実装不能 | プラン、レンズ A、レンズ B | real |
| R9 | **approval manifest の exact grammar・固定 path・発見方法が未定義。** D282 は照合する意味集合を定めるが manifest 自身の exact object schema は定めない | プラン、レンズ B | real |
| R10 | **`submit_pilot` の成功契約が未定義。** qsub まで到達すれば D292 違反、一行 deny なら D264 の恒真 deny stub 却下に触れる | プラン、レンズ A、レンズ B | real |
| R11 | **Q2 (D229 決定 (8) の必須 kill 3 件の帰属段) が未裁定**で、「gate 完成」の定義が定まらない。D500 が明示的にユーザー裁定へ返した項目 | レンズ A、レンズ B | real。親 brief の「Q2 は producer 段でないため非閂」は誤り — 本 wave は kill 2 件目が要求する全履歴 validator を作る wave なので直接の受入条件 |

### refuted (不採用)

| # | 所見 | 出所 | 裁定と根拠 |
|---|---|---|---|
| F1 | 「(P3) は CMakeCache の再読脚を落とし 3 者一致を 2 者一致へ弱める」 | レンズ A [blocker] | **refuted。** §6.3 の逐語自身が第 3 脚を「`cmake_cache` の申告値 (`CMakeCache.txt` 由来)」と**定義しており、raw `CMakeCache.txt` の再読を要求していない**。承認済み §0 は「producer が申告した派生値は、受理集合を狭める方向にだけ使う。不一致を拒否理由にし、一致は受理の正の根拠にしない」と定めており、(P3) の形をそのまま承認している (段 2 プランが同逐語を独立に引いた)。レンズ A の反例 (実 cache = 1、configure / compile command / 申告値 = 0) は、**承認済み schema に raw CMakeCache pointer が 0 件である以上どの実装でも検出できず**、(P3) と承認済み契約の差ではない。schema 自身の限界であり保証境界へ書く事項 |
| F2 | 「§8 の予定テストは第 3 脚の欠落を検出しない」 | レンズ A [blocker] | **部分 refuted。** F1 により「第 3 脚 = raw 再読」という前提が不成立。ただし「不一致検査が consumer でなく semantic helper 直呼びである」という指摘は real で、否定検査は consumer 経路で書くこととし、実装時の要件へ移す |

## 2. 撤回する親の provisional 裁定

**(P1) 撤回** — 階級分けによる切り出しは成立しない。B 級は 2 件のみで、いずれも安価。
**(P2) 撤回** — 述語を保存しない。§6.7 は 8 脚すべて実装する。
**(P4) 撤回** — 全 63 制約 + 6 層結線 + 4 名前 export を同時に満たしたときだけ「gate 完成」を名乗る。
**(P3) 採用** — 上記 F1 のとおり。**これは本 wave の主要な前進である** (下記 4 節)。

## 3. 本 wave は実装しない (4 → 7 → 8 → 9)

**理由 (実測に基づく):**

1. **裁定が認可した「切り直し」に、承認済み受理述語を弱めない形が存在しない。**
   親が用意した 2 つの切り口 (P1)(P2) を、独立した 3 本の検証子がすべて
   「承認済み admission 要件の緩和」と判定した。command の指示は
   「規律 2 を緩める方向の変更は採らない」であり、この 2 案はその方向である。
   全 63 制約の独立分類で D320 の見送り対象と判定されたのは 2 件だけで、
   いずれも安価 (manifest への sha256 1 field と既 land pin の読取 1 行) なので、
   切っても規模は動かない。**「階級で切る」戦略は実測で死んだ。**

2. **措置後の規模は D205 / D220 の水準を大きく超えたままである。**
   独立 3 見積り = 親 1,650〜3,450 (過小と判定された)、段 2 プラン 2,570〜3,740、
   レンズ B 3,550〜6,200 (6 層接続込み)。いずれも tests を含まない。
   repo 実測の test/production 比 2.18 を掛けると総計 8,000〜19,700 行。
   D220 が D205 のプロトタイプ基準に照らして過大と判定したのは production 645〜816 行であり、
   本件は下限で 3.2 倍、上限で 7.6 倍。

3. **Q2 が未裁定で「gate 完成」の定義が定まらない。** D500 は
   「どの段の受入条件に置くかはユーザー裁定へ返す」と明記し、本 wave 開始時点で未回答である。
   本 wave は必須 kill 2 件目が要求する全履歴 validator を作る wave なので、Q2 は直接の受入条件。

4. **D264 が部分 land を禁じる。** 4 名前は gate 完成と同じ commit でだけ export でき、
   恒真 deny stub も台帳だけの半実装も名指しで却下されている。
   R7 のとおり本 wave が land しうる範囲には consumer が 0 件で、未結線 leaf の型になる。

**`DW-S04` の定めどおり、親は承認済み裁定 (Q1 = 択 (a)) を不採用にしない。**
裁定時に未見だった上記の事実を添えて、ユーザー再裁定へ返す。

**変異 matrix は免除** (`DW-S04`: 実装しないと裁定済みで実装差分ゼロの wave)。
**受入全走は免除されない** — 段 7 の記録前に実走して結果を worklog へ書く。

## 4. 本 wave が前へ進めたこと (D500 の状態からの差分)

1. **D500 が同定した閂 (T-139 V1 の D320 衝突) が消える見通しを実測で得た。**
   T-139 V1 は「イ (新 exact-byte approval payload) を作らずに B1 を閉じる案は
   (a) 受理集合が空 (b) 受理述語の弱化 の 2 つしかない」と実証したと書いていた。
   本 wave は**第 3 の経路**を実測した — CCBench の `cmake/Options.cmake:59-67` が
   `ADD_ANALYSIS` / `TRACE` を target_compile_definitions として吐くため、CMakeCache の 2 値は
   `compile_commands.json` に必ず現れ、凍結 schema はその `compile_commands` を
   `fileRecord` (path/size/sha256) として既に持っている。
   加えて承認済み §0 が「申告値は受理集合を狭める方向にだけ使う」を既に定めている。
   **B1 は凍結 bytes を 1 bit も変えずに閉じられる。**
2. **切り直しの可能性を実測で潰した。** 全 63 制約の独立階級分類は本 wave が初めて作った。
3. **D500 決定 (6) が次 wave の段 1 要件と定めた再利用先の棚卸しを完了した** (下記 5 節)。
   併せて親の「無料再利用」判定 2 件が誤りであることを実測で訂正した (R4 / R5)。
4. **6 単位の実装分割 (編集 path 素集合) を確定した。** 依存順 `1||2` → `3`,`4` → `5` → `6`。

## 5. 再利用先の確定 (D500 決定 (6) の次 wave 段 1 要件 = 本 wave が果たす)

- **採る:** `qualification/attempt_ledger.py:169-373` の hash 連鎖 replay と連番 create-only event を
  `preregistration/attempt_registry.py` へ移植する。`SeriesAttemptLedger` 自体は T-126 固定
  (64 桁 series ID、一初回 + 最大一 retry、`QualificationWriteCapability` 束縛) なので直接使わない。
- **採る:** `qualification/artifacts.py:125` `QualificationWriteCapability` の private-token 型
  opaque capability を `PreregBinding` の構造的先例とする。
- **採る:** `campaign/trial_registry.py:878` `assert_prereg_ancestor` (D234 (vi) が名指し) と
  `:895` `_blob_at_commit`。ただし S8c import graph を避けるため
  `blobref.py` の衛生化 Git 実行面を公開 helper へ抽出して使う。
- **採る (書き直しつき):** `atomic_publish.py:24` `publish_bytes`、
  `s8b_holdout_admission.py:681-703` の O_EXCL / 全量 write / fsync パターン。
- **採らない:** `qualification/series.py` (T-126 の SPRT / subject-reference 二者 FSM に固定)。
  `s8b_holdout_admission.py` の台帳本体 (同 file が `:10`, `:2273` で
  「`O_EXCL` は file が存在する間だけ効く。この耐性は保証範囲外」と明記)。
  `qualification/identity.py` (T-126 の script path / protocol に固定)。
- **新規実装が要る (親の「無料」判定の訂正):**
  - path の**各 component** を `O_NOFOLLOW` で辿る読取 (R4)。既存は最終 component のみ。
  - canonical bytes を強制しない duplicate-key 拒否 JSON reader (R5)。
    既存 `load_json_strict` は承認外の canonicality を強制する。

## 6. ユーザーへ返す設計択一

**Q-A (最重要). 投入 gate に production 2,570〜6,200 行 (tests 込みで概ね 3 倍) を投じるか。**

- **(a) 投じる。** 本 wave が確定した 6 単位分割を複数 wave に分けて実行し、
  4 名前 export は最終 wave の最終 commit だけで行う。
  **規律を 1 つも緩めない唯一の道。** ← 親の推奨は保留 (Q-A は費用の判断であり親が決める性質でない)
- **(b) RF study (T-139) 系列を畳む。** pilot / 本走を行わず受領証 gate も作らない。
  D292 の forbidden を恒久化する。**この場合 T-338 / T-139 系列の未了項目は一括で閉じる。**
- **(c) 承認済み受理述語を明示的に縮小する新 decision を起こす (= 自分たちで上げた証拠水準を下げる)。**
  本 wave の全 63 制約分類がそのまま候補表になる。落とす制約をユーザーが指定する。
  **止めているのは物理ではなく自分たちで課した証拠水準である** — この選択は正当であり、
  D320 が既に「bytes 級 provenance の新設・維持は既定で見送り」と同じ方向を定めている。

**Q-B. Q2 — D229 決定 (8) の必須 kill 3 件をどの段の受入条件に置くか (D500 が未裁定で返した項目)。**

- **(a) validator / consumer 段へ移す (producer 段では登録しない)。** ← 親の推奨 (T-338 package から不変)
- (b) producer 段の条件として残す。→ producer は 3 件が kill できるまで完成としない。

**Q-C. B1 の閉じ方 (本 wave の実測で新たに可能になった)。**

- **(a) (P3) を採る。** `cmake_cache` 申告値を**拒否専用**とし、受理は `compile_commands` 実体の
  再読と `configure_argv` の macro 一致で決める。**新 approval payload 不要・凍結 bytes 不変。**
  保証境界に「受領証が raw `CMakeCache.txt` を持たないため、configure 後に cache だけを編集した
  乖離は検出しない」と逐語で書く。← **親の推奨**
- (b) T-139 V1 の イ を作る (新 exact-byte approval payload で schema に `cmake_cache_raw`
  fileRecord を足す)。→ D320 の既定に反するため別途承認が要る。

## 7. 不変条件の確認 (本 wave 終了時点)

- `pilot_submission = forbidden` / `main_submission = forbidden` は **1 bit も動いていない**
  (`orchestrator/publication/report.py:214-231` を段 3 レンズ A が確認)。
- D264 の 4 名前非 export は維持 (`preregistration/__init__.py` の `__all__` は 10 名前、
  `test_module_exports_no_admission_api` が生きている)。
- 凍結 bytes は不変。実装差分ゼロ。
- certified 選択の値、材料レポート、proof chain、既存 gate、受理集合はいずれも不変。
