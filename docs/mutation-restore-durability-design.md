# 変異復元の耐久化設計 ([T-487] 起草、未裁定)

**状態:** 設計起草 + 生死確認のみ実測済み (§8.1)。**production 実装ゼロ。**
第一 slice の着手は §9.2 の択一待ちで、L-B (物理ノード死) は `UNKNOWN` のままである。
本書の主張には次のタグを付ける。タグのない断定を certify 済みと読んではならない。

- `[要求]` — 設計がこう要求する、の意。実装されていない
- `[未実装]` — 現行コードに存在しない
- `[未計測]` — 実機で測っていない。真偽は `UNKNOWN`

起草は [T-487] のユーザー裁定「変異復元を grace 予算依存から journal + fsync + 再開時修復へ
転換する方向とし、設計 wave が案を起草して返す」に基づく。設計択一は本書 §9 で裁定へ返す。

---

## 1. 問題 — 何が壊れているか

`tools/mutation_harness.py` は変異試験のために**実 checkout の tracked file を書き換え**、
テストを走らせ、`finally` で元に戻す (`_apply_mutation` の `finally` → `_restore_targets`)。
この復元は **process が生き延びること**に依存する。

現行が守るもの:

- graceful な SIGTERM/SIGINT — handler が `SignalAbort` へ変換し (`_install_signal_handlers`)、
  復元中の再入は `_defer_cleanup_signals` が `pthread_sigmask` で遅延する。
- harness 自身の再起動 — `_assert_clean_tracked` が汚染された木での起動を**拒否**する。

現行が守らないもの:

- **SIGKILL** (login ノードの OOM kill、scheduler の hard kill、`qdel -f`)。捕捉できないので
  `finally` を通らない。
- **ノードの死・電源断**、**Lustre client の eviction**。
- 復元書込は `write_text` のみで **fsync がない**。file 内で唯一 fsync を持つのは ledger の
  atomic write (`_write_ledger`) である。

**この残留は被覆の穴ではなく、テストが固定した現行仕様である。**
`orchestrator/tests/test_mutation_harness.py` の
`test_completed_record_is_flushed_before_next_runner_sigkill` は、SIGKILL 後に変異 bytes が
残ることを `assert` し、`finally` で手動復元している。

### 1.1 残留の実害はどこに出るか

`_assert_clean_tracked` があるので **harness 自身は保護されている**。無保護なのはそれ以外である。

- **受入全走・別 session・build・checker** は同種の gate を持たない。汚染された木を測って
  偽の赤/緑を得る ([T-476] の機序。worklog (210) の 79 failed が実例)。
- **人間**には、何が原因でどう直せば安全かの記録がない。
- そして `_assert_clean_tracked` は**阻止的**なので、強制終了後の変異 campaign は
  **人間が手で掃除するまで止まる**。これは `docs/orchestrator-design.md` §D の
  「失敗したらゼロからやり直しは数千回の評価のループでは許容できない」に正面から反する。

→ 転換の効能は「汚染を防ぐ」ではなく **「人間待ちの停止を、自己修復と再開に変える」** が正確である。

### 1.2 grace 予算という枠組みの限界

[T-360]/[T-399] は「復元が scheduler の grace 窓に間に合うか」を問うてきた。
[T-471] はその答が測定では出ないことを示した — 凍結式 `G_usable_lower ≥ 5s + 5s + R` の左辺は
凍結代入規則で 5.013 s に固定され、`R ≥ 0` ゆえ **`R` の値によらず偽**である。
凍結記号 `R_restore_bound` は上限性を立証できないため null のままとする。

実測 (診断値 `R_restore_observed`、計算ノード bnode064、500 trial、失敗 0) は max **71.79 ms**。
これは `_stop_process` の 10 s 清掃予算に対し **約 2.1 桁下** (139 倍)、
nominal grace 60 s に対し **約 2.9 桁下** (836 倍) である。
**裸の「3 桁下」は使わない** — どの予算に対してかで桁が変わる。

しかし桁が足りていることは本質ではない。**grace 予算という枠組みは、
そもそも「予告されて猶予をもらえる終了」しか扱わない。** SIGKILL・ノード死・client 断には
予告も猶予も無い。転換の狙いは、間に合うかを測る問題**自体を消す**ことである。

---

## 2. 枠組み — これは新方針ではなく既存 doctrine の適用である

