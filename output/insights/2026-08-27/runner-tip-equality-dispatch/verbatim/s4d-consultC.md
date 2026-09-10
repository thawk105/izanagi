## 仮説 H の判定

### H1

**条件付きで成立する。ただし提示された3条件だけでは、まだ「弱点が消える」とは言えない。**

成立に必要なのは次の追加条件である。

- launcher が、子の起動前に main 側で `{session nonce, shard_count, tested_main, expected runner SHA-256}` を確定すること。
- 各 shard の digest が、expected digest の転記ではなく、**実際に stdin bootstrap へ渡した同一 bytes**から計算されること。
- launcher が検査を outcome 発行より前に行うこと。現行は子終了後、outcome を書くのが `tools/acceptance_launcher.py:425-461` なので、検査の挿入点は `:451-461` の間に置ける。
- shard を使わない pathname 再実行を P から R まで fail-closed にすること。

現在の compute 子では、pathname の `tools/run_tests.py` を起動する処理と、結果を書き出す処理が分離している。`tools/pegasus/dispatch_compute.py:1010-1022` が起動、`:1030-1044` が `result.json` 発行である。ここへ単に expected digest を追加すると、pathname 起動へ戻す変異をしても main digest を書き続けられるため恒真になる。**一度だけ読んだ source bytesを hash し、その同じ bytesを subprocess stdinへ渡す結合**が必要である。

また、bounded local は作業ツリーの runner pathname を再起動する。`tools/run_tests.py:1895-1906`。queue や headroom による分岐は `tools/run_tests.py:2496-2586` にあり、H の「各 compute shard」だけではこの経路を覆わない。PからRの間は launcher が明示 shard を要求し、attestation が無い bounded 経路を拒否する必要がある。

同一 UID による attestation 偽造までは防げないが、それは D387 が明示的に防御範囲外としている。`docs/decisions.md:16451-16468`。したがって H が成立する範囲は、**独立して起きる実装事故・退行**であり、暗号的な実行証明ではない。

結論として、H は「main 所有 manifest + same-buffer execution + bounded 経路の拒否」を含めれば成立する。単なる digest file の追加では成立しない。

### H2

作業ツリー外に、既に利用可能な受け渡し経路がある。

1. shard 共用 root は Git common dir の親にある `.izanagi-acceptance-shards` で、repo 内・land control container 内を明示的に拒否する。`tools/acceptance_shards.py:177-199`
2. session と `shard-0` から `shard-(K-1)` は外部 root に生成される。`tools/acceptance_shards.py:970-989`
3. 外側 runner は session root と K をログへ出す。`tools/acceptance_shards.py:1189-1197`
4. 各 shard の `artifact_root` は `session/shard-i/dispatch`、nonce は `shard-i` である。`tools/acceptance_shards.py:1243-1251`
5. dispatcher は split mode の `artifact_root` が repo 外であることを要求する。`tools/pegasus/dispatch_compute.py:2716-2733`
6. 実 submission dir は `artifact_root/shard-i` となる。`tools/pegasus/dispatch_compute.py:2833-2838`
7. compute 側はそこへ `result.json` を create-only で書く。`tools/pegasus/dispatch_compute.py:934-1044`
8. login 側 dispatcher は `result.json`、stdout、stderr、compute marker、会計を全て収集する。`tools/pegasus/dispatch_compute.py:3346-3384`
9. job ID、stage、request SHA を照合してから receipt を `submission_dir/receipt.json`、失敗時は artifact root の fallback へ保存する。`tools/pegasus/dispatch_compute.py:2651-2666`、`:3447-3493`
10. shard plugin 自身も `session/shard-i/report.json` と JUnit を書き、親は K 本を併合する。`tools/acceptance_shards.py:936-960`、`:1368-1394`

したがって attestation は、例えば

`session/shard-i/dispatch/shard-i/result.json`

の新しい厳格 field、または同 directory の create-only 専用 file として運べる。作業ツリーの fingerprint には触れない。作業ツリー側の `status_bytes == 0` 要求は `tools/dev_wave_land.py:805-817`、待ち手の走行前後 clean 検査は `tools/dev_wave_wait.py:3742-3760`、`:3821-3842` にある。

現状、dispatcher worker から shard 親へ返る値は `index/rc/child_started` だけである。`tools/acceptance_shards.py:1000-1032`。launcher receipt にも外側 runner の digestしかない。`tools/acceptance_launcher.py:347-397`。したがって **外部 artifact 経路は実在するが、launcher への attestation 収集は未実装**である。

### H3

実測された明示 K=3 経路では、launcher は K を知りうる。

待ち手は queue 可用時に `IZANAGI_ACCEPTANCE_SHARDS=3` を launcher 環境へ入れる。`tools/dev_wave_wait.py:821-845`。launcher から runner への subprocess は `env=` を指定しないため継承される。`tools/acceptance_launcher.py:213-227`。runner はこの値を 1、2、3 の閉集合で解釈する。`tools/run_tests.py:253-298`

