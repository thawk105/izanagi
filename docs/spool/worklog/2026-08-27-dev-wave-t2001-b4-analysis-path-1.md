---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t2001-b4-analysis-path
seq: 1
title: [T-2001] B-4 の凍結分析契約を実行する 5 経路を実装した — 割当の検査が実装から自己導出されていた穴を段 6 が実測で暴いた (コード、branch worktree-dev-wave-t2001-b4-analysis-path、変異 matrix = baseline PASSED・11/11 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 事前登録 §5.1.1 が凍結した規則を実行する経路を新設した。着手前は
  `scheduled_attempt_registry` / `analysis_manifest` / `analysis_invalid` の 3 語が
  repo の Python にも JSON にも 0 件で、実装は存在しなかった。
  一次資料は `output/insights/2026-08-27_t2001-b4-analysis-path/`。
- **この wave は前提条件 9 を充足しない。** 権威ある producer、sanctioned CLI、永続 writer、
  §7.1 の全件 report generator、certified 選択への配線がいずれも無い。
  file-drawer も閉じていない。純関数の直呼びも production caller の一覧固定までしか閉じていない。
  **成果物にも docstring にも「充足した」「閉じた」とは書いていない。**
- 事前登録 doc は 1 byte も編集していない。並行 wave `t1840` が同 doc の §7.2 を編集する
  scope を持つため、依頼の「同じ file を編集する必要が出たら land を待て」に従った。
  §5 の primary outcome 欄の記入は t1840 の land 後の別 task とする。

- **段 6 の 2 レビューが独立に検出した最重の欠陥は、割当無作為化の検査が実装から
  自己導出されていたことである。** テストが `derive_assignment()` を呼んで manifest を作り、
  同じ関数で再検証して比べていたため、**全 block で同じ順序を返す定数関数へ置き換えても
  型・決定性・manifest 一致・再生成検査がすべて通った**。無作為化は `Bin(m, 1/2)` の
  帰無分布の前提そのものなので、ここが空洞だと p 値と verdict の根拠が消える。
  独立に計算した HMAC 検査ベクトルへ差し替え、変異 X09 が実測で殺せることを確認した。
- **適格性の検査は恒真だった。** 不適格行を 201 件の cutoff より後ろに置いていたため、
  適格性述語を 1 つ消しても manifest が変わらなかった。3 系統とも同じ形だった。
- **文面 hash の照合が論理和で、生 bytes の変更を素通ししていた。**
  段 5 の親 prompt が「無害な空白・強調の変更では赤にしない」と書いていたが、
  これは段 4 裁定の「exact section bytes hash」と矛盾していた。**親が段 5 指示を撤回し**、
  生 bytes の一致を無条件要求へ変えた ({{D:frozen-doc-section-needs-byte-exact-pin}})。
- **source artifact の照合が multiset 一致どまりで、arm 間で digest を入れ替えても
  検出できなかった。** 順序付き全単射へ変えた。
- 焦点再レビューの判定は **closed 8 / partial 3 / regressed 0**。partial 3 件は
  (a) 適格性 4 条件が上流検査から含意される冗長 gate であること、
  (b) manifest 完全性が多層で守られ単独変異では帰属できないこと、
  (c) 純関数の直呼びが静的 caller の固定までしか閉じないこと。
  いずれも本 wave の scope 内では閉じられないと裁定し、限界として明記した。

- **統合単位は段 2 のプランが親案へ足したものである。** 親案の「契約型 → adapter / 台帳」
  だけでは、呼び手が違反件数と割当遵守を自己申告できる穴が残ると指摘された。
  この単位を置いたことで、**3 module が同じ値域を別々に実装して食い違っていた**欠陥が
  初回実走で露出した ({{F:duplicated-domain-predicate-diverges}})。
  単位を分けて実際に繋ぐまで、module 間の値域の食い違いは出ない。
- 段 5 の fix 子が 1 巡まるごと空転した。親が「既存テストの期待値を変更するな」と
  「loader 失敗の理由は受け皿へ」を同時に指示し、その wave の新規赤テストが古い理由を
  期待していたため両立不能になった。**子は何も変えずに停止した。判断は正しく、
  指示側の射程が過大だった** ({{F:fix-child-blocked-by-overbroad-expectation-freeze}})。
- 段 4 で事前登録した変異 M1〜M13 のうち 7 件は単一理由性を持たないと段 6 が実証した。
  特に M12 (2 層同時変異) は第 3 の gate に守られて SURVIVED、M13 は当時の論理和実装では
  受理集合が変わらず赤 node が無かった。DW-M01 / DW-M02 に従い登録を取り下げ、
  実効 gate へ再照準して X01〜X12 として登録し直した。初回登録は insights の erratum に残した。
- 適格性述語 11 条件のうち 4 条件は実効 gate ではない。台帳の上流検査が既に必須化しており、
  消しても受理される成果物は変わらない。DW-M03 に従い**冗長 gate と明記し、
  単独変異の証拠から外した**。

- 段 5 の実装子はいずれも sandbox から計算ノードへ dispatch できず (`rc=16`) 実走 0 件だった。
  記録した緑はすべて親の実走である。新規 5 file で 152 passed、
  一覧検査で 60 + 128 + 971 passed、全史 provenance 監査 6618 件・新規違反なし。
- 親の手順ミスが 2 件あった。(a) レビュー子へ `--reasoning` を指定して rc=2 で 2 本とも即死
  (段 5 / 6 の effort は tool が docs 権威から導出するので caller は指定できない)。
  (b) 変異 spec の `category` に語彙外の値を書いて harness が中止。どちらも即座に直した。
- 一覧検査の中核 6 node は `IZANAGI_GROWTH_HOLD_V1` で通常走では skip され、
  **受入全走でしか発火しない**。迂回せず、同じ性質を親が静的に確認した。
  holdout 三軸 conjunction の走査も同じく hold されるため、親が走査関数を直接呼んで
  `conjunction_hits` が空であることを実測した。

- **段 8 の自己改善は 3 候補のうち 0 件を dev-wave docs へ収容した。** 内訳は次のとおり。
  - **`--reasoning` の段別制約を `DW-S06-A` の文言へ書く案は撤回した。** 同節の
    `reasoning=xhigh` は checker が**採用 pin として exact 照合**しており、変更には
    採用裁定と pin の同時更新が要る。裁定境界に当たるので実装せず裁定へ返す。
  - 実装子が dispatch できない事実 (`DW-S05-C`) と、期待値変更禁止の射程 (`DW-S06-B`) の
    2 件は、**`docs/dev-wave/**` の L1.5 予算に余裕が 0 bytes** だったため収容できなかった。
    編集前の unique footprint は上限 9566 bytes ちょうどで、1 byte も足せない。
    D782 の手順 1 (既存記述の削減) は、**main が本 wave 中に同じ節を既に圧縮しており**、
    base 側で削っても取り込み時に上書きされるため意味を成さない。手順 3 (上限引き上げ) は
    「収容先を作れないと確かめられた場合」に限るが、main 取り込み後の実際の余裕を
    測るまでその確認ができない。**よって本 wave では収容せず、失敗台帳へ内容ごと残した**
    ({{F:fix-child-blocked-by-overbroad-expectation-freeze}})。

## 次の一手差分

### 完了

- [T-2001] 凍結した分析契約を実行する 5 経路を実装し、変異 matrix と一覧検査を通した。
  前提条件 9 の残りは producer 側の別 task として分離した。
  remaining: none
  base: b1d54c91e4776d7643e68eb007a7ed0a66c4ebbca1363df0ceb45adde5528c81

### 新規

- {{T:b4-raw-record-producer}} **P1・新規**: B-4 の raw 試行記録を書く権威 producer を実装する。
  本 wave の adapter が必須にした `execution_disposition`・実行 slot 順・`treatment_fired`・
  `contaminated`・`protocol_ok`・`precursor_hash`・reference の 2 hash は、
  repo 全体に durable な生成者が無く、現状の実成果物はすべて adapter に拒否される。
  所有は `t1840` の B-4 起動器と重なるため、**同 wave の land 後に着手する**。
- {{T:b4-schedule-and-seed-issuer}} **P1・新規**: 予定 attempt の全列・割当 seed・
  実走前 manifest の発行者を決めて実装する。本 wave の台帳は発行者束縛の receipt を
  必須にしたが、**receipt を発行する権威が存在しない**ため file-drawer は閉じていない。
  seed の一様性と事前発行の担保も発行者側の責務として残っている。
- {{T:b4-analysis-sanctioned-entrypoint}} **P2・新規**: 分析経路の正式起動口、不変な結果
  artifact の writer、§7.1 の全件 report generator、certified 選択への必須配線を実装する。
  これが無い限り、本 wave の 5 module は certified 選択・レポート・台帳の値を 1 bit も変えない。
- {{T:b4-fill-primary-outcome-cell}} **P2・新規**: 事前登録 §5 の primary outcome 欄へ、
  本 wave が出す analysis source closure receipt の path と sha256 を記入する。
  D1143 の解除条件は本 wave で満たしたが、**並行 wave `t1840` が同 doc を編集するため
  その land を待つ**。記入しても他の欄が未記入なので実走前検査は開かない。
- {{T:b4-frozen-text-inconsistencies}} **P2・ユーザー裁定待ち**: 凍結文面の 3 点の不整合を
  どう扱うか。(a) 理由 enum は 11 名か 12 名か (本 wave は 12 で実装した)。
  (b) 「入力は上の 3 つだけ」は 4 つの誤記か。(c) 台帳 2 hash の観測側を純関数の入力に
  加えるか、統合層での照合を正式に許すか (本 wave は後者で実装した)。
  詳細は {{D:b4-frozen-enum-and-layer-reading}}。
- {{T:dev-wave-docs-budget-headroom}} **P2・新規**: `docs/dev-wave/**` の L1.5 予算の
  実余裕を main 取り込み後に測り直し、収容できなかった 2 件を該当 leaf 節へ統合する。
  対象は実装子が計算ノードへ dispatch できない事実 (`DW-S05-C`) と、fix 子への
  期待値変更禁止の射程 (`DW-S06-B`)。余裕が作れないと確かめられた場合だけ D782 手順 3 へ進む。
- {{T:dev-wave-review-effort-pin}} **P2・ユーザー裁定待ち**: `DW-S06-A` の
  `reasoning=xhigh` が採用 pin として exact 照合されているため、
  「段 5 / 6 の effort は docs 権威から導出され caller は指定できない」という
  実測を同節へ書けない。文言を変えるか、pin の対象から外すか。
  本 wave では `--reasoning` を review 段へ渡して `rc=2` で 2 本とも即死させた。
