# 段 1 調査報告 (sonnet 調査子、2026-09-29、read-only)。親が要点を tool 現物で照合済み (dev_wave_cleanup.py:1577-1591、CLEANUP-READY の repo 内 0 件)

対象: 2026-09-29 に land した wave 約 35 本の Claude Code transcript 50 本 (`/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi*/*.jsonl`)。9/27〜28 は未精査。

## 結論
wave 本体の木は land 後の撤去でおおむね消えている。溜まるのは主に Codex 子木とその branch。

## wave ごと (抜粋。rc は wave 木撤去の結果)
- rc=0・残置なし: land-knowhow-ops-docs, gen-opt-literature-cards, gen-opt-evolution-design, gen-opt-correctness-gate, gen-opt-stage-a-candidate, phase3-readme-sync, vhash-story-v2, vhash-novelty-repositioning, vhash-forwarding-proof, paper-story-20260929, t2852-p5, vhash-cicada-rts-check, roadmap-revision (1 回目 rc=21 自分の sleep の cwd)
- vhash-forwarding: wave rc=0。manifest 子木 14 本が remove-child rc=20 (途中版 mismatched)、manifest 外の補助木 14 本 (integ, run-a/b, smoke, verify)。rm -rf script は auto mode 分類器が拒否。計 28 本残置。git worktree add 31 回 (fix 巡ごとに新木)
- vhash-hot-block-microbench: 子 23 本を manifest 登録、manifest を /work/SFC (symlink) path で渡して rc=2 一斉拒否、6 本撤去後 調整役の窓切れで PAUSED、子 17 本と wave 本体残置。git worktree add 25 回 (vhb-fix1..fix10)
- t2854-ccbench-format-ci: CLEANUP-READY 送信後 調整役の OK 待ちで約 3 時間放置
- vhash-cicada-baseline-tuning: wave rc=20 (branch reflog、amend)、子 rc=20 (mismatched)
- vhash-eval-prereg, vhash-forwarding-model: wave rc=20 (reflog)
- vhash-cicada-verifier-ext, gen-opt-gate-liveness, md2-push-pack-hint, vhash-readonly-share: rc=30 partial (main changed since integration proof / admin-recheck)、dir は消え登録だけ残る
- vhash-gc-connection-prototype: 9 本中 8 本撤去、author-a が rc=20 (not integrated)
- t2853-r2-fig8b: 子 fix1/fix2 rc=20 mismatched; t2853-r2-fig6, t2853-r2-fig11, t2872-mocc-g2-split, output-pruning, t2273: probe/plot 子が rc=20 (empty owned_paths)
- cleanup-remove-lock: 子 rc=20 (統合証明崩れ)
- vhash-cicada-version-measure: 子 16 本同時起動で Lustre 詰まり、codex 子 6 本 rc=20 残置
- vhash-related-work, paper-story-vhash-setup: land 後 `result:` を書いて終了、cleanup 呼出し 0 回

## 原因分類 (wave 単位、重複あり)
| 原因 | 件数 |
|---|---|
| 子木 rc=20 (fix 途中版 mismatched・owned_paths 空) | 約 10 |
| 調整役の窓・合図待ちで停止 | 2 |
| rc=30 partial (main が進んだ) | 4 |
| wave 本体 rc=20 (reflog、amend) | 3 |
| cleanup を呼ばず result: で終了 | 2 |
| 子木が manifest 外 | 1 (14 本) |
| auto mode 分類器の rm -rf 拒否 | 1 |
| 隔離ガードで cleanup 本体が撃てない | 0 (周辺確認のみ拒否。ExitWorktree keep で main に戻る運用あり) |
| rc=75・rc=21 一過性 | 約 8 件 (再試行で通過) |

## その他
- `dev_wave_codex.py` は子木を作らない。子木は親が `git worktree add -b` で作り、manifest 登録も親の責任。
- `tools/dev_wave_land.py` に cleanup 言及なし。
- `dev_wave_cleanup.py --help` が rc=2 (phase=argv) を返し、約 24 回無駄打ち。
