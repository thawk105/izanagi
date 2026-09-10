# [T-503] 変異復元耐久化の生死確認実験 — 一次資料と射程

`docs/mutation-restore-durability-design.md` §8.1 が要求する `DW-G01` 最安の生死確認実験の記録。
ユーザー裁定 (2026-08-05 /rulings、worklog (223)) は「着手は `DW-G01` 生死確認実験から
(部分 bytes が出たら NO-GO)」を固定していた。

wave = `dev-wave-t503-liveness` / branch = `worktree-dev-wave-t503-liveness`。
**全 leg を同一 commit `2e0f76bd` で測った** (途中版で測った run2〜run4 は採用しない。理由は下記)。

## 結論 — 機械が導出した判定は GO

`verdict` 副 command が各 leg の実成果物から導出した (親の申告ではない)。逐語は
`evidence/verdict.json`。

| leg | 内容 | 結果 |
|---|---|---|
| **L-A** | 計算ノードの writer が原子的置換まで進み READY で待機 → **別の計算ノード**から armed 可視性と完全 bytes を確認 → SIGKILL → 同じ別ノードから修復 → 別 process で再 open 検証 | **PASS** |
| **L-C** | 正の control。in-place で変異後 bytes の**正確に先頭半分**を書いた状態を同じ検査器にかける | **PASS** (= 検出して隔離した) |
| **L-B2** | walltime 満了で job ごと落とし、scheduler accounting を証拠に別ノードから修復 | **PASS** (proxy) |
| **L-B** | 物理ノード死 (管理者承認の reboot) | **UNKNOWN** (実施していない) |

required leg はコード内定数 `("L-A", "L-C")`。`L-B` は**コード上つねに UNKNOWN** であり CLI から
PASS にできない。`NO-GO` は非 0 で終わる。

### 実測値 (逐語は `evidence/`)

- **L-A**: writer=`bnode004` / inspector=`bnode014` (boot_id も相違)、`cross_client=true`、
  `mount.fstype=lustre`、両 target とも `MUTATED` かつ `size=1048576` (**完全 bytes**)、
  `repair=RESTORED` (`crash_evidence=controlled-sigkill-receipt`)、
  `verify=PASS` (`targets_original=true`, `clean_terminal=true`)。
- **L-C**: writer=`bnode016` / inspector=`bnode017`。両 target とも `OTHER` かつ
  `partial_prefix=true` かつ **`size=524288`** (1 MiB の正確に半分)。
  `repair=QUARANTINE` (rc=4、**無書込**)、`verify` rc=5。
- **L-B2**: writer=`bnode021` / inspector=`bnode004`。
  `repair=RESTORED` (`crash_evidence=scheduler-accounting`)、`verify=PASS`。
  scheduler 側の逐語は `evidence/legB2-scheduler-terminal.txt`
  (`Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)`)。

**部分 bytes は L-A で 1 byte も観測されなかった。** 裁定の NO-GO 条件は成立しない。

## 主張してよいこと / 主張してはいけないこと

### 主張してよい

- 観測した Lustre (`/work`、`st_dev=743766374`) 上で、READY 到達後に writer process を
  SIGKILL した特定の crash 点に限り、**別 node の別 process が durable な `armed` を読め、
  2 file とも完全 bytes であり、原文へ復元して再 open で確認できた。**
- 同じ検査器が「変異後 bytes のちょうど先頭半分」を検出し、**書込前に隔離した**。
  つまり L-A の緑は「何も見ていない緑」ではない。
- allocation 終了 (walltime SIGKILL) 後も、別 node から同じ復元ができた。

### 主張してはいけない

- 物理ノード死、client eviction、OST/MDT failover、電源断後の fsync 永続性、fresh-client recovery。
  **L-B は `UNKNOWN`** であり、L-B2 を物理ノード死の代用にしない。
- 複数 file の旧新混在窓の解消、任意 crash 点、repair 自身が落ちた場合の冪等再開。
- 非協調 consumer の安全性、lease / quiescence、canonical state root と incarnation、
  legacy lock からの移行、本番 journal / quarantine 機構の完成。
- multi-stripe / RPC を跨ぐ耐久性 (stripe 数を gate も記録もしていない)。

### §9.1 必須 6 点との対応

| 必須点 | 本実験の接触 | 判定 |
|---|---|---|
| 1. quiescence の証明 | 特定 writer の終了を試しただけ | **未接触** |
| 2. 原子的 target 置換 | L-A と L-C が直接比較した | **接触** (READY 後の 1 crash 点・file 単位) |
| 3. 祖先 directory の耐久化 | 新規作成した各 directory の親を fsync した (`evidence/*-root-durability.json`) | **部分接触** (既存祖先と power loss は未証明) |
| 4. canonical root + incarnation | 使い捨て CLI root。段 4 の P4 で probe scope 外と裁定 | **未接触** |
| 5. legacy lock からの移行 gate | 機構なし | **未接触** |
| 6. quarantine | exact half の**無書込**拒否を実測した | **部分接触** (consumer fail-stop と repair 途中例外は未証明) |

## 検出力の裏取り — 事前登録した変異 7 件

段 4 で実装前に登録し、以後変更していない (`mutation-spec.json`)。台帳は `mutation-ledger.json`。
baseline rc=0。