`docs/orchestrator-design.md` §D/§A が durability の正本であり、campaign 層は既にこれに従う。
**`mutation_harness` は共有状態 (checkout) を書き換える唯一のコンポーネントでありながら、
この doctrine から唯一外れている。** 転換はその例外の解消であり、対応は 1 対 1 で付く。

| doctrine (§D/§A) | 既存実装 | 変異復元への写像 |
|---|---|---|
| ログ先行書込 + append 毎 fsync | `orchestrator/campaign/wal.py` の `append` | 変異書込の**前**に intent を fsync |
| commit record なき評価は復旧時に破棄 (rollback) | `STAGE_COMMIT` の有無 | **復元検証済みの印が無い変異は復旧時に巻き戻す** |
| 状態を保存せず入力だけから id を再現 (再起動を跨ぐ安定同一性) | spec 内容から campaign id を再計算 | **repo identity から journal 位置を再計算** |
| 末尾切れトレラント + 証拠 receipt 先行 | `wal.py` の `repair_truncated_tail` | 途中で切れた journal 行の扱い |
| 修復は冪等・before/after hash の transaction・第三の状態で停止 | `docs/spool/` の fold | 再開時修復の契約そのもの |

`campaign/wal.py` の `append` は既に必要な耐久化契約を持つ:
`O_APPEND|O_CREAT|O_NOFOLLOW|O_CLOEXEC` → `flock(LOCK_EX)` →
**tail-gate** (最終 byte が `\n` でなければ拒否し明示修復を要求) → 完全 write ループ →
`os.fsync(fd)` → **flock を保持したまま**親 directory の `os.fsync` → 先行エラーを覆わない close。

→ **裁定でユーザーに問うべきは「新しい耐久化方針を採るか」ではない。**
「既存 doctrine の適用範囲から `mutation_harness` を外し続ける理由があるか」である。

---

## 3. 失敗モード表

| 失敗モード | 現行が保証すること | 現行が保証しないこと | 転換後 `[要求]` |
|---|---|---|---|
| graceful SIGTERM/SIGINT | signal → `SignalAbort` 変換、`finally` で復元、復元中の signal は遅延 | 復元書込に file/dir fsync がない。直後のノード死に耐えない | 高速経路として維持。**復元 file/dir の fsync 後にだけ** `clean` を journal へ fsync |
| harness への SIGKILL | 完了済み変異の ledger は atomic write により残る | handler も `finally` も通らない。実行中の変異は木に残り、ledger にも載らない。テストがこの残留を明示的に固定している | 最初の target write より**前**に `armed` を fsync 済みなので、別 process が発見して修復できる |
| 計算ノードの死・電源断 | 実質なし。process 内の cleanup も node-local `/tmp` lock も失われる | 変異書込も復元書込も fsync されないため、旧 bytes・新 bytes・部分 bytes のどれが残るか契約がない | 成功した fsync が Lustre で永続する限り別ノードから修復可能。**この前件は `[未計測]`** |
| Lustre client eviction・I/O error | 同期 `OSError` は集約して失敗にする | eviction 後に再開できる durable intent がない | arm の fsync が失敗したら target を一切触らない。以後の I/O 失敗は `clean` を禁じ、journal を non-clean のまま残す |
| 変異中に別 process が木を読む | harness 同士は**同一ノードの** `/tmp` flock で排除 | reader は lock を取らない。in-place 書込のため部分 bytes・複数 file の旧新混在を読める。別ノードの harness は排除できない | 原子的置換で file 単位の部分 bytes は消える。**複数 file の混在窓は残る** → §7 の quarantine と lease で扱う |

---

## 4. 転換の骨格 — 4 つの部品

**journal + fsync + 再開時修復の 3 点では足りない。4 点目が要る。**

### 4.1 原子的 target 置換 `[未実装]` — これが無いと他が成立しない

現行の変異・復元はどちらも `Path.write_text`、すなわち **in-place の truncate + write** である。
途中で死ぬと**部分 bytes**が残る。部分 bytes は hash では人間の編集と区別できない。
したがって修復器は「触ってよい file」を安全に判定できない。

`[要求]` 同一 directory の temp file へ完全 write → mode 設定 → temp を fsync →
live target の hash 再検査 → `os.replace` → target directory を fsync。

`[要求]` temp の名前・inode・hash を `armed` へ**事前登録**する。登録と厳密一致する残骸だけを
除去できる。さもないと修復器は自分の残骸を「無関係 dirt」と見て永久に停止する
(修復の冪等性が壊れる)。

