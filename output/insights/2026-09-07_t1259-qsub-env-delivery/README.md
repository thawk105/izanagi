# [T-1259] qsub -v の env 到達と NQSV の ambient 継承 — 一次資料

wave branch = `worktree-dev-wave-t1259-qsub-env-delivery`
着手時 main = `442cb549c`
authority: none / default_effect: no-state-change

## 1. 要点

計算ノードで 3 request を実走し、[T-1259] が問うた 2 点を実測した。**official 床値走行は投入していない。**
`floor_campaign.sh` と `s8b_floor_campaign.py --mode official` の campaign 本体は起動していない。

| 問い | 実測の答え |
|---|---|
| `qsub -v` の 2 本目は計算ノードへ届くか | **届く** |
| 3 本目は届くか | **届く** |
| 2 本構成でも届くか | **届く** |
| NQSV は `-v` 指定外の ambient env を継承するか | **継承しない** |
| **承認変数名そのもの**は ambient 継承するか | **継承しない** |
| 同名が `-v` と ambient の双方にあるときどちらが勝つか | **`-v` が勝つ** |
| 承認なしで実 driver を起動するとどうなるか | **argv 完全一致のまま rc=2 で拒否される** |

**[T-2324] が着地させた §8 承認束縛は、この経路では黙って拒否されない。**
R1 の §8 射影は `approval-bound` / `confirm_flag_would_be_appended: true` に落ちた。
「2 本目が届かないせいで official 床値の投入が無駄になる」という懸念は、実測上は起きない。

ambient 継承が無いことは、**承認 env が投入側 shell から漏れて計算ノードへ届く経路が
存在しない**ことも意味する。

## 2. 実行 identity

