# B-4 対照対 driver を候補と参照の 1 session 形へ直す — wave の逐語と変異台帳

D1699 に従い `orchestrator/campaign/floor_pair_driver.py` の対照対測定を、
候補と参照が 1 つの低水準 session に入る形へ直し、reference の個数と D の式を凍結した wave の
一次資料。裁定は D1699、凍結項目は D1641 第 3 項、driver の初版は T-2166。

**この wave は bench を 1 度も実走していない。** 性能値を新規取得していない。
変更したのは測定手順の構造と凍結項目だけである。

## 何を直したか

D1699 は、役割ごとに別 session で測る 3 role (`candidate_1` / `candidate_2` / `reference`) を
却下し、候補と参照を 1 つの低水準 session で測る形を命じた。理由は、役割ごとに別 session で
測ると候補と参照の比が走行間のドリフト帯を跨ぐことである。B-4 は床値の主張なので、
この比が主張の根拠になる。

1 pair-sample を独立した 2 つの side session とし、各 side session は 1 つの区間の中で
候補と参照を各 1 回測る形にした。区間は次のとおりで、**3 つの probe がすべて clear のときだけ**
その session を complete とする。

```
事前 probe -> 測定 -> 中間 probe -> 測定 -> 事後 probe
```

`D = abs((median(candidate_1)/median(reference_1) - 1) - (median(candidate_2)/median(reference_2) - 1))`
とし、分母を side ごとに分けた。reference の測定は pair-sample あたり exact 2 件である。

凍結は spec の `statistics` へ `reference_measurements_per_pair_sample` と `difference_formula` を
必須 field として置き、loader が module 定数との exact 一致を要求する形にした。
値の意味が変わるので spec / plan / window / summary の 4 schema を上げた。

## 「1 つの低水準 session」をどう読んだか — 段 3 の指摘を却下した理由

段 3 の敵対相談は「2 回の `measure_point` 呼び出しを 1 つの probe 区間で包んだだけであり、
D1699 が却下した『複数の低水準実行を上位の組として同一 session と呼ぶ』読み替えの再実施である」
と指摘した。**親はこれを却下した。**

根拠は現物である。`runner.measure_point` は `reps` 回の loop を回し、**各 rep を別 process として
spawn する** (`orchestrator/calibrator/runner.py:1122` の `for index in range(reps)`、
docstring も「Each rep is spawned, decoded, parsed, and cleaned before the next rep is started」
と明記)。したがって**この repo で「1 低水準 session」が「1 process」を意味したことは一度も無い。**
現行の 1 role session ですら 5 process の spawn 群である。所見の判定基準を適用すると
「現行 driver には低水準 session が 1 つも存在しない」ことになり、背理となる。

この driver における session の実体は **admission probe に挟まれた 1 区間**であり、
そこへ候補と参照を入れる形は D1699 の逐語を満たす。D1699 が却下したのは
**別々の session で測ったもの**を組だから同一と呼ぶ読み替えであり、今回は別々の session を
作らず 1 区間 1 record へ統合している。呼び名の変更ではなく実行構造の変更である。

**ただし残余は real として認めた。** 区間内で候補の全 rep が参照の全 rep に先行するため、
区間内ドリフトは相殺されない。rep 単位で交互に測ればより強く相殺できる。これは D1699 が
要求しておらず、D1641 §11.1 が測定手順の決定主体をユーザーに置いているため実装せず、
裁定パッケージへ回した。

## 段 3 が正しく暴いた、実装前に閉じた欠陥

**3 session を 2 session にすると、競合を検出できない窓が広がる。** 現行なら候補と参照の境界で
検出できた競合を新設計は取り逃す。これは既存の正しさゲートの弱体化であり規律 2 が禁じる。
そこで**区間の中間に probe を残した**。pair-sample あたりの probe 数は 6 個のままで
(2 session x 3 probe = 6、現行は 3 session x 2 probe = 6)、検出力を維持するだけで
新しい gate は足していない。

## 段 6 が正しく暴いた、緑のテストが守っていなかった穴

**spec の schema 不一致を拒否する検査に負例が 1 件も無く、検査を削除してもテストが 1 件も
赤にならなかった。** 全 fixture が module 定数を参照していたためである。本 wave は 4 つの
schema 識別子を上げ、版の識別を成果物の意味を分ける唯一の手段にした。その版の検査が
効いていないのは穴である。spec / plan / window の 3 つについて、構造は新版のまま schema 文字列
だけを旧版にした document を拒否する負例を足した。**期待値は module 定数から導かず literal で
書いた。** 導くと恒真になり検査にならない。

summary は生成するだけで loader も再検証器も無いため、拒否の負例を書く入口が無い。足していない。

## 段 6 のもう 1 本が出した 3 件 — いずれも本 wave 以前から存在する

次の 3 件は base 版 (`cf4273f56`) に同じ形が存在することを親が現物で確認した。
**本 wave の後退ではないので scope 外とし、裁定パッケージへ回した。**

- finalizer が probe の status を raw の returncode / stdout / stderr から再導出しない
  (`_probe_payload_status` は base の 2131 行に同型が存在し、事前 / 事後 probe に同じ扱いをしていた)。
- 読み込み後の spec を `dataclasses.replace` で差し替えられる
  (base の plan payload にも `environment` と `failure_policy` は入っていない)。
- binary の hash 検査から spawn までに path が差し替わりうる
  (base の 1821 行にも同じ「検査してから path で起動」がある)。

## 変異走行 — 実効 gate 7 件が発火することを確認し、冗長 gate 2 件を証拠から外した

**期待ノードを推測で書くと帰属が崩れるため、probe (全件 SURVIVED 期待で観測ノードを集める)
→ 期待確定 → 本走の順で回した。**

