静的検査の結論は、**段 2 プランをこのまま採用してはならない**です。Web は使っていません。HEAD `2310ea67` の読み取りだけを行い、pytest・build は未実走です。したがって緑判定はありません。

### 1. 既存 required 集合の縮小は明確な fail-open

- 深刻度: blocker
- file:line: `orchestrator/campaign/login_headroom.py:338-354,425-439,820-826,1025-1032`、`orchestrator/tests/test_login_headroom.py:397-399,470,485-501`、`plan-out.md:46-58,118-128`
- 再現条件: `file_writeback` が欠落し、`current=100`、`effective_ceiling=RESERVE_BYTES+101`、estimate 1 byte、予約 0。
- これを直さないと何が起きるか: 現行は `login_headroom() is None` から必ず DISPATCH だが、プランでは `occupied=current` として exact boundary が LOCAL になる。

現行 `_parse_memory_stat()` は `{anon,file,shmem,file_dirty,file_writeback}` を必須にしています。プランの `{anon}` への縮小は、今日の受理集合を拡大するため、規律 2 に反します。「新式に対して current へ degrade するから保守的」という説明では、**現行の DISPATCH 契約から LOCAL へ変わる事実**を消せません。

親 brief の P2 `handoff.md:52-56` も、既存 4 キーの欠落まで current fallback にする意味なら誤りです。後から提示された対案、すなわち既存 5 キーを required のまま維持し、新規 `slab_reclaimable` だけ optional にする方が規律 2 上で明確に優れます。

`test_every_observation_failure_is_none_and_dispatch[stat_missing]` の削除は、fail-closed 契約の削除そのものです。`anon` 欠落テストへの置換では同値になりません。少なくとも既存 5 キー欠落は `None`／DISPATCH、新規 slab 欠落だけ current fallback、という二群を別々に固定すべきです。

### 2. `file` 全体と `slab_reclaimable` 全体は「確実に回収可能」ではない

- 深刻度: blocker
- file:line: `plan-out.md:15-23,101-114,158-162`、`/sys/fs/cgroup/user.slice/user-31609.slice/memory.stat:1-21`
- 再現条件: clean な file page が mlock、長期 pin、子 cgroup の保護、継続的 refault などで回収できない。または reclaimable slab に参照中 object が多い。
- これを直さないと何が起きるか: 実際には残る charge を空きと数え、14 GiB の安全天井を超える local 実行を許可し、user slice 内の無関係なプロセスまで OOM 対象にし得る。

式 `current - clean_file - slab_reclaimable` の分類は次のとおりです。

| 量 | プランの扱い | 判定 |
|---|---|---|
| `anon`、kernel stack、page tables、percpu、sock、`slab_unreclaimable` | `current` の残差として保持 | 保守的。実物は `memory.stat:1,3-6,21` |
| `anon`、`shmem`（swap 無し） | file 候補から shmem を戻して保持 | 正しい。実環境は `memory.swap.max:1 = 0` |
| dirty/writeback | file 候補から除外して保持 | admission には正しい |
| file-backed mlock | `file` として減算され得るが、`unevictable` | 過小評価。実物にも `unevictable=4440064` が存在する。ただし、その全量が file 由来とは断定できない |
| GUP/DMA 等の pinned file page | clean file として減算され得る。専用 stat がない場合がある | 過小評価を検出不能 |
| `active_file` / `inactive_file` | 区別せず全 file を減算 | LRU 状態は回収保証ではない。保護、pin、即時 refault で残り得る |
| `file_thp` | clean なら全量を減算 | THP 自体は回収可能だが、locked／pinned／protected の場合を識別しない |
| `slab_reclaimable` | 全量を即時回収可能として減算 | 「reclaimable cache の所属」は、全 byte がその時点で解放可能という保証ではない |

例えば `current=13 GiB`、clean file 2 GiB のうち 1.5 GiB が mlock/pin、他の回収不能量 11 GiB なら、プランは 11 GiB と判定しますが、真の回収不能量は 12.5 GiB です。estimate 1 GiB と予備 2 GiBを加えると、プランは exact boundary で LOCAL、真値では 14 GiB を超えます。

`inactive_file` を使えば自動的に安全になるわけでもありません。これは回収候補の分類であって、即時・全量の回収保証ではありません。厳格な admission にするなら、減算対象が確実に回収可能であることを別途証明できない限り、raw current 側へ倒す必要があります。

### 3. 非原子的読み取りと clamp が最大の fail-open 値を作る

