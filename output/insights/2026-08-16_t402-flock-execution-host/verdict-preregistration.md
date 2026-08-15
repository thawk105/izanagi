# [T-402] 実測前の判定式凍結 (verdict pre-registration)

**凍結日時:** 2026-08-16 (JST)。**この文書は probe を投入する前に commit する。**
実測後にこの文書を編集してはならない。訂正が要る場合は初回凍結文を消さず
`verdict-preregistration-erratum-N.md` を追加する ((191) の先例に従う)。

対象タスク = [T-402] (= [T-361] / D130 条件 2)。
目的 = `bnode` 2 台の間で `/work` と `/home` の `flock` が silent fail-open しないことを、
`qstat -J -f` の Execution Host と compute node の job marker を一対一照合したうえで確定する。

---

## 1. なぜ再走が要るか (実測済みの事実)

2026-08-03 の attempt (request 882038) は `/work`・`/home` とも cross-node 6/6 `BLOCKED` を
観測したが `dangerous` は `null` のままだった。その原因は本 wave の段 4 で実測確定した。

1. **実際の `qstat -J -f` の書式は `Request ID:` block 内の単数形 `Execution Host = <host>`** である。
   証拠 = `output/insights/2026-08-03_t361-t362-cluster-probes/evidence/`
   `20260804T125421Z-5e03df98c93b444e/attempts/t362-mitigation/`
   `20260804T125421Z-t362-mitigation-a1-2a754178cd1a19d9/work/controller/raw/`
   `00025-lifecycle-qstat-attempt-1.stdout.raw`
2. **旧 parser が fullmatch を要求していた `Execution Hosts(JSVNO):` は、
   保存 evidence 全体で出現 0 件**である。
3. **健全な走行でも host が 1 件も取れていなかった。** 上記 request 887918 は完走し
   authoritative と判定された attempt だが、`attempt-result.json` の
   `monitor.execution_hosts_raw_order` は `[]`、`execution_hosts_raw_evidence` は `null`。
4. 2026-08-03 の attempt の保存 raw は `rbudgetcheck` / `qsub` / `qwait` の 3 command だけで、
   **qstat には一度も到達していない**。

したがって「controller の NameError が原因」という当初の見立ては誤りであり、
**parser を直さない限り何度再走しても結果は `null` である**。

## 2. 既知の不確実性 (実測前に明示する)

**2 job 構成の `qstat -J -f` 実出力は手元に無い。** 上記 §1 の実測は 1 job の request である。
2 block の区切り方は外挿であり、実装は「寛容に読み、判定は fail-closed」で吸収している。
**正当な 2 job 出力を過剰拒否して `dangerous: null` に終わる可能性は残る。**
その場合も安全側へ倒さず、事実をそのまま記録する。

## 3. 凍結する判定式

```
A := observation_valid is True ∧ external_root_terminal_proven is True
H := 対象 request の qstat block がちょうど 2 件
     ∧ job number 集合 = {0, 1}
     ∧ 2 host が相異なる
     ∧ 各 marker の (job_number, host) が qstat 写像と一致
     ∧ marker の request ID が対象 request と一致
     ∧ marker がちょうど 2 件、全件 parse 成功
S := overall と work / home の probe self-checks がすべて literal true
E := どちらの mount にも localflock が無い
B := work / home それぞれの raw outcome が「ちょうど 6 件の closed-enum 文字列」かつ全件 BLOCKED
     (controller が raw から再導出したもの。producer の派生 field は判定に使わない)
```

**三値判定:**

| 条件 | `dangerous` |
|---|---|
| `A ∧ H ∧ S ∧ E ∧ B` | **`false`** (この tuple では危険でない) |
| `A ∧ H ∧ S ∧ (¬E ∨ ¬B)` | **`true`** (危険側。詳細 verdict は失わない) |
| `A`・`H`・`S` のいずれかが不成立・欠測・矛盾 | **`null`** (判定不能) |

**`attempt_safe` をこの authority 連言へ加えない。** D161 の証拠 3 分離
(`observation_valid` / `attempt_safe` / `admissible`) を維持し、
**危険側の観測も authoritative になれる**性質を守る。これは 2026-08-04 に
「cleanup が走らないという危険な結末そのものが `admissible: false` を生む」欠陥を出した
反省に基づく (エントリ 149)。

## 4. 読まない観測 / 安全側へ倒さないこと

- 自己検査 (S) が不合格の実行の観測は**読まない**。後から安全側へ倒さない。
- `localflock` は**危険側の陽性所見**である。自己検査不能 (`null`) へ畳まない。
- 欠測・型不正・矛盾は `null` のままとし、既定値で埋めない。
- 前回 (2026-08-03) の `BLOCKED` 6/6 や当時の marker を、今回の結論の補完に使わない。
- host を取り逃して `null` に終わっても、**同一 wave 内で自動再試行しない**。

## 5. 結論の射程 (実測前に固定する)

- 得られる結論は「**この attempt で実測した exact host pair・当日 kernel・当該 mount signature**」
  に限る。**`bnode001` / `bnode005` に固定しない** — PBS に host selector は無く、
  scheduler が別の 2 host を割り当てうる。
- **gen_S 全体へ一般化しない。** 将来の kernel・mount 変更にも一般化しない。
- **この結果だけでは D130 条件 2 は閉じない。** 条件 2 が要求するのは
  「同一 repo で同時 1 本」の保証が bnode 間で成立することであり、
  1 host pair の 1 回の観測はその十分条件ではない。
- **D131 共通前提 1 (shared / legacy lock の移行と、移行期間に二重走行の窓を作らないこと) も
  閉じない。** 本 wave は移行窓に一切触れない。

## 6. 資源の上限 (実測前に固定する)

- 投入は **`t361-flock` の 1 request だけ**。`--flock-leg-only` を必ず指定する。
- `t362-mitigation` は既に authoritative であり**再投入しない**。
  `t362-default` / `t362-split-warning` も本 wave では投入しない。
- controller の既存 gate (request 上限 6 / requested node-min 上限 40) を弱めない。
  投入前の消費は request 4 / node-min 19 であり、本走後は 5 / 29 になる見込み。
- 初回 4 request の point gate は、**wave-state に記録済みの 313.97 → 306.37 (減少 7.60)** を
  入力とする。**投入時点の現残高はこの gate の入力ではない。**

## 7. 単独性と外乱

`#PBS -b 2` は 2 job の要求であって**ノード専有の証明ではない**。したがって
**専有を主張しない**。各 execution host における同居 job の snapshot を証拠に残し、
取得できなかった場合は「未確認」と記録する。外乱を検知した場合は再計測する。
