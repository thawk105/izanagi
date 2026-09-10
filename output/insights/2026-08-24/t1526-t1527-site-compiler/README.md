# [T-1526][T-1527] 受入 source-digest test の available compiler 化

## 結論

- T-1526 の campaign 8 nodeを exact `g++-13` から既存 `_any_cxx()` 系へ寄せた。通常checkoutでは
  6 nodeが即実走し、template patchが必要な2 nodeはcompiler判定より前のconditional skipを維持する。
- T-1527のdirect comparisonは別の9件目で、fake repoへ最小mocc CMakeと
  `cc/mocc/transaction.cc` (`int mocc_fixture;`) をinitial commit前に供給し実走化した。
- productionの `submission.prepare_toolchain()`、`source_digest.py`既定、buildcache/site resolverは
  変更していない。qualificationのexact toolchain manifest / series identityの受理集合は不変。

## compiler・identity・受理集合

- 実在は `/usr/bin/g++-12` -> `/usr/bin/x86_64-linux-gnu-g++-12`, version
  `g++-12 (Ubuntu 12.3.0-1ubuntu1~22.04.3) 12.3.0`。plain `/usr/bin/g++` はg++-11。
  `g++-13`は不在。helper候補順から焦点走はg++-12を選ぶ。run_tests receipt自身はrealpath/versionを
  fieldに持たないため、選択はPATH実在とhelper順からの推論であり、receipt fieldと偽らない。
- source token / variant IDは同一選択compiler内のcurrent/HEAD関係で検査する。compiler版横断の
  digest値・関係は保証しない。cache keyはgenome, commit, trace, src token, admissionを固定し、
  cxx要求名だけをg++-12/g++-13で変える正例で分離を確認した。
- missing defineは同compilerの完全define positiveを先に通し、BACKOFF_FIXEDだけを除いたnegativeで
  macro名とundefined系診断を要求する。include drift、builtin alias、TRACE diff-of-diffsのrejectは不変。
- 実装前の対象9 nodeは9 skip。実装後は7 pass / 2 conditional skip。meta 6 nodeとcache-axis
  1 nodeを加えた焦点走は14 passed / 2 skipped (request 941759.nqsv, child rc=0)。

## 実装・レビュー・検査

- 実装commit `cffad9199d1a93b3c9f4300b1bdde639c82c4225`、fix commit
  `ddbc66ca7e8d2102a81cc9dfcefb8a4b1f5f343d`。いずれもCodex author。
- 敵対review 2本のreal所見から、compiler単独cache軸、qualified/scope-aware AST consumer、
  全callの`cxx=` keyword、helper4状態をfix。焦点再reviewはclosed 4 / partial 0 / regressed 0。
- file単独走: `test_campaign.py` 377 passed / 3 skipped、`test_s1_direct_comparison.py` 97 passed、
  `test_skip_classification.py` 6 passed。
- 段6受入全走: tested main `c6c98f4b3b8673da8041b222f5550803ea27fb06`, tested tip
  `dfeb968404cf74b9b6a1d6277f937d6c5697f86d`, verdict child-green,
  14941 passed / 60 skipped, red 0, flake 0。

## 変異 matrix

- 最終spec sha256 `b3052027d6ee792fee65d6862442816b7adc8e29a50c43648ebe01d4013c993f`。
  baseline PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。
- 初走はM4の実失敗2 nodeのうちreal-repo側に`@real-repo` suffixが付いて期待側だけMISMATCH。
  suffix付き期待はpytest collectionに存在せず起動前拒否される既知F95のため、M4をselected-cxx
  meta nodeへ再照準した。初走は`mutation-ledger-attempt1-erratum.json`として残す。
- 最終結果は`mutation-ledger.json`。M1/M2 helper候補・全滅、M3 conditional順序、M4 consumer
  binding、M5/M6 mocc source/CMake、M7 compiler cache軸、M8 qualified calleeを各期待nodeでkillした。

## scope外の所見

- legacy cacheはcompiler要求名をpre-imageへ入れるが、plain `g++`のresolved executable/versionまで
  束縛しない。v2 complete toolchain manifestとは別であり、compiler portability一般化として
  本waveでは実装しない。
- `_any_cxx()`はavailable test compiler fallbackで、Pegasus compute productionのplain `g++`と
  同じ要求名を選ぶ保証ではない。cross-version digest保証、他testのg++-13整理、shared resolverは
  追加しない。

## 一次資料

- `verbatim/`: brief、plan、相談2本、裁定、review 2本、fix、焦点再review。
- repo外受入receipt/log: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1526-t1527-site-compiler/`。
