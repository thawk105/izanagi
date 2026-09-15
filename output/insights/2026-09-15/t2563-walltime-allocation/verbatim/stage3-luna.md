## 独立の数え直し

以下、`S`＝`tools/pegasus/certify_calibration.sh`、`C`＝`orchestrator/calibrator/cli.py`。行番号は現物。

**[real / scope 内 / must-fix] 親 brief の 3230・8760・8820 はそれぞれ 20 秒不足。plan の算術訂正は正しい。**

| 計測前の項 | S の行 | 秒 |
|---|---:|---:|
| qstat | 252 | 30 |
| static probe | 383 | 120 |
| gflags configure/build/install | 475、481、487 | 180 |
| glog configure/build/install | 540、546、552 | 360 |
| third-party copy | 585–596 | 360 |
| pristine 検証 | 598 | 120 |
| CCBench configure/build | 681、682 | 1800 |
| binary hash / nm | 685、687 | 120 |
| pre probe | 729 | 120 |
| perf version / smoke | 850–874 | 40 |
| **合計** | | **3250** |

- `third_party_name` のループは２箇所ある。S:181 は存在検査だけ。S:585 は **3 回、それぞれ `timeout 120` が１回**。
- perf 候補は policy に２件。第１候補の version 成功→smoke 失敗→第２候補成功なら、`timeout 10` が４回走る。条件付きでも成功へ到達可能な経路に含まれる。
- post probe は CLI 成功時だけの 120 秒。前後の固定 timeout 指定値の和は **3370 秒**。
- CLI 予約をそのまま足すなら **3250＋4990＋600＝8840**。内蔵 reserve 60 を除く算術なら **8780**。post probe を別加算するなら各々さらに 120 秒。

**成果物影響:** 旧数値を残すと、材料レポートと新規 receipt の時間式が 20 秒過小計上される。

**[real / scope 内 / must-fix] 8840 は job 全体の「真の上限」ではない。**

timeout がない処理として、少なくとも次が存在する。

- source の `git status`：S:210、448、512、623。
- CCBench の `git worktree add`：S:626。
- `/proc` 全走査：S:698。
- worktree 削除：S:99、960。
- receipt の I/O、CLI の `fsync`：C:302–318。
- 別途、submit receipt 待ちに最大 60 回の `sleep 1`：S:197–200。

したがって **3250 は列挙した timeout 指定値の部分和**。上限計上の取りこぼしという意味で下限側の集計だが、**実所要時間が 3250 秒以上という意味の下限ではない**。

また、`remaining` は S:819 の従属値であり、固定項として再加算できない。計算後に perf 等が走るため、その遅延を Δ とすると、outer timeout が満了した時点の残余は概ね `600−Δ`。600 秒の確保自体も保証していない。

plan が明記したこの限定は正しい。一方、追補の「真値」「最大経路」という呼び方は限定を落としている。

さらに `orchestrator/calibrator/sweep.py:295` 付近は certify 時に scale 測定前で return する。CLI 式の `2*3*120=720` は**現在も存在する予約定数の項**であり、認定実行で走る２群の timeout ではない。CLI 式の意味を変更せず、由来を区別する必要がある。

**成果物影響:** 放置すると、receipt の予約数値が未計上処理まで包含する保証として材料に使われる。

## 不等式の検算

**[real / scope 内 / must-fix] `points=5` 限定の計算を CLI 全体へ拡張できない。**

既定 repetitions では、点数を \(p\) として、

```text
budget.required_s = 3190 + 360p
budget.required_s + reserve_s = 3790 + 360p
受理に必要な時間条件：3790 + 360p ≤ R ≤ Q
```

C:145–150 は start/max records と repetitions を公開引数として受け取り、C:797–813 は正値等だけを検査する。C:823 はその引数から予算を計算する。したがって CLI 直接呼び出しでは点数は可変。

| 案 | R | Q | p=5 | 時間判定を通る点数 |
|---|---:|---:|---|---|
| 現行 | 6610 | 7200 | 5590≤6610≤7200 | p≤7 |
| 案 A | 8840 | 10800 | 5590≤8840≤10800 | p≤14 |
| P1′ | 5590 | 7200 | 5590＝5590≤7200 | p≤5 |

