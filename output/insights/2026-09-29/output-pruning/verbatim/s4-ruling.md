# 段 4 裁定 — dev-wave-output-pruning (2026-09-29 17:4x〜18:1x JST、親)

入力: 走査 3 回目 (scan/、2,287 秒)、分類 v5 (config-v4)、段 3 レンズ A (s3-lensA.md) / レンズ B (s3-lensB.md)、親の追加実測。

## real / refuted

| 所見 | 判定 | 処置 |
|---|---|---|
| A-O1/O2: 上位 40 root に高確信度の B は無い (生ログが判定証拠・事前登録対象・他資料の参照先) | real | b_roots は空。第 1 段の B は親が本文照合した t2668 の device probe 2 件だけ |
| A-O3: 保護語が root 名から全子 file へ波及 (certif 179/190、witness 197/232、provenance 177/211、oracle 113/118) | real | 第 1 段では規則を広げない (広げた分は再照合が要る)。次段の走査器で root 以下の相対 path に当てる |
| A-O4: blob 重複 5,462 余剰 path の大半は守る証拠の中 (最大は t361-t362 の 0 byte raw 2,118) | real | 重複だけを削除理由にしない |
| A-O5 / O6: 自 root manifest の hash 束縛・t361 evidence・t2817/t2243 の probe-ledger 列挙は依頼の明示条件に当たる | real | 第 1 段で外さない。次段候補として効果を実測し一次資料に載せる |
| A: C を root 丸ごと外すと「README.md は外さない」と両立しない | real | C は第 1 段 0 件。t2447-lens-p2-p6 を低確信度の次段候補に記録 |
| B-F1: A の gz 44 file は README が gz 化前の名前で引く (走査器の穴) | real (親も独立に実測: gz 化前 basename が md 58 本に出現) | A の gz 75 件を全部 D |
| B-F2〜F4: spec・ledger・正例負例・正規化記録・提出/予約記録・pin 証拠が A に混入 | real | 名前・root で D |
| B-F5: `{1,2}`・`before/after/x` の束表記を走査器が展開しない | real | 残り A を同 root md の stem で照合し、当たれば D |
| B-F6: 大文字 hex・連結 path・binary 内参照 | 限界として記録 (A への実例なし) | 動的 reader の root 保護を維持 |
| B-F7: layout-index は現行案内 | real | 第 1 段では layout-index も t361 raw も触らない |
| B-F9: 索引は規律 7 を満たすが README の旧名参照は索引経由の案内が要る | real | 第 1 段の 6 件は README から名前で引かれていないので README 追記は不要。output/README.md に索引の 1 行 |
| 親の追加実測: 2026-09-10 の配置移行 (588 dir) 前の docs 引用は旧 path (`<date>_<name>`) のまま。走査器は旧 path を新 root に対応づけない | real | 残り A を旧 path でも照合し、root が旧 path で引かれていれば D (t190・pegasus-compute-node-dispatch・t627・t678) |
| 親の追加実測: t1795 `dogfood-attempts.json` は README が「本 wave の中心的な証拠」と名指し (file 名ではなく概念で) | real | D。名前照合だけでは足りないので残りを README 本文で照合 |
| 親の追加実測: t2686 README「原 job 資料も保持する」、t2780 は復旧が主題 | real | D |

## 採否

- 第 1 段で外す: 6 file (A 4 = t180 の投入 prompt 3・token-hygiene の verify prompt 1、B 2 = t2668 の device probe 出力)。
- 索引: output/PRUNED-INDEX.jsonl (path・blob・size・最後に存在した commit・分類・理由)。output/README.md に 1 行。
- 次段候補 (外さない、効果だけ実測): 自 root manifest だけが sha256 を持つ機械出力 2,996、t361-t362 evidence (事前登録の dir 引用) 3,179、t2817 / t2243 (probe-ledger 列挙) 1,374、計 7,549 (+第 1 段 6)。
- 効果測定: 基準 c0bcf1abb vs 仮 commit c7bfccd7b (次段候補 7,549 を外した tree、branch output-pruning-measure-hypo、着地させない) と、基準 vs 第 1 段 commit 535d6d221 を同時刻に 3 巡。

## 変異事前登録

実装面を repo へ入れないため、変異 matrix は無し (走査器・分類器・索引生成器は repo 外の使い捨て道具で、各規則の変異は Codex 子の selftest が確かめた)。
