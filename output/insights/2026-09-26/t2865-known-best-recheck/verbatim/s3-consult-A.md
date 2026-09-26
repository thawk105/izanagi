## 所見

1. **must-fix — P2 の分類に優先順位がない。** [brief.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/brief.md:7>) は「点の verify 失敗」を失格、「参照不適格・束縛不成立」を判定不能とするが、両方が同時に起きた場合を定めていない。また [driver](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/orchestrator/campaign/silo_policy_recon.py:447>) は IR 点自身の理由を参照より先に選ぶ。**影響:** 同一 JSON を「失格」とも「判定不能」とも記録でき、論文に載せる点の集合が変わる。**代案:** まず job と点の束縛を確認し、不成立なら判定不能。成立後は対象点の verify／trace0 失敗を失格、それ以外の不適格を判定不能、最後に比を判定する順序を明記する。参照 1 本の不適格、参照の前後 evidence の片方欠落、相方 IR の失敗は、対象点の比を都合よく再計算する理由にしない。

2. **must-fix — P3 の投げ直し条件と試行の採用時点が曖昧。** [brief.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/brief.md:8>) の「error で点の行が無い」は、行がある途中失敗や参照不適格を含まない。一方、[driver](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/orchestrator/campaign/silo_policy_recon.py:230>) は各 case の失敗を行の status に収めて次へ進み、job の一部を終えた後の例外は `error` と部分的な行を残す。**影響:** 完了後の不利な値を「infra」と呼んで再投入すると、再測の選別が後付けになる。**代案:** 起動前失敗、または対象点の行を一つも生成せず終了した job のみ、値を見る前に 1 回再投入する。部分 JSON に対象点の行があれば採用して判定不能を含む規則を適用する。pre-running の競走では、採用する試行を結果 JSON を開く前に完了順で固定し、各試行を残す。

3. **should — P5 の正例一致だけでは束縛照合を保証しない。** [brief.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/brief.md:10>) の旧 16 点完全一致は、正常データだけの検査である。既存の [_compare_detail](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/orchestrator/campaign/silo_policy_recon.py:367>) は case の順序・role・本文・因子・対照 genome・fixed10 の両 trace define に加え、[source evidence が非空で前後一致すること](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/orchestrator/campaign/silo_policy_recon.py:418>)を検査する。**影響:** 新集計がこの一つでも落とすと、本来 null の点に比と「再現」を付けうる。**代案:** 旧 8 job との一致に加え、新スクリプトの該当照合を静的レビューし、少なくとも evidence 欠落と fixed10 define 不成立の入力を拒否することを確かめる。既存 `compare-aggregate` は 8 job と同一 PIN を要求するため、旧 5 job と新 3 job を混ぜてそのまま使うことはできない。

4. **should — 見積りの上限が P3 と一致しない。** [brief.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/brief.md:12>) は infra 再投入を「1 本」だけ加算するが、[P3](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/brief.md:8>) は 3 job のそれぞれに 1 回を許す。元の実測単価は [768〜779 秒／job](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md:122>)。**影響:** 検査込み合計「≦約 1.4 node 時間」と、2 時間の確認要否を過小評価する。**代案:** 最大 6 計測 job で約 1.30 node 時間とし、受入全走の実測単価・予定回数、焦点走が必要になる条件を別に足す。受入 0.25 時間を 2 回と仮置きすれば約 1.80 時間で、追加の焦点走を含む上限は現 brief からは確定しない。実装差分ゼロなら変異 matrix 免除という扱いは妥当。

5. **should — 「別 job」の効力を限定して記述する。** [_cases](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/orchestrator/campaign/silo_policy_recon.py:35>) は常に IR 2 点と参照 4 本を入れ、job 番号 mod 6 で巡回する。元 JSON の順序も job 0＝`0000,1111,…`、1＝`1110,…,0001`、6＝`0110,1001,…` で一致する。したがって新 job でも対象点の位置は同じである。**影響:** 別 job で比が再現しても、対象点固有の実行位置や job 内の熱・周波数の影響から独立した再現、と論文に一般化すると過大になる。**代案:** 既存 driver を使い、3 つの独立した job で再測した、と正確に書く。相方 IR の結果は対象点の判定に使わない。単点 mode のコード追加は今回の「本題だけ」に対して過剰。

6. **nit — PIN 差の説明は範囲を絞る。** `git diff --stat e9e477ca 68106660` は実行でき、差分は `cc/mocc/transaction.cc` の 64 行追加のみだった。[brief.md](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/brief.md:9>) の「silo の build 入力は同一」は、差分統計だけからビルド全入力の同一性まで証明した表現になる。**影響:** insight が旧・新 PIN のバイナリ同一性を保証したかのように読まれる。**代案:** 「確認した CCBench の差分は mocc の当該ファイルのみ。PIN 差を記録し、同一バイナリの証明とは扱わない」と書く。PIN 差だけを理由に再測を無効化する必要はない。

