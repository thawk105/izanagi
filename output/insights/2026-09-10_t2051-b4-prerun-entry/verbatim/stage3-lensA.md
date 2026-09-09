## 親 brief への所見

中心結論は、**M11 の機械条件は正しいが、M13 と結合して「権威ある母集合が 0/201」とは言えない**、である。issuer が見るのは実 precursor ではなく caller が構成した行であり、母集合の権威 producer 自体が存在しない。

| ID | 実測の判定 | 一般化の判定・影響 |
|---|---|---|
| M1 | **real** — `p3_b4_material_report.py --help` は再実測 rc=0、不在 root は rc=2。 | **refuted** — 証明したのは CLI と拒否枝であり、valid production 入力から report が出る成功経路ではない。実 report・certified 選択は依然 0。 |
| M2 | **real** — T-2049 は producer/durable writer と report generator/sanctioned command の着地を記す。`2026-09-01_t2049-b4-material-report/README.md:18-39`。 | **refuted** — ここでいう producer は raw result producer であり、実 precursor から `B4ScheduledAttemptInput` を作る権威 producer を含まない。一般化すると L1 の欠落を隠す。 |
| M3 | **real** — T-2049 の「残る 1 語」という引用自体は正確。同 README `:20-24`。 | **refuted** — 5 語の履歴台帳内だけの話で、現在の formal entry には予定表 producer、publication caller、authority binding も残る。停止台帳の層数を過少報告する。 |
| M4 | **refuted** — T-2139 は「無条件 3 件 + 順方向の場合 1 件」の計 4 点。`2026-09-01_t2139-b4-certified-selection-connection/README.md:106-114`。 | 「現在は完成不能」は **real**。ただし 3 件だけを再開条件にすると、順方向接続を早く開く危険がある。 |
| M5 | **real** — `output/` の `report.complete` は 0、campaign source に material-report consumer はない。T-2139 `:57-61,106-114`。 | checkout と検索 root の範囲では **real**。certified 選択・耐久判定は変化しない。 |
| M6 | `output/` 配下 3 固定名が 0 件、という実測は **real**。 | 「production 成果物が全世界で 0」は **refuted**。issuer は caller 指定の任意の絶対 root を許す。`p3_b4_prerun_issuer.py:709-724`。検索 root 外の publication を排除できず、参照先の全称主張には使えない。 |
| M7 | **refuted** — 現在の `campaign.lock` は 30 でなく 32 件。ただし `b4_reflux_ablation` hit は 0。検索 root は `/work/1/SFC/tanab/izanagi/output`。 | B-4 marker 0 の結論は **real**。件数差は nit で、certified 選択・report 値は変わらない。 |
| M8 | **real** — bootstrap CLI は publication root と attempt ID を必須にする。`p3_b4_launcher.py:673-693`。 | 「publication が最初の停止点」は **refuted**。admission record 検証が先に走る。`p3_b4_launcher.py:381-386,561-589`。停止台帳の理由が変わる。 |
| M9 | 「repository 内の production caller と CLI がない」は **real**。定義は `p3_b4_prerun_issuer.py:709`、production 呼出しは 0。 | 「呼び手 0 件」を無修飾に言うのは **refuted**。test/support caller は複数ある。影響は production issuer が未到達のままで、台帳・manifest は発行されないこと。 |
| M10 | **real** — ledger 自身が authoritative producer の不在を明記する。`p3_b4_analysis_ledgers.py:1-6`。issuer も外部母集合への束縛なしを宣言する。`p3_b4_prerun_issuer.py:3-15,53-60`。 | **real** — これが最初の権威上の停止点。caller 値を採用すれば registry・manifest の値を偽装可能になる。 |
| M11 | **real** — `generate_analysis_manifest()` は caller-supplied registry の eligible 行が 201 未満なら `design_not_feasible`、以上なら先頭 201 行を採る。`p3_b4_analysis_ledgers.py:1050-1105,1140-1159`。 | 「201 個の実 precursor を要求する」は **refuted**。機械条件は 201 個の型付き行であり、実 artifact の存在を再導出しない。caller 自己申告で issuer の受理集合が開く。 |
| M12 | `REJECTED + 赤 class` が必要条件であることは **real**。`p3_b4_analysis_ledgers.py:922-936`。 | それが全条件であるとの一般化は **refuted**。`reason=scheduled`、calibration、bootstrap、unique reference、未汚染、hash 等も必要。省略すると適格集合を広く報告する。 |
| M13 | **refuted** — production 赤を一律 0 とする文言は追補自身が撤回した。`output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/s4_rejections_digest.txt:3,9,13` に赤節 3 件。 | 「観測済みで eligible は 0」は **real**。3 件の campaign には `loop_state.json` がなく、実在する 3 loop state の whiteboard 7 行は全て success。ただし権威母集合が未同定なので「母集合全体が厳密に 0」は **refuted**。report の precursor 数は「赤最大 3、適格確認 0」とすべき。 |
| M14 | **refuted** — `未記入` を含む値セルは 6 でなく 7 行。事前登録 `:159,162-167`。 | 「§6 の一条件でも欠ければ実走禁止」は **real**。`:624-684`。件数は直す必要があるが、formal 受理集合は依然空。 |
| M15 | **real** — manifest の path/hash/行数と registry の path/hash を要求し、規則参照だけの記入を禁止。事前登録 `:193-200`。 | **real** — caller が作った source-free bundle を §5 の権威値へ昇格させることを禁じる。 |
| M16 | **real** — closure 5 file の現 sha256 は事前登録 `:161` の全値と一致。 | **real** — この pin を動かす変更は分析意味を変える。現 plan の diff=0 は衝突しない。 |
| M17 | **real** — caller inventory は `analysis_path.evaluate_b4_artifacts` と非 export probe の exact 2 件。`orchestrator/tests/test_p3_b4_analysis_path.py:357-371`。 | **real** — 新しい `evaluate_analysis` caller を足す案は受理集合を変え、pin と衝突する。現 plan にはその変更はない。 |
| M18 | **refuted** —現在の `git worktree list` には当該 `dev-wave-t2051-b4-prerun-entry` が実在する。「t2051 無し」は brief ヘッダとも内部矛盾。 | 「未 commit 差分 hit 0 ⇒ 稼働 wave と編集面重複なし」も **refuted**。commit 済み作業面を検出しない。現時点では科学値を変えない operational nit だが、実装へ進むなら再確認が必要。 |

