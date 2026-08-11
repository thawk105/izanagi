# レンズ B 判定

T-798 と T-799 はともに `real`。ただし、親の Q1(b) は「小〜中コスト」「新しい recovery 機構は不要」とは言えない。state の削除を遅らせると、commit 済み・state 残存という新しい状態が生まれ、現在の land recovery では処理できない。

テストや pytest は実行していない。読み取り専用の静的検査と既存 probe log の読解のみである。

なお、C2 のログには不一致がある。`probe_t799c.log` は rc=0 の成功を記録している一方、より早い `probe_t799.log` は同名の C2 を rc=20 で拒否している。[findings.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/findings.md:1) は後者を採用していない。裁定 package では、どの実行を正本にしたかとコード checkout を明記すべきである。

## 1. Q1(b) の active-aware gate

### 1-A — 狭い状態判定そのものは成立する — `refuted`

`apply_fold` の状態遷移から見ると、次の判定は妥当である。

| state と tree | 意味 | gate |
|---|---|---|
| 全 target が after、全 GC target が missing | apply 完了・commit 待ち | 受理可能 |
| target に before が残る | apply 未完了 | 拒否 |
| GC が一つでも present | GC 未完了 | 拒否 |
| target が before、GC が missing | 第三状態 | 拒否 |
| schema、symlink、path、hash が不正 | state 自体が信用不能 | 拒否 |

`apply_fold` は state に after bytes を保存し、全 target の状態を確定してから書込みと GC を行っている。[spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2298) したがって、厳密にこの集合だけを `validate_spool_tree` で許せば、通常の部分 resume を見逃すとは言い切れない。

### 1-B — state と tree だけで十分という主張は崩れる — `real`

「全 target after / 全 GC 削除済み」は、次の二つを区別できない。

1. apply 完了後、まだ fold commit 前。
2. fold commit 成功後、postcondition または state finalize 前。

(b) では後者が実際に発生する。commit 後に process が死ぬと、main は fold commit を指し、state は残る。ところが land の active recovery は `locked_main != tested_tip` を即座に `RC_FOLD_RECOVERY_FAILED` とする。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:2194)

つまり、active-aware gate は docs 検査を通せても、land recovery の状態機械を完成させない。

成果物影響: canonical 3 台帳と `FOLDED.md` は commit 済みでも、state finalize ができず、次の land が fold commit を正規成果物として確定できない。

### 1-C — 「抑止 flag 不要」は条件付きで正しい — `refuted`

`check_docs.py` は `validate_spool_tree` の finding を受け取るだけであり、専用抑止 flag は不要である。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/check_docs.py:797)

ただし `_discover` の変更は以下を必須にする。

- state の JSON/schema/path を fail-closed に検査する
- target の path escape と重複を拒否する
- target の実 bytes と after hash を照合する
- GC path が全て本当に消えていることを確認する
- 予定外の pending fragment を受理集合へ混ぜない
- 部分状態では従来どおり `transaction-active` を返す

ここを単に「state があれば内容を見て問題なければ通す」とすると、規律 2 に反する受理集合の拡大になる。

## 2. Q1(b) のコスト

### 2-A — raw の呼出し口が 2 箇所という数え方 — `refuted`

本番の直接呼出し口が standalone CLI と land の 2 箇所という数え方自体は正しい。しかし、状態遷移は 2 種ではない。

land 側には少なくとも以下がある。

- fresh land: ff-only 後に fold
- main が既に tested tip の land
- active transaction recovery
- commit 後の postcondition failure
- rollback failure
- standalone apply

`_fold_main_locked` は apply、docs gate、pending postcondition、staging、commit、commit後検査を一つの try 節で扱っている。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:1839)

### 2-B — 「新しい状態遷移がない」は誤り — `real`

(b) を入れると、少なくとも次が増える。

```text
state retained
  → canonical applied
  → fold commit created
  → state retained
  → postcondition/finalize pending
```

commit 成功後に例外が出れば、同一 process 内では `_rollback_fold` が commit、index、worktree、state を巻き戻す必要がある。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:1745)

process 死亡なら rollback は実行されない。次回 land は現在の active recovery 条件に入れず、state だけが残った fold commit で停止する。

また、state 不在を固定するテストは package の「5 行」より多く、少なくとも `test_spool_fold.py` の 1779、2583、2687、2730、2834、2898 と `test_dev_wave_land.py` の 2763〜2765 が直接影響する。[テスト検索結果](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/orchestrator/tests/test_spool_fold.py:1779)

成果物影響: 正常系の T/D/F 値は変わらないが、commit済み台帳を `landed` として確定できない中間履歴が新たに残る。

## 3. 冪等性の主張

### 3-A — apply 層の二重挿入は起きにくい — `refuted`

rotation、failure supersede、見送り追記も、plan 作成時に after bytes へ展開され、state に保存される。state がある場合の `apply_fold` は再度 render せず、after hash と before hash を比較するだけである。

したがって、同一 state の再 apply では、

