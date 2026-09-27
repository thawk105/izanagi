## 所見

1. **must-fix — stock だけを見て genome を選ぶと consumer を落とす。** 根拠: [plan:26](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:26)、[規則 v2 R4:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/output/insights/2026-09-26/t2854-d297-header-review/README.md:62)。具体入力: 変更 header を si target は stock で読み、silo target は `WAL=1` の genome で初めて読む。header の変更は `WAL=1` でだけ展開を変える。stock の consumer からは si しか選ばれず、silo genome を走らせないまま **pass** し得る。production target ごとの consumer を未実行の genome について stock から推定しないこと。選定に必要な構成を列挙して依存を調べるか、未調査の構成を安全に除外できる根拠を要求する。

2. **must-fix — `(entry, argv)` が同じでも configure 間の生成 header は同じとは限らない。** 根拠: [規則 v2 R4:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/output/insights/2026-09-26/t2854-d297-header-review/README.md:62) の「1 回に集約」、[plan:22,32](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:22)。具体入力: 二つの選定 configure で TU の argv は同じだが、custom target が作る `config.h` の値が異なる。変更 header はその値が 1 の構成でだけ旧新不一致となる。先に値 0 の構成を比較して argv を重複除去すれば **pass** する。集約は生成物と依存閉包の内容まで同一と証明できる場合に限る。証明できなければ `(compiler, configure, entry)` ごとに比較する。

3. **must-fix — TRACE token のない entry を非 consumer と確定できない。** 根拠: [plan:9,30,70](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:70)、[規則 v2 R3・R6:61–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/output/insights/2026-09-26/t2854-d297-header-review/README.md:61)。具体入力: `-DTRACE=0` のない entry が `#if TRACE` 内で変更 header を読む。plan の「後付け指定をしない」方法では 0/1 の依存照会が同じ状態になり、この entry は consumer から消える。別 entry が consumer なら 0 件拒否も働かず **pass** し得る。各 entry で両 TRACE 状態を実際に作り、実効値を確認する。作れない entry は consumer 判定前に拒否する。

4. **must-fix — production target の出所が未確定のままでは R4 を実装できない。** 根拠: [plan:7–8,68](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:68)、現行の [_v2_commands:1961–1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/buildcache.py:1961)。具体入力: 並走 wave が `tpcc_silo.exe` を production に加え、変更 header をその target と genome 空間のない target が stock で読む。判定元を現行の `ycsb_<protocol>.exe` に固定すると silo genome を選ばず、そこでだけ生じる差を残して **pass** し得る。実際の production build 経路から target 集合を取得し、取得不能・未対応 target は拒否する。plan の「実装時に確定」は受理条件としては未完成。

5. **should — 変異 #4・#5・#6 のテストは、記載のままでは狙った欠陥を識別できない。** 根拠: [plan:50–58](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:50)、[plan:28](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:28)。#4 は生成 header が存在すれば `-MG` への変異が観測されず、存在しなければ正常実装も依存失敗で拒否する。#5 の「旧新 argv だけ変更」は database 一致検査が先に拒否し、他 protocol consumer を比較した証拠にならない。#6 は予定集合を欠陥のある consumer 列挙から作れば、予定と実行の照合が恒真になる。結果として、偽緑を作る変異が生存してもテストは緑になり得る。#4 は他の正常 consumer を残した欠落経路、#5 は旧新 argv を同じにした展開差、#6 は独立した期待集合を使い、各変異で期待する最初の失敗理由を確認する。

## plan・brief の前提で不成立と判断したもの

[brief:36–39](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/s1-brief.md:36) の consumer 21、database 一致、42/42 一致は、[生死確認:5–17](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/s1-live-summary.md:5) の三構成での結果に限られる。plan はこれらを固定件数や一般的な不変条件にはしていない。一方、plan の stock 起点の選定と TRACE token 不在 entry の扱いは、その実測で問題が現れなかったことを一般化すると上記の偽緑になる。

既存拒否の迂回は、**plan に書かれた順序どおり**共通の diff 検証を先に行い、header と `.cc` の両方を必ず比較する限り、静的には見つからなかった。[現行の拒否:180–201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:180)、[plan:18,34](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/out/s2-plan.md:18)。

## scope 外候補

admission build、link object、trace symbol/data、receipt の結合は [D780 項 2](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/verbatim/D780.md:7) の別防壁である。plan の保証名は選定 configure の database 上の比較に限られており、現状の文言から別防壁を実装したという過大な主張は見つからなかった。選定外 genome、Debug、opt-in target、GCC 以外も今回の保証外として明記されている。

## 総括

**plan どおりの実装には偽緑の経路がある。** 特に configure 選定、同一 argv の集約、TRACE token 不在 entry の三点は、比較を正しく実行しても対象 entry または構成が比較前に消える。production target の取得元を含め、受理条件を実装前に確定する必要がある。今回は指定資料の静的検査のみで、ファイル変更・テスト実行はしていない。