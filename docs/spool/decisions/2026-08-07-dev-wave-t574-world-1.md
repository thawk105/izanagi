---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t574-world
seq: 1
---

## {{D:receipt-expectation-scope}}. 宣言済み run_contract の identity 欠落は fail-closed にし、診断の適用層を名乗る

**決定:** oracle report の receipt expectation 導出は、`run_contract` を Mapping として宣言する
manifest に対して `env_tag` と `contract_sha256` の非空 str を要求し、欠落・空・非 str を resolver
より前に拒否する。`run_contract` field 自体が無い真の legacy と、field が非 Mapping のケースの
挙動は変えない (後者は既存の manifest issue が拾う)。

この診断を `manifest-global` と名乗らない。実際に行へ載るのは **campaign-start が一意で schedule
row を持つ campaign の観測経路だけ**であり、directory 欠落・WAL read error・terminal issue の
早期 return と 0-row campaign では載らない。この限定を docstring に書く。0-row・早期 return 経路へ
届く top-level structured issue の新設は行わない。

**理由:**
- 宣言していながら identity が不完全な manifest を legacy 扱いで通すと、contract / calibration /
  execution receipt の束縛なしに row が `completed` へ到達しうる。受理集合の縮小はユーザーが承認済み。
- 発行済み official manifest は 0 件で、`build_manifest` / `write_manifest` の production caller も
  0 件である。よってこの締めは既存成果物の受理を 1 件も変えない。**この射程を台帳に正直に書く。**
- 「manifest 全域に効く」と書くと、早期 return と 0-row では診断が消える事実と食い違う。
  D203 が禁じた「観測的に区別できない保証を台帳に書く」型の再発になる。適用層を名乗るのが
  同決定の直接の帰結である。

**却下した選択肢:**
- 非 Mapping のケースもここで拒否する — 既存の manifest issue が拾うため二重拒否になる。
- 0-row・早期 return へ届く top-level issue を新設する — 現在の certified 値・受理集合を変えない
  防御的堅牢化であり、プロトタイプ基準 (D205) の既定は見送りである。択一として返す。

## {{D:current-only-resume-spec}}. 契約世代を跨いだ resume の喪失は正式仕様とし、因果で pin する

**決定:** campaign resume は current 契約束縛のままとし、契約世代が進むと旧世代 protocol の
中断 run を再開できないことを正式仕様として受容する。これを回帰試験で固定する。

固定の仕方は**例外型の一致では足りない**。current 契約検査が calibration 読込みより前に拒否した
という**因果**を、calibration loader の呼出し回数 0 で pin する。fixture は現行 g1 と正当な後継 g2 の
2 世代 mapping を作り、`GENERATIONS` / `REGISTRY` / 契約 hash index の 3 属性を一貫して局所差し替え
する。g1 を index に残すことで、resume を歴史 resolver へ誤配線した改修が検出される。
通る正例 (current が進んでいない同じ resume が完走する) を必ず添える。

**理由:**
- 例外型だけを見る試験は恒真である。`attestation_mode="none"` の calibration loader は
  grandfathered v1 artifact bytes だけを受理するため、正当な後継世代は calibration 参照を必ず変え、
  合成 g2 の calibration 読込みが**必ず**失敗する。したがって守るべき current 契約検査を削除しても、
  後段が同じ例外型を返して試験が緑のままになる。変異検査で実証した。
- lookup だけを差し替える fixture では registry と契約 hash index が旧世代のままとなり、
  模擬状態が自己矛盾する。3 属性を同一 mapping から構成すれば矛盾しない。
- 実 registry は bootstrap fuse により単一世代のままである。この試験が模すのは
  「現在値が後継世代へ進んだ」admission 境界であって、実際の世代発効ではない。
  この差を試験の docstring に明記する。

**却下した選択肢:**
- 未登録 hash を protocol に書いて世代跨ぎを模す — 破損・未登録を模しているだけで、
  世代跨ぎ固有の退行を検出しない。
- 診断文字列を `match=` で pin する — 揮発する payload を期待値へ焼き込むことになる。
- resume へ歴史 resolver を配線する — 承認されていない受理集合の拡大であり、D202 の
  live/read-only 分離を崩す。

## {{D:silo-verify-result-current-compat}}. silo verify-result の binding 層は current 互換検査である

**決定:** silo ladder の `verify-result` が committed artifact の記録 `contract_sha256` を
current registry の値と比較する層は、**歴史 proof verifier ではなく current 互換検査**である。
記録 hash からの世代解決を配線しない。certified 成果物の再検証可能性を語るとき、この層は
その範囲に含めない。

再訪条件は、世代を跨いだ再検証が研究上必要になったときとする。

**理由:**
- 契約世代が進めばこの層は必ず赤くなる。意味を決めないまま放置すると、赤の原因が
  「証拠が壊れた」のか「current と違うだけ」なのか読み手に判別できない。
- resolver を配線すると、この入口が publish 済み artifact の歴史検証も兼ねることになり、
  live/read-only の分離 (D202) と同型の曖昧さを新たに作る。プロトタイプ基準 (D205) では
  投資に見合わない。

**却下した選択肢:**
- 歴史 verifier として resolver を配線する — 研究の前進に直接効かない堅牢化であり、
  ユーザー裁定で推奨が反転した。
- 既存の decision 本文を書き換えて表現を狭める — 決定本文は書き換えず後続決定で範囲を狭めるのが
  この台帳の筋である。
