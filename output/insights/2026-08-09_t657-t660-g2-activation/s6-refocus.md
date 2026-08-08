## 任務 1: 所見対応表

| ID | 判定 | 根拠 file:line | 評価 |
|---|---|---|---|
| C-1 | closed | [s4-adjudication.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:94)、[同:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:105) | M5 は理由文字列の diagnostic sensitivity pin に再設計され、kill 集計から明示的に除外された。所見の根因である「診断差を受理集合の kill と数える」誤りは裁定上閉じた。 |
| D-1 | partial | [reissue_floor_protocol.sh:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:30)、[同:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:34)、[同:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:225) | 非破壊 backup と EXIT 復元は実装されたが、復元中の再 signal と `git restore` 失敗時に target を失ったまま終了できる。R-1/R-2。 |
| D-2 | partial | [reissue_floor_protocol.sh:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:2)、[同:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:107)、[同:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:282) | fail-fast と検査は連結されたが、重要条件を Python `assert` に依存し、`PYTHONOPTIMIZE` で全消去できる。R-3。 |
| D-3 | closed | [reissue_floor_protocol.sh:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:326)、[同:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:344)、[同:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:347)、[同:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:355) | message file → `--message-file` preflight → `commit -F` → full-history audit の順序が実装されている。 |
| D-4 | closed | [ident.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/ident.py:52)、[同:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/ident.py:172)、[pipeline.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/pipeline.py:1027)、[同:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/pipeline.py:1085)、[wal.py:947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/wal.py:947) | identity は `search_config.environment_contract_sha256` を必須化し、両 COMMIT 経路が `contract_sha256` を記録する。replay も lock、COMMIT hash、env tag の一致を検証する。g1 WAL を g2 identity で再利用する経路は閉じている。 |
| D-5 | closed | [s4-adjudication.md:135](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:135)、[同:139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:139)、[operations.md:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/docs/dev-wave/operations.md:121) | post-C に受入・変異・land を限定し、land 対象を mutation ledger を含む記録 commit tip とした。共通 land 契約が tested main/tip と監査 commit を再照合する。実施済みではないが、手順の曖昧さは閉じた。 |
| D-6 | 裁定により scope 外 | [s4-adjudication.md:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:111)、[contract.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/qualification/contract.py:38) | `env_contract.py` は code identity に含まれるため series 値自体は回転する。旧 series 不継続を直接固定する受入 node は backlog へ明示送付されており、scope 外裁定は妥当。 |

## 新規所見

### R-1 — must-fix — cleanup 中の再 signal で復元を中断できる

根拠: [reissue_floor_protocol.sh:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:30) で EXIT/HUP/INT/TERM をすべて既定動作へ戻した後、[同:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:34) から復元を始める。この間の2発目の HUP/INT/TERM は shell を即終了させうる。

成果物影響: `floor_protocol.json` が欠落した作業木となり、floor artifact の参照と certified admission 入力が失われる。

修正案: cleanup 冒頭では `trap - EXIT` だけで再帰を止め、HUP/INT/TERM は `trap '' HUP INT TERM` として復元完了まで無視する。安全状態確認後に終了する。

### R-2 — must-fix — `git restore` 失敗を検出するだけで backup を復元に使わない

根拠: [reissue_floor_protocol.sh:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:34)–[38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:38) の復元が失敗すると、[同:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:42)–[44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:44) は rc=97 にするだけで終了する。[同:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:225) の検証済み backup は参照されない。

成果物影響: index lock、I/O error、`git restore` 中断時に tracked floor が欠落、または index が新 bytes のまま残り、成果物参照が不整合になる。

修正案: HEAD restore が失敗した場合、検証済み backup から target を原子的に再作成する fallback を設ける。最後に HEAD/index/worktree の3者一致を再検査し、一致するまで cleanup を成功扱いしない。

### R-3 — must-fix — `PYTHONOPTIMIZE` で前提・golden・trailer 検査が消える

