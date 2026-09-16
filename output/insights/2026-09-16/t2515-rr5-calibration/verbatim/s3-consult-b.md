## 所見

以下、S=`tools/pegasus/submit_certify.sh`、J=`tools/pegasus/certify_calibration.sh`、W=`tools/dev_wave_wait.py`。行番号は現 worktree。**静的検査のみで、pytest・投入・計算ノード検査は未実行。**

[1] **real・高 —「先行と同一 script bytes」は失効。旧 SHA の転記は今回の証拠束縛を壊す。**  
現 HEAD は `262c2993eae89f452dcea35fc61f97e41a689e8e`。現 J の SHA256 は **`3fc75c03fb66b4c284b70d6558b7fbe6eb081a2d02b3f10c07a1c99bb570e110`**。先行 3 件の submission が指す `0600887d92538b3f34d894f9674d202d0a29a578` と比較した結果：

- J：予約式のコメントと acquisition receipt の `walltime.formula` が変更済み（J:7–24、784–806）。実行 timeout の変更ではない。
- S：相対 job path の絶対化と、`cd "$REPO_ROOT"` 後の qsub が追加済み（S:211–229）。現在は wave root 指定と実行 root が束縛される。
- `policy.json`、`policies/calibration_v1.json`、CCBench gitlink：差分なし。
- calibrator：`analyze.py` の選択処理は D2026 により変更済み。`632754bbc` が HEAD の祖先であることも確認した。

したがって先行所要は参考値として使えるが、**同一実行物による所要保証には使えない**。差分だけで先行測定を無効とする理由もない。

[2] **real・高 — attempt 追加は source identity を壊さないが、未収録のまま受入・land に進むと止まる。**  
S:110、J:223 は `output/` を除外する。新 attempt はまず untracked として増えるので、「既存 tracked file を書き換える」とは限らないが、通常の tree clean は崩れる。対象は attempts だけでなく calibration の **job-staging と registered** も含む。W:360–363、2854–2859 は untracked を含む clean を要求し、`tools/dev_wave_land.py:1846–1848` も wave の完全 clean を要求する。job 終端後に証拠・文書を収録してから受入へ進む必要がある。

[3] **real・高 — 親 P3「実装面なし」は、既存コーパステストのままでは成立しない。受入全走を阻害する。**  
`orchestrator/tests/test_env_attestation.py:1011–1022` は、v1/v2 を区別せず `attempts/*/calibration.md` を固定集合と比較する。通常の新 attempt は CLI:1028 で Markdown を追加する。段2が指摘した問題は実装上実在する。これは source identity の問題とは別であり、accepted の品質判定を変更する理由にはならない。**pytest の失敗を実測したという報告ではない。**

[4] **real・中 — hydrate 完了だけでは投入準備完了にならない。共有ソースと計算ノード側依存が残る。**  
現物では wave の staging root と 3 依存は実ディレクトリ。gflags/glog は policy 指定の **repo 外絶対パス**に実在し、HEAD はそれぞれ `e171aa2d…`／`8f9ccfe7…`、status は空。CCBench も HEAD/gitlink=`511c9538…`、status は空だった。現時点の「新 checkout に依存がない」という疑いは退けられる。

ただし gflags/glog は wave 専用ではなく、他作業の変更で J:444–470、508–534 が止まる。hydrate cache の存在自体は job の成功条件ではない。job は staging をコピーし、**コピー先の pin・Git root・clean を再検証**する（J:598–630）。build cache は使わず `/scr` で再ビルドする。

[5] **推定・高 — 現状で残る停止経路は以下。発生済みとは判定していない。**

| 条件 | 停止箇所・影響 |
|---|---|
| legacy clock 環境変数が定義済み、引数不正、staging 消失・symlink化、policy 欠損・解析不能 | S:22–98、J:119–205。明示 exit 2 |
| 投入前／開始前の非 output dirty、HEAD・script・receipt・request 条件不一致 | S:104–113、J:220–260。exit 2 または Python 非ゼロ |
| repo 外 scheduler 証拠領域、submission、job-staging の権限・容量・create-only 衝突 | S:114–132、J:40–57。exit 2 または shell 非ゼロ |
| preflight コマンド失敗 | S:151–156、200–202。exit 3。**rc=0 でも queue 稼働・残高十分とは限らない** |
| qsub 成功後の ID 解析／receipt 書込み失敗、可視化が60秒を超過 | S:237–283、J:207–216。投入済みなのに launcher exit 4、または job exit 2 |
| PBS 変数不備、計算ノードの `/scr` が作成不能・既存 | J:28–57。exit 2。login の `/scr` 確認では代用できない |
| allocation/start 不明、hostname 不一致、topology 読取不能 | J:265–369。exit 2 または Python 非ゼロ |
| module／compiler／cmake／nm／Python 3.10 候補が使用不能 | J:396–440、581–595。exit 2 または shell 非ゼロ |
| 依存 source の変更、コピー・pristine 検証・build失敗／timeout | J:444–630、694–700。exit 2、124、その他非ゼロ |
| CCBench pin/clean不一致、worktree追加失敗、binary不存在、trace混入 | J:632–707。shell assertion または exit 2 |
| build 子孫残留、pre-probe不適合、module名なし、acquisition receipt不成立 | J:711–848。非ゼロ終了 |
| 予約時間不足、perf候補全滅 | J:850–909。exit 2。CLI予約検査も別途残る |
| CLI品質却下・publish失敗、post-probe失敗、cleanup失敗 | J:955–995。非ゼロ。公開済み成果物と共存しうる |

`qstat` が空だったことは瞬間的な観測であり、queue が稼働可能である証拠でも、今後の単独性保証でもない。

