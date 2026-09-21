---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-t2344-source-bound-emitters
seq: 2
---

## {{D:prior-grammar-collected-without-confirmed-corpus}}. 直前 grammar の歴史収載は、実在 corpus が未確認でも tuple を動かす同じ commit で行う (本 wave の政策判断、裁定パッケージ)

**決定 (実装 wave の裁定、ユーザー裁定を求める):** enforcement source closure の収載 tuple を動かす変更単位では、
**直前の grammar の歴史収載を、その grammar の実在 corpus が確認できていなくても同じ commit に含める。**
本 wave は exact-85 (直前 grammar) を、指定走査で記録済み lock を検出できないまま収載した。
D1653 (D1770 が追認) の「収載する grammar は実在 corpus が確認できたものだけ」は**収載時点で未充足**である。
これは既裁定から必然的に導ける結論ではなく、本 wave の政策判断であり、insight §8 の裁定パッケージでユーザーの
裁定を求める。撤去は exact-85 の独立 literal・兄弟 validator・歴史 decoder 分岐・grammar 固有 scope 定数・
新設 test 群の削除で足り、exact-63 以前の経路と certified 経路には影響しない。

**理由:**

- 観測 (事実): 指定した走査条件 (`/work/1/SFC/tanab` と `/home/SFC/tanab`、`.git` / `external` / `__pycache__` /
  `node_modules` / `.cache` を除外、mtime ≥ 2026-09-20 21:55、2026-09-21 08:31〜08:45 の区間) で 85-key v2 の
  campaign.lock は**未検出**。exact 照合済みの exact-85 corpus は未確認である (不在の証明ではない)。
- 生成可能性 (事実): 現行 production の capture 経路は、収載 85 本の clean な木で exact-85 の binding を返す
  (`output/insights/2026-09-21/t2344-closure-emitters/exact85-reachable.json`)。
- 予測 (不確実): 直前 grammar の lock は、main で tuple が前進した後も、前進前の commit に固定された木から生まれうる。
  exact-63 では main の land (09-21 00:21) 後の 00:34〜03:53 に 25 本が記録されていた (同一の固定木による反復なので、
  exact-85 で同じ発生が起きる独立証拠ではない)。
- 政策判断: D2194 項 4 と D2193 は「tuple を動かす変更単位には直前 grammar の歴史収載を同 commit で含める」と定める。
  収載しない誤りは、後から収載するまで記録が両経路から読めない状態を作り、その解消には別 commit が要る
  (exact-62 のときは 8 日の空白になった)。収載しすぎる誤りは、HISTORICAL_RAW の exact ordered tuple が 1 個増えるだけで
  certified の受理集合は変わらない。**取り返しの非対称性**を根拠に収載を選んだ。

**却下した選択肢:**

- **corpus 未確認なら収載しない (D1653 の字義)** — land 後に旧 grammar の lock が生まれた場合、別 commit を要する空白を作る。
- **受入直前に再走査し 1 本以上なら収載する** — 走査時点の 0 は land 後の発生を防がないため、同じ空白が残る。
  実装を 2 通り用意する費用も生じる。
- **exact-85 の lock を自分で作って corpus を満たす** — 条件を満たすための成果物生成であり、gate の骨抜きになる。

**保証しない範囲 (記録):** 歴史収載は記録 commit の blob との整合を検査するが、**その lock が実際に発行されたことも、
実在 corpus があることも認証しない**。記録 commit の 85 blob と整合する合成 lock も歴史入口で読める。
本決定は「production に存在した grammar なら corpus 未確認でも事前収載してよい」という先例を作る。
歴史型・validator・scope 定数・test 群の恒久保守が費用として残る。

## {{D:closure-stage-emitters-first}}. enforcement source closure の次段は発行器 6 本と発行器起点にだけ居る module を収載する (exact 85 → 96)

**決定 (D2194 項 4 (1) の実装、実装 wave の裁定):** 収載 tuple を exact 85 から **exact 96** に進める。
収載するのは D2194 項 4 が名指しした発行器 6 本と「発行器起点の import 展開にだけ現れる 10 本」の**和 11 本**で、
5 本が重複するため 16 本ではない (`autonomous_trial_completeness` だけは tuple 起点の発見集合に既にあった)。
既存 85 の宣言順は動かさず、11 本を path の sorted 順で末尾へ足す (D2193)。tuple 起点の 2 段目 23 本は含めない
(新 11 本との重なりは 0)。scope 文言は D2081 の形式で「curated exact 96 path; 2026-09-21 (5efd69367 の source 木、
本版の 96 path を起点) の実測では 173 module、うち収載 96 / 未収載 77」とする。

**理由:**

- 96 本を起点に辿った発見集合は 173 module で、従来の「tuple 起点 163 と発行器起点 168 の和」と**同一集合**になる
  (`closure-head.json`)。発行器を seed に足したことで候補集合の定義が tuple 起点だけに依らなくなった。
- 収載が発行器に与えるのは (a) campaign 開始時に発行器の bytes を lock へ記録すること、
  (b) certified 受理時に現行収載 path が clean committed であることの要求 (`artifact_admission.py` の
  `capture_contract_loader_binding`) の 2 つである。**発行時 bytes と記録 bytes の同一性は要求しない** (D1163 のまま)。
- 「発行器 6 本」は D2194 項 4 が選んだ seed であって certified consumer の全数ではない
  (`backoff_sweep_report` / `backoff_requested_us` / `b10_backoff_static_tail_formal` / `t1998_stock_inline_pair` /
  `layer3_report` も certified 経路を持つ)。全数を名乗らない。

**却下した選択肢:**

- **「6 + 10 = 16 本」として重複を二重に数える** — 実測では和が 11 本である。
- **2 段目 23 本を同時に足す** — D2194 項 4 が「その後」と定めた。
- **`b10_backoff_shape_sweep` の report 分岐にも収載の検査を掛ける** — 同分岐は歴史 exact-24 限定で現行 capture を
  通らない。掛けるには新しい機構が要り、本 wave の scope 外である。

**保証しない範囲 (記録):** 「certified 経路が source-bound である」は推移閉包の意味では引き続き名乗らない
(96 起点の発見集合 173 のうち未収載 77)。「発行器起点も閉じた」とも書かない。
`artifact_admission.py` の bytes が変わるので新規 admission receipt の `validator.sha256` は変わり、
B-4 projection hash の材料にも同 file が入る (D2081 が既に限界として記す)。記録済み成果物の bytes は変えない。
