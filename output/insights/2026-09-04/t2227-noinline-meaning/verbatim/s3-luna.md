## 所見

1. 「対象 (`s2-plan.md:32-36,100-120`; `verbatim-decisions.md:82-94`)」  
「何が問題か」(P2) は実要求 0、実既定 0 に対して `default` slot を対照値 1 と読み替え、green 条件を requested `(0,1)` / comparison `(1,1)` に変える。これは D1490 の「要求値で `(1,1)`、既定値で `(0,1)`」の補足ではなく、`default` の意味を含む決定の書き換えである。  
「裁定にどう効くか」D1569 は A-2 の厳格化を命じるが、D1490 の値契約を明示的には改定していないため、ユーザー裁定パッケージが必要である。一方、macro 固有の枝選択 witness であり、BACKOFF_FIXED の scalar decoder を流用しないので D1242 の却下形には当たらない (`verbatim-decisions.md:75-80,106-107`)。  
「性質 (real / refuted)」real。  
「推奨する扱い」P2 と validator の逆順対応は裁定まで実装しない。「要求値と既定値」から「実要求値と識別用対照値」へ契約を変更するかを明示して裁定を受ける。

2. 「対象 (`s2-plan.md:58-120`; `condition_meaning_gate.py:180-211,873-888,2857-3035`)」  
「何が問題か」registry 登録と factory 拡張が D1569 の却下した「集合へ追加するだけ」かという懸念は成立しない。  
「裁定にどう効くか」集合の拡張は `MEANING_SUPPORTED_MACROS` の所属を増やすだけだが、witness の発行は factory が exact request に registry-bound declaration を返し、owner TU の実 compile command で観測して green/red を発行することである。plan は後者まで含み、旧宣言型も `BACKOFF_FIXED` 固定のままである (`condition_meaning_gate.py:533-549`)。  
「性質 (real / refuted)」refuted。  
「推奨する扱い」registry、macro 固有 factory、owner-TU 観測は維持する。`MEANING_SUPPORTED_MACROS` を直接編集する変更は加えない。

3. 「対象 (`condition_meaning_gate.py:553-571,3058-3071,4009-4027`; `s2-plan.md:132-138`)」  
「何が問題か」plan の「`ConditionalBranchMeaningDeclaration` は factory からだけ得られる」は文字どおりには偽である。型は公開 constructor として export され、registry tuple と一致すれば外部から直接構築できる。evaluator の factory 再導出と値比較は受理条件を守るが、発行元を証明しない。  
「裁定にどう効くか」受理集合が factory 条件より広がる穴ではないが、D1491 の「factory 以外から発行できない」という明文 (`verbatim-decisions.md:118-122`) とは衝突する。  
「性質 (real / refuted)」real。  
「推奨する扱い」D1491 を object 発行元まで要求する決定として守るなら、registry-bound だけでなく factory-issued を識別する狭い issuer 束縛が必要である。semantic equality で十分とするなら、その解釈を先に裁定する。

4. 「対象 (`s2-plan.md:38-42,256-280`; `verbatim-decisions.md:137-150`)」  
「何が問題か」D1492 に promotion 限定はなく、「raw だから配線しない」という境界は親が解釈で追加できない。実コードでは driver ごとの結論も plan と異なる。t1683 probe は `BACKOFF_NOINLINE` を要求し (`t1683_rr5_cost_probe.py:146-175`)、admission を `condition_gates` として出力 JSON に保存する (`:180-224,243-252`) ため、未配線では green/unestablished の分裂が残る。反対に `backoff_sweep` の実呼び出しは `BACKOFF_FIXED` だけ (`backoff_sweep.py:361-373`)、`silo_ladder_rung1` も FIXED と rung/report だけ (`silo_ladder_rung1.py:2173-2187`) である。`screening_driver` は要求し得るが gate の返値を捨てており (`screening_driver.py:543-549`)、admission は成果物へ載らない。  
「裁定にどう効くか」A-2、s1、t1683 は配線対象。backoff_sweep、screening_driver、silo_ladder_rung1 はそれぞれ上記の実理由で対象外となる。s1 は develop の raw role も同じ WAL に admission を載せる (`s1_direct_comparison.py:1001,1186-1198`) ため、plan の s1 配線自体は正しい。  
「性質 (real / refuted)」real。  
「推奨する扱い」t1683 と対応 test を変更面へ追加する。raw/promotion という新しい境界は削り、driver ごとに「要求の有無」と「admission carriage」で記録する。