## 段 2 plan への所見

1. **real / must-fix — L2 の `design_not_feasible` は実測停止点ではない。**  
   plan `:24,64-68` は「0/201 なので issuer が停止」とするが、issuer を呼ぶ production caller はなく、実際の拒否 receipt もない。さらに issuer は caller-supplied 201 行なら publication を作れる。`p3_b4_prerun_issuer.py:709-805`、`p3_b4_analysis_ledgers.py:305-367,922-936`。  
   **影響:** L2 ledger は `state=stopped` でなく `state=unreached`。停止理由・参照・観測値が変わる。

2. **real / must-fix — L3 の停止理由と順序が誤っている。**  
   plan `:25` は publication 不在を理由にするが、3 admission record は全て不在で、launcher は publication を driver へ渡す前に `verify_b4_admission_record()` を呼ぶ。`p3_b4_launcher.py:381-386,561-589`。追補 A7 の実測も `record is unavailable`。  
   **影響:** formal-launch 台帳の first failure は admission record unavailable。publication rejection と記録すると停止層・参照が誤る。

3. **real / must-fix — M13 訂正を取り込んでいない。**  
   plan `:9,23,70-76,96` は 0 を維持するが、追補と実 artifact は赤節最大 3 を示す。  
   **影響:** precursor 報告値が変わる。eligible 確認数 0 と issuer 未到達は変わらない。

4. **real / must-fix — 権威境界を認識しながら、0/201 を権威値のように扱っている。**  
   plan `:39-41,64-68` 自身が caller-supplied 行と authoritative producer 不在を認める。`whiteboard_result`、赤 class、calibration、bootstrap、reference、hash はすべて caller が `B4ScheduledAttemptInput` へ書く。issuer はその batch を自己生成 commitment へ束縛するだけである。  
   **影響:** 201 個の自己申告行で registry・manifest・receipt が生成可能。これを §5 の実体として扱えば母集合、割当、report verdict を事後構成できる。

5. **real — 後付け可能性も閉じていない。**  
   issuer は別 root への再発行を防がず、seed の outcome 前発行も証明しない。`p3_b4_analysis_ledgers.py:8-11`、`p3_b4_prerun_issuer.py:8-16,53-64`。  
   **影響:** publication を権威化すると、結果を見た後の母集合・schedule 選択が可能になり、規律 3 と §5.1 `:193-200,358-408` に反する。

6. **real — 「発火しないから実装候補でない」という除外規則は強すぎる。**  
   T-2101 は formal run が現在発火しないことを明記しつつ、非恒真な pre-run predicate を受理している。`2026-09-09_t2101-proposal-binding/README.md:9-35,107-128`。  
   **影響:** この規則だけで候補を落とすと、formal launcher の受理集合を正当に狭める実装を見逃す。

7. **real — manifest membership は plan が落とした具体的な非恒真述語である。**  
   manifest は eligible の先頭 201 行だけを選ぶ。`p3_b4_analysis_ledgers.py:1071-1105`。一方、bootstrap binding は registry 全行から attempt ID を選ぶだけで、manifest を見ない。`p3_s4_loop.py:450-507`。base/sort/trigger の既存 loader がこの共通関数を呼ぶ。  
   **影響:** 現受理集合には manifest 外の registry attempt が含まれる。membership を要求すれば formal bootstrap の受理集合が 201 manifest rows へ狭まる。ただし母集合を manifest と registry のどちらにするか未裁定なので、直ちに実装せず裁定へ返すべき。