根拠: activation 検査の [reissue_floor_protocol.sh:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:107)、旧 golden の [同:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:166)、T-080 payload の [同:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:212)、新 golden の [同:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:282)、trailer の [同:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:337) がすべて `assert`。`-O` は指定していないが、実測で `PYTHONOPTIMIZE=1 python3` は assert を実行しなかった。

成果物影響: activation/T-080/golden の不一致を通過させ、不正な floor bytes を stage・commitして certified admission の受理集合を変えうる。

修正案: すべての `assert` を明示的な条件分岐と `raise SystemExit(...)` に置換する。補助防壁として `sys.flags.optimize == 0` も検査する。

### R-4 — must-fix — g2 活性化後も floor test helper が「末尾=g1」を仮定している

根拠: production registry は [env_contract.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:245)–[303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:303) で Pegasus `(g1, g2)`。ところが [test_s8b_floor_campaign.py:4395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_floor_campaign.py:4395) は「単一世代」と記述し、[同:4401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_floor_campaign.py:4401) で末尾 g2 を `g1_entry` とし、[同:4413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_floor_campaign.py:4413) でさらに generation=2 を追加する。これは [env_contract.py:317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:317)–[325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:325) の 1..N 連番検査で必ず拒否される。helper は4 nodeから使用されている。

成果物影響: post-C 受入台帳に想定外の赤が少なくとも4 node残り、歴史 g1／現行 g2 lane の受入参照を成立させられない。

修正案: 合成 successor helper を廃止し、`GENERATIONS["pegasus"][0]` を歴史 g1、`lookup("pegasus")` を現行 g2として実 authority を直接使う。合成 g3 が必要なら現行 g2を predecessor、generation=3 を successor にする。

## script 敵対検証の補足

- `rm`、freeze途中、golden失敗、commit失敗、通常の `set -e` 中断は EXIT cleanup に入る。ただし R-1/R-2 のため復元保証にはならない。
- 最初の HUP/INT/TERM は `exit 129/130/143` から EXIT cleanup に到達する。`local rc="$?"` は意図した終了コードを捕捉し、実測でも INT は `cleanup-rc=130` だった。
- EXIT trap を外すため無限再帰はない。問題は同時に signal trapまで既定化していること。
- freeze CLI 形は正しい。[s8b_floor_campaign.py:3519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:3519) の専用 parser を [同:3543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:3543) が dispatchし、[同:3589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:3589) の `__main__` に到達する。stdin redirect はなく、子の [同:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:622) の tty 検査まで届く。
- 未commitの新 bytes は clean-tree 検査と HEAD blob一致検査を通れないため、冪等分岐が「実施済み」と誤認する穴はない。
- script は mode `100755`。`check_docs.py` は insights の `*.md` だけを列挙し、frozen manifest は明示23 pathだけを固定する。provenance は `.sh` を実装面として扱い、script commitには Codex author trailerがある。`bash -n` と `check_docs.py` は rc=0。配置による既存検査違反は確認しなかった。
- pytest、freeze、receipt verify、commit は実行しておらず、受入緑は主張しない。

## 取り残し分類

歴史値として正しいのは `00000001.json`、Pegasus g1 registry entry/golden、未再発行の committed floor、committed silo evidenceである。現行 head は [env_contract.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract.py:373) の serial 2、現行 Pegasus は activation record 2 の g2である。更新漏れは R-4 の test helperだけを確認した。

## 総括

**NO-GO**

- D-1/D-2 は partial。D-3/D-4/D-5 と C-1 は closed。
- must-fix は R-1〜R-4。
- 特に cleanup 中の signal／restore失敗で tracked floorを失う経路が残る。
- Python `assert` は環境変数だけで全停止条件を無効化できる。
- stale g1 helperにより post-C 受入も現状では緑にならない。
- 修正後に焦点再レビューと、親による post-C 受入再走が必要。