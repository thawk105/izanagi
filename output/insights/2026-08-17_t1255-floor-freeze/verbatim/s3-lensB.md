結論: **NO-GO**。静的検査のみで、ファイル変更・pytest実行はありません。主な blocker は、親案が現在の裁定 D471 と、T-1255 の明示された実行手順を同時に上書きしている点です。

## 所見 B-1 — T-1255 の実行経路を無断で差し替えている

- 深刻度: blocker
- 根拠: `docs/archive/worklog-phase3-0817-611.md:565-573`、`s8b_floor_campaign.py:1237-1315`、`s8b_floor_campaign.py:6691-6701`、brief `:26-41`
- 再現の筋道:
  - 裁定は「tty判定を明示フラグ + AI provenanceへ置換してから凍結」と記録している。
  - 実装上の `freeze_protocol()` は現在も `sys.stdin.isatty()` を要求する。
  - 親案はこれを変更せず、別の零引数 `reseal_protocol()` を正式経路とみなす。
  - `reseal-protocol` の出力は path、contract、pin、byte length、shaだけで、誰がどの承認値で実行したかを記録しない。コード commit の `AI-Agent` trailerは発行実行の provenance ではない。
- 影響:
  - v2 artifact自体は発行できても、T-1255の承認手順を満たした実凍結とは記録できない。
  - protocol shaが `2c8cf9be...` に変わっても、certified選択・レポート・試行台帳へ「承認済みAI発行」として参照できる根拠が欠ける。
- 必要な再裁定:
  - `reseal_protocol()` をT-1255の正式経路として認めるか。
  - 零引数APIとprovenanceなしを認めるか。
  - 認めないなら、実経路へ明示フラグと発行provenanceを追加するか。

## 所見 B-2 — resolver変更は D460 だけでなく D471 にも正面衝突する

- 深刻度: blocker
- 根拠: `s2-plan.md:7-23,42-62`、`docs/decisions.md:D460` (`19196-19224`)、`docs/decisions.md:D471:19572-19616`
- 再現の筋道:
  - 親案P1は、現行contract候補内の `ccbench_pin == HEAD gitlink` を優先し、単独候補へfallbackする。
  - しかしD471は `resolve_current_floor_protocol` を変更しないと明記している。
  - D471は親案と同じP1を「却下した選択肢」として記録している。
  - D471はさらに「D460のresolver契約を維持する」と明記している。
- 影響:
  - 現在はindex 1件でlegacyが解決される。
  - versioned artifactを追加すると、現行contract候補は2件になり、現行resolver (`s8b_floor_campaign.py:882-901`) はfail-closedする。
  - P1を入れると、床値admissionの受理集合が「拒否」からversioned record受理へ変わる。これは単なる配線ではない。
  - certified writer、holdout admission、レポート、試行台帳が空集合からv2 protocolを参照する状態へ変わる。
- 判定:
  - D460を部分改訂するだけでは不十分。D471の「resolver変更なし」と、P1を却下した記録も撤回対象になる。
  - ユーザー再裁定なしに実装してはならない。

## 見送り裁定 T-419 (1)(2) の混入

現時点では、混入は確認できません。

- `effective_clock.method` の実体比較を追加する記述はない。
- 第1世代の自己不整合を拒否するgateも追加していない。
- `ccbench_pin`によるprotocol選択と、calibration artifactのmethod・世代整合性は別の契約である。

ただし、P1はT-419(1)(2)ではなく、D460/D471に抵触する新しいprotocol選択gateです。見送り裁定の実装として偽装してはなりません。

## 発行からadmissionまでの値の追跡

P1がユーザー承認され、artifactがcommit済みになった場合の想定値は次の通りです。