### 4.2 write-ahead journal `[未実装]`

`[要求]` 基盤は `campaign/wal.py` の framing/append/tail-repair primitive を共通層へ抽出して
共有する。**`AttemptJournal` を基礎にしてはならない** — dir fsync も tail-gate も
writer 間 flock も resume reader も持たず、それらを再実装すれば
`campaign/wal.py`・`AttemptJournal`・mutation journal の三方言が並立して
一方だけ hardening される。

`[要求]` 状態機械: `armed → mutated → restoring → clean`。
crash 再開経路は `armed|mutated|restoring|recovering → recovering → clean`。
**`clean` が唯一の terminal state。** error record を terminal 扱いにしない。

`[要求]` 順序契約 (この順序が守られなければ設計は無効):

1. HEAD・cleanliness・path type を検査し、対象 bytes と hash をメモリ内で確定する
2. `armed` を完全 write し、journal file を fsync する
3. attempt directory を fsync し、`active` locator を no-overwrite で公開して親を fsync する
4. **ここまで成功して初めて target を触ってよい**
5. §4.1 の原子的置換で変異を適用する
6. 全 target の変異後 hash を確認した後に `mutated` を append + fsync
7. 復元の前に `restoring` (または `recovering`) を append + fsync
8. 全 target を原子的に復元し、各 file/dir を fsync。HEAD・bytes・mode・cleanliness を再検査
9. **その後にだけ** `clean` を append + fsync
10. `last-clean` を更新して dir fsync → `active` を unlink して dir fsync
11. 変異結果を `--out` ledger へ書くのは `clean` の後だけ

`[要求]` **祖先 directory まで耐久化する。** `fsync(file)` は新しく作った祖先 directory entry を
保証しない。既存 `_write_ledger` も直近の親しか fsync しない。journal 階層を初回に作るなら、
既に存在する trusted root まで各 mkdir の親を順に fsync するか、階層を事前 provision して
耐久化済みであることを証明する。**これを欠くと、変異だけ残って journal へ到達する
名前空間が消える。**

### 4.3 journal の置き場所 `[要求]`

要件は 3 つ同時に満たすこと: (a) repo と同じ失敗ドメインで durable、
(b) `--out` を知らない第三者が**発見できる**、(c) `git status` に映らない
(映ると harness 自身が起動不能になる)。

`[要求]` **site canonical root** を正本化し、CLI で自由に変更できないようにする。
呼出しごとの自由値の必須引数は canonical にならない — 二つの正しい引数値から二つの lock と
`active` が作れ、同じ checkout を二重に変異させる split-brain になる。
**root の値はマシン固有なので `docs/pegasus-runbook.md` に置き、本書には導出規約だけを書く。**

`[要求]` path だけでなく **worktree incarnation nonce** を束縛する。絶対 git-dir path は
worktree の種類を分けるが、その worktree 個体の不変な身元ではない。削除・prune・同名再作成で
admin path は再利用されうる。

**却下した候補: git admin dir 配下** (`--git-dir` / `--git-common-dir`)。発見可能性は最も強く
`git status` にも映らないが、**`git worktree prune` や worktree 削除で journal だけが
巻き添えで消える。** 汚染された作業木を残したまま記録が消えるのは現状より悪い。

**却下した候補: `--out` ledger の隣**。別の `--out` で起動した process が残留 journal を見失う。

### 4.4 再開時修復 `[未実装]`

`[要求]` **phase 0 に置く** — canonical repo/state-root を解決した直後、
spec hash の検証 (`--expected-spec-sha256`) よりも**前**に `active` を inspect する。
`_read_head_sources` と `_assert_clean_tracked` の前に置くだけでは足りない。
operator が誤った spec hash を指定すると、その手前で終了して汚染を報告しないまま隠れる。

`[要求]` **全 target 二段階検査 — preflight を全部終えてから、初めて書く。**
各 target を `ORIGINAL` / `MUTATED` / `OTHER` に分類し、
**1 つでも `OTHER` があれば他を含め一切修復せず停止する。**
後半の不一致を見つける前に前半を復元してはならない。

`[要求]` fail-closed にする分岐 (署名で書く。通る正例を 1 つ添える):