- rotation archive を再生成しない
- `FOLDED.md` の receipt を再追記しない
- supersede 行を再挿入しない
- 見送り追記を再挿入しない

という静的保証がある。これは親の主張を支持する。

### 3-B — probe による一般化は過大 — `real`

`probe_post_apply_resume.py` は単純な worklog fragment しか扱っていない。さらに「canonical は不変」の検査は同じ `git status` を左右で取得して比較しており、常に真になる。[probe_post_apply_resume.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_post_apply_resume.py:49)

rotation、failure supersede、見送り追記で同じ resume を実測した証拠にはなっていない。コード構造上の冪等性は支持できるが、「実測で全 plan を確認した」という表現は修正が必要である。

成果物影響: 同一 state の resume で台帳値が二重化する所見は refuted だが、commit後 crash の recovery 不備は別に残り、未確定の proof chain を作る。

## 4. Q2(a) の schema 互換

### 4-A — 省略可能 field は fail-open — `real`

親の「新 field を省略可能として読み、有る場合だけ照合」は T-799 を旧 state に対して無効化する。

旧 code が v1 state を作った直後に process が死に、新 code が次の land で読むケースでは、field が無いこと自体が「起源を検証できない」証拠である。それを照合せず通すと、まさに旧来の wrong-HEAD resume が継続する。

現行 `_load_state` は `version == 1` を要求し、`_state_plan` は多数の key を必須としている。[spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2236)

### 4-B — version 2 への単純な切替も不十分 — `real`

version 2 を厳格に要求すれば fail-closed になるが、旧 v1 の in-flight state を復旧不能にする。これは実際の state lifetime、すなわち「一回の land 中に state が生き、次の land が消費する」境界に直撃する。

安全な移行は、例えば次のいずれかが必要である。

- v1 state は無条件に land recovery へ進めず quarantine する
- 実際の wave ref/HEAD と現行 main を使って plan を再計算し、fragment、target、transaction ID を完全一致させる
- 旧 state の起源を外部の durable journal が証明できる場合だけ v2 へ変換する

成果物影響: 省略可能 field では wrong-origin fold の受理集合が残る。厳格 v2 では旧 crash state の復旧受理集合が狭くなるが、未検証成果物の main への確定は防げる。

## 5. Q2(a) の束縛先

### 5-A — `tested_tip` が完全に無効という表現は過大 — `refuted`

現在の `_verify_heads` は、argv の `tested_tip` と実際の wave HEAD/ref が一致することを検査している。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:602)

したがって argv は単なる無検証の文字列ではない。

### 5-B — しかし state の起源識別には足りない — `real`

C2 は wave B の実 HEAD/ref と argv が一致していても、wave A 由来の state を消費できる。必要なのは「今回の argv と一致すること」ではなく、「state を作った観測値と今回の実体が一致すること」である。

少なくとも以下を、申告値ではなく実測値として記録・照合すべきである。

- `origin = land` / `standalone`
- ff 前に lock 内で観測した `main_before`
- plan source の実 `wave_ref`
- plan source の実 `wave_head`
- `tested_tip` と実 wave HEAD の一致
- apply 開始時の main HEAD
- 実際に CAS rollback に使う `rollback_ref`
- 可能なら audited closure または source tree identity

これらの束縛値は transaction ID にも含めるべきで、state の JSON field だけを後から書き換えられる形にしてはいけない。

さらに、Q2(a) の「proof chain が durable になる」という主張は現状の state だけでは成立しない。state は成功後に削除され、`FOLDED.md` の receipt は `wave`、`seq`、`content_sha256`、allocation しか持たない。[spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2089)

成果物影響: runtime の wrong-HEAD 受理集合は狭められるが、base/origin/tested tip は state 削除後の `FOLDED.md` や fold commit には残らず、レポートの durable proof chain は自動では増えない。

## 6. Q2(b) 一律封鎖の副作用

### 6-A — 安全側の封鎖という評価は不十分 — `real`

standalone resume が commit を作らず、T-798 と同じ dirty tree に着地することは実測されている。[probe_t799_after.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_t799_after.log:1)

しかし、land が使えない状況では standalone が唯一の復旧入口になり得る。

- land process 自身が起動できない
- lock を取得できない
- land の import/checker が壊れている
- main が別の理由で land を受け付けない
- process 死後に state の内容だけを確定検査したい

lock busy のときに standalone が lock を迂回するのは危険なので、封鎖自体には理由がある。ただし封鎖するなら、同等の lock-aware finalize/recovery command が必要である。単に CLI を閉じると安全な復旧経路も消える。

`docs/spool/README.md` は「中断後は同じコマンドで resume」と記しつつ、fold は land lock 内だけと定めている。[README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/docs/spool/README.md:119) この二つの契約を同時に満たす recovery protocol がまだない。

成果物影響: 正常 land の ledger 値は変わらないが、crash 後に手動 restore または未検証の手動 commitへ追い込まれ、proof chain の受理集合と復旧可能性が悪化する。

## 7. 第4案

