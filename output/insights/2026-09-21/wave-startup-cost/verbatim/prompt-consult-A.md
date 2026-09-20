単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/brief.md
- 自 wave の起動時刻列と所要: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/self-startup-timeline.txt、同 dir の submodule-init.log、gate-time.txt
- 現存 worktree 21 本の git 管理 file の mtime 一覧: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/wt_timeline.out (採取 script: 同 dir の wt_timeline.sh)
- 直近 16 wave の startup-gate.log mtime と HANDOFF.md の起動行: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/scan_startup.out (採取 script: 同 dir の scan_startup.sh)
- 主 checkout の submodule store と現存 worktree の module 配置・pack の hardlink 共有: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/inspect_modules.out、同 dir の inspect_links.out
- 昨日の単独起動の一次資料 (t2797 の submit-tree 作成 log / script、mutation-source 作成 script、file mtime): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/t2797-setup-submit-tree.log.filtered、同 dir の t2797-setup-submit-tree.sh、t2797-make-mutation-source.sh、t2797-tree-build-mtimes.txt
- tracked file 数の内訳: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/ls-files-count.txt
- submodule 初期化 tool の実装 (抜粋): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/git_state.py.excerpt (全文は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/tools/dev_waves/git_state.py と同 dir の ../dev_wave_submodule_init.py)
- 既存 insight の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/wall-decomp-README-s1-3.md (dev-wave 所要分解、§1〜§3)、同 dir の t2817-README-s1.md (受入 `pre` 61 秒の分解)
- 既裁定・failures・手順の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim/ の D95.md、D1009.md、F26.md (worktree add の所要の再発記録を含む)、DW-C01.md、DW-O20.md、DW-S04.md、DW-G05.md

## 前置き — この依頼の性質

これは自分たちの開発運用 (dev-wave) の「wave 起動の固定費」の実測と、その結果に基づく条件付き実装の可否判断に対する設計レビューである。ユーザーの依頼は「固定費 (EnterWorktree → submodule 再帰初期化 → 開始 gate → 受入 fresh 木の +60 秒) を直近 wave の資料から実測し、**submodule 初期化が固定費の大半なら** `git submodule update --reference <主 checkout の module store>` 等の既存 git 機構で初期化を短縮する局所修正 1 件を、効果を同じ資料で見積もってから Codex author で実装する。gate・台帳・一般化の追加は scope 外」である。親は実測の結果「submodule 初期化は固定費の約 1 割で大半ではない → 条件不成立 → 実装しない」と provisional に裁定している (brief の P1〜P5)。**親 brief と親自身の実測値・その一般化を検査対象とし、守らずに点検すること。** セキュリティでも攻撃でもなく、外部入力も扱わない。書込可能 tmp が無いので pytest 緑は要求しない — 静的検査でよい。テスト実測は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

# 依頼 — レンズ A (実測の妥当性・整合) と レンズ B (実効性・過剰・削除) を 1 本で

次を file:line と数値で点検し、所見ごとに **real / refuted / 判定不能** と、real なら **must-fix / should / nit** と「放置時に何がどう変わるか」を 1 行で書け。

