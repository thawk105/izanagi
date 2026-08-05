# 段 1 brief — [T-139] 代替 X probe 再走 (dev-wave 2026-08-05)

`authority: none` / `default_effect: no-state-change`。可変状態の正本は worklog 末尾。

## scope

[T-139] 択 (a) を実行する — **O(1) stripe 計算 + cache line padding を備えた代替 X (以下 modeX) で
正例 (positive control) の生死確認 probe を再走する**。D126 が不成立と記録した mode2 の置き換えである。

**scope 外 (実装しない):** 正例 artifact の発行、qualification manifest、`patches/ledger.json` への登録、
RF calculator、`recovery_measurement_eligibility` の解消、T-338 Q11 の validator (= [T-339])、
適格性の権威境界 (= [T-337])。これらは D120 / D126 で裁定済みまたは裁定待ちである。

## 確定済みユーザー裁定 (前提)

- **[T-139] 択 (a)** (worklog (124))。着手条件は「[T-338] の Q1〜Q5 の裁定の後」(worklog (134))。
- **[T-338] は 2026-08-03 (142) で Q1〜Q11 全件裁定完了** → 着手条件は**成立済み**。
  worklog の [T-139] 項は (134) 以来 pointer で持ち越されており **stale**。段 7 で繰り上げを記録する (F35)。
- **D126 決定 (4)**: probe の受理条件は事前に固定し、結果を見てから変えない。
- **D126 決定 (3)**: 適格性宣言の権威境界は親が決めない → 本 wave も artifact を発行しない。

## 段 1 の前提実測 (親、本 wave で実測)

| 前提 | 実測 |
|---|---|
| 前回 patch が現 CCBench pin へ当たるか | **当たる** — submodule `d706650…`、`patch -p1 --dry-run` rc=0 |
| third-party 3 本 (masstree/mimalloc/googletest) | **有** — `/work/1/SFC/tanab/izanagi-thirdparty-cache`、`verify` で pin 一致 |
| policy が指す gflags/glog source | **無** — `/home/SFC/tanab/github/` がディレクトリごと不在。`verify-deps` rc=1 |
| `tools/pegasus/policy.json` の pin 閉包 | **bytes pin 有** — `policy_sha256` (`silo_ladder_rung1.py`)、`{commit}:tools/pegasus/policy.json` identity (`qualification/identity.py`)、`qualification/contract.py` の対象一覧 |
| YCSB の key 表現 | `std::string`、**8 byte 固定・big-endian** (`ycsb.hh` `SimpleKey<8>`) → 低位 bit は末尾 byte 側 |
| mode2 の stripe 計算 | key 全 byte を舐める FNV 風ループ = **O(len)**。`std::array<std::mutex,2>` に **padding 無し** |
| 既存 3 arm データ | `0_877859.nqsv` の 1 job のみ = **J=1** (cluster 間分散は 1 点も推定できない) |
| 計算資源 | Pegasus gen_S、投入時点で **QUE 123 / RUN 40** の混雑 |

**新事実 1 件 (裁定時点で未見):** gflags/glog の消失は、[T-139] probe だけでなく
`silo_ladder_rung1.sh` 系の再現全体に掛かる。**policy.json のパス書き換えは凍結証拠の pin を壊す**ため
本 wave では行わない。probe 側で調達経路を持つ (P2)。probe 外への一般化は scope 外で、段 4 の
裁定パッケージへ返す。

## 親の provisional 裁定 (攻撃対象)

- **(P1) modeX の形** — stripe 数は **2 のまま**とし、(i) stripe を key 末尾 8 byte の O(1) 読み出しから
  導く、(ii) 各 mutex を `alignas(64)` 相当で cache line 分離する。stripe を増やさない理由は、
  stock へ近づきすぎると受理条件の全標本分離 `max(X) < min(stock)` が壊れうるため。
  **成果物影響:** stripe 数を誤ると正例が「回復ゼロ」または「stock と非分離」になり、
  正例 artifact の生成経路が再び持てなくなる。
- **(P2) 依存 source の調達** — `policy.json` を **1 byte も編集せず**、probe 側 (PBS) が gflags/glog の
  source root を env で受け取り、**HEAD == policy の `dependency_pins` かつ clean** を従来どおり検査する。
  実体は `/work` 配下へ pin 付き clone する (home へ戻さない)。
  **成果物影響:** policy.json を編集すると `policy_sha256` と identity binding が動き、
  T-126 / rung1 の凍結証拠が赤になる (D107/D110 が既に却下した型)。
- **(P3) 受理条件** — 前回と同じく **両 workload で全標本が `mode1 < modeX < stock`** を段 4 で事前固定する。
  liveness 288/288・nm witness・単独性検査も継続。本 wave は **J=1 の生死確認**であり、
  T-338 の J≈11 / d≈1.0 は**正例本走の設計**であって本 wave の対象外。
  **成果物影響:** ここを結果を見てから緩めると D126 決定 (4) 違反 = 受理集合の事後変更になる。
- **(P4) 発行しないもの** — artifact、gate、ledger 登録、受理集合の変更はゼロ。
  **成果物影響:** certified 選択・材料レポート・proof chain・凍結 bytes はいずれも不変。

## 不変条件

1. `patches/ledger.json`、`tools/pegasus/policy.json`、既存 rung1 成果物の bytes を変えない。
2. 受理集合を変えず、gate を新設しない (probe の内部検査は izanagi の gate ではない)。
3. 規律 1 — 性能計測は trace-disabled build、liveness は `ADD_ANALYSIS` の別 build・別 run。
4. 規律 2 — modeX は stock の write-lock CAS を同一 lvalue・同一 `expected`/`desired` で 1 回だけ実行し、
   serializability を変えない。mutex 保持者は record lock を待たない。飢餓は liveness 受理条件で検出する。
5. 結果を見てから候補・受理条件・workload を差し替えない (D126 決定 (4))。

## 成果物の形

- probe patch v2 (modeX) と probe driver / PBS の依存調達 fix (`tools/pegasus/probes/` 配下、使い捨て)
- Pegasus 計算ノードでの実測 raw (`output/env/pegasus/t139-positive-control-probe/<job>/`)
- `output/insights/2026-08-05_t139-alt-x-probe/` の逐語
- worklog / decisions の spool fragment (段 9 の land が採番・追記する)

## 並列分割方針

- 段 2: codex read-only 1 本 — file:line 粒度の plan (modeX 実装 + 依存調達 + 事前登録)
- 段 3: codex read-only 2 本 — レンズ A = 正しさ防壁・pin 閉包・権威境界・規律 2 / レンズ B = 機序と
  実験設計・事前登録・資源見積り
- 段 5: codex `role=author` 1 本 — patch v2 と probe 調達 fix (docs 編集・commit なし)
- 段 6: codex read-only 2 本 — 敵対レビュー

**軽量版にしない理由:** (P2) が pin 閉包と権威境界に触れ、(P1)(P3) は設計択一が割れうるため、
`DW-C00` により独立の敵対検証子を省かない。