| 層 | 値 | 判定 |
|---|---|---|
| issuer | `floor-protocols/e576...--511c...json`, 774 bytes, `2c8cf9be...` | 実発行は未観測 |
| resolver | 現行contract 2件からHEAD pinのv2を選択 | P1変更が必要 |
| shell driver | resolver結果を `--protocol`、metrics、job-resultへ流す | 親案で対応予定 |
| holdout admission | resolver結果v2とHEAD blob v2を比較 | 親案で対応予定 |
| certified writer | 既存resolverからv2を読む | resolver変更なしでは拒否 |
| official preflight | legacy bytes `261cec1c...` とv2 shaを比較 | v2を拒否 |
| holdout producer | legacy path/hashを読む | v2 resultを拒否、またはlegacy参照を生成 |

歴史錨定である `s8b_prediction_runner.py:79,1542-1548` と `s8b_ratified_freeze.py:76,2678` をlegacyのままにする判断自体は妥当です。過去のproof chainをcurrent resolverへ差し替えてはいけません。

## 所見 B-3 — driver自身の `--protocol` はcaller選択のまま

- 深刻度: major
- 根拠: `s2-plan.md:85-98`、`s8b_floor_campaign.py:6749-6762`、`s8b_floor_campaign.py:6036-6050`
- 再現の筋道:
  - shellはresolver結果を渡すが、driver CLIは引き続き任意の `--protocol` pathを読み込む。
  - 直接legacy pathを渡すと、driverはlegacy protocolでbuild、manifest、run idを先に作る。
  - 最後のholdout admissionでresolverがv2を返し、supplied protocolとの不一致で拒否する。
- 影響:
  - 最終的なcertified resultや試行台帳はfail-closedで生成されない。
  - しかしlegacyのprotocol shaを持つpartial run、manifest、binary storeが先に残る可能性がある。
  - 「driver層全体が同じauthorityを通る」という主張は成立しない。

## scope外だが real な所見

### B-4 — official preflightを休眠扱いしてよい根拠になっていない

- 深刻度: major
- 根拠: `s8b_floor_campaign.py:259-264,3607-3635,3662-3702,5727-5745,6740-6747`
- 再現の筋道:
  - official CLIは現在拒否されている。
  - しかしofficial coreとlaunch preflightは実装として残っている。
  - v2を渡しても preflight は `_PREFLIGHT_FIXED_FILES` のlegacy fileを読み、legacy shaとv2の `protocol_sha256` を比較するため拒否する。
- 影響:
  - officialを将来再有効化した瞬間、launch certificate受理集合はv2について空のままになる。
  - official result、manifest、report、試行台帳が生成されない。
  - 「今日は休眠だからseamは閉じた」と記録すると、次の権限裁定時に同じ破断を再発させる。
- 処置:
  - 今waveで実装せず、official preflightもv2 authorityへ接続するか、officialはlegacy専用と明記するかを裁定パッケージへ返す。

### B-5 — holdout freeze producerがlegacyへ戻る

- 深刻度: major
- 根拠: `s8b_holdout_freeze.py:1293-1336,1543-1551,1648-1651`、`s2-plan.md:64-72`
- 再現の筋道:
  - `_validate_floor_inputs()` はlegacy protocolを読み、legacy raw shaを計算する。
  - v2 official resultの `protocol_sha256=2c8...` を渡すと、legacy sha `261cec1c...` と不一致で拒否する。
  - 旧protocolのresultを渡せば、生成candidateの `floor_protocol.path` はlegacyのままになる。
- 影響:
  - v2を使ったg1 candidateを生成できず、将来のcertified chainが進まない。
  - 生成できた場合も、report/verdictがlegacy path/hashを参照し、current resolverのv2 authorityと証拠参照が分裂する。
  - closureのdedicated集合もlegacyだけなので、versioned artifactがclosureへ誤って混入する可能性がある。
- 処置:
  - T-419(3)のshell/driver scope外として、producer配線を別のユーザー裁定パッケージへ分離する。
  - `FROZEN_MANIFEST`へversioned artifactを追加する必要はない。T-1218/D471の「載せない」は維持する。

## 親の実測値の一般化

### B-6 — 「現行契約候補2件」は実発行の実測ではない

