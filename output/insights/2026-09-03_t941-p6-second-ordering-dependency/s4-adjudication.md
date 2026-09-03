# 段 4 裁定 — [T-941] P6 機械実装 + [T-942] V-12

## 裁定の結論

**実装しない (`DW-S04` の「実装しない」分岐、`4→7→8→9`)。**

段 3 の 2 レンズが独立に NO-GO を返し、親がその決定的な主張を 1 件ずつ現物で検算した結果、本 wave が
実装へ進むと `DW-G04`・`DW-STOP`・2026-08-12 の承認済み裁定のいずれにも抵触する。`DW-S04` の
「承認済み裁定は裁定時の未見事実でだけ止め、親は不採用にせず新事実を添えてユーザー再裁定待ちへ戻す」
に従い、[T-941]「起動可」の裁定を親の判断で覆さず、新事実を添えて裁定へ戻す。

## 親が現物で検算した事実 (レンズの報告を鵜呑みにしていない)

| # | 事実 | 検算方法 |
|---|---|---|
| M1 | `orchestrator/campaign/reflux_origin_authority_v2.json` の `origins` は空配列。本番 origin の登録は 0 件 | JSON を直接 parse |
| M2 | `orchestrator/campaign/reflux_origin_ledger.py:2914-2915` の `_initialize_locked` は `store.fixture` でなければ `production runtime initialization is forbidden` で停止する。本番 runtime は構造的に作れない | 該当行を読んだ |
| M3 | `reflux_formal_consumer.py:722-729` の `_wal_trigger()` は root の `record["kind"] == "TriggerGateBinding"` と root `trigger_binding` を要求する。一方 `wal.py:1354-1359` の `log_trigger_binding()` は `stage=trigger_gate_binding.WAL_RECORD_STAGE` と `payload[TRIGGER_BINDING_PAYLOAD_KEY]` で書く。**着地済みの 8c formal consumer は本番形状の WAL record を 1 件も読めない** | 両方の実装を読んで形状を突き合わせた |
| M4 | `evaluate_formal_origin()` の非 test caller は `p3_autonomous_workload_trial.py:1654` の 1 件だけで、そこへ origin 入力を渡す本番経路が無い | `grep` で全 caller を列挙し tests を除外した |
| M5 | 2026-08-12 の裁定 (`docs/archive/worklog-phase3-0812-462-465.md:2011-2016`) が「**V-6〜V-10 の裁定まで結線実装 wave を起票しない原則**、発行 3 条件 0/3、本番 authority entry 0、閉じた成果層 0/11、D114 上限 1 は不変」と定め、V-6 / V-7 / V-9 は V-8 の後と順序づけている | 逐語を読んだ |
| M6 | V-8 (物理実行を 1 query = 1 campaign run にするか。費用 33 倍) は**今も未裁定**。2026-08-13 (archive 517) 以降の言及が無く、2026-09-02 の一括裁定 374 件 (entry 1184) にも、2026-09-03 に main へ着地した /rulings 第 4 回 31 件 (`9efeacd69`) にも含まれない | archive 全走査 + 2 つの裁定 commit を内容検索 |
| M7 | `verify_done` payload には `build_attempt_id` が**存在する** (`pipeline.py:1485`)。P6 設計 §3.2.1 の「無い (実測)」は 2026-08-03 時点の測定であり現行コードと一致しない | 該当行を読んだ |

## 所見の裁定

### real・採用 (scope 内で対処 = 記録する)

| 所見 | 裁定 | 扱い |
|---|---|---|
| A1 ≡ B4 (P6 不在で V-12 を繋ぐのは [T-942] の裁定理由に反する) | **real**。2 レンズが独立に到達 | 実装せず裁定パッケージへ |
| A2 (SC-02 は 4 adapter の `P6Derived` 正例を合接要求するので「機械化」と名乗れない) | **real** | 実装しないので名乗りも生じない。記録に残す |
| A3 (実 wire に witness の `kind` 判別子が無く、C-08 は dispatcher 直呼びでしか発火しない) | **real** | insight へ記録。将来 wave の前提条件 |
| A5 (SC-03c の key-renaming / version-shift 対称性義務が落ちている) | **real** | 同上 |
| A7 ≡ B の候補 4 (permutation witness の同値関係が規範上未裁定) | **real** | 裁定パッケージへ |
| A10 ≡ B6 (親 brief の `verify_done` 実測が現行コードで偽) | **real。親の誤り** | M7 として記録し訂正 |
| A11 (変異表に検査者列が無く、単一理由性を満たさない行がある) | **real** | 実装しないので変異表は成立しない。記録に残す |
| B1 (production 発火経路が無い。`DW-G04` 不成立) | **real。M1/M2/M4 で検算済み** | 本裁定の主因 |
| B3 (formal consumer が本番形状の WAL を読めない) | **real。M3 で検算済み。新規の欠陥記録** | insight へ記録 |
| B5 (V-12 の live consumer chain が scope 外) | **real** | 実装しないので発生しない。将来 wave の前提条件 |
| B7 (見積り 2,000〜3,000 行。P6 vertical slice は 4,000〜8,000 行級) | **real** | 記録に残す |

