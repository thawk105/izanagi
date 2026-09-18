## 判定と確認範囲

**GO。実行・収集面に、今回の結果を無効にする must-fix は見つかりませんでした。** ただし、discriminator の実走被覆は **0件**です。

指定資料、全9 block・314走の JSON、保存 raw、dispatch log を照合しました。Q1/Q2 の集計は現行 runner でメモリ上に再計算し、summary と一致。G2 の全336 raw ファイル、計2,007,636,727 byteについて manifest のサイズ・SHA256 一致を確認しました。変更・pytest・ベンチ再実行は行っていません。

以下、`J/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/`、repo パスは指定 worktree 相対です。

## must-fix

なし。

Q1 の `BACK_OFF=1` は既に裁定追記2で観測へ格下げされ、Q2では修正されています。また、Q2実走時の75件の分類誤りは、指定された主解析 `summary-q2.json` では補正済みです。

## should

**S1 — 実走 runner と再集計 runner の版の束縛を補完する。**

- **根拠:** `J/probe/t2774_probe.py:479–532` は source・patch・binary・policy 等を保存しますが、runner 自身の SHA256 は保存しません。author／fix1／fix2b 報告の runner は524／519／655行、現物は704行です。`summary-q2.json:187` 以降には入力 result の SHA と再分類履歴がありますが、再分類に使用した runner の digest はありません。
- **成果物への影響:** build 条件は再構成できても、実走時と再集計時の分類処理を原本から一意に再現する束縛が不足します。
- **是正案:** 保存済みの版があれば、実走・再集計それぞれの runner 原本と digest を対応づけて退避する。今後は既存 bindings／summary に runner digest を加える。現物の digest を過去の実行版として遡及記入しない。

現物の SHA256 は `2e2ddea834f782abb7a671b42d8a57f82ac8b82d7ac90d23965ad3ca3fd41c00` です。

## nit

**N1 — 「単独性確認を通過」と「他 job 不在の実証」を区別する。**

- **根拠:** runner の呼出位置は `:459` の準備前と `:283` の各走直前。helper は `s3_mocc_lock_coverage.py:32` で `p2_2` から import され、実体は今回の射影外です。指定 dispatch log に host や process 一覧はありません。
- **成果物への影響:** 他 job の混載によって今回の率が変わった証拠はありません。ただし、これらの資料だけで node 専有を証明したとは書けません。
- **是正案:** 「確認呼出を備える runner が完走。host は result の記録」と記述する。必要なら既存の実行時単独性記録を添える。

**N2 — 異常終了時の保存被覆は、通常例外まで。**

- **根拠:** runner `:545–556` は準備・build 中を含む通常例外を最終 result に保存します。一方、site 判定・最初の単独性確認・出力 directory 作成はその try より前です。`write_json:48–59` は file fsync＋同一 directory 内 rename ですが、directory fsync はありません。指定9 log は全件成功経路です。
- **成果物への影響:** 今回の保存欠落は0件。起動初期失敗、強制終了、保存先障害まで「必ず result が残る」と一般化する根拠はありません。
- **是正案:** 成功実走と例外時の静的被覆を分けて報告する。

**N3 — 未開始走の集計と walltime は、再利用時の被覆限界。**

- **根拠:** runner `:185–215` は `runs` から N を算出し、block の `planned_runs/not_started` を集計しません。Q2は50走なので、verify が毎回300秒なら、runを3秒と置いても252.5分＋準備となり150分枠を超えます。
- **成果物への影響:** 今回は全 block の `not_started=0` で影響なし。途中終了した block では、summary 単体から予定分母を復元できません。
- **是正案:** 今回は完走件数と予定件数を併記する。runner を再利用する際は未開始数も集計する。

## 束縛と build 条件

全 block の repo HEAD は `d2ebef7a407dc6be61622ed596cf08b8b518f606`、policy SHA256 は `66ea7135…986acd6`、compiler は同じ gcc/g++-11 の path・version-body digest です。

Q1は source OID・両 patch SHA・arm別 source SHA／binary SHA・configure argv を保存。Q2はさらに arm別 pin・patch一覧・witness・observational_only と arms JSON の digest を保存しています。hostname・開始／終了時刻は result 本体にあります。

**BACK_OFF の差は bindings から確認できます。**

