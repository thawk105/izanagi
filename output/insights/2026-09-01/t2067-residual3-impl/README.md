# [T-2067] 床値選択の残余 — s8c load-only consumer への g1 限定強制と、実装しない 4 項目

wave `dev-wave-t2067-residual3-impl`。base = local main `2bf9cf387`、実装 commit `88c45eeaa`、
main 取り込み `7fe67cfd3`。段 4 裁定は `ruling-stage4.md`、段 1 brief は `brief.md`、
子の逐語は `verbatim/`。

## 何をしたか

D1313 が列挙した残余のうち、load-only consumer 群への選択強制を **s8c の床値 verifier / publish
の 1 群だけ**実装した。残り 4 項目は実装せず、理由を確定した。

**D1241 / D1313 の advisory / non-certifying 上限は解除していない。** 追加で主張してよいのは
D1313 の (a)(b)(c) の 3 点のままである。強制点が増えたのは実装事実であって主張の水準ではない。

## 設計 — なぜ `launch_validate` を使わないか

| | 静的 loader | `launch_validate` | 本 wave の新 API |
|---|---|---|---|
| otherwise-valid な g2 | 受理 | **拒否** (artifact I/O より前) | **何もせず返る** (現状保存) |
| 選択 identity | 課さない | g1 で課す | g1 で課す |
| activation HEAD / current admission / closure / live scan | 課さない | 課す | **課さない** |
| historical reverify への影響 | — | 無し | 無し |

段 3 レンズ A が指摘したとおり、consumer から `launch_validate` を呼ぶと **3 群すべてに新しい
g2 拒否挙動が生じる**。これは「g2 は実在してから設計する」と定めた D1325 に抵触する。
また full current admission を consumer 契約へ昇格させると、D1313 が許した 3 点を超える
第 4 の主張になる。よって選択規則だけを g1 限定で課す狭い API を新設した。

## 段 6 が見つけた製品の穴

選択 identity の helper は、探索する namespace を **selected path の env_tag から自分で組み立てる**。
`_launch_validate` では proto8 と env_tag 連鎖の束縛が選択呼出しの**後段**にあるため、合成全体
としては別 namespace を指す path が最終的に拒否される。しかし選択規則だけを切り出すと後段が無く、
**別 env の namespace を指す `floor_source.path` を持つ g1 は、真の namespace により早い導出適格
run があっても探索から外せた。**

fix 子が修正前に実測した診断:

```
generation/protocol env : linux-baremetal
floor_source.path       : output/env/foreign-env/.../20260718T120000Z-75b01122/result.json
真の namespace の earlier: output/env/linux-baremetal/.../20260718T115959Z-75b01122/result.json
earlier の導出適格性     : True

修正前: assert_g1_floor_selection_identity(...) == None、適格性導出の呼出し = []  ← 0 回
修正後: floor-selection-unverifiable / selection-env-chain
```

fix では選択呼出しの前へ proto8 束縛と env_tag 連鎖束縛を足し、失敗は既存の
`floor-selection-unverifiable` へ畳んだ。**新しい拒否理由は作っていない。**

## 実装しない 4 項目

| 項目 | 判定 | 決め手 |
|---|---|---|
| oracle manifest 群 | **保留** | 設計は同型で正しい。既存 2 正例の synthetic 批准物が `generation_number=1` のため gate が発火して必ず赤になる。fixture 追随には別 wave が保有する未着地 test file の編集が要る。production への test 専用 bypass は入れない |
| s8c C06 予算群 | **実装しない** | gate は C05 常時拒否より手前で発火できるが、実装前後とも budget ledger を生成できる入力集合は空。変わるのは error の順序だけで成果物影響 0。単一理由の変異も登録できない |
| 起動証明書の実時間性 | **実装しない** | 不能理由は「再計算できない」ではなく **「launch 時点の独立した commitment が保存されていない」**。preimage は certificate / journal / manifest / Git tree のどれにも残らない。certificate 自身の値を expected にする形は D80 が恒真として禁止。閉じるには署名・nonce・一回性台帳が要り D1241 が禁止 |
| s8c production final claim 配線 | **実装しない (設計メモ)** | 反復 schedule (exact 6 cell・n>=2・6×n 観測)、attestation authority、判定パラメータ正本がいずれも不在。加えて 3 表は repo 外の絶対 path、receipt schema は 3 表の path/hash を持たず**失敗原子的に束ねられない** |

### C07 について誤読しないこと

s8c 事前登録の C07 述語は `s8c_result_judge` の 3 関数連鎖を AST で検査するが、その
consumer_requirement path は **同 module 自身**であり外部 production callsite を見ていない。
親の実測では C07 は本 wave の前後とも `EVIDENCE_UNDEFINED` /
`completion-proof-not-machine-checkable` = 全構造検査を通過した終端であり、
`SATISFIABLE_CONDITION_IDS` が C10 だけなので **設計上 SATISFIED に到達しない**。
配線しても C07 の status は変わらない。

## 変異 matrix

anchor commit `88c45eeaa`、spec sha256 `eeb9d8e2...`。
probe 段 (全件 SURVIVED 期待) で観測 node を集めてから本走した。

| id | 変異 | 結果 |
|---|---|---|
| M1 | verify 側の consumer 配線を bare loader へ戻す | KILLED |
| M2 | publish 側の current binding を bare loader へ戻す | KILLED |
| M3 | g1 限定の枝を無条件実行へ変える | KILLED |
| M4 | env_tag 連鎖の束縛を潰す | KILLED |
| M5 | proto8 の束縛を潰す | KILLED |

**baseline PASSED (赤 0) / KILLED 5 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、期待 node 完全一致 5/5。**

M3 は当初、内部 sentinel による赤しか作らず `DW-M03` の kill 条件を満たしていなかった
(段 6 レンズ B が指摘)。g2 の同一 namespace により早い導出適格 run を置いた fixture へ照準し直し、
**受理と拒否が実際に反転する**形にしてから登録した。

詳細は `mutation-probe2-summary.json` と `mutation-final-summary.json`。

## 現時点で主張してよいこと・いけないこと

**主張してよい:**

- 選択規則の強制点が s8c の床値 verifier / publish にも増えた (実装事実)。
- g2 の受理・拒否・選択・投影は本 wave の前後で完全に同一である。
- 静的 loader と historical reverify の受理集合は変わっていない。

**主張してはいけない:**

- production final claim を配線した。
- C07 が改善した / 満たされた。
- 公開物が current admission に束縛された。
- D1241 / D1313 の上限が動いた。
- active g1・official floor run・予算承認が存在する (現 tree ではいずれも 0 件)。