| 変異 | 結果 | 赤くなった node |
|---|---|---|
| M1 armed の fsync を最初の target write の後へ移す | KILLED | `test_writer_fsyncs_armed_before_first_target_write` |
| M2 部分 bytes を `OTHER` でなく `ORIGINAL` へ分類 | KILLED (過剰決定) | 期待 node に加え 4 件 |
| M3 修復述語を「1 つでも一致すれば可」へ緩和 | KILLED | `test_repair_refuses_when_any_target_is_other` |
| M4 復元検証より前に `clean` を記録 | KILLED | `test_clean_is_recorded_only_after_restore_verification` |
| M5 temp file の fsync を削除 | KILLED | `test_writer_fsyncs_temp_before_replace` |
| M6 別クライアント要求を削除 | KILLED | `test_cross_node_requirement_rejects_same_host` |
| M7 verdict で `UNKNOWN` を `PASS` に数える | KILLED | `test_unknown_leg_never_counts_as_pass` |

**7/7 が kill された。** M2 だけ台帳上 `MISMATCH` になっているが、これは「期待 node が赤にならなかった」
のではなく、`classify` が共有 primitive のため期待 node に加えて 4 件が同時に赤くなった
**過剰決定**である (`DW-M03`)。単一理由の証拠としては期待 node の赤が成立している。
初回結果は書き換えず台帳のまま残す。

## 実機でしか出なかった食い違い 3 件

いずれも机上のレビューでは出ず、実走で初めて出た。

1. **login ノードでは `tools/pegasus/` を実行できない。** `hooks/guard_bash.py` が拒否する。
   段 1 の (P2)「検査・修復を login ノードで行う」は**実測で refuted**。迂回せず recovery 側も
   計算ノードへ移した結果、writer と recovery が別々の計算ノードになり、要求 (別 process・別ノード)
   を**より強く**満たすことになった。
2. **NQSV accounting の書式が想定と違った。** 見出しは `Request ID:` であり、`PBS_JOBID` は
   `0:890867.nqsv` の形で accounting 側の `890867.nqsv` と文字列一致しない。初回 L-B2 は
   これで fail-closed し (拒否動作自体は正しい)、述語を実書式へ合わせたうえで
   `signal SIGKILL` と walltime 文言の**同一行**要求を足して**厳しくした**。
   正規化は canonical 実装 (`orchestrator/campaign/silo_ladder_rung1.py`) に揃え、
   `0:` 以外の subrequest prefix と Request ID 行の 0 件・複数を拒否する。
3. **recovery job が writer より先に走ると即死した。** script は `ready` を最大 300 秒待つ設計なのに、
   その手前で root を `realpath -e` していた。設計と実装の食い違いであり、投入順の工夫で回避せず
   root 出現待ちを解決より前へ移した。

## 途中版の測定を採用しない理由

run2 (L-A/L-C) は `347da065`、run3 (L-B2) は `a752924b` で測った。`verdict` は
writer-info の `probe_sha256` が現行 probe と一致することを受理条件にするため、
**版が混ざった leg 群を合成すると証拠が正当でも FAIL になる**。焦点再レビューがこれを指摘し、
親は「全 leg を同一 commit で測り直す」を選んだ。採用するのは run5 (`2e0f76bd`) だけである。

## 敵対レビューで閉じきらず、実装 wave へ回す所見

probe が**自分で作った証拠を自分で検証している**ことに由来する。probe 単体では原理的に閉じない。

- **kill provenance の独立 anchor** — `record-crash` は caller が渡した wait status を信じる。
  「READY → inspect → 実 kill 完了 → repair」の因果鎖は receipt だけでは証明できず、
  PBS accounting と commit hash を人間が突き合わせる前提が残る。
- **journal の hash-chain** — seq・遷移・record 型は検査するが chain は無い。inspect 後に
  armed の原文 bytes を差し替える攻撃を拒否できない (設計 §4.2 の `[要求]`)。
- **既存祖先 directory の耐久性** — 新規作成分しか fsync していない。外部で作られた root の
  親は触らない。power loss 後の namespace 残存は未証明。
- **repair 途中 crash からの再開** — `recovering` を append した直後に repair が落ちると、
  状態機械は valid と認めるのに repair が `records[-1] != mutated` で隔離する。過剰拒否。
- **PBS 実 kill 経路を通る正例** — 単体テストの正例は `run_writer()` を直接呼び、
  実 CLI・blocking writer・PBS の kill/wait を通らない。

## 再現手順

```
# writer (計算ノード)
qsub -v T503_ROOT=<root>,T503_MODE=atomic,T503_KILL_MODE=sigkill \
     tools/pegasus/probes/t503_restore_durability_probe.pbs
# recovery (別の計算ノード。同一ノードなら exit 7 で止まるので再投入する)
qsub -v T503_ROOT=<root>,T503_LEG=L-A \
     tools/pegasus/probes/t503_restore_durability_recover.pbs
# 判定 (計算ノード。leg 区切りの ; は escape する)
qsub -v T503_VERDICT_ROOT=<vroot>,T503_LEG_ROOTS="L-A=<a>\;L-C=<c>\;L-B2=<b>" \
     tools/pegasus/probes/t503_restore_durability_verdict.pbs
```

L-B2 は writer を `-l elapstim_req=00:04:00` と `T503_KILL_MODE=walltime` で投入し、
job 終了後に `<root>/scheduler-terminal.txt` へ NQSV の `.e` ファイルを置いてから recovery を投入する。
