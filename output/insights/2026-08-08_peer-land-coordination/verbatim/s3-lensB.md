[1] real | 対象: `brief.md:28`, `s2-plan.md:242`, `s2-plan.md:261` | must-fix — 主張: 現案は中心課題の 18 分窓を閉じない | 根拠: 減る事象列は「A land → B が受入開始前の次 tool round で通知受信 → B が main を取り込んでから受入」のみだが、その受信規則がない。減らない事象列は「A/B が同じ main を取込 → 両者が受入全走 → A land → 通知は B の走行中に滞留 → B 完走後に stale 判明 → 再取込・再走」で、現案の通常競争はこちらである | 影響: 本修正を実装しない場合、worklog の権威ある受入 request／実測参照は最初の走行から約 18 分後の再走へ変わる一方、certified 選択・レポート受理集合は変わらない | 推奨: land 後通知ではなく、受入投入直前の `land-intent` と受信側の main 再確認を scope の中心にする。

[2] real | 対象: `docs/decisions.md:5075`, `docs/dev-wave/operations.md:117`, `tools/check_wave_startup.py:319`, `s2-plan.md:279` | should-fix — 主張: S-B は「wave 開始時に表示される」機能を新設せず、手動 helper の出力を増やすだけである | 根拠: D109 は repo 内の自動 caller が 0 件と明記し、DW-O20 は人間・AI に手動実行を要求する。実行されれば INFO は見えるが、brief には実行ログ・artifact path・計測 IDがなく、開始時の一度限りの snapshot は後段の land 状態変化も追わない | 影響: 協調 manager が DW-O20 を守った場合だけの best-effort 可視化であり、衝突削減を保証できない | 推奨: S-B を診断補助へ格下げするか、実 wave の startup artifact と読後アクションを先に記録して `DW-G04` を満たす。

[3] real | 対象: `brief.md:12`, `s2-plan.md:71`, `s2-plan.md:73`, `s2-plan.md:109`, `docs/dev-wave/core.md:60` | must-fix — 主張: 実測済みなのは `SendMessage` 単体の生死だけで、handoff＋Git＋roster→候補→ListAgents→送信→受信の全経路は未発火である | 根拠: `dispatch.short` が recipient か未確認、ListAgents schema も未確認、曖昧 join は候補ゼロへ倒れ、`notify` 自身は送信しない。現行 12 session の topology から一意宛先が得られる証拠もない | 影響: 本修正を実装しない場合は通知数 0 のままになり、worklog の受入 request 参照が stale 走行から再走へ変わる経路を一切減らせない | 推奨: 現在の実 peer 2 本以上で一意照合・送信・受信・main 再確認までを先に smoke し、その artifact path を brief に固定する。失敗時は実装しない。

[4] real | 対象: `.claude/commands/dev-wave.md:21`, `.claude/commands/dev-wave.md:75`, `.claude/commands/dev-wave.md:111`, `s2-plan.md:303`, `s2-plan.md:321` | should-fix — 主張: 「終端」末尾の追記は死文と断定まではできないが、段 9 で必ず再読される位置ではない | 根拠: 段 9 の just-in-time dispatch は `DW-S09`・`DW-CTX`・`DW-STOP`・`DW-O23` だけを列挙し、案は意図的に dispatch 表外へ置いて閉包を不変にしている。command 起動時に一度読まれるだけで、実行検査もない | 影響: 長い wave や context 圧縮後には送信義務が抜けても検出されない | 推奨: 通知を段 6 の受入開始項と段 9 の状態遷移本文へ置くか、land 結果処理の単一 wrapper に結合する。

[5] real | 対象: `docs/dev-wave/workers.md:16`, `s2-plan.md:307`, `docs/archive/worklog-phase3-0804-154.md:3` | must-fix — 主張: 送る側だけで、受信側が「いつ、何を止め、何を再実行するか」の層が欠落している | 根拠: 追記案は「git 照合・検査省略禁止」までで、受入前・受入中・受入後の分岐がない。一方 T-389 の既裁定は「受入投入直前に main HEAD を再確認」と既に定めている | 影響: 本修正を実装しない場合、通知を受けても受入済み tip の受理可否は変わらず、worklog の権威ある受入参照は再走 request へ移る | 推奨: 受入前なら待機または main 取込後に一度だけ全走、受入中なら中断せず完走後に `DW-O23` 判定、受入後なら既存 stale 復帰、という receiver 契約を scope に入れる。予算上入らなければ裁定パッケージへ返す。

[6] refuted | 対象: `docs/decisions.md:6281`, `docs/decisions.md:6416`, `tools/dev_wave_land.py:1673`, `tools/dev_wave_land.py:1724` | nit — 主張: 「実 land 自体を新機構で直列化する必要がある」は反証される | 根拠: `dev_wave_land.py` は既に協調 lock 内で main を再照合し、D128 は同 lock 内 fold、D132 は正規 wave-side main merge の判定を持つ。実 mutation は直列化済みで、残る穴は lock 取得より前の受入全走である | 影響: land/fold の受理集合を変える理由はない | 推奨: 問題名と成功条件を「main-land の同時実行」ではなく「pre-land acceptance window の追い越し削減」へ狭め、`dev_wave_land.py` は現状維持する。

