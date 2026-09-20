単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s1-brief.md
- 段 4 裁定と plan v2・変異事前登録 (レビュー対象に含める。末尾の追記は変異経路の訂正): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s4-adjudication.md
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s5-author.md
- 統合後の差分 (着手時 local main b7f970dfa → wave tip 04ae82a1c、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/verbatim/review-diff.patch
- 生成器 (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/plot_b7_fixed5_regression.py
- test (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/orchestrator/tests/test_plot_b7_fixed5_regression.py
- figures README の fig10 節 (末尾の節。一覧表の fig10 行も): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/README.md
- 着地 provenance: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.provenance.json
- caption_source の稿 (値・判定・限定の出所): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md
- 権威 bytes: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json
- raw manifest: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/raw-manifest.json
- 床値 JSON (rr95。他 2 本は同 dir の rr5 / rr50): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json
- durable raw cell JSON (repo 外、読むだけ): /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/jobs/rr95/raw/rr95-fixed5.json
- 作図規約: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/FIGURE_CONVENTIONS.md
- fig9 の雛形 (比較用): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/plot_a1_sized_paired.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo に足した**論文図 (fig10) の生成器・test・README の設計レビュー**である。セキュリティ調査ではない。目的は、
(1) 図・caption・README・provenance の値と判定が一次資料 (certification.json、raw cell JSON、床値 JSON、稿) と一致しているか、
(2) 生成器の各検査が実際に効くか (恒真な検査、同じ入力を別の層が先に拒否して意味を持たない検査、fail-open な経路が無いか)、
(3) 生成器が判定を「作って」いないか (D2162: 床値判定はコードに入れず稿で計算する。図は稿の判定を写し、述語との整合だけを検査する裁定)、
(4) 規律 1 (性能値は trace-disabled)・規律 2 (certified を性能認証と言わない)・規律 7 (前後比較しない)・F36 (稿に provenance hash を書かない) を点検することである。
差分は commit 済みで、図 3 成果物の生成 (login で実 durable root に対して実走、rc=0) と README 3 file の編集は**親が実行済み**である。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査と、`python3` での値の再計算 (読むだけ) はしてよい。

# 依頼 — レンズ「正しさ境界・整合・実効性」で実装と文書を点検する

## 点検項目

1. 値の一致: provenance の `cells[].samples_tps` / `median_tps` / `effects` / `floors` / `judgments` と、稿 §2.1 / §2.2 / §1.4、certification.json、raw cell JSON、床値 JSON を
   独立に照合する (少なくとも rr95 の 2 cell は raw から自分で読む)。caption の百分率・request・pin・source commit・条件が一次資料と一致するか。
   README fig10 節・一覧行・着地 SHA-256 3 行と provenance `outputs[].sha256` の一致。
2. 検査の実効性: `_authority_data` / `load_evidence` / `validate_repo_closure` / `validate_external_sources` / `check_figure_layout` の各 `_require` について、
   (a) 恒真になっていないか、(b) 同じ入力を前段の別検査が先に拒否して単独では発火しないもの (F820 の単一理由性)、(c) 例外の握り潰し・fail-open、
   (d) test が実体の関数を通しているか (stub / monkeypatch で機構を迂回していないか、F649)、(e) fixture の実寸 (FIGURE_CONVENTIONS §10) を点検する。
3. 判定の出所: 生成器が `RECORDED_JUDGMENT` を写して述語一致を検査する形は D2162 の趣旨に収まるか。逆に、記録判定を変えれば通ってしまう (定数と述語が両方
   一致すれば何でも通る) 経路について、test と稿照合 (`test_pins_floors_effects_and_judgments_match_results_document`) がそれを縛っているか。
4. 規律: caption / README が certified を性能認証と言っていないか、anomaly 0 を raw に無い根拠で言っていないか、既存材料との前後比較・プールを示唆していないか、
   同一 binary・同時実行を主張していないか。`performance.trace_enabled is False` と `correctness[].trace_enabled is True` の両方を要求しているか (規律 1)。
5. 変異事前登録 (裁定末尾の表 13 件) の各 negative 変異について、対応 test がその変異だけで赤になるか (kill の単一理由性)、位置が一意か (DW-M04)、
   期待 node に問題が無いかを静的に評価する。単一理由でない疑いのある id を列挙する。
6. 親 brief / 裁定自身の誤り (前提、実測値、一般化、F/D 番号の誤引用) を点検する。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 所見
各所見を `B-1`〜 で採番し、種別 (must-fix / should / nit / backlog)、対象 (file と関数名または節名)、内容、放置時に成果物 (図・caption・README・受理集合) がどう変わるか (DW-G05 の 1 行) を書く。
## 値の照合結果
上の 1 の結果を表で (一致 / 不一致)。
## 変異事前登録への所見
上の 5 の結果。
## 親 brief / 裁定への所見
上の 6 の結果。
## 総括
must-fix の件数と要旨、実装をこのまま採ってよいかの判定 (GO / NO-GO) を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
