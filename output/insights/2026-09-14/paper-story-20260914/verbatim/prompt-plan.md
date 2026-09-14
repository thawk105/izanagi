単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/2026-09-05.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/roadmap.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260914/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い)。静的な読解と照合だけでよい。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 依頼

親は `docs/paper-story/2026-09-14.md` という**新しい日付の版**を追加しようとしている。
`docs/paper-story/README.md` の凍結規約は、新しい日付の版は**その日付時点の正典全体からの
全項目再導出**でなければならず、一項目だけの差分改訂を新しい日付として置いてはならないと定める。

お前の仕事は、**最新版 (2026-09-05) の各項目が 2026-09-14 時点で正典に照らしてどうなっているかを、
親とは独立に洗い出し、項目ごとに一次資料の所在を付けた再導出地図を作ること**である。
本文の代筆はしなくてよい。地図と、親の暫定裁定への賛否を返せ。

## 正典 (矛盾があればこちらが勝つ)

- `docs/roadmap.md` のポジショニング節 (§8)
- `docs/decisions.md` — D1646 以降が最新版の後に増えた分。`grep -n "^## D" docs/decisions.md` で索引する
- `docs/worklog.md` (現行) と `docs/archive/worklog-phase3-09*.md` (2026-09-05〜09-14 の 209 エントリ)
- `docs/phase3.md` と `docs/phase3-main-experiment.md`

数値・日付・判定は一次資料 (`output/insights/` の成果物、decisions の D 本文、凍結 policy JSON、
`docs/paper-story/results/` の統制稿が指す権威 bytes) から取れ。**最新版の記述を数値の出所にするな。**

## 親が段 1 で実測済みの事実 (お前はこれを疑ってよい。疑うなら一次資料を指せ)

- A-2: attempt `t2364-20260907b` (2026-09-07) が outer `observed-positive`。
  rr5 adopted 3,987,794 / stock 2,438,295 (+63.5485%)、rr50 adopted 4,297,929 / stock 3,756,230 (+14.4213%)。
- A-6: attempt `a6-20260908b` (2026-09-08) が status `reject`。rr95 stock 10,088,796 / adopted 9,505,248、
  effects −0.057841193339621455。
- T-2557 / T-2589: balanced の stock-inline 対を 2026-09-13 に正式測定し 2026-09-14 に `accepted`。
  ratio 1.1122537536191646、improvement_percent 11.225375361916456、
  baseline median 3,893,509 (cv 0.0227) / target median 4,330,570 (cv 0.0128)。再測定はしていない。
- A-1: pilot attempt-0004 が 2026-09-11 に全 3 workload `valid` で完走 (各 60 対)。
- T-2265: cohort 2 の主判定 +4.900% (95% CI [+3.316%, +6.509%])、11 group 認証で費用を理由に打ち切り。
- T-2566: 静的 tail 本走 driver を実装し投入前条件 5 件を実測。**本走は未投入。**
- C-4: 軸 1 OpenAlex の継続取得を D1760 で打ち切り、軸 3 は D1931 で走らせず `RW0` 据え置き。
- D1936 が全 50 項を一括裁定した (2026-09-10)。D1984 / D1985 が 2026-09-14 に確定した。

## 親の暫定裁定 (P1 — 攻撃してよい)

- (P1-a) A-2 の `observed-positive` が出ても、§8 の A-2 は A 群の残件から外さない。
  理由: D1645 の解除条件 (「正しい identity で取り直した attempt」) を満たすかを README 自身が
  「本節はまだ判定していない」と書いており、本版が正典から判定する。
- (P1-b) balanced stock-inline 対の `accepted` (+11.2254%) は但し書き 1 (A-1) を外さない。
  T-1998 の事前登録は A-1 の estimand (D1262) とは別に立った別の事前登録だからである。
- (P1-c) §9 の第 4 文を「採用構成の現行環境での正式判定はまだ無い」から
  「2 workload について `observed-positive`、read-heavy は `reject`」へ書き換える。

## 守らせる不変条件

- 既存の版・`results/`・`figures/` は 1 byte も変えない。新版は新しい日付の file として足すだけ。
- 旧 attempt の判定を取り消さない (絶対規律 7)。前後比較として読ませない。
- `observed-positive` は protocol の status であって研究の成功宣告ではない (D12)。
- 正しさの緑を性能の主張へ染み出させない (絶対規律 2)。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。提案してはならない。

## 出力形式 (この見出しをそのまま使う)

## 再導出地図

最新版の §0 / §1 / §2 (第 1〜3 幕、(a)〜(g)) / §3 (項目 1〜5) / §4 (図の表) / §5 / §6 (言えること・
言えないこと) / §7 (前半 36 項・後半 11 項) / §8 (exact claim、A 群、B 群、C 群) / §9 (4 文要約と 7 種の表)
の各項目について、次の 4 列の表または箇条書きで書け。
`項目 | 2026-09-14 時点の状態 (不変 / 更新 / 訂正 / 新設 / 削除) | 一次資料の path または D 番号 | 一言の理由`

**「不変」も明示的に書け。** 書かれていない項目は「調べていない」と解釈される。

## 新版が前版を訂正すべき箇所

最新版の記述が一次資料に照らして**誤り**になっている箇所を列挙する。stale (古いだけ) と
誤り (当時から間違い) を分けて書け。

## 親の暫定裁定への評価

(P1-a) (P1-b) (P1-c) のそれぞれについて 同意 / 不同意 を書き、不同意なら一次資料を指した対案を書け。

## 見落としの危険

親の地図に入っていないが新版に入るべき正典の前進を列挙する。逆に、親が入れようとしていて
実は正典に無い / 射程を超えるものも列挙する。

## 総括

10 行以内。新版の headline を 1 文で提案し、最大の危険を 1 つ挙げる。
