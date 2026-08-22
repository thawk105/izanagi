# レンズ B（実効性・網羅性・scope）攻撃結果

前提として、単独段 dispatch の射影により読めるのは stage1 brief と stage2 plan のみです。したがって、以下の「独立再検証」は実ソース・grep の再実行ではなく、提示 artifact 内の引用と論理の敵対レビューです。実 repo の確認未達自体が stage2 の証拠上の欠陥です。

## 1. 安全判定 3 件

### `s8b_floor_campaign.py:5672-5687, 7075-7104`

提示された `run_campaign`/CLI 経路については、authority 検査が `_run_campaign_core` より前にあるため、working-tree-only mutation は拒否されるという主張を崩せなかった。

ただし、`_run_campaign_core` の全 production caller、wrapper 経路、別 CLI が同じ gate を必ず通ることまでは示されていない。もし別 caller が core を直接呼ぶなら、raw protocol の seed で schedule を生成できる。

- 暫定判定: **refuted（提示された主経路のみ）／全 caller 網羅性は未確定**
- 失敗シナリオ: gate を迂回する caller が working-tree の `floor_protocol.json` を読み、異なる `master_seed` の schedule を実行する。

### `s8b_ratified_freeze.py:1881-1884`

stage2 plan は `_capture_g_h_worktree` が G の git blob を返すと述べている。しかし、`1881` の `protocol` 引数がその blobから直接派生し、途中で raw worktree fallback や再読込みに置換されないことは、引用だけでは証明されていない。

- 暫定判定: **実装欠陥としては攻撃したが崩せなかった。ただし独立再検証は未達**
- 失敗シナリオ: G blob の取得後に `root / FLOOR_PROTOCOL_REL` を再読込みする分岐があれば、G は正しくても `build_schedule` は改変 seed を消費する。

### `s8b_holdout_admission.py:1222-1225`

plan の記述どおり、resolver の固定 commit blobと供給 protocolの byte-exact比較が `build_schedule` より前に行われるなら安全である。

ただし resolver 単体は working tree bytes と HEAD blob の一致を要求しない（`stage2-plan-output.md:19`）。したがって、比較の実行順序と、`1222` に渡る protocol が比較対象と同一 object であることが重要であり、planの引用だけでは完全には確認できない。

- 暫定判定: **実装欠陥としては攻撃したが崩せなかった。順序確認は未達**
- 失敗シナリオ: `build_schedule` 後に authority 比較を行う実装なら、改変 seed で一度 schedule を作った後に拒否するだけになり、下流の検証・副作用が先行し得る。

### `s8b_holdout_freeze.py:1362-1378, 1444-1447`

これは plan 内で raw working-tree 読込みが明示されており、real である。

`1376-1378` の canonical SHA 検査は、現在読んだ bytes 自身との整合性しか検査しない。HEAD の git blobまたは `receipt.source_commit` との byte-exact binding ではない。

- 暫定判定: **real**
- 失敗シナリオ: qsub 後に output 配下の `master_seed` だけを変更すると、`build_v2_g1_candidate`（`1715-1718`）が改変 protocol を読み、`1444` で別 schedule を生成する。

## 2. 網羅性

### `stage2-plan-output.md:34-51`

plan は「指定 grep の全 hit」と称しているが、次の問題がある。

- 表には `s8b_holdout_admission.py:1222` があるのに、grep hit一覧には同ファイルがない。
- exact literal grep は、別名定数、import された path、環境変数、動的な `Path` 構築による consumer を検出しない。
- `build_schedule` の全 caller の網羅性は、この grep だけでは証明できない。

失敗シナリオは、protocol path literalを持たない wrapper が raw path を組み立て、authority gateを迂回するケースである。

- 暫定判定: **real（網羅性の証拠不足）**
- 実装上の追加 consumer の有無は、射影制約のため未確定。

### shell consumer

brief は `tools/pegasus/floor_campaign.sh:1160-1186` の安全性を述べているが、stage2 planには要求された shell grep の結果がない。

- 暫定判定: **real（調査漏れ）**
- 失敗シナリオ: shell が別の `--protocol`、環境変数、または静的 output path を Python consumer に渡し、Python側の resolver経路を使わない。