### 7-A — 安価で同等以上の drop-in 案はない — `refuted`

候補を確認すると、

- `apply_fold` に commit まで含める  
  → commit 前後の process death と state finalize の窓を API 内へ移すだけ。
- index と commit を同時に行う  
  → Git の ref、index、working tree、state file は一つの atomic transaction ではない。
- state deletion に fsync を足す  
  → durability は上がるが、Git commit と state unlink の原子性は得られない。

したがって、現行 API と同程度のコストで窓を消す第4案はない。

### 7-B — 強い長期案は存在する — `real`

temporary index/tree で folded tree を構築し、gate を通した commit object と phase journal を作り、ref を CAS 更新する「commit-first + phase journal」方式は、未commit canonical の窓を大きく縮められる。ただし working tree 復元、ref更新、state finalize の recovery が必要で、大規模な別設計である。

成果物影響: immediate fix の選択肢ではないが、成功 fold の commit、base/tip provenance、finalize 状態を durable に結びつけられる。

## 8. Q3 の順序

| 順序 | 判定 | 問題 |
|---|---|---|
| Q1(b) → Q2(a) | **real な危険** | state 寿命だけ先に延び、wrong-HEAD resume の窓を拡大する |
| Q2(a) → Q1(b) | 条件付きで許容 | strict schema、旧 state policy、commit後 recovery が先に必要 |
| 同一変更 | 最も安全 | ただし旧 v1 in-flight state の移行を別途解決する必要がある |

親の「分割するなら Q2 を先」は正しい。Q1(b) を先に出す順序は拒否すべきである。

成果物影響: Q1先行では未確定 canonical が land recovery の受理集合に入り、Q2先行では wrong-origin fold の受理集合だけを先に狭める。

## 9. DW-G05 の成果物影響

`DW-G05` は、certified 選択・レポート・台帳の値、受理集合、参照を1行で特定することを要求する。[core.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/docs/dev-wave/core.md:65)

| 対象 | 判定 | 不足または具体化すべき影響 |
|---|---|---|
| Q1(a) | `real` | 成功時の T/D/F と receipt bytes は通常不変。変わるのは land journal と crash recovery の受理集合であり、receiptへ provenance を追加するか明記が必要 |
| Q1(b) | `real` | 成功時の台帳値は不変だが、active-aware gate が「apply完了・commit待ち」を受理し、postcommit state を扱える land recovery が新たに必要 |
| Q1(c) | `refuted` | 親の記述は canonical、receipt、main history の欠落を具体的に指しており、空語ではない |
| Q2(a) | `real` | state削除後に base/origin/tested tip が durable artifact に残らないため、「proof chain を台帳から言える」は過大 |
| Q2(b) | `real` | standalone recovery command の受理集合を狭めるが、代替 finalize path を書かない限り成果物を安全に確定できない |
| Q2(c) | `refuted` | wave commit と無関係な main 上で T/D/F と receipt が確定する、という影響は具体的 |
| Q3 | `real` | 1変更に束ねることで中間リリースの受理集合を避けるが、旧v1 state移行と postcommit recovery を同時に解く必要がある |
| Q4 | `real` | `SystemExit(0)` が `_load_rotate_limit` の `except Exception` を抜けると、fold未完了でも land process が rc=0・出力なしになり、成功記録の受理信号が壊れる |

## Q4 の付随所見

`_load_rotate_limit` の `except Exception` は `SystemExit` を捕捉しない。[spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:1806) `check_docs.py` が通常の main guard を持つため現行の本番入力では P3 だが、失敗ゲートが rc=0 に化ける構造は `real`。親の P3 起票は維持してよい。

## 総括

- **Q1 は、親の無条件 `(b)` から `(a)` へ変更すべき。** `(b)` は単なる unlink の延期ではなく、commit済み・state残存という新しい phase と recovery protocol を作る。`(a)` を採る場合も、二つの独立 journal を作らず、phase・commit SHA・起源束縛を持つ一つの authoritative finalize protocol にする必要がある。
- **Q2 は `(a)` を維持するが、optional field の fail-open は却下。** strict schema と旧v1 stateの移行／quarantineを必須にする。`(b)` の一律封鎖は、代替の lock-aware finalize command ができるまで採用しない。
- **Q3 の「同一変更」は維持。** 分割するなら Q2を先にし、Q1を先に出さない。
- **Q4 の P3 起票は維持。**
- 裁定 package に追加すべき問:
  - fold commit 後、state finalize 前に process が死んだ場合の phase と recovery をどうするか。
  - 旧 v1 in-flight state を拒否・再計画・手動 quarantine のどれにするか。
  - base/origin/tested tip/rollback ref を state 以外のどの durable artifact に残すか。
  - land が起動不能または lock busy のときの安全な finalize 経路を何にするか。
  - active-aware gate の受理表を、partial target、mixed GC、rotation、supersede、見送り追記ごとにどう固定するか。
  - C2 の rc=20 と rc=0 の相反する probe log を、どの checkout・コード世代の測定として採用するか。