8. **refuted — plan 自体が verdict・受理集合を広げる変更は提案していない。**  
   diff=0 であり、規律 2/3 の直接緩和はない。manifest membership 候補も狭める方向である。  
   **影響:** 現 plan のまま certified verdict は変化しない。ただし caller-input CLI を追加する案へ転じれば上記 4・5 の権威破れになる。

9. **real — 「恒真な保証」に最も近い問題は、未発火なのに `state=stopped` と宣言すること。**  
   実装された新 guarantee は plan に存在しない。L2 の記述は mutation で検査された保証でも観測停止でもなく、入力を作らなかったことを拒否実績へ読み替えている。  
   **影響:** 台帳に存在しない rejection と参照を記録する「実装したふり」になる。

10. **refuted — closure pin / caller inventory との直接衝突は現 plan にはない。**  
    closure 5 hash は一致し、新 `evaluate_analysis` caller も提案されていない。  
    ただし `p3_b4_prerun_issuer.py:53-55,902-906` の固定 `formal_launcher_not_wired...` と事前登録 `:709-720` は現 launcher と食い違う。固定 receipt field と凍結文面なので、黙って直す対象ではない。  
    **影響:** 現状では receipt の non-guarantee 値・文書参照が古い。変更するなら erratum が必要。

## P1 を倒す反例 (あれば)

**「今日 production で発火する、裁定不要の純増」については反例なし。** admission record、§5、floor、権威母集合が未充足だからである。

ただし、P1 の証明連鎖は **refuted** である。

- **機械的反例:** 型を満たす caller-declared eligible 行を 201 件渡せば、実 precursor が 0 件でも issuer は manifest を生成できる。根拠は `p3_b4_prerun_issuer.py:709-849` と `p3_b4_analysis_ledgers.py:922-936,1050-1105`。これは権威違反なので正当な実装候補には数えないが、「0 production precursor ⇒ issuer が必ず拒否」は偽。
- **最強の実装候補:** manifest membership。既存 production consumer があり、正例・負例で値が変わり、受理集合を狭め、closure 5 や `evaluate_analysis` pin に触れない。ただし T-2101 が「母集合は manifest 201 行か registry 全行か」を明示的な未裁定事項としている。`2026-09-09_t2101-proposal-binding/README.md:170-180`。

したがって、**P1 の diff=0 結論はまだ成立し得るが、理由は「0/201」ではなく「必要な authority ruling が未決」でなければならない。**

## 裁定パッケージ候補

1. **real — formal B-4 の実行集合を manifest 201 行に限定するか、registry 全行を許すか。**  
   影響: launcher の attempt 受理集合、manifest 外 attempt の build/WAL 到達可否、全件報告範囲。

2. **real — authoritative publication を誰が、どの root/receipt pin で一意に指名するか。**  
   影響: 別 root 再発行による母集合・schedule・report 参照の差替え可否。

3. **real — publication receipt hash・attempt ID・manifest membership の成功をどの耐久 carrier に残し、どの sink が必須参照するか。**  
   影響: 実走後の attempt 付替え、raw record と report の出所束縛。

4. **real — continuation の初期 proposal を復元する carrier を新設するか。**  
   T-2101 `:58-69,170-174`。影響: continuation 結果を同じ precursor block へ正当に帰属できるか。

5. **real — 古い固定文言の erratum。**  
   issuer の `formal_launcher_not_wired_to_require_this_receipt`、事前登録 §7.2、closure-pinned `p3_b4_analysis_path.py:13-15` は現実装とずれている。影響: receipt の non-guarantee 値と文書参照。erratum なしの直接編集は不可。

6. **real — §5 の開始時刻 sentinel を発効版でどう扱うか。**  
   事前登録 `:275-287` が未裁定を明記する。影響: admission record が §5 placeholder gate を越えられるか。

## 総括

段 2 plan はそのまま採用不可。最低限、停止列を次へ直す必要がある。

- L1: 権威ある予定表 producer 不在。観測済み eligible は 0 だが、権威母集合の全称カウントは不能。
- L2: issuer は `stopped` でなく `unreached`。短い caller list なら拒否、201 自己申告行なら機械的には発行可能。
- L3: 実測 first failure は admission record unavailable。
- L4/L5: production report・certified connection は未到達。

P1 の「今日は発火しないから実装なし」という一般原則は T-2101 先例で崩れる。一方、具体候補の manifest membership は母集合の権威裁定が必要なので、現 consult だけで実装へ送ってはならない。

書込み、pytest、build、qsub、性能測定、formal B-4 実走は行っていない。