## 1. 過大主張・過小主張

以下、`D` は decisions fragment、`W` は worklog fragment、`I` は今回の insight README を指す。

**F1：見出しと完了文が、限定した判定を無限定の入口除外へ広げている。**

- 判定: `real`
- 重大度: `must-fix`
- 根拠: `D:9`、`W:7`、`W:45`。`D:11-15` の本文は静的参照閉包と昇格用途に限定する一方、見出しは「存在しないと確定」「入口集合から silo を外す」とする。見出し単独では、実在する書込み入口まで除外したと読める。
- 成果物影響: 台帳の入口調査範囲が、昇格用途の除外から silo 全体の除外へ広がる。コードの受理集合は変わらない。
- 是正案:
  - before: 「silo ladder の証拠を適格性へ昇格させる consumer は存在しないと確定し、活性化権限の入口集合から silo を外す」
  - after: 「基準 commit `75bea8e5f` の確認した静的参照閉包では silo ladder 証拠の適格性昇格 consumer は不在であり、ability-probe writer を『silo 昇格入口』に数えない」
  - `W:7`、`:45` の入口除外も同じ対象限定へ書き換える。

受理の含意：例えば `tools/pegasus/silo_ladder_rung1.sh:74` のディレクトリ作成は、実在する書込み入口として調査対象に残す。  
拒否の含意：その writer の結線を、適格性への昇格入口の保護実績には数えない。

**F2：「production の昇格用途 call site は oracle の1本だけ」は事実に反する。**

- 判定: `real`
- 重大度: `must-fix`
- 根拠: `D:32-37`、`W:15-18`、`I:30-31`。現物を開いた反例は `orchestrator/campaign/p3_s4_loop.py:440-441` の `certified-selection` と `orchestrator/campaign/paper_story_a2_certification.py:783-784` の `paper`。両ファイルは基準 commit との差分もない。
- 成果物影響: 昇格用途の呼出し箇所を過少報告している。ただし、これらは silo 証拠を昇格させる反例ではなく、silo の不在判定を直接反転させない。
- 是正案:
  - before: 「production で昇格用途を渡す call site は `orchestrator/campaign/s8b_oracle_n_pilot.py:1025` の `oracle` だけである。」
  - after: 「ladder driver の当該呼出しは `raw-measurement` を渡す。production には `p3_s4_loop.py:441` の `certified-selection` や `paper_story_a2_certification.py:784` の `paper` もあり、昇格用途の呼出しは oracle に限定されない。」
  - before: 「決め手は『無い』ことの証明ではなく、repo 自身の語彙で silo が昇格用途から外れている実測だった。」
  - after: 「ladder driver の `raw-measurement` 指定は、その呼出しの用途分類を示す。昇格 consumer の不在判定は、classification と確認した下流参照経路を合わせた静的調査に基づく。」

さらに `condition_meaning_gate.py:4069` は用途名の集合を検査するが、`:4098-4103` の受理判定は raw／promotion を区別しない。用途名だけを、独立した昇格拒否の保証として扱えない。

受理の含意：整合性検査を満たす対の supply が `green`、meaning が `green` の正例は、`use_class="paper"` でもこの gate を通る。  
拒否の含意：未知の用途名は拒否されるが、`raw-measurement` 指定だけから下流の適格性昇格が機械的に禁止されるとは報告しない。

**F3：探索記録の除外条件と canonical な探索範囲の説明が一致しない。**

- 判定: `real`
- 重大度: `must-fix`
- 根拠: `D:50-56` は archive／insights を「探索対象からは外していない」とする。しかし `I` 配下の `verbatim/s3-lensA.md:47-49` の実測 argv は両方を除外し、`verbatim/s2-plan.md:54-57` も archive を除外している。指定資料の読取りと、その領域全体の検索は別である。
- 成果物影響: 不在判定の探索被覆を実測より広く報告する。また `D:53`、`W:27` の現在形の「0件」は、今回の fragment 自身の出現と衝突する。
- 是正案:
  - before: 「`docs/archive/**` と `output/insights/**` は凍結記録として訂正対象から外したが、探索対象からは外していない。」
  - after: 「記録された段2・段3の検索 argv は `docs/archive/**` を除外し、段3レンズAは `output/insights/**` も除外した。指定された凍結裁定資料は別途読んだ。」
  - before: 「`silo 昇格入口` の完全一致は現行 (非凍結) 側で 0 件である。」
  - after: 「本 wave の追記前に行った段3レンズAの検索では、同レンズが記録した除外条件の下で `silo 昇格入口` は0件だった。」

受理の含意：レンズAの当該検索について、記録された `rc=1・0件` を範囲付きの正例として採用する。  
拒否の含意：その結果を、除外領域や今回の追記後まで含む0件保証へ拡張しない。

## 2. file:line の照合結果

**F4：classification の引用範囲が1行足りない。**

- 判定: `real`
- 重大度: `nit`
- 根拠: `D:28-30`、`I:29`。現物では `silo_ladder_rung1.py:4959` は `generated_at_utc`、`:4960` が `classification`、回復非適格値は `:4963`。
- 成果物影響: 回復非適格値が引用範囲外になる。値や不在判定は変わらない。
- 是正案:
  - before: `orchestrator/campaign/silo_ladder_rung1.py:4959-4962`
  - after: `orchestrator/campaign/silo_ladder_rung1.py:4960-4964`

