前提資料・一次裁定・起票文はすべて読了した。現行 worktree は `HEAD=b9c7a534...`、clean。実測値は以下を基準にした。

- `wc -c`: core 8,655 / workers 4,526 / mutation 3,689 / operations 8,329
- section slicer: L1 10,625 / L1.5 9,566 / L2 5,008（13節）
- 理論値: `10,625 + 9,566 + 13×1,000 = 33,191 bytes`
- 旧 aggregate 25,200 比で +7,991 bytes

### 1 / blocker

対象: `s1-brief.md:49-51`、`s2-plan.md:98,174,194,197`、`docs/skill-self-improvement.md:30-33`

実測: 現行13節だけなら最大は33,191 bytes。L1+L1.5 は20,191 bytesなので、L2節数を `N` とすると受理上限は `20,191 + 1,000N` になる。

なぜ壊れるか: `s2-plan.md:174` は「L2節を各1,000 bytes以下で追加し、registry/dispatchも整合更新」すれば緑としている。さらに節数上限を置かない。したがって33,191 bytesは13節固定時の数値にすぎず、将来の実効上限はない。

これは一次裁定の「全体固定上限を撤廃」とは整合するが、「無制限には増えない」ための発火実績・機械的義務代替の歯止めが新規L2追加へ伝播していない。`[T-664] R5(a)` の「入らない候補は見送りで確定」も、L2として再登録すれば回避できる。

提案: 本 wave では既存13 IDだけを対象に固定し、新規L2 IDには routing 3 の証拠、機械検査による義務代替、ユーザー裁定を要求する。`[T-577]` の見送り候補を再登録できない tombstone も必要。

### 2 / major

対象: `s1-brief.md:81-85`、`s2-plan.md:12-16,172-186`、`output/insights/2026-08-08_t664-docs-budget/package.md:74-88`

実測コマンドは `rg` による `docs/worklog.md`・`docs/archive/`・`docs/failures.md`・`docs/decisions.md` の byte/予算記録検索と、現行節 slicer。結果は次のとおり。

| 記録 | 必要量・対象 | 新 gate の判定 | 評価 |
|---|---|---|---|
| T-279 A2 | 163 bytes / `DW-O01`（L1.5） | `9,566+163` で停止 | ただし現行O01に同じ foreground wrapperがあり、T328裁定は部分 stale |
| T-279 A3 | 154 bytes / `DW-O20`（L2、現489） | `489+154=643≤1,000` で通過 | 裁定どおりの解放。防壁後退ではない |
| T-345 A7 | 99 bytes / `DW-S03`（L1.5） | `9,665>9,566` で停止 | L1.5固定どおり |
| T-346 A8 | 134 bytes / `DW-S01`（L1） | `10,759>10,625` で停止 | L1固定どおり |
| T-317 A9 | 147 bytes / 計画位置は`DW-S01`（L1） | `10,772>10,625` で停止 | ただし代替位置`DW-O19`なら `602+147=749` で通過。配置が未確定 |
| T-341(c) | 63 bytes / `DW-O01`（L1.5） | 停止 | `docs/archive/worklog-phase3-0803-134.md:88-94` |
| T-491 | 177 bytes / `DW-S09`（L1） | 停止 | `docs/archive/worklog-phase3-0805-210.md:298-306` |
| F146 | `DW-S06-C`への追記。残余13 bytes、本文長は未記録 | L1.5は正の追加を全て停止 | `docs/failures.md:3547-3563` |
| F161 | `DW-S06-B`への追記。残余4 bytes、本文長は未記録 | L1.5は停止 | `docs/failures.md:3936-3954` |
| `DW-M01`恒久文 | 1文、正確なbytesは未計測 / L1 | 正の追加なら停止 | `docs/failures.md:4093-4095` |
| T-648 | 1文、正確なbytes・対象節は未計測。`DW-S04`想定は推測 | L1なら停止。実際はfallbackで本文未編集 | `worklog-phase3-0809-326.md:3-16` |
| T-550 | 1文、正確なbytesは未計測。例示先`DW-G01`はL1 | L1なら停止。`docs/decisions.md`記録は可能 | `package.md:139-160` |
| T-665/T-662 | 最小91 bytes実測、案A 400–700 / 案C 800–1,200は概算。`DW-O01`（L1.5）・S09（L1） | いずれも停止 | `verbatim/s2-plan.md:304`、package `:13-17,82-89` |
| T-412 | L2剪定候補0 bytes | 判定対象なし | R1(a)どおり |
| T-454 | 回収0 bytes | gateでは解決しない | R4記録どおり |
| T-577 | 必要bytesは現資料に記載なし | 数値ではなく見送り | R5(a)どおり |

[T-328] 全候補は1,463 bytes必要だが、実際に新 gateで通るのはL2へ置けるA3と、A9を`DW-O19`へ置く場合だけである。L1/L1.5側の従属項目やT-665/T-662/T-648/T-550は、実装後も書けない。

提案: `DW-G05` の効果主張を「T-328系のL2部分だけを解放」に修正する。L1/L1.5項目はfallback・台帳へ戻し、L2へ移すことを解決策として扱わない。