具体例：

- `--start-records 500000 --max-records 16000000` は **p=6**。必要値 5950 は現行で通り、P1′で `reservation-mismatch`。
- p=8 では必要値 6670。現行は拒否、案 A は通過。
- p=15 では必要値 9190。案 A でも `reservation-mismatch`。

repetitions も変える場合の左辺は `1870＋120*sweep_reps*(p+2)＋120*noise_reps`。

ただし **公式 wrapper の S:903–913 はこれらの引数を渡さない**。既定の 100万→1600万、3回、10回が適用され、p=5。公式経路に限定すれば両案ともこの２判定を通る。

**成果物影響:** P1′は可変点数へ同じ新 receipt を適用すると受理範囲を縮め、案 A は広げる。「両方向に不変」という無限定の説明は誤り。

## 受理集合の不変性

**[refuted / scope 内] P1′だけで公式 job の小さい要求枠が新たに通る、という経路は確認できない。**

述語だけなら `5590≤Q<6610` が新たに通る。例は Q=6000。しかし公式 job は S:124、140 で policy の 7200 を読み、S:238 で submit receipt の要求値との一致を実行時に要求する。小さい Q の receipt はここで落ちる。

B4/B5 は実行時 gate ではなくソース整合テスト。**実際の根拠は S:238 の比較**である。CLI 直接入力では小さい Q と R=5590 の組を以前から渡せるため、CLI 未変更の今回差分が新設する経路ともいえない。

**成果物影響:** policy 据置きの公式経路では、この理由による accepted attempt の増加はない。

**[real / scope 内 / must-fix] 要求枠増加による成功集合の拡大を、現裁定下で「正当な履行」と断定できない。**

同じ所要経路が旧窓で timeout、新窓で成功するなら、完了して受理される実行の集合は広がる。異常検出の閾値を変えることとは別だが、「受理集合不変」ではない。

D1936 項38 は「必要分だけ要求時間を増やす」と明記する一方、後続 D1971 は、

> 要求時間・timeout・標本数は本waveで変更しない。

> 要求時間増加へ戻さず、時間式再凍結を完了扱いにしない。

と明記する。恒久禁止と読む必要はないが、今回案 A を積極的に認める根拠には使えない。D1986 項3・9・10 は別対象の限定裁定であり、5590 への意味変更や枠増加を直接承認してもいない。

**成果物影響:** 案 A は従来 timeout だった実行から新しい certified 材料を生成し得る。

**[real / scope 内の説明は must-fix、実装修正は scope 外] 「outer timeout 非ゼロなら accepted 成果物を一つも残さない」は成立しない。**

制御順は次のとおり。

1. C:1017 で accepted 判定。
2. C:1023 で accepted な `candidate.json`、C:1028 で材料レポートを書込。
3. C:1067 で registered へ公開。
4. C:1079 以降で公開後検査・追記。
5. C:1100 で成功終了。

**3 と 5 の間で TERM を受ければ、registered の accepted ファイルが存在したまま wrapper は非ゼロ終了し得る。** S:954–956 は failure を記録するだけで公開物を取り消さない。通常の SIGTERM は C:1101 の Python 例外処理による清掃を保証しない。

後段 `calibration_verify.py:106` 以降と `env_contract.py:605–631` は内容・hash・schema・quality 等を検証するが、wrapper の `calibrate_rc` や publish 完了記録を必須としていない。完全な公開済み JSON が参照された場合の経路は残る。途中で切れた不正 JSON は parse/hash 検証で落ちる。

一方、**測定中の rep 失敗を捨てて続行する変更はない**。certify は `require_all_reps=True`、`require_complete_metrics=True` を渡し、runner の fatal は CLI の拒否へ伝播する。quality reasons、隔離、clock 判定も今回の編集面外で不変。