[failures.md](</work/1/SFC/tanab/izanagi/.claude/worktrees/t2865-known-best-recheck/docs/failures.md:21>) の型タグでは、正例だけで集計を通したことにする **[恒真ゲート]・[テスト代表性]**、結果を見て再投入や閾値を変える **[手順漏れ]**、別 job の観測を統計的優位へ広げる **[捏造/幻覚]・[計測汚染]** が再発しうる。

## brief の前提の判定

| 項目 | 判定 | 理由 |
|---|---|---|
| P1 | **要修正** | 既存 compare は各 job に相方 IR も入る。「1 点 1 job」は対象点ごとに別 job を割り当てる意味なら満たすが、厳密な単点構成ではない。 |
| P2 | **要修正** | 分類の優先順位と欠損時の扱いを固定する必要がある。 |
| P3 | **要修正** | 部分完了 job と pre-running 競走の採用規則を固定する必要がある。 |
| P4 | **要修正** | 差分の実測は real。ビルド全入力同一という一般化を限定する。 |
| P5 | **要修正** | 8 job・PIN 制約は real。旧データ完全一致だけでは束縛照合の正例に偏る。 |
| 判定規則 | **要修正** | `r′ = 1.03` は非再現と一意にできるが、複数の不適格理由の優先順位が未固定。 |
| 見積り | **要修正** | 再投入を最大 1 本としている一方、P3 は最大 3 本を許す。 |

## 推奨する判定規則 (最終形)

> 対象は事前に固定した `1111`（job 0）、`1110`（job 1）、`1001`（job 6）で、各対象について別々の compare job を 1 本採用する。採用試行は結果の throughput・abort 率・比を読む前に固定する。起動前失敗、または対象点の行を一つも生成せず終了した場合だけ、同じ job 番号を最大 1 回再投入する。pre-running で重複投入した場合は先に完了した試行を採用し、他方も記録する。完了後の参照不適格や対象点の不利な値を理由に再投入しない。
>
> まず採用 job の phase、job 番号、case_order と各行の role・順序、対象点の本文 SHA-256・因子、abort0 本文、参照 genome、fixed10 の trace1／trace0 実効 define、固定 workload と source evidence、旧計測とは異なる job の識別情報を照合する。対象点を判定できない束縛不成立または行の欠損は **判定不能** とする。束縛成立後、対象点の `verify-not-certified` または `trace0-not-clean` は **失格** とする。それ以外で対象点・abort0・参照 3 本のいずれかが D2240 項 2 の条件を満たさない、または対象点が high-abort なら **判定不能** とする。相方 IR の適格性は対象点の条件に含めない。
>
> 残る対象点について、5 rep throughput 中央値を、同じ job の stock・B0-L-W0・fixed10 の各中央値の最大値で割った `r′` を算出する。`r′ > 1.03` は **再現**、`r′ ≤ 1.03`（ちょうど 1.03 を含む）は **非再現** とする。fixed10 が最良参照でなくても最大値を分母に使い、fixed10 比も併記する。再現した点だけを「別 job 再測でも、同 job の測定済み既知参照の最良を 3% 超えた」と記述する。「3 点とも」は 3 点すべて再現した場合だけ用いる。
>
> この再測は、16 点から 3% 超の 3 点を選んだ後に、別 job の値でその観測を確認するもの。元と新の比を平均して判定せず、元の選択値を新たな独立証拠として数えない。5 rep の最小が fixed10 の最大を超える条件は、主判定には加えず補助的に報告できる。3% 線は未較正であり、統計的優位、多重選択を補正した有意性、別 workload への転移を主張しない。この限定を新 insight の判定規則と結論、および論文の当該記述の近くに置く。

`r′ > 1.03` は論文の限定された文「別 job 再測でも既知最良を 3% 超えた」に過不足が少ない。fixed10 比にも同じ閾値を課す案は、分母が参照 3 本の最大値であるため常に満たされる冗長条件になる。5 rep の完全分離を必須にする案は記述以上に強く、元・新の平均は選択バイアスを再び判定へ混ぜる。

firewall は `projection.json` を書き換えないだけでは完結しない。[手順書](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/verbatim/axis-onboarding-firewall.md:8>) が対象とする漏洩経路は、insight を読んだ人が coder 入力や planner direction を起草する過程にもある。新 insight・結果 JSON・集計 JSON を段階 E/F の入力に渡さず、読んだ事実は provenance に残す、という既存の運用を守ればよい。

## 総括

**adopt_with_conditions**。must-fix は **P2 の分類優先順位**と **P3 の値を見る前の再投入・採用規則**。あわせて見積りの上限を P3 と揃え、集計の束縛照合を確認してから実走する。