```
repair(attempt) → RESTORED   ただし次を全て満たすときのみ:
    active locator の inode が attempt file と一致し symlink でない
    完全な armed record が存在し、seq/hash-chain/遷移が正当
    現在 HEAD == 記録 HEAD          (移動していたら停止)
    repo path / worktree incarnation nonce が一致
    全 target の bytes ∈ {ORIGINAL, MUTATED}   (1 つでも OTHER なら停止)
    target とその親 component が symlink でなく repo 外へ解決されない
    index dirt なし、target 外の tracked/untracked dirt なし
    旧 attempt の reader/writer がゼロであると証明できる (§4.5)
    書込直前の hash 再検査が変化していない
それ以外は QUARANTINE  (tree を書き換えず、§7 の quarantine を立てる)

通る正例:
    使い捨て worktree で 1 変異 (2 file) を適用中に harness が SIGKILL される。
    journal は armed + mutated まで durable。HEAD 不変。両 file の bytes は記録された
    変異後 hash と一致。無関係 dirt なし。scheduler の job は terminal を報告済み。
    → recovering を fsync し、2 file を記録 HEAD 内容へ原子的に復元、fsync、
      全体検証の後 clean を記録。campaign はそのまま再開する。
```

### 4.5 quiescence — 両レンズが独立に到達した最重要の穴

**durable lock を取得できたことは、旧 attempt が静止した証拠にならない。**
lock は harness 親 process が持ち、終了時に閉じるだけである。runner は別 subprocess であり、
`_stop_process` は二度目の wait timeout 後は生存を許したまま戻る。

壊れる筋: login ノードの harness が OOM で SIGKILL される → dispatch した計算ノードの job は
**生き続ける** → 別 process が解放済み lock を取り、復元して `clean` を書き `active` を消す →
その後、生き残った runner が target や `.pyc` を書く → consumer は `active` 不在・epoch 安定を
観測して**再汚染された木を採用する**。

`[要求]` **`clean` を書く前に、旧 attempt の reader/writer がゼロであることを証明する。**
`armed` へ scheduler job ID・PID/PGID・process start token・cgroup identity を束縛し、
job の terminal state を確認できない間は修復も clear もしない。判定不能なら quarantine する。

---

## 5. 何が捨てられ、何が残るか — grace 依存の正確な射程

転換は **grace 依存を全部は消さない。** 正直に区別する。

| grace が今支えているもの | 転換後 |
|---|---|
| 木の汚染 (復元が間に合うか) | **消える。** ただし durable repair + quiescence + consumer quarantine が実装され**実機で受入されてから** `[未計測]` |
| 子 process の後始末 | **消えない。** ただし grace ではなく quiescence lease / scheduler terminal 証明へ**置換できる** |
| `H_head` (`_assert_head` の git subprocess) | **意味検査としては残る。** ただし grace 内に収める時間上限の証明は不要になる |
| `D_delivery` (PBS warn 配送遅延) | 安全性の問題から**可用性の問題へ下がる** |

したがって:

- **[T-360] の D130 条件 3 を「T-487 の設計を採用した」だけで closed にしてはならない。**
  明示的に supersede する裁定が要り、旧条件 3 は
  「durable recovery + quiescence + consumer quarantine の実装と実機受入」へ置換される。
- **[T-486] は `closed` ではなく `deferred`** とする。転換が実機受入まで到達しなければ、
  probe leg は再び必要になる。

---

## 6. P1 の限界 — intent だけで足りるか

復元内容の権威は現行実装では git HEAD blob (`git show HEAD:<rel>`) であり、起動時に
clean を要求するので、原理的には「どの HEAD の・どの rel が変異中か」だけが durable なら足りる。
しかし次の穴がある。

- **`git replace` refs。** `refs/replace/<記録 HEAD>` を作れば `rev-parse HEAD` は記録値と
  一致したまま `git show` が別 blob を返す。harness の git 呼出しは `--no-replace-objects` を
  渡しておらず、`GIT_NO_REPLACE_OBJECTS` は env 濾過で落ちるため replace は**有効なまま**である。
- **object 不在・破損・partial clone の lazy fetch 不可。**
- **HEAD 移動**、`.git` 破損、submodule・非 UTF-8・symlink 対象。
- **metadata。** 現行は text 一致しか見ない。HEAD が 100644 でも作業木が 0664、
  あるいは `core.fileMode=false` なら executable bit の差は cleanliness に映らない。
  原子的置換は permission を Git mode 由来の値へ変えてしまい、元の permission を失う。

