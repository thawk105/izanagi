# [T-316] 計測段 — 計算ノード sandbox backend の実測と、実装段への判定材料

- 生成 wave: `worktree-dev-wave-t316-sandbox-measure` (2026-08-10)
- 種別: **計測**。意味 gate 本体は実装していない (scope は probe・計測 policy・テスト・admission 登録)
- 上流の裁定: `output/insights/2026-08-09_t316-semantic-gate/package.md` の R1 / R3-1 / R3-2、
  ユーザー裁定 **R2-b (独立 oracle)** (2026-08-09 /rulings、worklog 337)
- 計測 ID: **`0:900383.nqsv`** (bnode085、是正前) と **`0:900427.nqsv`** (bnode027、是正後)
- receipt: `output/env/pegasus/t316-sandbox-backend/<計測 ID>/receipt.json` (create-only、`COMPLETED` 付き)

---

## 0. この文書が答える問い

R3-1 は実装段の blocker として「login node の実測を計算ノードへ転用してはならない (F29 型)。
qsub 計測 ID を作って実測せよ」と要求していた。本 wave はその計測である。

**答え: 候補 profile は計算ノードで NO-GO である。** ただし全面的な NO-GO ではなく、
**build 段の 1 点で破れている**。以下、成立した観測・破れた観測・帰属できなかった観測を分けて示す。

---

## 1. 決定的所見 — build profile が `std::system` を封じ込めていない

| | runtime profile | build profile |
|---|---|---|
| `std::system` | **contained** | **REACHED + 副作用観測 → no-go** |
| network connect | contained | contained |
| file write | contained (不在による) | contained (不在による) |
| 無限ループ | 子孫の消滅を確認 | 子孫の消滅を確認 |

- 2 走とも `inside_payload_state = reached`、`inside_side_effect_observed = true`、
  `inside_blocked = false`。**同一 path の sandbox 外正例も `reached` で成立**しているので、
  「payload が走らなかった」「別要因で失敗した」ではなく **封じ込めが効いていない**と帰属できる。
