# [T-1795] attempt 対応の永続証拠 — 二重条件による local recorder の解禁

- wave: `worktree-dev-wave-t1795-attempt-evidence`
- 一次資料: D965 (ユーザー裁定)、D952 (射程限定)
- 起点 commit: `ac9a9ed7feb514fb19f419e4845eb809866d919f`
- 実装 tip (変異・試走を走らせた commit): `bf0ac886c17590e896b7a557d3709d437225dc9b`

## 何を解いたか

変異 harness の attempt sidecar は `--runner-mode dispatch` でしか使えなかった。束ね経路
(dispatch の `--task mutation`) は job の内側が local 実行になるため、attempt 証拠を残せない。
attempt pair を残すと wrapper が停止し、落とすと attempt 対応を失う二択だった (D952)。

D965 はこの二択を閉じる設計 — task 内部からだけ立つ marker と compute site の二重条件で
local recorder を許す形 — を独立 wave で扱うと裁定した。本 wave がその実装である。

## なぜ親から marker を注入できないか (構造的な理由)

`TASKS["mutation"]` は `env_mode="clean"` かつ `env_allowlist` が空である。clean 環境に残るのは
`_CLEAN_CHILD_ENV_KEYS` の 9 key (HOME / LANG / LANGUAGE / LC_ALL / LC_CTYPE / LOGNAME / PATH /
TZ / USER) だけで、marker key はそこに含めない。さらに request の `environment` に allowlist 外の
key があると、compute 側の再検査で child 起動前に拒否される。

**この構造は本 wave が作ったものではなく、既にそこにあった。** 二重条件の片翼は最初から
成立していた、というのが設計上の要点である。

## 実測 1 — 束ね経路の live dogfood (本 wave の中心的な証拠)

計算ノードへ `--task mutation` を 1 回投入し、collection + baseline + 変異 1 件を完走させた。

| 項目 | 値 |
|---|---|
| 外側 job | `963533.nqsv` (request ID)、hostname `bnode084` |
| 外側 request の task | `mutation` |
| 変異 | `tools/spool_fold.py` の filename 照合 gate を無効化 (出現 1 箇所) |
| 変異 matrix | baseline PASSED、KILLED 1 / 1、MISMATCH 0、SURVIVED 0 |
| sidecar schema | `izanagi-dev-wave-mutation-attempts-local/v1` |
| sidecar の attempt | 3 件 (collection / baseline / mutation)、全件 finished、各 `request` は `None` |
| `local_authorization` | marker schema `izanagi-dev-wave-mutation-attempt-marker/v1`、dispatch root、submission dir、`pbs_jobid=0:963533.nqsv`、`hostname=bnode084`、request SHA-256 |

**記録から外側 job への機械的到達を実物で検証した。** sidecar の `submission_dir` から
`request.json` と `compute-visible.json` を読み、次を確認した。

- `request.json` の SHA-256 が `local_authorization.request_sha256` と一致する。
- `compute-visible.json` の `pbs_jobid` と `hostname` が記録と一致する。
- 外側 request の `task` が `mutation` である (= 記録自体が束ね経路由来であることを示す)。
- 外側受領証の `request_id` (`963533.nqsv`) が記録の job ID (`0:963533.nqsv`) に対応する。
- `submission_dir` が記録した dispatch root の内側にある。

これが D952 の言う「attempt 対応の永続証拠」の実体である。

## 実測 2 — 変異 matrix

| 走行 | spec SHA-256 | 結果 |
|---|---|---|
| probe (全件 SURVIVED 期待) | `05d9bd81...` | baseline PASSED、14 件すべて検出、SURVIVED 0 |
| 本走 1 回目 | `7437bc9b...` | baseline PASSED、**KILLED 14 / 14**、matching 14/14。ただし wrapper rc=125 |
| 本走 2 回目 (独立 clone を source) | `7437bc9b...` | baseline PASSED、**KILLED 14 / 14**、matching 14/14、rc=0 |

本走 1 回目の rc=125 は「共有木の事後検査に失敗」であり、**走行中に別 wave の land で main が
`ac9a9ed7f` から `24014bdb2` へ進んだことが原因**である。観測 root には「repo の primary 作業
コピー」が入るので、並行 land が走ると必ず落ちる。自分の worktree は clean のままで漏れは無い。
ただしこの検査の意味は「変異が隔離容器の外へ漏れていないこと」なので、原因が外部でも
「漏れていないと言い切れない」状態になる。そこで**独立 clone を source にして取り直した**。
1 回目の結果は消していない。