- 実測 commit: `1813aa312b26d75b8c4050c6f26b8654a3e02175` (probe・PBS・投入 script はこの HEAD に束縛)
- 投入元: 固定 SHA の detached submit-tree
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1259-qsub-env-delivery/submit-tree`、D1643)
- attempt: `/work/1/SFC/tanab/izanagi-job-evidence/t1259/attempt-20260908c`
- request と実行ノード

  | request | scheduler request | ノード | ok |
  |---|---|---|---|
  | R1 承認あり (`-v` 3 本) | `982468.nqsv` | `bnode011` | true |
  | R2 承認なし (`-v` 3 本) | `982469.nqsv` | `bnode001` | true |
  | R3 ambient のみ (`-v` 2 本) | `982470.nqsv` | `bnode011` | true |

- 3 request とも `repo_working_tree_unchanged: true`。

### 先行 attempt

`attempt-20260908a` の R1 (`982424.nqsv`、`bnode011` ではなく `bnode008`) も同じ結論を出している。
これは投入 script の受理検査が落ちる前に実際に投入された request で、
**別ノード・別時刻で 1 本目の結論が再現している**。
`attempt-20260908b` の R1 (`982450.nqsv`) も投入されたが、結果は本 README の主張に使わない。

## 3. 何を測ったか — 3 request の設計

| request | `-v` の中身 | 投入 shell の ambient |
|---|---|---|
| R1 | nonce, approval=nonce, evidence root (3 本) | sentinel のみ |
| R2 | nonce, probe 固有 hex, evidence root (3 本) | sentinel + **同名の別 hex** |
| R3 | nonce, evidence root (**2 本**) | sentinel + **承認名に nonce と一致しない固定 literal** |

- R1 は `tools/pegasus/submit_floor.sh:632-638` が最大構成で作る exact 3 名と同じ値の形
  (32 桁 hex 2 本 + 絶対 path 1 本) である。
- R3 の ambient 承認値は 32 桁 hex ではない固定 literal であり、届いても
  `tools/pegasus/floor_campaign.sh:559` の exact 一致検査を通らない。
- **ambient の陽性対照**: sentinel は attempt ごとの乱数で、投入 process が実際にそれを見たことを
  create-only の submission manifest に記録している。したがって job 側の不在を
  「継承しなかった」と「export し忘れた」に分離できる。

## 4. 実測値

### 4.1 明示 `-v` の到達 (投入側の値との exact 比較)

| request | 1 本目 | 2 本目 | 3 本目 |
|---|---|---|---|
| R1 | `IZANAGI_SUBMISSION_NONCE` 32 byte 一致 | `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` 32 byte 一致 | `IZANAGI_FLOOR_JOB_EVIDENCE_ROOT` 88 byte 一致 |
| R2 | 同 32 byte 一致 | `T1259_QSUB_SECOND_HEX` 32 byte 一致 | 82 byte 一致 |
| R3 | 同 32 byte 一致 | (なし) | 87 byte 一致 |

比較は存在検査ではなく、**投入側が `-v` 文字列を組むのと同じ shell 変数から書いた
create-only manifest との byte 一致**である。

**到着順序は測っていない。** `os.environ` から `-v` の並びは復元できない。
manifest が持つのは投入 argv に書いた順序だけであり、result にもそう明記してある。

### 4.2 ambient 継承

3 request すべてで `submitted_process_present: true` / `job_present: false`。
**投入 process には確かに存在した固有名の変数が、計算ノード側には 1 件も届かなかった。**

R3 では承認変数名そのものを投入 shell に置いたが、job 側は `present: false` だった。
§8 射影は `ambient-approval-not-delivered-unbound` に落ちた。

### 4.3 同名が `-v` と ambient の双方にある場合

R2 は `-v` に `T1259_QSUB_SECOND_HEX=<hexC>` を載せ、投入 shell に別の `<hexD>` を export した。
job 側が観測したのは `-v` の値である。**`-v` が勝つ。**
(ambient がそもそも継承されない以上、これは 4.2 の系でもある。)

### 4.4 承認なしの実 driver

R2 だけが実 driver を起動した。

- argv は固定契約と完全一致 (`argv_exact_match: true`)、承認 flag 不在。
- rc=2、stdout は単一 JSON `{"status": "refused", "reason": "official mode は
  --confirm-official-floor-run による 明示承認がないため拒否する"}`、stderr 空。
- protocol file は**前後とも不在** (`protocol_loader` へ到達していない)。
- scratch の entry 集合は前後で不変。
- campaign source の sha256 は expected / before / after の 3 値が一致。

## 5. 依頼の前提を 1 件反証した

[T-1259] の原文と親 brief は「[T-2228] の 2 本渡し実績が『2 本目は届く』を被覆している」と
書いたが、**これは循環していた。** T-2228 の 2 本目必須化とその先の成果物実在が示すのは
「2 本目の値が job 側に存在した」ことだけで、**その値が `-v` の 2 番目 field で運ばれたのか、
ambient 継承で届いたのかを識別できない**。ambient 継承の有無が未確定である以上、
前者の証拠にはならない。段 3 の 2 レンズが独立に反証した。

本 wave は 1・2・3 本目すべてを新規の直接観測として扱った。
なお 4.2 の実測 (ambient 継承なし) が確定した今、遡って T-2228 の 2 本目は `-v` 由来だったと
言えるが、**それは本 wave の測定によって初めて言えることである**。

## 6. 親 brief のもう 1 件の誤り

brief は「ambient 継承するなら承認束縛の前提そのものに関わる」と書いたが**過大**だった。
`tools/pegasus/submit_floor.sh` の実投入 guard は shell 内部変数
`CONFIRM_OFFICIAL_FLOOR_RUN` を見ており、これを 1 にするのは CLI 引数だけである
(`:33,44-46,84-87`)。ambient の `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` は guard 判定に
一切使われない。**ambient 継承の有無にかかわらず標準 submitter の引数必須性は不変である。**
影響が及ぶのは raw `qsub` の非標準経路だけで、そこは runbook §8 と D926 が既に保証外と明記している。

## 7. 投入 script を repo の実行体にしなかった理由

`docs/pegasus-runbook.md` の分類規定により、

- `local-ok` の grandfather は 4 本限りの例外で、他 entry を `local-ok` にするには実測が要る、
- **AI セッション・子エージェント・自動化は分類の実測を自分で行わない**、
- hook は `tools/pegasus/` 配下の登録 path のうち `local-ok` でないものを login で拒否する。

したがって投入 script を `tools/pegasus/` の実行体として置くと循環する。repo の別 subtree へ
逃がすのは runbook が明示的に禁じる迂回である。**[T-2228] の前例に合わせ、投入 script は
repo の実行体にしない。** repo には shebang なし mode 644 の
`tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh.txt` として置き
(`orchestrator/tests/test_hooks.py` の execution inventory は
「拡張子 `.py`/`.sh`/`.pbs`」「実行 bit」「先頭 `#!`」のいずれかで実行体と数えるので、
この 3 条件を外すと数えられない)、親が repo 外へ退避して実行した。

**正直に記す限界: repo 外で走る投入 script は単体検査で守られない。** 守るのは敵対レビューだけである。

## 8. 変異 matrix

`mutation-spec-final.json` (sha256 `80e42174741ba0323d0e19434dc3b3efee7b01f6b7bf466022e335718a34c3ea`) を
`tools/mutation_harness.py --runner-mode dispatch --detached` で走らせた。

- **本走: baseline PASSED、KILLED 9、SURVIVED 1 (事前登録どおり)、MISMATCH 0、TIMEOUT 0、
  PARSE_ERROR 0。期待 node 完全一致 10/10。** 走行時 HEAD は `e43da7655`。
- runner argv は `python3 tools/run_tests.py --force-dispatch
  orchestrator/tests/test_t1259_qsub_env_delivery_probe.py orchestrator/tests/test_hooks.py -q -rf`。
- probe 走は 2 巡ある。1 巡目 (10 件) で 5 件が SURVIVED、2 巡目 (4 件) は新しい負例を足した後の
  観測 node 収集である。

### 変異だけが暴いたこと

**1 巡目で 5 件が生き残った。うち 3 件は規律 2 の中心にあった。**

- 未承認 driver の argv に `--confirm-official-floor-run` を混ぜてもテストは緑のままだった。
- argv の完全一致を先頭 3 要素だけの一致に緩めても緑のままだった。
- R1 の「承認値が nonce と一致する」検査を骨抜きにしても緑のままだった。

fix の報告は「負例を追加した」と書いていたが、**その負例は実際にはこれらの述語を通っていなかった**。
**段 3 の敵対相談 2 本、段 6 の敵対レビュー 2 本、焦点再レビュー 1 本のいずれもこれを
見つけられていない。変異だけが暴いた。**

M4 (projection の categorical 値と 2 つの bool の整合 invariant) は、到達可能な入力で
不整合を作れない等価変異である。負例を作らず SURVIVED 期待として登録した。

## 9. 実機だけが暴いたこと — 合成 fixture の限界

投入 script の qstat 本文照合が、**状態列でなく Pri 列を読んでいた**。
実測した本文の field 番号は `0=RequestID 1=ReqName 2=UserName 3=Queue 4=Pri 5=STT` であり、
実装は index 4 を状態として読んでいた。

**合成 fixture で書かれた既存 test は STT を index 4 に置いていたため、旧実装でも緑だった。**
実機の `qstat` 本文を 1 度も通していない検査だったということである。
実測した 3 行を逐語 fixture として入れて閉じた。

同じ実走で、親が段 6 に書いた受理述語 `accepted_states = ("QUE", "RUN")` が
**投入直後の実測値 `STG` に到達しない**ことも分かった。`DW-O13` (field の実在では足りず、
実環境で取りうる値を実測してから述語を採る) に従って
`("STG", "ARR", "WAI", "QUE", "PRR", "RUN")` へ広げた。
**実測できたのは `STG` の 1 値だけで、残りは `qstat -Q` header 由来の未実測候補である。**

## 10. 緑でも言えないこと

本 probe の結果が緑でも、次はいずれも言えない。

- `submit_floor.sh` が実際にその request の qsub argv を生成したこと。
  本 probe は raw `qsub` を直接呼んでおり、sanctioned な投入経路を通っていない。
- probe の全 ambient env と official wrapper の qsub process env が同一であること。
- `floor_campaign.sh` §8 が実行され、実 argv に承認 flag が 1 個追加されたこと。
  **§8 は実測 env への source 射影であって shell を実行した観測ではない。**
- 承認ありの実 driver が CLI・public gate・private gate を通過すること。
  承認あり側の実 driver は起動していない。
- official campaign が build・claim・計測・result materialize まで完走すること。
- ambient 継承が全変数・全 node・全時刻・他 queue でも同じであること。
  測ったのは 1 つの固有名と承認名の 2 つ、gen_S の 4 request、2026-09-08 の 1 時点である。
- 3 要素以外の個数・別順序・別長・comma を含む値・空値・重複名へ一般化できること。
- raw `qsub` の観測が D926 の認証済み official 投入を構成すること。
- repo および scheduler 全体に副作用が皆無であること。
  保証するのは「repo working tree へ file を作らない・変えない」までで、
  scheduler が持つ spool は閉包の外である。

## 11. 3 request の読み方

group intent と request receipt は投入側が create-only で残す。
**terminal state と結果 hash を確定する機構は作っていない** (ユーザーが台帳の追加を
scope 外と明示したため)。回収は親が job 終了後に行い、本 README へ書いた。

**3 request の 1 本でも欠ければ全体を `indeterminate` と読む。**
ambient 判定が R1/R2/R3 で食い違う場合も同じである。本 attempt では 3 本とも揃い、
ambient 判定は 3 本とも一致した。

## 12. 検査と実測

- 焦点走 (親の実走): `test_t1259_qsub_env_delivery_probe.py` + `test_hooks.py` +
  `test_plain_runner_coverage.py` が **528 passed / 1 skipped**。
- `tools/check_docs.py`: rc=0。
- 変異本走: KILLED 9 / SURVIVED 1 / MISMATCH 0、期待 node 完全一致 10/10。
- 計算ノード実測: 3 request すべて `ok=true`、2 ノード (`bnode011` / `bnode001`)。
- **受入全走は記録 commit の後に投入する契約なので、その結果は本 README には入らない。**
  所在は session の報告と land の受領証である。

## 13. 成果物

| 段 | 成果物 |
|---|---|
| 1 | `s1-brief.md` (§0 で 2 件自己訂正) |
| 2 | `verbatim/s2-plan.md` |
| 3 | `verbatim/s3-consult-lensA.md` (承認束縛と正しさ境界)、`verbatim/s3-consult-lensB.md` (測定設計と干渉) |
| 4 | `s4-adjudication.md` (P1 確定、3 request 設計、変異事前登録) |
| 5 | 実装 (Codex author、commit `0bb6e9209`) |
| 6 | `verbatim/s6-review-A.md` (must-fix 6)、`verbatim/s6-review-B.md` (must-fix 8)、`verbatim/s6-focus.md` (must-fix 4) |
| 6 | `s6-adjudication.md` (9 系統の裁定)、fix 5 巡 |
| 6 | `mutation-spec-probe.json` / `mutation-ledger-probe.json` / `mutation-spec-probe2.json` / `mutation-ledger-probe2.json` / `mutation-spec-final.json` / `mutation-ledger-final.json` |
| 7 | `evidence/` (3 request の result・manifest・qsub/qstat 生出力・group intent) |
