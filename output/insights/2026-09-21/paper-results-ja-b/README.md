# 本体論文 (日本語) の結果・考察草稿 2026-09-21b 版 (同日第 2 版) — B-8 の 3 値判定 `pass` を反映し、同じ wave で要旨・結論と限界節も改めた (docs のみ、台帳 ID 未起票の執筆依頼)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 成果物: `results-discussion.md` (本 dir)。**同日の前稿 `output/insights/2026-09-21/paper-results-ja/results-discussion.md` (2026-09-21 版、worklog entry 1772) を
  supersede する。** 前稿の bytes は変えない (wave 開始時の sha256 `b593e70a…` を記録 commit 時にも照合する)。前稿 dir の `README.md` の冒頭に前方 pointer の節を足す
  (09-20 → 09-21 の先例と同じ)。
- 同じ wave の成果物: 要旨・結論の同日第 2 版 `output/insights/2026-09-21/paper-abstract-conclusion-ja-b/{abstract,conclusion,README}.md` (前稿 = 同 `paper-abstract-conclusion-ja/`)、
  限界節の 2026-09-21 版 `output/insights/2026-09-21/paper-intro-ja/{limitations,README}.md` (前稿 = `output/insights/2026-09-20/paper-intro-ja/limitations.md`、
  別表は同 README §2)。**wave の記録 (段 1 の実測・段 6 のレビューと裁定・検査) は本 README に集約する。**
