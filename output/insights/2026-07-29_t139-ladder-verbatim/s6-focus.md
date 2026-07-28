修正の大半は縮約で閉じていますが、3 件の退行と 1 件の残余があります。

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| R1-1 | closed (縮約による) | source clean は post-hoc 仮定、CXXFLAGS/binary は回収不能と明示し、値を non-acceptance に落としている。`2026-07-29_t139-silo-degradation-ladder-design.md:108-118`; `0_873583.nqsv/manifest.json:17-35` |
| R1-2 | regressed | B-4 の一般反証は撤回したが、代替主張の「全30標本で A・B とも stock 未満」は誤計数。30 行は stock 10 + 候補 20 であり、該当するのは候補20標本。`2026-07-29_t139-silo-degradation-ladder-design.md:120-123`; `0_873583.nqsv/summary.tsv:2-31` |
| R1-3 | closed (縮約による) | 10k/100k を未較正・cache-resident 局所観測と明記し、calibration や受理入力から除外した。`2026-07-29_t139-silo-degradation-ladder-design.md:95-96,108-111` |
| R1-4 | closed (縮約による) | t4 trace liveness と t48 gap を明確に分離し、t48 per-worker liveness を未確認・後続義務とした。`2026-07-29_t139-silo-degradation-ladder-design.md:25-29,80-84,197-199` |
| R1-5 | closed (縮約による) | 数値表の直前と §8、task namespace の三箇所で未較正・受理不能・headline 等への採用禁止を明記した。`2026-07-29_t139-silo-degradation-ladder-design.md:95-106,214-220`; `t139-probe/README.md:3-6` |
| R1-6 | closed (縮約による) | sidecar は JSON・patch・driver・full HEAD・compiler を束縛し、binary/argv/trace digest は回収不能、恒久実装での再束縛が必要と限定した。`t139-probe-correctness.provenance.json:2-11`; `2026-07-29_t139-silo-degradation-ladder-design.md:179-194` |
| R1-7 | regressed | witness と D93 の結論は訂正したが、object/section diff 未取得と認めながら「`.rodata` が変わる」と新たに断定している。一次資料が直接示すのは `__LINE__` 引数定数まで。`2026-07-29_t139-silo-degradation-ladder-design.md:136-144`; `external/ccbench/include/debug.hh:54-64` |
| R1-8 | closed | 診断計器の inert を default-OFF から導かず、各 patch が実 TU/binary witness で個別立証する条件へ修正した。`patches/README.md:12` |
| R1-9 | closed | mutex は scheduling 制約のみ、A の同一 CAS・B の stock `writePhase()` 一回という safety 論拠が維持されている。`2026-07-29_t139-silo-degradation-ladder-design.md:54-65` |
| R1-10 | closed | correctness は trace build、gap は trace-disabled の別 build/run と限定され、gap 側 trace symbol 0 も記録されている。`2026-07-29_t139-silo-degradation-ladder-design.md:67-84` |
| R1-11 | closed | 省略されていた B の4 worker値を全て列挙し、median・比率の数値も一次表と一致する。`2026-07-29_t139-silo-degradation-ladder-design.md:74-77,98-101` |
| R1-12 | closed | 外部相談を出自付きデータとして扱い、採否を親・ユーザー裁定へ限定している。`2026-07-29_t139-silo-degradation-ladder-design.md:7-10,221-222` |
| R2-1 | closed (縮約による) | CCBench・gflags・glog の HEAD と clean を post-hoc attestation と明示し、第三者 forensic 証拠ではなく non-acceptance とした。`0_873583.nqsv/manifest.json:15-22,34-35` |
| R2-2 | closed (縮約による) | job ID・会計時刻・script/patch hash は回収し、binary/compile argv/CMakeCache は回収不能と列挙して forensic/受理用途を撤回した。`0_873583.nqsv/manifest.json:4-16,27-35` |
| R2-3 | closed (縮約による) | A/B の共通 symbol と scrub 未実装を隠さず列挙し、macro 固有 witness と環境 scrub を恒久要件へ送った。`0_873583.nqsv/manifest.json:30-32`; `2026-07-29_t139-silo-degradation-ladder-design.md:195-203` |
| R2-4 | closed (縮約による) | trace t4 と perf t48 を一体の確定事項ではないと明記し、perf-liveness を受理義務として残した。`2026-07-29_t139-silo-degradation-ladder-design.md:25-29,80-84,197-199` |
| R2-5 | regressed | authority と親参照は直ったが、sha256 は既存慣行の64桁でなく8桁 prefix のみで、さらに `handoff-final.md` は不存在のまま placeholder 行が追加された。`t139-ladder-verbatim/README.md:3-24`; `2026-07-28_t140-review-verbatim/README.md:5-9` |
| R2-6 | closed | 段3 A/B と段6 R1/R2 の全 ID・裁定・反映先を恒久台帳 §9 に収録した。`2026-07-29_t139-silo-degradation-ladder-design.md:224-272` |
| R2-7 | partial | 現 wave に recovery/RF の受理主張はなくなったが、親 inline 射影の防壁は依然「自己規律」で、machine-readable gate は後続要件のまま。`t139-ladder-verbatim/README.md:26-30`; `2026-07-29_t139-silo-degradation-ladder-design.md:186-190` |
| R2-8 | closed | namespace を task-scoped disposable probe、非 calibration、未較正・受理不能と一意に宣言した。`t139-probe/README.md:1-6` |
| R2-9 | closed (縮約による) | 固定順・非専有・単独性検査一回を明記し、B/W1 を provisional、全値を非受理とした。`2026-07-29_t139-silo-degradation-ladder-design.md:112-128` |
| R2-10 | closed | correctness の実行日を post-hoc artifact field に置き、JSON 自体には timestamp がないという限界も併記した。`t139-probe-correctness.provenance.json:9-11` |
| R2-11 | closed | 数値・中央値・比率は維持され、`patches/README` の変更も既存分類を狭める witness 条件追加に留まる。`2026-07-29_t139-silo-degradation-ladder-design.md:98-106`; `patches/README.md:12` |

## regressed / 新規破壊

1. 局所観測の標本数を「全30」と誤記した。正しくは「10 paired triplets すべて」または「候補20標本すべて」。`2026-07-29_t139-silo-degradation-ladder-design.md:121`; `0_873583.nqsv/summary.tsv:2-31`
2. R1-7 の訂正で、section diff のないまま `.rodata` 変化を断定した。`__LINE__` による binary 非同一仮説と、変更 section／単独原因の確定を分ける必要がある。`2026-07-29_t139-silo-degradation-ladder-design.md:136-144`
3. 凍結 README に不存在の `handoff-final.md` と未確定 hash placeholder を追加し、既存11 payload の hash も64桁でなく prefix のみにした。`t139-ladder-verbatim/README.md:8-24`

**NO-GO — 縮約後にも一次資料と一致しない標本数、未立証の `.rodata` 因果、壊れた凍結 package 参照／hash が残り、値・主張・参照の判定基準を満たさない。**