5. 「対象 (`s2-plan.md:28-30,92-98,177-186,222-234`; `condition_meaning_gate.py:2681-2713,2828-2850`)」  
「何が問題か」依存 file の実読検査、新 reason code、marker 偽装負例は本題に必要ではない。計装 header が実際に読まれれば、その中へ挿入した completion marker が出力される。読まれなければ通常は両観測が `(0,0)` となり、既存の非識別判定で赤になる。plan の負例は owner が内部 marker macro を意図的に偽装する仮想リスク専用である。  
「裁定にどう効くか」D1490 が要求するのは owner TU 全体の実 compiler 観測であり、別の依存台帳を必須とはしていない。追加は D1569 の厳格化ではなく新しい防壁となる。  
「性質 (real / refuted)」real。  
「推奨する扱い」dependency file 読み取り、`compile-time-branch-instrumented-source-unobserved`、その負例と変異項目を削る。`-MD -MF` 自体は既存 preprocess argv に既に存在する (`condition_meaning_gate.py:1939-1992`) が、本 wave の新 witness 入力にはしない。

6. 「対象 (`paper_story_a2_certification.py:655-697`; `condition_meaning_gate.py:2409-2433,3743-3768`; `ruling-package.md:68-80`; `s2-plan.md:38-46`)」  
「何が問題か」A-2 の noinline meaning は factory 配線後に green になり得るが、D1523 対象の供給 arm が赤の間は admission は `False` のままである。A-2 は false admission で例外を投げ、receipt を append しないため、「成果物の未確立一覧が今すぐ縮む」は成立しない。  
「裁定にどう効くか」D1198 の独立性どおり、meaning の緑は supply の赤を救済しない。D1523 を本 wave で触らない判断は正しいが、効果は D1523 wave の取り込み後に fresh A-2 を再実行した時点で初めて成果物へ現れる。  
「性質 (real / refuted)」real。  
「推奨する扱い」plan にこの順序依存を明記する。本 wave では供給 arm を変更せず、直後の成果は「undeclared 理由が meaning の green/red に置換される」までとする。

7. 「対象 (`s2-plan.md:78-90,122-130,146-175`; `paper_story_a2_certification.py:589-612`; `condition_meaning_gate.py:1562-1614,1654-1684,2931-2983`; `test_condition_meaning_gate.py:142-236,1924-1935`)」  
「何が問題か」新入力が存在しない、または fixture 変更が既存 test を壊すという懸念は静的には成立しない。A-2 は patch 適用後の `variant_root` を capture し、`CMAKE_PREFIX_PATH` と `FETCHCONTENT_BASE_DIR` を保持する。configure は `compile_commands.json` を生成し、owner entry を `cc/silo/transaction.cc` と `ycsb_silo.exe` の一意な組で選ぶ。fixture の追加 3 行は EVOLVE block 外なので block 束縛に入らない。BACKOFF_FIXED の finite witness も抽出済み hole を使う。build-site fixture と t316 では NOINLINE は未定義または 0 なので追加枝は前処理で消える。  
「裁定にどう効くか」深い鏡像と compile operand の shadow owner TU への変更は、header 内の指令を owner TU 文脈で観測するために必要であり D1490 に整合する。共有 fixture への directive 追加も core positive test の実入力として妥当である。  
「性質 (real / refuted)」refuted。  
「推奨する扱い」深い鏡像、owner-TU operand、fixture 3 行、registry/patch 束縛 test は維持する。ただし実 CCBench の transaction.hh 中継と絶対 include 群で通るかは未実走なので、親 dogfood の確認対象に残す。

