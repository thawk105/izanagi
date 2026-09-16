## 所見

**MUSTは0件。実装の裁定違反、段3所見の実装への反映漏れ、scope外の追加は見つかりませんでした。記録上のNITが1件あります。**

**RB-1・NIT — 最終記録に再現条件とcaller説明の訂正を明記する。**

- **主張:** 予定文「既定を替えると legacy 経路で偽 hit する欠陥を実測で再現し、修正後は同条件で miss になることを確認した」は、存在する欠陥の再現という意味では正しい。ただし単独で記録すると、実CCBench binaryや各production caller全体まで検証したと読める。旧briefの誤記も最終記録へ転記しないこと。
- **根拠:** job内 `s1-brief.md:5,10` にs1のstock control扱い、pipelineのcompiler伝播、研究停止の広い表現が残る。訂正は `s4-ruling.md:10–22`。実測の対象は `probe/before-hit-gcc.json:43–49,96–109` と `probe/after-hit-gcc.json:18–42,158–171`。極小C++を生成する実体は `t785_legacy_cache_probe.py:116–124`。
- **成果物影響:** certified選択・key・受理集合は変わらないが、レポート／台帳が主張する検証済み範囲と証拠への参照が広がる。記述の限定で解消でき、追加実装・gate・検査は不要。
- **書き換え案:**

> Pegasus login node上で、実ccbench checkoutのsource evidenceとstock admissionを用い、cmake実行を極小C++ ELFの生成に置き換えたproduction legacy `build()` probeを実施した。`silo|BACK_OFF=1`・`trace=False`について、既定をgcc-12/g++-12からgcc/g++へ替え、receiptが一致する条件で、修正前は旧compiler製ELFへの偽hit、修正後はkey分離と新compilerによる再生成を確認した。

最終記録に維持すべき訂正は次のとおり。

- pipelineのlegacy分岐はcc/cxxを省略する。compiler入りの`common`はbuild_v2側で使用する。現物は `orchestrator/campaign/pipeline.py:1992–2013`。
- 引用されたs1のbuildはgenerator receiptを伴う生成物buildであり、stock controlではない。`orchestrator/campaign/s1_verify_extime_calibration.py:372–396`。
- between_run_floorはPegasus分岐だけcompilerを明示し、非Pegasusでは省略する。`orchestrator/campaign/between_run_floor.py:315–328`。
- 「研究停止なし」は「T-785に起因すると確認された研究停止は提示資料にない」に限定する。`s4-ruling.md:20`。
- receiptはcompiler依存のsource digestを含む。既定変更一般が必ず偽hitするとは書かない。`s1-brief.md:26`。
- probeは各CLI全体、trace=True、生成物admission、CCBench実行・性能値・certified選択の検証ではない。

## 親の実測の検算

