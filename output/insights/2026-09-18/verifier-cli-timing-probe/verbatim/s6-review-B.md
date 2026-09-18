## レビュー結果

**GO。主要な観測値・判定・識別子は一致し、must-fix はありません。** CPU合計に丸め順序による0.001秒の差があります。説明と参照先について should / nit を下表に示します。

原本のJSONを読み、派生値を独立に再計算しました。本走summaryの373行はresult.jsonと一致。probeの実SHA-256・行数、verifier全9ファイルとpipeline.pyの実SHA-256も照合しました。bench・verifier・selftest・pytestは再実行していません。

## 主張の射程と参照資料

「1条件・1反復・1 node」「当時の再現ではない」「D2144を置き換えない」「CC性能主張に使わない」は守られています。bench **3.344秒**、verifier **421.707秒**、`certified=true`という観測事実も明確で、断り書きによって曖昧にはなっていません。

§4.3の「比較ではない」は、数値比を掲載しているため、厳密には「同条件比較・速度向上の推定ではない」と書く方が正確です。31.4%という算術自体は正しいです。

§5にはCLIとpipelineの処理差、単独性検査の時点、`ru_maxrss`の子孫への言及が既にあります。追加するとよい限界は次の2点です。

- verifier直前に、pipelineにはないfile一覧passが全traceを行数計数・ハッシュ計算のために読みます。計時から除外しても、キャッシュ状態への影響は除外できません。その影響量は未測定です。
- `ru_maxrss`はプロセス群のRSSを同時刻で合算したピークではありません。43.95 GiBを、CLIと全workerの総メモリ需要やcgroup charged memoryとして使えないことを明記すると安全です。

既往値の引用先は次のとおりです。

| READMEの引用 | 原本での確認 | 判定 |
|---|---|---|
| 中央値1408.8秒 | t2229 §2、D2144本文に明記 | 一致。ただし高commit 3変種・13反復で、欠測attempt 3反復を含む |
| 約120秒以下、条件付き | t2229 §4、D2144本文に明記 | 一致 |
| Python側約91% | t2229 §4、D2144本文に明記 | 一致 |
| 約17〜19秒、1.0〜1.1 μs/commit | t2229 §4に明記 | 一致。D2144本文では「換算で約20秒」 |
| trace無し版3.35〜3.42秒 | t2229 §4に明記 | 一致 |
| `acf840c8` 595.5〜626.9秒 | t2229 §5.2の高commit 3変種の最小・最大。D2144本文にも帯を明記 | 一致。低commit変種は173.1〜178.7秒 |
| 「D2144 §4」「D2144 §5.2」 | D2144本文にはこの節番号がない | t2229 READMEの節番号と明示するのが適切 |

§6のjob dir、mainの列挙ファイル、main/smokeのtrace各48ファイルと`log/`、dispatch receipt、probe、運転script、selftest log、裁定、author prompt・報告、repoの`verbatim/probe-source.md`は実在しました。運転scriptはsmoke成功後だけmainを起動し、READMEの条件と一致します。

一方、確認時点で以下は未作成でした。

- `run/smoke/summary.md`：「同構成」との記載に例外があります。
- repo内の`verbatim/s6-review-A.md`、`verbatim/s6-review-B.md`：進行中レビューの収録予定として扱う必要があります。

## 総括

**判定：GO。must-fix 0件。** 数値の中心的結論は維持できます。以下の修正・補足を推奨します。

| 番号 | real/refuted | 重要度 | 根拠 | 放置時に変わる値・主張 |
|---|---|---|---|---|
| B1 | real | nit | 原本CPU合計は1812.169477＋88.976072＝1901.145549秒 | §4.1は原本から3桁丸めなら **1901.146秒**。1901.145は丸め済み値の和 |
| B2 | real | should | t2229 §2・D2144が中央値の母集団と欠測attemptを明記 | §4.3の1408.8秒を全反復の中央値と誤読し得る。13反復・欠測3反復を補足 |
| B3 | real | should | probeはcount→file一覧・hash→verifyの順 | §5に追加passによるキャッシュ状態への影響が未測定と補足 |
| B4 | real | should | `ru_maxrss`の「子孫込み」だけでは合算値との区別が弱い | §4.1・§5の43.95 GiBを全worker同時合計メモリと誤読し得る |
| B5 | real | should | smoke summaryとrepoのレビュー逐語2本が未作成 | §6の「同構成」「逐語が在る」という参照先の実在性 |
| B6 | real | nit | §4・§5.2はD2144本文でなく、そこから参照するt2229 READMEの節 | §1・§4.3の参照先を明確化 |
| B7 | real | nit | 120÷3.343941605＝35.885794… | §4.3「その1/36」は「**約**1/36」が正確 |
| B8 | refuted | must-fix相当の疑義 | 原本、stdout、verifier JSON、summaryを照合 | 主要時間・件数・verdictの転記誤りはない |
| B9 | refuted | must-fix相当の疑義 | `certified`→`Integrity.clean()`→X/P gate、reportはproof surfacesを出力しない | JSONにproof surfacesがなくても`certified=true`と矛盾しない |
| B10 | refuted | must-fix相当の疑義 | §1・§4.3・§5が観測範囲を限定 | D2144の置換・性能改善の確定という主張はしていない |

