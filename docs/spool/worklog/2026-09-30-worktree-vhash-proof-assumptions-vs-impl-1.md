---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-vhash-proof-assumptions-vs-impl
seq: 1
title: [T-2906] VHash md_36: forwarding と GC 接続の論証が置いた仮定を Cicada 実装と試作のコードで照らした — 論文に「実装は仮定を満たす」とは書けない。構成 E では書き込み検査の走査中に止まる予定の版が回収されうる、stock の時刻は同じ thread で重複しうる、E の境界の読みは FS-b に対応しない (試作では thread 0 が抑える)。直列化の閉路の完成列は無い (insight のみ、branch worktree-vhash-proof-assumptions-vs-impl)
---

## 本文

- 依頼: 並行 VHash wave の md_36 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_36.txt`)。新規の計測・実装・モデル編集はしていない。対象 item は [T-2906] (完了) と [T-2907] で、[T-2907] は md_26 の wave (worklog (1974)) で開始 floor の条件 FS-a/b/c として完了済みだったので、本 wave では実装が FS-b を満たすかの照合に読み替えた。
- 正本: `output/insights/2026-09-30/vhash-proof-assumptions-vs-impl/README.md` (照合表、W* の非原子走査の列、FS-b と途中入場、時刻の重複、直し方と効き先、論文に書ける文・書けない文)。設計判断は {{D:vhash-proof-impl-correspondence}}。コードは試作 3 枚を pin 68106660 に fuzz 0 で当てた写し (repo 外 job dir `/work/1/SFC/tanab/tmp/vhash-proof-assumptions-vs-impl-2026-09-30/src/`) で読んだ。
- 段 1 の親の仮置きのうち 2 つを段 3 で撤回した: 構成 E の W* の列について「直列化は壊れない」(解放・再利用後の実行には論証の前提が当てはまらない)、時刻の重複を「(時刻, thread 内の順) の辞書順で無害化できる」(実装の比較・鎖の位置・検証がその順序を使わない)。
- 段 4 で親が境界の読みの列 G1 を書いた後、初稿の列の段 4 が矛盾する (W@40 が活動中に公開される MinWts は 40 以下) ことに気づき、試作では前進しない thread 0 が MinRts を MinWts_{r−1}−1 以下に抑えることを見つけた。これで段 2 の起草と段 3 相談 A の「同じ round で MinRts > MinWts」の列は試作では起きず、G1 はどの thread も前進しうる一般の構成 E の列になった。
- 段 6 のレビュー 2 本 (read-only codex) の所見はすべて real として親が直した。レンズ A は §4.3 の順序の一文の誤りと read-only の値破損の条件を、レンズ B は RC を「満たす」とした誤り (実装は PENDING を除く検査を持たない。stock と試作では floor の条件から導ける) と、列の非 RMW の条件・group commit の出典・A2 の一般化を指摘した。焦点再レビューは 2 巡使った。1 巡目 (NO-GO) は RC 行の新しい導出の書き漏れ (古い slot の読みと PENDING 版の設置時刻) と §3.2 の過剰な一文を、2 巡目 (GO) は不等号 1 か所 (< を ≤ へ、結論は不変) を指摘し、親が直した。
- 棄却した所見: なし。
- 実 repo を読む検査: 記録 commit の前に `python3 tools/check_docs.py` 違反なし、`python3 tools/spool_fold.py --dry-run` rc=0。受入は縮小受入 (D2316) を land の前に取る。
- エージェント工数: Codex plan 1・consult 2・review 2・focus 2 (いずれも gpt-6-sol、read-only)。実装子なし (実装面の差分ゼロのため変異 matrix は免除)。

## 次の一手差分

### 完了

- [T-2906] 仮定の照合を一次資料 `output/insights/2026-09-30/vhash-proof-assumptions-vs-impl/README.md` にまとめた。満たさない仮定の直し方は新規の item に分けた。
  remaining: none
  base: 198db926def245de7d3a32c4d79e22342c3aee3f57c5dce16bae907c3d692f4a

### 新規

- {{T:vhash-e-wscan-reclaim}} **P2・新規**: VHash の構成 E で、書き込み検査の走査中に止まる予定の版が回収される列 (md_36 一次資料 §3.2、計測した長い tx の update の key が既読でない場合に乗る) を除く規則を決めて試作に入れる。候補は書き込み key を持つ tx は floor を公開しない、公開値を書き込み key の直下の確定版の wts 以下に抑える、走査中の版の物理保護と検査のやり直し。前 2 つは長い tx の GC 改善を測り直さないと主張できない。根拠: `output/insights/2026-09-30/vhash-proof-assumptions-vs-impl/README.md` §3・§6。
- {{T:vhash-e-boundary-read}} **P3・新規**: VHash の構成 E の境界の読み (thread の floor が前進で上がり次の begin で下がる + leader の非原子な集計) を一貫した snapshot にするか、試作にある thread 0 の抑えを規則にして論証するかを決め、md_26 の FS-b・「GC: 境界を読む」の実装対応を書き直す。一般の E では既読版が回収される列 G1 がある。根拠: 同 §4・§6。
- {{T:cicada-ts-duplicate}} **P3・新規**: stock Cicada の時刻生成が、abort 後の上乗せが残ったまま次の tx が commit すると同じ thread の続く tx に同じ時刻を返す (A2) 頻度を trace で数え、thread 内で厳密に増やすかを決める。CCBench の挙動を変えるので D16 / D18 / D20 の分類が要る。根拠: 同 §5。
- {{T:vhash-impl-atomicity-lemma}} **P3・新規**: VHash の直列化の定理を Cicada の実行に当てはめるための置換補題 (観測の線形化点を最後に読んだ next pointer に置く、status の順次確定、論理版 ID と物理アドレスの分離、書き手側の記憶順序) を書く。根拠: 同 §2・§6。
- {{T:vhash-model-boundary-read}} **P3・新規**: VHash の小モデルに、GC の境界の非原子な読みと thread 内の floor の下降を足して、G1 と FS-b の列の witness を取るかを判断する ([T-2939] の途中入場とは別の軸。途中入場だけでは G1 は出ない)。根拠: 同 §7。
