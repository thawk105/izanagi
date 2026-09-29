## 所見

1. **must-fix — 依頼の参照先が一致しない。** [md_23.txt:1–29](/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt:1) は Cicada への VHash hot block 実装・計測を依頼し、`external/ccbench` を所有外としている。一方、[brief:1–12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/s1-brief.md:1) と [plan:21–23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:21) は `gc_records()` 修理を md_23 の完了として扱う。修理の移管自体は brief に記録されているが、この依頼本文からは確認できない。放置すると、修理 commit と patch が完成しても md_23 の成果物・所有・完了判定との対応が成立しない。親は移管元または正しい依頼文書を一次資料に明記すべき。

2. **must-fix — 提案した「同じ job」の計測行列を現行 `CUSTOM` では表現できない。** [plan:57–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:57) は build ごとに cell・thread・反復数を変えるが、[launch_gcfix_run.py:1311–1315](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/launch_gcfix_run.py:1311) は全 build に同一の cell×thread、[同:1129–1131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/launch_gcfix_run.py:1129) は同一反復数を掛ける。指定どおり実行すると不要な走行が増え、指定を狭めると必要な F t8 や対照が欠ける。build 別の run 指定を小さく追加するか、仕様別 job に分け、合計時間を事前に算定する必要がある。

3. **must-fix — `CUSTOM` の終了コードを合否として使えない。** [plan:64–66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:64) 自身が認めるとおり、[launch_gcfix_run.py:1138–1147](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/launch_gcfix_run.py:1138) は `CUSTOM` の非 0 rc と判定項目の失敗を総合失格にしない。`stock_pass()` は必要項目を既に照合する（[同:818–834](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/launch_gcfix_run.py:818)）。修理版 trace にこれを適用し、TRACE=0 の rc・timeout、F の W-D 件数、無修理版の既知 ERR を別途集約する局所変更で足りる。これを欠くと判定器の合否が誤って緑になる。

4. **should-fix — 無修理対照の事前登録が弱い。** [plan:59–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:59) は t4・t8 各 10 回を置きながら「少なくとも 1 件」で合格とする。[D1:7–12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/d1-result-summary.md:7) では無修理 t8 が 5 回中 1 回完走した。両 thread で少なくとも各 1 件、**同じ既知の `gc_records` ERR** を要求する方が、完了判定との対応が明確になる。初回を各 5 回とし、陰性の thread だけ追加する逐次計画なら走行数を抑えられる。修理版の N/N は採用した N を固定して報告する。

5. **should-fix — 計測量と時間上限の根拠が足りない。** [plan:59–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:59) の指定を意図どおり数えても 54 run と複数 build になり、D1 の「2 build・20 run、約 1 分」から trace と CI を含む所要を直接推定できない。2 node 時間未満とテスト全体 5 分のそれぞれについて、予定 build 数・run 数・打切り条件を分けて記すべき。pin C での F t4 3 回は、厳密適用と F での実走に加える価値が明示されなければ削れる（[plan:46,62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:46)）。

6. **should-fix — patch の共存確認を完了条件へ広げすぎない。** [plan:46–49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:46) の pin C への厳密適用、必要な trace 二本との重ね適用は必要。一方、forwarding、version-lifetime、broken 系の前後両順すべての実測は今回の修理判定に使わない。未確認と README に記すだけでよい。`-instr` 別 patch も、単一 `fix-cicada-gc-records.patch` が必要順に厳密適用できない場合に限る。余分な patch を作ると適用先の参照が分岐する。

7. **nit — 所有と CI の方向は妥当。** [plan:44–53,68–70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/plan.md:44) は local branch 1 本、修理 patch、README 節、一次資料に収め、`ledger.json` の 1 entry 契約（[patches/README.md:913–917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/patches/README.md:913)）とも整合する。format の全対象 file と全 protocol build も必要。T-2854 の script を流用する際は、親 OID だけでなく commit 対象・出力参照・成功条件が F 子 commit を指すことを確認する。md_19 は同じ `transaction.cc` の 923–927 行付近を扱うため、branch を混ぜず、後の統合時に適用順を再確認する（[brief:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/s1-brief.md:5)、[transaction.cc:923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix/external/ccbench/cc/cicada/transaction.cc:923)）。

## 親の実測と一般化への指摘

[D1:14–35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/d1-result-summary.md:14) が示すのは **F・warehouse 1・t4/t8・1 job の ERR 10 件**で、全件 `aborted-delete-over-deleted`、abort 段は全件 `read_recheck`。X1 がその鎖を扱う根拠にはなるが、他 cell・warehouse 数、(b) に達する経路、`node_set` で aborted が committed の上に残る別症状まで修復した証拠にはならない。一次資料は観測範囲をこの条件に限定すべき。

## 変異の事前登録案

1. 修理 hunk だけを外した同条件 build を同じ job で走らせ、t4・t8 それぞれで既知の `gc_records` ERR を再現する。修理版は固定した N/N 完走と trace 判定を満たす。
2. GC 判定で **aborted を 1 段だけ**読み飛ばす変異を置き、D1 で実測された 2 段鎖に対応できないことを確認する。これは X1 の連続走査が必要な理由を直接試す。
3. 最初の非 aborted 版が deleted でない場合の `ERR` を外す変異は採用しない。異常を隠すだけなので、静的な条件確認を負例として記録すれば足りる。

## 総括

修理案 X1 と、単一 patch・短い README 節・全 file format／全 protocol build という骨格は小さい。着手前に **依頼文書の不一致**を解消し、`CUSTOM` の計測行列と合否集約を直す必要がある。そのうえで無修理対照を thread 別に判定し、不要な共存実験と pin C の重複走行を削れば、完了判定と時間上限により確実に収まる。