**§4.1の全行と付随値の対応表**。通常の秒数は小数3桁。Popen復帰時間のみREADMEの小数4桁と照合しました。

| 項目 | READMEの値 | 原本の値／独立再計算 | 照合 |
|---|---:|---:|---|
| T_trace wall | 3.344秒 | 3.343941605→3.344 | 一致 |
| bench Popen復帰 | 0.0002秒 | 0.000204392 | 一致 |
| bench近似communicate窓 | 3.344秒 | 3.343737213→3.344 | 一致 |
| bench rc | 0 | 0 | 一致 |
| bench user / sys | 143.193 / 5.214秒 | 143.193015 / 5.213706 | 一致 |
| bench maxrss | 529,672 KiB、517 MiB | 529,672 KiB＝517.2578125 MiB | 一致 |
| bench 120秒超過 / timeout | なし / なし | false / false | 一致 |
| T_count wall | 16.858秒 | 16.857903951→16.858 | 一致 |
| C行数 | 17,128,612 | 17,128,612 | 一致 |
| count換算 | 0.984 μs/commit | 0.984195564 | 一致 |
| count換算 | 82.6 ns/行 | 82.617043865 | 一致 |
| file一覧pass | 16.676秒 | 16.675985391→16.676 | 一致 |
| T_verify wall | 421.707秒 | 421.706717790→421.707 | 一致 |
| verifier Popen復帰 | 0.0003秒 | 0.000340893 | 一致 |
| verifier近似communicate窓 | 421.706秒 | 421.706376897→421.706 | 一致 |
| verifier rc / timeout | 0 / なし | 0 / false | 一致 |
| verifier user / sys | 1812.169 / 88.976秒 | 1812.169477 / 88.976072 | 一致 |
| verifier CPU合計 | 1901.145秒 | 1901.145549→**1901.146** | 丸め順序差 |
| CPU/wall | 4.51 | 4.508217367 | 一致 |
| verifier maxrss | 46,084,868 KiB、43.95 GiB | 46,084,868 KiB＝43.949954987 GiB | 一致 |
| trace複製 | 3.979秒 | 3.978619626→3.979 | 一致 |
| 複製bytes | 6,520,332,111 | inventory合計と保存traceのstat合計が同値 | 一致 |

**§4.2の全行の対応表**。

| 項目 | READMEの値 | 原本・code | 照合 |
|---|---|---|---|
| rc / verdict / certified | 0 / serializable / true | result.jsonとverifier.jsonが同値 | 一致 |
| txns | 17,128,612 | verifier stats.txns、expected-commits、stdout witness、C行数が同値 | 一致 |
| edges | 296,980,787 | verifier stats.edgesが同値 | 一致 |
| anomaly_count / total_cycles | 0 / anomalies空 | verifier JSONは **0 / 0**、anomalies=[] | 整合。total_cyclesは直接0と書ける |
| integrity clean | true | JSON true、`Integrity.clean()`の出力 | 一致 |
| orphan_reads / version_dups / dup_txids | 各0 | 各0 | 一致 |
| genesis_commits / missing_txids / write_version_mismatch | 各0 | 各0 | 一致 |
| malformed_keys / framing_violations | 各0 | 各0 | 一致 |
| lock_coverage / write_intent / permutation違反 | 各0 | 各0 | 一致 |
| notes | 空 | [] | 一致 |
| proof_surfaces_present | false | JSONに当該キーなし、reportも出力しない | 一致 |
| certifiedとX/P gate | gate成立を含意 | modelの`certified`・`clean`・`certification_gate_satisfied`が裏付ける | 一致 |
| verifier.json | 1,237 bytes | stat＝1,237 | 一致 |
| verifier.stderr / bench.stderr | 0 / 0 bytes | stat＝0 / 0 | 一致 |
| bench.stdout | 21行 | 実ファイル21行 | 一致 |
| commit / batch_commit / abort | 17,128,612 / 0 / 3,066,603 | stdoutの各witnessと一致 | 一致 |

X/P gate成立の含意は確認できました。一方、「emitter ×3」「L432」というstock source上の具体的な個数・行番号は、今回指定されたcode断片やJSONからは直接検証できません。`certified=true`がその個数・行番号まで証明するわけではありません。

**その他の派生値の対応表**。

| 項目 | READMEの値 | 原本から再計算 | 照合 |
|---|---:|---:|---|
| 3区間合計 | 441.909秒 | 441.908563346→441.909 | 一致 |
| bench割合 | 0.76% | 0.756704414% | 一致 |
| count割合 | 3.81% | 3.814794586% | 一致 |
| verifier割合 | 95.43% | 95.428501000% | 一致 |
| 1408.8秒に対する比 | 31.4% | 31.367728801% | 一致 |
| 120秒に対するbench | 1/36 | 1/35.885794123 | 近似として一致 |
| count＋verifier割合 | 99.24% | 99.243295586% | 一致 |
| verifier / txn | 24.62 μs | 24.620016951 μs | 一致 |
| verifier / edge | 1.42 μs | 1.419979798 μs | 一致 |
| verifier分秒換算 | 7分1.7秒 | 7分1.706717790秒 | 一致 |
| 表題の規模 | 17.13M commit・204M行・6.52 GB | 17.128612M・204.048743M・6.520332111 GB | 一致 |

