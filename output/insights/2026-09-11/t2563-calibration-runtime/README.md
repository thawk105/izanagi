# T-2563 認定較正 job の実時間 — コピー並行化は採用しない

3依存コピーだけを並行化して比較したが、短縮効果を示せず候補を全撤回した。
全体は4秒短かったものの、変更前の工程ですでに3秒違い、コピー区間の短縮は確認できない。
要求時間・timeout・標本数・検証は変更していない。T-2564や較正対象の拡大は含めない。

## 既存記録を先に分解した結果

既存成功例989271.nqsv (mocc/rr50/t48、bnode020) のscheduler Elapseは302秒、
開始epochからjob-resultまでは298秒だった。static→preが30秒、pre→postが263秒。
保存fileのmtimeは取り込み時刻へ揃っていたため工程計時には使えない。
copy85秒・pristine検証22秒という旧実測はlogin→NFS側であり、compute→/scrの費用ではない。
正本は既存 `output/insights/2026-09-10/t2535-certify-offline-fetch/README.md` とjob記録。

測定は3点×3rep＋noise10rep＝19回で、重複ではなく標本設計どおり。
canary starttime差はsweep3群が1068/1196/1458、noiseが3547 tick。
当該jobの秒換算根拠・cooldown観測列は保存されておらず、秒数を捏造しない。
代表walltimeは1標本であり、3倍を全rep合計にはしない。

gflagsは3ソースを通常版/非スレッド版へ各1回、計6compile・2archive生成していた。
単純な未使用重複という親仮説は撤回した。指定pinのconfig.cmake.inにはstatic target名の
展開漏れがあり、component無指定のglogがnothreadsを選び得る。
フラグで変更できてもリンクするライブラリを変えるため、今回の時間短縮へ混ぜなかった。
gflags→glog→CCBenchはinstall成果物に依存する。共有build再利用とmasstreeの共有source直参照は
fresh/job-private契約を破る。時点の異なるprobeやbinary照合も検証省略として削減しない。

## 今回の比較

既存submitterを使いbefore/after各1回だけ。workload=mocc/rr50/skew0.9/rmw0、threads=48、
同一CCBench pin・toolchain・依存pin・標本設計・要求7200秒と各timeoutを維持した。
候補は3copyの並行起動と全waitだけで、全成功後のpristine検証はそのまま実行した。
比較候補commitは `7044055cdd49df33a7c1d29f7a6eda7b62cafd9f`、beforeは
`d85bbb21196f503440ef9641e3dec095e3b43844`。候補のcode/testはD95 authorが書き、撤回も同authorが行った。

| 区間・結果 | before 991694 | after 991727 |
|---|---:|---:|
| host | bnode038 | bnode064 |
| Created→Started (queue・起動待ち) | 7秒 | 525秒 |
| scheduler Elapse (主比較) | 186秒 | 182秒 |
| Started→job-result (補助比較) | 182秒 | 178秒 |
| Started→static observed | 6秒 | 6秒 |
| static→pre observed | 33秒 | 29秒 |
| pre→post observed | 143秒 | 143秒 |
| quality / calibrate_rc | accepted / 0 | accepted / 0 |
| sweep標本 / noise標本 | 9 / 10 | 9 / 10 |

同じ環境契約による比較だが、同一hostの対照ではなく各1回である。
job内部epoch差とscheduler会計の4秒差は別の範囲として保存し、工程へ勝手に配賦しない。
起動待ちの518秒差もcopy並行化の効果ではない。

新規jobの移送前file時刻を `before/after/original-file-times.json` に保存した。
以下は秒精度のログ更新時刻から得た**付帯処理込みの粗い区間**であり、専用timerによる純処理時間ではない。
stderrに出力があった場合のmtimeを開始時刻には使わず、空stderrとstdout終端を使った。

| 境界 | before | after |
|---|---:|---:|
| gflags source-status→configure stdout終端 | 2秒 | 1秒 |
| gflags build空stderr→stdout終端 | 2秒 | 2秒 |
| glog source-status→configure stdout終端 | 7秒 | 5秒 |
| glog build空stderr→stdout終端 | 2秒 | 2秒 |
| glog install stdout終端→pristine検証の空stderr | 1秒 | 1秒 |
| pristine検証の空stderr→worktree-add stdout終端 | 1秒 | 0秒 |
| worktree-add→CCBench configure stdout終端 | 2秒 | 2秒 |
| CCBench configure→build stdout終端 | 14秒 | 14秒 |

gflags/glogの未変更configureに計3秒差があり、コピーを含む区間はどちらも約1秒。
全体4秒 (約2.2%) の差をcopy並行化へ帰属できない。統計的な同等性や「一切効果がない」とは主張しない。
短縮効果を示せなければ実装を残さないというユーザー指示に従い、測定を増やさず不採用とした。

処理回数は両jobとも、gflags/glogのconfigure/build/install各1、CCBench configure/build各1、
copy3・pristine検証1。認定の標本は19回、window probe記録は10件。
wrapperとCLIの異なる時点の検証を維持し、trace-disabled build、測定前の子孫終了、
各測定窓の単独性、自己比較を既存認定経路で確認している。

## 避けられない費用と実行可能な構成

今回の19標本ではextime=3秒の指定区間が計57秒、cooldown正常通過には最低2間隔＝60秒を要する。
少なくともこの117秒分に、初期化・build・検証・probe・集計が加わる。将来の全体時間保証ではない。
今回確認できた実行可能な最小構成は、既存mocc/rr50/t48の逐次jobをそのまま1本実行する形で、
実績は186秒である。標本削減・検査省略・不適格な証拠再利用は短縮案にしない。

最終code/testは起点のGit blobへ戻した。時間式も既存構成のままで、不整合は未解決として残る。
旧予約項を個別command上限へ展開した部分和は、逐次8350秒、copyだけ並行でも8110秒
(mocc/tictoc、siloはさらに300秒)。これは実時間でも全処理の厳密な総上限でもない。
CLIは別に4990秒の予算とwrapper reserve600秒の包含を要求する。
これらを実測186秒やouter timeoutの打切り式で置き換えて成功完遂を保証したことにはしない。
要求枠増加は今回の既定解に戻さず、T-2563の時間式再凍結を完了扱いにしない。

## 検証と一次資料

- 候補の親実走: workload74passed/6.16秒、tools69passed/4.03秒、追加consumer/meta2passed/51.61秒。
  すべてtools/run_tests.py経由。最後の2nodeは同じ2file bytesのauthor worktreeで実行した。
- plan1、consult2、author1、review2、撤回author1。静的所見と親裁定はverbatim/へ保存。
- 両計算jobは認定成功。before/after/へ元receipt・profile・標本・window・主要buildログ・会計を保存。
- 最終実装面差分ゼロのためDW-S04の変異免除を適用。候補の変異killを実証したとは報告しない。
- 復元後の関連2fileは139passed/13.20秒、runner rc=0。文書検査・Codex設定検査・spool dry-runもrc=0。
- 保存ログと逐語の末尾空白がgit diff --checkに抵触したため、可視文字を保って正規化した。
  `whitespace-restoration.json` は原文SHA-256・byte数・行末suffixを保持する。
  原文がLF終端でなければ保存版の最後のLFを1個除き、各1始まり行へhex suffixを戻すと原文を復元できる。
  12fileすべての原文hash・byte数との一致を検算した。元job記録そのものは編集していない。
