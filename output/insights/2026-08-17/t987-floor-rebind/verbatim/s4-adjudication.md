# 段 4 裁定 — [T-987] 床値 v2 再測定の束縛を記録基準へ緩める

裁定日時: 2026-08-17 09:45 JST / 親 (manager) / branch `worktree-dev-wave-t987-floor-rebind` / base `699c9cae`

## 裁定: **実装しない。裁定パッケージをユーザーへ返す。**

段の遷移は `4→7→8→9` とする (`DW-S04`)。

理由は 1 つに尽きる。**確定済みユーザー裁定が求めた「束縛を記録基準へ緩める」を
そのとおり実装しても、その目的 (床値 v2 を作る) は達成できない。**
達成を阻んでいるのは、本 wave が緩めてよいと裁定された束縛ではなく、
**別のユーザー裁定待ち事項 (§8 承認束縛方式) と、凍結 proof chain の consumer 側**である。
さらに、裁定どおりに実装して再測定を実施すると、**下流 [T-750] が必要とする
一回限りの権利を焼き切る**という不可逆な害が出る。

---

## 1. 段 3 所見の real / refuted 裁定

| # | レンズ | 所見 | 裁定 | 採否 | scope |
|---|---|---|---|---|---|
| A-1 | A | 専用 lane は環境変数 1 つで受理集合を拡大する | **real** | 採用 | 内 |
| A-2 | A | 提案の 4 重束縛は独立でなく、全て caller 由来の document へ従属 | **real** | 採用 | 内 |
| A-3 | A | pilot lane が将来 official の一回性 key を焼く | **real** | 採用 | 内 |
| A-4 | A | record が成果物へ durable に束縛されず、事後削除で成功が残る | **real** | 採用 | 内 |
| A-5 | A | **versioned protocol の測定結果を受け取る v2 consumer が存在しない** | **real** | 採用 | **外 (決定的)** |
| B-1 | B | 親の「production caller ゼロ」は誤り (CLI 経路が実在) | **real** | 採用 (親の誤りを訂正) | 内 |
| B-2 | B | M6 の count=2 は real | **real** | 採用 | 内 |
| B-4 | B | 記録追加だけでは R2 (fail-closed) を満たさない | **real** | 採用 | 内 |
| B-5 | B | 記録と測定結果が結合していない | **real** | 採用 (A-4 と同一根) | 内 |
| B-6 | B | 記録入力が不足 (activation serial / state hash / 実測 HEAD) | **real** | 採用 | 内 |
| B-7 | B | 既存 receipt / ledger / marker と二重記録になる | **real** | 採用 | 内 |
| B-8 | B | 新 path/schema の pin 閉包が未成立 | **real** | 採用 | 内 |
| B-9 | B | t657 着地後も第二の主 gate は残る | **real** | 採用 | 内 |
| A-* | A | held 三つ組・chain pattern・verdict 境界への侵食は無い | **refuted** (攻撃不成立) | — | — |

親自身の実測のうち **1 件を誤りとして取り下げる**: 「`reseal_protocol()` の production caller はゼロ」。
実際には CLI サブコマンド `reseal-protocol` が実在する
(`orchestrator/campaign/s8b_floor_campaign.py:6691-6701`、parser 同 :6566-6570)。
誤りの原因は親の grep が `grep -v "^orchestrator/campaign/s8b_floor_campaign.py"` で
同一 file 内の呼び手を自分で除外していたこと。訂正後も結論の向きは変わらない
(発行経路は「無い」のではなく「ある」ため、裁定の前提はより強く覆る)。

---

## 2. 実装しないと裁定した根拠 (親が直接検証した)

### 根拠 1 — official mode は core で無条件拒否されている

`orchestrator/campaign/s8b_floor_campaign.py:368-378`

```
def _assert_official_permitted(mode: str) -> None:
    if mode == "official":
        raise FloorCampaignError(
            "official mode は §8 (承認束縛方式) 未裁定のため core で無条件拒否する "
            "(F6 まで pilot のみ実行可)"
        )
```

拒否理由は **「§8 承認束縛方式が未裁定」= ユーザー裁定待ち**である。
本 wave が緩めよと裁定された束縛ではない。

### 根拠 2 — v2 再凍結の consumer は固定 legacy protocol に束縛されている

`orchestrator/campaign/s8b_holdout_freeze.py:1293-1336` (`_validate_floor_inputs`)

```
protocol_raw = _capture_regular_nofollow(root / FLOOR_PROTOCOL_REL, label="floor protocol")
...
if result.get("mode") != "official":
    raise FreezeError("floor result.mode が official でない")
if result.get("eligible_for_refreeze") is not True:
    raise FreezeError("floor result.eligible_for_refreeze が true でない")
if result.get("protocol_sha256") != protocol_sha256:
    raise FreezeError("floor result.protocol_sha256 が固定 protocol hash と不一致")
```

`FLOOR_PROTOCOL_REL` は固定 legacy path。したがって

- pilot の result は `mode` / `eligible_for_refreeze` で必ず落ちる
- versioned protocol で測った result は `protocol_sha256` で必ず落ちる

**束縛を記録基準へ緩めて測定を通しても、その値は v2 床値になれない。**
consumer 側を変えることは「記録基準へ緩める」の射程外であり、
凍結 proof chain の trust root を動かす別作業である。

### 根拠 3 — 裁定どおり実施すると不可逆な害が出る

