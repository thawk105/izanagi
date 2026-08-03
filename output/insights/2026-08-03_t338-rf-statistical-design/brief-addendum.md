# 段 1 brief 追補 — 段 2 の実行中に親が実測した 2 件 (2026-08-03)

本追補は brief.md の一部である。段 2 の子はこれを見ていない (投入後に判明した)。
**段 3 のレンズは brief.md と本追補の両方を攻撃対象とする。**

## 追補 A — roadmap §3.6(3') の前提と RF の paired 設計は正面から食い違う

`docs/roadmap.md` §3.6(3') は between-run floor を採否 floor に据える根拠として、

> variant と baseline は**決して同一セッションで測らない** (別ビルド・別時点) ので、
> 採否の floor は within-run でなく between-run であるべき

と書いている。一方 RF の 3 arm は**同一 allocation・同一 session 内で interleave して測る**
(段 3 レンズ B の「paired design です」の根拠、および 2026-08-02 正例 probe の `shuf` interleave =
`output/insights/2026-08-02_t139-positive-control-probe/README.md:61`)。
つまり **roadmap が floor の種類を決めるのに使った事実的前提が、RF の測定設計では成り立たない。**

なお 2026-07-29 の第 1 次 probe (`output/env/pegasus/t139-probe/t139_probe_gap.sh:81-83`) は
rep ごとに `stock A B` の**固定順**で回しており interleave していない。paired 化の根拠に
使えるのは 2026-08-02 の probe だけである。

帰結として点 ③ の裁定は次のどれかを選ぶことになる。

- (i) RF は roadmap の前提が成り立たない別クラスの測定であると位置づけ、**第 3 の floor**
  (paired 差 floor) を §3.6(3') へ追加する。roadmap は戦略層なので改訂には
  `docs/roadmap-history/README.md` の手続き (版凍結 + decisions 記録、または協議改訂) が要る。
- (ii) RF も「別セッションで測る」へ設計を寄せ、既存 between-run floor をそのまま使う
  (paired の利得を捨てる)。
- (iii) RF は floor による丸めを使わず、別の識別可能性規則を使う。

**親はこれを (i) と見るが、roadmap 改訂の手続きが要る点を裁定パッケージに明記する。**
どの案でも「roadmap の前提が RF では成り立たない」事実は変わらないので、**放置は選べない**
(現状は roadmap の文が RF にも適用されるかのように読める)。

## 追補 B — 「paired 差 floor」の paired 単位を取り違えると D19 の誤りを paired の衣で再演する

段 3 レンズ B は「floor は `d_j = m_stock,j − m_degraded,j` の散布から取れ」と述べたが、
**`j` が何を数える添字かで意味が正反対になる。**

- **(a) 1 allocation 内の interleave した rep 対**を `j` とすると、`d_j` の散布は
  同一 session の warm cache・同一熱状態・同一周波数定常を共有する。これは
  **within-run 散布の paired 版**であり、これを採否 floor に使うのは D19 が塞いだ
  「within-run floor を採否に流用して偽 faster を出す」経路と**同型**である。
- **(b) 独立 allocation ごとに 1 つの `d_j`** を作り、その **allocation 間**の散布を取ると、
  session 共通外乱が対で相殺されたうえで、run 間ドリフトは floor に残る。これが
  「差が信用できる下限」として正しい量である。

**したがって親の (P1) は (b) に限定して読むべきであり、必要な実験単位は
「独立 allocation を J 本」である** (1 allocation 内で rep を増やしても J は増えない)。
J = 8 で足りるかは点 ① の帰無分布と点 ② の多重性の裁定に依存する
(既存 8 session は CV 推定の相対 SE 約 27% であり検出力根拠ではない — レンズ B)。

**費用への影響:** (b) は「独立 allocation を J 本、各 allocation で全 arm を interleave」を要求する。
これは正例 artifact の実験計画そのものを決めるので、[T-139] の再走設計と直結する。

**親の実測 (2026-08-03):** 現存する唯一の 3 arm データセット
(`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/`) は
`run-<idx>-<workload>-<arm>-r<rep>.log` + `order.tsv` の形で、**1 job = 1 allocation の中に
5 rep 分の paired block が入っている**。すなわち **J = 1** である。
したがって現存データからは (b) の floor は**原理的に 1 つも作れない** (allocation 間散布の
標本サイズが 1)。点 ③ を (b) で裁定すると、正例 artifact は**新規の J 本走が必須**になる。

**追補 D — 「独立 allocation を J 本」は G12 と衝突する。ただし同じ問題を既存 floor が既に
解いた前例がある。**

- `docs/pegasus-runbook.md:432-434`: campaign の `isolation_policy` は
  **single_process=True / allow_resume=False** (G12 =「campaign を単一 allocation/node/process で
  完遂。途中 kill は全数値を不採用」)。2026-08-02 のレンズ B も blocker に
  「8 job 構成が Pegasus の single-process campaign 契約と衝突する」を挙げている
  (`output/insights/2026-08-02_t139-positive-control-probe/s3-lensB.md:129`)。
- **既存 unpaired floor もまったく同じ制約下にある。** `between_run_floor.py` の 8 session は
  1 process 内の back-to-back であり、docstring 自身が「fresh な back-to-back セッションは
  cold-boot/温度ドリフトを含まない**下限**」と認めている
  (`orchestrator/campaign/between_run_floor.py:16-17`)。
- **その解き方が既に確立している:** 「wired する floor は本値と cross-campaign の genuine な
  between データ (sweep vs repro、別時間窓) を突き合わせ**保守側 (最大)** に採る」
  (同 `:16-17`、`docs/roadmap.md` §3.6(3') 第 3 項)。wired 3.0% が実測 fresh 0.11〜1.07% より
  大きいのはこの手続きの結果である。

**帰結:** 点 ③ を paired で裁定しても、**J 本の独立 allocation を新設する必要は必ずしもない**。
既存と同じ二段構え —(i) 1 allocation 内の paired 差から fresh 下限を測り、(ii) 別時間窓の
genuine な paired データと突き合わせて保守側を wired 値にする— を踏めば、G12 を破らずに
追補 B の (a) の罠 (within-run 散布の paired 版をそのまま採否 floor にする) を避けられる。
**親はこの二段構えを (P1) の具体形として推す。**レンズはこの案が本当に (a) の罠を避けているか、
「保守側に採る」が恒真な言い訳になっていないか (どの数値と突き合わせるのかが未定なら
実質チェックされない) を攻撃せよ。

**追補 C — layer3 の floor kind は閉じた表である。**
`orchestrator/campaign/layer3_report.py:218` の
`block_for_kind = {"within_run": "noise_floor", "between_run": "between_run"}` は
floor の種類を閉表で持ち、同 `:231` は 1 つの calibration record が複数 kind の block を
持つことを `Layer3ReportError` で拒否する。**第 3 の floor kind を足す裁定は、この consumer の
閉表を広げる変更とセットでなければ成果物に出ない** (「gate を作っても誰も呼ばない」型の穴)。
