追加の `qsub`・scheduler 問合せ・テストは行わず、指定ログ、保存 bytes、NQSV R1.16 のローカル man page を静的に照合した。

### 1. **BLOCKER / real** — `qattach` が P2 の攻撃をさらに強くする

probe 2 の完全な `qstat -f` は `qattach command = Enable` を示す（[qstat_f.out](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out2/qstat_f.out:40)）。NQSV の `qattach(1-N)` は、request owner が RUN 中の request 内で任意 command を実行できる仕様である。

同一 uid の攻撃者は真正 floor request へ `qattach -c` し、wrapper を経ず private core を起動できる。この process では qcat bytes、qstat の ID・RUN・host・User Attributes、さらには cgroup/PID 所属まで真正になり得る。したがって単なる `qcat -p`、PID、cgroup の追加照合でも wrapper lineage は閉じない。長い wrapper prologue 中に claim を先取する競争も残る。

最小実測:

1. 人間認可した捨て request へ `qattach -c` し、PID/PPID/cgroup/PBS 環境を採取する。
2. attached process から `qcat -p/-i` と `qstat -f` を取得し、wrapper 非子孫でも一致するか確認する。
3. official core は呼ばず、admission 入力が揃うところまでで停止する。

### 2. **BLOCKER / real** — P1 は「取得 primitive」と「証拠経路」を混同している

`qcat` が証明するのは「caller が指定した live request の input」である。実際、probe 1 は同一 owner の別 request も読めている（[probe.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:48)）。probe 2 で qstat の state・host・属性まで読めるようになったが、すべて同じ caller-selected ID から導出される。

したがって P1 は「scheduler spool 取得 primitive は実現可能」までなら成立するが、「D86 §4 を満たす証拠経路」と呼ぶのは過大である。process→request、request→wrapper lineage、ユーザー認可の三辺が欠けたままである。

### 3. **BLOCKER / real** — User Attributes は revision authority ではない

probe 2 は属性の保存・job 内取得を実証した（[probe2.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out2/probe2.log:57)）。しかし値を選ぶのは submitter 自身であり、AI も同じ `-U` を設定できる。`qalter -U` が無いことは、標準 owner CLI による事後変更耐性を示すだけで、投入時の値に権威を与えない。

D86(8) は submission artifact を認可証明にしてはならないと明記する（[decisions.md](/work/1/SFC/tanab/izanagi/docs/decisions.md:3797)）。scheduler record だから「Git receipt ではない」という P3 の字義論は、D86(8) と D87(5) の実質を回避できない。属性はユーザー署名・既存 allowlist 等の外部 authorityを運ぶ器にはなれるが、authority の発生源にはなれない。

### 4. **BLOCKER / real** — live admission が下流 proof chain から消える

request 消滅後に qcat/qstat を再取得できず、計画は spool hash・source commit・request ID を certificate/journalへ残さない（[stage2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/stage2-plan.md:150)）。A-5 は probe 2 でも全く変わらない。

同一 Python 権限内の monkeypatch/private-core 攻撃まで threat model に含める以上、「その場で gate が通った」という自己申告だけでは downstream が偽 certificate を区別できない。P1 を official feasibility へ昇格させるには、D86(4)/(5) を覆す proof-chain 拡張が別途必要である。

### 5. **MUST / real** — 「常に投入 bytes + `\n` 1個」は未成立

probe 2 により例は実際には3件（2077→2078、2031→2032、357→358）となり、末尾改行あり・なし双方を含む点は強化された。しかし全例が小さい text shell script、同一 site/version、file/pipe への非 TTY 出力である。

NQSV の `qcat(1-N)` は `-n` をbyte数ではなく「行数」と定義する。長大 script、極端に長い1行、出力内部上限、NUL/不正 encoding、locale 差は未測定である。binary は有効 job script の契約外なら除外してよいが、その domain 制限を主張へ書く必要がある。production が pipe 固定なら TTY 差は対象外にできる。

最小実測:

1. 実 wrapperに加え、100000行超・巨大1行・末尾改行あり/なしの有効 script を用意する。
2. `LC_ALL=C` と site locale で pipe captureし、投入 bytesとの exact diffを取る。
3. NUL等は qsub が受理する場合だけ測り、拒否なら「valid text script限定」と記録する。

### 6. **MUST / real** — 状態一般化と「run中しか取れない」が矛盾する

HLD の反例は rc=0 が成功判定にならないことを証明するが、NQSV には ARI/HOL/MIG/POR/SUS/TRS/WAT/STG/EXT 等もある。これらで空・部分・古い内容を返さないとは言えない。

一方、親自身が QUE/PRR で全 bytes を観測しているため、P1 の「run 中にしか取れない」は誤りで、「request が保持され、取得可能な状態にある間」が正しい。計画の exact equality は通常の空・部分出力を fail-closed にするが、qstat→qcat 間の状態遷移と切詰め衝突は残る。RUN を qcat 前後で挟んで確認すべきである。

最小実測:

1. HLD→QUE→PRR→RUN→POR/EXT を短い request で追跡する。
2. 各 qcat を前後2回の qstatで挟み、rc・長さ・hash・状態を同時記録する。
3. 観測できない状態は production で明示拒否する。

### 7. **SHOULD / real** — M4 は「再取得が保証されない」まで

1件の ENOREQ は、事後監査を qcat の保持に依存できないことを証明するには十分である。しかし、すべての正常終了・異常終了・POR/EXT・管理者 archive で即時取得不能になるという普遍則までは示さない。

記録は「少なくとも1 requestで消滅後取得不能、従って永続性保証なし」と狭めるべきである。

### 8. **MUST / real** — JSV path の差替え推論は妥当だが、まだ条件付きである