1. **時刻の読み方 (P3・実測 1〜3)。** `wt_timeline.out` の `commondir` mtime を「worktree add の開始」、superproject `index` mtime を「checkout の終了」、`modules/external/ccbench/config` を「submodule 初期化の開始」、最深 `googletest/index` を「再帰初期化の終了」と読む親の解釈は git 2.34 の `worktree add` / `submodule update --init --recursive` の書込み順序として正しいか。特に (i) `git clone` が config を複数回書く (最後は checkout 後?) ため ccbench の `config` mtime が初期化の開始でなく終了に近い可能性、(ii) 後続操作 (`git status`、PIN checkout、ff-only) が `index` を書き換えて checkout 終了時刻を上書きする可能性 (submit-tree 群・t2786 系で `index` が `modules` より遅い例)、(iii) 自 wave の `before-submodule-init` 07:39:31 と ccbench `index` 07:39:32 の差が 1 秒しかないこと、を使って親の各区間の値 (checkout 中央値 70 s、submodule 中央値 8 s) が過大・過小のどちらに偏るかを判定せよ。
2. **標本の代表性 (P1・P4)。** 今朝の 10 本は 07:32〜07:39 に同時起動した混雑下の標本であり、昨日の単独標本 (t2797 submit-tree ≈ 45 s、mutation-source 68 s) と F26 の再発記録 (混雑下 7 分) を合わせて「submodule 初期化が固定費の大半ではない」は、混雑の有無を問わず成り立つか。submodule 初期化が相対的に大きくなる条件 (例: superproject が既に温かい、混雑が submodule 側にだけ掛かる、nested clone が hardlink でなく copy になる別 filesystem) を挙げ、それが本 repo の運用 (同一 Lustre、hardlink nlink 155) で起こりうるか判定せよ。
3. **`--reference` / alternates の効果見積り (P2)。** 主 store の pack が既に hardlink 共有されている (inspect_links.out) とき、`git submodule update --reference` (alternates) が省けるのは何か (hardlink 作成 ≈ 36 file、`objects/info/alternates` 1 行で済む)、省けないのは何か (3 段の clone process 起動、≈ 2,500 file の checkout、`.gitmodules` 解決)。親の「効果 ≤ 1〜2 s」を git_state.py.excerpt の argv (`submodule update --init --recursive --no-fetch`、URL は主 checkout の `.git/modules/...` 絶対 path) から検証せよ。逆に、alternates を導入した場合の壊れ方 (主 store の gc / prune / 主 checkout の deinit / 撤去で参照先が消える、`dev_wave_cleanup.py` の nlink 検査 F1026 との相互作用) を 1 行ずつ挙げよ — 実装しない裁定でも insight に「導入しない理由」として残すため。
4. **固定費の本体の同定 (P4)。** 「superproject 31.7K file (872 MB、output/insights 77%) の checkout が本体」は資料から言えるか。file 数 (Lustre の metadata 操作) と bytes (872 MB の書込み) のどちらが律速かは本資料では分離できない — 親はそう書くべきか。impl wave が木を 3〜6 本作る (wave 木、Codex unit 木 1〜3、mutation-source、submit-tree) という数は wall-decomp / t2797 の資料から支持されるか、1 wave あたり 3〜9 分という換算は妥当か。
5. **「受入 fresh 木の +60 秒」の読み (P5)。** 受入が git の木を作らない (chain log・launcher・`dev_wave_wait.py` に clone / worktree add 無し) ことを親は静的に確認した。ユーザーの「+60 秒」を T-2817 の受入 `pre` 61.9 s と読むのは妥当か。別の読み (例: 受入前の post-claim merge、submodule readiness preflight、計算ノードでの `git status` / fingerprint 採取) があれば、それが 60 秒級か資料から判定せよ。
6. **裁定パッケージ候補 (レンズ B)。** 実装しない裁定の下で、親が insight に残す「次の局所修正候補」として (a) git の `checkout.workers` (git ≥ 2.32 の並列 checkout、repo local config 1 行、既存 git 機構) を主 checkout に設定して worktree add を短縮する、(b) `output/insights` (24.4K file) の checkout を省く sparse-checkout、(c) 木の本数を減らす運用 (Codex unit 木の再利用)、のどれが「既存機構の局所修正」で、どれが受理条件・gate・pin 検査 (`tools/pegasus/README.md` 327 行付近の sparse / alternates 拒否、`fetch_third_party.py` の verifier) に触れて scope 外か、根拠の file:line 付きで分類せよ。(a) の効果を本 wave の親が job dir の独立 clone で 1 回 probe (ABA: workers 既定 → 8 → 既定、各 1 回、混雑下) することは「効果を同じ資料で見積もる」の範囲か、それとも本題外の追加実験か — 判定と理由を書け。
7. **過剰・削除。** brief の scope・不変条件・DW-G05 の 1 行は依頼を超えていないか、逆に依頼の「効果を同じ資料で見積もってから」を条件不成立時にも満たす (見積りを書く) べきか。docs-only (insight + worklog fragment) で終える場合、DW-S04 の「実装面差分ゼロ → 変異免除・受入全走は免除しない」の適用に誤りはないか。

## 出力形式
- `## 所見` (番号、real/refuted/判定不能、must-fix/should/nit、file:line、放置時の影響 1 行)、`## 親 brief への指摘`、`## 段 4 裁定に入れるべき変更`、`## 裁定パッケージへ返すべき択一` (あれば)、`## 総括` (必須)。
