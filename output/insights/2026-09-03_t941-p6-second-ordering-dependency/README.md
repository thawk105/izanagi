# [T-941] P6 の機械実装は始められない — 順序依存は 1 本ではなく 2 本だった (2026-09-03)

- `authority: none`
- `default_effect: no-state-change`

(`output/README.md` の insights 規約。本ディレクトリは調査・裁定の凍結スナップショットであり、
可変状態の正本ではない。可変状態の正本は worklog 末尾と現行 phase doc。)

## 結論

**P6 の機械実装に着手しなかった。実装面の差分はゼロである。**

worklog entry 1184 は [T-941] を「起動可」と裁定し、その理由を「二段束縛の**唯一の**順序依存が
解けた」と書いた。本 wave はその前提で起動したが、段 1 の前提実測と段 3 の敵対 2 レンズ (ともに
NO-GO)、および親の再検算により、**順序依存はもう 1 本、より手前に開いたまま**であることが判明した。

1184 が閉じたのは「P6 の実装と認定を**どの wave が所有するか**」という所有の停止項だけである。
所有が決まっても、P6 を発火させる前提が repo に 1 つも存在しない。

## 親が現物で検算した事実

レンズの報告は鵜呑みにせず、結論を変える主張は親が 1 件ずつ実装を読んで確かめた。

| # | 事実 | 場所 |
|---|---|---|
| M1 | 本番 origin の登録は **0 件** (`origins` が空配列) | `orchestrator/campaign/reflux_origin_authority_v2.json` |
| M2 | `_initialize_locked` は `store.fixture` でなければ `production runtime initialization is forbidden` で停止する。本番 runtime は構造的に作れない | `orchestrator/campaign/reflux_origin_ledger.py:2914-2915` |
| M3 | `_wal_trigger()` は root の `record["kind"] == "TriggerGateBinding"` と root `trigger_binding` を要求する。一方 production の producer は `stage=trigger_gate_binding.WAL_RECORD_STAGE` と `payload[TRIGGER_BINDING_PAYLOAD_KEY]` で書く。**着地済みの 8c formal consumer は本番形状の WAL record を 1 件も読めない** | `orchestrator/campaign/reflux_formal_consumer.py:722-729` と `orchestrator/campaign/wal.py:1354-1359` |
| M4 | `evaluate_formal_origin()` の非 test caller は 1 件だけで、そこへ origin 入力を渡す本番経路が無い | `orchestrator/campaign/p3_autonomous_workload_trial.py:1654` |
| M5 | 「**V-6〜V-10 の裁定まで結線実装 wave を起票しない原則**、発行 3 条件 0/3、本番 authority entry 0、閉じた成果層 0/11、D114 上限 1 は不変」。V-6 / V-7 / V-9 は V-8 の後と順序づけ済み | `docs/archive/worklog-phase3-0812-462-465.md:2011-2016` |
| M6 | V-8 (物理実行を 1 query = 1 campaign run にするか。費用 33 倍) は**今も未裁定**。2026-08-13 以降の言及が無く、2026-09-02 の一括裁定 374 件にも、2026-09-03 に main へ着地した /rulings 第 4 回 31 件 (`9efeacd69`) にも含まれない | archive 全走査 + 両 commit の内容検索 |
| M7 | `verify_done` payload には `build_attempt_id` が**存在する**。P6 設計 §3.2.1 の「無い (実測)」は 2026-08-03 時点の測定であり、現行コードと一致しない | `orchestrator/campaign/pipeline.py:1485` |

## 開いたままの第 2 の順序依存

```
V-8 (未裁定)
  → V-7 (V-8 の後と順序づけ済み、未裁定 = 本番 runtime provisioning をどう作るか)
  → 本番 authority entry (現在 0 件)
  → 本番 origin
  → P6 の発火条件 (契約 §3.11.1 は fixture 由来を明示的に不可としている)
  → P6 の機械実装
  → 認定 (D156 のコア要件 (1) は admission 結線まで含めた end-to-end calibration)
  → [T-434] の二段束縛
```

さらに M3 により、この鎖の途中にある着地済み formal consumer 自体が本番形状の WAL を読めない。
provisioning が済んでも、それだけでは本番 origin の projection は witness 検査より手前の FC05c で落ちる。

## なぜ「一部だけ実装する」を選ばなかったか

段 2 のプランは witness 正規化器と `_validate_wal_outcomes` の出所移動を `file:line` 粒度まで
設計し、受理集合の変化を 10 群、変異事前登録を 31 点まで具体化していた。それでも実装しなかった
理由は 4 本である。

1. **`DW-G04` を満たせない。** 発火条件を満たす既存 artifact path も計測 ID も 1 件も書けない
   (M1 / M2 / M4)。これは 2026-09-02 の [T-434] wave が同じ理由で撤退したのと同型である。
2. **`DW-G05` の成果物影響が仮想である。** 本番 origin が 0 件なので、受理集合の変化は fixture 上の
   差分にとどまる。加えて `P6Unavailable` と `FormalContractRejected` は client 側で同じ
   `OriginSealed(aborted=True, constraint_class_sha256s=())` に写る
   (`orchestrator/campaign/reflux_origin_client.py:247`)。