- Q1：専用 `configure_defines` フィールドはありませんが、全armの `configure_argv` に `BACK_OFF=1`。例：`J/arm-B/B1/result.json:2765,2794`。
- Q2：`configure_argv` と `configure_defines` の両方に `BACK_OFF=0`。例：`J/arm-B/Q1/result.json:5148,5171`。pilot の固定オプションとも一致し、source/build/依存先の実行時 path は異なります。

**binary SHA は一致しません。** Q1の短縮表示は次のとおりです。

| block | instr | diag |
|---|---|---|
| B1 | ed3fd0ae2310 | 6e9d532c65b4 |
| B2 | abbfca0996e2 | 23b24d47a27c |
| B3 | 5a76a6911232 | f0dc8a39af0a |
| B4 | a480161fab29 | 593c7c81088b |

各armの source file SHA は4 blockで一致しています。Q2も5 armそれぞれ、4 blockの binary SHA がすべて異なります。

原因候補は、一意な scratch/source/build path の埋込み、依存ライブラリの build 差、それらに伴う build-id 差です。同じ source・compiler だけでは byte 一致は保証されません。binary は scratch とともに削除されているため、**差が path 等だけに限られるか、命令列も違うかは未確認**です。これだけで率を無効とは判定しませんが、bit再現を確認済みとは書けません。

## 走数・欠測・主解析

| 系列 | 予定／保存走数 | 未開始 | benchmark rc≠0 | timeout |
|---|---:|---:|---:|---:|
| smoke | 2／2 | 0 | 0 | 0 |
| Q1：B1〜B4 | 各28／28、計112 | 0 | 0 | 0 |
| Q2：Q1〜Q4 | 各50／50、計200 | 0 | 0 | 0 |

全314走で result 内の run と個別 `run.json` が一致し、stdout／stderr、verifier JSON、discriminator 記録が存在しました。

Q1は **instr 56/56、diag 56/56** が certified serializable。smoke は各1走で別枠です。

Q2の主解析は次のとおりです（`J/arm-B/summary-q2.json:4–182`）。

| arm | N | G2 | certified no-G2 | indeterminate | 再分類後failure |
|---|---:|---:|---:|---:|---:|
| p058-plain | 40 | 2 | 0 | 38 | 0 |
| e9-plain-nowit | 40 | 3 | 0 | 37 | 0 |
| e9-instr-nowit | 40 | 2 | 38 | 0 | 0 |
| e9-instr-wit | 40 | 0 | 40 | 0 | 0 |
| e9-diag-wit | 40 | 0 | 40 | 0 | 0 |

実走保存時の failure はQ1〜Q4で **19／19／20／17件、計75件**。すべて `rc/verdict/aggregate contradiction` で、timeout・JSON破損ではありません。実 verifier は rc=3、`indeterminate`、`serializable=true`、`integrity.clean=false` でした（例：`J/arm-B/Q1/runs/001-p058-plain/verifier.json:9–21`）。現行 `classify:113–127` はこれを受け入れ、主解析の再分類履歴と再計算結果が一致します。

**summary の m=40 は「有効な verifier 出力数」で、全走が判定可能という意味ではありません。** plain 2 armの2/40・3/40は検出割合として示し、38／37件の indeterminate を併記すべきです。`decisive_m` だけを使った2/2・3/3も母集団のG2率にはできません。

## raw・manifest・discriminator

G2は計7走で、すべて witness-off でした。

| block | G2走 |
|---|---|
| Q1 | 010-p058-plain |
| Q2 | 040-e9-plain-nowit |
| Q3 | 036-e9-instr-nowit |
| Q4 | 032-e9-instr-nowit、040-e9-plain-nowit、043-p058-plain、044-e9-plain-nowit |

各走48本、計336本の trace を保存し、全 manifest digest が現物に一致しました。非G2の307走には trace／witness raw が残っていません。

7つの trace-manifest は schema・workload・pin・binary SHA・root_dir が bindings／verifier と整合し、ファイル集合も一致します。verifier の result shape・trace_dir は `_validate_verifier:388–472` のG2入力要件と整合します。

ただし、**witness-manifest は0件、discriminator 起動も0件**です。7走とも `reason="witness-off"` で、runner `:323–327` の意図した未実行経路です。

