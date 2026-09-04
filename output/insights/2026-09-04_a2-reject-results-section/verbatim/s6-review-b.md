## Must-fix

1. **results 系列の分類が同じ README 内で矛盾している。**
   (a) D12 の完全・決定論的な機械射影だと誤読され、手書き散文まで一次事実として利用される。
   (b) [README.md:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/README.md:171) は「D12 の材料レポート」とする一方、[README.md:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/README.md:187)、[results:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/results/2026-09-04-a2-certification-reject.md:3)、fragment:20-21 は「D12 の機械射影ではない」とする。
   (c) README:171 を「一次資料に束縛した執筆者向け統制稿。D12 の機械射影の材料レポートではない」に統一する。
   (d) real 確度: **1.00**。

2. **決定 fragment に確定 D 番号が残っている。**
   (a) spool 合成時の番号管理と既裁定参照が混同され、結果系列の根拠が未割当 fragment 自身の番号であるかのように読まれる。
   (b) [fragment:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/spool/decisions/2026-09-04-dev-wave-a2-reject-results-section-1.md:20)、`:21`、`:27`、`:29`、`:31` に `D12` 3 件、`D1013` 2 件。見出し自体は正しく `{{D:paper-story-results-series}}`。
   (c) 5 件を「材料レポート裁定」「claim-evidence 系列裁定」など番号を持たない名称へ置換する。
   (d) real 確度: **0.99**。

## Nit

3. **「成果物自身は信頼区間を持たない」の局所的な先行詞が曖昧。**
   (a) 直前に表の CI を説明しているため、表や provenance 自体に CI が無いという自己矛盾に読まれる。
   (b) [results:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/results/2026-09-04-a2-certification-reject.md:99)。意図した区別は results:46-49 にある。
   (c) 「`certification.json` 自身は信頼区間も有意差判定も持たない」と対象を明記する。
   (d) real 確度: **0.91**。

4. **二つの作業過程の主張は一次資料束縛ではなく執筆者の証言になっている。**
   (a) 「新規計測なし」「人手で 1 回検算」が機械監査済みの provenance 事実だと誤読される。
   (b) [results:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/results/2026-09-04-a2-certification-reject.md:9)、[results:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/results/2026-09-04-a2-certification-reject.md:96)。親の再計算記録は後者を補強するが、certification / raw-manifest / WAL / 裁定そのものではない。
   (c) 前者を「本稿と図は既存 attempt の入力だけを使用する」に狭め、後者の「1 回」を削るか作業記録への参照と明示する。
   (d) real 確度: **0.82**。

## B1〜B10 実装判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| B1 | closed | 旧値を先置きせず、数値再掲も排除。`results:31-32,69-78`、caption |
| B2 | closed | attempt、2 request、2 host、別時刻、論理積へ束縛。`results:36-44`、caption |
| B3 | closed | status 不変、意味関門未確立、遡及認証禁止、後継 results で改訂を明記。`results:51-57`、`README:116-124` |
| B4 | closed | D1257、legacy 1 回、L01、noise floor、minimality、D1198、D1169、D1263 を実配置 |
| B5 | closed | 表見出し・脚注と図中表示が correctness を別 run、非性能 certification と明記 |
| B6 | closed | mean CI と median 効果・status・有意差を分離。caption と `results:97-100` |
| B7 | closed | abort を集約 1 点、descriptive、CI なし、因果主張なしに限定 |
| B8 | **partial** | results 本体と fragment は正しく再分類したが、README:171 が逆の分類を残す |
| B9 | closed | stale 注記は 2 件と明記され、2 件目に D1198 未適用と非遡及性を配置 |
| B10 | closed | 生成器は 548 行で目安 550 行以内。採用範囲を実装し、却下した一般 hardening は持ち込んでいない |

## 数値・caption・SHA

表 1 の対象 **42 数値すべて**が provenance の `cells` / `effects` と、記載精度どおり一致する。

