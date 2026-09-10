## 同型の時限装置の全件列挙

対象 3 ファイルを全行走査した。`head` などの件数制限は使っていない。

- 絶対 path らしい文字列: テスト 58 箇所、ツール 36 箇所、hold 実装 0 箇所
- `/home/`: 3 箇所
- `/work/`: 2 箇所
- `CODEX_HOME`: 15 箇所
- `~/.codex`: 1 箇所
- 固定日付: 7 箇所

実際に環境側の削除で失効する読み込み依存は、2 系統、6 artifact だった。

### 既に失効した 5 rollout

1. POS `019faca2-...`

   - 実体: [test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:145)、[codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/tools/codex_reasoning_ab.py:197)
   - 2026-07-29 15:49 JST。固定 path のほか prompt 入力として要求される。

2. NEG `019facbe-...`

   - 実体: `tools/codex_reasoning_ab.py:198,205,3703-3716`
   - 2026-07-29 16:19 JST。NEG prompt の生成に必要。

3. fix2 `019facb2-...`

   - 実体: `tools/codex_reasoning_ab.py:199,206,935-960`
   - 2026-07-29 16:06 JST。reverse route の patch 抽出に必要。

4. author `019fac6b-...`

   - 実体: `tools/codex_reasoning_ab.py:200,207,935-970`
   - 2026-07-29 14:49 JST。親実測の rollout count 0 の直接原因。

5. fix1 `019fac91-...`

   - 実体: `tools/codex_reasoning_ab.py:201,208,935-970`
   - 2026-07-29 15:30 JST。independent route の patch 抽出に必要。

5 ID とも現存 session tree に filename 一致は 0 件だった。POS と author は親実測でも欠落が確定している。全て 2026-07-29 生成であり、削除済みの `2026/07` に属する。

ツールの既定値も `CODEX_HOME/sessions` または `~/.codex/sessions` を使うため、同じ 5 個の pin を CLI から利用する経路も既に失効している。

- 実体: `tools/codex_reasoning_ab.py:12091-12096,12127,12136,12170`

### これから失効しうる 1 artifact

6. 別 wave の stage 2 plan

   - 実体: `orchestrator/tests/test_codex_reasoning_ab.py:396-399,9971-9975`
   - `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/s2-plan.md`
   - 現在は存在し、393 bytes。`dev-wave-jobs` の cleanup が入れば 1 node が決定的に赤になる。削除日は不明。

### 時限装置ではなかった候補

- `OLD_ROOT` の `/home/...` は file open ではなく prompt 内 path の置換対象。

  - 実体: `tools/codex_reasoning_ab.py:190-194,3729-3737`

- `2026-07-29...` と `2026-08-09...` の repo 内 artifact は Git 管理済み。対象 2 directory では 24 files が tracked だった。

  - 実体: `test_codex_reasoning_ab.py:129-142,12787-12794,12812-12818,12999-13005`

- `/bin/sh`、`/usr/bin/env`、`/usr/bin/bwrap`、`/tmp/...` の多くは fake executable、sandbox argv、毒値であり、日付 cleanup 依存ではない。

## 保持窓の一般化可否と次に壊れる日付

**B-04 / refuted**

7 月が 2026-09-01 00:54 に消え、8 月 01〜31 が残ったという 1 境界だけから、保持日数や「日ごとの失効」は一般化できない。月単位 cleanup、一定日数、容量制限、手動削除の区別がつかない。

特に 7 月全体が消え、8 月 01 日分も残っている観測は、「毎日 1 日ずつ消える」と断定する根拠にならない。

判定に必要な追加計測は次のとおり。

- 8 月 01 日と 8 月 31 日が同時に消えるか、別日に消えるか
- 最古 surviving session の作成日時を日次で記録
- cleanup の実行時刻、timezone、対象判定が path 日付か mtime か
- 次の削除を最低 2 回観測するか、cleanup 実装・設定・ログを確認

射影されたテストとツールには、`2026/08/.../rollout-...` という固定 session path は **0 件**。したがって、repo 内の固定 session 参照から算出できる「次に壊れる日付」はない。