- 深刻度: major
- 根拠: brief `:11-12,28-38`、handoff `:11-24`、`output/insights/2026-08-17_floor-reseal-rulings/README.md:15-21`
- 再現の筋道:
  - 現repositoryで実在するindexはlegacy 1件だけ。
  - 2件目は合成したindexで再現した値で、`reseal-protocol`の実行、read-back、commit後scan、consumer実走は未観測。
- 影響:
  - 「発行後はadmissionがcount=2で止まる」はコードからの予測としては妥当だが、実測値として記録できない。
  - 実発行失敗やcommit後のpath差異があっても、すでにresolver変更を正当化したことになってしまう。
  - 現時点のcertified選択・レポート・試行台帳の値は変わっていない。

### B-7 — 774 bytes / `2c8cf9be...` も発行結果ではなく予測値

- 深刻度: minor
- 根拠: brief `:62-65`、`s2-plan.md:126-165`
- 再現の筋道:
  - legacy bytesをdeep copyし、`ccbench_pin`だけを置換する実装から算出した値である。
  - 実issuerのcreate-only write、read-back、post-index検査をまだ通していない。
- 影響:
  - 実artifactのshaや改行・canonical bytesが異なれば、親の固定期待値がartifactを誤拒否する。
  - 「1欄だけの差分」は、実発行後のbyte比較を完了するまで成果物事実として記録できない。

### B-8 — live閉包3点という一般化は過大

- 深刻度: major
- 根拠: handoff `:76-90`、`s8b_floor_campaign.py:3632-3702,6749-6762`、`s8b_holdout_freeze.py:1293-1651`
- 再現の筋道:
  - shell、holdout admission、certified writerの3点は、resolverを承認した場合のpilot成功経路に限れば説明できる。
  - official preflight、driver直接入口、producer write-pathは別authorityを保持している。
  - `s8b_verdict.py:953-973` はfreeze recordのpointerを読むため、producerがlegacy pointerを生成すれば下流reportもlegacyを参照する。
- 影響:
  - pilotだけはv2へ進めても、official・future refreeze・reportのauthority閉包は未完成。
  - 「全層を配線済み」と記録すると、実際にはv2を拒否する層を見落とす。

## 記録とD460の扱い

このwaveではD460を改訂すべきではありません。D471がresolver不変更とD460契約維持を明記し、親案P1を既に却下しているためです。

ユーザーがP1を再裁定で承認する場合に限り、次を撤回対象にします。

- D460の「ccbench pinを選択条件に入れない」。
- D460の「同一contract複数recordはproductionで到達不能」という理由。
- D471 `:19589` のresolver不変更。
- D471 `:19594` のD460 resolver契約維持。
- D471 `:19610-19616` のP1却下理由。

残すものは次です。

- callerはpath、contract、pin、env tagを渡せない。
- resolverはrootだけからauthority recordを返す。
- indexed bytesと再読bytesのsha照合。
- zero matchと曖昧な複数matchのfail-closed。
- 辞書順、mtime、最大pin、namespace優先による任意選択の禁止。
- D444/D471のcreate-only、legacy bytes不変、組単位発行前拒否、versioned artifactを `FROZEN_MANIFEST` に載せない契約。

worklogには、実際に発行していないこと、2件とshaは投影値であること、official/producerが未接続であることを記録すべきです。「seam closed」や「v2で測定済み」とは書けません。

**最終判定: NO-GO。**

## 総括

親案P1は、D460だけでなくD471の明示的なresolver不変更に反する。
T-1255の明示フラグとAI provenanceも、実際の発行経路には存在しない。
pilotの3点経路は、承認済みならv2へ流せる見込みがある。
official preflightとholdout producerは、v2を拒否するかlegacyへ戻す。
2件、774 bytes、sha、3点閉包はいずれも一部が投影値または限定経路の値である。
ユーザー再裁定とscope再確定なしに実装・発行へ進めてはならない。