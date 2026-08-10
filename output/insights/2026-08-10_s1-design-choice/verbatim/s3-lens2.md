## 所見

### L2-1

- **主張:** P1の「SI先例で案Aは安い」は、狭いhook差分を正式なcross-protocol移植全体のコスト根拠へ一般化しており、5–8／7–11人日の見積りを裏付けていない。
- **根拠:** `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/brief.md:23-28,68-69`、`s2-plan.md:103-113`、`external/ccbench/cc/si/transaction.cc:526-553`、`external/ccbench/cc/silo/transaction.cc:147-180,362-435,584-686`。
- **具体的な失敗筋書き:** SIは`si_commit`内の単一ブロックでC/R/Wを出すだけだが、Silo側の追加箇所にはlock shadow、retention、cleanup、並べ替え前後の検査が含まれる。SIの32行程度のhook追加を基準にMOCC移植を見積ると、実装段階でtrace-v2共通基盤、protocol固有の完全性検査、fixture、較正、レポート接続が追加される。したがって5–8／7–11人日はhook実装の下限に過ぎず、SIとの差から何倍安いかを算出できる履歴的根拠はない。なお現行Siloの`#if TRACE`は実際には10箇所で、親briefの「13箇所」とも一致しない。
- **深刻度:** **must-fix**。案Aをコスト理由で選ぶかどうかが変わり、正式比較の実装工数と受理時期の見積りが不安定になる。

### L2-2

- **主張:** 案AはERМIA／MOCCの登録と実装を見積っているが、段7の前提台帳が要求するprotocol登録・protocol別較正・target別between-run floor再測定を完了条件として取り込んでいない。
- **根拠:** `docs/phase3.md:347-356`、`s2-plan.md:67-83,89-111`、`orchestrator/campaign/genome.py:87-96`、`orchestrator/campaign/between_run_floor.py:49-63,159-168`。
- **具体的な失敗筋書き:** 段7を台帳どおり実行すると、未登録の`tictoc`／`cicada`は`space_for`で停止し、登録を省略すると比較対象の受理集合が暗黙にSilo／MOCC／ERMIAへ縮む。さらに現行floor測定はSilo baselineだけであり、Siloの3 workload pointを3 protocolへ展開するだけでもfloor測定セルは3から9へ少なくとも3倍になる。較正と実測時間を「別」として除外したままでは、5–8／7–11人日は段7成立費用ではない。
- **深刻度:** **blocker**。protocol登録、較正、floor参照がない候補は段7のcertified受理集合に入れられず、比較行そのものが成立しない。

### L2-3

- **主張:** A-5が掲げるcertified選択結果・材料レポート・試行台帳への影響は、現行の公式report／schema／selection consumerへ接続されておらず、新しい`cross_protocol_report.py`だけでは成果物にならない。
- **根拠:** `s2-plan.md:85-99,147-151`、`orchestrator/campaign/layer3_report.py:289-346,506-546`、`orchestrator/campaign/layer3_schema.json:5-21`、`orchestrator/campaign/pipeline.py:722-733,1019-1093`。
- **具体的な失敗筋書き:** protocol別floorを同じrecords・threads・workloadで追加すると、現行floor照合はprotocolをキーにしないため、複数一致として`layer3_report.py:345-346`で停止する。さらに現行schemaは追加プロパティを拒否し、`build_accepted_report`自身も「certified-selection consumerは未接続」と明記している。新reportを別ファイルに置けば公式材料レポート・受理集合に反映されず、公式reportへ統合すればfloor選択、schema、acceptance receipt、selection consumer、fixture／テストが追加で必要になる。
- **深刻度:** **blocker**。certified選択結果、材料レポートの比較行、floor・pin・binary・sourceの参照鎖が公式成果物に入らず、段7の受理結果を生成できない。

## 所見なし

- **build target解決:** `buildcache.py:494-515,653-668,825-846`と`external/ccbench/cmake/ProtocolHelpers.cmake:33-43`から、`ycsb_<protocol>.exe`は既にprotocol-parametricであり、案Aのtarget解決見積りに明白な取り残しはない。
- **MOCC移植候補の基本経路:** `external/ccbench/cc/mocc/transaction.cc:156-268,888-953,1017-1071`と`external/ccbench/cc/mocc/CMakeLists.txt:1-10`に、read set・validation・commit/writePhaseの対応箇所があり、静的読解上の候補選定は裏付けがある。
- **P3の段階案:** `s2-plan.md:211-228,230-236`が、Bを別namespaceに閉じ、Bの値をAへ再利用せず、Aを新しい較正・floorでやり直すことを明記しているため、隠れた証拠再利用の所見はない。ただしこれはコスト削減ではなく、明示された実装順序である。

## 総括

blockerは2件ある。  
最重要はL2-3で、公式report／selection consumer未接続のため成果物が受理できない。  
L2-2も、protocol別較正とbetween-run floorを外出ししたままでは段7の受理集合が未定義になる。  
L2-1は、SIの狭いhook先例から全体工数を安く見積る根拠がない点を修正すべきである。