# [T-2773] 段 1 brief — mocc 温度述語 template 接続の機械実証 (wave 2)

- wave: `dev-wave-t2773-mocc-template-wave2`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2`、branch `worktree-dev-wave-t2773-mocc-template-wave2`、base = local main `657e1e5a7` (worktree 作成 21:44 JST は `a99425b66`、peer 通知 (T-2489 land) を契機に 22:03 JST に ff-only で前進。差分は T-2489 の docs / insight / paper_story a2 test のみで本 wave の編集面と重複なし。submodule 511c9538、開始 gate rc=0)
- 起点: ユーザーの `/dev-wave [T-2773]` 引数 + ユーザー決定 (2026-09-19)「mocc 温度述語軸のオンボーディング段階 A を承認し、T-2773 wave 2 の機械実証を認可する。探索および pin 前進は認可しない」
- 設計正本: `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` §5・§8〜§13 (逐語 = `wave-artifacts/verbatim/t2757-design-README.md`)、D2134 項 1〜9、D579、D38 決定 4、D95
- 前提 wave 1 = **T-2772** (`output/insights/2026-09-18/t2772-mocc-mutation-proof-wave1/`、worklog entry 1666、main に land 済み、36 走 all_pass、12/12 KILLED)。引数の「wave 1 = t2780」は pilot discriminator (T-2780、mocc trace pilot の入力配線) であり D2134 項 8 の wave 1 ではない。両者とも main 上に実在する (実測: `patches/broken-mocc-hot-update-unlock.patch`、`orchestrator/campaign/s3_mocc_mutation_proof.py`、`output/env/pegasus/calibration/s3_mocc_mutation_proof.json` が HEAD にある)

## 研究前進 (1 行)

論文主張「AI が workload 特化 CC を合成・選択する枝が Silo 以外の protocol (mocc) にも開ける」の**土台**。止めている研究 = mocc 温度述語軸の変異探索 (D579 が auditor-live 相当の機械実証を前提に要求)。最小差分 = 設計 §12 wave 2 の表 (template・軸定数・計装 template 版・auditor mocc 節・DQ / consumer 束縛の対照・gate test・n=1)。完了判定 = **当該 template に束縛された機械証拠 JSON (同一性 3 比較・DQ 対照・consumer 束縛対照・hot/cold check が all_pass) と別記の n=1 素材 3 候補**。本 wave の緑は探索・pin 前進・certified 比較・正式な軸採用のいずれも認可しない (D2134 項 9)。

## scope

- 作る: (1) `patches/mocc-temperature-predicate-variant.patch` (file-scope helper に唯一の EVOLVE-BLOCK、hole = bool 式 1 個、4 callsite 296/459/566/970、OFF 側は helper 宣言も消し原文逐語、`cmake/Options.cmake` universal 相乗り `CCBENCH_MOCC_TEMP_PREDICATE` → `MOCC_TEMP_PREDICATE` 既定 0)。(2) `orchestrator/campaign/axis_mocc_temperature.py` (MARKER_ID / SOURCE_REL / TEMPLATE_PATCH / FLAG / frozen bytes / 読取契約 / PIN / proof 束縛関数)。(3) 計装 patch の template 版 (新 file。`#line` を template 適用後の論理行へ再生成。旧 `instr-mocc-lock-coverage.patch` は 1 byte も変えない — sha が 12 file に pin されている)。(4) 新 driver + 新 JSON (P1・P2)。(5) DQ 対照 (frame-altered / outside-region / hole-escape / malformed + benign 受理)。(6) `.claude/agents/auditor.md` の mocc 節 (P7)。(7) gate test (P6) と consumer 束縛の 3 対照 (P5)。(8) 登録簿閉包 (P9)。(9) `patches/README.md` の mocc 節に template と計装 template 版の項。(10) fresh auditor n=1 の 3 候補 (P8)。
- scope 外 (引数・D2134・§13): 探索 loop driver、pin 前進 (旧 pin↔候補の D297 比較は別 T)、正式 template の承認、追加 gate、read 側 hot 経路 / RLL / DELETE の witness、auditor 型番号の連番拡張、verifier 編集、broken 4 patch の template 版。

## 確定済みユーザー裁定・既裁定 (再裁定しない)

- 段階 A 承認・wave 2 認可・探索 / pin 前進は非認可 (ユーザー 2026-09-19)。段階 B (敵対レビュー) は段 6 のレビュー 2 本で兼ねる (引数)。
- D2134 項 1 (hole = 温度述語、契約 = 4 site で同じ分類、読取契約 = 値渡しと定数だけ)、項 2 (安全論拠は既存防壁の保存に限定)、項 3 (証拠を経路共通 / template 依存に二分)、項 5 (n=1 は `all_pass` に入れない)、項 6 (gate の鍵 = template または軸 module の登録、EBS 所属は使わない、consumer 束縛の 3 対照)、項 7 (I 行は gate に含めない)、項 9 (非解禁)。
- D95: 実装面は Codex `role=author` が書く。親は docs-only 本文だけ編集する。`.claude/agents/auditor.md` とその pin 3 箇所も author に書かせる (role file は機械が sha で消費する設定)。