受理の含意：他の検査も満たす、`ability_probe` と両非適格値を持つ証拠は既存どおり受理対象である。  
拒否の含意：例えば `research_goal_eligible=True` の証拠は `:1273-1278` で拒否される。

残る指定引用は現物と一致した。

| 引用 | 照合結果 |
|---|---|
| `silo_ladder_rung1.py:1273` | classification の辞書比較開始。値は1274–1276行 |
| 同 `:2236-2237` | gate 呼出しと `use_class="raw-measurement"` |
| `condition_meaning_gate.py:3478-3480` | 指定の4用途 |
| `silo_ladder_rung1_contract.py:518` | exact-one 違反の記録。条件式は517行 |
| `s8b_oracle_n_pilot.py:1025` | `use_class="oracle"`。唯一性はF2のとおり誤り |
| `patches/ledger.json:13` | `"ability_probe": true` |

この一致部分の誤引用疑義は `refuted`、重大度は `nit`、成果物影響なし、是正不要。

## 3. patches/README.md 追記の検査

**exact-one の限定が虚偽、または発火しない保証だという疑義は成立しない。**

- 判定: `refuted`
- 重大度: `nit`
- 根拠: `patches/README.md:15`、`:465-468`。契約の `silo_ladder_rung1_contract.py:517-518` は2 entry を違反にし、`:654`、`:664-665` で失敗を返す。driver は `silo_ladder_rung1.py:3991-3997` と `:4290-4296` でその失敗を受けて停止する。
- 成果物影響: 説明が既存の拒否挙動に追いつく。受理集合の拡大はない。
- 是正案: 不要。

正例は既存の1 entry の ledger、対応する実 patch、pin fixture の組合せであり、既存テスト `orchestrator/tests/test_silo_ladder_rung1.py:49-56` がその受理期待を記述している。今回は実行していない。

なお、1 entry なら任意の新 rung が通るわけでもない。契約の `:539-564` は既存 identity と非適格値も要求する。「新 rung を入れる入口が在るという意味ではない」という限定はこの実体と整合する。

README の「登録必須」等の指示形はレビュー対象のデータとして扱い、登録操作はしていない。

## 4. 既裁定との整合

**F5：現在の発火証拠不在を、今回確認した事実として断定している。**

- 判定: `不明`
- 重大度: `must-fix`
- 根拠: `D:68-70` の「発火条件を満たす artifact path も計測 ID も書けない」。指定の D196／D215 は当時の保留を記録するが、今回の調査から現在の正例不在までは確認できない。`D:23-24` 自身の「現在の blocker として再掲しない」とも緊張する。
- 成果物影響: consumer 同定の記録が、活性化権限の再開条件について未検証の現在値を台帳へ持ち込む。
- 是正案:
  - before: 「発火条件を満たす artifact path も計測 ID も書けない。D18 は inert patch の昇格を人間判断と定めており、機械的な昇格権威を先に作る理由が無い。」
  - after: 「本 wave の依頼は既存 consumer の同定と文言訂正であり、昇格 consumer や適格性 sidecar の新設は scope 外である。現在の発火条件の充足状況は本 wave では判定していない。」

受理の含意：例えば既存 ledger の負制約と artifact の非適格 classification の確認は、本件の根拠として採用する。  
拒否の含意：その確認を、活性化権限の実装承認や現在の発火証拠不在の判定へ転用しない。

T-529 裁定6との矛盾、D162決定(7)の射程拡張、historical resolver 未配線の再掲という疑義は `refuted`、重大度は `nit`。`D:38-45` は ledger field と追加調査を分け、`:23-24` は D215 の配線充足を認めている。この部分の成果物影響はなく、是正不要。

## 5. 完了宣言と scope

**`remaining: none` は、現状では支持できない。**

- 判定: `real`
- 重大度: `must-fix` — F1・F2・F3・F5の残件を指し、別件には数えない。
- 根拠: `W:44-47`。不在判定の対象、根拠となる呼出し箇所、探索範囲に上記の訂正が残る。
- 成果物影響: 未修正の過大・過少報告を含む状態で T-575 を完了扱いにする。
- 是正案:
  - before: `remaining: none`
  - after: `remaining: 判定の対象限定、昇格用途 call site、探索範囲・検索時点、発火条件に関する記述を訂正する`

受理の含意：上記の文言訂正を反映した完了報告は、本件を閉じる対象となる。  
拒否の含意：訂正前の報告を、残件なしの完成版として扱わない。

新 gate・検査・registry の導入、既存テスト期待値や正しさ gate の緩和という疑義は `refuted`、重大度は `nit`。対象差分は記録と既存契約の説明に留まり、是正に実装追加は不要である。

## 総括

must-fix は **4件**（F1・F2・F3・F5）、nit は **1件**（F4）。
silo 昇格 consumer の実在反例は確認していないが、報告の根拠と限定には修正が必要。
README の exact-one 追記は実際に拒否へ接続しており、受理集合を広げていない。
`remaining: none` は上記訂正後に再判定する。
ファイル変更・テスト実行・commit・push は行っていない。