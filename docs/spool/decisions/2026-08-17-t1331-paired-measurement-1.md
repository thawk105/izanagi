---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: t1331-paired-measurement
seq: 1
---

## {{D:oracle-comparison-rule-refreeze}}. 8b oracle の比較規則を明示的に再凍結する

**決定:**

1. **集約規則を明示的に再凍結する。** `s8b_oracle_judge.judge_oracle` の集約は、各 trial の
   bench rep 中央値を求め、その trial 中央値群の中央値を構成ごとの cell 値とする
   二段中央値 (median of medians) とする。floor は入力にも argmax の tie-break にも使わない。
   同関数の docstring が要求していた「実測開始前の明示的な再凍結」は本決定で満たす。
   docstring からその未凍結宣言を外し、本決定を**題で**指す (番号は land 時に採番されるため
   コードへ書けない)。
2. **raw oracle の判定境界を現行のまま再凍結する。** holdout ごとに eligible な構成の cell 値の
   最大値を取り、最大値と**完全一致**する構成が 1 つなら一意最良、2 つ以上なら tie、
   eligible が空か unknown を含むなら判定不能とする。
3. **反復数の凍結手段は既存機構に置く。ただし trial 数の値は未凍結である。**
   bench rep 数と実行時間は `s8b_experiment_numbers` の承認定数と exact 一致を manifest 検証が
   要求し、再測定 round は 1 完全一致で pin されている。**trial 数は reviewed spec の承認手番に
   従属し、承認定数が未設定の現状では凍結されていない** (機構全体が `no-approved-spec` で
   fail-closed に止まり、official の受理集合は空である)。本決定はその定数を書かない。
4. **構成集合・holdout 集合の凍結手段は既存機構に置く。新設しない。** manifest 検証は
   freeze の全 byte hash 一致を要求し、さらに schedule の holdout 集合が freeze の holdout 集合と
   完全一致すること、schedule の cell 集合が holdout × 構成の完全積と完全一致することを
   独立に検査する。
5. **機械強制の内訳を分けて記録する。** 集約規則は既存の judge テストが集約値と勝者を期待値として
   pin しており、規則を書き換えれば赤くなる。**判定境界は本決定と同じ land で新設したテストが担う** —
   変更前の exact tie テストは本物の完全一致しか置かないため、境界を `isclose` 系や固定幅へ緩めても
   赤くならなかった。新設テストは完全一致を tie とし、1 ulp 差を両方向で一意最良と固定する。
   **変異実測**: 同じ緩和変異 2 件が、変更前 HEAD では 2 件とも SURVIVED、
   新設後は 2 件とも KILLED で、落ちた node は新設テスト 1 本と完全一致した。
6. **`judge_oracle` の判定関数と observations の受理条件は変更しない。**
   ただし docstring の byte 変更で同 module の実ファイル hash が変わるため、
   **reviewed spec の generator identity は旧 hash から新 hash へ移る** (manifest 検証が
   `generator_versions` の実 byte hash 一致を要求する)。同一 land で独立 golden の literal と
   その派生 hash を実測値へ追随させた。
7. **D496 が外すべき対象は受入関門ではなく最終判定層である。** 床値を比較の基礎として使っている
   のは `s8b_verdict` の条件 3 (実測差が凍結 per-pair floor を超えるか) と scale gate
   (stock の実測 median を床値 campaign 由来の期待値と比較) である。**ただし条件 3 は
   2026-07-16 のユーザー裁定が逐語凍結した truth table の一部であり、本決定では変更しない。**
   変更は当該裁定の再裁定を要する。
8. **床値に従属すると説明されていた受入関門 2 件は、実装上いずれも過去値との比較ではないが、
   D496 の下では不要になる。** manifest の per-pair 対表 exact 検査は freeze の floor 節の内部整合
   だけを見ており、構成集合の凍結は決定 4 の別述語が担う。floor/budget の部分 hash は
   freeze 全体の byte hash 照合と重複する。driver の測定 binary bytes 照合は、照合対象の receipt
   自体が過去の床値 campaign 由来であるため「今回測る binary が過去 campaign の binary と同じか」を
   要求している。**いずれの撤去も受理集合を広げるため、本決定では実装しない。**
9. **D496 決定 3 は現状の実装では実行できない。** 実走マーカーが freeze の byte hash を identity と
   して出力先非依存に排他作成され、存在すれば同じ freeze の再走を全拒否する。この resume 拒否は
   別のユーザー裁定が凍結した挙動である。加えて v1 freeze の verify は毎回 repository novelty
   search の pass を要求し、初回観測後の再走と両立しない。**どちらが優先するかは本決定では
   決めない。**

**理由:**

- D496 決定 2 は事前登録を放棄せず凍結対象を規則側へ移すと定めた。実測すると、規則の 4 要素のうち
  構成集合・holdout 集合は既存機構が凍結しており、反復数も 3 量のうち 2 量は凍結済みで trial 数だけが
  承認手番待ちである。未凍結のまま実測へ入りうるのは集約規則と判定境界であり、本決定はその 2 つを
  閉じる。既存機構がある要素については名指しで参照し、新しい凍結装置を重ねない。
- 判定境界だけは既存テストで pin されていなかった。宣言だけを台帳へ書けば恒真な事前登録になるため、
  緩和変異を捕まえる正例つき検査を同じ land で足した。純増の検出力はこの 1 点である。
- 床値の比較利用が最終判定層にあることは、裁定時に見えていなかった事実である。判定層の変更は
  逐語凍結された truth table に触るため、人間の再裁定を経ずに実施してはならない。
- 受入関門の撤去は受理集合を広げる。規律 2 の下では、置き換える事前登録の発効が先である。

**却下した選択肢:**

- 比較規則を宣言する新しい定数と、spec / manifest / runtime の三者一致 pin を新設する —
  宣言と実装の乖離検出という利点はあるが、manifest schema の版上げと受理形の変更という代償が
  大きい。乖離検出だけを目的に受理形を変えず、撤去実装と同じ裁定へ束ねて返す。
- 判定境界を走行内分解限界 (変動係数) 由来の帯へ書き換える — D496 決定 4 が求める
  「差が機械の分解限界より小さい」を判定へ反映できる利点はあるが、raw oracle の tie を変えると
  判定関数を書き換えないという裁定時の留保に触る。**択は 2 つではない** — 順位の事実と性能主張の
  境界を二層に分ける案、replicate 単位の対比とその分散を使う案があり、対比の共分散は
  manifest の replicate 添字と observations の schedule 添字から復元できる (共分散と相関の
  実装は pilot module に既に存在する)。境界の算式そのものが未裁定であり実装者が選んではならない。
- 受入関門と最終判定層の床値依存を本決定と同じ land で撤去する — 受理集合を広げる変更と
  逐語凍結された truth table の変更を、事前登録の発効と同時に既成事実にすることになる。
- 事前登録ごと外す — 絶対規律 2 に触れる。人間だけが変更できる。