- supported／contradicted／indeterminate／no-g2／input-rejected：すべて0件。
- input-rejected の stderr：該当なし。
- `discriminator.json` の存在は起動証拠ではありません。未実行時にも `:359–360` が記録を作ります。
- diag の全97走で、run と discriminator 記録の `observational_only=true` を確認しました。実際の診断arm識別結果はありません。

退避は `:294–304`、非G2削除は `:347–351`、scratch全体の削除は `:548–550` で、G2 raw を退避後に scratch を片づける順序です。

## 実行順・node・投入形

全記録の ordinal／pairまたはround／orderを照合しました。Q1は14 pairをAB/BA交替、Q2は5 armの開始位置を毎round回転し、各armが各位置に2回ずつ現れます。

Q1のB1／B2／B3／B4は、それぞれ bnode002／003／012／022で、両armとも **0/14** です。

Q2のblock別検出数／有効verifier出力数は以下です。plain列には前節の indeterminate を含みます。

| block／node | p058-plain | e9-plain-nowit | e9-instr-nowit | e9-instr-wit | e9-diag-wit |
|---|---:|---:|---:|---:|---:|
| Q1／004 | 1/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| Q2／006 | 0/10 | 1/10 | 0/10 | 0/10 | 0/10 |
| Q3／009 | 0/10 | 0/10 | 1/10 | 0/10 | 0/10 |
| Q4／022 | 1/10 | 2/10 | 1/10 | 0/10 | 0/10 |

node差の推論は行いません。

requestはQ1が5068／5069／5070／5072、Q2が5142／5143／5144／5145（いずれも `.nqsv`）。各log `:3,11` が request と result path を結び、hostname は各result `:4` にあります。

両launcher `:11–12` の指定は walltime 9000秒、queue-wait 3600秒、overall-grace 4200秒。4つの異なるworktreeから投入されています。

**pending orphan hold の保存は正常経路です。** dispatcher `:3779` 付近でqsub前に作成し、終端証拠保存後に解除します。全9 logで `:2` に作成、`:8` に削除、`:9` に child rc=0 があり、今回の投入が orphan-hold 拒否や残留で終わった記録はありません。

## 時間・env・保存の実証範囲

elapsed の分布は秒単位で次のとおりです。

| 系列 | run_s 最小／中央値／最大 | verify_s 最小／中央値／最大 |
|---|---|---|
| smoke | 3.068／3.069／3.069 | 17.286／17.937／18.588 |
| Q1 | 3.068／3.069／3.119 | 16.686／17.786／18.687 |
| Q2 | 3.068／3.068／3.123 | 10.528／18.612／22.742 |

`discriminator_s` は未実行のため全件ありません。

- **「smoke 80秒」**：会計 `dispatch-smoke.log:39` の値として正確。Started→Endedは76秒、runner内部は75.641秒です。
- **「verify 17〜19秒」**：smokeの17.286／18.588秒と整合します。
- **「Q1各block 10.6〜10.8分」**：runner内部はB1から645.964／637.796／635.356／638.917秒、約10.59〜10.77分。会計Elapseは652／643／641／645秒、約10.68〜10.87分なので、会計値を指すなら上端は10.9分です。
- Q2内部は1102.551／1110.422／1100.263／1111.186秒。会計上も1105〜1117秒で、9000秒枠に7883秒以上残っています。

envは `PATH=os.defpath` ですが、verifier／discriminator は `sys.executable` の絶対pathとrepo cwdで起動します（runner `:285,306–311,330–335`）。今回、verifier全314走でこの面の起動失敗はありません。将来、補助コマンドが非標準PATHにしかない、または外部環境設定が必要な依存が追加された場合には不足し得ます。discriminator側は静的確認に留まります。

`TMPDIR` は `:475` で設定し、checkoutは `:502`。`patchharness.py:362` が明示的にこの値を読むため、設定順は適切です。

## 総括

**GO：今回の実行・収集結果は、限定を明記した観測資料として採用可能です。**

Q1はBACK_OFF=1の参考観測。Q2は各arm40走が揃い、再分類後の欠測・実行失敗は0件です。ただしplain 2 armには計75件の indeterminate があり、discriminator は全件未実行です。根因識別や、その実走経路の成功を示す結果には昇格できません。

残る should は、実走・再集計 runner の版を再現資料へ束縛する1件です。