`[要求]` 最低限 `--no-replace-objects --no-lazy-fetch` を arm 時と修復時の**両方**で使い、
accepted metadata を `lstat` から記録して保存不能なものは arm 前に拒否する。

**親の推奨は「原文 bytes も journal に持つ」。** 1 変異が触る最大 file 数は 2、
対象 file の最大は 240,600 bytes であり、[T-471] の実測は bytes が所要時間にほぼ効かないことを
示している (支配項は `__pycache__` purge)。**安い。** そして bytes を持てば、
git object store の可用性・replace refs・lazy fetch・HEAD 移動という依存が**一族まるごと消える**。
§9 の裁定軸とする。

---

## 7. quarantine — 「何もしない」だけでは安全でない

曖昧な木を上書きしない方が、不可逆な人間データ破壊より優先される。これは正しい。
しかし**「何もしない」は、同じ checkout の全 consumer が止まって初めて安全になる。**
修復器が cache 1 個で停止し、target が変異したまま残り、別 session が受入全走を起動すれば、
汚染された木の測定結果が公開される。

`[要求]` 優先順位を明文化する:

1. 曖昧時は tree を絶対に書き換えない
2. **同時に checkout を durable な quarantine 状態にし、sanctioned consumer を fail-stop させる**
3. stderr だけでなく、repo・attempt・理由・安全な次操作を durable に提示する

「沈黙して汚染を残す」と「誤って書き戻す」の二択にしてはならない。**無書込 + consumer 拒否**が要る。

### 7.1 consumer 契約の射程 — `DW-G03` を守る

前後 epoch 検査 (読取前後に `active` 不在と `last-clean` 一致を確認) だけでは不十分である。
consumer は precheck 後に外部効果 (job 投入、artifact 書込、ユーザーが見た stdout) を
起こしうるが、postcheck で汚染を知っても**それらは取り消せない**。

`[要求]` 協調 consumer は実行全体で durable な shared lease を保持し、変異は exclusive lease を
保持する。epoch は lease の欠陥と短い ABA を検出する**補助証拠**へ下げる。

**ただし一般化の範囲は `DW-G03` に従う。** 族全体への制度一般化は同型欠陥が異なる
producer/consumer で独立に 2 件再現したときだけ許される。現時点で明示できる exact pair は
`mutation_harness → run_tests / 受入投入` の 1 件だけである。
→ **今はこの 1 pair の局所修復に留める。** 全 checker/build/session への一般化は、
第二の独立 pair を示すか、ユーザーが `DW-G03` の例外として裁定した場合に限る。
専有・使い捨て worktree 方式を採れば、族一般化そのものを回避できる。

---

## 8. 実装 wave が要する層 (棚卸し)

新しい gate が実際に効くには次の層すべてが要る。**producer だけ先に有効化してはならない。**

| 層 | 要るもの |
|---|---|
| durable I/O 基盤 | canonical framing、reader、tail repair、locking、schema upgrade |
| harness producer | 原子的 writer、状態機械、CLI、ledger 順序、cache policy |
| worktree provisioner | 専有 worktree、incarnation nonce、owner lease、破棄条件 |
| repair tool | inspect / repair / abandon、承認の束縛、quarantine receipt、exit code |
| root / config | site canonical root、権限、mount 検査、GC と retention |
| [T-360] transport | state root の伝播、scheduler identity、旧 process の停止 (D131 の二択が未解決) |
| consumer admission | `run_tests.py`、`check_wave_startup.py` の fresh/resume、`dev_wave_land.py`、および同じ checkout を読む entrypoint の実在 inventory |
| 手順・docs | `DW-M05`、`DW-O18`/`O19`/`O20`、dev-wave 入口、Pegasus runbook、tools docs |
| rollout | legacy harness の停止、旧 journal と dirty tree の migration、version skew |
| 検証 | syscall fault matrix、別 client、node death、orphan child、人間編集、consumer lease |

**`DW-O19` の現行手順は復元の正本を `git diff` / `git checkout --` としている。**
実装後もこれを残すと、journal と所有確認を迂回した手動復元が正規手順として残る。同時に是正が要る。

### 8.1 最安の生死確認実験 (`DW-G01`) `[実施済み — GO]`

**2026-08-06 に実施した。** 一次資料と射程は
`output/insights/2026-08-06_t503-restore-durability-liveness/`。結果は
SIGKILL leg = PASS、正の control (部分 bytes 検出) = PASS、walltime proxy = PASS、
**node-death leg = `UNKNOWN` (未実施)**。**部分 bytes は観測されず、NO-GO 条件は成立しない。**
実験の実行体は `tools/pegasus/probes/t503_restore_durability_probe.py` と
同 `_probe.pbs` / `_recover.pbs` / `_verdict.pbs`。以下は当初の設計記述である。