- 深刻度: blocker
- file:line: `orchestrator/campaign/login_headroom.py:403-425`、`plan-out.md:17-21,107-114,161-162`
- 再現条件: `memory.current` を読んだ後、別プロセスが file cache を増やしてから `memory.stat` を読む。または `file + slab_reclaimable >` 先に読んだ current になる。
- これを直さないと何が起きるか: stale current に新しい cache を二重に減算し、回収不能量を真値より小さくする。異常値では `max(0, ...)` が回収不能量 0、すなわち最も緩い値を返す。

具体例として、current 読み取り時点で回収不能量 12.1 GiB、その直後に別プロセスが clean file cache 1 GiB を追加したとします。後から読む stat の file だけが 1 GiB 増えると、プランは `12.1-1=11.1 GiB` と算出しますが、真の回収不能量は依然 12.1 GiB です。estimate 0.5 GiB、予備 2 GiB なら、プランは 13.6 GiB として LOCAL、真値では 14.6 GiB です。

`file > current` や `reclaimable > current` で回収不能量を 0 に clamp するのも誤りです。その観測は安全な「全量回収可能」の証拠ではなく、snapshot 不整合の証拠です。ここは current fallback または `None`／DISPATCH に倒すべきです。

一方、`file < shmem + dirty + writeback` のとき `clean_file=0` とする clamp は保守側です。問題は最終差が負になるケースまで 0 として許可側へ倒している点です。外側の `min(memory_current, ...)` は、入力が非負なら実質的に冗長で、競合を解決しません。

### 4. dirty/writeback に関する親 P1 は正しい

- 深刻度: nit（P1 自体は修正不要）
- file:line: `handoff.md:46-51`、`plan-out.md:17-23`、`memwatch.sh:127-130`
- 再現条件: dirty、writeback、shmem、または dirty と writeback が相互に重なる snapshot。
- これを直さないと何が起きるか: memwatch 式を admission に流用すると、書き戻し完了前のページを空きとして数える。

cgroup v2 では `shmem` は `file` の内数です。dirty/writeback も file cache の状態量であり、相互に完全排他だとは仮定できません。したがって

`clean_file = file - shmem - file_dirty - file_writeback`

は、重なりがあれば clean file を過少評価し、回収不能量を過大評価します。倒れる方向は DISPATCH 側であり fail-closed です。

逆に memwatch の `file - shmem` は dirty/writeback まで回収可能側へ入れるため、admission には楽観的です。memwatch は監視用ヒューリスティックとしては成立しても、規律 2 の admission 正本にはできません。親 P1 が正しく、ただし所見 2 の mlock/pin 等を解決していないため十分ではありません。

### 5. 予告された 3 変異は静的には KILL 可能だが、最重要変異が未登録

- 深刻度: must-fix
- file:line: `plan-out.md:101-138`、`orchestrator/tests/test_login_headroom.py:397-501`
- 再現条件: 計画どおりの値でテストを実装する場合。
- これを直さないと何が起きるか: 予告 3 変異だけは殺せても、既存 fail-closed 契約を削る `{anon}` required 変異が生存する。

静的な帰属は次のとおりです。

| 変異 | 正常値 | 変異値 | 静的判定 |
|---|---:|---:|---|
| 回収不能量を current に戻す | 650 | 1000 | 算出テストで KILL |
| clean file 減算を落とす | 650 | 950 | 算出テストで KILL |
| dirty/writeback を回収可能側へ戻す | 650 | 550 | 算出テストで KILL |
| `_decision_locked` だけ current へ戻す | LOCAL | DISPATCH | admit 専用テストで KILL |
| `grant_budget` だけ current へ戻す | 900-byte grant | 100-byte grant | grant 専用テストで KILL |

したがって、親が予告した 3 変異について「そのテストは殺せない」という穴は見つかりません。ただし、最も危険な変異である「既存 required を `{anon}` へ縮小する」はプラン自身が採用し、これを殺す既存 `[stat_missing]` node を削除します。変異集合が危険面を外しています。

### 6. `occupied_bytes` の意味変更は公開契約を静かに壊す

- 深刻度: must-fix
- file:line: `orchestrator/campaign/login_headroom.py:209-234,1190-1209`、`plan-out.md:25-28,158-165`
- 再現条件: repo 外 consumer が、公開された `LoginHeadroom.occupied_bytes` を現行 docstring どおり raw current として使う。
- これを直さないと何が起きるか: consumer がコード変更なしで楽観的な量へ切り替わる。現行 docstring も実装と矛盾する。

