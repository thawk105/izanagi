## 所見 1 — 7 個の逐語アンカーはすべて実在し、一意である

(i) 主張  
プランの現行 215 / 262 / 680 / 887 / 997 / 1002 / 1057–1061 行という位置指定に誤りはない。各アンカーの完全一致件数はすべて 1 件だった。

(ii) 現物の逐語根拠

- [215 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:215): `**その artifact path と sha256 を値として書けるとき**だけである ...`
- [262 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:262): `実際の開始時刻は...`
- [680 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:680): `不都合な campaign を別 root へ...`
- [887 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:887): `- file-drawer の機械強制 ...`
- [997 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:997): `上表が割り当てた決定主体は変えない...`
- [1002 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1002): `**本節は測定を許可も要求もしない。**`
- [1057–1061 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1057): プラン記載の括弧内注記と逐語一致。先頭行も文書内で 1 件だけなので範囲は一意。

(iii) 放置時の破損  
この点では破損しない。各編集点は機械的に一意に同定できる。

(iv) 判定  
real — 誤りなし。

## 所見 2 — pair-sample 以下の算術は正しいが、「1 セル」の個数は 1 pair 前提を欠いている

(i) 主張  
「1 pair-sample = 2 side session」「1 side session = candidate 1 + reference 1 = 2 measurement」は正しい。一方、「1 セル = 124 pair-sample」は driver 単体からは導けず、各 campaign の当該セルに `pair_id` が exact 1 件という前提が必要である。

(ii) 現物の逐語根拠  
[driver 1347–1351 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1347) は、各 window について `pair_ids × range(sample_count)` を作る。  
[1365–1421 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1365) は `_SIDE_IDS` の各要素につき 1 session を作り、各 session に `_MEASUREMENT_ROLES = ("candidate", "reference")` の 2 measurement を作る。  
[1429–1441 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1429) が、pair-sample ごとに exact 2 session、exact 4 measurement、各 session の role が candidate/reference であることを検査する。  
[2709 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:2709) の実集計も `pair_sample_count = window.sample_count * len(window.pair_ids)` である。対象文書自身も [1047 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1047) で「この算術がそのまま言えるのは 1 pair の場合だけ」と限定している。

したがって、campaign ごとの pair 数を `P` とすれば、2 campaign・n=62 の正しい一般式は次のとおり。

- pair-sample = `124P`
- side session = `248P`
- measurement = `496P`
- candidate measurement = `248P`
- reference measurement = `248P`

`P = 1` のときだけ、プランの 124 / 248 / 496 になる。

(iii) 放置時の破損  
複数 pair を持つ spec で費用を `1/P` に過小評価する。driver が保証していない「セルあたり exact 1 pair」を事実として事前登録へ焼き込む。

(iv) 判定  
real。

## 所見 3 — `REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE = 2` は pair-sample あたり 2、side あたり 1 である

(i) 主張  
親・プランの解釈は正しい。「side あたり reference 2」ではない。

(ii) 現物の逐語根拠  
定数は [70 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:70)。実際に数える [1423–1437 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1423) は、2 つの `sample_sessions` に含まれる全 measurement を flatten して、`role == "reference"` の総数が 2 であることを検査する。続く [1438–1441 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1438) が各 side session の role 集合を `{candidate, reference}` に固定するため、side あたり reference は 1 件である。  
最終計算も [2956–2960 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:2956) で `reference_1` と `reference_2` を別々に使う。

(iii) 放置時の破損  
誤って side あたり 2 と読むと pair-sample あたり 6 measurement と数えるが、現実装は 4 measurement である。親・プランにはこの誤りはない。

(iv) 判定  
real — 誤りなし。

## 所見 4 — 7,440 秒は正しい名目値だが、brief の「起草時 248 / 3,720 / 1,860」は誤記である

(i) 主張  
1 pair 前提で `496 measurement × 5 reps × 3 秒 = 7,440 秒` は正しい。ただし brief 73 行の「起草時は 248 session / 3,720 秒 / 1,860 秒」は時系列上誤りである。起草時は 236 / 3,540 / 1,770 だった。

