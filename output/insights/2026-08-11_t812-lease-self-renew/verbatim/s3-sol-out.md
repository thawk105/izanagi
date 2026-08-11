- **A-01 / BLOCKER — `holder` は invocation ではなく slug の識別子であり、`held-self` は同時実行を許可する**

  - **根拠:** holder は wave slug の SHA-256 を12桁へ切っただけである（[wave_land_window.py:101–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:101)）。現行は自己一致でも `held` を返し（[wave_land_window.py:719–725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:719)）、待ち手は `acquired` だけを受理する（[dev_wave_wait.py:607–628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:607)）。計画は `{acquired, held-self}` を受理する（[s2-plan.md:64–72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:64)）一方、この危険を前提条件へ落としている（[s2-plan.md:269–273](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:269)）。
  - **失敗系列:** 同一 slug の invocation A/B が lease 無しから同時 claim。A が `acquired`。A の claim subprocess が fd を閉じた直後、B は同じ digest を見て `held-self`。flock は claim 間だけを直列化し、受入 command 中は保持されないため、A/B 双方が受入へ進む。現行ならBは `held`で待ち、直ちには進まない。
  - **成果物影響:** 受理集合が「claim 勝者1本」から「同一 slug の全 invocation」へ拡大する。異なる tip/main に対する受入が並行し、少なくとも一方の rc=0 は land 時 main に対する直列化証明にならない。certified 選択・land・台帳へ不正な受理結果が入る。
  - **修正案:** **現 scope 外だが拡張必須。** lease holder を `(wave, invocation_id, ownership capability)` にし、能力を提示した継続 invocation だけを `held-self` にする。さらに同じ capability の重複 waiter を止める active-invocation guard が必要。「1 slug 1 invocation」は機械保証でなく、排他機構の前提にはできない。

- **A-02 / BLOCKER — P2 の「別 invocation を release しない」は UNKNOWN 窓で破れる**

  - **根拠:** 計画は claim 前を `UNKNOWN` とし、`UNKNOWN` に release 権限を残す（[s2-plan.md:80–94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:80)）。現行も subprocess 前に `UNKNOWN` を設定し、JSON parse 後にだけ確定する（[dev_wave_wait.py:577–604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:577)）。cleanup は `UNKNOWN` を `ACQUIRED` と同様に release し（[dev_wave_wait.py:758–780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:758)）、release の権限証明も slug digest だけである（[wave_land_window.py:747–779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:747)）。
  - **失敗系列:** A が受入中。B は同一 slug で claim。helper がAの leaseを更新した後、JSON出力前の signal・timeout・stdout異常で結果が不明になる。Bの lifecycle は `UNKNOWN` のまま cleanup へ入り、Aの leaseを owner と誤認して unlink。C が取得し、Aと並行受入になる。
  - **成果物影響:** Aの受入は走行中なのに lease が消え、Cも `acquired` として受理される。受入集合・land候補・台帳が同時実行を含む。
  - **修正案:** **現 scope 外・A-01と同時解決必須。** claim attempt が事前生成した capability を lease に束縛し、UNKNOWN cleanup の release もその capability 一致を要求する。単に UNKNOWN release を止める案は、真に取得済みだった場合の長時間リークへ問題を移すだけである。

- **A-03 / BLOCKER — lock 前の mtime snapshot により、更新直後の lease を stale claimant が削除できる**

  - **根拠:** `_open_lease()` は `fstat` を flock **前**に行い、その metadata を flock 後も更新せず stale 判定へ使う（[wave_land_window.py:300–322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:300)）。stale 側は inode 一致だけを見て unlink する（[wave_land_window.py:726–737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:726)）。計画の post-renew `_same_entry` は更新側しか検査しない（[s2-plan.md:43–51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:43)）。
  - **失敗系列:** TTL境界直前に自己更新者Aが `fstat` して fresh と記録されたところで停止。境界直後に外部wave Bが同じ inode を `fstat` して stale と記録。Aが先にEX lockを取り、mtimeを更新して `held-self`。続いてBがlockを取り、古い metadata により stale と判断する。renewalはinodeを変えないため `_same_entry` は真となり、Bが更新済みleaseをunlinkして取得する。
  - **成果物影響:** Aは`held-self`、Bは`acquired`として双方が受入へ進む。lease更新成功という報告と実際の排他が食い違い、受理集合が二重化する。
  - **修正案:** **scope 内。** flock取得後に必ず再 `fstat` し、その metadata から age/stale を再計算する。stale unlink直前にも、lock下の最新metadataを用いる。TTL境界で二claimを止めるbarrier testを追加する。

