---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t1799-post-oracle-regen-ban
seq: 2
---

## {{D:post-oracle-regen-ban-narrow-protection}}. 判定後の材料再生成の禁止は、実効 build 根とその配下だけを build 中に書込み不能にして実装する

**決定:** D984 の 2 手段のうち「判定後の source tree の書込み不能化」を採る。
`buildcache._build_v2_impl` の post-oracle 束縛がある経路で、configure 成功後の既存 2 検査
(`_assert_fetchcontent_fully_disconnected_effective` と `_assert_post_oracle_dependency_material`)
の後に `_masstree_source_root_from_cmake_cache(staging)` で実効 build 根を読み、
binding が指す `<fetchcontent_base_dir>/masstree-src` と **exact 一致**することを要求してから、
その根**とその配下の全 node だけ**を `cmake --build` の間だけ書込み不能にする。

- **親 directory (= `FETCHCONTENT_BASE_DIR` そのもの) には触れない。**
  既存の汎用 snapshot 保護 (`s8b_expected_materialization.make_snapshot_non_writable()`) は
  parent の write bit も外すため、`<base>` 直下への新規 entry 作成 (別依存の populate、
  masstree prebuild directory) を巻き添えで壊す。as-is 再利用は採らない。
- 保護に入る時点で**根 directory 自身が書込み可能であること**を要求し、そうでなければ
  write bit を 1 つも触らずに拒否する。これは排他機構ではなく保護の前提条件であり、
  同じ根への二重保護を構造的に起こさせない。
- 既存の post-oracle 照合 (初期・configure 前・configure 後の disconnected + material・
  build 後 material・build 後の実効根照合) は 1 つも削らず、緩めず、順序も変えない。
  build 後の実効根は**保護用に読んだ値を流用せず改めて取得する**。
- post-oracle 束縛の無い build の configure argv・cache identity・receipt schema・
  受理集合は 1 byte も変えない。

**理由:**

- **D953 が塞いだのは再取得であって再生成ではない。** `FETCHCONTENT_FULLY_DISCONNECTED=ON` は
  populate を止めるだけで、`masstree_build` の `add_custom_command` が source root 内で
  `bootstrap.sh` / `configure` / `make` / `ar` / `ranlib` を走らせる経路は残る。
  D953 自身が「実効的な排他は process 間 lock を要し、書込み権威の変更として別審査に属する」と
  書いており、D984 がその別審査である。
- **前後の hash 照合は検出であって禁止ではない。** 判定済み材料が**同一 bytes で**作り直された
  場合、manifest・`config.h`・archive・HEAD の照合はすべて同じ値を見るため通る。
  D984 は可能性そのものを残さないことを求めている。
- **検査した根と build する根が食い違いうる。** 材料検査は `<base>/masstree-src` を固定導出する
  一方、build 側は `FETCHCONTENT_SOURCE_DIR_MASSTREE` の override を受け、実効根は
  CMakeCache が非空の SOURCE_DIR を優先する。現行の実効根照合は build **後**にしかないため、
  保護を掛ける根が build に使われる根と同じであることを build 前に固定しなければ、
  保護そのものが空振りする。official floor の呼び出しでは両者は常に一致する (恒真) が、
  恒真でも保護の前提として必要である。
- **private snapshot は同じ禁止をより高い費用で実現する。** floor は既に submission payload を
  job-local base へ複製しており、判定後にもう一度 3 source を全複製すると、binding 導出・
  postflight の期待値・cleanup lifetime が連動変更になり、変更面が
  `s8b_floor_campaign.py` へ広がる。

**却下した選択肢:**

- 既存の汎用 snapshot 保護をそのまま呼ぶ — parent まで凍結し、無関係な正当 build を巻き込む。
- private snapshot からの build — 上記の費用。D984 は両手段を許可しているので、
  安い方を採って規律を満たす。
- 実効根照合を build 後だけに残す — 保護対象の根が build に使われる保証がなくなる。
- configure 後に読んだ実効根を build 後の検査へ流用する — 既存の root drift 検査を
  実質的に消し、build 中の実効根変更を新たに受理する。絶対規律 2 に反する。
- process 間 lock・復旧台帳・復旧 daemon を足す — D953 が別審査に属すると裁定済みであり、
  本 wave の scope 外である。残る限界 (強制終了で復元が走らない、交差の一時 gap) は
  実装と成果物へ明記する。
