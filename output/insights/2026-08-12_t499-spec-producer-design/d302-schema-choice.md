# D302 schema 択一の実測票 — 据え置き解除か再発行か

**裁定を求めた問い:** `output/s8b-oracle-spec/` へ durable artifact を発行するにあたり、
D302 の schema version 据え置きを解除するか、schema を再発行 (v1 → v2) するか。
どちらを取るとどの consumer が壊れるかを実測で示し、択一で提示する。

**本 wave の結論: 提示された択一は、そのままでは択一になっていない。**
以下に実測を示し、置き換えるべき問いを提示する。

- 検証: 段 2 プラン子 (codex sol/max) + 段 3 敵対 2 本 (sol / luna、いずれも max) + 親の独立実測。
  **A 却下論法の否認は 3 者独立に一致した。**
- 本 wave は durable artifact を 1 件も発行せず、`APPROVED_SPEC_SHA256` を書かず、
  contract test の期待値を変えていない。

---

## 1. 実測 — 番人の実体

`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`
(`test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec`)

```
for relative in ("output/s8b-oracle-manifest-candidates", "output/s8b-oracle-spec"):
    ... rglob("*") ... if path.is_file()
assert durable_files == []
```

実測でわかったこと。

- **schema version による分岐が無い。** この検査は JSON を parse すらしない。
- **対象は 2 directory 両方**である。spec だけの番人ではない。
- `is_file()` が真の entry だけを数える。symlink・FIFO・socket・broken symlink は数えない。
- ファイルシステムを見ており git を見ない。untracked なファイルでも赤になる。

## 2. 実測 — この検査は本走そのものの阻止器でもある

`build_approved_manifest` (`orchestrator/campaign/s8b_oracle_manifest.py:1170-1232`) は
`load_approved_spec` を消費し、`_candidate_output_parts` (`:882-892`) により
`output/s8b-oracle-manifest-candidates/` 配下にしか書けない。

→ **spec を承認して本走が candidate を出した時点で、同じ assertion が必ず赤になる。**

ただし正確を期すと、spec を承認しただけでは candidate は発行されない。
`build_approved_manifest` は spec より**先に** active ratified freeze を読むため
(`:1170-1188`)、active freeze が無い現在は spec 承認だけでは candidate 生成に到達しない。

**意図と実効の差:**

| | 内容 |
|---|---|
| 意図 | D302 の「v1 durable artifact はまだ 0 件」という判断根拠を監視する番人 |
| 実効 | 初回発行で赤、candidate 発行でも赤。acceptance を必須とする運用では本走を land できなくする |

この検査は runtime guard ではない。pytest を無視すればプロセス自体は起動できる。
**運用上の阻止器であって、正しさの runtime 防壁ではない。**

## 3. 実測 — 選択肢 A と B の受理集合

現行 test の受理集合を `E`、v1 lifecycle gate を `A`、v2 lifecycle gate を `B` とする。

| gate | 受理する状態 |
|---|---|
| `E` | 両 directory に `is_file()` が真の descendant が 0 件 |
| `A` | `E` に加え、承認済み v1 spec と、それに対して検証済みの v1 candidate の状態 |
| `B` | `E` に加え、承認済み v2 spec と、それに対して検証済みの v2 candidate の状態 |

**`E ⊊ A` かつ `E ⊊ B`。** raw bytes としては v1 と v2 の literal が異なるため
`A ⊄ B` かつ `B ⊄ A` だが、差が schema literal だけなら v1↔v2 の置換で一対一に対応し、
**規律 2 の観点で A と B の強さは同じである。**

→ **「A は受理集合を広げるから規律 2 と両立しない」という論法は refuted。**
B も同じ量だけ広げる。段 2 プラン自身が「B でも zero-file assertion は落ちる」と認めており、
この 2 つの記述は両立しない。

## 4. 実測 — D302 が直接論じている schema はどちらか

schema authority は 2 つある。

| artifact | schema authority |
|---|---|
| reviewed spec | `s8b-oracle-reviewed-spec/v1` (`orchestrator/campaign/s8b_oracle_spec.py:18,109`) |
| official manifest | `8b-oracle-manifest/v1` (`orchestrator/campaign/s8b_oracle_artifacts.py:20,131-146`) |

`docs/decisions.md` の D302 本文は「manifest schema へ `spec_sha256` を持たせるだけでは
受理集合を 1 bit も狭めない」から始まり、`verify_manifest` の内容再導出を決定している。
**D302 の直接対象は official manifest schema である。**