正確な限定は「測定が完了する前に打ち切られた実行を、部分標本から新たに accepted と組み立てる経路はない」。これを全終了時点の公開原子性へ拡張してはいけない。

**成果物影響:** 試行の失敗記録と accepted な公開物・材料レポートが併存し、後段がその公開物を参照し得る。既存の限界であり、本件による新設ではない。

## pin の恒真化

**[refuted / scope 内] plan の B1 方針そのものは循環検査ではない。**

| pin | 分類・実際の射程 |
|---|---|
| B1：代入式全体の固定逐語 | **生成器ソースの pin**。通常の単独誤編集を検出 |
| B2：formula 文字列 | 説明文字列の pin。数値生成器の検査ではない |
| B3：`finalize_reserve(600)=5590` 等 | 表示された派生値の pin |
| B7：receipt の変数参照 | 出力との接続の pin |
| B4/B5 | PBS と policy、文字列時刻と秒値の整合 |
| B6 | reserve 表記と policy の一致、reserve と Q の大小 |

B6 は `600<7200` を調べるだけで、**5590 や 8840 が Q 未満かは調べない**。ただし一致元が別なので、検査自体が恒真なのではない。

`assert "...代入式..." in source` は実行される唯一の代入を証明しない。古い代入をコメントに残して実行式を変更する、後から再代入する場合には通り得る。これは既存の逐語 pin の限界であり、新パーサー等を足す理由にはしない。

**成果物影響:** B2/B3だけへ退化させると、receipt の数値生成が誤っても表示文字列が残れば通る。plan どおり B1 を維持する限り、通常の代入式の誤編集は検出する。

## pin 閉包の抜け

**[refuted / scope 内] 今回変更が必要な、未掲出の calibration policy byte pin は見つからなかった。**

path 以外にも以下を確認した。

- `certify_walltime(_s)`、`pegasus-calibration-policy/v1`。
- `_MOVED_KEYS` と shared policy 読出し検査。
- registry の schema key と entry 集合。
- admission registry の分類、role adapter 側の参照。
- calibration freeze authority の manifest。
- test nodeid を key にする実行時間台帳。
- 現行 `calibration_v1.json` の実 SHA-256 による逆引き。

manifest の hash は自身の fixture／gate／row 集合、時間台帳は test nodeid の所要時間であり、対象 policy の値の pin ではない。

ただし親 G の説明には訂正がある。`test_pegasus_policy_registry.py:27–30` は key の「存在検査」ではなく **移設済み key 名の集合定義**。検査は production が shared policy からそれらを直接読むことを検出するもの。値変更による追加更新箇所はない。

**成果物影響:** 追加の pin 更新漏れによる成果物参照の破損は確認できない。G の検査説明の訂正は **nit**。

読めなかった推測先は `orchestrator/calibrator/quality.py` と、`tools/test_groups*`、`tools/*manifest*`、`.codex/*manifest*`、`orchestrator/tests/test_pegasus_admission*`。実在ファイルを再探索して検査を継続した。必読射影ファイルの読取り失敗はない。

## 総括

**第３案「現行の数値判定を据え置き、算術誤記と保証の限界を追補する」を選ぶ。**

- `R=6610`、Q=7200、timeout、標本数を維持する。
- 6610 は**既存の受理判定用の凍結値**として明示し、正しい実行上限として再認証しない。
- 3250／8840 の導出、未計上処理、未実行の CLI 予約項、公開後 timeout の限界を既存成果物の文面に出す。
- 過去 receipt の bytes と解釈を遡って変更しない。

名称は **「予約式の不整合と保証限界の明文化」**。D1936 項38の「再凍結完了」ではない。D1971 の明示的な据置きと未完了扱いを優先し、D1986 の限定開示という扱いに沿わせる。35〜39 秒や186秒の実測は最大経路の保証にも、要求枠が常に十分という証明にも使わない。

P1′は公式経路だけなら数値整合するが、未解決事項を閉じるために `required_s` の意味を変える必要性はない。現行値を保持する第３案なら、点数可変時を含む判定の変化も避けられる。

編集・テスト実行・commit・push は行っていない。