(ii) 現物の逐語根拠  
driver は 5 reps・3 秒を定数化していない。`reps` と `extime` は任意の正整数として読む [775–795 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:775) もので、実測呼出しにもその spec 値を渡す [1590–1597 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1590)。したがって 7,440 秒は実測保証ではなく、プランが明記した比較用名目値に限って正しい。

正しい推移は次のとおり。

- 起草時 n=59、2 campaign: 118 pair-sample、candidate 236 session = 3,540 秒、reference 118 session = 1,770 秒、計 5,310 秒。
- D1695 後の旧構成: 124 pair-sample、candidate 248 session = 3,720 秒、reference 124 session = 1,860 秒、計 5,580 秒。
- D1699 後の現構成: 124 pair-sample、248 side session、496 measurement、名目 7,440 秒。

対象文書 [1057–1058 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1057) も起草時値を 236 / 3,540 / 1,770 と明記する。これに反して brief [73 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:73) は D1695 後の値を「起草時」と呼んでいる。段 2 プラン [129 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:129) の推移は正しい。

(iii) 放置時の破損  
標本数変更と session 構成変更の効果を混同し、どの差分で費用が増えたかを誤って説明する。

(iv) 判定  
real。

## 所見 5 — 機構は実在するが、実在範囲は library と任意の local issuer までである

(i) 主張  
「registry・manifest・完全性検査のコードが実在する」は正しい。ただし「append-only registry の機構が実在する」を operational な永続台帳まで含む意味で読むと、プランは言い過ぎである。

(ii) 現物の逐語根拠  
[analysis_ledgers 157–167 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:157) は registry を「sealed scheduled batch plus append-only violation events」と定義する。[670–683 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:670) は scheduled batch を一括 seal し、「no single-attempt API exists」と明記する。append できるのは [772–811 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:772) の violation event であり、旧 canonical bytes の prefix を維持した新しい値を返す。

manifest generator は [1050–1105 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:1050)、完全性検査は [1140–1185 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:1140) に実在する。local issuer も発行時 [807 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:807) と reload 時 [1141 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:1141) にこれを呼ぶ。

一方、issuer 自身が [8–16 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:8) で、formal launcher が receipt を要求しない、外部の権威ある母集合と束縛されない、別 root 再発行を防がない、と列挙する。永続発行も [623–625 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:623) の create-only な registry/manifest bundle であり、issuer から `append_registry_violation` を呼ぶ箇所はない。

現物から言える正確な範囲は「sealed registry のデータ型、violation の prefix-preserving append 純関数、manifest generator、exact regeneration validator、任意の local create-only publisher が実在する」までである。権威ある producer・formal launcher の必須配線・end-to-end file-drawer closure は実在しない。

(iii) 放置時の破損  
「機構のコードがある」と「正式走で必ず使われる operational registry」が混同され、§6 条件 9 や §7.1 の全件報告が実効化済みと誤読される。

(iv) 判定  
real。

## 所見 6 — `output/` の「実体 0 件」は B-4 固有なら真、無限定なら偽である

(i) 主張  
brief とプランの「`output/` 配下に manifest と registry の実体は 1 件もない」は、B-4 issuer 固有の成果物という限定が必要である。

(ii) 現物の逐語根拠  
issuer の固定名は [46–48 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:46) の次の 3 件。

- `scheduled-attempt-registry.jsonl`: 0 件
- `analysis-manifest.json`: 0 件
- `prerun-issuer-receipt.json`: 0 件

さらに `p3-b4-scheduled-registry/v1` または `p3-b4-analysis-manifest/v1` の schema を持つ非圧縮 file も 0 件だった。したがって「B-4 issuer publication の実体は 0 件」は正しい。

一方、`find output -type f \( -iname '*manifest*' -o -iname '*registry*' \)` は 70 件を返した。例として `output/registry/t139-alpha-reservations.jsonl` や多数の `manifest.json` が実在する。無限定の「manifest と registry は 1 件もない」は字義どおりには偽である。

(iii) 放置時の破損  
既存の別用途 manifest/registry まで不存在とする虚偽の現況主張になる。B-4 固有の固定名または schema を指すと限定すれば事実になる。