## 不変条件

- 規律 1: 計装は `#if TRACE` 内、template は CC-native (perf build に常駐する述語) で **OFF 側は前処理本文が e9e477ca と一致** (`source_digest` 実 resolver で `src_token="stock"`)。同一 template 状態で計装なし↔ありは TRACE=0 の (論理行, 非空本文) 列一致 (D1687)。
- 規律 2: DQ は deny-only。auditor pass は機械 reject を覆せない (`auditor_gate.apply_mandatory_deny_only_veto`)。読取契約を緩める提案・DQ 対照の期待値を「受理」へ倒す変更は採らない。
- 旧 bytes 不変: `instr-mocc-lock-coverage.patch` (sha e9e65b78… が 12 file に pin)、broken 4 patch、`s3_mocc_lock_coverage.{py,json}`、`s3_mocc_mutation_proof.{py,json}` (wave 1 JSON sha c99aedb9…)。wave 2 は新 file で足す。
- `.claude/agents/auditor.md` (sha a0912ebb…) を変えたら同 commit で `.codex/role-adapters/auditor.json` (`render_adapter` 出力)、`orchestrator/codex_roles/review_ledger.py` の `SOURCE_FILE_SHA256["auditor"]`、`orchestrator/tests/test_reflux_originless_compatibility.py` の role_file_sha256 baseline (T-2528 型の `_extend_*` 追記) を追随する (F433 型)。description は変えない。`auditor_gate.py` の型番号 1〜21 schema は変えない。
- 新 define `MOCC_TEMP_PREDICATE` は `condition_meaning_gate.DEFINE_SPECS` (ROUTE_CMAKE_CACHE、mocc owner、template patch) + witness、`test_ccbench_spawn_sites.py` の Counter pin、新 build 関数の `materializer_admission` NON_ADMISSIBLE 登録、`test_p3_s4_loop.py` の patches/*.patch 走査 (IZANAGI_ トークン) を閉じる。
- `patches/ledger.json` は ability probe 専用 (entry 1 固定)。鍵・登録先に流用しない。
- 事前登録: 変異 matrix は段 4 で M0〜Mn を事前登録し、結果を見てから期待値を変えない。

## 成果物の形

| 物 | path | 束縛 |
|---|---|---|
| template | `patches/mocc-temperature-predicate-variant.patch` | touch set = {`cmake/Options.cmake`, `cc/mocc/transaction.cc`}、marker id `mocc-temperature-predicate` |
| 軸定数 | `orchestrator/campaign/axis_mocc_temperature.py` | `MARKER_ID`/`SOURCE_REL`/`TEMPLATE_PATCH`/`FLAG`/`FROZEN_TEMPLATE_*_BYTES`/`SYNTAX_CONTRACT_*`/`PIN`/proof 束縛関数 |
| 計装 template 版 | `patches/instr-mocc-lock-coverage-temperature.patch` (名は plan で確定) | preimage = e9e477ca + template |
| driver / JSON | `orchestrator/campaign/s3_mocc_template_proof.py` / `output/env/pegasus/calibration/s3_mocc_template_proof.json` (P2) | template sha・計装 template 版 sha・wave 1 JSON sha・e9e477ca |
| test | `orchestrator/tests/test_mocc_template_proof.py` (gate test・DQ 対照・consumer 束縛 3 対照・JSON consumer・軸 module 契約) | |
| auditor | `.claude/agents/auditor.md` mocc 節 + pin 3 箇所 | §9.1 |
| n=1 | `output/insights/2026-09-19/t2773-mocc-template-wave2/auditor-n1.md` + 候補 diff・digest・射影・実応答 | 機械 JSON とは別記 |

## 親の provisional 裁定 (攻撃対象)

- (P1) **wave 2 の compute = template ON (stock 等価述語 B) の stock 12 走** (W / U × hot 0 / cold 21 / default 10 × 1 / 4 thread、certified & silent) + 同 template 状態の trace0 同一性 (計装 template 版なし↔あり) + identity 2 比較 (無 template↔OFF は `src_token="stock"`、OFF↔ON-B は別 identity)。broken 4 patch は template 上で再走しない — 経路共通は wave 1 が済 (D2134 項 3)、broken patch の template 版は scope 外。所要見込み = wave 1 実測 (stock 12 走の verifier 最大 54.8 秒、Elapse 791 秒 / 36 走) から 400〜600 秒。
- (P2) **wave 1 の driver / JSON の bytes は不変。** wave 2 は新 driver `s3_mocc_template_proof.py` (wave 1 / T-2294 の helper を import) と新 JSON (schema `s3-mocc-template-proof/v1`) を作り、`wave1_proof` field で wave 1 JSON の path / sha256 を束縛する (鎖 wave 2 → wave 1 → T-2294)。設計 §12 の「wave 1 の driver / test / JSON の拡張」は import 再利用で読む (D2134 項 5 の「歴史的結果を書き換えない」と整合)。新 driver は template の 2 file touch を許し、計装 template 版は transaction 単独 touch を要求する。
- (P3) **骨格**: file scope の `#if MOCC_TEMP_PREDICATE` 内、anonymous namespace の `inline bool izanagi_mocc_is_hot(std::uint64_t temp, std::uint64_t threshold)` (型は `Epotemp::temp` = `uint64_t : 32` の昇格、`FLAGS_temp_threshold` = `uint64`)。EVOLVE-BLOCK marker は helper 本体内に 1 組 (`#if MOCC_TEMP_PREDICATE` / hole 1 行 / `#else` stock 等価述語の逐語 (frame) / `#endif`)、DQ parser 契約に従う。4 site は `#if MOCC_TEMP_PREDICATE` helper 呼出 `#else` 原文逐語 `#endif`、970 の `|| (*itr).failed_verification_` は両枝で保存。`#ifndef MOCC_TEMP_PREDICATE #error` を置く (Silo 軸と同型)。
- (P4) 計装 template 版は preimage = e9e477ca + template。`#line` は template 適用後の論理行 (helper 挿入 + 4 site の増分) を復元する。
- (P5) **consumer 束縛** = 軸 module が公開する 1 関数 (proof JSON の template sha / SOURCE_REL / PIN / 計装 template 版 sha の一致を要求し不一致は例外) と、それを将来の consumer が呼ぶ契約テスト。3 対照 = 別名・別配置 template → 拒否、軸 module の定数を使わず literal を直接持つ形 → 同じ proof 要求へ到達 (gate の鍵 (a) で発火)、marker 導入済み checkout を直書き PIN で取る → 拒否。実 loop driver は作らない。
- (P6) **gate test** の鍵 = (a) `patches/*.patch` のうち `cc/mocc/transaction.cc` に `EVOLVE-BLOCK-BEGIN` を導入する patch の存在、(b) `orchestrator/campaign/axis_*.py` のうち `SOURCE_REL == "cc/mocc/transaction.cc"` かつ `MARKER_ID` と `TEMPLATE_PATCH` を持つ module の存在。どちらかで発火し、新 JSON の実在・`all_pass`・sha 束縛・必須 key・auditor.md の mocc 行 (型 8/9/13/16 とチェックリスト 11〜13 への mocc 追記) を要求する。既存 trace-hook だけなら発火しない (負例)。
- (P7) auditor.md は既存型番号への mocc 追記 (§9.1 表) と 5 分類。連番 22 以降は足さない。
- (P8) **n=1** = Claude の `auditor` subagent (fresh・Read/Grep/Glob) 1 呼で 3 候補 (A1' lockskip 相当 → reject、A2' `FLAGS_clocks_per_us` 読取 → reject、B' `!(temp < threshold)` → pass)。入力射影 = template 適用後の transaction.cc、template、候補 diff、digest、不可触箇所、性能値を除いた構造化 verify 結果。fitness / 勝ち筋 / 期待 verdict は渡さない。段 6 fix・compute 後に 1 回。
- (P9) 登録簿: `MOCC_TEMP_PREDICATE` は ROUTE_CMAKE_CACHE (Silo 軸と同型)。新 build 関数は NON_ADMISSIBLE。
- (P10) 受入・実測環境: compute = Pegasus gen_S の generic dispatch (wave 1 と同型)、login は build / preprocess / DQ / test の生死確認のみ。受入全走・変異 matrix は計算ノード dispatch。

## 並列分割方針

段 2 plan 1 (read-only、file:line)。段 3 consult 2 (A = 正しさ境界: 読取契約・DQ / auditor の素通り・規律 1 の同一性・4 site 契約の穴 / B = 閉包・pin・過剰: 登録簿・sha pin・gate の鍵の偽陽性 / 偽陰性・scope 肥大)。段 5 author 1 (全 file 所有、worktree 内)。段 6 review 2 + fix 1〜2 + 変異 matrix + compute 1〜2 + n=1 1 呼。

## DW-G05 (放置時の成果物影響)

本 wave が未達でも certified 選択・レポート・台帳の値は変わらない (mocc の変異面は閉じたまま)。must-fix の基準 = 「template に束縛された機械証拠の意味 (同一性・DQ・consumer 束縛・hot/cold) を変える欠陥」だけ。
