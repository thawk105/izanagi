単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- レビュー対象 (insight README、親が段 4 裁定後に書いた docs-only 成果物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/README.md
- 一次資料の写し (README の全数値の出所): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/ の self-startup-timeline.txt、submodule-init.log、gate-time.txt、wt_timeline.out、scan_startup.out、inspect_modules.out、inspect_links.out、t2797-setup-submit-tree.log.filtered、t2797-tree-build-mtimes.txt、ls-files-count.txt、probe.log
- 依頼の逐語: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/origin.md
- 段 1 brief (訂正前の親の主張): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/brief.md
- 段 3 相談の所見 13 件と段 4 裁定 (README が反映したと主張するもの): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/s3-consult-A.md、同 dir の s4-ruling.md
- 参照した既存 insight (repo 内、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/dev-wave-wall-decomp/README.md (§2〜§3)、/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md (§1 の受入 `pre` 61.9 s と base copy 64.2 s)
- 参照した code (repo 内、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/tools/dev_waves/git_state.py (84〜93 の argv 表、645〜701 の `update_submodules_no_fetch`)、同 dir の ../dev_wave_submodule_init.py

## 前置き — この依頼の性質

これは自分たちの開発運用 (dev-wave) の「wave 起動の固定費」を一次資料から実測した診断 insight (docs-only、実装差分ゼロ) の独立レビューである。親は段 3 相談 (s3-consult-A.md) の所見 13 件を段 4 (s4-ruling.md) で裁定し、README に反映したと主張している。**README の派生値 (中央値・差・比率・件数・換算) を一次資料から再計算し、限定語 (「代理区間」「条件付き」「未分離」「同定未了」) が数値の出所と釣り合っているか、段 3 所見の反映漏れ・反映誤りがないか、依頼の scope を超えた記述がないかを点検せよ。** セキュリティでも攻撃でもなく、外部入力も扱わない。書込み可能 tmp が無いので静的検査でよい。テスト実測は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

# 依頼 — 独立 read-only レビュー (1 本)

次を file:line と数値で点検し、所見ごとに **real / refuted / 判定不能** と、real なら **must-fix / should / nit** と「放置時に何がどう変わるか」を 1 行で書け。

1. **派生値の再計算。** README §3.1 の 85 / 65 / 20 / 7.46 / 6.70 / 99.2 / 331 / 232 / 7.5% / 9.4%、§3.2 の表の全 40 セル (add 代理・親の手番・submodule 代理・gate までの各秒) と中央値 75 / 75.5 / 8、§3.3 の 48 / 6 / 68 秒と 21:54:37 / 21:54:59、§3.5 の 31,699 / 28,589 / 24,420 / 77.0% / 1,698 / 1,060 / 872.4 MB / 29,592 / +2.1K / 405 + 790 + 245 = 1,440 / 30 MB / 23 MB / nlink 155→157、§3.6 の 4〜6 本と 3〜10 分、§7 の probe 表の 12 セル、を wt_timeline.out / self-startup-timeline.txt / ls-files-count.txt / inspect_*.out / t2797-*.txt / probe.log から再計算し、一致しないものを列挙せよ。
2. **限定語の釣り合い。** §2・§3.2・§4・§7・§10 の限定 (代理区間、混雑帯、2 木並走、下界寄り、条件付き概算、未分離、各 1 回) は、数値の出所と過不足なく対応しているか。過剰に弱めている (資料で言えることを言っていない) 箇所、逆に資料が支持しない一般化が残る箇所を挙げよ。特に §4 の「不成立」の結論文と §3.6 の「S1 の外側に加算」を wall-decomp README §2 の区間定義 (S1 = 起点 = startup-gate.log mtime → brief) に当てて検証せよ。
3. **段 3 所見の反映。** s3-consult-A.md の所見 1〜13 と s4-ruling.md の採否表を README の該当節に当て、反映漏れ (採用したのに本文に無い)、反映誤り (裁定と違う書き方)、裁定で不採用にしたのに本文へ入っているもの、を列挙せよ。所見 6 (`--reference` は local clone の hardlink 複製を省かない) の README §5 の書き方が git 2.34 の `clone.c` (`clone_local()` / `copy_or_link_directory()` / `--shared`) の挙動として正しいかも判定せよ。
4. **scope と成果物の形。** README は依頼 (origin.md) の「実測」「条件付き実装」「本題だけ」を超えていないか。§7 の予備診断 (checkout.workers ABA) の置き方 (「実装しない、各 1 回、採用効果にしない、採否は別 wave」) は依頼の「gate・台帳・一般化の追加は scope 外」と両立するか、それとも裁定パッケージから外すべきか。§5 末尾「runbook への 1 行は書かない」は依頼の条件文 (実装した場合に書く) の読みとして正しいか。
5. **出所の束縛。** README 冒頭の「採取 script は repo へ入れず scripts.sha256 で束縛」は verbatim/ の実体 (scripts.sha256 の 5 行、script 本体の不在) と一致するか。verbatim/ に置いた file で README が参照していないもの、README が参照しているのに無いものを列挙せよ。
6. **言わないこと (§10) の整合。** §10 の 5 項は本文の主張と矛盾しないか (本文で断定しているのに §10 で「言わない」としている、または逆)。

## 出力形式
- `## 所見` (番号、real/refuted/判定不能、must-fix/should/nit、file:line、放置時の影響 1 行)、`## README に入れるべき訂正` (置換前→置換後の形で)、`## 総括` (必須、GO / NO-GO と must-fix 件数)。
