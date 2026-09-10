# [T-2049] B-4 材料レポート生成器と正規コマンド — 一次資料

wave `dev-wave-t2049-b4-report-generator`、branch `worktree-dev-wave-t2049-b4-report-generator`。
base commit `24014bdb2`。2026-09-01。

`verbatim/` に段 1〜6 の全成果物 (brief、plan、敵対相談 2 本、裁定、実装子報告、
敵対レビュー 2 本、fix 2 巡) を逐語で置く。変異の spec と report は同 directory 直下に置く。

## 成果物

- `orchestrator/campaign/p3_b4_material_report.py` (新規、1306 行)
- `orchestrator/tests/test_p3_b4_material_report.py` (新規、865 行、41 node)

既存 file は 1 byte も変更していない。分析 source closure
(`p3_b4_analysis_path.py` の `_SOURCE_CLOSURE_PATHS` 5 file)、事前登録文書、
raw 試行記録 producer、`layer3_report.py` のいずれにも触れていない。

## この wave が埋めたもの

`p3_b4_analysis_path.py` の docstring が自ら「authoritative artifact producer, sanctioned command,
durable writer, report generator, certified-selection connection は scope 外」と明記している 5 語の
うち、**report generator と sanctioned command の 2 つ**を埋めた。
producer と durable writer は 2026-08-29 の wave が埋めている。
**残るのは certified-selection connection の 1 語だけである。**

## 正規コマンド

```
python3 orchestrator/campaign/p3_b4_material_report.py PUBLICATION_ROOT [--output-root PATH]
```

publication root だけを入力に取り、判断値を caller から受け取らない。既存 API
(`load_b4_prerun_publication` → `assemble_b4_raw_analysis` → `build_contract_binding` →
`evaluate_b4_artifacts`) の合成に限り、新しい分析規則を作らない。
qsub、build、性能測定、campaign 実走への入口は持たない。
計算ノード投入器の exact path 許可リストには載せない (計算ノードへ何も投入しないため)。

出力は `report.json` (機械可読の完全射影)、`report.md` (人間可読の決定論的な表)、
`report.complete` (両者の hash を持つ公開完了 marker) の 3 file である。

## この wave の正直な到達点

**分析 verdict は `protocol_violation` にしかならない。** 事前登録 §5 の `floor` 欄が
1 欄も埋まっていない (D1060) ためである。事前登録は `floor` を「§5 の凍結 artifact から
読んだ値」と定めており、生成器が CLI 引数や既定値でこれを埋めることは、caller の自己申告を
凍結値の位置へ入れることになる。したがって埋めない。

**本 wave は事前登録 §7.1 の 4 分類を実効化したとは主張しない。**
正規経路で到達する分類は 1 つである。レポートはこの事実を機械可読に宣言する。
4 分類を実効化するには権威ある floor artifact の発効が要り、それは別 task である。

## 実測 (親が実走した値)

| 走 | 内容 | 結果 |
|---|---|---|
| 段 1 生死確認 | `test_p3_b4_raw_record_producer` + `test_p3_b4_analysis_path` | 46 passed / 28.44s |
| 段 6 焦点走 1 | 段 5 実装子の成果物 | 9 failed / 19 passed / 39.21s |
| 段 6 焦点走 2 | fix1 適用後 | **40 passed / 98.49s** |
| 一覧検査 | plain_runner_coverage / campaign_import_invariant / pytest_collection_config | 103 passed / 6 skipped / 76.03s |
| 段 6 焦点走 3 | local main を 76 commit 取り込んだ後 | **40 passed / 87.91s** |
| 段 6 焦点走 4 | fix2 適用後 | **41 passed / 88.37s** |
| 変異 本登録走 | baseline | rc=0 / 103.817s |

正式 B-4 実走、qsub、性能測定、build は**行っていない。**

## 変異 matrix

`DW-M07` の契約 (probe -> 中間 -> 本登録) に従って回した。spec と report は同 directory に置く。

### 最終結果 — 最終 commit `7a14171f5` に対して KILLED 20 / SURVIVED 7 / MISMATCH 0

fix3 (`5e28090e0`) がテスト側の順序依存を断ち node が 1 件増えたため、
fix3 と記録を含む最終形に対して probe と本登録をもう一巡した。
変異 harness は untracked file があると走らないので、記録 commit を先に置き、
本走後の raw 台帳を後続 commit へ収める順序にした
(`DW-O19` の「本走後の raw 台帳は後続の記録 commit へ置く」)。

| 走 | spec | 対象 commit | 結果 |
|---|---|---|---|
| probe3 | `mutation-probe3-spec.json` | `7a14171f5` | baseline rc=0 / 114.301s、検出 20 / SURVIVED 7 |
| **本登録 (最終)** | `mutation-registered2-spec.json` | `7a14171f5` | **baseline rc=0 / 118.981s、KILLED 20 / SURVIVED 7 / MISMATCH 0 / matching 27** |

