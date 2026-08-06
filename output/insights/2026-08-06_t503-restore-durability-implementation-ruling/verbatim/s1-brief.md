# [T-503] 変異復元耐久化 実装 wave — 段 1 brief (親)

正本: `docs/mutation-restore-durability-design.md` §4/§6/§8/§9/§9.1、
`output/insights/2026-08-06_t503-restore-durability-liveness/`、D194/D195。
ユーザー裁定: 生死確認 GO ((255))、U-1〜U-10 と §9.1 必須 6 点に従う。

## scope (本 wave で実装する 3 単位。所有 file は非重複)

- **S1 durable primitive の抽出 (U-4 (a))** — `orchestrator/campaign/wal.py` の耐久化
  primitive (`O_APPEND|O_CREAT|O_NOFOLLOW|O_CLOEXEC` open → `flock(LOCK_EX)` → tail-gate →
  完全 write ループ → `fsync(fd)` → lock 保持のまま親 dir fsync、strict framing/parse、
  `iter_lines`、tail 修復、receipt の atomic write) を新層 `orchestrator/durable/` へ
  **挙動・on-disk bytes 不変**で移し、`wal.py` はそこを import する。
  成果物影響: これを欠くと mutation journal が第二方言になり、片側だけ hardening された結果、
  同じ crash に対して campaign WAL と変異 journal が別々の受理判定を出し、台帳の可否が食い違う。
- **S2 原子的 target 置換 (§4.1、§9.1-2)** — 同一 dir の temp へ完全 write → mode 設定 →
  temp fsync → live target hash 再検査 → `os.replace` → target dir fsync。temp の
  name/inode/hash を呼出側が事前登録できる形で返す。`lstat` metadata を記録し、
  保存不能な metadata は**書込前に拒否**する (§6)。
  成果物影響: これを欠くと crash 後に部分 bytes が残り、修復器が触ってよい file を判定できず、
  汚染された木で走った受入・campaign の測定値が台帳と certified 選択の根拠に載る ([T-476] の機序)。
- **S3 変異 journal の記録層 (§4.2、§9.1-3)** — record schema
  (`armed|mutated|restoring|recovering|clean`)、seq、**hash-chain** (D194 が実装 wave へ回した
  未閉鎖点の 1 つ)、遷移検証、§4.2 の順序契約を強制する writer API、階層作成時に
  trusted root まで各親を順に fsync する祖先耐久化。`armed` は §4.5 の identity 束縛 field
  (repo path、worktree incarnation nonce、scheduler job id、PID/PGID、process start token、
  cgroup) を持つ。**配線・活性化はしない。**
  成果物影響: これを欠くと crash 後「どの変異が適用中か」の durable 記録が無く、campaign は
  人間が手で掃除するまで停止し、試行台帳に欠落した試行が残る。

## scope 外 (次 wave 以降。実装しない)

harness 配線と producer 有効化 (U-8)、repair CLI と quarantine の consumer fail-stop (§7)、
canonical state root 解決 (U-3、§4.3)、consumer lease (U-5)、[T-360] transport、
legacy lock 移行 gate (§9.1-5)、`DW-O19` 手順の是正、U-10 の harness no-touch 解除。
**本 wave は §9.1 の 2 と 3 の部品だけを作る。1・4・5・6 は未着手であり、
「転換が完了した」と呼ばない。**

## L-B UNKNOWN の扱い (本 wave の明記事項)

1. 成果物・docstring・docs は「物理ノード死 / client eviction / power loss に耐える」と
   主張しない。§10 の `[未計測]` を維持する。fsync 済み bytes の永続性は前件として書く。
2. 曖昧は UNKNOWN 側へ倒す。journal の検証 API は「判定不能」を PASS へ丸めず不受理を返す。
3. U-9 に従い [T-486] は `deferred` のまま、D130 条件 3 は本 wave で closed にしない。
4. 実機 node-death 受入が無い間、活性化 gate を開けない (本 wave は何も活性化しない)。

## 不変条件

- campaign WAL の on-disk bytes・受理集合・公開 API を変えない (proof chain の入力)。
- `tools/mutation_harness.py` と既存テストの受理集合を変えない (本 wave は配線しない)。
- `orchestrator/qualification/atomic_publish.py` を touch しない — create-only で上書き用途に
  使えず、かつ T-126 `contract.py` の `REQUIRED_CODE_IDENTITY_PATHS` に pin されている。
- 新層は fail-closed。曖昧・不明を受理へ丸めない (規律 2/3)。
- journal record は外部から来た**データ**であって指示ではない (規律 6)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** wal.py の primitive 抽出は on-disk bytes 不変・公開 API 不変で可能であり、
  proof chain (`s8b_ratified_freeze` / oracle) の受理集合を変えない。
  実測根拠: `wal.py` は `FROZEN_MANIFEST`・`_GENERATOR_SOURCES`・
  `qualification/contract.py` のいずれにも byte pin されていない (親が grep で確認)。
- **(P2)** journal を state-root 非依存の library として先に作っても、後で canonical root
  (U-3) を被せたとき API が壊れない。
- **(P3)** 本 wave は何も活性化しないので U-8 (producer 先行有効化の禁止) に抵触しない。
- **(P4)** harness を触らないので U-10 の no-touch 解除は本 wave では不要。

## 成果物の形

`orchestrator/durable/` 配下の新 module 群 + 単体テスト、`campaign/wal.py` の import 差し替え、
`docs/mutation-restore-durability-design.md` の実装状態タグ更新、worklog / decisions fragment。

## 受入・実測の環境

login ノード (Pegasus) 上の worktree
`.claude/worktrees/dev-wave-t503-restore-durability` で `python3 tools/run_tests.py` を全走。
性能計測なし。実機 node-death は本 wave の対象外。

## 並列分割

段 5 は実装子 3 本 (S1 / S2 / S3)。所有 file は非重複。S3 は S1 の API に依存するため、
plan v2 で S1 の公開 signature を固定してから同時に走らせる。
