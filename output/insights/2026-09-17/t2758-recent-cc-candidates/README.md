# [T-2758] 近年 CC 手法の候補表 — 一次資料・レビュー・是正の凍結記録 (2026-09-17)

- authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と phase doc)
- wave: `dev-wave-t2758-recent-cc-candidates` (branch `worktree-dev-wave-t2758-recent-cc-candidates`、docs のみ、実装面 0 byte)
- 起点: ユーザーの `/dev-wave` 引数「[T-2758] (P2、D2114 項 4) 近年 CC 手法の候補表を docs/related-work に起こす — 一次資料・実装可用性・ライセンス・YCSB 適合・trace 移植費用・証明面・既存 CC (Silo / MOCC / TicToc / Cicada) との差、追加対象と棄却理由。入口 = docs/related-work/README.md の literature map (NeurCC 2503.10036 SIGMOD 2026 / ATCC 2026)。D2095 の軸 1 登録済み検索とは重複取得しない (通常の文献調査として行う、D1760 が許す範囲)。CCBench への実装追加とは分け、A (mocc 第 2 例) に従属させない。着手直前の local main から fresh worktree を作る。docs のみ。規律 2 を緩めない。本題の候補表だけ。framework・一般化は scope 外。」
- 成果物: `docs/related-work/cc-candidates-2026-09-17.md` (日付付き凍結物)、`docs/related-work/README.md` 7.1 のポインタ段落、`docs/README.md` の地図 1 行
- 逐語: `verbatim/` (親 brief、段 6 レビュー prompt と出力、親の是正対応表、焦点再レビュー prompt と出力、web 取得の記録)。行末空白のみ可逆に正規化しうる、内容は無変更
- 計測: なし。本 wave は測定も build も行っていない。変異 matrix は実装面差分ゼロにつき免除 (DW-S04)

## 1. 何を決めて何を決めていないか

決めたこと (候補表上の判定): 優先調査候補 = Rebirth-Retire (PVLDB 2025)、Bamboo (2021、対照候補)、Polaris (SIGMOD 2023、対照用)。
保留 = Plor、Tebaldi、Shirakami の S-OCC。棄却 (不適合確認) = Brook-2PL / Aria / IC3 / Shirakami の S-LTX (事前知識)、
Caracal (GPL-2.0)。母集合外 = Polyjuice / NeurCC / ATCC (学習型、入口)、CormCC (単一 protocol でない)、Sundial (分散)、
TXSQL (engine 内最適化)、ESSN (certifier 基準)。**追加対象 (四条件の充足確認済み) は 0 件。**

決めていないこと: CCBench への実装追加 (D2114 項 3 の別件)、pin 前進 (D1603 / D2104 項 13)、変異探索面化 (D579)、
共通契約の設計 (D2114 項 4 の「要求を共通契約へ反映する」は候補表 §6 の確認課題を入力にした別作業)。

## 2. 段 1 brief と裁定

brief = `verbatim/s1-brief.md`。(P1) 母集合 = 2017 以降の単一ノード in-memory serializable 汎用 CC で YCSB 対話型を実行できる
もの、学習型 3 本は入口。(P2) 列は T 定義どおり。(P3) 4 条件 (a 公開実装と license / b YCSB 対話型 / c trace 3 点の費用 /
d 既存 4 CC との差)。段 2 / 3 の子は docs-only につき省略 (DW-C00 軽量版)、段 6 に read-only codex の敵対レビュー 1 本 +
焦点再レビュー 1 本。web 検索は段 5 で明示して使い、登録済み索引 (arXiv API / OpenAlex / DBLP) の query は出していない。

## 3. 一次資料の取得 (2026-09-17)