[7] refuted | 対象: `docs/handoff/README.md:7`, `docs/handoff/README.md:38`, `docs/handoff/README.md:40` | should-fix — 主張: 「段 2 案は handoff 宣言板の完全な再発明」は反証されるが、三者 join は過剰な延長である | 根拠: 既存宣言は監査対象と性能計測だけで、land-intent や受信動作を持たないため、それだけでは足りない。一方、各 session 一ファイル・節目更新・他 session の一瞥という必要な基盤は既にある | 影響: 新たな roster inventory を持たずとも協調点を作れる | 推奨: handoff 本文へ `- land-window: idle | acceptance(<main SHA>) | landed(<main SHA>)` の一行だけを足し、fresh ListAgents で人間的に照合する。

[8] real | 対象: `docs/worklog.md:1841`, `s2-plan.md:53`, `s2-plan.md:260`, `brief.md:68` | should-fix — 主張: 通知の時間収支と宛先絞りが未成立である | 根拠: 実測全走は 1055.40 秒。利益は受入前に届けば最大 1055.40 秒、受入中なら 0 秒である。三 wave の初回競争では成功者＋敗退者が各二 peer へ送れば最大 6 wake-up、retry を含む上限はない。走行中は次 tool round まで届かないので直接中断害は 0 だが、待機後の追加 turn の時間・token は未計測である | 影響: 現状では期待純益を正にできず、local な `rejected`・`lock-busy`・fold failure まで全 peer に撒く | 推奨: 受入前 `land-intent` と、実際に main が変わった `landed` だけに限定し、stale/lock-busy/local failure は送らない。

[9] real | 対象: `s2-plan.md:16`, `s2-plan.md:246`, `s2-plan.md:325`, `s2-plan.md:346` | should-fix — 主張: 約 610 行、専用 16 test＋startup 5 test、三データ源 join は得られる効果に比べて重すぎる | 根拠: 最終送信はなお手動 ListAgents 照合であり、600 行の結果も未検証候補に留まる。roster を外しても既存 handoff と ListAgents だけで同じ advisory を送れる | 影響: 保守対象・誤 join 面・schema drift 面だけを増やし、18 分窓への作用点は増えない | 推奨: S-A/S-B を落とし、handoff 一行宣言＋固定 `land-intent`／`landed` 文面＋receiver 契約だけにする。

[10] real | 対象: `s2-plan.md:113`, `s2-plan.md:121`, `s2-plan.md:129` | should-fix — 主張: Git ancestry だけでは active と landed を区別できず、peer 集合に偽陰性または偽陽性が出る | 根拠: 新規 wave の branch tip は最初の commit 前には main と `equal` だが active である。これを「main 合流済み」と除外すれば見落とし、除外しなければ land 後 branch と区別できない | 影響: startup 表示と recipient candidate 集合が lifecycle 解釈次第で変わる | 推奨: lifecycle は owner が書く handoff 宣言を正本にし、ancestry は main SHA の照合だけへ限定する。

[11] real | 対象: `docs/dev-wave/core.md:55`, `brief.md:10`, `brief.md:17`, `brief.md:25`, `docs/archive/worklog-phase3-0804-144.md:57` | should-fix — 主張: 「並行三 wave が同一 byte 予算を消費中」から恒常的な衝突族への一般化は `DW-G03` を満たさない | 根拠: brief が示すのは「生きた handoff 3 本」と「残り 4 byte」という同時 snapshot であり、三者が同じ bytes を変更した独立二事故ではない。T-389 は一つの consumer wave が同じ `/rulings` session に六回追い越された例、T-641 は byte 予算競合で、同型 producer/consumer 二例ではない | 影響: 広い peer inventory 制度の根拠にならず、局所緩和を越えた射程が未証明である | 推奨: 今回は T-389 の受入前調整へ限定し、別 producer/consumer の二例を観測してから一般化する。

[12] real | 対象: `brief.md:56`, `docs/worklog.md:3175`, `docs/dev-wave/core.md:65` | should-fix — 主張: brief の `DW-G05` 成果物影響は F157 を誤用している | 根拠: T-641 はユーザー裁定 (c) により「failures 記録だけで恒久対応なし」を受容して終端済みであり、本通知機構を実装しても F157 の恒久対応欄は埋まらない。変わりうるのは受入 request・所要時間の参照で、certified 選択・レポート受理集合ではない | 影響: 現在の成功判定では効かなかった機構も成果物改善として誤記録できる | 推奨: F157 を成果物影響から外し、「stale 再走件数・捨てた秒数・通知前後の main SHA」を効果指標にする。

## 総括

**NO-GO。** 現案は送信候補生成を厚くした一方、18 分窓より前の送信、受信側契約、実 caller の三点を欠く。  
推奨する最小案は `wave_peers.py` と startup integration を作らない。  
既存 handoff 本文へ land-window の一行宣言だけを置く。  
受入投入直前に fresh ListAgents から peer を照合し、固定 `land-intent(base_main_sha)` を一度送る。  
受信側は受入開始前だけ待機／main 再取込を行い、受入中は中断せず既存 `DW-O23` へ戻す。  
land 後は main が実際に変わった成功時だけ固定 `landed(main_sha)` を送る。  
この最小形を独立二 wave pair で発火・再走削減まで実測してから、roster や自動 join を再検討する。