### 所見 1 — P2 を採ると承認付き実 job は driver 前で全拒否される

**主張:** plan の 3 ファイルだけを変更する P2 は実行不能である。追加した receipt key を、先行する static admission が未知 key として拒否する。

**一次証拠 (file:line):** [s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:30) は optional field を追加する。一方、job は [floor_campaign.sh:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:54) から [同:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:95) で、後段 validator より先に static admission を実行する。その helper は [certified_writer_preflight.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_preflight.py:160) で admission を import し、[同:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_preflight.py:172) で呼ぶ。consumer は [certified_writer_admission.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_admission.py:27) の固定 `_FLOOR_KEYS` と [同:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_admission.py:52) の完全一致を要求する。

**成立条件:** `pegasus-floor-submit-receipt/v1` に `confirm_irreversible_pilot_holdout` が存在し、`certified_writer_admission.py` を現状のままにする。

**成果物への影響:** static admission が rc=3 で終了し、plan の env/receipt 一致検査にも driver にも到達しない。plan の fragment test はこの先行 admission を切り落としているため検出できない。

**推奨:** P2 を採らない。採る裁定なら `certified_writer_admission.py`、fixture、`test_campaign.py`、schema version 方針まで scope を広げ、実 helper を通す confirmed-path test を必須にする。

### 所見 2 — gate が証明するのは人間承認ではなく argv token の存在だけである

**主張:** AI、cron、背景 automation が承認引数を書いても、人間が書いた場合と完全に同じ成果物になる。plan は主体を検査しない。

**一次証拠 (file:line):** [s2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:7) は zero-arity flag の受理だけを定める。`submit_floor.sh` は [admission_registry.json:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/admission_registry.json:184) で `local-ok` であり、guard は [guard_bash.py:1200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/hooks/guard_bash.py:1200) から target の class だけを見て [同:1229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/hooks/guard_bash.py:1229) で許可する。floor 固有正本も [tools/pegasus/README.md:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/README.md:226) で receipt は人間性を証明しないと明記する。D356 も [docs/decisions.md:15565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/decisions.md:15565) と [同:15589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/decisions.md:15589) で、同じ AI が receipt まで作れるため trust root にならないと確定している。

**成立条件:** 非人間 process が `submit_floor.sh --confirm-irreversible-pilot-holdout` を起動できること。現行 guard はこれを拒否しない。

**成果物への影響:** brief I1 の「人間が明示承認」は機械的不変条件として成立しない。成立するのは「caller が token を渡した」までである。

**推奨:** 成果物の保証文を「人間性を認証する gate」ではなく「標準投入手順で明示 token を要求する運用 gate」に限定する。人間性の機械確認が必要なら、現裁定では実装不能として再裁定へ返す。

### 所見 3 — 迂回路は 4 系統あり、raw env 単独だけは P2 により止まる

**主張:** inspected surface で、人間の新規判断なしに承認 flag または承認値を driver へ渡せる経路は次の 4 系統である。

1. AI・cron・retry automation が標準 submitter を承認引数付きで起動する。
2. raw `qsub -v`、`qsub -V`、または任意 job wrapper が承認 env と整合 receipt を用意して job script を起動する。
3. `s8b_floor_campaign.py --confirm-irreversible-pilot-holdout` を直接起動する。
4. Python caller が `run_campaign(..., confirm_irreversible_pilot_holdout=True)` を直接呼ぶ。`--resume` も同じ flag を毎回渡せば通る。

**一次証拠 (file:line):** canonical job に `#PBS -V` はなく、directives は [floor_campaign.sh:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:2) から [同:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:5) の 4 個だけで、[test_pegasus_floor_tools.py:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:510) が集合を固定する。標準 submitter は [submit_floor.sh:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:411) から [同:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:423) の `-v` だけを使う。一方 raw `qsub` は [test_hooks.py:3815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_hooks.py:3815) で許可形である。driver の直接入口は [s8b_floor_campaign.py:6192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:6192) と [同:6197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:6197)、Python API は [同:5152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:5152) にある。

**成立条件:** raw scheduler 経路では、env だけでなく non-dry、同じ job ID/nonce、正しい source/script hash の receipt も必要である。P2 を直して採用した場合は receipt field も必要だが、同じ Unix principal が両方を作れるため人間性の境界にはならない。

**成果物への影響:** P2 は偶発的な env 単独注入を止めるが、非人間 caller と同一権限の producer は止めない。

**推奨:** raw `qsub` と直接 driver/API は非標準・非認証経路として明記し、標準経路だけを保証対象に限定する。

### 所見 4 — dry-run、既存 resume、同一 PBS job の再実行は暗黙承認にならない

**主張:** この 3 経路から過去の承認が自動継承される破れはない。

**一次証拠 (file:line):** dry-run は [submit_floor.sh:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:429) から [同:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:439) で qsub を実行しない。dry-run receipt は [certified_writer_admission.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_admission.py:186) と [floor_campaign.sh:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:444) が拒否する。標準 wrapper は [test_pegasus_floor_tools.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1051) で `--resume` 不在を固定し、runbook も [phase3-8b-restart-runbook.md:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/phase3-8b-restart-runbook.md:246) で fresh job を要求する。同一 PBS job body の再実行は [floor_campaign.sh:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:163) から [同:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:170) の create-only attempt directory で止まる。