8. 「対象 (`s2-plan.md:140-220`; `test_condition_meaning_gate.py:727-867,1135-1180`)」  
「何が問題か」`test_condition_meaning_gate.py` では、registry parameter の 1 件増加で 2 configure、inert 正例で 2、requested=1 正例で 2、依存負例で 2、逆順 validator 用 green record で 2、合計 10 回の CMake configure 増加になる。A-2 stub test は 0 回。s1 正例を保存済み real helper 経由で行えば別 suite でさらに 4 回、stub なら 0 回であり、plan はここを確定していない。  
「裁定にどう効くか」依存検査を所見 5 のとおり削れば condition suite は 8 回増まで減る。現行 88 件 5.07 秒からは、10 回増で約 6〜7 秒、8 回増なら約 5.8〜6.5 秒が静的な目安で、5 分上限には十分収まる。  
「性質 (real / refuted)」real。  
「推奨する扱い」plan に configure 回数を記載する。validator は逆順 green と値束縛の最小負例だけ残し、既存 test と重複する same-count、argv-drift 等の追加は削る。

9. 「対象 (`brief.md:29-36`; `paper_story_a2_certification.py:791-842,1101-1108`; `s1_direct_comparison.py:487-490,525-527`; `t1683_rr5_cost_probe.py:226-252`)」  
「何が問題か」`output/` 内の既受理影響が空集合という実測は、その範囲では成立するが、全保存先の空集合には拡張できない。A-2 は policy の durable base 配下の `attempt/jobs/<workload>/scheduler/job.stdout`、s1 は任意 `output_root` の WAL、t1683 は任意の絶対 `--out` を持てる。もっとも、既知の A-2 失敗では false admission の canonical receipt は保存前に例外となるため、外部 attempt root に「admitted な unestablished admission」が残る経路は確認できない。`/work/1/SFC/tanab` に対する bounded path 名確認でも既知 attempt 名・既定 t1683 出力名は見つからなかったが、外部内容の全走査にはならない。  
「裁定にどう効くか」成果物への影響は一行で言えば、既存 certified 選択値・材料レポート・測定値は変わらず、future admission の record ID/digest・未確立一覧・参照だけが変わり、witness red の候補は受理集合から落ち、green は従来どおり残る。s1 の試行 WAL は `condition_gate` 部分の bytes が変わる。  
「性質 (real / refuted)」real。  
「推奨する扱い」記録は「repo `output/` 内は空集合、外部保存先は未確定」と限定する。migration 不要という結論も repo 内だけに限定する。

## brief と plan が正しかった点

- A-2 の要求値が 0、既定値も 0 で、現行 factory の 1/0 条件では未確立が縮まないという診断は正しい (`brief.md:50-55`; `condition_meaning_gate.py:873-883`)。
- A-2 は patch 済み木を検査し、その同じ `variant_root` を campaign build に渡す (`paper_story_a2_certification.py:589-612,3111-3131`)。
- supply arm、D1523、CLI、旧 `MeaningWitnessDeclaration` を触らない P6 は D1198、D1242、D1523 と整合する。
- header witness に深い鏡像と shadow owner TU が必要という P1 は、D1490 の「所有 TU 全体」を満たすための本題である。
- 旧宣言型が `BACKOFF_FIXED` 固定であることと、registry tuple を evaluator が再照合することは維持されている。
- A-2 と s1 の factory 配線、core 0/1 正例、factory 範囲 test、legacy 境界 test は必要な変更である。
- 実装を Codex author に一単位で渡す方針は D95 と整合する (`brief.md:151-154`; `verbatim-decisions.md:10-25`)。

## 総括

最も重い所見は、(P2) が D1490 の補遺ではなく値契約の書き換えであり、実装前のユーザー裁定を要する点である。  
次に、D1492 は raw を除外しておらず、admission を JSON へ保存する t1683 の未配線は実衝突である。  
依存 file の実読、新 reason code、marker 偽装負例は本題外なので削れる。  
A-2 の成果物上の効果は D1523 修正後の fresh run まで現れず、現時点では admission は false のままである。  
親が実測すべき点は、実 CCBench の中継 header を通る深い鏡像と、condition suite の実所要時間である。  
pytest は実行しておらず、外部 durable 保存先の内容も確定していない。