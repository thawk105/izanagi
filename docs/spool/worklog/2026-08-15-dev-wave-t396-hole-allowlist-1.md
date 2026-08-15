---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t396-hole-allowlist
seq: 1
title: [T-396] の起票前提が 3 点とも失効しており、実装候補は敵対レンズの caller 閉包で消えた — 択一 4 件を返す (docs のみ、branch worktree-dev-wave-t396-hole-allowlist)
---

## 本文

- **[T-396] は本 wave で実装しない。設計・実測を凍結し、ユーザー択一 4 件を返す。**
  正本 = `output/insights/2026-08-15_t396-hole-allowlist-refuted/` (逐語は同 dir `verbatim/`)。
  実装差分が無いため変異 matrix は対象外 (`DW-S04`)。**受入全走は免除せず実施し、赤ゼロだった** —
  実測 = **`11034 passed, 65 skipped` (failed 0)**、145.40 秒、Pegasus gen_S request 911163、
  tested_main `152767ee` / tested_tip `5571810e`。receipt の `verdict` は `child-green`、
  `red_nodeids` は空。land する tip では同じ受入を再走して緑を再確認した
- **[T-1107] のフレークが本 wave でも発火し、受入を 1 回やり直させた。** 記録 commit を足した最終 tip の
  受入 (09:32 JST) が `test_dev_wave_wait.py::test_public_main_real_signal_releases_lease` で
  `status=attributable-red` になった。失敗内容は既知どおりで、SIGTERM 到達より先に
  `acceptance-scheduler-attestation` が `marker-count` (`observed=[]`) で発火し rc=143 でなく rc=70 になる。
  親が同 node を焦点走で回すと **1 passed / 2.16 秒**で緑 (docs のみの差分は当該 file に到達しない)。
  `DW-O18` に従い非帰属のフレークとして扱い、新しい T は起こさない。
  **新事実は頻度である** — 同じ node は 08:51 JST にも別の docs-only wave の受入を止めており、
  **約 40 分の間に連続する 2 wave を止めた**。[T-1107] は「たまに踏む」ではなく現に律速している
- **受入 attempt 1 は走行前に停止した (走行の失敗ではない)。** `preflight-submodule-ready` が rc=2 で、
  原因は入れ子 submodule `external/ccbench/third_party/shirakami` の未初期化である。
  `DW-O20` は新規 worktree について最上位の `git submodule update --init` しか書いておらず、
  そのとおりに実行すると入れ子が残る。`--init --recursive` で解消した。
  背景 job の wave は必ず踏むため、手順の是正を択一 D の材料として添える
- **起票の前提は 3 点とも現行 main で失効していた。** 台帳 (`docs/archive/worklog-phase3-0804-148.md`) は
  2026-08-04 起票で、trigger 軸の hole を「任意 1 行」「機械 gate は識別子 5 個の blacklist だけ」
  「関所は auditor だけ」と書く。並行 wave [T-428] (2026-08-04 着地) が受理経路を固定 5-bit wire +
  32 正準述語の閉集合へ置き換えており、任意テキストが hole へ入る経路は無い。
  `SYNTAX_CONTRACT_FORBIDDEN` が単独の受理関所である箇所はゼロで、production caller 3 箇所は
  いずれも membership 検査か quarantine と併用している
- **台帳が指す実装は 2026-08-05 に破棄裁定済みだった。** 先行 wave [T-409] (entry 166) が文法 v1 を
  完成させ全緑にしたが、/rulings で「択一 A = (a) land せず破棄」と裁定された (entry 193)。
  段 3 レンズ B が裁定文と択一表を**選択肢集合で**照合し、その射程は trigger 軸に限られると確認した
  (親の読みは正しい)。ただし sort 軸への実装許可ではない
- **親の段 1 実測は 3 度誤っており、いずれも段 2・段 3 が現物で反証した。** (1) 「sort 軸なら
  `pro_set_.pop_back();` + 正当な comparator の 2 文で関所は auditor だけになる」は誤り —
  `sort_swo_oracle._validate_single_sort_statement` が hole を単一 `sort(...)` 文に限定し、
  2 文形は `qualified-or-non-sort-callee` / `not-a-single-sort-statement` で機械拒否される
  (後者は既存境界テストが固定済み)。(2) 「sort 軸に識別子 blacklist が一切かかっていない」は誤り —
  `coder_effect_gate.DENY_TABLE` が host-effect 5 category と無条件ループを拒否する
  (`pro_set_` を収載していないだけ)。(3) oracle 不可用は fail-open ではなく例外送出で fail-closed