- **A-04 / HIGH — renewal成功判定がsyntheticで、clock skew・粒度・部分成功を見抜けない**

  - **根拠:** stale判定はwall clockとmtimeの差である（[wave_land_window.py:218–226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:218)）。計画はclientの `time.time_ns()` を明示値として設定し、post-`fstat`ではowner・inodeだけを検査して、観測mtimeを再評価せず `age_seconds=0` を上書きする（[s2-plan.md:43–58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:43)）。安全性ではなく公平性用のticket heartbeatを前例にしている（[wave_land_window.py:509–530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:509)）。
  - **失敗系列:** clockが遅いnodeで更新するとmtimeが後退し、他nodeから見たTTL残量が数秒まで縮むが、返答は常に age=0。逆に速いnodeならTTLが最大でほぼ倍へ延びる。粗いmtime、属性可視性遅延、または `utime` 成功後の `fstat/_same_entry` 失敗では、実際には更新済みなのに `self-renew-failed` となり、P2によりleaseを保持したまま止まる。O_RDONLY fdへのutimeが未対応・read-only・権限拒否なら開始はfail-closedだが、可用性は失う。
  - **成果物影響:** mtime後退では受入中に別waveがstale回収し二重受理、未来mtimeや部分成功では待ち手が最大TTL分余計に止まり、land・台帳追加が遅延する。
  - **修正案:** **scope 内。** filesystem-authoritativeな「現在時刻」を使える方式を選び、post-`fstat`の実mtimeからfreshnessを再計算する。mtime後退・非更新・staleを成功扱いせず、syntheticな0を証拠にしない。実配置はread-only確認上Lustreなので、private probeから共有Lustreのvisibility/utime semanticsを一般化せず実FS契約を検証する。

- **A-05 / BLOCKER — 一度のrenewalではunbounded受入を守れず、排他喪失後もrc=0になる**

  - **根拠:** lease TTLは2400秒（[dev_wave_wait.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:38)）。claim後にmerge等を行ってから、受入commandを明示的に無期限実行する（[dev_wave_wait.py:811–877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:811)）。終了時は経過がTTL超過でも `ttl_remaining=0` と印字するだけで `RC_OK` にする（[dev_wave_wait.py:880–895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:880)）。runbook自身もfencing無しを既知限界とする（[pegasus-runbook.md:875–880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/docs/pegasus-runbook.md:875)）。
  - **失敗系列:** held-self更新後、postclaim処理と受入が計2401秒を超える。Bがstale回収して受入開始。Aはその後成功し、TTL残0でもrc=0を返す。
  - **成果物影響:** 「排他を保持して完走した」という受理集合に、実際にはBと重なったAが入る。A/Bいずれかのland・台帳記録は直列検査済みという意味を持たない。
  - **修正案:** **完全修正は現 scope 外。** invocationに束縛したheartbeat/fencingと、renewal喪失時に結果を受理しない仕組みが必要。単なる終了時警告や事後failでは、すでに発生した並行受入を取り消せない。

- **A-06 / HIGH — self-renewは既存の外国待ち札を追い越し、無期限starvationを作れる**

  - **根拠:** queue headを見るのはleaseが無い場合だけ（[wave_land_window.py:667–710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:667)）。leaseがfreshならticket登録後にqueueを見ず自己分岐へ入る（[wave_land_window.py:712–725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:712)）。runbookは後着が先着を追い越さないことをFIFO契約としている（[pegasus-runbook.md:849–855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/docs/pegasus-runbook.md:849)）。
  - **失敗系列:** Xが1走目を成功してleaseを保持。Yが先に待ち札を作る。その後Xが2走目をclaimし、Yを見ずrenewして`held-self`。Xが2400秒以内にclaimを繰り返せばYは永遠にstale回収できず、7200秒で`claim-timeout`になる。queuedから取得したXでも、1走目後の自己再入で後続Yを同様に追い越す。
  - **成果物影響:** Yの受入が投入されず、そのtipのland・certified選択・台帳追加が欠落または任意時間遅延する。これはbriefの「公平性を退行させない」（[brief.md:45–49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/brief.md:45)）と両立しない。
  - **修正案:** **機構はscope内、政策は段4裁定。** foreign queue headがある場合のrenew可否と、累積保持時間・連続renew回数の上限を定義する。無条件owner優先を採るならFIFO保証を撤回し、starvationを既知限界ではなく明示的意味論として裁定する必要がある。