## 3. 親実測の一般化可能性

### `orchestrator/tests/test_s8b_floor_campaign.py:_test_holdout_authority`

brief は scratch git repoによる実測だと明記している（`stage1-brief.md:16`）。その fixture が以下を再現している証拠は提示されていない。

- `external/ccbench` の gitlink 解決
- 複数候補 commit の曖昧性解消
- `env_tag` contract lookup
- 実 repo の receipt/source-commit 検証
- 実 production の caller graph

したがって、fixtureで拒否されたことから、実 repo の resolver 経路全体でも必ず拒否されるとは一般化できない。

- 暫定判定: **real（実測の一般化不足）**
- 失敗シナリオ: fixtureでは単一 HEAD blobが選ばれるが、実 repoでは候補選択や env_tag lookup が別 recordを選び、working-tree-only mutationの拒否条件が変わる。

## 4. scope 妥当性

### `stage1-brief.md:3-7, 21-26`

[T-647] を scope 外とする判断は妥当である。また CCBench/variant を無関係に変更しない方針も妥当。

一方、`production 変更は s8b_floor_campaign.py 系のみ`を文字どおり単一ファイル群と解釈すると、今回実際に問題化している `s8b_holdout_freeze.py:1362-1447` を修正できない。「系」に ratified / holdout / admission と shell callerを含むことを明記すべきである。

追加で scope に含めるべきなのは、次の実効性確認である。

- `build_schedule` の全直接・間接 caller
- shell経由の protocol供給
- `source_commit` と artifact署名・receiptのbinding
- holdout freeze の正当な reseal commitを通す正例

- 暫定判定: **real（scope境界の曖昧さ／過小 scopeリスク）**
- 過剰 scope: T-647、CCBench/variant、一般的な protocol refactor。
- 過小 scope: holdout freeze producer、shell bypass、動的 consumer、source-commit binding。

## 5. 影響評価

### `s8b_holdout_freeze.py:1362-1378, 1424-1425, 1444-1447, 1715-1718`

具体的な攻撃鎖は次のとおり。

1. generation commit C は protocol `P(seed=A)` を保持する。
2. qsub後、`output/` の dirty検査対象外領域にある protocolを `P'(seed=B)` に変更する。
3. `build_v2_g1_candidate` が raw working treeから `P'` を読み込む。
4. `build_schedule` が `P'` と整合する `expected_schedule` を生成する。
5. official floor result の `protocol_sha256`、`master_seed`、`expected_schedule` を `P'` と自己整合させ、source commit bindingがなければ、次世代 holdout freeze の証明鎖へ混入できる。

`1424-1425` の hash照合が official result と `P(seed=A)` のhashまで検査するなら、protocol変更だけでは拒否される。その場合、攻撃には改変 seed と整合する official resultの作成・差替え能力が必要である。しかし、raw protocolがgeneration commitに束縛されていない以上、artifact側の認証が弱い経路ではこの組合せが成立する。

影響はライブ campaign実行そのものではなく、holdout freeze producer と proof-chain の研究成果物の正しさに及ぶ。

- 暫定 severity: **High（証明鎖・研究成果物の完全性）**
- exploitability: **conditional**（official resultの真正性・source commit検証の強さに依存）
- 最低限でも、seed不一致による候補の誤受理・誤拒否、再現性破壊が発生し得る。

## 総括

| 指摘 | 暫定判定 |
|---|---|
| campaign主経路の authority gate | **refuted**（提示経路内。全 callerは未確定） |
| ratified freeze | **実装欠陥は未確認。独立検証未達** |
| holdout admission | **実装欠陥は未確認。比較順序の検証未達** |
| holdout freeze raw protocol読込み | **real** |
| Python grepによる網羅性 | **real（証拠不足）** |
| shell consumer調査 | **real（未実施）** |
| scratch fixtureの一般化 | **real（不十分）** |
| scope境界 | **real（`s8b_floor_campaign.py系`の解釈が曖昧）** |
| 影響 | **realなauthority gap。深刻度High、悪用性は条件付き** |