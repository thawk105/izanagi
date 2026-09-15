# [T-2545] 段 1 brief — D1881 の名指し実装

- wave: `dev-wave-t2545-b4-publication-root`
- branch: `worktree-dev-wave-t2545-b4-publication-root` / base `61e0e9c4a`
- 対象裁定: D1881 (decisions.md の `## D1881`)。後続の上書き・停止裁定は無い。

## 研究前進

B-4 還流 ablation の事前登録は「file-drawer を閉じる」方向の主張を持つが、発行器の
publication root を呼び手が実行時に選べるため、D1846 の bootstrap 束縛は
「その hash を持つ registry を別 root へ発行すれば通る」形で恒真化しうる (D1881 理由節)。
本 wave は事前登録が root を 1 つ名指しし、発行器がそれ以外を拒否することで、
`publication_under_a_different_root_is_not_prevented` を実際に閉じる。
完了判定 = 発行器が名指し root 以外の発行を型付き reason で拒否する負例と、
名指し root での発行が通る正例が、実 repo の事前登録文書を読んで両方成立すること。

## 確定済みユーザー裁定 (設計は変えない)

- D1881: 事前登録が publication root を **1 つ**名指しする。発行器はそれ以外での発行を拒否する。
  却下済み = 現状維持。「新しい機構を作らない」「事前登録に 1 行足すだけで閉じる」。
- 依頼: 名指しの実装に限定。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- D2016 項 6: **凍結済みの §5.1.1 には 1 byte も触れない。**
- D1936: 各実装は名指しの変更に限定し、付随する gate・台帳・汎用化を足さない。

## 不変条件 (DW-G05 / 規律 2)

1. **受理集合は狭まるだけ。** 既存の拒否 reason・拒否条件を 1 つも緩めない。
   名指し root での既存の全拒否 (root 既存・symlink 成分・planned result 衝突など) は不変。
2. §5.1.1 の bytes を変えない。`p3_b4_analysis_prereg_consumer._locate_section` は
   §5.1.1 直下の H5 を**ちょうど 6 個・指紋順一致**で要求する (`_H5_FINGERPRINTS`)。
   §5.1.1 内への H5 追加・削除・並べ替えは即赤。
3. 解析 source closure `_CLOSURE_PATHS` の 5 module を変えない (発行器は非メンバ)。
4. `orchestrator/campaign/p3_b4_producer_auth_experiment.py` の `_ISSUER_PATCHES` が持つ
   発行器への byte 逐語錨 3 本を壊さない。とくに錨 3 =
   docstring `"""Issue exactly one B-4 pre-run publication under a new absolute root."""`
   + 空行 + `    root = _canonical_absolute_path(\n`。**この間へ挿入してはならない。**
   `CHANGE_CLOSURES[Candidate.ISSUER] = (2, 1, 2)` の 3 数も期待値なので整合を確認する。
5. 発行済みの固定名成果物は `output/` 配下に 0 件 (事前登録 §7.2 追記)。
   よって既存 publication の再発行・無効化は発生しない。
6. 事前登録は `tools/check_docs.py` の LIVING_DOCS 在籍 (発効前は living)。
   docs 間の行番号参照を作らない。マシン固有 path を持ち込まない。

## scope と成果物の形

- `docs/phase3-b4-reflux-ablation-preregistration.md`: publication root を 1 つ名指しする行を
  §5.1.1 の**外**へ足す (+ 読み手が曖昧にならない最小の文脈)。値は repo 相対 path。
- `orchestrator/campaign/p3_b4_prerun_issuer.py`: 事前登録の名指しを読み、
  canonical 化後の root が名指しと一致しなければ新しい型付き reason で拒否する。
  **RNG 取得と publication root 作成より前**に拒否する (既存の早期拒否と同じ位置づけ)。
- `orchestrator/tests/test_p3_b4_prerun_issuer.py`: 負例 (別 root → 新 reason で拒否)、
  正例 (名指し root → 既存の完全 bundle 発行が通る)。新規 test file は作らない。
- `orchestrator/tests/acceptance_duration_ledger.json`: 追加 nodeid の所要を登録する。

## scope 外 (実装しない)

- 非保証列 `B4_PRERUN_NON_GUARANTEES` の書き換え = T-2546 (b4-stale-non-guarantees)。
  本 wave で発行器の挙動が変わる結果として当該項が stale になるかは段 4 で裁定し、
  越境実装はしない。
- `load_b4_prerun_publication` 側 / `p3_s4_loop.require_b4_proposal_registry_binding` 側への
  同型検査の追加。D1881 は**発行器**だけを名指す。
- 母集合・選択関数・§5 の欄・解析 consumer の受理形。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- (P1) 名指しの置き場所は §5.1.1 の外。§6「実走の前提条件」と §5.1 の新規 bullet が候補。
  §5.1 は「欄別の解除条件 (規範。§5 の値セルへ書かない)」なので、値そのものを書く場所として
  適切かは割れる。**親の暫定裁定 = §6 に置く。**
- (P2) 名指しの値は `output/` 配下の repo 相対 path 1 つ。発行器は絶対 path を要求するので、
  repo root (`Path(__file__).resolve().parents[2]`、`p3_b4_material_report` の既存 idiom) から
  解決して比較する。**repo root 解決が実行環境で成立するかは段 2 で file:line まで確認させる。**
- (P3) 検査位置は `root = _canonical_absolute_path(...)` の**直後**。錨 3 を壊さず、
  かつ `_ensure_new_publication_root` より前に入る。
- (P4) 事前登録の読み取りは exact literal 1 本の抽出で足り、新しい parser 族を作らない。
  §5.1.1 の semantic digest 経路とは独立にする。

## 並列分割方針

実装面は素集合 1 単位 (発行器 + その test + 所要台帳) なので段 5 は実装子 1 本。
docs 本文は親が書く。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズを分ける)、
段 6 レビュー 2 本 + fix。受理集合が変わる wave なので敵対検証子は省略しない (DW-C00)。