3. **承認済み裁定 (M5) に抵触する。** 結線実装 wave は V-6〜V-10 の裁定まで起票しない原則が生きており、
   その起点である V-8 が未裁定である (M6)。
4. **「機械化した」と名乗れない。** 契約 SC-02 は 4 adapter 各々の `P6Derived` 正例到達を合接要求する。
   `lock_coverage` / `write_intent` は整数 counter しか無く、構造化には稼働中の別 wave (T-2191) の
   編集面が要る。部分実装を SC-02 の機械化と呼ぶことは実装したふりになる。

段 3 のレンズ A (正しさ境界) とレンズ B (実効性と成果物影響) は、互いを見ずに **A1 ≡ B4**
(P6 不在で V-12 を繋ぐことは [T-942] の裁定理由に反する) へ独立に到達した。合議ではない。

## 将来の P6 実装 wave が使える成果

段 2 のプランと段 3 の 2 レンズの逐語を `verbatim/` に凍結した。provisioning が裁定された後に
同じ設計から再開でき、次の所見は前提条件として先に閉じる必要がある。

| 所見 | 内容 |
|---|---|
| A3 | 実 wire に witness の `kind` 判別子が無く、未知 kind の fail-closed は dispatcher 直呼びでしか発火しない。`verify.integrity` の exact-key 検査が要る |
| A4 | `CycleWitness` の成立条件 (`verdict="non-serializable"` と integrity clean) の再計算・照合がプランに無い |
| A5 | SC-03c の key-renaming / version-shift 対称性義務が落ちている。証明 artifact を作らないなら SC-03c 機械化を名乗れない |
| A6 | attempt 一意性を caller 選択の byte 区間内だけで判定すると、同じ attempt の区間を 2 つ置いて前半を隠せる |
| A8 | rotation ごとに 8 規則を完遂してから辞書式比較する順序が未固定。C-02b〜e は単軸変異なので浅い特徴射影でも全通しうる |
| A9 | `permutation_violations > len(sample)` だけでは `total=4/sample=5` や `total=6/sample=6` を非切詰めと誤判定する |
| A11 | 変異表に検査者列が無く、`SC-01/attempt` と `SC-03a/reason-type` は単一理由の kill にならない |
| B3 | M3 と同じ。formal consumer の stage 統一は provisioning 裁定と独立に必要 |
| B5 | V-12 の live consumer chain (p3 → `layer3_report.render()`、completeness の fresh rebuild、trial registry) を同一変更単位で持つ必要がある |
| B7 | 段 2 プランの再見積り 2,000〜3,000 行。P6 の production vertical slice は 4,000〜8,000 行級 |

## ユーザーへ返す裁定パッケージ

- **U1.** [T-941] を今 起動可のままにするか。M5 / M6 と M1 / M2 を踏まえ、**V-8 → V-7 の裁定まで
  保留へ戻す**ことを推奨する。1184 の裁定を否定するのではなく、1184 が見ていなかった前提を添えて
  再裁定を求めるものである (`DW-S04`「親は不採用にせず、新事実を添えてユーザー再裁定待ちへ戻す」)。
- **U2.** V-8 を裁定するか。これが鎖の起点であり、2026-08-12 以来「費用内訳の再提出待ち」で
  止まっている。費用内訳の再測定を別 wave で行うことを推奨する。
- **U3.** [T-942] V-12 を P6 の認定完了まで延期するか、「P6 不在でも診断専用・非完全 projection として
  繋ぐ」ことを新たに許すか。**延期**を推奨する (2 レンズ独立一致)。
- **U4.** M3 の欠陥 (formal consumer が本番形状 WAL を読めない) を独立の修理 wave として先に起票するか。
  **起票する**ことを推奨する。provisioning 裁定と独立に必要で、かつ P6 より小さい。
- **U5.** permutation witness の同値関係と thread-hint 除外を確定するか。未裁定のまま実装すると
  class SHA が未裁定の規則で固定される。**確定するまで permutation を known-unavailable に倒す**ことを推奨する。

## 本 wave が名乗らないこと

「P6 の機械実装を進めた」「production 受理集合を狭めた」「V-12 を結線した」のいずれも名乗らない。
P6 の状態は `NOT_IMPLEMENTED` のままであり、cap-lift・認定・`NOT_CLAIMED` のいずれも生じていない。

## ファイル

| ファイル | 内容 |
|---|---|
| `README.md` | 本文 |
| `brief.md` | 段 1 親 brief (提示時点の (P1)〜(P4) を含む。(P1)(P3)(P4) は段 4 で否定された) |
| `s4-adjudication.md` | 段 4 親裁定 |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex、read-only、xhigh) の逐語 |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A (正しさ境界と契約整合、NO-GO、BLOCKER 5 / MAJOR 6) の逐語 |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B (実効性と成果物影響、NO-GO、BLOCKER 5 / MAJOR 2) の逐語 |
