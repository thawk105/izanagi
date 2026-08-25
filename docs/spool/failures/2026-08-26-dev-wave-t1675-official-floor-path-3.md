---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1675-official-floor-path
seq: 3
---

## 新規

### {{F:brief-missed-guard-in-read-docstring}}. 読んだ docstring に書かれていた防壁を、brief の閉塞列挙へ入れ損ねた [手順漏れ]

- 事象: 段 1 brief が床値 official の閉塞を 2 つ (入場鍵の衝突、seam 分類) と列挙したが、
  実際は 4 つあった。落としたのは
  (a) `orchestrator/campaign/s8b_floor_campaign.py` の `_assert_official_permitted` による
  core の無条件拒否と、(b) `output/s8b-freeze-budget-approvals/g1.json` の不在である。
  段 3 の敵対相談 2 本が独立に両方を指摘し、親が一次資料で確認して real と裁定した。
- 根本原因: 親は同 module の docstring
  「official mode の無条件拒否は private core 自体で行い、public wrapper の迂回を許さない」を
  **実際に読んでいた**が、seam と適格性の調査に注意が向いており、閉塞の列挙へ転記しなかった。
  読了と列挙が別の作業であることを踏まえた検査を持っていなかった。
  (b) は「下流が要求する成果物の実在」を確かめる手順が brief に無かったため。
- 恒久対応: memory `enumerate-blockers-by-walking-the-consumer-chain` — 「経路を開く」型の
  brief では、開こうとしている経路の入口から成果物が消費される所まで consumer を 1 段ずつ辿り、
  各段の拒否条件と要求成果物の実在を列挙してから scope を書く。
  拒否文言を grep するだけでは、成果物の不在 (b 型) を見つけられない。
- 再発検知: 「経路を開く」「gate を外す」型の wave の段 3 レンズに、
  「この経路が実際に通るために越える門を全部挙げよ。1 つでも別の理由で止まるなら名指しせよ」を
  必ず含める。本 wave ではこのレンズが実際に 2 件とも検出した。

### {{F:orphan-hold-message-names-only-summary-path}}. orphan hold の解除文言が、実際に閉塞している耐久記録を名指ししない [手順漏れ]

- 事象: 親が全史 provenance 監査を 2 分のタイムアウトで打ち切り、計算ノード job の終端を
  観測し損ねて orphan hold が武装した (rc=16)。文言の指示どおり
  `output/pegasus-dispatch/orphan-hold.json` を削除して再走したが、同じ rc=16 が返った。
  実際に gate を成立させていたのは request 別の耐久記録
  `output/pegasus-dispatch/orphan-holds/948009.nqsv.json` だった。
- 根本原因: `tools/pegasus/dispatch_compute.py` の `_orphan_hold_present` は
  要約 marker `orphan-hold.json` の実在**または** `orphan-holds/` 配下のエントリ 1 件以上で
  真を返すが、同 file が出す解除文言は要約 marker の path しか名指ししない。
  指示に従って削除しても hold が残り、しかも文言は不在の path を指し続けるため、
  次の手掛かりが無い。
- 恒久対応: 解除文言に、成立要因となった実 path (要約 marker と request 別記録の両方) を
  列挙させる。実装は {{T:orphan-hold-message-lists-actual-paths}} が持つ。
- 再発検知: hold を張った状態で解除文言を出させ、`orphan-holds/` だけが存在する場合に
  その path が文言へ現れることを固定する検査を置く。

## 再発

### F333

- **再発: 2026-08-26** — [T-1675] wave の段 7 で、親が `tools/check_ai_provenance.py` を
  2 分の command timeout で打ち切り、同型の orphan hold
  (`job-may-remain-without-terminal-evidence`) が武装した。2026-08-24 の再発と引き金・対象
  command とも同一で、既存記述に修正すべき点は無い。監査自体は計算ノードで成功しており
  (`child_rc=0`、5858 件・新規違反なし)、実害は復旧作業だけだった。
  **新しい情報は解除側にある** — 要約 marker を消しても request 別の耐久記録が残る限り
  hold は解けず、解除文言はその path を名指ししない
  ({{F:orphan-hold-message-names-only-summary-path}})。

### F57

- **再発: 2026-08-26** — [T-1675] wave (docs のみ、実装差分 3 fragment) の受入全走 1 走目で
  `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` が 1 件だけ落ちた
  (16558 passed / 60 skipped)。**assertion は wall-clock 系ではなく pid 登録期限**
  (`child.pid was not registered before deadline`、stderr は空、test 所要 5.845 秒) で、
  子が 2 秒以内に pid file を書けなかった。同 node を計算ノードで単独走すると
  1 passed / 7.24 秒 / rc=0。負荷は load average 4.13 (5 分平均 6.31)、
  `run_tests.py` 16 本・codex 34 本が同時稼働。非帰属。