[6] **推定・中 — CCBench worktree 操作の競合は同一 Git common dir を共有する場合に残るが、主 checkout との直接競合は確認されない。**  
wave の common dir は `.git/worktrees/dev-wave-t2515-rr5-accepted-calibration/modules/external/ccbench`、主 checkout は `.git/modules/external/ccbench` で別だった。したがって「他 wave なら必ず競合する」は誤り。ただし同じ wave の submodule を操作する主体とは J:639、992 の add/remove が競合しうる。どちらも timeout がなく、共有 FS の遅延も予約時間を消費する。先行記録にも worktree add の13分遅延がある。

[7] **real・高 — `job-result.json`、`failure.json`、registered の存在だけで正常成功と読むと誤認する。**  
CLI:1067 の publish 後にも自己照合・attempt確定・publish receipt 書込みが続く。さらに J:961 の post-probe は **job-result より前**、J:992 の通常 cleanup は **job-result より後**である。

- publish 後の失敗で registered が残り、attempt は rejected／rejection になりうる。
- `calibrate_rc=0` の job-result と、signal／cleanup由来の failure が共存しうる。
- J:28–57 の早期失敗は trap 設置前。failure は残らない。
- failure 書込み自体も J:69 の `|| true` で失敗を許容する。SIGKILL も捕捉しない。
- EXIT cleanup の失敗は J:112–115 で元の rc を維持する。`failure.json` 不在は cleanup 成功の証明ではない。
- `/scr` の binary・build tree は scheduler cleanup で失われる。後から回収できる前提は不可。

[8] **real・中 — 段2の compute 待ちは使用可能。ただし rc=0 は成功判定ではなく終端判定。**  
W:1642–1652 に経路があり、W:2000–2057 はファイルだけを15秒間隔で確認し、qstat を呼ばない。`scheduler_nqsv.py:154–183` は対象 ID 行がちょうど1本、その後に `Ended Request Time:` があることを要求する。先行 request `998860` の repo 外 `.scheduler.stderr` は実際にこの形式だった。

今回も **新 nonce の scheduler stderr** を `--accounting-file` にし、`--done-file` は存在しない request 固有パスを渡す構成でよい。`job-result.json` を done-file にすると cleanup 前に待ちが終わるため不可。会計未着・形式変更では既定6時間まで待ちうるため、待ち手の timeout を job 失敗や取消と混同しない。

[9] **real・低 — silo 1本に絞る scope を覆す、現在停止中の研究主張に結び付く根拠は見つからない。**  
J は1 protocol／1 jobで、各 job が依存 build・cooldown を個別に払う。3本同時投入してもこの費用は共用されず、同一ノード・同一環境時点も保証されない。将来 mocc/tictoc の取得が必要なら queue 待ちを並行化できるが、それだけでは今回の追加投入の根拠にならない。`docs/phase3.md:534–546` の rr5取得と workload入力化に、非 silo rr5 の同時取得を必須とする条件はない。ただし T-2224 の「本題に不要」は別タスクの判断なので、それだけを今回の根拠にしない。

## 投入前チェックリスト

1. **記録する SHA を現物へ訂正する。** 先行との差分、今回の HEAD、launcher、policy、CCBench pinを今回の証拠として固定する。
2. 非 output の変更・commitを投入前に終える。コーパステスト修正を後回しにするなら、**job 終端後**に行う。
3. staging と共有 gflags/glog の pin/clean、CCBench の pin/cleanを再確認。同じ wave の source・submodule・receipt・stagingを走行中に変更しない。
4. queue 状態、混雑、quota、残高を本文まで確認。scheduler 証拠領域と repo 出力先の書込み可能性・容量を親の実環境で確認する。
5. wave root を明示した既定 launcher、`--protocol silo --rratio 5` を使用。`--attempts-root` を変えない。J:208 は既定位置しか読まない。
6. 投入後は request 可視性を一度確認し、nonce／request／receiptを照合。launcher失敗時も、投入済みの可能性を解消するまで再投入しない。
7. compute 待ちを1本起動。約240秒は進捗評価の目安に留め、周期 qstat は追加しない。
8. 終端後、下記の証拠を照合してから取得記録を確定。成果物を収録し clean にして、親が受入検査・landを進める。

**無条件に「accepted を取得した」と書く最小の証拠集合：**

- 今回の submit receipt と acquisition receipt、その request／source／script／binary の束縛。
- registered の実 bytes と SHA、attempt の `calibration.json` との一致、対象が silo／rr5／t48／pegasus、`quality.status=accepted`、`cache_floor_warning=false`。
- 今回の `publish.json` と `published-self-comparison.json` の成功。
- `job-result.json` の `calibrate_rc=0` と request 固有の終端会計。
- failure／rejection／post-probe／cleanup 証拠の確認。矛盾があれば「accepted 公開物はあるが wrapper は失敗」と分離して記録する。

会計本文は終端を示すが、確認した先行形式には終了コードがない。会計だけで正常終了を補ってはいけない。

## 失効した前提

- **失効確認済み：** J の旧 SHA、launcher が従来と同じ cwd 動作という前提、親 P3 の実装差分不要という見込み。
- **維持確認済み：** policy、CCBench pin、共有 gflags/glog の現時点の pin/clean、wave の staging 実在、compute 待ち経路。
- **保証へ格上げ不可：** 先行184／177／238秒、空の qstat、旧却下系列からの accepted 予測、receipt や failure の単独ファイル存在。

## 総括

**silo／rr5を1本投入する方針は成立する。** ただし旧 SHA の訂正、終端と publish の分離、生成証拠の収録、既存コーパステスト問題の処理が必要。現物検査では依存欠落による即時停止は確認されなかったが、計算ノード側の条件と今回の accepted は未検証である。