`orchestrator/campaign/s8b_holdout_admission.py:493-497`

```
def _key_fields(
    *, freeze_sha256: str, freeze_holdout_key: str, configuration_id: str,
    ccbench_pin: str, env_tag: str, observation_role: str,
) -> dict[str, str]:
    # protocol_sha256 is deliberately evidence only and must never enter here.
```

key に `mode` が入らない。よって新 pin `511c9538` で pilot を 1 度成功させると、
同じ pin で将来 official を回すときに必要な one-shot key が**先に消費される**。
下流 [T-750] (床値 v2 実凍結) が必要とする権利を、本 wave が焼くことになる。

### 根拠 4 — 裁定が択 (a) を却下した理由が実測で偽

再裁定文は「待つ相手 ([T-478] (d)) が保留確定の機構であり事実上の無期限凍結になる」と書く。
実測では、待つ相手である世代移行は**本日 08:16 以降のユーザー指示で稼働中**である
(`/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/handoff.md`)。
target pair (`1346c20b`, `511c9538`) まで算出済みで未発行なだけ。
「無期限凍結」は成立していない。

---

## 3. 実装した場合に達成されること / されないこと

| | 段 2 案を全実装した場合 |
|---|---|
| 床値 v2 の pilot 測定が現 gitlink で走る | 達成しうる |
| 再測定の事実と入力が記録される | 達成しうる (ただし B-4/B-6/B-7/B-8 の是正が必要) |
| **床値 v2 が作られる** | **達成しない** (根拠 1・2) |
| **[T-750] が前進する** | **後退する** (根拠 3 — one-shot key を焼く) |

裁定文の目的語は「床値 v2 の再測定を先に実施する」であり、
2026-08-16 の択 (b) 本文は「現 gitlink で床値を再測定して **v2 を作る**」である。
v2 が作れない以上、実装は裁定の目的を満たさない。

---

## 4. ユーザーへ返す裁定パッケージ

### 問

床値 v2 を実在させるには、次のどれを開くか。

- **択 (α)** **§8 承認束縛方式を裁定して official mode を開く。**
  `_assert_official_permitted` の拒否理由がまさにこれ。開けば official 走行が可能になり、
  `eligible_for_refreeze=true` の result が作れる。ただし v2 再凍結 consumer の
  固定 legacy protocol 束縛 (根拠 2) は別途解く必要がある。
  → 本命。ただし凍結 proof chain の中核に触るため、ユーザー裁定なしに AI は進めない。

- **択 (β)** **v2 再凍結 consumer の protocol 束縛を、固定 path から
  「解決された現行 protocol」へ張り替える。**
  `s8b_holdout_freeze._validate_floor_inputs` の `FLOOR_PROTOCOL_REL` 直読みを
  resolver 経由へ変える。これは [T-987] の「記録基準へ緩める」の射程外であり、
  凍結 trust root の変更にあたる。単独では official 拒否 (根拠 1) が残るため不十分。

- **択 (γ)** **[T-419] / t657 の世代移行の着地を待ち、その後に改めて残 gate を測る。**
  待ち時間は無期限ではなく本日中の見込み。t657 着地後は resolver は通るようになるが、
  holdout authority・wrapper・refreeze consumer・official 拒否は残る (B-9 で確定)。
  → 待つこと自体の費用は小さいが、これ単独では何も解けない。

- **択 (δ)** **床値 v2 を諦め、現行 g1 床値表のまま 8b oracle 本走を進める。**
  memory の既定方針 (論文主張には粗い provenance で足りる / 凍結チェーン検証は保留 /
  研究最優先) と整合する。失うのは「床値が現 gitlink で測られていること」だけで、
  verdict の faster/no-difference 境界は旧表のまま固定される。

### 親の推奨

**(δ) を既定とし、(α) を本命の代替とする。**

理由: ユーザーの既定方針は 3 本とも「凍結機構へ費用を払わない」方向である
(凍結チェーン検証は保留確定、論文主張には粗い provenance で足りる、
研究最優先・プロトタイプ基準)。床値 v2 の実在は、その方針の下では
**8b oracle 本走の必要条件ではない**。一方 (α) は §8 という未裁定の
承認束縛方式を開く話であり、費用は (δ) より一桁大きい。

(β) 単独と (γ) 単独は、いずれも床値 v2 を実在させない。

### この wave が実装しない理由の要約 (1 行)

裁定が緩めよと言った束縛を緩めても v2 は作れず、実施すると下流の一回限りの権利を焼くため。

---

## 5. 変異事前登録 (`DW-M01`)

**免除。** `DW-S04` の「『実装しない』と裁定済みで実装差分ゼロの wave だけ変異 matrix を免除する」に該当する。
本 wave の差分は docs (spool fragment + insights) のみで、実装面はゼロ。
受入全走は免除しない。

---

## 6. 成果物影響 (`DW-G05`)

本 wave が実装しないことで成果物がどう変わるか:

床値表は g1 pin (`d706650c`) のまま固定され、
`orchestrator/campaign/s8b_verdict.py:954-982` が `freeze.floor_protocol` から引く
floor 表と scale tolerance は現 gitlink (`511c9538`) の実測値に更新されない。
その結果、certified 選択の faster / no-difference 判定境界は g1 世代の値で決まり続ける。
これは本 wave の不作為ではなく、根拠 1・2 の未裁定事項が原因である。