**生存 7 件は fix3 の前後で同一である** (M05 / M06 / M07 / M10 / M13 / M21 / M22)。
冗長 gate という裁定は fix3 後も維持できる。

### fix3 より前の commit `ee13b00c7` に対する結果 (経過の記録)

| 巡 | spec | 結果 |
|---|---|---|
| probe (1 回目) | `mutation-probe-spec.json` | M03 で `PARSE_ERROR` 停止。下記「停止した 2 回」参照 |
| probe (2 回目) | 同上 | 23 件完走、18 件検出、**5 件 SURVIVED** |
| 中間 (1 回目) | `mutation-intermediate-spec.json` | 期待 node の実在検査で停止。下記参照 |
| 中間 (2 回目) | 同上 | 27 件完走、KILLED 18 / SURVIVED 7 / MISMATCH 2 |
| **本登録** | `mutation-registered-spec.json` | **KILLED 20 / SURVIVED 7 / MISMATCH 0 / matching 27、baseline rc=0** |

anchor は 27 件とも対象 file 内で厳密に 1 回だけ出現し、`old != new` であることを
親が投入前に機械検査した (`bad=0`)。巡ごとに変えたのは期待値と、下記 2 件の是正だけである。

### SURVIVED 7 件は穴ではなく冗長である — 両層同時変異で裏取りした

probe で生存した 5 件 (M05 件数 gate、M06 全単射 gate、M07 往復 gate、M10 一致方向、
M13 実体 path 比較) について、親は「隣接する層に mask されている」と仮説を立て、
両層同時変異を事前登録して裏取りした (`DW-M02`)。

**結論 (7 件を単独 gate の証拠から外す) は妥当だが、親が最初に書いた因果の説明は誤りだった。**
段 6 の焦点再レビューがこれを指摘し、親は訂正した。訂正前の主張と訂正後の事実を両方残す。

| 両層変異 | 実測 | 親の当初の説明 | 訂正後の事実 |
|---|---|---|---|
| M21 (件数 + 往復) | **生存** | 「第 3 層が拾う」 | 正しい。行不足は identity 集合の件数検査が、source 改変は各 source の照合が拾う |
| M22 (全単射 + 同一性) | **生存** | 「第 3 層が拾う」 | 正しい。行ごとの序数・planned path の位置照合が複製を拒否する |
| M23 (一致 + 配下) | **検出** | 「M10 が配下方向に mask されていた証拠」 | **誤り。**実際の赤は `[below]` node と symlink node で、`[equal]` は落ちていない。赤の一次原因は配下 gate の除去であって M10 の露出ではない。M10 を露出させるには一致・配下・祖先の三層を同時に外す必要がある |
| M24 (字面比較 + 配下) | **検出** | 「M13 が配下方向に mask されていた証拠」 | **誤り。**一次赤は配下 gate の除去である。比較箇所の resolve は、output と campaign root が既に解決済みであるため冗長で、M13 の効果は現れていない |

**したがって M23 / M24 は M10 / M13 の mask 仮説を実証していない。**
「KILLED 20 / SURVIVED 7 / MISMATCH 0」は登録 spec との一致としては正しいが、
M23 / M24 の意味づけをこの矢印で語ってはならない。

そのうえで、5 件を単独 gate の証拠から外す結論自体は静的根拠で支持される。
完全射影の oracle は、件数・同一性による全単射・行ごとの field 照合・往復 bytes・
hash 一意性という重なり合う不変条件を持つ**過剰決定**の検査であり、
出力先 guard の一致・配下・祖先も互いを包含する。単独の層を外しても別の層が拾う。
**これは穴ではなく強さである。**ただし単独変異では帰属できないため、
`DW-M03` に従い**冗長 gate と明記して単独変異の証拠から外した。**

### 落ちる node 数 (帰属の一意性)

射影 gate の変異 (M03、M04、M14、M18) は 16〜17 node に落ちる。共有 document を多数の test が
使うためである。ただし**赤の理由は変異ごとに一意**であり
(`projection_value_mismatch: derived row 1 field <X> differs` の `<X>` が異なる)、
`DW-M08` が求める「期待 node の完全集合との完全一致」で帰属を固定した。
他の 16 件は 1〜3 node に落ちる。

### 停止した 2 回と、その扱い (正直に記す)

- **probe 1 回目は M03 で `PARSE_ERROR` 停止した。** 変異は正しく発火していたが、その gate の
  呼び出しが module-scope の共有 fixture の中にあったため pytest が `ERROR at setup of ...` を出し、
  変異 harness の node 抽出が `FAILED ` 行だけを読むため 0 件になった。
  **kill されているのに単一 node へ帰属できない状態**であり、`DW-M01` の要求を満たせない。
  fix2 で fixture の責務を分け、機構の呼び出しを test の call 段階へ移して解消した。