**成立条件:** repo の既存 wrapper/resume 契約を使うこと。外部 automation が新 nonce で承認引数付き submitter を再起動する場合は所見 2 の迂回になる。

**成果物への影響:** dry-run 自体は一回性 key を消費しない。ただし P2 の dry-run receipt に `true` を書く案は、実投入でない記録を「承認済み」と見せる意味上の混乱を作る。

**推奨:** dry-run の安全性は維持し、P2 を採らないことで偽の approval record も作らない。

### 所見 5 — 既定拒否と exact bool は plan の骨格では緩んでいない

**主張:** bash 展開、空文字、`set -u`、配列展開、`"true"`・`"1"`・整数 `1` による driver gate の型迂回は、plan を逐語実装する限り成立しない。

**一次証拠 (file:line):** submit 側は [s2-plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:17) から [同:25](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:25) で内部値 `0/1` だけを使い、未承認 env を省略する。job 側は `${VAR+x}` と `${VAR-}` を指定し、driver は quoted array の [同:85](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:85) から [同:97](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:97) で起動する。CLI の `store_true` は [s8b_floor_campaign.py:6197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:6197) で exact bool を作り、core は [同:5255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_floor_campaign.py:5255) で `type(...) is bool` を要求する。下層も [s8b_holdout_admission.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_holdout_admission.py:683) から [同:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_holdout_admission.py:695) で再検査する。

**成立条件:** submit 内部変数を ambient env から初期化せず、job 側の未設定参照を plan 指定どおり guarded/default 展開にすること。

**成果物への影響:** driver gate の受理集合は `False/True` のままで、plan が開くのは意図した `True` 経路だけである。問題は型ではなく、その `True` を誰が生成したかである。

**推奨:** ambient submitter env を `1` にしたまま承認引数なしで実行し、qsub env・receipt・driver argv の全てに承認が出ないことを専用 test にする。既存の exact PBS directive test も維持する。

### 所見 6 — brief M8 と M9 は反証された

**主張:** M8 の「path 束縛のみ、bytes 束縛なし」は偽である。M9 の「両 script の pin が 0 件」も一括表現として偽であり、正しくは floor job script は動的 hash 束縛済み、submitter 自身は未束縛である。

**一次証拠 (file:line):** brief の主張は [brief.md:28](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/brief.md:28) と [同:29](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/brief.md:29)。しかし certified admission は直後の [certified_writer_admission.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_admission.py:197) で receipt hash を取り、[同:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/certified_writer_admission.py:204) で source blob bytes と照合する。producer は [submit_floor.sh:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:235) から [同:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:256)、job は [floor_campaign.sh:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:508) から [同:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/floor_campaign.sh:555) で実行 bytes、receipt、commit blob を三者照合する。test も [test_pegasus_floor_tools.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:548)、[同:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:564)、[同:1146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1146) で固定する。

別軸では path/class pin が [admission_registry.json:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/admission_registry.json:46) と [同:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/admission_registry.json:184)、文字列・呼出し数 pin が [test_pegasus_floor_tools.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:686) から [同:699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:699) と [同:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:987) から [同:1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1074) にある。総行数 499/1135 の exact pin は見つからなかった。

**成立条件:** 「pin」を固定 digest literal だけでなく、receipt 由来の加工後 hash、role/path key、文字列・呼出し数の semantic pin まで含めること。

**成果物への影響:** 親の pin 閉包評価と consumer 列挙が誤っており、所見 1 の致命的 scope 落ちを招いている。

**推奨:** M8 を撤回し、M9 を「submitter 自身の固定 bytes trust root はない。floor job bytes は source commit と per-submission receipt に動的束縛済み」と書き直す。

### 所見 7 — submitter 自身の hidden drift は既定拒否を破れる

**主張:** `submit_floor.sh` 自身には commit blob hash 照合がない。`assume-unchanged` で隠した変更により、承認引数なしでも env・receipt・driver flag を無条件生成する submitter を、clean-tree gate を通して実行できる。

**一次証拠 (file:line):** submitter 自身の検査は [submit_floor.sh:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:83) の path 一致と [同:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:194) から [同:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/submit_floor.sh:205) の通常 diff だけである。job script については [test_pegasus_floor_tools.py:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1178) から [同:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_pegasus_floor_tools.py:1195) が、`assume-unchanged` 下では status が clean のままで、別途 hash が必要なことを実証している。submitter 自身には同等の hash check がない。

**成立条件:** 同じ account が index flag と submitter bytes を変更できること。

**成果物への影響:** I1 を hostile workspace drift まで含む不変条件としては満たせない。P2 を採って consumer を直した場合も、変更済み submitter が env と receipt の両方を生成できる。