(iv) 判定  
real。

## 所見 7 — 同型の機構不存在断言は、§7.2 / §10 以外に未訂正のまま残ってはいない

(i) 主張  
文書全体を走査した結果、B-4 registry/manifest/completeness 機構について、今回の §7.2 と §10 以外に同型の未訂正断言は見つからなかった。

(ii) 現物の逐語根拠

- §5.1 の [210–215 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:210) は primary outcome 欄の古い現在地を含むが、scope 1 の直後追記がまさに訂正するため本 wave 内。
- §5.1.1 の [587–593 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:587) と §6 の [652–655 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:652) は「実在を発効条件として要求する」という規範であって、現在不存在との断言ではない。
- §2.3 の [96–100 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:96) は機械導出制約を使う「新架構」の不存在であり、今回の B-4 analysis ledger とは別物。本 wave 外。
- §8 の [763–780 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:763) は critic 能力遮断などの非保証で、別機構。本 wave 外。
- §11.0 の古い floor 接続断言には既に [918–926 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:918) の T-2424 erratum がある。
- §11.2 の driver 不在断言には [1092–1101 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1092) の D1694 erratum がある。
- §11.3 の floor 接続断言にも [1115–1122 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1115) の T-2424 erratum がある。

(iii) 放置時の破損  
追加の取り残しはないため、本項を理由に scope を広げる必要はない。

(iv) 判定  
real — 追加の同型欠陥なし。

## 所見 8 — 追記本文案は living-doc lint の禁止形式に触れていない

(i) 主張  
対象文書へ挿入予定の本文には、他文書への行番号参照や `check_docs.py` の明示的禁止形式は見つからない。

(ii) 現物の逐語根拠  
対象文書は `LIVING_DOCS` に明示列挙されている [check_docs.py 124–146 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/tools/check_docs.py:124)。禁止する行番号参照は [171–179 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/tools/check_docs.py:171) の `.md:数字`、`.md の N 行`、`line N 参照`。追記本文案にはいずれもない。  
[6701–6740 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/tools/check_docs.py:6701) が検査する `現在は Phase`、`次 =`、CURRENT_PIN literal、実在しない path もない。本文案が挙げる 6 個の Python path はすべて regular file として実在した。F36 の禁止 placeholder 3 語 [206–210 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/tools/check_docs.py:206) も含まない。

(iii) 放置時の破損  
対象文書の追記本文については、静的に確認できる living-doc 違反はない。

(iv) 判定  
real — 誤りなし。

## 所見 9 — worklog 内容は検算不能で、brief とプランの変更 file 数も矛盾している

(i) 主張  
worklog が可変状態を再掲していないことは、段 2 プランに worklog 本文案が無いため検算できない。また変更 file 数の主張が brief とプランで一致しない。

(ii) 現物の逐語根拠  
brief [93–95 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:93) は対象文書に加え `output/insights/...` と `docs/spool/` の worklog fragment を成果物として要求する。対してプラン [3 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:3) は対象を 1 文書だけとし、[141 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:141) は「変更 file が対象文書 1 件だけ」と検査するとしている。提供資料には worklog 本文案がない。

(iii) 放置時の破損  
brief どおり metadata を作ればプランの「1 file だけ」が偽になり、作らなければ brief の成果物が欠落する。worklog の内容上の規約適合も、現プランからは肯定できない。

(iv) 判定  
real — 矛盾と検算材料欠落は実在する。実際の worklog 本文が規約違反かどうかは未判定。

## 所見 10 — bytes pin の 312–596 行という導出は正しい

(i) 主張  
凍結範囲と全編集点の範囲外判定に誤りはない。

(ii) 現物の逐語根拠  
`_locate_section()` は [301–321 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301) で、fingerprint に一致する exact 1 個の H4 を始点とし、その後最初の level <= 4 見出しを終点にする。対象文書では始点が [312 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:312)、次の level <= 4 が [597 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:597) の `## 6.`。したがって slice は現行 312–596 行を包含する。

この範囲の実測 sha256 は `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30` で、consumer [47–49 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47) と一致した。