- **中間巡 1 回目は期待 node の実在検査で停止した。** 並列実行の group 名が失敗行の nodeid へ
  接尾辞として付く一方、`--collect-only` の nodeid には付かないため、期待 node をどちらの形で
  書いても片方の検査が必ず外れる。runner を直列 (`-n 0`) にして接尾辞そのものを消して解消した。
  元々 group で 1 worker に固定していたので所要はほぼ変わらなかった (98.49s → 103.8s)。
  **変異の内容は 2 回とも変えていない。**

## 段 3 と段 6 で独立 2 レーンが一致した所見

段 3 (plan への敵対相談) で 2 件が独立に一致した。

1. **正規経路から 4 分類のうち 3 分類が到達不能である。** 機構は変えず主張を狭める裁定にした。
2. **出力先 guard が path alias と祖先方向を閉じていない。**

段 6 (実装への敵対レビュー) でも最重要欠陥が独立に一致した。

- **共有 fixture が producer の再導出を通らず、正常経路を通る node が 0 件だった。**
  fixture が一時的な repository root / role file path の patch の内側で証拠を publish し、
  patch が戻った後に再導出したため、内容と hash が同じでも
  `evidence.transitive_evidence[*].path` の UTF-8 bytes が食い違って組立てが拒否されていた。
  **19 件の緑は拒否経路だけを見ていた。**

## 親の裁定が実測で覆った 2 件 (記録)

- **(P2) CLI `--floor` 引数**: 親の段 1 brief は「CLI 必須引数 + 出所記録」を provisional 裁定に
  していたが、段 3 の 2 レーンが独立に自己矛盾を指摘した。brief 自身が「判断値を caller から
  受け取らない」と書いており、事前登録も floor の出所を凍結 artifact に限定している。
  **親は裁定を撤回した。**
- **段 1 の一般化**: 「46 passed = producer から分析判定までの経路が生きている」は広すぎた。
  fixture は 1 block の real seed と 200 block の複製で、evaluator には test caller が
  `floor=0` を注入している。正規経路の `floor=None` とは別物である。**親は限定を受け入れた。**

## 段 6 レビューが見つけた実在欠陥 (すべて fix で閉じた)

| 所見 | 内容 |
|---|---|
| sol F1 / luna F1 | 正常経路を通る node が 0 件 (上記) |
| sol F2 | artifact 在否の二重観測で report 全体が消えうる |
| sol F3 | 完全射影検査が自己 oracle で恒真。登録変異 1 件が候補集合に含意されて恒真 |
| sol F4 | campaign root が不明なとき output guard が fail-open |
| luna F2 | **campaign root を `runs/` と誤認していた。** WAL は `<campaign-root>/runs/wal.jsonl` にある |
| luna F3 | 2 成果物の公開が原子的でも durable でもない |
| luna F4 | Markdown が出力規約 (provenance と再現コマンド) を満たさない |
| luna F5 | standalone 起動で test file が import に失敗する |

luna F2 は親が `orchestrator/campaign/layout.py:203-208` で独立に確認した。
この誤認があると `<campaign-root>/任意の名前` が三方向検査を素通りし、
campaign root 配下の完全性検査 (`autonomous_trial_completeness.py:3317-3336,3379-3385` が
`rglob("*")` で全列挙し厳密一致を要求する) を実際に赤にできる。

## 閉じられないと確定したこと (非保証として実装に列挙)

- **権威ある floor artifact が無い。** 事前登録 §5 が発効するまで、正規経路の分析 verdict は
  `protocol_violation` にしかならない。
- **producer の rejection が永続化されていない。** publication root だけを入力とする consumer は、
  過去の rejection を完全には復元できない。レポートが報告できるのは生成時点で観測した
  在否と拒否理由までである。file-drawer を機械的に閉じきるには producer 側の
  durable rejection ledger が要る。
- **certified-selection connection は未実装である。**
- 事前登録 §7.1 が要求する 11 項目のうち **model hash と予算消費は現行 artifact に存在しない。**
  捏造せず「不在」として載せている。`anomaly_class` も存在せず、代わりに置ける
  `precursor_digest_red_classes` は処置割当て**前**に記録された別概念なので、
  同名識別子を二義化せず補助 field として別名で載せている。
- `initial_proposal_sha256` は registry に実在するが、それを計算・記録する経路が repo に無いため
  **束縛は転記に留まる。** 値は載せたうえで `binding: "transcribed"` と非保証を同じ行から辿れるようにした。

## 使用した子 (`receipt.json` schema v5、全件 `accepted`)

| 段 | stage | model | effort |
|---|---|---|---|
| 2 | plan | gpt-5.6-sol | xhigh |
| 3 | consult x2 (sol / luna) | gpt-5.6-sol | xhigh |
| 5 | author | gpt-5.6-sol | xhigh |
| 6 | review x2 (sol / luna) | gpt-5.6-sol | xhigh |
| 6 | fix x2 | gpt-5.6-sol | xhigh |
| 6 | focus (再レビュー) | gpt-5.6-sol | xhigh |

codex-cli 0.151.0。