- **段 2 が唯一残した実装候補も、段 3 レンズ A の caller 閉包が反証した。**
  「materialize 済み source を `pipeline.evaluate()` / `buildcache.build()` へ直接渡す経路は
  gate を通らない」は関数単位では真だが、両 sink の production caller を全列挙して source 由来を
  分類すると、LLM 合成断片が到達する caller は 1 本も無い。LLM sort 断片の唯一の production 列は
  quarantine → auditor → SWO oracle → evaluate → build である。
  **親はレンズ A を採用し、レンズ B の所見 7 (「残余は実在する」) を refuted と裁定した** —
  レンズ B は関数の非再検査だけを見て caller 到達性を見ておらず、親と同型の誤りを繰り返している
- **D344 (2026-08-12) が本件の直接の blocker である。** その「却下した選択肢」第 1 項
  「sort comparator への typed IR / AST allowlist … 親は決めずユーザー裁定へ返す」に、
  段 2 の提案文法は選択肢集合として一致する (レンズ A・B が独立に判定)。文法が再帰的で受理集合が
  無限でも、有限 production からの合成 DSL に変わるため該当する。`DW-STOP` により親は実装できない
- **親の (P2)「宣言済み契約の機械執行だから宣言を狭めない」も成立しなかった。**
  「任意の既存 API call が副作用なしであることは C++ 意味解析なしには判定不能」であり、
  提案文法は既存正例の generic lambda (`const auto&`) を落とす
- **実装しなかったが real と裁定した所見:** closed-region 契約のうち機械執行されていない項目が 5 つ
  (lambda 内の型/関数追加、非決定ビルトイン、blacklist 外の副作用呼び出し、bounded ループ、条件付き
  `throw`)。最も重いのは **bounded / data-dependent loop が「通ること」を
  `test_coder_effect_gate.py:151` が明示的に固定している**点で、契約と実装の不一致がテストで
  恒久化されている。レンズ B はこれらより verifier の予定操作数欠落が本丸だと指摘した
- **親の誤りの型は F73「防壁の射程誤認」** (レンズ B の診断、新型ではない)。軸限定の gate 不在を
  全関所の不在へ一般化していた。段 8 の改善候補 = 段 1 で gate inventory 表 (順方向・逆方向、
  file:line、拒否条件、UNAVAILABLE 挙動、直接 caller、既存 test) を作り、その表なしに
  「gate は無い」と書かない。今回レンズ A の caller 閉包が実際にこの表であり、唯一の実装候補を
  反証したことが有効性の実証である
- **セッション異常:** 段 3 レンズ A の初回投入が上流の安全分類器に拒否され、model call 16 回・
  出力 0 bytes を空費した。F256 の再発 (再発記録は同 wave の failures fragment)。
  防御目的は prompt 冒頭に明記していたが、**後から追記した節**が「回避する C++ 文字列を構成せよ」と
  攻撃成果物の作成を求めていた。被覆監査の枠組みへ書き直して再投入し成功。凍結逐語は再投入版
- **訂正 2 件。** 正例コーパスの内訳は「sort 軸 16 件」ではなく実 C++ 実装 15 件 + `SORT_VARIANT=0` の
  stock メタデータ 1 件 (説明文を文法の正例にすると非 C++ を受理させる)。
  `check_syntax_contract` の production caller は 2 箇所でなく 3 箇所

## 次の一手差分

### 更新

- [T-396] **P1・ユーザー裁定待ち**: 起票の前提 3 点は現行 main で失効し、到達可能な reward hack 経路は
  実測で 0 件だった。台帳が指す AST allowlist は trigger 軸では 2026-08-05 に破棄裁定済み、
  sort 軸では D344 の却下選択肢に一致してユーザー裁定待ちである。実装候補は消滅した。
  返した択一は A (closed-region 契約の未実装 5 項目 — 契約側を実態へ合わせる / 実装側を契約へ
  合わせる = D344 を覆す / 現状維持)、B (テストで恒久化された bounded loop の扱い)、
  C (verifier の予定操作数検査を起票するか)、D (段 8 候補の gate inventory 1 文が L1 予算を
  85 bytes 超過したため本文編集を止めた件)。正本 =
  `output/insights/2026-08-15_t396-hole-allowlist-refuted/`
  base: 16cde725e76d0e553c3fb58834603a929fe9d7614f3b7d297f596b7fdfe33f92
