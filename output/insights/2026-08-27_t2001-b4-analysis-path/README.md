# [T-2001] B-4 の凍結分析契約を実行する 5 経路

wave `t2001-b4-analysis-path` / branch `worktree-dev-wave-t2001-b4-analysis-path`
base main `343b8f5a5` / 実装 commit `592a08f3`

## この wave が実在させたもの

事前登録 §5.1.1 (D1140〜D1143 が凍結した規則) を実行する経路を新設した。
着手前は `scheduled_attempt_registry` / `analysis_manifest` / `analysis_invalid` の 3 語が
repo 内の Python にも JSON にも 0 件で、実装は存在しなかった。

| module | 役割 |
|---|---|
| `orchestrator/campaign/p3_b4_analysis_contract.py` | 凍結された入力型と純関数。理由 enum 12 個、順位規則、block score、有理数 exact の `A_hat`、厳密符号検定、Clopper-Pearson 根の外向き包囲、入力検証を全件先に済ませる全域 verdict |
| `orchestrator/campaign/p3_b4_analysis_adapter.py` | raw 試行記録から契約入力型を作る。十進 lexical を exact 有理数へ読み、producer 不在の field を推定せず拒否する |
| `orchestrator/campaign/p3_b4_analysis_ledgers.py` | 予定 attempt の全件台帳と分析対象 manifest の生成器、再生成による完全性検査、発行者束縛の seed からの割当導出と遵守検査 |
| `orchestrator/campaign/p3_b4_analysis_path.py` | artifact bytes から verdict までの統合経路。違反件数と割当遵守を自分で導出し、申告 hash を受理しない。source closure receipt を出す |
| `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py` | 実装の定数と挙動が凍結文面と一致することを、文面から独立に抽出して照合する |

対応するテスト 5 file を同時に置いた。

## この wave が実在させていないもの (過大に読まないための逐語)

- **事前登録 §6 の前提条件 9 は未充足のままである。** 権威ある producer が無い。
- **file-drawer は閉じていない。** 予定 attempt の全列を発行する権威が存在しない。
- **純関数の直呼びは閉じていない。** 閉じたのは production caller の一覧固定までである。
- source bytes の内容から `status` や throughput を再導出しない。
- seed の一様性と実走前発行は本 module では証明しない。発行者の責任として残る。
- sanctioned CLI、永続 writer、§7.1 の全件 report generator、certified 選択への配線は無い。
- 事前登録 doc の §5 の値セルは 1 欄も埋めていない (並行 wave `t1840` が同 doc を編集するため)。

## 親が実走した結果

| 対象 | 結果 |
|---|---|
| 新規 5 test file | **152 passed / 0 failed** |
| `test_p3_build_authority_cli` / `test_p3_exploration_namespace` / `test_ccbench_spawn_sites` | 60 passed |
| `test_t1286_commit_receipt` ほか 4 file | 128 passed / 9 skipped |
| `test_s8b_*` ほか 8 file | 971 passed / 3 skipped |
| 全史 provenance 監査 | 6618 件・新規違反なし |
| holdout 三軸 conjunction 走査 (親が直接呼出) | `conjunction_hits` 空 |

段 5 の実装子はいずれも sandbox から計算ノードへ dispatch できず (`rc=16`) 実走 0 件だった。
**上の緑はすべて親の実走である。**

## 変異 matrix

`mutation-spec-final.json` / `mutation-final-report.json` が一次資料。

**baseline PASSED・11 件すべて KILLED・SURVIVED 0・MISMATCH 0。**

期待 node は完全集合として固定した。全件 SURVIVED 期待の probe (`mutation-spec-probe.json` /
`mutation-probe2-report.json`) で観測 node を先に集めてから本登録した (DW-M07)。

| 変異 | 内容 | 赤 node 数 | 帰属 |
|---|---|---|---|
| X01 | 十進 exact 読取を外す | 1 | 単一 |
| X02 | tie 境界を境界値排除にする | 6 | 多層 |
| X03 | `missing` 同士の score を変える | 1 | 単一 |
| X04 | protocol violation の判定を崩す | 7 | 多層 |
| X05 | `A_min` を成立条件へ加える | 19 | 多層 |
| X06 | 台帳の batch 正規化を外す | 1 | 単一 |
| X07 | 母集合を先頭 n から末尾 n にする | 14 | 多層 (適格性 7 条件が個別に反応) |
| X09 | 割当を定数にする | 3 | 独立 HMAC ベクトル 2 + 非定数性 1 |
| X10 | 文面 section の raw hash 照合を外す | 1 | 単一 |
| X11 | source digest の全単射を集合一致へ戻す | 1 | 単一 |
| X12 | receipt の consumer 結果束縛を外す | 2 | ほぼ単一 |

### erratum — 段 4 で事前登録した変異の取り下げ

段 4 で登録した M1〜M13 のうち、段 6 のレビューが **M1 / M5 / M8 / M9 / M11 / M12 / M13 は
単一理由性を持たない**と実証した。特に:

- **M12 (manifest の行比較と bytes 比較を同時に外す 2 層変異) は SURVIVED になる。**
  第 3 の gate (`manifest != regenerated` の object 比較) と、統合経路の completeness 再呼出、
  actual binding の完全一致比較が同じ入力を拒否するためである。
- **M13 (raw section hash の除去) は当時の論理和実装では受理集合が変わらず**、赤 node が無かった。

DW-M01 / DW-M02 に従い、**登録を取り下げて実効 gate へ再照準し、X01〜X12 として登録し直した**。
初回登録は本節の erratum として残す。