- **本走 (`mutation-ledger.json`): 7 件登録、7 件 KILLED、全件が期待と一致。** baseline も緑。
- 置換対象は全件ちょうど 1 箇所であることを生成器が機械検査している (複数箇所だと帰属が崩れる)。

発火を確認した実効 gate は次の 7 つである。

| 変異 | 期待どおり赤にしたテスト |
|---|---|
| D を単一分母へ戻す | 二分母の検査と成果物再計算の 2 件 |
| 実行時に中間 probe が 2 回目の測定を止めない | 中間 probe の competing / indeterminate の 2 件 |
| finalizer が中間 probe の競合を無視する | 中間 probe competing の 1 件 |
| 凍結した reference 個数の一致検査を外す | 凍結定数の負例 1 件 |
| 凍結した D の式の一致検査を外す | 凍結定数の負例 1 件 |
| finalizer の exact 2 measurement 件数検査を外す | 完備検査と重複 ID 拒否の 2 件 |
| spec の schema 一致検査を外す | 段 6 の fix で足した旧版拒否の負例 1 件 |

最後の 1 件は、段 6 のレビューが指摘した穴が**実際に塞がったことの実証**である。
fix 前ならこの変異は生存していた。

### 単独変異の証拠から外した冗長 gate 2 件 (DW-M03)

- **実行時の exact 2 measurement 完備条件は構造的に到達不能だった。** round 1 で生存したので
  現物を読んだところ、`_session_outcome` では complete 以外の結果がすべて上流で return するため、
  その条件が真になる入力を呼び出し側から構成できない。**実効 gate は finalizer が生記録を
  検証する側**であり、そこへ再照準して KILLED を確認した (`MUT-B4PAIR-06B`)。
- **finalizer の probe 3 件完備検査は `_probe_payload_status` に mask される。** 同関数が
  `type(value) is not dict` で None を先に拒否するため、完備検査だけを外しても落ちる。
  DW-M02 に従い両層同時変異まで裏取りしたところ **SURVIVED** で、事前登録した KILLED 期待は
  満たされなかった (`mutation-ledger-probe-round3-two-layer.json`)。
  **出荷コードはどちらか一方で必ず弾くので保護されているが、その対を同時に検査するテストは無い。**
  backlog として残す。

初回の probe 結果は消していない (`mutation-ledger-probe-round1.json` 以下)。

## 実測

- 焦点走: 変更前 226 件緑 → 実装後 245 件緑 → fix 後 **248 件緑**。
  焦点集合は driver を参照する test 3 file 全件 (参照関係で引いた)。
- provenance: 全史監査 rc=0 (8510 件、新規違反なし)。
- **bench の実走は無い。**

## 証明していないこと

driver の `NOT_PROVEN` へ 2 行を足した (既存 8 行は減らしていない)。

- 凍結項目の一致検査は同一 revision 内の自己整合を示すだけであり、定数が D1699 の裁定値である
  ことを証明しない。独立な pin も freeze receipt も無い。定数・spec・実装・テストを同じ commit で
  同期して変えれば赤にならない。
- 測定実体は module 属性であり、同一 process 内でこれを差し替える経路は防がない。

## 段 8 (自己改善) — 候補 2 件を実測したが、どちらも byte 予算に入らなかった

いずれも本 wave で実測した手順の欠落であり、仮想的懸念ではない。

1. **変異 harness は KILLED 期待に `expected_nodes` を要求する。** したがって初出の変異は
   全件 SURVIVED 期待の probe で観測ノードを集めてから期待を確定する必要がある。
   `docs/dev-wave/mutation.md` の `DW-M01` へ 1 行で入れたかった。
2. **上限到達で子が停止しても実装が完成していることがある。** 本 wave の実装子は
   `stop_reason=max_model_calls` で SIGTERM を受けたが、実装は完成しており焦点走も緑だった。
   rc と成果物の不在だけで未実施と判定せず作業木を検査する、を
   `docs/dev-wave/operations.md` の `DW-O01` へ 1 行で入れたかった。

**どちらも実装していない。** `docs/dev-wave/**` の L1 byte 予算 (10625 bytes) に隙間が無く、
最短化した 1 行 (93 bytes) でも超過した。場所を作るには既存の規範文を削る必要があるが、
それらの byte はテストが逐語照合しており、圧縮は gate を壊す実測済みの危険がある。
自己改善契約は予算のために安全義務を削ることを禁じているので、実装せず記録に留める。
**予算の引き上げが要るかどうかはユーザー手番。**

## 次 wave への持ち越し

1. **[最優先] 凍結 spec は実リポジトリ上で作成できない。** `load_frozen_spec` が
   「spec bytes == HEAD の blob」(`floor_pair_driver.py:1137-1139`) と
   「spec 内 `provenance.source_commit` == HEAD」(同 `:1182-1186`) を同時に要求する。
   spec は追跡 file なので、自分自身を含む commit の hash を自分の中に書くことになり、
   hash の不動点を要求している。テストが緑なのは偽の VCS が定数を返すためである。
   **現状 driver は production で spec を 1 度も load できない。** 本 wave の scope 外
   (provenance 束縛の設計択一であり別の裁定が要る)。段 3 の別レンズが暴いた。
2. rep 単位の交互測定 (区間内ドリフトをさらに相殺する案)。
3. `probe_fn` の差し込み口、finalizer の probe status 再導出、binary の TOCTOU の 3 件
   (いずれも base から存在)。
4. 事前登録 §11.2 の費用の目安の段落。reference が pair-sample あたり 2 件になったので、
   加算ではなく内訳の組み替えになる。別 wave が数値だけを当て、構成の記述は本件の裁定範囲として
   残してある。**正式標本の実走前に必要。**
5. probe 3 件完備検査とその mask 層を同時に検査するテスト。