所有者書込み可能・sticky bitなしの directory では、通常のPOSIX意味論上、file owner/modeに関係なく directory entry を unlink/renameできる。touch→rm は directory の作成・削除権限と非 read-only mount を実証した（[probe2.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out2/probe2.log:23)）。

ただし root-owned `user_script` 自体の unlink は未実測であり、immutable flag、NFSv4 ACL、LSM、名前/inode別ポリシー等は反例になり得る。bash が既に開いた FD は旧 inode の実行を継続させるだけで、path の完全性を守らない。むしろ `$0` の再openが差替え後 bytesを読むTOCTOUになる。

推論どおり差替え可能なら、JSV直読は証拠に使えず診断 observation にしかならない。

最小実測:

1. 人間認可した捨て request が即座に外部 bodyへexecした後、mount/ACL/LSM/immutable情報を採る。
2. `user_script` を退避renameし、別 inodeを同名作成してrc・inode・hashを記録する。
3. open済みFDとpathのhash差を確認し、request終了までに可能なら復元する。

### 9. **BLOCKER / real** — I2「owner側に改竄手段なし」は過大

| 面 | 同一 uid 攻撃者が操作できるもの |
|---|---|
| `PBS_JOBID` | exec時の環境値。別のlive requestを指定可能 |
| `qcat` / `qstat` | probeはPATH解決。計画の絶対pathはPATH偽装だけを閉じる |
| `$0` | caller/execが選択。probe 2自身もexternal bodyへのexec後に別pathとなる |
| User Attributes | server保存値は比較的安定でも、初期値はsubmitterが選ぶ |
| client観測 | `LD_PRELOAD`、locale、`NQSV_PRIV`、同一Python内monkeypatch/runner差替えが残る |

server record自体を `qalter` で変えられないことと、admission processが正しく観測したことは別問題である。絶対path、clean env、出力上限、timeoutは必要だが、任意exec・同一Python monkeypatchまで敵とするなら privilege-separated helper が要る。

### 10. **SHOULD / refuted** — 「qcat は何も閉じない」という攻撃は不成立

NQSVの `qsub(1-N)` は script を即時spoolし、その後の元file変更に影響されないと明記する。実測も qcat、JSV copy、元bytesの一致を支持する。したがって qcat は、元の `9<"$0"` にあった「callerが選んだpathを自分で読むだけ」という恒真化を、request→spooled bytes の辺については実際に閉じる。

probe 2 も「計算ノードではqstat不可」という仮説を明確に refute した。捨てるべきなのは primitive ではなく、それをlineage/authorizationまで一般化する部分である。

### 11. **SHOULD / real** — 「A-1を閉じる設計は無い」までは言えない

現行 `gen_S`、同一uid・同一node・任意exec・qattach有効という能力なら、案A単独で閉じないという親の結論は正しい。

しかし、queue-level `qattach=disable`、schedulerが署名/保護するPID→request対応、root保護された spool、privilege-separated launcher、ユーザー署名revision、proof-chain永続化を組み合わせれば設計余地はある。`qcat -p` や cgroup はその候補だが、現在のqattach有効状態ではrequest所属しか証明せずwrapper lineageを証明しない。従って「現scopeでは閉じない」は妥当、「一般に閉じる設計なし」は未証明である。

### 12. **NIT / real** — M1 は server version まで実測していない

`qstat -V` 等が示すのは NQSV CUI/API R1.16 であり、batch server実装のversion一致までは直接証明しない。`/etc/pbs.conf` 不在もPBS互換surfaceの不存在を意味しない。記録は「Pegasusで観測したNQSV CUI/APIはR1.16」と狭めるべきである。

### 13. **MUST / real** — F49手続きの充足は保存証拠から完結しない

F49例外は、compute marker、投入直後の親側qstat可視性、終了後会計痕跡の3点を各投入で要求する（[pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/pegasus-runbook.md:961)）。

保存物には compute marker と `.e/.o` があるが、「投入直後」の親側qstat確認とポイント差分は提示されていない。job内qstatは実走後の自己確認で、時点要件を代替しない。また測定台帳の901501はHLD後に実際にRUNしている（[izt781held.e901501](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/izt781held.e901501:3)）。従って「計算ノードprobe 2本」以外に、少なくとも第三の実行requestも監査対象である。

さらに `-U` は sanctioned submit scriptに無い新しいqsub surfaceであり、runbookの「投入interfaceを発明しない」との例外関係を明示裁定していない。並走ガードも「非性能probeだから歪まない」では満たせず、計算ノード上の単独性・静穏preflightそのものが必要である（[restart runbook](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/phase3-8b-restart-runbook.md:19)）。

### 14. **SHOULD / refuted** — 「AIがqsubした時点で全probe無効」は広すぎる

D86/D87の「AIはqsubしない」は、official floorの人間認可と段階1 closureの文脈にある。後発のF49裁定は、永続セッション型からの診断・開発投入を3点検査付きで許可している。従ってAI qsubという一点だけでbyte観測を無効化する攻撃は成立しない。

ただし、そのAI投入で作ったUser Attributeを「人間が選んだrevision」の証明へ昇格することは、D86(8)/D87(5)により明確に禁止される。

## 総括

- **NO-GO** — P1/P3を根拠にofficialを非空化することはできない。
- 最大の攻撃点は、`qattach=Enable` により真正request内へwrapper非経由commandをownerが投入できる点。
- probe 2 はqstat/属性の取得可能性を確定したが、lineage・人間認可・proof-chainは一切閉じない。
- qcat primitive自体は有用なので、「指定requestのspool取得可能」という限定事実としてのみ採用できる。