### 3 / major

対象: `s1-brief.md:49-51`、`tools/check_docs.py:176-181,254,3561-3565,3704-3709`

実測:

- `operations.md = 8,329`
- 現行 file cap = 8,400
- 残余 = `8,400-8,329=71 bytes`
- `DW-O04` に計画どおり72 bytesを足すと8,401で旧file capを超える
- operationsの内訳は、hot部分3,321 bytes + L2 5,008 bytes = 8,329

なぜ壊れるか: P1の「file capを残すとL2が実質解放されない」は、O04の72 bytesやO20の154 bytesには当たるが、「第三の道がない」という証明ではない。

提案: ファイル自体は維持し、file capをL1/L1.5のhot sliceだけに適用する。L2 sliceは各節1,000 bytes capだけにする。これなら現行file capの形状保護を残しつつ、`DW-O20`の154 bytesも通せる。ファイル移設ではないため、D94のファイル再編却下とも別物である。

### 4 / major

対象: `docs/archive/worklog-phase3-0802-106-110.md:372-375`、`s2-plan.md:104-106`、`.claude/commands/dev-wave.md:16-17`、`docs/dev-wave/core.md:114-124`

実測:

- 入口には「外部 supervisor が最初の `claude -p` 前に `DW-CTX` を読む」とある。
- `rg -n 'DW-CTX|docs/dev-wave/core\.md' tools/dev_waves/daemon.py tools/dev_waves/worker.py` は該当なし。
- T328裁定も `daemon.py` / `worker.py` に読取処理がないと記録している（`s4-adjudication.md:69`）。

なぜ壊れるか: wave開始表から`DW-CTX`を外す変更は、重複したdispatch edgeの整理には効く。しかし、実際の外部 supervisor がその節を読まない問題は残る。P4の「本文分割をしない」はscope限定としては妥当だが、「読み動線を直す」という起票目的を解消してはいない。

`DW-O04`は条件04と段5/6の条件行が残るため、段8行を落とす修正自体は有効である。

提案: 本 waveの成果を「DW-CTXの分類重複除去」に限定し、実読取の結線は別タスクに分離する。全体を解消したと報告しない。

### 5 / major

対象: `s2-plan.md:40-72,112-164`

実測: 計画は typed U/C map、flatten view、condition trigger、registry照合、literal layer key、raw section slicer、8個の変異候補を同時に導入する。一方、現行dispatchでは次の正当な多重参照がある。

- `DW-CTX`: 段9 + 条件21 + 条件22
- `DW-O04`: 段5 + 段6 + 条件04（現状は段8も重複）

なぜ壊れるか: 計画は集合の両方向照合とU優先を示すが、同一 `(path, ID)` が複数のstage/condition edgeを持つ場合の合法性を定義していない。集合へ潰せば重複を検出できず、逆にowner exactly-oneとして実装すれば、`DW-CTX`や`DW-O04`の正当な共有参照を誤拒否する。

提案: edgeを `(stage/condition, mode, path, ID)` 単位で保持し、共有参照の許可表を明示する。typed map・flatten view・layer導出はそのedge表から導出する。これによりpinの二重化を減らし、O04/CTXの正例テストを追加できる。

### 6 / nit

対象: `docs/skill-self-improvement.md:30-33`、`s2-plan.md:110,197`、`tools/check_docs.py:4011-4031`

実測: routing 3 のL2削除条件「発火実績なし × 機械検査で義務代替済み × ユーザー裁定」は、self-improvement本文に残っている。`[T-664] R1(a)`もL2候補0であり、本 waveは削除を計画していない。

ただし `rg -n '発火実績|義務代替|L2.*削除' tools/check_docs.py orchestrator/tests/test_check_docs.py` は該当なし。checkerが検査するのは見出しで、条件意味までは機械固定していない。

なぜ壊れるか: 現 waveの裁定未実装ではないが、将来のL2追加・削除に対する機械的歯止めはない。これは所見1の新規L2 admission欠落と結び付く。

提案: 本 waveではself-improvement本文を変更しないままでよい。ただし新規L2 IDの登録条件にrouting 3の証拠を要求する。

### 7 / nit

対象: `s1-brief.md:25`

実測: briefは実測基準を`@34957a24`と記載するが、現在のworktreeは`HEAD=b9c7a534...`。bytes自体は現行worktreeでも一致した。

なぜ壊れるか: 値が一致しているため直ちに判定を誤らないが、測定 provenance は一致していない。

提案: 実装直前に現行HEADで再計測し、layer pinの基準commitを更新する。

判定: **NO-GO**

## 総括

- 新規L2節をregistry/dispatch整合だけで追加でき、33,191 bytesは現行13節にしか有効でない。
- T-328系・T-665/T-662等の大半はL1/L1.5固定に当たり、実装後も書けない。
- DW-CTXはdispatch整理にはなるが、実際の外部supervisor読取欠落を解消しない。
- raw file capをhot slice限定で残す第三の道があり、全面撤去の費用対効果は未立証。