- wave: `worktree-dev-wave-paper-b8-pass-ja` (背景 job、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-b8-pass-ja/`、依頼の逐語は同 dir の
  `request-verbatim.md`、段 1 brief は `s1-brief.md`)。
- 起点 local main = **採用時点 `d99c556df`** (2026-09-21 13:35 JST、worklog entry 1795 までの fold を含む。着手直前の local main から fresh worktree、
  開始 gate rc=0 = job dir `startup-gate.log`)。段 4 直前に main を再走査し前進 0。
- **新規の測定は 0 件。** 凍結物 (results 稿・版・claim-evidence・figures) と前稿本文の bytes は 1 byte も変えていない。実装面の差分 0 で変異 matrix は `DW-S04` により免除、
  受入全走は免除しない。
- 依頼の確定事項: 対象 3 組 (結果・考察 / 要旨・結論 / 限界節)、出所は B-8 の結果稿 `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md` と
  insight `output/insights/2026-09-21/t2807-b8-effective/README.md`、旧稿の bytes は不変で同日版の命名規則に従う新版、条件語 (30 枠、extime 10 s、8 反復 × 3 workload、
  対象が案 A) を要約で落とさない、英語稿なし、並走の論文ストーリー 21c 版 wave と同じ結果稿に書き方を揃える、本題の執筆だけ (gate・検査・台帳・一般化の追加は scope 外)。

---

## 1. 一行で

3 稿の前稿の骨格と本文を継承し、B-8 (最終候補の種を変えた長時間検証) を「未発効・未取得」から「発効した事前登録 v1 の下で、案 A に対する
本走 (独立 8 反復 × 3 workload・extime 10 s の 24 枠) と校正の完走 6 枠 (3 workload × extime 6 s / 10 s、各 1 回) からなる判定集合 30 枠の
すべてで anomaly 0、3 値判定 `pass`」へ移した。結果・考察稿は §6 を 6.1 (採用候補 2 genome の
検証相、案 B) と 6.2 (B-8、表 8b) に分けた。あわせて、新しい採用時点で前稿の記述を偽にしていた状態語だけを最小限に直した (§3)。

## 2. 段 1 の実測 (親、2026-09-21 14:04〜14:11 JST = 開始 gate の log の mtime と、brief 冒頭に記した当時の mtime、login node、読み取りだけ)

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| B-8 の main への着地 | 発効 commit `624c84986` (08:42 JST)、land 着地 tip `7bde4b60e` (10:58 JST)、fold `acd7cdb30` (11:03 JST、D2202 / entry 1791 を採番) | 3 稿の前稿の採用時点 (`285477c00` = 09-21 00:21 JST / `482f19b88` = 09-20 17:56 JST、commit 時刻) はいずれもこれより前 |
| B-8 の数値と限定 | 結果稿 §3.1〜§3.4 と §4 の限定 11 件、insight §5 / §6 | 表 8b と「言えること / 言えないこと」は結果稿 §3.3 / §4 の逐語・言い換えに限る |
| 論文ストーリー入口 | `docs/paper-story/README.md` の stale 注記 3 (B-8 の発効と判定、仕分け (2) は発効をもって「独立 process の自己シード」へ改まる、検証相は B-8 に数えない) | B-8 の語彙の照合先 (21c 版 wave も同じ出所) |
| 前稿の採用時点以後の着地の走査 | worklog entry 1771〜1795 (結果・考察 / 要旨・結論) と 1748〜1795 (限界節) の見出し、D2186 / D2194 / D2200 の項見出し | 前稿の記述を偽にするものだけを直す (下の表)。親の初稿は B-5 の試走完走 (entry 1779) を「本走は未認可を偽にしない」とだけ判定し、同じ項の「未実走」を見落とした (段 6 review A の所見 2 で下の表 #7 に追加) |
| 旧稿の path を読む機械 file | `*.py` / `*.json` / `*.sh` / `*.toml` / `*.yaml` の走査で診断 JSON 1 件 (`output/insights/2026-09-21/land-roundtrip-diagnosis/waves.json`、データとしての言及) だけ。sha pin 0 件 | 旧 path はそのまま残す |
| 同日版の命名 | 同日第 2 版の先例は insight dir `paper-story-20260921b` だけ (`output/README.md` は子名に日付を重ねない) | 同日第 2 版は `-b` 接尾 (`paper-results-ja-b/`、`paper-abstract-conclusion-ja-b/`)。限界節は日付が変わるので `2026-09-21/paper-intro-ja/` |

## 3. 前稿の記述を偽にしていた状態語 (最小限に直したもの。#5・#6 は B-8 の着地に付随する箇所)

| # | 稿・箇所 | 前稿の記述 | 本稿 | 根拠 (実施記録) |
|---|---|---|---|---|
| 1 | 結果 §12・結論 §7・限界 §5 | g1 の起動検査は既存の不整合 2 件で拒否 | 2 件は整合済み、live は ccbench pin 前進後の段階 4 (binary admission policy 不一致) で拒否。**型:** 3 稿の前稿とも、採用時点で原因の記述として既に不正確だった — 結果・結論の前稿 (`285477c00`) では D2184 が採番済み、限界節の前稿 (`482f19b88`) では D2184 の採番前の spool 断片 (`docs/spool/decisions/2026-09-20-dev-wave-t2304-pin-advance-1.md`、同 commit の tree の path で fold 後は無い) と pin 前進の commit (`827682b60`、祖先) が main に在った (D2184 項 1 = pin 前進で admission policy の sha が変わり旧 policy の binary を消費できない、同 D の帰結の書き方 = 旧系列は固定 checkout で続ける)。不整合 2 件の整合 (D2196) と、g1 の段階 4 の拒否を実測した記録 (entry 1776 の N1、起点は `482f19b88`) は後の着地 | D2196 / entry 1776、entry 1787 / 1790、D2201、D2184 |
| 2 | 結論 §7 (結果 §8.1 は 1 文追加) | 同 job stock 対照は driver の修復と再投入の認可を待つ | driver は修復済み (緑は結合検査まで)、実機の再投入は予算の再提示待ち | D2205 / entry 1795、`t2795-pair-repair` §0 |
| 3 | 限界 §1 | A-1 の独立再現 2 本目は未投入で測定値は無い | 2 本とも完走、同一配置の反復で分類と符号が一致した観察 | entry 1755、D2194 項 6 |
| 4 | 限界 §3 | 「非列挙」の定義の置き直しは未裁定 | 2026-09-02 に裁定済み、壁と休眠は不変 (**前稿の執筆時点で既に偽**) | D1441、21b 版 §2 第 3 幕 (b)、20b 版の訂正 1 |
| 5 | 結果 §6.1 | 検証相は B-8 の 3 要素 (対象・種・長さ) のいずれも要件と違う | 対象と長さが違う (種の仕分けは B-8 の発効で独立 process の自己シードへ改まった) | insight §2、stale 注記 3 |
| 6 | 結果 §12 (pin) | §3〜§6 はいずれも pin `511c9538` の下 | §6.2 の B-8 だけが前進後の pin `e9e477ca` の下 | B-8 の結果稿 §1.2 |
| 7 | 結果 §12 (B-2 / B-5) | B-2 と B-5 はともに「未実走・未取得」 | B-2 は未実走・未取得、B-5 は試走 (3 arm と block stock の 4 job、計 53 論理 session) が完走したが n = 1・主標本外で未取得、本走は未認可 (段階認可は本走の認可ではない)。事前登録 v1 は未発効 | entry 1779、D2200 項 1 |

## 4. 段 6 read-only レビューと裁定

**Codex の独立レビューは実施できなかった。** 2026-09-21 14:28 に投入した Codex の read-only レビュー 2 本 (A = 結果・考察、B = 要旨・結論・限界) は、
いずれも 14 model call・約 110 秒で `You've hit your usage limit ... try again at Sep 26th` を受け、出力 0 byte (`failure_class=f45_missing_output`、
`codex_exit_code=1`) で終わった (receipt = job dir `artifacts/dev-wave-paper-b8-pass-ja/review-{a,b}/receipt.json`)。D582 に従い自動の再試行はしていない。
**代替として、同じ prompt (job dir `prompt-review-{a,b}.md`) で Claude の独立 context の子 2 本** (subagent_type = Plan で Edit / Write を持たない、model = opus) を
並列で走らせた。親とは別 context だが同じ系統のモデルであり、Codex の独立レビューと同等の独立性は主張しない。子の終了後に作業ツリーへの書き込みが 0 であることを
`git status` で確かめた。逐語は job dir の `review-a-out.md` / `review-b-out.md`。

