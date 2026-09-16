単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/brief.md (親の段 1 brief)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/README.md (33,959 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/2026-09-14.md (229,235 bytes / 2,310 行 — 最新版。**全文 `cat` しないこと**。`grep -n "^## \|^### " <file>` で節の位置を出し、`sed -n '<開始>,<終了>p'` で 200 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/output/insights/2026-09-16/t2647-b10-tail-downstream.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md (37,670 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/results/2026-09-16-b7-three-run-materials.md (50,842 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/spool/worklog/2026-09-16-dev-wave-t2630-scan-boundary-reach-1.md

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,248,926 bytes / 64,167 行、
`docs/failures.md` は 2,661,806 bytes、`docs/worklog.md` は 98,430 bytes / 3,666 行である。
**これらを全文 `cat` してはならない** (出力が壊れて成果物が不採用になる)。
`grep -n "^## D" docs/decisions.md | awk -F'D' '{split($2,a,"."); if (a[1]+0 >= 1989) print}'` で
D1989 以降の見出しを出し、必要な D だけ `sed -n` で 60 行以内ずつ読め。worklog は
`grep -n "^## " docs/worklog.md` で見出しを出してから読め。archive は
`docs/archive/worklog-phase3-09*.md` (1 file = 1〜2 entry、entry 1485〜1574) を entry 番号で選んで読め。
`wc -c` / `wc -l` は許す。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(`-o` の file は read-only sandbox では書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い)。静的な読解と照合だけでよい。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 依頼

親は `docs/paper-story/2026-09-17.md` という**新しい日付の版**を追加しようとしている。
`docs/paper-story/README.md` の凍結規約は、新しい日付の版は**その日付時点の正典全体からの
全項目再導出**でなければならず、一項目だけの差分改訂を新しい日付として置いてはならないと定める
(D1858 も同じ)。前版は 2026-09-14 版 (local main `af3762d62` から導出)。本版は local main
`bf4f91f51` (2026-09-17 00:33 JST) から導出する。

お前の仕事は、**最新版 (2026-09-14) の各項目が 2026-09-17 時点で正典に照らしてどうなっているかを、
親とは独立に洗い出し、項目ごとに一次資料の所在を付けた再導出地図を作ること**である。
本文の代筆はしなくてよい。地図と、親の暫定裁定 (P1)〜(P5) への賛否を返せ。

## 正典 (矛盾があればこちらが勝つ)

- `docs/roadmap.md` のポジショニング節 (§8)
- `docs/decisions.md` — **D1989〜D2087** が最新版の後に増えた分 (99 件)。特に D2044 (全 39 項の一括裁定、2026-09-16) は全項を読め
- `docs/worklog.md` (現行、entry 1575〜1579) と `docs/archive/worklog-phase3-09*.md` (entry 1485〜1574)。
  entry 1485 が前版を作った wave の記録である
- `docs/phase3.md` と `docs/phase3-main-experiment.md`
- `docs/failures.md` — 2026-09-14 以降の追記 (F 番号は見出しに日付が無い。「再発:」追記と F98x〜F1015 を見よ)

数値・日付・判定は一次資料 (`output/insights/2026-09-1[4-6]*/` の成果物、decisions の D 本文、
凍結 policy JSON、事前登録、`docs/paper-story/results/` の統制稿が指す権威 bytes、
`output/env/pegasus/calibration/registered/*.json`) から取れ。**最新版の記述を数値の出所にするな。**

## 親が段 1 で実測済みの事実 (お前はこれを疑ってよい。疑うなら一次資料を指せ)

brief.md の「brief 前に実測した前提 (引数 12 項目)」の表と「引数に無く、導出で入れる候補」を見よ。
要点だけ再掲する:

- B-10 静的右 tail 本走 (group `b10-backoff-grid-20260915T061814Z-545445`) は 2026-09-15 に完走、
  集団 verdict `not-observed-in-any-workload`、18 区間すべて `declining`、`performance_certified: false`。
  前版の 5 箇所 (§0 前進 9 / §2(g) 項 7 / §8 B-10 ×2 / §9 運用欄) が現在地として古い (当時は真)。
- official 床値 campaign が 2026-09-16 に初めて計測段を越えて完走した ([T-2698]、request `1818.nqsv`、
  rr20 = 35,817.945 / rr80 = 46,065.78、両 holdout とも配線下限 0.03 × stock 中央値、`eligible_for_refreeze: true` は
  producer 自己申告で未発効)。前版の A-4「launch certificate で停止・D1341 により未 land」は現況ではない。
- 層 3 の bench-first screening は 2026-08-25 から対象内で、前版の 6 箇所は**執筆時点で既に偽** (entry 1539、F1 再発)。
- B-7 三走行材料の results 稿 (entry 1531) は出たが、**D2044 項3 が B-7 の要件充足への昇格を否定**した。
- rr5 の accepted 較正 (entry 1535、records 2,000,000、CV 0.97%)、非 silo 較正 3 件 (entry 1503) と
  用途限定解除 (entry 1576 / D2083)、B-4 binary record (entry 1544) と配置 (entry 1555 / D2069)、
  B-4 記述統計追補 (entry 1500 / D2016)、適格赤 0 件 (entry 1547)、fig7 (entry 1541 / D2053)、
  D1640 追補 (entry 1533 / D2049)。
- [T-2630] (D2044 項25、main `bf4f91f51` に着地、worklog fold 未): `#define`/`#undef` が identity に乗らず、
  5 変異で identity 同一のまま実 TU が別プログラムになった。coder 面からは到達しない。修正は裁定待ち。
- [T-2588] (D2044 項9): K2 ループを既存経路で 1 巡、`certified` / 719,324.5 tps、proposal-2 は未評価。
- A-1: D2044 項8 が本走の認可据え置きを継続。T-2590 (pilot 専用分岐の一式) が稼働中 wave。

## 親の暫定裁定 (攻撃してよい)

brief.md の (P1)〜(P5) を読め。要点:

- (P1) 09-15 cohort の論文図は本 wave では作らず「未作成」と書く。置き場所 (本体系列 `figures/fig8_…`、生成器名、入力の束縛形) だけ本版が定める。
- (P2) §9 の 4 文要約の第 4 文は書き換えない。肯定的 headline 主張は増えていない。
- (P3) 前版の訂正の分類: 「執筆時点で偽」= 層 3 の 6 箇所 (訂正 1 件)。B-10 の 5 箇所と official 床値は「前進」。
- (P4) T-2630 を §3 項目 5・§5・§6・§9 に入れ、§8 exact claim (正しさ) の限定 (v) として足す。
- (P5) README の stale 注記 3 件を本文へ吸収して 0 件へ戻し、「2026-09-17 版が前版を訂正した箇所」節を新設する。

## 守らせる不変条件

- 既存の版・`results/`・`figures/`・`claim-evidence/`・`docs/paper-story-backoff/` は 1 byte も変えない。新版は新しい日付の file として足すだけ。
- 旧 attempt の判定を取り消さない (絶対規律 7)。前後比較として読ませない。
- `observed-positive` / `reject` / `accepted` / `not-observed` は protocol の status であって研究の成功・失敗宣告ではない (D12)。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。
- 正しさの緑を性能の主張へ染み出させない (絶対規律 2)。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。提案してはならない。

## 出力形式 (この見出しをそのまま使う)

## 再導出地図

最新版の §0 (前進 13 点と冒頭の訂正 4 件) / §1 / §2 (第 1〜3 幕、(a)〜(g)) / §3 (項目 1〜5) / §4 (図の表) / §5 /
§6 (言えること・言えないこと) / §7 (前半 49 項・後半 9 項) / §8 (exact claim、決着済み、A 群、B 群、C 群) /
§9 (4 文要約と 7 種の表) / §10 の各項目について、次の 4 列の表または箇条書きで書け。
`項目 | 2026-09-17 時点の状態 (不変 / 更新 / 訂正 / 新設 / 削除) | 一次資料の path または D 番号 | 一言の理由`

**「不変」も明示的に書け。** 書かれていない項目は「調べていない」と解釈される。

## 新版が前版を訂正すべき箇所

最新版の記述が一次資料に照らして**誤り**になっている箇所を列挙する。stale (古いだけ) と
誤り (当時から間違い) を分けて書け。親が把握しているのは「層 3 の 6 箇所 (誤り)」と「B-10 の 5 箇所 (stale)」だけである。

## 親の暫定裁定への評価

(P1)〜(P5) のそれぞれについて 同意 / 不同意 を書き、不同意なら一次資料を指した対案を書け。

## 見落としの危険

親の地図に入っていないが新版に入るべき正典の前進を列挙する (D1989〜D2087 と entry 1485〜1579 を走査せよ)。
逆に、親が入れようとしていて実は正典に無い / 射程を超えるものも列挙する。
特に次を現物で確かめよ: 完了証明層の `SATISFIABLE_CONDITION_IDS` の現況、A-5 の状態、C-4 の状態、
8c 事前登録の現況 (D2071 / D2072)、D1341 の現況 (official 床値の成果物が land されたか、退避 bundle だけか)。

## 総括

10 行以内。新版の headline を 1 文で提案し、最大の危険を 1 つ挙げる。