却下選択肢の「schema version を上げる — durable 発行 0 件を機械確認したうえで据え置く。
durable 発行後にこの決定を変えるなら再発行が要る」は、
**「D302 の意味を変えるなら再発行」**であって、
**「最初の v1 artifact を発行すること自体」は再発行理由ではない。**

→ **reviewed spec 側の schema version を上げる根拠は、D302 から直接は出てこない。**

## 5. 実測 — v2 化のコスト (仮に B を取った場合に触る面)

### reviewed spec 側

- `orchestrator/campaign/s8b_oracle_spec.py:18,105-110` (authority と exact check)
- production consumer 4 module: `s8b_oracle_driver.py:487,497,1220` / `s8b_oracle_judge.py:372` /
  `s8b_oracle_report.py:1763` / `s8b_oracle_manifest.py:1186`
  (いずれも loader 経由なので定数追随で足りる)
- `orchestrator/tests/s8b_oracle_spec_fixture.py` (定数参照のため追随)
- `orchestrator/tests/test_s8b_oracle_manifest.py` の独立 golden は v1 literal と raw SHA を
  持つため、v2 の exact bytes / hash で再発行が要る

### official manifest 側

- `orchestrator/campaign/s8b_oracle_artifacts.py:20,131-146` (classifier)
- `orchestrator/campaign/s8b_oracle_manifest.py:34,766-787,991-1018`
- `orchestrator/campaign/s8b_oracle_driver.py:320-339` (構造拒否)
- `orchestrator/tests/test_s8b_oracle_manifest_contract.py:18-34,85-102` (consumer pin)
- `orchestrator/tests/test_s8b_oracle_artifacts.py:218-240` (schema alias)

**得られるもの:** durable artifact が 0 件である以上、v1 bytes を読んでいる consumer は
存在しない。守るべき互換性が無い。**受理集合は 1 bit も変わらない。**

**失うもの:** spec SHA、manifest SHA、manifest ID、driver の claim identity が一斉に変わる
(`s8b_oracle_driver.py:976-983`)。winner が同じでもレポートと台帳の参照値が変わる。

## 6. 裁定

### 6.1 schema version について

**裁定: 実際の semantic delta が無い限り v1 据え置き (選択肢 A)。**

- 理由 1: D302 の直接対象は manifest schema であり、spec 側 bump の根拠が出ない (§4)。
- 理由 2: durable 発行 0 件のため守るべき互換性が無く、v2 化は受理集合を変えない (§5)。
- 理由 3: A 却下論法は受理集合の包含として成立しない (§3)。
- **但し書き (sol の指摘を採用):** 将来 authenticated receipt の hash / ID を schema 内へ
  加えるなど、**schema object に実際の field / 意味の差分が生じる場合は、
  変更した側の schema だけを上げる。** 「無条件に v2 化不要」とは主張しない。
- receipt を外部 artifact として新設する場合は、receipt 自身を `/v1` で新設する。

### 6.2 択一そのものについて

**裁定: 「据え置き解除か再発行か」は本質的な問いではなかった。**

どちらを選んでも zero-file assertion は落ちる。真の問いは次である。

> **未承認状態の zero-file 条件を保ったまま、承認済み状態だけを受理する
> lifecycle state machine をどう設計し、それを runtime のどこへ接続するか。**

この置換は「durable file を許す緩和」ではないが、**受理集合が真に広がることは事実である。**
広げる判断は実装者の裁量ではなく、**ユーザーの明示裁定 (新しい D) として記録されなければならない。**
本 wave はその裁定を求める材料を提示するに留め、実装しない。

### 6.3 本 wave での帰結

- **contract test は 1 文字も変えない。** 期待値も緩めない。
- **`SCHEMA_VERSION` は v1 のまま。** 触らない。
- **durable artifact は 0 件のまま。** 両 directory は不在のまま。
- D302 は据え置きのまま有効。**本 wave は D302 を変更しない。**

---

## 7. この択一より重大な設計欠陥 (段 3 が発見)

A/B の議論に集中していると見落とすが、敵対 2 本は**より上位の欠陥を 4 件**挙げた。
これらは schema version をどちらにしても残る。詳細は `producer-design.md` を参照。

1. **人間承認が機械強制されていない** — AI が bytes・hash・receipt・pin をすべて作れる。
2. **lifecycle の状態機械が閉じていない** — pin だけ / receipt だけ / 複数 candidate 等が未拒否。
3. **pin 設定後から本走までの同時 drift が閉じていない。**
4. **spec の binding と `LaunchValidatedFreeze` の交差照合が marker 作成前に無い** —
   誤 binding が one-shot 実走を消費する。

**schema version の選択は、これらのどれ 1 つも解決しない。**