### 冗長 gate の明記 (DW-M03)

適格性述語 11 条件のうち **4 条件 (`block_id`、`reference_tps`、2 つの reference hash) は
実効 gate ではない**。台帳の上流検査が `reason is SCHEDULED` の時点で既に必須化しており、
その条件を消しても受理される成果物は変わらない。冗長 gate として明記し、
単独変異の証拠から外す。到達可能な 7 条件は cutoff 前の行で個別に検査できる。

## 段 6 レビューが実証した欠陥 (すべて是正済み)

2 レンズが独立に検出し、親が裁定した。焦点再レビューの判定は **closed 8 / partial 3 / regressed 0**。

1. **割当の検査が実装から自己導出されていた。** `derive_assignment()` を定数関数へ置き換えても
   型・決定性・manifest 一致・再生成検査がすべて通った。**無作為化は `Bin(m, 1/2)` の
   帰無分布の前提そのもの**なので、ここが空洞だと p 値と verdict の根拠が消える。
   → 独立に計算した HMAC 検査ベクトルを置いた。X09 が実測で殺せることを確認した。
2. **適格性の検査が恒真だった。** 不適格行を 201 件の cutoff より後ろに置いていたため、
   述語を 1 つ消しても manifest が変わらなかった。3 系統とも同じ形。
   → cutoff 前へ移し、到達可能な 7 条件を個別 node にした。
3. **文面 hash の照合が論理和だった。** 生 bytes が変わっても正規化後が一致すれば受理していた。
   → 生 bytes の一致を無条件要求へ変えた。段 5 の親 prompt が「無害な変更では赤にしない」と
   書いたのは段 4 裁定 A8 と矛盾していたので、**親が段 5 指示を撤回した**。
4. **source artifact の照合が multiset 一致だった。** arm 間で digest を入れ替えても検出できなかった。
   → 順序付き全単射へ変えた。
5. **統合経路の一括 `except Exception` が真因を潰していた。** 40 行分の例外を 1 つの理由へ
   写しており、親は repo 外 probe で真因を切り分ける必要があった。
   → 段別の型別捕捉へ分割し、分類できないものだけ凍結文面の受け皿へ写す形にした。

## 段 5 で単位 D が露出させた統合欠陥

単位 D (統合経路) の初回実走は 9 failed / 3 passed だった。親が repo 外 probe で切り分けた真因:

- 単位 C は `reference_tps` を `(100, 1)` (整数比 tuple) で作る
- 単位 A の変換は受理する。単位 B の変換は拒否する
- **同じ値域を 3 module が別々に実装していて食い違っていた**

単位 A が変換と binding domain 述語を**公開正本**として export し、B と D が委譲する形へ統一した。
**単位 A の受理集合は 1 bit も変えていない** — 単位 B の過剰拒否だけを是正した。

**統合単位 D は段 2 のプランが親案へ足したものである。** 親案の A→B/C だけでは、呼び手が
違反件数と割当遵守を自己申告できる穴が残る。この単位が無ければ上の食い違いも露出しなかった。

## 一次資料

- `verbatim/` — 段 1 brief、段 2 プラン、段 3 の 2 レンズ、段 4 裁定、段 5 の実装子 5 本と
  fix 2 本、段 6 のレビュー 2 本と fix 3 本、焦点再レビュー、親の実測記録
- `mutation-spec-final.json` / `mutation-final-report.json` — 本走
- `mutation-spec-probe.json` / `mutation-probe2-report.json` — 観測 node 収集の probe

## erratum — 逐語 1 箇所の可逆 defang (D88 / DW-S07)

`verbatim/s2-plan.md` の 1 箇所を、原文のまま commit できないため置換した。

- **理由**: 段 2 プランの一覧検査の表が、`orchestrator/campaign/login_headroom.py` にだけ
  出現してよいと pin されている数値 literal を**そのまま引用していた**。
  `orchestrator/tests/test_login_headroom.py::test_ceiling_numeric_literal_occurs_only_in_login_headroom_module`
  は tracked / untracked の全 text を読み、**空白を全除去してから**照合するため、
  整形では回避できない。原文のまま置くと同検査が赤になる。
- **置換**: 当該 literal 1 箇所を `<login-headroom-ceiling-literal>` へ置換した。
  **置換は 1 箇所のみで、可視文字の他の変更は無い。**
- **原文 sha256**: `42bb85063ff82dca036ffccca2543158f93859747bae5fdc188e7f2d12eaf898` (57131 bytes)
- **置換後 sha256**: `c0057a0c8a3308b19368f431bc599cb25a010b4be53735116f1976f918dd7379` (57153 bytes)
- **復元法**: `<login-headroom-ceiling-literal>` を、上記検査が pin している
  compact な数値 literal へ戻すと原文 sha256 に一致する。

**発見の経緯**: 受入全走でだけ発火した。同検査は growth hold の下にあり通常走では skip される。
親は段 7 の凍結前走査で三軸語と placeholder は見たが、**この gate の検出語を見ていなかった**。
DW-S07 は「全 gate の検出語」を機械走査せよと定めており、親の適用が不足していた。

## erratum — 受入全走で発火した 2 件目 (production の識別子衝突)

`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py` の local 変数名 `evaluate` が、
repo 全体を AST 走査する certified-writer の caller 検査で
`campaign.pipeline.evaluate` へ解決され、未解決参照として拒否された。
**実際に同 API を呼んではおらず、名前の衝突だけである。** 改名で解消した。
これも growth hold のため受入全走でだけ発火した。