- **別ノードで独立再現した** (1 走目 bnode085 / 2 走目 bnode027)。
- 機序は段 6 レビュー (レンズ A #5) が事前に指摘したとおり: build profile は host の `/bin` を
  bind するため `/bin/sh` が存在し、`std::system` が成立する。runtime profile は `/bin` を隠す。

**実装段への含意。** 裁定 R1 の「(ii) を全軸の host-security boundary とする」は、
**現行の profile 案のままでは build 段で成立しない**。実装段は次のいずれかを決める必要がある。

1. build profile から shell を排除する (host `/bin` を bind せず、CMake/compiler が必要とする実行体だけを
   個別に bind する)。CMake は shell を要求する場面があるため、build が通るかは再計測が要る。
2. build 段は「shell 実行を許す」前提で、封じ込めの主張を run 段に限定し、build 段は別の防壁
   (source を DSL/IR に落とす、あるいは build 出力の copy-out を厳格化する) で守る。
3. build を封じ込め対象から外し、**残余として台帳に明示する**。

**本 wave は 1〜3 を裁定しない** (非同値な設計択一であり `DW-S04` により親は決めない)。

---

## 2. 成立した観測 (計算ノードで実測。login 実測の転用ではない)

| R3-1 の要求項目 | 結果 |
|---|---|
| user / net / pid namespace が起動する | **成立** (mnt も含め 4 種) |
| network connect が失敗する | **成立** (直接 IP、proxy 経由とも contained) |
| credential / home / agent socket へ到達しない | **成立** (不在による封じ込め。agent socket の正例は計算ノード内で自作) |
| source が RO、write が scratch 限定 | **成立** (source RO、repo・tmp への write 拒否、scratch のみ書ける) |
| process-tree timeout が子孫を残さない | **成立** (setsid で escape した子孫の PID 消滅を確認) |
| CMake build が成功する | **成立** (sandbox 内で `ycsb_silo.exe` を build。trace-disabled、source identity 検証済み。sandbox 外 build も正例として成功) |
| `perf stat` / numactl / 48-thread run が成功する | **成立** |

backend inventory: bwrap / unshare / setpriv は計算ノードに在る。landlock は不在 (login と同じ)。

---

## 3. 性能 — sandbox の実行時オーバーヘッドは測定上ほぼゼロ

計測 ID `0:900427.nqsv` (単独性が有効と判定された走行)。

- **wall elapsed の overhead 比: 中央値 0.9991、MAD 0.0067** (6 対)
- 6 サンプル: 0.9827 / 0.9957 / 1.0046 / 1.0071 / 0.9896 / 1.0025
- 条件: 同一 binary (SHA 一致)、trace-disabled、48 thread、`numactl --physcpubind=0-47 --membind=0`、
  `perf stat` 検証済み、warmup を標本から分離、**内外の実行順序を対ごとに反転**
- 単独性: 自分以外の非システムユーザ (uid >= 1000) の process なし、load average と 48 CPU 全数 affinity を記録

**この数値が言えること / 言えないこと (receipt の `metric_semantics` が明示):**
言えるのは「stock の trace-disabled binary 1 本について、sandbox 内外の wall elapsed に
検出可能な差がない」ことだけである。**TPS でも CC throughput でも floor 再較正の判断でもない。**

したがって「sandbox は重すぎて使えない」という懸念は、少なくとも stock 実行については
**実測で否定された**。ただし §5 のとおり variant 側は未測定である。

---

## 4. 帰属できなかった観測 (「測れなかった」として明示する)

- **DNS の遮断 (`S3_NETWORK_DNS_NODE_CAPABILITY_UNAVAILABLE`)。**
  計算ノードは **sandbox の外でも DNS を引けない** (外側正例も `EAI_AGAIN`)。
  したがって内側の拒否を sandbox へ帰属できない。**probe の欠陥ではなく node の性質**である。
  DNS 遮断を主張したいなら、DNS が引ける環境で測るか、別の観測点を設計する必要がある。

---

## 5. R3-1 のうち本 wave が discharge していない項目

receipt の `r3_1_coverage` に機械可読で入っている。**overall が go でも R3-1 完了を意味しない**
ことは receipt 自身が宣言する。

- **stock/variant 双方の性能差** — variant 側は合成 pipeline を要し、計測段 (`DW-G01` の生死確認) の
  射程を超えるため本 wave の scope 外とした
- **trace 実行 (正しさ検証側の run)**
- **floor 再較正の要否判断**

`discharged_by_this_probe` は 2 走目で
`["single stock trace-disabled binary sandbox elapsed-overhead sample"]` のみ
(containment 側は S3 が inconclusive のため discharge されていない)。

---

## 6. 実装段が依然として塞がれている理由

1. **§1 の設計択一が未裁定** (build 段の shell をどうするか)。
2. **[T-184] の canonical stage matrix が未発行。** worklog 363 が land したのは reasoning 面
   (段別 model/effort) だけで、`docs/phase3.md` は
   「reasoning 面の採用を [T-316] の待ち解除根拠にしてはならない」と明記している。
   R4 は sandbox profile を [T-184] 所有の stage policy へ置くとしており、この依存は未充足。
3. **R3-3 (field mapping)、R3-4 (sandbox execution receipt と WAL topology)、R3-5〜R3-9** は
   本 wave の scope 外であり未着手。
4. **R2-b の独立 oracle 本体は未実装。** 本 wave は「候補が制御する trace/stdout の外側で観測する」
   という R2-b の考え方を probe の設計原則 (正例と負例の対、sentinel、副作用の直接観測) として
   適用したが、pipeline の certified 経路に対する独立 oracle は作っていない。

---

## 7. 計測の信頼性について (この結論をどこまで信じてよいか)

- **段 6 の敵対レビュー 2 本と焦点再レビュー 1 本がいずれも当初 NO-GO** を出し、
  fix を 3 巡当てた。閉じた偽 GO 経路の主なものは、非 0 終了の封じ込め読み替え、
  無限ループ制御の恒真、S4 の子孫消滅未検査、S3 write の `O_EXCL` 恒真、計測 ID の未束縛、
  部分結果の非永続化。
- **変異 matrix 8 件は 2 走目で 8/8 KILLED (SURVIVED 0、MISMATCH 0)。**
  初回走行 (spec v1) は KILLED 3 / MISMATCH 4 / **SURVIVED 1** で、生存した M7 は
  「S7 の discharge を丸ごと無効化しても誰も気づかない」という**検査側の穴**だった。
  静的レビュー 3 本を通過した後で変異だけがこれを見つけた。初回台帳は
  `mutation-ledger-run1.json` に erratum として残している。
- **計測 ID は計算ノードと実行 bytes に束縛されている**: hostname、`PBS_NODEFILE`、
  expected/observed commit の一致、対象 path の clean、probe/pbs/policy の runtime SHA。
  **login node で走らせた場合は fail-closed で停止する。**
- **機体固有の実測 1 件**: この機体の `/work` では `renameat2(RENAME_NOREPLACE)` が
  **通常ファイルに対しても EINVAL** を返す (tmpfs では成功する)。receipt の出力先は `/work` 配下なので、
  単体テストが tmpfs で緑でも実機の publish だけが落ちる。`os.link` による create-only publish へ
  置き換えた。runbook は directory についてしか記録していなかった。

---

## 8. ユーザーへ返す判断

- **裁定が要る**: §1 の build 段 shell の扱い (3 案)。
- **報告のみ**: §3 の性能実測 (sandbox overhead ≈ 0)、§4 の DNS 帰属不能、
  §5 の未 discharge 項目、§6 の実装段 blocker 4 件。
- **本 wave は実装段を起票しない** (`DW-G04`: 発火条件を満たす artifact は揃ったが、
  §6 の 2〜4 が未充足のため)。