編集点 215・262 は始点より前、680・887・997・1002・1057–1061 は終点より後である。前方への挿入後は物理行番号がずれるが、H4 から H2 直前までの raw bytes 自体は変わらない。

(iii) 放置時の破損  
この点では破損しない。プランが「現行 312–596 行」と限定しているのも正しい。

(iv) 判定  
real — 誤りなし。

## 所見 11 — 「発効版では開始時刻を別文字列にする」は裁定に無い新規規範である

(i) 主張  
プラン本文案の `開始時刻 = 予定日時の事前指定なし` は、D1649/D1812 の反映ではなく未裁定の追加である。

(ii) 現物の逐語根拠  
D1649 は [rulings 86–90 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:86) で、予定開始時刻拘束を外し、欄は「`未記入` のままでよい」、実時刻は実走成果物側の既存記録だけを正本とすると明記する。D1812(b) も [8–10 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/verbatim/rulings.md:8) で固定日時を指名しないことだけを裁定する。

これに対してプラン [43 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:43) は「発効版では ... `開始時刻 = 予定日時の事前指定なし` と記す」と規範化し、[157 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage2-plan.md:157) でも推奨している。現行 parser が `未記入` を拒否するという事情は、D1649 の逐語を別の受理文字列へ変える裁定にはならない。

(iii) 放置時の破損  
本 wave が「既裁定の反映」ではなく、開始時刻欄の新しい値と将来の発効手続きを独自に裁定したことになる。現在の値セルを変更しなくても、本文に未裁定の将来義務が残る。

(iv) 判定  
real。

## 所見 12 — brief に行番号と引用帰属の小さな誤記がある

(i) 主張  
brief の現物参照には 2 件の軽微な誤記がある。

(ii) 現物の逐語根拠  
brief [67–68 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:67) は「行 72 `DIFFERENCE_FORMULA =`」とするが、代入文の開始は driver [71 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:71) で、文字列本体が 72–73 行である。

また brief [83–86 行](/home/SFC/tanab/.claude/jobs/74c07adf/tmp/wave-t2140-t2414/stage1-brief.md:83) は issuer を挙げた直後に「同 module の docstring」として `"this module does not create or identify the authoritative producer..."` を引用するが、この逐語は [analysis_ledgers 3–6 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_ledgers.py:3) にあり、issuer の docstring ではない。issuer は別の非保証を [8–16 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_prerun_issuer.py:8) に列挙する。

(iii) 放置時の破損  
結論自体は変わらないが、親の引用を追跡した読者が誤った module を確認する。

(iv) 判定  
real。

## 総括

must-fix:

- 「1 セル = 124 pair-sample」は exact 1 pair 前提を明記する。一般式は `124P / 248P / 496P`。
- registry の実在を、library-level の sealed registry・violation append 純関数・local issuer までに限定する。formal launcher への必須配線や operational append 台帳は実在しない。
- `開始時刻 = 予定日時の事前指定なし` を既裁定の反映として扱わない。D1649 の逐語は `未記入` のままでよい。
- brief の成果物 3 系統と、プランの「変更 file 1 件だけ」を整合させる。worklog 本文は現資料では規約検算不能。

nit:

- brief の「起草時 248 / 3,720 / 1,860」は D1695 後の旧構成値。起草時は 236 / 3,540 / 1,770。
- `output/` の実体 0 件は B-4 issuer の固定名/schema に限定すれば真。無限定では 70 件の manifest/registry 系 file がある。
- brief の `DIFFERENCE_FORMULA` 行番号は 71 行開始。
- authoritative producer の引用元は issuer ではなく `p3_b4_analysis_ledgers.py`。

誤りなし:

- 7 個の逐語アンカーと一意性。
- reference は pair-sample あたり 2、side あたり 1。
- exact 1 pair・名目 5×3 秒という条件下の 248 session / 496 measurement / 7,440 秒。
- bytes pin の現行 312–596 行、hash、一連の編集点がすべて範囲外であること。
- §7.2 / §10 以外に、同じ B-4 ledger 不存在断言の未訂正取り残しはない。