大型機構を作る前に、実 repo を使わない 100 行以内の使い捨て driver で確かめる。

- Lustre 上の使い捨て directory に target・journal・`active` を作る
- writer は `armed fsync → active dir fsync → 原子的変異 fsync → READY` まで進んで待機
- **SIGKILL leg:** READY 後に writer を SIGKILL し、**別 process・可能なら別ノード**から
  journal と target を開いて修復し `clean` を確認する
- **node-death leg:** 同じ READY 後に、管理者承認のもとで writer ノードを実際に
  reboot / power-cycle し、別ノードの recovery job で確認する

**scheduler の walltime kill は「process 死 + allocation 終了」の proxy にはなるが、
物理ノード死の証明ではない。** 実ノード reboot を実施できなければ node-death 欄は
`UNKNOWN` のままにし、walltime SIGKILL だけで certify してはならない。

受入条件: 別 client から durable な `armed` が見え、target が旧か新の**完全 bytes**であり、
修復後の original / clean が再 open 後にも見えること。
**journal だけ残って target が部分 bytes になる設計は NO-GO。**

### 8.2 事前登録すべき変異 (この機構の検出力を測るため)

`armed` の fsync を最初の target write の後へ移す / journal 初回作成後の dir fsync を削除 /
temp file または target dir の fsync を削除 / 復元検証より前に `clean` を記録 /
append 失敗後も poison せず `clean` を書く / 修復述語を `current != original` へ緩和 /
記録 HEAD でなく current HEAD から復元 / 全 target preflight 前に最初の target を復元 /
無関係 dirt を無視して修復 / symlink・path escape・hardlink target を許可 /
durable lock または `active` の no-overwrite 主張を削除 / 未終端 tail へそのまま append /
journal `clean` の前に terminal ledger record を書く / consumer が postcheck を省略。

各変異に対し、少なくとも 1 つのテストが確実に赤になることを事前登録で対応付ける。

---

## 9. ユーザー裁定へ返す択一

| # | 軸 | 選択肢 | 親の推奨 |
|---|---|---|---|
| U-1 | 無人自動修復の権限 | (a) 機械的に専有を確認できる**使い捨て worktree のみ**自動、一般 worktree は inspect-only + 人間承認 / (b) 一般 worktree でも協調 lock 前提で自動 | **(a)**。hash 一致は権限の証明にならない。byte 単位で一致する人間の編集と TOCTOU は識別できない |
| U-2 | journal が原文 bytes を持つか | (a) intent のみ + resolver pin / (b) **原文 bytes も持つ** | **(b)**。最大 2 file・240 KB で安く、git object 可用性・replace refs・lazy fetch・HEAD 移動の依存が一族ごと消える |
| U-3 | state root の権威 | (a) **site canonical root** + worktree incarnation nonce / (b) 呼出しごとの自由値の必須引数 | **(a)**。(b) は split-brain を作る |
| U-4 | journal 基盤 | (a) **`campaign/wal.py` の primitive を共通層へ抽出して共有** / (b) `AttemptJournal` 派生の専用実装 | **(a)**。(b) は三方言並立を招き「第二方言を作らない」に抵触する |
| U-5 | consumer 協調の強度 | (a) **実行全体の shared lease + 変異の exclusive lease、epoch は補助** / (b) 前後 epoch 検査のみ | **(a)**。epoch では発行済みの外部効果を巻き戻せない |
| U-6 | consumer 契約の射程 | (a) **既知 1 pair の局所修復に留める** (`DW-G03` 遵守) / (b) 全 consumer へ一般化 | **(a)**。独立 2 例が揃っていない |
| U-7 | `__pycache__` | (a) **不在を入場条件にし、自動削除しない** / (b) journal 対象にして削除・復元する | **(a)**。無条件 purge は別 process の artifact を壊す。ただし dispatch では `PYTHONDONTWRITEBYTECODE=1` が計算ノードへ伝播しないため、transport 全層での無効化が別途要る |
| U-8 | rollout | (a) **producer・consumer gate・quarantine・手順更新・旧版停止を 1 つの activation gate に束ねる** / (b) consumer を後続 task にして producer を先行有効化 | **(a)**。(b) は producer だけ効いた危険な中間状態を作る |
| U-9 | [T-486] と D130 条件 3 | (a) **[T-486] は `deferred`、D130 条件 3 は明示的 supersede の裁定を経て置換** / (b) 設計採用時点で不要・closed | **(a)**。実機受入前に closed にはできない |
| U-10 | 実装 wave での harness no-touch | (a) **実装 wave で明示的に解除する** / (b) harness を変えず worktree 丸ごと隔離・破棄する方式へ設計変更 | **(a)**。wrapper では in-place 書込を原子化できず本設計と等価にならない |