| レビュー | 所要 | 判定 | 所見 |
|---|---|---|---|
| A (結果・考察 21b 版、同 README、前稿 dir README の pointer) | 759 秒、道具 55 回 | NO-GO | must-fix 1 / should-fix 2 / nit 7 / refuted 8 |
| B (要旨・結論 21b 版、限界節 21 版、2 dir の README、前稿 dir README 2 本の pointer) | 921 秒、道具 71 回 | NO-GO | must-fix 1 / should-fix 2 / nit 7 / refuted 6 |

**must-fix は A・B とも同じ型 (1 件):** 判定集合 30 枠を「独立 8 反復 × 3 workload・extime 10 s」へ丸ごと帰属させる要約 — 実際は本走 24 枠が 8 反復 × 3 workload・
extime 10 s で、残る 6 枠は校正の単発 (3 workload × extime 6 s / 10 s) である (結果稿の題は「24 枠すべて anomaly ゼロ」)。数値の逐語照合 (163 token) では
捕まらない「数に付く条件」の誤りで、結果 §6.2・§12、要旨の冒頭・§2・§3 (c)、結論 §3、要旨・結論 README §1・§2、限界 README の B-8 行、本 README §1、
`docs/phase3.md` の項に同型があった。
全箇所を「本走 (独立 8 反復 × 3 workload・extime 10 s の 24 枠) と校正の完走 6 枠からなる判定集合 30 枠」の形へ直した (限界 §2 は初稿から正しい形)。

| 所見 | 裁定 | 処置 |
|---|---|---|
| A-1 / B-1 (上の must-fix) | real・採用 | 上記の全箇所 |
| A-2 §12 の B-5「未実走」は entry 1779 の試走完走で偽 | real・採用 | §12 を B-2 と B-5 で分け、冒頭と §3 の表 #7 に足した。親の初稿の「偽にするのは 3 件だけ」は反証された |
| A-3 §11 が旧 pin の性能不成立と現行 pin の B-8 `pass` を限定抜きで並べる | real・採用 | 旧環境・旧 pin / 現行 pin・patch、条件語、D12 を足した |
| B-2 結論 §3 の「発効した事前登録」が S' の登録と読める、「S-1 (iv 付属) の充足ではない」が要旨・結論・限界の B-8 段落に無い、「検証された」は (P5) の語彙から外れる | real・採用 | 3 稿の B-8 段落に「S' の事前登録の (iv) 付属 (検証相の規則) の充足ではない」(呼び名は焦点再レビューの nit で統一)を足し、登録を「S' とは別の B-8 事前登録 v1」と明示、動詞を「3 要件が揃った検証を行い」へ |
| B-3 限界 出所 6 が supersede 済みの 09-10 版方法節を指す | real・採用 | 09-20 版へ |
| A-4 表 8b の題 (費用行は dispatch Elapse の和) / A-5「事前登録は対象を案 A とし」(案 A は推奨、D2186 項 1 が認可) / A-6 限定 3 の 32 bit 句の欠落 / A-10 §8.1 の「新しい pin」 | real (nit)・採用 | 文言を直した |
| A-7 本 README §3 の節題と #1 の型 (D2184 項 1 で前稿の採用時点で既に不正確) | real (nit)・採用 | 節題と #1 の型の記述 |
| A-8 前稿 dir README の pointer に entry が無い、「執筆時点では真」の曖昧さ | real (nit)・採用 | 3 本の pointer とも「採用時点 (`…`) では真」と実施記録の entry を足した |
| A-9 L-A1S-4 を「2 attempt の観察に基づく限定」と読む事実を足せる | real (nit)・**不採用** | 偽ではなく足せる事実で、依頼 (本題の執筆だけ) の scope 外 |
| B-4 要旨 §2 の見出しの字数 / B-5 別表の「10 行」は 9 行 / B-6 変更箇所の自己記述 / B-7 未実証一覧を受ける言及の書き方 / B-8 限界 §2 に D2160 の 10 s 未完走との非比較 / B-9 別表 B-6 行の 4 巡目と予算の出所 (D2187) / B-10 結論 §7 の B-5「試走と本走で問う」 | real (nit)・採用 | 文言を直した |
| A-11〜18、B-11〜16 (P2〜P5 の攻撃、命名、pointer、pin の「だけ」、§6 参照、scope、裁定の出所) | refuted (レビュー自身の判定) | 維持 |