### real だが scope 外 (実装しない)

A4 / A6 / A8 / A9 は、いずれも実装を前提とした所見であり、実装しない裁定により発生しない。将来の
P6 実装 wave が同じプランを再利用する場合に備え、insight へ所見 ID とともに残す。

### refuted

なし。両レンズの BLOCKER・MAJOR はすべて real と裁定した。

## 親 brief の (P1)〜(P4) の帰結

- **(P1) 否定。** 「出所の移動だけで `DW-G05` の成果物影響を満たす」は成り立たない。M1/M2 により本番
  origin が 0 件なので、受理集合の変化は fixture 上の仮想差分にとどまる。B2 の指摘どおり、
  `P6Unavailable` と FC07 は client 側で同じ `OriginSealed(aborted=True, constraint_class_sha256s=())`
  に写る (`reflux_origin_client.py:247`)。
- **(P2) 条件付き支持。** [T-326] 裁定 (b) と独立 verifier module は両立するというレンズ 2 本の一致は
  得た。ただし [T-942] の時間順序制約 (A1 ≡ B4) は別に残るため、V-12 は本 wave で実装しない。
- **(P3) 部分否定。** 実測部分 (permutation の構造化、`sample` 5 件上限) は支持されたが、
  「fail-closed だけで SC-02 を満たす」への一般化は否定された。
- **(P4) 否定。** 1 wave に収まらない。

## 本 wave が成立させた新事実 (これが成果である)

**entry 1184 の「二段束縛の唯一の順序依存が解けた」は、事実として誤りである。**

1184 が閉じたのは「P6 の実装と認定を**どの wave が所有するか**」という所有の停止項だけである。
所有が決まっても、P6 を実装できる前提が揃っていない。**第 2 の、より手前にある順序依存が開いたまま**である。

```
V-8 (未裁定) → V-7 (V-8 の後と順序づけ済み、未裁定) → 本番 runtime provisioning
             → 本番 authority entry (現在 0) → 本番 origin → P6 の発火条件
             → P6 実装 → 認定 → T-434 の二段束縛
```

加えて M3 により、この鎖の途中にある着地済み formal consumer 自体が本番形状の WAL を読めない。
provisioning が済んでも、それだけでは本番 origin の projection は FC05c より手前で落ちる。

## ユーザーへ返す裁定パッケージ

- **U1.** [T-941] を今 起動可のままにするか。M5/M6 の「V-6〜V-10 の裁定まで結線実装 wave を起票しない」
  原則と、M1/M2 の本番 origin 0 件を踏まえ、**V-8 → V-7 の裁定まで T-941 を保留へ戻す**ことを親は推奨する。
  1184 の裁定を否定するのではなく、1184 が見ていなかった前提を添えて再裁定を求めるものである。
- **U2.** V-8 (物理実行を 1 query = 1 campaign run にするか。費用 33 倍) を裁定するか。これが鎖の起点であり、
  2026-08-12 以来「費用内訳の再提出待ち」で止まっている。親は費用内訳の再測定を別 wave で行うことを推奨する。
- **U3.** [T-942] V-12 を、P6 の認定完了まで延期するか、「P6 不在でも診断専用・非完全 projection として繋ぐ」
  ことを新たに許すか。親は**延期**を推奨する (2 レンズ独立一致)。
- **U4.** M3 の欠陥 (formal consumer が本番形状 WAL を読めない) を、独立の修理 wave として先に起票するか。
  親は**起票する**ことを推奨する。これは provisioning 裁定と独立に必要で、かつ P6 より小さい。
- **U5.** permutation witness の同値関係と thread-hint 除外を確定するか。未裁定のまま実装すると、
  class SHA が未裁定の規則で固定される。親は**確定するまで permutation を known-unavailable に倒す**ことを推奨する。

## 変異事前登録

`DW-S04` により、実装面の差分がゼロの wave は変異 matrix を免除する。本 wave は docs のみであり、
変異は登録しない。受入全走は免除されないので段 7 の記録前に実走する。
