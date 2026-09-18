# T-2489 — A-2の5ノード化とnode-local lockの局所実測

**A-2の `scheduler.nodes=5` はD2148項5に従って採用する。局所lock候補は不採用とする。**
候補同士は同一ノードで排他され、別ノードでは同時取得できた。しかし、既存default consumerとの
組合せは同一ノードで両方向とも同時取得でき、従来の協調排他を失う。共通job bodyへの一行追加は撤回し、
既存lockを保持する。全launcher改修や新gateへ範囲を広げない。

本資料は実行基盤の判断材料であり、CC性能・正式認証の結果ではない。付随性能値を論文採用値へ昇格せず、
遠隔実行の追加総timeoutも保留する。規律2・認証条件・anomaly拒否は維持する。

## 変更と根拠

- policyは `orchestrator/campaign/paper_story_a2_certification.v2.json` のnodes一キーだけ1→5。
  literal policy pin、4 siblingの正例、既存run_workload負例のhost入力、nodefile、qsub argvを同時整合する。
  単一ノード契約は専用fixtureで保持し、共通fixtureをnodes=1へ戻して出荷policyの変更を隠さない。
- policy SHA-256は `cacfdd5dd5f5841ed300310f73fcf36c0684b401c15cf88a83e9405fe86e5e3b` から
  `f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c` へ変わる。
  schedulerを含まないprotocol SHA-256は
  `d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c` のまま。
- nodes採用の既往根拠は `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md`。
  約50分→12分08秒・node秒+16%は当該attemptの観測で、比較attempt間にはprotocol・job body・adopted
  source bytesの差もある。一般的な倍率や将来のqueue待ちを保証しない。
- 過去の凍結artifact・attempt・policy証拠は変更しない。新policyのbytes束縛は新attemptで生成する。

## 局所候補と実測条件

候補はA-2/A-6共通 `tools/pegasus/paper_story_a2_certification.sh` の既存
`mkdir -p "$scratch_base"` の直後へ `export IZANAGI_BENCH_LOCK="$scratch_base/bench.lock"` を置くもの。
jobごとのscratchやTMPDIRをlock pathに含めない。固定pathは
`/scr/tanab/paper-story-a2-certification/bench.lock`、defaultは
`/home/SFC/tanab/.izanagi/bench.lock` だった。

| 項目 | 実測値・識別 |
|---|---|
| 日時・request | 2026-09-19、9137.nqsv、2ノード・上限5分 |
| 割当・実hostname | bnode082 / bnode083 |
| 実走commit | c5bfe9e8249634236ac267e4114044433a64490c（試作を含むauthor記録） |
| 基準local main | 7975385b55a2e3451f6c80d584a9312f44d5199d |
| Created / Started / Ended | 07:32:50 / 07:38:45 / 07:38:47 JST |
| NQSV会計Elapse | 6秒（上記時刻差とは別の会計field） |
| filesystem | 両ノードとも `/scr` はXFS、`/home` はLustreの `rw,flock` |
| probe Python SHA-256 | 3cf2f694c1a0798236b71b145e351e62c82c458124a5580b572ea0ca5fff04bd |
| probe PBS SHA-256 | dac35103eb74e938f8183e2f0815bcf92dd487cf9e91d24e2776cd30dbc95b6e |
| lock.py SHA-256 | fbc371a864954a19de6e54fe7c3925ab8194d1a5ef24e12ce61acae0fd739e89 |

probeは候補job bodyの実source代入行とexport位置を検査し、その代入を評価してpathを得た。
別processが実 `bench_lock(path=None, blocking=False)` を呼び、default側では環境overrideを除去した。
同一ノードのprocessには別TMPDIR・別scratchを与え、HOMEは両ノードで同じ実体に固定した。
保持完了通知→挑戦結果→解放通知の順で同期し、時計差から同時性を推定していない。
probeの45秒待機上限は実験の通知待ちだけで、production timeoutは変えていない。