| cell | 5 標本 | median | mean ± CI | cv | abort | 効果 |
|---|---:|---:|---:|---:|---:|---:|
| rr5-stock | 5/5 一致 | 2,527,542 | 2,554,949 ± 119,798 | 0.0378 | 0.7767 | 分母 |
| rr5-fixed10 | 5/5 一致 | 1,355,011 | 1,359,770 ± 20,944 | 0.0124 | 0.1189 | −46.3902% |
| rr50-stock | 5/5 一致 | 3,662,448 | 3,700,807 ± 136,990 | 0.0298 | 0.6903 | 分母 |
| rr50-fixed5 | 5/5 一致 | 1,248,603 | 1,242,560 ± 32,945 | 0.0214 | 0.2048 | −65.9080% |

- provenance の実 SHA-256 は `4d40222a98ccf1baee49881bf8b94292119f3771141064c49658c8c7631c6101`。results:150 と一致し、placeholder はない。
- certification の実 SHA-256 も記載どおり `f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40`。
- figures README の blockquote marker を除いた caption 正文と provenance `caption` は byte 一致した。両者の SHA-256 は `d1d7a6e5ee0eb4b7498c1fdd13f80760047808fbbf70e0874b2a0ca97294843e`。
- したがって caption 内の request、host、時刻、効果、条件値も provenance と一致する。

## L-A2-1〜11 の実配置

| 限定 | 判定 | 実文 |
|---|---|---|
| L-A2-1 | closed | `results:64-65,101` |
| L-A2-2 | closed | `results:62,65,101` |
| L-A2-3 | closed | `results:18,66-67` |
| L-A2-4 | closed | `results:46-49,97-100` |
| L-A2-5 | closed | `results:18-19` |
| L-A2-6 | closed | `results:51-57`、caption |
| L-A2-7 | closed | `results:39-40`、caption |
| L-A2-8 | closed | `results:69-78`、caption |
| L-A2-9 | closed | `results:41,102-104` |
| L-A2-10 | closed | `results:63-64,101` |
| L-A2-11 | closed | `results:97-100`、caption |

caption には D1198 未適用、L01、D1257 が明記されている。D1169 は番号表記ではなく、2 独立 campaign、2 request、2 host、別時刻、outer の論理積という実内容で入っている。

## 区別の規律

- correctness の緑は性能と分離されている。
- 旧系列の数値は fig5 と results 本文に再掲されず、comparator にされていない。
- `reject` は protocol status と明記され、研究の失敗宣告へ拡張されていない。
- Pegasus 一般への一般化はなく、attempt と 2 campaign に束縛されている。
- mean CI は median 効果・status・有意差から分離されている。nit 3 の先行詞だけ改善余地がある。
- abort 下段は機序同定に使わないと本文、caption、図中テキストの三方にある。
- A-2 の完走を「全但し書きが外れた」とする文はなく、read-heavy は A-6、旧系列の但し書き 1・3 は残る。

## 系列規則と決定 fragment

README、stale 注記 2 件目、fragment の append-only、再導出単位、版履歴非登録、一次資料限定、protocol status の限定は整合している。例外は must-fix 1 の README:171 だけである。

fragment は次の状態だった。

- 有効な `[T-数字]` の例示: **なし**
- 題末尾の日付: **なし**
- 確定 D 番号: **あり、5 件**。must-fix 2
- 新規決定の見出し: `{{D:paper-story-results-series}}` で正しい

## 散文の一次資料束縛

数値、status、campaign identity、correctness、D1198 の証拠上限、D1257、D1263、旧系列との禁止推論、S' と A-2 の区別には、それぞれ certification、provenance 経由の raw-manifest / WAL、または逐語裁定への経路がある。科学的・数値的な事実命題で辿れないものは確認しなかった。

一次資料束縛から外れるのは nit 4 の作業過程に関する二つの自己証言だけである。なお、指示どおり raw-manifest / WAL の repo 外 bytes は直接読まず、hash 束縛された provenance、certification、親の再計算値で照合した。

## 総括

- B1〜B10: **closed 9、partial 1、open 0**
- 所見: **4 件**
- must-fix: **2 件**
- nit: **2 件**
- pytest: 指示どおり未実走
- 書き込み: なし

最重要 3 件は、(1) README:171 の D12 分類矛盾、(2) decision fragment に残る 5 件の D 番号、(3) results:99 の「成果物自身」という曖昧な先行詞である。