### 9.1 転換の必須条件 (段 3 の致命所見から昇格)

裁定がどう転んでも、次を満たさない実装を「転換が完了した」と呼んではならない。

1. **quiescence の証明** — 旧 attempt の reader/writer がゼロであることを示せない間は修復も clear もしない
2. **原子的 target 置換** — **live target に**部分 bytes を作らない
   (準備中の temp に残る部分 bytes は別問題であり、quarantine 側で扱う)
3. **祖先 directory までの耐久化** — journal へ到達する名前空間自体が消えない
4. **canonical な state root と incarnation 束縛** — split-brain を作らない
5. **legacy lock からの移行 gate** — 旧版の drain を receipt で証明してから切り替える
6. **quarantine** — 曖昧時は無書込かつ consumer を fail-stop させる

### 9.2 第一 slice を凍結しなかった理由 `[2026-08-06 実測]`

生死確認 GO の後の実装 wave は、基盤 3 単位 (WAL primitive の抽出・原子的置換・journal 記録層) を
**配線せずに作る**案を起草し、敵対相談 2 レンズを経て**実装せずに止めた**。裁定と逐語は
`output/insights/2026-08-06_t503-restore-durability-implementation-ruling/`。着手前に決める
択一は同書の表 (V-1〜V-6) が正本である。止めた根拠は次の 4 点で、いずれも一次資料で確認した。

- **木へ触る process は arm より後に生まれる。** `mutation_harness` は target を書いた後に
  runner を新 session で起動し、dispatch ではその先に job も生まれる。arm 時点の単一 writer
  identity では §4.5 の quiescence 束縛を満たせない。runner 登録 record か exclusive lease が要る。
- **incarnation nonce と job ID の発行者がいない。** worktree の git admin dir に不変の身元はなく、
  `PBS_JOBID` は login shell では unset である。§4.3 の束縛は provisioner なしには空洞になる。
- **`clean` の発行権限がない。** verifier を caller callback にすると、no-op 復元でも
  `clean` を書けてしまう。sealed capability の発行者が要る。
- **配線しない基盤は `DW-G05` の成果物影響を書けない。** 活性化しない限り certified 選択・
  レポート・台帳の値・受理集合・参照は変わらない。有効な部分集合も見つからなかった。

次に実装する wave への持ち越し条件:

- 抽出を行うなら、`append` / recovery suffix / tail-repair receipt の各経路に**現行 bytes の
  golden vector** を置き、例外の型・`__module__`・診断順序・materialization gate の位置を
  exact に固定する。receipt の code identity は leaf-only であり、抽出は盲点を広げる (別 task)。
- 共通層を repo 全体の汎用 framework と呼ばない。`DW-G03` の独立 2 例は揃っていない。
- test 名・docstring・完了記述に「syscall 順序であって物理永続性ではない」を残す。L-B は `UNKNOWN`。

---

## 10. 本設計が保証しないこと

- **物理ノード死・client eviction・OST/MDT failover 後に、成功済み fsync がどこまで永続するか。**
  `[未計測]`。公式意味論から保証外を切り分けることはできるが、実機の fault 実験なしに確定できない。
  **同じ失敗ドメインにあるものを backup と呼ばない。**
- **複数 file の旧新混在窓。** 原子的置換は file 単位の部分 bytes を消すだけである。
- **非協調 consumer。** lease も epoch も見ない reader には何も保証しない。
- **`_assert_clean_tracked` は全 dirt を見ていない。** 実測で確認した — harness と同じ
  `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` は
  **ignored file を報告しない** (`--ignored` が要る)。`*.o` / `build/` / `*.so` のような
  テスト結果を左右する生成物と、skip-worktree / assume-unchanged entry に盲目である。
  修復器の「無関係 dirt なし」条件はこの盲点を継承してはならない。