**推奨:** 親は「committed submitter bytes を信頼済み前提にする」か、「index flag 拒否と外部起点の bytes 束縛を別 wave・別裁定にする」かを選ぶ。script 内 self-check だけでは同じ編集者が check 自体を消せるため、人間性の trust root にはならない。

### 所見 8 — M10 の「実害は将来のみ」は一般化しすぎている

**主張:** 完了した floor 測定と一回性 key 消費が 0 件でも、投入実績と queue 消費まで 0 とはいえない。

**一次証拠 (file:line):** brief は [brief.md:30](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/brief.md:30) で実害を将来だけとする。一方、[worklog-phase3-0816-584.md:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/archive/worklog-phase3-0816-584.md:437) から [同:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/archive/worklog-phase3-0816-584.md:443) は既存投入 3 件を記録し、[phase3-8b-restart-runbook.md:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/phase3-8b-restart-runbook.md:185) から [同:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/phase3-8b-restart-runbook.md:187) は拒否前に scheduler が受理し queue 資源を消費すると明記する。

**成立条件:** 「実害」に投入・待ち・queue 資源消費を含めること。

**成果物への影響:** approval gate の不可逆 key 保護は未発火でも、運用上の失敗実績は既にある。

**推奨:** M10 を「完了測定と不可逆 key 消費は 0。投入は 3 件あり、queue side effect は既発生」と分解する。

### 所見 9 — P2 は新 authority ではないが、裁定上は採らないのが正しい

**主張:** receipt field は狭義の「新しい承認 authority」には当たらない。決定主体、署名者、再利用可能な permission store を新設しないためである。ただし新しい必須 gate 入力と approval record は増やし、裁定の「既存控えを参照する最小形」を超える。

**一次証拠 (file:line):** 裁定本文は [2026-08-16-rulings-full-43rulings.md:109](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full-43rulings.md:109) から [同:112](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full-43rulings.md:112)。plan の P2 根拠は [s2-plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:163) から [同:169](/work/1/SFC/tanab/dev-wave-jobs/t1180-pilot-approval/s2-plan.md:169) だが、「人間が投入器を通した証跡」という部分は所見 2 の正本と矛盾する。さらに既存 holdout ledger は [s8b_holdout_admission.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_holdout_admission.py:878) から [同:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/campaign/s8b_holdout_admission.py:894) で accepted bool を既に記録する。

**成立条件:** 粗い provenance で足り、人間 identity を receipt で証明しないという現裁定を維持すること。

**成果物への影響:** P2 は人間性を強めず、schema・consumer・test scope だけを増やす。しかも現 plan では所見 1 により実経路を全拒否する。

**推奨:** **P2 は不採用**。CLI flag、exact env、job 側 literal 検査、既存 driver flag だけにし、裁定控えの参照を docs/worklog に残す。

### 所見 10 — 人間手順書と full-chain test が scope から落ちている

**主張:** shell 2 本と test 1 本だけでは、承認経路が実際に使える全層を閉じられない。

**一次証拠 (file:line):** 現行手順は [tools/pegasus/README.md:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/README.md:210) から [同:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/tools/pegasus/README.md:214)、および [phase3-8b-restart-runbook.md:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/phase3-8b-restart-runbook.md:229) から [同:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/docs/phase3-8b-restart-runbook.md:235) で、承認引数なしの実投入を指示する。既存 actual admission test は [test_campaign.py:4943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_campaign.py:4943) から [同:4977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1180-pilot-approval/orchestrator/tests/test_campaign.py:4977) の base receipt だけで、confirmed receipt を通さない。

**成立条件:** wave を「人間が標準手順で実投入できる」状態で完了扱いすること。

**成果物への影響:** docs を更新しなければ人間は unconfirmed command を実行して拒否される。P2 を採る場合、full-chain test がなければ全拒否回帰を緑として出荷する。

**推奨:** 親への裁定パッケージは次の択一にする。

- 推奨: P2 を外し、両手順書に dry-run と実投入それぞれの承認付き command、人間手番、非認証境界を明記する。ambient env 非継承 test も足す。
- P2 維持: admission consumer、fixture、actual preflight test、schema version を scope に追加する。ただし人間性を証明したとは書かない。
- 人間性の機械確認を要求: 現裁定と衝突するため実装を止め、外部 trust root の再裁定を求める。

## 総括

- 最も危険なのは、P2 の optional key が先行 static admission に拒否され、承認付き実 job が全て driver 前で死ぬ点である。
- それを直しても、AI・automation と人間は同じ flag・env・receipt を生成でき、人間性は証明されない。
- M8/M9 は反証され、floor job bytes は動的に pin 済みだが submitter 自身の hidden drift は未束縛である。
- 既定無引数、exact bool、dry-run、標準 resume の拒否骨格には緩和変異を認めなかった。
- 推奨裁定は P2 不採用、最小 CLI→env 経路、手順書更新、保証文を「明示 token gate」に限定する案である。
- 「人間承認を機械確認した」と主張するなら、現裁定のままでは不可能であり、外部 trust root の再裁定が必要である。