---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2408-b10-lock-identity
seq: 2
---

## {{D:b10-report-lock-digest-admission}}. B-10 の限定受理は系列ごとの lock 全体 digest で閉じ、個別の構造比較を足さない

**決定:** B-10 の集約 (report) が読む campaign lock は、**系列ごとに lock file 全体の SHA-256 を
module literal と exact 比較して受理する。** 歴史 decoder を通した後に読む値 (binding / spec /
calibration / workload / path など) は値の取り出し口として残すが、
**偽造対策として個別の構造比較を新たに足さない。**

**理由:**

- 段 6 の敵対レビュー 2 レンズが独立に、歴史 decoder を通しただけでは identity の真正性に届かないことを
  示した。現物 lock を土台に inner と outer を再 canonical 化すると、3 系列そろえた calibration の値改変、
  `space_version` と `trial` の対改変、別系列の**実在する** authority との交換、未検査の
  `search_config` key の改変が、いずれも通った。
- lock 全体の digest 1 本でこの 4 型すべてを閉じる。個別に構造比較を足す案では、
  未検査 key の網羅 (現物で 23 key) と値 literal の登録が必要になり、しかも後から key が増えると穴が空く。
- これは D1597 が名指しした形そのものである — 「系列ごとの有限な内容 digest 集合へ exact に閉じ、
  一般規則は作らない」。受理集合は 3 系列の有限集合のままで、literal は増えるが暗黙にならない。
- 個別の構造比較を足すと、その多くが digest 照合に含意されて**恒真**になる。恒真な述語は
  壊しても赤にならず、変異防壁として数えられない。足さないことでこの汚染を避ける。
- 代償として、**raw lock 由来の既存 predicate と系列間比較は独立した変異防壁ではなくなる。**
  これは主張せず記録する。診断価値のために残しているだけである。

**却下した選択肢:**

- **calibration の値 literal・`search_config` の exact key 集合・authority と系列の対応比較を個別に足す** —
  上記のとおり網羅が要り、しかも digest を入れれば恒真になる。
- **`artifact_admission.require_admitted_campaign(purpose=HISTORICAL_RAW)` を使う** — 実測で
  `legacy_admission_overlay_v1.json` に B-10 の formal campaign ID は 1 件も無い。採ると
  overlay ledger への登録という別問題を開く。D1653 が要求する記録 blob 照合は、
  `contract_loader_binding.verify_committed_contract_loader_blobs` の再利用で満たせる。
- **通常 decoder を 24 path grammar へ広げる** — 認証側の consumer まで旧 grammar を受理する (D1653)。

## {{D:b10-historical-report-drops-live-site-contract}}. 歴史成果物の report は現在の計測サイト contract を前提にしない

**決定:** B-10 の report phase は `pipeline._require_measurement_site` / `p2_2.resolve_site_runtime` /
現在の contract との `clocks_per_us` 比較 / claim directory の作成を**要求しない。**
official output root の解決だけを行う。build 専用の binary path policy 検査も report の後段へ移す。
**代わりに、lock 記録値どうしの整合 (calibration の `env_tag` と `threads`、locked clocks による
物理残差検査) は残す。**

**理由:**

- 3 系列の lock と 135 record がすべて正しくても、現在の runtime contract の値が測定当時から変われば
  report が発行できなくなる。これは D1771 が治した病 (現行の live 成果物と一致しないと過去の測定が
  読めない) を別の場所で再発させる形であり、規律 7 に反する。
- `B10_BINARY_PATH_POLICY_ENV` は formal build の前提であって、凍結済み成果物を読む report の前提ではない。
  設定されていないだけで発行不能になるのは、正しさと無関係な拒否である。
- 落としてよいのは「現在の環境が測定に適格か」を問う検査だけで、「記録どうしが整合しているか」を問う
  検査は残す。後者は歴史成果物だけで完結し、外部の状態に依存しない。

**却下した選択肢:**

- **現在の contract と locked calibration を exact 比較して不一致なら止める** — 止まる形は
  fail-closed で安全に見えるが、測定当時と同じ環境が永続することを前提にしており、
  規律 7 が禁じる「現行コードとの差だけを理由に過去の測定を無効にする」に落ちる。
- **report でも live patch と applied tree を検査する** — 歴史 patch SHA とは比較できず、
  current patch と自己比較するだけでは無関係な live tree の変化で止まる。
