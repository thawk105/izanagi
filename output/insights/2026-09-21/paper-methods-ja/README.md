# 本体論文 (日本語) 方法節と実装対応メモの改稿 (2026-09-21 版) — B-8 の方法を加え、K2 の stock 対照口と B-5 の状態記述を揃えた wave の記録

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- wave: `worktree-dev-wave-paper-methods-ja-b8` (背景 job 57c44f00、専用 handoff は repo 外の job dir)
- 起点 = 採用時点の local main: `36fb14a3d` (2026-09-21 20:45 JST に fresh worktree、開始 gate `check_wave_startup.py --mode fresh
  --external-handoff` rc=0、main との乖離 0)
- 成果物: [`methods.md`](methods.md) (方法節草稿、6 節) と [`implementation.md`](implementation.md) (実装対応メモ)。前稿
  `output/insights/2026-09-20/paper-methods-ja/` (worklog entry 1749、照合基準 `482f19b88`) の本文 2 file を複製し、下の §3 の
  箇所だけを書き換えた。前稿の `methods.md` / `implementation.md` の bytes は変えていない (sha256 を wave 開始時と記録時に照合、§6)。
  前稿 dir の `README.md` には冒頭に前方 pointer の節だけを足した。**実装面の差分 0** (docs-only)。
- 依頼の逐語 (dev-wave 引数): [`verbatim/request.md`](verbatim/request.md)。

## 0. この wave が主張すること・しないこと

- 主張する: 新稿の B-8 の方法 (発効束・runner v5・校正段・本走段・3 値判定の規則) が、B-8 の事前登録 v1 本文、D2175 / D2186 項 1 /
  D2190 / D2194 項 1 / D2202 の本文、結果稿 `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md`、発効記録
  `output/insights/2026-09-21/t2807-b8-effective/README.md` (entry 1791) に対応していること。K2 の同 job stock 対照口が D2187
  (初投入の不成立) と D2205 (pair mode への修復、実機の再投入は未) を区別して書かれ、対照の成立を示唆しないこと。B-5 が
  D2200 項 1 の段階認可 (本走は未認可) として B-8 と分けて書かれていること。
- しない: 2026-09-20 以後の着地全般の総点検 (上の三つ以外の記述は前稿の照合 `482f19b88` を継承し、再照合していない)。
  新しい測定・合成・判定。既存の certified 記録・事前登録・凍結物・論文ストーリーの版・他の草稿の変更。英訳。gate・検査・台帳・
  一般化の追加。方法節への性能値・図の転載 (前稿の裁定を継承)。論文ストーリーの版や同日の草稿 (entry 1801) を出所にすること。

## 1. 段 1 brief (親、20:53 JST。逐語は [`verbatim/s1-brief.md`](verbatim/s1-brief.md) = 専用 handoff の段 1 節)

- 研究前進: 本体論文の方法節に B-8 (D2202 で `pass`) の方法を入れ、結果・要旨・限界の 3 草稿 (entry 1801) と方法節の不整合
  (方法節だけが B-8 を「未発効」と書く) を解消する。
- (P1) 採用時点 = `36fb14a3d`。三つの対象以外は前稿を継承し、再照合しないと本文冒頭と本 README に明記する。
- (P2) B-8 の方法は方法節 §3 (正しさ検証) の検証相の直後に置き、6 節構成を保つ。§6 の B-5 / B-8 の文は B-5 だけにして B-8 は §3 を指す。
- (P3) §2 の「新しい pin の main から旧系列を再開・再投入するのは行われていない」は、K2 の同 job pair の初投入 (pin 前進後の main、
  新しい campaign ID) と食い違って読めるので、K2 についてだけ揃え、他の系列は「前稿の照合時点の記述で、再照合していない」と限定する。
- 段 2・3 は省略 (軽量版。設計択一なし・正しさ防壁に触れない・受理集合不変)。段 6 は一次資料から事実を再抽出する docs-only なので
  `DW-C00` により read-only の独立レビュー 1 本 (2 レンズ) + 焦点再レビュー。
- 条件の再評価: `DW-O08` / `O09` / `O10` は非該当 (新規 path。前稿 dir を参照する test・pin・目録は `orchestrator` / `tools` / `hooks` /
  `output/s1-freeze` / `output/env` の grep で 0 件)、`O11` は削除なし、`O13` は gate の新設なし。

## 2. 稿の作り方

1. 入力: B-8 の結果稿 (全文)、発効記録 (全文)、B-8 事前登録 v1 の §0・§3.2・§4・§5・§6・§7・§10・§12、D2175 冒頭、D2186 項 1、
   D2190 全文、D2194 項 1・2、D2202 全文、D2187 全文、D2205 全文、D2200 項 1、D2172 項 4、D2206 の窓と収集 (B-5 / K2 の状態)、
   worklog entry 1746 / 1754 / 1755 / 1779 / 1790 / 1791 / 1795 / 1801 (archive の該当 file)、K2 pair の初投入 insight
   (`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` §0) と修復 insight (`output/insights/2026-09-21/t2795-pair-repair/README.md` §0)。
2. 実装アンカーの照合 (三つの対象の行だけ): pair mode は `orchestrator/campaign/loop.py` の `authorization_session` /
   `_AuthorizationSession` と、`_authorize_measurement` / `run_campaign` の keyword-only 引数、`p3_s4_loop.py` の `main` の
   pair mode 分岐 (`--run-iteration` と `--stock-control` の併用)、job body の `IZANAGI_S4_STOCK_CONTROL=1` の拒否条件を
   `36fb14a3d` で確かめた。B-8 の発効束 JSON・事前登録・template patch は repo 内の実在を確かめ、runner v5 は repo 外であることを
   発効記録 §1 と D2190 項 1 で確かめた。
