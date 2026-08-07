---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t529-impl-reraise
seq: 2
---

## {{D:g04-firing-material-exists}}. 活性化権限の保留根拠から「発火正例を書けない」を外す

**決定:** D196 の理由 (b) と D215 の同一条文 (「`DW-G04` が要求する artifact path も計測 ID も
書けない」) は**事実認定が古い**ものとして supersede する。発火素材は実在する。
ただし保留自体は継続する — 残る根拠は入口面が Python 層に閉じていないこと 1 本だけになる。

素材は次のとおりで、いずれも repo 内の tracked artifact と実測値である。

- `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json`
  — `env_tag=pegasus`、`schema_version=calibration/v2`、`quality.status=accepted`、
  file sha256 が content-address と一致する。
- 計測 ID `892707.nqsv` — `job-result.json` の `calibrate_rc = 0`。
- この較正を指す prospective 後継世代は `is_valid_successor` を True で通り
  (`contract_sha256 = 1346c20b5519be4b…`)、`load_verified_calibration` は
  現行世代と prospective 後継世代の双方を ACCEPT する。

**理由:**
- `DW-G04` が求めるのは「発火条件を満たす既存 artifact path か計測 ID を brief に書けること」で
  あって、その機構が既に land していることではない。上記はどちらも書ける。
- 素材の不在を理由に挙げ続けると、実際には入口面が唯一の blocker であることが台帳から読めなくなる。
  保留の理由を実態より広く書くのは、解除条件を過大に見せる点で「実装したふりをしない」規律の裏返しの
  失敗である。
- 一方で、この較正を「正規 g2」と呼んではならない。runtime loader が外部検証するのは
  path 封じ込め・bytes SHA・schema・env・clock・policy までで、publish 記録・job-result・
  self-comparison・final receipt は読まない。schema は `quality.status=rejected` 自体を許し、
  production loader に `accepted` の明示検査はない。よって「loader が通る = 正規 publisher を
  通った」は成立しない。正確な呼称は「レビュー済み commit が束縛する publish 済み較正であり、
  後継世代の実在素材」である。

**却下した選択肢:**
- 素材が実在するのだから保留を全面解除する — 入口面 (Python 層より前に書く shell wrapper) は
  裁定で別タスクへ外出ししただけで閉じていない。部分実装は入口被覆率の過大報告になる。
- 従来どおり「素材なし」と書き続ける — 実測と食い違う記述を台帳に残すことになる。

## {{D:floor-protocol-two-lane}}. floor protocol の検証を historical 再検証と current admission へ分ける

**決定:** `s8b_floor_campaign` の protocol 検証を resolver 必須の共有 core と 2 lane に分ける。

- **historical lane** — 記録 `contract_sha256` を `resolve_by_contract_sha256` で一度だけ解決する。
  unknown / ambiguous / cross-env / 不正返却のいずれでも current lookup へ fallback しない。
  公開 `validate_protocol` はこの lane に束縛し、公開面に切替引数を足さない。
- **current lane** — `lookup(env_tag)` と記録 hash の一致を要求し、解決した contract object を
  返す。protocol builder、発行直後の read-back、fresh run と resume の live admission はこちら。
  admission 後の二度目の lookup は削除し、同一 object を calibration・execution receipt・build・
  計測 command receipt へ渡す。
- **historical 検証を通した document を実行権限 token にしない。** CLI は load 後に historical で
  artifact を検証し、`run_campaign` が current admission を必ず再実行する。
- 記録 `contract_sha256` の exact 型検査は共有 core に 1 か所だけ置き、両 lane の受理集合を
  一致させる。

**理由:**
- 凍結済み floor protocol は旧 contract hash を pin し、その bytes は凍結されている。
  検証を current 比較に固定したままだと、後継世代を活性化した瞬間に凍結済み protocol の
  受理集合が空になる。歴史世代解決はこれを解く。
- 一方で同じ入口は producer と live admission を兼ねている。全体を historical へ倒すと
  「現在 active でない較正で新しい実測を走らせる」ことを許し、D202 が履歴解決を read-only 入口へ
  限定した理由と、D213 が resume を current に固定した理由の両方に反する。
- 型検査を共有 core へ寄せたのは、敵対レビューが実測で受理集合の食い違いを示したためである。
  記録 hash に `str` の派生型を入れると current lane は受理し historical lane は拒否していた。
  実 artifact は JSON parse 由来で必ず exact `str` なので、凍結 bytes 由来の受理集合は変わらない。

**却下した選択肢:**
- 公開関数に `historical=True` のような切替引数を足す — 呼び手が既定で弱い方を選べる面を
  新設することになる。用途が明白な private 関数へ分ける方が狭い。
- 凍結済み protocol を新 contract 用に再発行する — 凍結 bytes の書き換えを伴い、
  proof chain の参照を切る。
- 活性化を保留したまま何もしない — 保留が解けた瞬間に同じ壁へ戻る。