### 変異の再照準 (DW-M01 の単一理由性)

登録した 14 件のうち 2 件は、最初の定式化では単一理由にならなかった。

- **site 条件の除去**: 最初の否定テストは現 hostname だけを非 compute にしていたため、
  site 条件を外しても後段の hostname 照合が同じ入力を拒否した。受理集合は変わらず、
  変わるのは診断文字列だけである。DW-M03 はそれを kill に数えない。
  binding・外側証拠・現 hostname の 3 つを同じ非 compute 値へ揃えて再照準した。
  **本走で当該変異はちょうど 1 件のテストで検出された。**
- **marker 不在拒否の除去**: `raise` を消すだけだと `json.loads(None)` が TypeError を投げ、
  拒否の種類が変わるだけになる。「marker 不在時に検証を素通りして admission を通す」形へ
  再照準し、受理集合が実際に広がるようにした。
- **厳密キー検査**: 外すと missing-key 側は後段の直接添字参照で `KeyError` になるため、
  extra-key 側だけを変異の証拠に数える。本走でも `[extra]` の 2 node だけが落ちた。

## 実測 3 — 焦点走

- 焦点 4 file (`test_mutation_attempt_marker.py`、`test_mutation_harness.py`、
  `test_mutation_worktree.py`、`test_pegasus_dispatch_compute.py`): 計算ノードで **491 passed**。
- **同じ焦点走がログインノードでは 5 件落ちる。** 信号処理系のテストは wrapper 子プロセスを
  起動し、ログインノードでは `_refusing_local_site` が即中断させるため `ready` file が作られない。
  main 単独の probe worktree でも同じ 5 件が同じ形で落ちたので**非帰属**と判定した。
  計算ノードへ dispatch された走行では 5 件とも通る。

## 実測 4 — 受入全走

| 走行 | tested main | 結果 |
|---|---|---|
| attempt 1 | `24014bdb2` | rc=70。19072 passed / 5 failed / 21 error / 67 skipped。赤 26 件はすべて `test_codex_reasoning_ab.py` で、本 wave は同 file を 1 byte も変更していない |
| attempt 2 | `dbdacb666` | **rc=0。19083 passed / 92 skipped / 0 failed** |

attempt 1 の赤は非帰属である。現行 main 単独の probe worktree で同じ内訳が再現した。原因は
repo 外へ pin した過去 session の消失で、記録は F20 の再発として残した。修正は編集面の衝突を
避けて別の単独 wave が入れ、本 wave は当該 file を触っていない。

## この機構が保証しないこと (主張せず明記する)

- **条件 A (計算ノードである) は、正規 marker の下では条件 B に含意される。** 正規 marker は
  計算ノード上でしか鋳造されないからである。A を独立した第 2 の権威証拠と呼んではならない。
  A が独立に発火するのは、marker が偽造または持ち出されて非計算ノードで使われた場合だけである。
- **submission dir が dispatch root の内側であることの判定は、binding 内部の整合と canonical 性
  だけを保証する。** `dispatch_root` も binding 由来なので、偽造者に対する権威ではない。
- **同一 UID が計算ノード上で自己整合する偽の submission dir を作れば通る。** 閉じるには marker の
  外側にある信頼根 (scheduler または kernel が保証する job membership) が要り、新機構の追加になる。
  D387 が既に認めている限界と同型である。
- 本機構が実際に閉じるのは、**束ね経路の外で local + attempt を使い、attempt 対応に見える証拠を
  偶発的に作ってしまう経路**である。
- 子は現 PBS job ID を独立に読めない (clean 環境の 9 key に `PBS_JOBID` は無い)。したがって
  陳腐化した binding の実行時検出は構造的にできない。代わりに永続記録で事後監査を可能にした。
- `local_authorization` を読む消費層は本 wave では作っていない。
- 本変更は束ね経路と direct harness の 2 つの entrypoint を同じ条件で開く。direct harness は
  共有 wrapper lock を通らない。

## scope 外として裁定へ返したもの

1. 同一 UID による計算ノード上の意図的な marker 偽造を閉じること。
2. job liveness (過去 job / 終了済み job の拒否)。
3. `local_authorization` を読む消費層。
4. marker module の bytes を harness identity / fan-out 固定集合へ足すこと (T-1946 境界)。

## 成果物の所在

- 変異 spec と台帳、試走の spec / 台帳 / sidecar、検証スクリプトは job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1795-attempt-evidence/` 配下に置いた。
  これらは repo 外の runtime artifact であり、harness の契約 (runtime artifact は試験対象
  checkout の外) に従う。