3. 執筆: 前稿 2 file を複製し、methods §2 (K2 対照口の 2 段落と pin 前進の段落の末尾)、§3 (B-8 の 9 段落と判定の 3 項)、§6 (B-5 と
   B-8 の段落)、implementation の冒頭・正本の優先関係・表 2 行・読み分け 3 行・境界節・確認点を書き換えた。
4. 親の自己点検 (段 6 前): 相対リンクの解決 (README 以外 0 件不達)、本文中の repo 相対 path の実在 (不達は schema 名 4 件と前稿から
   継承した短縮表記 1 件だけ)、新稿の「未発効」「本稿の時点」「1 job も」の走査。

## 3. 前稿から変えた点

「型」は、前稿の記述が前稿の照合基準 `482f19b88` の時点で既に偽だったか、その後の着地で古くなったかを示す。

| 箇所 | 前稿の記述 | 新稿 | 根拠 | 型 |
|---|---|---|---|---|
| methods §3 (新設の段落群) | B-8 の方法は無い (§6 で「未発効」とだけ書く) | 登録と対象・定義、発効と発効束、runner v5、校正段、本走段、3 値判定、2026-09-21 の実施、限定 | 事前登録 §0 / §3.2 / §4.1 / §4.2 / §5 / §6.1〜§6.4 / §7 / §12、D2175、D2186 項 1、D2190 項 1〜5、D2194 項 1、D2202 項 1〜4、結果稿 §1〜§4、発効記録 §1〜§6 | 後の着地 (発効 commit `624c84986` は 2026-09-21 08:42 JST) |
| methods §2 (K2 対照口) | 「本稿の時点でこの口は実装済みであるが、1 job も投入していない」 | 修復前の 2 process 形の初投入 1 job と不成立 (D2187)、pair mode への修復 (D2205)、実機の再投入は未、同 job の stock 対照は未取得 | D2187、D2205、entry 1754 / 1795、両 insight §0 | 後の着地 (初投入は `482f19b88` より後の main `6a3e158` の submit-tree から。D2187 の main 着地は fold `7baf3f375`、2026-09-20 20:42 JST) |
| methods §2 (pin 前進の段落の末尾) | 「新しい pin の main からそれらを再開・再投入するには…整合が要り、本稿の時点では行われていない」 | 「前稿の照合時点ではいずれも行われておらず、本稿はその後を再照合していない」+ K2 の pair が前進後の main で新しい campaign として投入された | t2795-k2-pair-attempt README (campaign `p3-s4-loop-s4-autonomous-b24749ae` = 新 ID・新 policy epoch) | 表記の限定 ((P3)。旧巡の campaign の再開ではないので、前稿の文が偽だったとは主張しない) |
| methods §6 (B-5 / B-8) | 「B-5 と B-8 は…事前登録 v1 が作られたが、いずれも未発効」 | B-8 は発効し 3 値判定まで済んだ (§3 を指す)。B-5 は未発効、試走は完走 (主標本外)、D2200 項 1 は段階認可で本走は未認可 | D2194 項 1、D2202、D2158、D2172 項 4、entry 1779、D2200 項 1、D2206 | 前稿の照合時点では真。B-8 の発効、B-5 の試走の完走 (entry 1779)、D2200 は後の着地 |
| implementation 境界節 | 「B-5 と B-8 の事前登録 v1 は未発効で、対応する runner・生成器は実装されていない」 | B-8 は発効・判定済み (repo 外の runner v5)。B-5 は未発効、driver と部品は着地、試走は完走、本走は段階認可のみ | 同上、D2190 | 前稿の照合時点では真 (B-5 の driver の初出は `c41cfb09f` = 2026-09-20 20:34 JST、D2190 の main 着地は fold `7c0a1c63a` = 同 22:54 JST で、いずれも後) |
| implementation 表 | K2 対照口の行は「0 件 (結線のみ)」 | K2 行を pair mode のアンカーと初投入の不成立・修復後の実機投入 0 件へ更新。B-8 行を追加 | 上と同じ | 後の着地 |
| implementation 読み分け | — | B-8 の `pass`、K2 pair の初投入、pair mode の結合検査の緑の 3 行を追加 | 上と同じ | 追加 |
| methods §1 / §5、implementation の A-1 行・境界節の兄弟 wave の文 | 「本稿の時点で…」 | 「前稿の照合時点 (`482f19b88`) で…」(中身は再照合していない) | (P1) | 表記のみ。新稿の採用時点を指すと読めて偽になりうる文を、継承の範囲へ戻した |

## 5. 限界

- **継承部分の未再照合:** 三つの対象以外の記述は前稿の照合 `482f19b88` のままであり、その後の着地で古くなった記述を含みうる。
  本 wave の作業中に目にした例として、A-1 sized の attempt-0002 は認可 record 経由で投入され完走した (entry 1755)。新稿の methods §5 と
  implementation の A-1 行は、その事実を書かず「前稿の照合時点では投入 0 件」の表記に留めた。新 pin の main から旧系列を再開するための
  整合も 2026-09-21 に系列ごとに実測されている (entry 1790、D2201)。いずれも依頼が総点検を scope 外とした範囲なので本文は直していない。
- **B-8 の runner v5 は repo 外である。** 新稿は runner の挙動を D2190 と発効記録の記述から書き、runner の source を本 wave で読み直していない。