月単位 cleanup なら 2026-10-01 頃という仮説は立つが、実測値としては提示できない。8 月日付を含む外部 plan はあるが、その cleanup 周期も不明。

## 案 1 の恒久性

**B-06 / refuted**

`_REAL_ROLLOUT.exists()` だけを見る案は持たない。要求対象は 1 path ではなく 5 rollout だからである。

- author/fix1/fix2: `tools/codex_reasoning_ab.py:935-970`
- POS/NEG: `tools/codex_reasoning_ab.py:3703-3716`
- fixture 呼び出し: `test_codex_reasoning_ab.py:787-825`
- fixture 外の golden: `test_codex_reasoning_ab.py:3128-3140`
- fixture 外の POS rollout: `test_codex_reasoning_ab.py:8575-8617`

現在の赤は session 依存の 26 items に分かれる。

- module fixture に依存する test function: 21
- fixture 外: `test_m2` 1、parametrized prompt 3、source-bound collector 1

node ごとに path を手書きする必要はない。`TASK_MANIFEST` の POS/NEG provenance と `shared_provenance.auxiliary_sessions` から 5 pin を列挙し、共通 fixture が `_find_rollout` で preflight する設計なら一元化できる。

ただし、全 26 items にその fixture または marker を配線する必要がある。新しい直接参照 node が追加されると追随が必要であり、外部 plan の別時限装置も残る。また欠落時には 26 items が永久に skip され、重要な mutation・golden coverage が失われる。

将来 8 月 rollout が manifest に追加された場合、manifest 駆動の共通 preflight なら吸収できる。個別 `_REAL_ROLLOUT` guard では吸収できない。

## repo 内凍結案の可否

**B-08 / real**

raw rollout をそのまま commit する案は、現時点では採れない。

- 元の 5 rollout が既に消えており、現在の workspace から凍結できない
- session ID は既に source 内にある
- token 数、rate-limit、plan type は既に `test_codex_reasoning_ab.py:150-162` に露出している
- POS/NEG prompt 本文は現在は hash と長さだけで、raw rollout の追加は新しい本文開示になる
- rollout には prompt、agent message、tool input、cwd、token・rate-limit 情報が含まれうるため、無審査の full copy は不適切

サイズは source 消失後なので測定不能。コードから分かる最小量は次のとおり。

- POS/NEG prompt: 6,485 bytes
- token slice: 778 bytes
- stage 2 plan: 393 bytes
- 既知最小量: 7,656 bytes
- これに author/fix1/fix2 の patch event、manifest、JSONL framing が加わる

`FROZEN_MANIFEST` という識別子は射影対象内に存在せず、repo 全体の凍結契約との完全な整合は確認できなかった。射影内では repo-relative path と SHA-256 を組にする契約が既にある。

- 実体: `tools/codex_reasoning_ab.py:174-188`
- session/prompt provenance: `tools/codex_reasoning_ab.py:196-223`

成立する形は raw copy ではなく、次の最小・審査済み fixture である。

`orchestrator/tests/fixtures/codex_reasoning_ab/t181/`

- `manifest.json`
- `prompts/POS.txt`
- `prompts/NEG.txt`
- `rollouts/author.min.jsonl`
- `rollouts/fix1.min.jsonl`
- `rollouts/fix2.min.jsonl`
- `token-count/POS.jsonl`
- `stage2/s2-plan.md`

manifest には少なくとも `path`、`bytes`、fixture SHA、元 rollout SHA、元 session ID、許可 row type、redaction profile を持たせる。元データとの逐字照合は、元データが存在するときだけ動く acceptance 外の provenance audit に分離する。

## 他 wave への影響の確定

**B-10 / real**

親の受入全走では対象 file が実際に collection され、21 errors + 5 failures を出した。同じ tip・同じ full-suite collection を使う wave は同じ赤で止まる。DW-O18 上、既存 F がない決定的赤は hold 登録できず、受領証も発行できない。

現在の hold registry は完全 node ID の exact match で除外する設計だが、登録済みは別 file の 1 node だけである。

- exact node 契約: [flaky_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/flaky_test_holds.py:1)
- F 必須: `flaky_test_holds.py:142-161`
- 現在の唯一の hold: `flaky_test_holds.py:200-238`

