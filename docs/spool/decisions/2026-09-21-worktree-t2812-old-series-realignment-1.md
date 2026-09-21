---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: worktree-t2812-old-series-realignment
seq: 1
---

## {{D:old-series-realignment-measured}}. 旧系列 4 本の新 pin main への整合を実測で分け、B-4 床値 f1 の固定 checkout 継続は裁定へ返さず、g1 の live launch だけを設計択一として提示する

**決定 (親の実施判断。ユーザー裁定ではない):** ccbench pin 前進 (D2150 項 1、D2184) の後に旧系列を新 main から再開・再投入するための整合を、login の read-only 実測に基づいて次のとおり分ける。実装・reseal の実行・候補 file の削除・認可改訂・再投入はいずれも本 wave では行わない。

1. **K2 の巡と A-1 sized v3 は、pin の整合を追加で要しない。** D1777 (投入前に submodule を対象 PIN へ checkout し、gitlink の差は commit しない) の既存手順で、`patchharness.assert_pinned_clean` と A-1 の CCBench 境界・source 契約はいずれも通る (実測)。両系列の driver の独立 full OID は据え置き、新しい campaign は現行 policy の新 identity・新 lock を持つ。旧 lock の live な再消費は、pin とは別に enforcement source closure の前進 (exact-63 → 85) で現行 codec が拒否する。
2. **B-4 床値 f1 の w2 と finalize は、既存の submit-tree から継続する。** 窓 JSONL の `loaded_head` と HEAD の一致を submitter が要求するので、これは系列の設計であって新しい択ではない。裁定へ返さない。新しい床値系列を始めるときだけ、successor protocol の発行 (AI reseal は commit 後に解決対象となる)・再 build・新 record・spec の再凍結・submitter の sha 束縛・B-10 grid の凍結木 pin の更新を一括して裁定する。B-4 本走は base driver 側の対応証拠の実装 (D2194 項 3) の着地に依存する。
3. **凍結 v2 g1 の live launch だけが、新 main の code で塞がっている。** 観測された最初の拒否は manifest 内 binary の admission policy 不一致で、12 cell すべてが同一の文言である。同じ期待値のまま policy を記録値にすると 12/12 が通る。段階 4 の残部と段階 5 以降は未観測であり、protocol は現行 env 契約の `contract_sha256` も要求する。
4. **「現行 registry + 系列自身の pin」で組み直した policy は、記録値に exact 一致する** (production の正規化関数で計算、g1 の 12 receipt・B-4 の portable record・A-1 の campaign identity preimage のいずれとも一致)。よって live の期待 policy を批准 protocol の pin で組み直す択 (以下 S') の要求値は到達可能である。S' の射程は launch 段階 4、W-5 の store 消費、記録済み binary を消費 checkout へ配置する経路の 3 入口に限る。
5. **S' は D2184 が却下した 4 種 (policy 照合の除去、resolver の曖昧 fallback、receipt の張り替え、live への `expected_policy=None`) のいずれでもないが、「現行 repository の stock pin への依存を切り離す」効果では D2184 が「必要なら別の裁定」と書いた択と実質同じである。** したがって無裁定で実装せず、O' (pin 前進直前 main への修正移植) と N (新 pin の新世代。世代 1 以外を拒否する現行契約のため g2 の設計が別途要る) と並べて裁定パッケージとして提示する。
6. **旧 binary の再 admission だけでは解消しない (D2184) の理由を実測で特定した。** 記録済み receipt に stock baseline の class は 1 件も無く、review の識別子は現行 registry に登載されているので、class の導出が障害なのではない。receipt を出し直すと receipt bytes が変わり、manifest から floor_source を経て批准世代へ至る sha の束縛が崩れる — これは却下済みの receipt 張り替えに当たる。

**理由:**

- D2150 項 1 は ②③⑤ を「各新系列の着手時」に置き、D2184 は「新 main へ移行するときは系列ごとに整合を揃える」と書いた。どの系列に何が要るかは系列ごとの実測でしか分けられず、実測すると 4 系列のうち 3 系列は既存手順と既存の固定 checkout で足りることが分かった。
- 規律 7 により、記録済みの判定・測定・凍結 bytes は本 wave で 1 つも変えていない。新 main での拒否を過去の無効化と読まない。規律 2 により、policy 照合の除去・曖昧 fallback・receipt の張り替え・live への `expected_policy=None` はいずれも採らない。
- 依頼は「設計と read-only 実測が本体、実装は裁定後の別 wave、gate・台帳・一般化の追加は scope 外」と定めた。本決定はその境界の中にある。
- 既存手順 (submodule だけを対象 PIN へ checkout する投入) は 2026-09-08 のユーザー裁定 (D1777) であり、新 main からの投入実績もある。**手順そのものを新しい択として提示し直さない。** 裁定へ返すのは「旧系列の継続を固定 checkout に留める現行の既定を K2 については新 main のこの経路へ移すか」という採択と、pair 再投入 1 job + 4 巡目 1 job の予算である。

**却下した選択肢:**

- **B-4 床値 f1 の継続を裁定項として返す** — 依頼と D2184 の既定どおりであり、新しい択ではない。ユーザーの手番を増やすだけになる。
- **g1 を O (pin 前進直前 main の固定 checkout) で再開する** — その commit は launch validator の修正を持たないので、policy 以外の理由で止まる。修正を移植した別 branch (O') は択として残すが、現行 main と同じ検査を主張するには移植の閉包が増える。
- **旧 binary へ新しい receipt を発行して再 admission する** — 却下済みの receipt 張り替えに当たり、批准世代の sha 束縛も崩す。
- **live 経路の policy 照合を外す / `expected_policy` を無指定にする** — D2184 の却下どおり。正しさ防壁を緩める。
- **S' を無裁定で実装する** — 受理集合を広げる変更であり、D2184 が別の裁定へ返した択と効果が重なる。