## 観測と採否

| 保持側→挑戦側 | 同一ノード・別process | 別ノード | 解放後の保持側再取得 |
|---|---|---|---|
| candidate→candidate | BenchBusy | 取得成功 | 成功 |
| default→default | BenchBusy | BenchBusy | 成功 |
| candidate→default | 取得成功 | 試験対象外 | 成功 |
| default→candidate | 取得成功 | 試験対象外 | 成功 |

両rankはcomplete、failure記録なし。schedulerのrequest消滅と両jobの出力境界を持つ会計を確認した。
消滅の一次出力は `evidence/qstat-terminal.stdout`（stderrは空）。Post-running時の出力とも区別して保存した。
同一ノードcandidateの保持者PID3123598と挑戦者PID3123600は同じdevice/inodeを開き、挑戦側が拒否された。
別ノードでは同じ数値のdevice/inodeが現れるが、それを共有inodeの証拠とはしない。
別ノードでの独立性は保持中取得とmount情報から判定した。

**不採用理由はmixed path両方向の同一ノード同時取得である。** 候補headと、環境指定なしでdefaultを使う
A-1/B10 shape等は別fileをlockする。開始時の競合process検知は、別lockを取得した双方の同時開始を
原子的に排除しない。gen_Sの `Exclusive submit=OFF` も実測し、48CPU割当を非同居の保証にはしない。
workerのtask固有lockやB10-grid/A5のjob固有lockは既存挙動であり、この候補で新たに失う保護と混同しない。

試作の継承harnessはA-2/A-6×親lock unset/別値の4caseでrun-workload子への到達を確認した。
git・hostname・qstat・staging・preflight等はstubであり、実flock・実scheduler予約の証拠ではない。
一方compute probeはpathの実flockを測るが、実job body全体を通した認証campaignではない。
同一予約内の別process・別scratchの観測から、独立scheduler jobのnamespace共有や全bencher排他を主張しない。
CC性能binaryは実行しておらず、旧資料の約8分という静的見積りも検証していない。

## 検証と保存

- 試作時の関連5fileはrequest9138.nqsvで **442 passed / 1 skipped、65.90秒**。
  skippedは既存の明示hold対象1件。候補継承試験とpolicy/fixture閉包を含む。受入全走の代替ではない。
- 独立plan・相談2本・レビュー2本を実施。レビューはnodes=5閉包に新規阻害所見なし。
  候補exportを出荷しない所見は実測採否へ反映した。
- 一次資料は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-nodes5-local-lock/probe-20260919a/`。
  各caseの保持・挑戦・解放後JSON、環境・mount・code識別、qstat、会計が揃う。
  repo内 `evidence/` は両rank結果・環境・qstat・会計の射影、`verbatim/` はplan/相談/裁定/author/reviewと
  probe原文（非実行用.md）を保全する。候補patchは同job dirの `candidate-implementation.patch`。
  probe原文の上記SHAは.md保全分とbyte一致する。
- qstatと子出力の末尾空白・最終改行だけを可逆正規化した。元/正規化SHA・byte数・行ごとの復元suffixは
  `evidence/normalization.json`。9ファイルの逆変換で元SHA一致を確認し、可視文字は変更していない。
- 試作撤回後のfile単独走は認証test **215 passed、7.10秒**、job-contract test **72 passed、15.26秒**。
  いずれも計算ノードの正規runner。最初の単独走投入はprovenance dispatch中のholdにより投入前rc16で拒否され、
  新jobは0件。親の直列化確認不足を訂正し、監査終端後に新しいlog/doneで再投入した結果である。
- 焦点レビューは候補撤回・両rank照合・policy閉包をclosedとした。消滅出力の追跡性だけpartialだったため、
  上記qstat一次出力を追加した。最終codeはpolicyと2testの3file、job bodyは基準SHAと一致する。