一方、env が無い場合の既定 K=2 は runner 内部で決まり、bounded scope へ再入すると実効 K=1になる。`tools/run_tests.py:282-297`、`:2496-2586`。この場合、launcher は現行入力だけから実効 shard 数を独立には決められない。tip 側の `ARTIFACT_PREFIX` だけから K を学ぶ案では、marker 自体の欠落と「正規の非 shard 走」を区別できない。

従って P では launcher を manifest の所有者にすべきである。launcher が K と session nonce を先に決めて環境へ渡し、`0..K-1` の exact set を要求する。Kを決められない場合や dispatch しなかった場合は、Rまで受入を fail-closed にする。この形なら欠落検出は成立する。

### H4

P 自身の通常受入では新検査は発火しない。待ち手は main に launcher があれば tested main の blob を選ぶためである。`tools/dev_wave_wait.py:2558-2579`。したがって P の receipt を「新 attestation gate が実走した証拠」として扱ってはいけない。

ただし D1114 にいう production 呼び手は名指しできる。P land 後の次の受入では、`tools/dev_wave_wait.py:3783-3817` が P の main launcher を起動する。よって gate 自体は死んでいないが、次の controls を P の land 条件にすべきである。

- P の受入で、`orchestrator/tests/test_acceptance_launcher.py` に missing shard と wrong digest の negative control を置き、production と同じ `_launch` を直接発火させる。既存テストも `_launch` を直接通している。`orchestrator/tests/test_acceptance_launcher.py:90-130`
- pathname runner を故意に divergent にした fixture で、same-buffer bootstrap を殺す mutation control を置く。digest の形式検査だけでは不可。
- Q の実受入を最初の production activation control とする。Q receipt の `launcher_executed_sha256` が P の main launcher blob と一致し、receipt が発行されたことを確認する。land は launcher blob と実行 digestを照合する。`tools/dev_wave_land.py:1021-1053`
- 新検査は outcome 発行より前に置く。そうすれば Q receipt の成立自体が「全 attestation 検査を通過した」証拠になる。`tools/acceptance_launcher.py:451-475`

producer だけ、または validator helper だけを先行 land するなら D1114 に抵触する。`docs/decisions.md:37608-37629`

## 問い 1 への回答

**P は着手すべき。** ただし、従来案のままではなく H の条件を含む P とし、条件を実装できなければ land せず設計へ戻すべきである。

- 恒真化を防ぐ核心は、expected digest の転記ではなく、同じ source buffer の hash と実行を不可分にすること。
- main launcher が exact K と session root を所有しなければ、「証拠不在」の意味が確定しない。
- Pの transport、request schema、stdin bootstrap、create-only artifact、negative controls はRでも再利用できる。Rでは主に外側 dispatcher import と bounded再入の権威を main側へ移すため、全作り直しにはならない。これは設計上の推測である。
- Hが成立しなければ、Pの価値は「runnerだけを編集した wave」の検出へ縮む。その場合「main blob固定を維持した」とは記録できない。

Git履歴による母集団の参考値は、dispatcher 導入日の2026-07-30以降、runnerを触った25 commit、dispatcherを触った26 commit、その両方を触ったcommitが6件だった。両方の6件は `a34266d2`、`fee55899`、`d26b345c`、`16df3e4e`、`9e81501f`、`532635b4`。これは file:line を持たない Git 履歴実測であり、commit数をwave数の近似にした値である。runner変更の約24%が同時変更で、無視できるほど小さくはない。一方、D838以降のrunner変更は0件である。`docs/archive/worklog-phase3-0827-1013.md:32-35`

## 問い 2 への回答

**Q-early を選ぶ。** ただし P の negative control と、Q 自身による production activation control が通った後に限る。Hが上記条件を満たさないならQへ進んではならない。

Q-late は現行機構では実行不能である。receipt は必須引数で、検証は全ての `already-landed` と merge より前に走る。`tools/dev_wave_land.py:5034-5042`、`:5492-5508`、`:5558-5559`。D388 は flag、環境変数、互換 bypass を逐語的に禁止している。`docs/decisions.md:16470-16494`。手動 FF は receipt だけでなく provenance、collision、fold、postconditionもまとめて迂回するため、Q-early の限定残余より侵害面が広い。

Q-early の残余母集団は、Hが正しく実装されれば「同一 UID が意図的に偽造する wave」まで縮み、これはD387の防御範囲外である。Hが不完全なら、歴史上6件あった runner+dispatcher同時変更がそのまま穴になるため許容できない。

なお acceptance lease は他 wave の投入を止める用途に使ってはならない。`docs/decisions.md:27307-27317`。従って「QとRを続けて行うから対象はRの1本だけ」は機械的保証ではない。運用上はQとRを連続させ、間のenv無し・bounded・attestation無し走行をmain launcherで全拒否する必要がある。

## 総括

P: 着手すべき  
Q: early  
Hはmain所有manifest、exact K、same-buffer実行、欠落時fail-closedを揃えれば事故モデル内で成立する。  
P自身の受入では新launcherが動かないため、negative testとQの実受入をactivation controlにする。  
Q-lateはD388の明示禁止を破り、landの複数権威をまとめて迂回する。  
Hを完全に実装できない場合はPをlandせず、Qにも進まない。