**B-11 / refuted**

「以後すべての wave に必ず入る」という無条件の主張までは確定できない。runner と collection 本体が必読射影に含まれていないため、shard、明示 deselect、file filter の有無を検査できなかった。

確認できた非収集経路は exact hold。現状では対象 node に hold はない。shard・deselect 経路は数えられなかった。

したがって確定表現は、「同じ acceptance-full-suite collection を使う wave は全て止まる」である。

## 案の比較 (持続期間)

| 案 | 次に同じ外部失効で止まるまで | 評価 |
|---|---:|---|
| 案 1: 個別 guard | 配線漏れがあれば即時。完全配線なら session 欠落では止まらないが 26 items を永久 skip | 赤隠しとしては長寿命、回帰検査としては劣化 |
| 案 2: hold | 現状 0。既存 F 不在で契約上登録不能 | 採用不能。仮に例外登録しても node 追加・改名へ追随 |
| 案 3: home へ復元 | 次の cleanup まで。期間不明で、別 host では即時失敗 | 最も環境依存が強い |
| 案 4: repo 内の最小・審査済み fixture | session・job retention では失効しない。次は明示的な repo 契約変更時 | 最長 |

## 推奨と、採らない案の理由

**推奨は案 4、repo 内の最小・審査済み fixture への置換。**

raw rollout 全体ではなく、テストが実際に必要とする prompt、patch event、token slice、stage 2 plan だけを manifest と SHA で凍結する。これだけが session cleanup と `dev-wave-jobs` cleanup の両方を閉じ、skip で coverage を失わない。

- 案 1は応急処置にはなるが、26 items の永久 skip または配線追随を残す。
- 案 2は DW-O18 と registry validator に反する。
- 案 3は同じ cleanup 面へ戻すだけで、portable でも恒久でもない。
- raw rollout の直接 commit は prompt 本文などの機微情報審査を通していないため採らない。

## 所見一覧

| ID | 判定 | 実体 | 影響 |
|---|---|---|---|
| B-01 | real | `test_codex_reasoning_ab.py:128,145-148`; `tools/codex_reasoning_ab.py:196-208` | 5 rollout は既に失効し、26 items を赤にする |
| B-02 | real | `test_codex_reasoning_ab.py:396-399,9971-9975` | 外部 plan cleanup で次の決定的赤になる |
| B-03 | refuted | `tools/codex_reasoning_ab.py:190-194`; test `:129-142` | OLD_ROOT と tracked date artifact は session 保持期限では失効しない |
| B-04 | refuted | blocker evidence の削除 1 点 | 1 境界から保持日数や日次 pruning は一般化できない |
| B-05 | real | test `:133,141,406`; tool `:194` | 射影範囲の固定 8 月 session path は 0 件 |
| B-06 | refuted | test `:787-825,3128-3140,8575-8617` | `_REAL_ROLLOUT` 単独 guard は必要な 5 pin と全 node を覆わない |
| B-07 | real | tool `:925-970,3671-3716` | manifest 駆動 preflight なら個別 path 手書きは避けられる |
| B-08 | real | test `:150-162`; tool `:196-223` | raw rollout の commit は prompt 本文などの追加開示を伴う |
| B-09 | real | tool `:174-188` | repo-relative path、bytes、SHA を持つ最小 fixture は retention から独立できる |
| B-10 | real | blocker evidence; hold `:200-238` | 同じ full-suite collection の wave は全て止まる |
| B-11 | refuted | hold `:1-4`; runner は射影外 | 全 wave 必須 collection、shard、deselect の不存在までは証明できない |
| B-12 | refuted | hold `:142-161`; DW-O18 | 既存 F がない案 2 は契約上成立しない |

## 総括

現在の赤は単一 path の事故ではなく、5 rollout と別 wave plan の計 6 artifact を repo 外の cleanup 面へ委ねた設計問題である。保持窓は未確定で、次の失効日も算出できない。

最も長く持つのは、機微情報を絞った repo 内 fixture と manifest に acceptance を切り替え、外部原本との照合を任意の provenance audit に分離する案 4 である。pytest は実行しておらず、所見は静的検査と親の実測に基づく。