| 資料 | 経路 | 状態 |
|---|---|---|
| NeurCC `2503.10036v4`、ATCC `2603.13906v1` | WebFetch (HTML → 小モデル抽出要約) | 抽出要約のみ (原文の全件走査ではない) |
| Bamboo `2103.09906` | arXiv PDF → pdftotext | 本文精読 |
| Plor DOI `10.1145/3514221.3517879` | 著者頁 PDF → pdftotext | 本文精読 (ACM は 403) |
| Rebirth-Retire PVLDB 18(9) | vldb.org PDF → pdftotext | 本文精読 |
| Shirakami `2303.18142` | arXiv PDF → pdftotext、abs 頁 | 本文精読 |
| Polaris DOI `10.1145/3588724` | ACM PDF 403、著者頁 PDF 404 | **本文未読**。機構は公開 source (`row_silo_prio.h`、`config-std.h`) |
| Brook-2PL / ESSN / TXSQL | arXiv abs (WebFetch) | abstract |
| Caracal / Aria / CormCC / Tebaldi / Sundial | WebSearch の結果表示、GitHub API | 題名・repo 記述まで |
| repo metadata (10 本) | GitHub REST API 匿名 `/repos/<o>/<n>`、README / LICENSE / config raw | `verbatim/web-evidence.md` |
| CCBench 側 | 現行 pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` の `LICENSE`、`include/tx_executor_concept.hh`、`cc/*/CMakeLists.txt` | source 直読 |

取得物 (PDF テキスト・README・LICENSE・config) は job dir (`$CLAUDE_JOB_DIR/tmp/pdf/`、repo 外) に置き、repo へは入れていない
(論文本文の複製は置かない)。レビュー子には同じ取得物を `sources/` として絶対 path で渡した。

## 4. 段 6 レビューと是正

### 4.1 敵対レビュー 1 本 (`verbatim/s6-review.md`、codex `gpt-6-astra` medium、read-only、rc=0)

所見 10 件 = real 9 (must-fix 8 / nit 1) / refuted 1。最重要 3 件:

1. Rebirth-Retire / Bamboo を「単版 lock 系、trace 専用 field 1 個」と書いた前提が誤り — `rr.txt` §4.4「a tuple may have
   multiple versions」、Bamboo §3.5「multiple uncommitted updates can exist on a tuple」。
2. Polaris の `validate` の説明が source と不一致 — `validate` は write set 外の locked を拒否し `data_ver` を照合するだけで、
   priority の `LOCK_ERR_PRIO` は `lock` / `try_lock` が返す。
3. P3 が未確認を合否へ倒していた (「公開実装なし」「唯一」の RW1 違反を含む)。

親の裁定と適用 = `verbatim/s6-parent-fix-table.md` (所見 1〜9 採用、10 は refuted だが README 段落の是正案は採用)。候補表を
v2 へ書き直した (P3 を「充足確認 / 不適合確認 / 未確認」の三値へ、判定を「優先調査候補 / 保留 / 棄却 / 母集合外」へ)。

### 4.2 焦点再レビュー 1 本 (`verbatim/s6-focus.md`、stage=focus、rc=0)

前巡 10 件の対応 = closed 6 / partial 4 (所見 2・3・6・8)。新規所見 8 件 = real 7 (must-fix 5 / nit 1) / refuted 1。
量化の検算 13 件 = 一致 8 / 未照合 5 (RR の LICENSE 本文と neurcc root 生一覧はレビュー子の照合資料に無かった、
費用の全候補最小、mocc 141 行の元 diff、web 検索の実行内容)。

| 新規 | 親の裁定 | 適用 (候補表 v3) |
|---|---|---|
| 1 三値の適用不揃い | real | S-OCC を保留 (d=?)、Plor を b=?、RR の「唯一」文に P1 対話型直接適合の未確認を併記 |
| 2 Polaris の変更範囲 | real | 保存 source の release 3 関数の priority 処理を書き、変更範囲を access / validate に限定しない。費用は仮説、順位は確定しない |
| 3 未照合を確定へ倒した分類 | real | 「A Hybrid Approach …」を包含保留へ、Caracal の b を未確認へ (棄却は a=× の API 分類で維持)、ATCC の「学習型」は README 7.1 の既存分類に依拠と明記 |
| 4 不在表現の粒度 | real | NeurCC は「root 直下に LICENSE 系 file なし」、ATCC は「公開実装を確認できる URL は提示されていない」、追加照合 3 件の独立照合未了を注記 |
| 5 年代誤認 (DTA 2018 / DRP 2019 / SLOG 2019) | real | SLOG は分散として対象外、DTA / DRP / OSDI 2024 多版は包含保留、Strife は候補として数えない |
| 6 timestamp の断定 | real | §6 項 4 を「初期値・最終値・再割当履歴と版・commit 順の対応は未照合」へ |
| 7 nit (引用脱字、§4.4、分類数、MOCC の年、Shirakami の参考文献) | real | 逐語どおり訂正 |
| 8 CormCC の裏付け | refuted | 出典を Plor §7 の逐語へ替えた |

3 巡目は起こしていない (DW-O16 の上限 3 巡内、残る是正はレビューの逐語案の適用)。親が残した量化の検算: 候補行 17、
最上位分類 = 優先調査 3 / 保留 2 行 (+ Shirakami 行内の S-OCC) / 棄却 5 / 母集合外 7、YCSB 対応 7 protocol、Polaris の
bit 割当 1/4/4/10/45 (合計 64)。

## 5. 追加照合 (レビュー後、親)

neurdb/neurcc の root 一覧 (GitHub API contents) に LICENSE 系 file なし、gitzhqian/RebirthRetire の LICENSE raw = ISC
(Bamboo-Public と同文)、luyi0619/aria の LICENSE raw = MIT。生記録は `verbatim/web-evidence.md` 末尾。焦点再レビューは
これらを独立照合できていない (照合資料に含めなかった)。

## 6. 検査

- `python3 tools/check_docs.py` rc=0 (v1 / v2 / v3 の各時点)
- `python3 -m orchestrator.campaign.s8b_holdout_freeze search` rc=0
- `git diff --check`、`spool_fold.py --dry-run`、`check_ai_provenance.py`、受入全走: 結果は worklog エントリに書く (本 README は
  commit 前に凍結するので、ここには載せない)

## 7. エージェント工数

codex 2 本 (review 1、focus 1、いずれも read-only、receipt は job dir の `artifacts/`)。計測ゼロ、build ゼロ。web 取得: WebSearch
7 回、WebFetch 6 回、GitHub API 14 回、raw / PDF 取得 20 回。

## 8. 次 wave の出発点 (裁定ではない)

- 優先調査候補 3 本の「未確認」を潰す作業 (Rebirth-Retire の source 読み、Polaris 本文の入手、CCBench の対話 API への
  適合の確認) は、B 実装の判断条件 (共通契約 + 固有実装費用、D2114 項 4) を揃える別 T の入力になる。
- 候補表 §6 の確認課題 7 件が共通契約への要求の入力。