fix は commit `fb9fac344`。**焦点再レビュー 1** (同じく Claude の独立 context の子、prompt = job dir `prompt-focus-1.md`、806 秒・道具 85 回、逐語は job dir の
`focus-1-out.md`) は **GO** — A・B の real 所見 20 件 = closed 18 / partial 1 (A-7) / 不採用が妥当 1 (A-9)、must-fix の同型は対象 8 file の全数検査で残り 0 件、
親の派生値 (字数 562 / 1,757 / 1,989、別表 15 行 = 更新 6 + 不変 9、結果稿 19 本、所見件数) は再計算で一致。新規 nit 9 件 (A-7 の fix が持ち込んだ #1 の型付けの誤り、
B-5 の 53 論理 session は 3 arm と block stock の和、未発効の B-5 登録を「の下で」と書いた句、(iv 付属) の呼び名の揺れ、要旨・結論 README の結論 §7 行の型付け、
同型箇所の列挙漏れ、本 README §2 の時刻の根拠、phase3 の項の代替の限定、worklog 断片の草稿) はすべて real とし、記録 commit で直した。所要秒数と道具回数は
レビューの逐語に無く、親が完了通知で受け取った値である (焦点再レビューは「照合不能」と記録)。DW-O16 の上限 3 巡の 1 巡目で閉じた。

## 5. 検査と受入

- 記録 commit 前の親の検査は worklog fragment に書く (`check_docs`、相対リンクと path の実在、数値 token の逐語存在、旧稿本文の sha256 不変、三軸語走査、
  全史 provenance 監査)。受入全走と land の結果は job dir の receipt と専用 handoff に集約し、本節には実測前の欄を作らない (09-20 序論 wave の先例)。

## 6. 限界・言わないこと

- 3 稿は執筆者向けの日本語草稿であり投稿本文ではない。英語稿は作っていない。新規の測定・図・gate・検査・台帳は足していない。
- 前稿の本文は継承しており、§3 の表と B-8 の箇所以外を採用時点 `d99c556df` の正典と逐文で照合し直してはいない。論文ストーリー 2026-09-21 版・21b 版
  (entry 1773 / 1793) の本文との逐文照合もしていない (走査は worklog entry の見出しと D の項見出しによる)。
- 稼働中・未着地の wave (論文ストーリー 2026-09-21c 版、B-4 の対応証拠、mocc の X/P 計装、B-5 の Tier0 など) の内容は数えない。
- B-8 の `pass` は規則の機械適用の出力であって研究の成功宣告ではない (D12)。本 wave はそれを論文草稿へ運んだだけで、判定・測定を足していない。
- 文書成果の完了であり、未取得の測定 (A-1 充足・A-5・B-1・B-2・B-4・B-5 など) や Phase 3 全体の完了を意味しない。
- 記録 commit (`1116f429b`) の時点で local main は `5be086476` へ進んでおり、第 29 回 /rulings (D2206、全 16 項) などが採用時点より後に着地した。
  D2206 の項は land・テスト・受領証などの運用で、3 稿の状態語を偽にする項は無い (項 14 の mocc G2 観測の上流報告は人間が送信する、は限界節 §2 の記述と整合)。
  採用時点は `d99c556df` のまま動かさない。

## 7. dev-wave 改善候補 (段 8、`docs/skill-self-improvement.md` の routing)

| 候補 | routing | 処置 |
|---|---|---|
| Codex の利用上限で、`DW-C00` が docs-only の一次資料再抽出 wave に残せと言う独立 read-only レビューに代替経路が無い (今回は Claude の独立 context の子で代替) | failures (F818 の同型再発) + 段構成の変更 | 再発追記は spool fragment。代替経路の正本化 (例: Codex 不可用時は Edit / Write を持たない独立 context の子で代替し、成果物に独立性の限定を書く) は段構成の変更なので実装せず、ここに候補として記録する (`DW-C00` は L1 予算) |
| 草稿を新しい dir へ複製して新版にすると、同 dir 相対のリンク (`intro.md`、`../paper-results-ja/`) が別の版や不在 file を指す | wave 固有の手順 (repo 外の記憶) | 相対リンクの解決先を機械で確かめて直した (job tmp の linkcheck)。repo は変えない |
| 数値 token の逐語照合 (163 token) は「数に付く条件」(30 枠が本走 24 + 校正 6 であること) を守らない | 既存の記憶 (数値の機械照合は散文の量化語を守らない) の同型再発 | repo は変えない |
