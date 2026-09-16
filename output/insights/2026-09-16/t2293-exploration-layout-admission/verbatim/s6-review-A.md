## 受理集合の同一性と anchor

**refuted — blocker 候補「仕様外の型を受理する」：該当なし。**

両 gate は plan-v2.md:29 の述語・例外文言と一致する。型判定は独立した2つの `is not` であり、等価比較・継承・属性の有無には依存しない。

- 内側：`orchestrator/campaign/reflux_result_evidence.py:447`
- 外側：`orchestrator/campaign/reflux_result_evidence.py:1219`

mutation-spec の `old` を現物と文字列照合した結果：

| 変異 | 出現数 | 開始行 |
|---|---:|---:|
| M1・M2・M3・M5・M6 | 各1回 | 447 |
| M4 | 1回 | 1219 |

指定 patch の全 hunk の適用後内容も、対象3ファイルの現物と一致した。

## 拒否述語の維持と負例の到達性

**refuted — blocker 候補「別層の拒否によって負例が恒真になる」：登録された内側変異では該当なし。**

| 入力 | 発行入口の拒否行 | projection 入口の拒否行 | 負例の定義行 |
|---|---:|---:|---|
| 両型の subclass | evidence:1223 | evidence:451 | unit:1226、1234 |
| frozen／namespace の duck object | evidence:1223 | evidence:451 | unit:1242、1250 |
| `str`／`Path`／`None` | evidence:1223 | evidence:451 | unit:1258、1266 |
| 両型に等価な metaclass impostor | evidence:1223 | evidence:451 | unit:1274、1282 |
| evidence root 外の exact 探索型 | evidence:1117 | 対象外 | unit:1289 |

ここで evidence は `orchestrator/campaign/reflux_result_evidence.py`、unit は `orchestrator/tests/test_reflux_result_evidence.py`。

発行負例は exact context を構築し、layout を事前検査しない helper から発行器を呼ぶため、外側 gate に到達する（unit:294、408、1184）。

projection 負例は外側 gate を通らず、内側 gate を直接検査する（evidence:539）。実 WAL の terminal prefix から digest を計算し、同一参照を正規 layout で先に成功確認する構造になっている（unit:1202）。WAL reader に layout 型拒否はない（`orchestrator/campaign/wal.py:1683`）。したがって M1／M2／M5 を後段の型拒否や digest 不一致が隠す構造ではない。

root 外負例は両 directory を作成し、loop を経由せず発行器を呼ぶため、`_context_roots` の包含検査が拒否地点になる（unit:1292、1309、evidence:1289）。M4 では拒否地点が外側型 gate に移り、M3 では包含検査が内側 gate より先に働く。

外側だけの型緩和は内側 gate に隠され得るが、その変異を登録しない plan-v2.md:62 と整合する。以上は静的判定であり、変異の実走結果は未検証。

## 規律 2 と差分の範囲

**refuted — blocker 候補「既存防壁の迂回・弱体化」：該当なし。**

production 差分は1ファイルの import、述語2箇所、注釈1箇所だけである（patch-author1.diff:3、12、28、38）。

context・capability・contract・receipt の検査、root 包含、WAL 検査、record 組立・導出 path 照合を経てから書き込む順序は維持されている（evidence:1215、1230、1289、1296、1380、1393、1399）。create-only の呼出しも未変更（evidence:1184）。

検疫・auditor veto・condition gate を迂回する production 経路の追加はない。

## テストの弱体化

**refuted — must-fix 候補「既存期待値・fixture の弱体化」：該当なし。**

既存正例の assertion を維持して official／exploration に展開しており、既存テストの skip 化、hash の差し込み、揮発 payload の追加固定はない（patch-author1.diff:111、unit:1321）。

探索単体正例は実際の `ensure()` を呼ぶ（unit:318）。worktree-container 検査と namespace 作成は残っており、これらの monkeypatch は差分にない（`orchestrator/campaign/layout.py:577`、580）。

**real — 検証範囲の留意事項。修正要求なし。**

新設統合正例は既存の trace runner と attestation probe の差替えを再利用するため、「依存先の差替えが一切ない」テストではない。ただし verifier・発行器・resolver を新たに stub 化してはいない（`orchestrator/tests/test_reflux_campaign_issuer.py:338`、350、550）。

既存 compiler helper の skip 条件も適用されるため、統合成功には実走結果の確認が必要（同:105）。skip を成功扱いできないという plan-v2.md:18 と整合する。

## 裁定整合と所有外

**refuted — blocker 候補「D2017／D1747／Q2〜Q4 への越境」：該当なし。**

D2044 項2の受理型追加と拒否条件の確定に収まっている。writer 認証の追加・保証の強化はなく、D2017 の「唯一 writer 性は運用前提」という上限を変えていない。consumer の canonical root 計算や schema にも変更はない（verbatim/D2017-D2018.md:17、verbatim/D1747.md:3、patch-author1.diff:1）。

提示 patch の変更先は指定3ファイルのみ。`acceptance_duration_ledger.json`、`p3_autonomous_workload_trial.py`、`reflux_formal_consumer.py`、`layout.py`、`loop.py` に差分はない（patch-author1.diff:1、54、319）。この判断は提示 patch の範囲に限定する。

## author 報告との食い違い

**refuted — 静的に照合できる変更内容・nodeid・件数の食い違い：なし。**

単体21 node と統合1 node、追加 helper 7関数、変更関数一覧は現物と一致する（author-1.md:14、39、44、unit:1132、issuer:546）。既定 official と `_drive_campaign` の既存呼出し関係も一致する（issuer:401、536、804）。

**unverified — 実走履歴と射影外の波及調査。**

34ケースの直接実行、メモリ上変異の結果、runner の rc=16、build guard による停止は、報告には記載されているが、提示資料に実行ログがなく独立確認できない（author-1.md:18、25、27）。所有外参照の検索結果と consumer 全体への影響も、この射影からは独立確認できない（同:32、35）。

author は統合成功・pytest 全走・完全な変異全走を主張しておらず、その点の食い違いはない。

## 総括

静的レビューでは **blocker 0件、must-fix 0件、nit 0件**。受理集合、拒否条件、変更範囲は plan-v2 と整合する。

テスト・変異は本レビューでは実行していない。統合到達性と完全な変異結果は **unverified** として、親の実走確認に残る。