repo 内 grep の結果は次のとおりです。

- `headroom_bytes`: production consumer なし。テスト `test_login_headroom.py:212,231,274` のみ。
- `current_bytes`: raw current alias のまま。production consumer なし。
- `occupied_bytes`: production では同じ module 内の admission 2 式だけ。ここは更新対象に入っている。
- `run_tests.py:1046` と `check_ai_provenance.py:1935`: `grant_budget()` の tuple を消費し、dataclass field は読まない。
- `mutation_fanout.py:1289`: `reserve()` を通るため `_decision_locked` の変更が効く。
- `mutation_fanout.py:1295,1539-1552`: 生観測から読むのは `memory_max_bytes` だけ。

したがって repo 内の判定 consumer 取り残しはありません。ただし `LoginHeadroom` は `__all__` で公開されています。既存 `occupied_bytes` は raw current のまま残し、新設 `unreclaimable_bytes` を admission が明示的に使う方が、意味の二義化を避けられます。少なくとも class docstring と型契約の更新は必須です。既存 required field まで `int | None` に広げる必要もありません。

### 7. code/test 以外の正本が scope 外に残っている

- 深刻度: must-fix
- file:line: `handoff.md:16-18,42-44`、`docs/pegasus-runbook.md:305-316,351-359`、`docs/decisions.md:9942-9954`、`AGENTS.md:41-43`
- 再現条件: 親 scope の code/test＋decision fragment だけを land する。
- これを直さないと何が起きるか: 実装は回収不能量、運用正本は raw `memory.current` のままとなり、次の作業者・運用者が相反する契約を読む。

新しいユーザー裁定は D209 の「file cache を差し引かない」を supersede するので、decision fragment は必要です。しかしそれだけでは、正本 runbook の `判定量 = raw memory.current` と予算式が残ります。少なくとも runbook §7 冒頭と §7.0.0、AGENTS の 14 GiB 記述を同じ wave の親 docs scope に入れる必要があります。

一方、各コマンド自身の見積もりを「専用 scope の charged-memory peak」で測る層、すなわち `docs/pegasus-runbook.md:374-379` と `tools/README.md:13-16` は変更してはいけません。変更対象は既存 user-slice 占有量であり、新コマンドの peak estimate ではありません。

### 8. 12.32 GiB／7.15 GiB から「local が通る」は一般化できない

- 深刻度: must-fix
- file:line: `handoff.md:24-29,38-40`、`/sys/fs/cgroup/user.slice/user-31609.slice/memory.current:1`、`memory.stat:2,7,9-10,20`
- 再現条件: 時間経過、別セッションの allocation、予約 record、前回 peak が存在する場合。
- これを直さないと何が起きるか: 一瞬の snapshot を恒常的な local 可否として扱い、受入所要や queue 待ちの解消を過大に約束する。

今回の読み取りでは raw current は 12.514553 GiB、file 3.478458 GiB、slab reclaimable 1.344580 GiBで、親式による回収不能量は 7.692247 GiBでした。親実測の 7.15 GiB から既に約 0.54 GiB動いています。14 GiB − 予備 2 GiB 後の理論余裕は、予約前で 4.307753 GiBです。

さらに、通常の `grant_budget()` は `MAX_LOCAL_BUDGET_BYTES=4 GiB` で cap されるため、brief の「約 4.8 GiB まで通る」は `admit/reserve` の算術境界としては理解できますが、run_tests／provenance の grant ではその額を付与できません。生存予約、前回 peak、1 GiB minimum、観測後に増えた他セッションの charge でも DISPATCH になります。

正しく言えるのは「その瞬間、予約 0 かつ式の全前提が成立するなら、対象 estimate の一部が通り得る」までです。local 実行が恒常的に通るとは言えません。

## 総括

- blocker: 既存 required 5 キーを `{anon}` へ縮める案と `[stat_missing]` 削除は、今日の DISPATCH を LOCAL に変える。
- blocker: clean file 全体と `slab_reclaimable` 全体の減算は、mlock・pin・保護・refault を回収可能と誤認する。
- blocker: current→stat の非原子的読み取りと負値 clamp は、競合時に回収不能量 0 まで過小評価する。
- must-fix: 既存 5 キー required＋新規 slab のみ optional を採用し、危険な required 縮小を変異・テスト対象にする。
- must-fix: 公開 field の意味、runbook／AGENTS／D209 supersede、実測一般化を段 4 で是正する。