**§1・§2.2の識別・時刻の対応表**。

| 項目 | READMEの値 | 原本・実照合 | 照合 |
|---|---|---|---|
| job / queue / node | 5868.nqsv / gen_S / bnode041 | dispatch log、result.jsonが同値 | 一致 |
| CPU / affinity / site | Xeon Platinum 8468 / 48 / PEGASUS_COMPUTE | result.jsonが同値 | 一致 |
| Created / Started / Ended JST | 15:30:10 / 15:30:18 / 15:40:42 | accountingが同値 | 一致 |
| Elapse | 628秒 | accounting＝628S | 一致。Started→Endedの差624秒とは別値 |
| 本走開始 UTC | 06:32:31.75 | 06:32:31.751008 | 一致 |
| bench Popen UTC | 06:32:58.93 | epoch 1789713178.9252086→06:32:58.925209 | 一致 |
| bench終了 UTC | 06:33:02.27 | epoch 1789713182.2691514→06:33:02.269151 | 一致 |
| verifier Popen UTC | 06:33:35.85 | epoch 1789713215.8465285→06:33:35.846529 | 一致 |
| verifier終了 UTC | 06:40:37.55 | epoch 1789713637.5532477→06:40:37.553248 | 一致 |
| 本走終了 UTC | 06:40:41.98 | 06:40:41.980366 | 一致 |
| §1のJST範囲 | 15:32〜15:40 | 上記UTC＋9時間 | 一致 |
| repo HEAD | c8e8dc06f33891aa2fd6345063b30ca11b52fe6d | bindingsと全桁一致 | 一致 |
| CCBench pin / clean | 511c9538… / true | bindingsの全桁pin・trueと一致 | 一致 |
| binary SHA-256 | 2a27e080…10f6931 | bindingsと全桁一致 | 一致 |
| compiler / version hash | gcc-11・g++-11 / b713e6ab… | bindingsと一致 | 一致 |
| policy / gflags / glog | 66ea7135… / e171aa2d… / 8f9ccfe7… | bindingsと一致 | 一致 |
| Python | /usr/bin/python3.10、3.10.12 | bindingsと一致 | 一致 |
| cli / core / dsg | 68e690c6 / 4d70c244 / e77eaabd | bindingsと実ファイルhashが一致 | 一致 |
| model / parse / report | 59136847 / 1aedb77a / e68e31a0 | 同上 | 一致 |
| commit_receipt / __init__ / __main__ | 106e0dcc / 56c7fb4c / 9a06c813 | 同上 | 一致 |
| pipeline | 472cc7a2… | bindingsと実ファイルhashが一致 | 一致 |
| default workers | 16 | min(48 files, affinity 48, 16)＝16 | 一致。実際のworker稼働数の計測ではない |
| probe | 544行、03a1efbc…52f8 | 実測544行、全桁SHA一致 | 一致 |
| selftest | 25/25 PASS | 25件のPASSと最終行を確認 | 一致。log単独では実行host pegasus02は未確認 |

probeの実SHA-256は
`03a1efbc832329982b1a947d21adefaced2fdb0356ab6462d462ee8f8b3d52f8`
でした。

時刻列は単調で、mainはsmoke終了後・job終了前に収まります。本走全体は490.229358秒で、3区間合計441.908563秒との差にはbuild等の前置処理、file一覧pass、複製・後始末等が含まれ、矛盾はありません。

**§4.4 smokeの対応表**。

| 項目 | READMEの値 | 原本の値 | 照合 |
|---|---|---|---|
| records / extime / threads | 10,000 / 1 / 48 | conditionsが同値 | 一致 |
| T_trace | 1.048秒 | 1.048099591 | 一致 |
| commit / abort | 4,933,099 / 3,330,543 | 同値 | 一致 |
| T_count | 4.741秒 | 4.740741971 | 一致 |
| file一覧pass | 4.601秒 | 4.601096043 | 一致 |
| 行数 / bytes | 57,674,153 / 1,812,744,103 | inventoryの独立合計が同値 | 一致 |
| T_verify | 92.806秒 | 92.805868346 | 一致 |
| rc / verdict / certified | 0 / serializable / true | 同値 | 一致 |
| edges | 92,352,511 | 同値 | 一致 |
| verifier user / sys | 413.954 / 22.207秒 | 413.953791 / 22.207453 | 一致 |
| verifier maxrss | 13,585,176 KiB | 同値 | 一致 |
| 複製 | 1.228秒 | 1.227810725 | 一致 |
| binary hash先頭 | 258440e6… | 258440e63ae53f8e… | 一致 |

**読めなかった必読資料：なし。** 未作成の参照先はB5の3ファイルです。巨大traceの全行再走査・全ファイルhash再計算は行わず、行数はresult.jsonのfile別値から独立加算し、保存ファイルについては個数とbytesを確認しました。