- **A-07 / HIGH — P1はstale inodeの復活を防ぐだけで、旧受入の停止を証明しない**

  - **根拠:** P1はstale自己保持をunlink後の`acquired`へ流す（[brief.md:52–56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/brief.md:52)）。実装はstale leaseをunlinkして再試行する（[wave_land_window.py:726–742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:726)）。旧holderを止めるfencingは無い（[pegasus-runbook.md:878–880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/docs/pegasus-runbook.md:878)）。
  - **失敗系列:** Aの受入commandがTTLを超えてまだ走っている。A自身または別invocationがstale leaseを回収し、新inodeで`acquired`となって次の受入を始める。新inode取得は旧command停止の証拠ではない。共有dirに先行ticketがあれば、再試行は`acquired`でなく`queued`にもなり得るため、段2表の「stale self→acquired」も一般則ではない。
  - **他waveが先に奪った場合:** 通常の異なるdigestなら、その後のA claimはforeign `held`となりmtimeを更新しない。この部分は安全である。ただし同一slug invocationまたは12桁digest衝突ならA-01の偽自己判定となり、他者のleaseを更新して進む。
  - **成果物影響:** stale回収者と旧holderの双方が受理され、land/台帳の直列化根拠が消える。
  - **修正案:** **stale-selfのfail-closed化はscope内、完全解決はscope外。** 旧invocation停止またはfencingを証明できない限り、stale-selfを`acquired`成功へ写さず `lost-exclusivity` として止める。

- **A-08 / HIGH — F-5の「ticket残骸0」は共有queueへ一般化できず、best-effort dropにも公平性穴がある**

  - **根拠:** private probeのF-5はticket 0枚だけを観測した（[brief.md:20–28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/brief.md:20)）。自己分岐は `_drop_ticket_best_effort()` の成否を無視する（[wave_land_window.py:719–725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:719)）。dropはflockを取らず、inode照合とunlinkの間にも窓がある（[wave_land_window.py:469–506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:469)）。
  - **失敗系列:** self ticketのdropが失敗してもrenewは成功扱いになる。その後holderがleaseを解放すると、残ったself ticketが最大300秒queue headとなり、終了済みwaveの後ろで他waveが待つ。繰返しclaimはticket heartbeatとlease renewの双方を続け、残骸を無期限化できる。
  - **他wave ticketの削除:** 正常な異なるdigestのticketは別名なので、直接削除する経路は読んだコード上ない。ただしholderは48-bit相当の12桁だけで（[wave_land_window.py:39–40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:39)）、同一slug・digest衝突では同じticket名を共有する。さらに `_same_entry` 後に同名ticketが再作成されると、遅れて行うunlinkがreplacementを消せる。
  - **成果物影響:** FIFO順が変わり、他waveの受入・land・台帳追加が最大300秒または反復中は無期限に遅れる。
  - **修正案:** **drop失敗処理と共有queue testはscope内。** held-self前にticket削除を確認し、失敗を成功扱いしない。invocation別ticket名と安全なcompare-and-deleteはscope拡張としてA-01と一体で裁定する。

- **A-09 / HIGH — 段2のテスト・変異matrixは上記の排他破れを検出しない**

  - **根拠:** primitiveテストは逐次self claim、単独renew失敗、post-check、単一flockだけである（[s2-plan.md:143–175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:143)）。deadlock再現も「事前claim→同じwaiter」の逐次系列である（[s2-plan.md:212–216](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:212)）。M01–M08にも同一slug並行、TTL境界snapshot、clock後退、foreign ticket、TTL越えcommandが無い（[s2-plan.md:218–229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t812-lease-self-renew/s2-plan.md:218)）。
  - **失敗系列:** A-01/A-03/A-06を含む実装でも、予定された全テストと全変異を通せる。特に「renew中はEX flock」というテストは、flock解放後に二waiterが同時受入へ進む欠陥を検出しない。
  - **成果物影響:** mutation/acceptance成果物が緑でも、排他契約は偽のままland可能になる。
  - **修正案:** **scope内。** 同一slug二waiterのbarrier試験、pre-lock stale snapshot競争、foreign head付きself-renew、clock後退・部分成功、commandがTTLを跨ぐ試験を事前登録する。

pytestは実行しておらず、緑は主張しない。

## 総括

- 最危険はA-01/A-02: slug digestだけでは`held-self`もrelease権限もinvocationを識別できない。
- 次はA-03: lock前snapshotにより、成功したrenewalを直後にstale回収できる。
- 第三はA-05/A-07: fencing無しのunbounded commandでは、TTL後もrc=0受理される。
- 段4の第一択一は「単一invocationを運用前提にする」対「capability＋active guardを機械化する」—後者が必要。
- 第二択一は「ownerの無期限優先」対「queue-awareな有界renewal」—FIFOを維持するなら後者。