以下、コードの相対パスは指定repo root、job内資料の相対パスは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t785-legacy-cache-key` 基準。

**裁定§6・所有範囲**

`git diff 0c292eff6 6022f70d7` は指定2ファイルだけ、31行追加・2行削除。production変更は `orchestrator/campaign/buildcache.py:635–641` のdocstringと`tc`行のみ。`DEFAULT_*`を省略条件に使用していない。引数既定・caller・build_v2・hit検査の変更はない。

新規テストは指定位置に1本だけで、全要件を備える。

| 要件 | 現物 |
|---|---|
| (a) DEFAULT未変更・cc/cxx省略でHを取得 | `orchestrator/tests/test_campaign.py:3215` |
| (b) 2組のDEFAULT変更と明示要求がHと異なる | 同`:3217–3223` |
| (b) 新要求同士も異なる | 同`:3228` |
| (c) DEFAULT変更中でも歴史的組はHを維持 | 同`:3225–3227` |

`6022f70d7`に対する現在のtracked差分も空だった。「所有外変更なし」はこのcommit差分について確認できる。authorが過去に一時編集した全履歴まで証明するものではない。

**段3所見との対応**

| 所見 | 裁定での扱い | 照合結果 |
|---|---|---|
| S-1 | 採用、記録訂正 | 裁定`:10`とpipeline現物が一致。caller変更不要 |
| S-2 | 採用、3判定を導入 | 両JSONに成立条件と比較値あり。単なるcached期待一致に依存していない |
| S-3 | 不要化 | 対象の変異7・8／第3テストは追加されていない |
| S-4 | 採用 | seedはg++-12、要求はg++。realpath・版の両方が異なる |
| L-1 | 採用、単文手順化 | 裁定`:43–55`に反映。全操作履歴の実行順は今回の資料では独立確認していない |
| L-2 | 採用、相ごとの復元 | 裁定`:47–54`に反映。現在のtracked差分は空。各相の途中復元まではJSON単独では証明できない |
| L-3 | 採用、未再現ならF停止 | 修正前JSONで偽hit成立を確認。Fへ進む条件を満たす |
| L-4 | 採用、caller／s1説明訂正 | 裁定`:10–11`と現物が一致。最終記録への転記はRB-1参照 |
| L-5 | 採用、compiler候補限定 | 実際の比較組は12.3.0対11.4.0。同一実体の別名比較ではない |
| L-6 | NIT採用、参照訂正 | 裁定`:18`に反映。Fの2行追加後に引用する際は行番号を更新する |
| L-7 | 採用、scope縮小 | 新規テスト1本・登録変異3本に一致 |
| L-8 | NIT採用、研究停止の限定 | 裁定`:20`に反映。最終記録も限定を維持する |

採用済みなのに実装が必要なものを欠いている、という所見はない。L-1/L-2の操作履歴は未検証であり、違反と認定していない。

**変異§7**

現物の完全な`tc`代入行は `orchestrator/campaign/buildcache.py:641` の1件だけ。これを置換元とするM1～M3に複数一致はない。ただし、今後生成する機械可読specの実物までは確認していない。

指定4 nodeに限定した期待KILLED集合は、静的に整合する。

| 変異 | 期待KILLED集合 | 理由 |
|---|---|---|
| M1：DEFAULT比較へ戻す | 新規テスト | 新既定要求がHに一致し、`:3223`で失敗 |
| M2：常にsuffix | goldenテスト | 歴史的組の値が変わり、`:11220`で失敗。新規テストのHにも同じsuffixが入るため同テストは生存 |
| M3：常に空 | compiler名分離、新規テスト | `:3197–3201`の比較と`:3223`が失敗 |

`test_cache_key_separates_trace_genome_and_commit`（`:3166–3181`）は、いずれも比較する入力間のtrace／genome／commit差が残る。登録4 node内で追加失敗を生むassertionは見つからない。

3変異とも非等価で、等価変異の混入はない。今回は恒等写像の変更や等価性判定を対象としておらず、SURVIVED正例を新設する必要はない。以上は静的予測であり、変異実走結果ではない。

**修正前後JSON**

hit JSONのbooleanだけでなく、seed JSONの値とも照合した。

| 項目 | 修正前 | 修正後 |
|---|---|---|
| seed → 要求compiler | g++-12 12.3.0 → g++ 11.4.0 | 同じ組 |
| admission receipt | seedと一致 | seedと一致。修正前とも同じ |
| seed → 要求key | `silo_fed9a86c14_t0` → 同一 | `silo_6c154d405d_t0` → `silo_f368efad6c_t0` |
| cached | true | false |
| binary SHA | seedと同一 | seedと異なる |
| 実コンパイル記録 | なし | g++、returncode 0 |
| ELF `.comment` | GCC 12.3.0 | GCC 11.4.0 |

根拠は `probe/before-hit-gcc.json:12–18,40,80–94`、`probe/after-hit-gcc.json:12–42,65,144–155`。receipt変更によるmissを修正効果と取り違えていない。

さらに各基準commitの`buildcache.py` bytesへ、DEFAULT定義だけをgcc/g++へ置換してSHA-256を計算すると、それぞれのhit JSONの`buildcache_source_sha256`（両方`:11`）と一致した。観測対象のbuildcacheが指定の一行変異であることを支持する。

**一般化・テスト実績・scope**

- **「現行の全入力でkey不変」:** DEFAULTが現行のgcc-13/g++-13のままである通常の文字列入力について、旧比較先と新literalが等しいため成立する。これは式の同値性による静的判断。runtimeでDEFAULTを差し替えた状態まで含めると成立せず、その差が今回の修正目的である。根拠は `buildcache.py:622,627,641–645`。
- **「4 node緑」:** 親の申告と矛盾はないが、今回確認できた資料から計算ノード上のpytest実行ログは独立確認できなかった。`artifacts/dev-wave-t785-legacy-cache-key/s5-f.md:14–23`が報告するのは直接関数呼出の成功であり、pytestは未実走と明記されている。この報告を計算ノード4 passedの証拠へ読み替えてはいけない。
- **production callerの手当て:** 共通のkey計算を修正しており、本件の省略条件による衝突を閉じるためのcaller変更不足は見つからない。evidence側の独立既定、同一要求名の実体変更などは裁定`:22`で既に限界として分離済み。追加修正をmust-fixにする成果物影響は本資料では示されておらず、`docs/dev-wave/core.md:80–88`に従いscopeへ追加しない。
- gate・新しい検査機構・台帳機構・一般化・build_v2・caller変更はcommit差分にない。

## 総括

**レンズBでは実装を承認可能。MUST 0件、記録の限定に関するNIT 1件。**

修正前偽hitと修正後missは、同じcompiler対・同じreceiptを持つ限定されたprobeで裏付けられている。変異3本の期待集合も指定4 node内では静的に妥当。親は予定どおり変異matrixと受入全走へ進める。

本レビューではファイル変更、pytest、probe再実行を行っていない。計算ノード4 passedは親申告として扱い、独立検証済みとはしない。