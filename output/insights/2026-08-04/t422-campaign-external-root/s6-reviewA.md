## 所見

### 1. resolve 前の lstat walk を `missing/..` で打ち切れる

- 種別: 受理集合拡大（A-1/A-2 不一致）
- 深刻度: 高・must-fix
- 根拠: [layout.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:233)、[layout.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:294)
- 壊れ方: env=`/tmp/missing/../safe` で `missing` が不存在なら、lstat walk はそこで `break` する。その後は `/tmp/safe` へ resolve されるが、`/tmp/safe/exploration/campaigns` は再検査されない。ここを repository 内への symlink にしても受理される。
- 成果物影響: 外部 root 表記のまま campaign.lock/WAL が repository 内へ書かれ、F98 の dirt と台帳参照先の分裂が再発する。
- 修正方向: raw path の検査に加え、resolve 後の `<root>/exploration/campaigns` を再度 lstat walkする。`..` component 拒否と resolved base の directory 型検査も追加する。

### 2. 8c の実 suffix `autonomous-trials` は env admission の対象外

- 種別: gate 迂回（A-1/A-2/B-1 不一致）
- 深刻度: 高・must-fix
- 根拠: [layout.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:294)、[p3_autonomous_workload_trial.py:1758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1758)、[p3_autonomous_workload_trial.py:1587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1587)
- 壊れ方: resolver が検査するのは `exploration/campaigns` だけ。`<base>/exploration/autonomous-trials` を main checkout 内への symlink にすると、base の `.git` 検査は通り、worktree-container gate も main checkout なので通り、`mkdir()` が repository 内へ書く。
- 成果物影響: attempts.jsonl、raw、proposals、report.json が repository 内へ生成される一方、成果物内参照は外部 root の lexical path になる。
- 修正方向: env 経路では `autonomous-trials` も固定 suffix として lstat 検査するか、実 `run_root` の resolved ancestor `.git` と symlink を materialize 直前に検査する。

### 3. process pin が二重 module identity で分裂する

- 種別: ドリフト（A-4 不一致）
- 深刻度: 高・must-fix
- 根拠: [layout.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:223)、[p3_autonomous_workload_trial.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:54)、[p3_autonomous_workload_trial.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:94)、[conftest.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/conftest.py:128)
- 壊れ方: `campaign.layout` と `orchestrator.campaign.layout` は別 module objectで、それぞれ独立した `_exploration_output_root_pin` を持つ。片方が root X を pin 後、env を Y に変えて他方を呼ぶと Y が初回値として受理される。conftest は両方を reset するだけで共有していない。
- 成果物影響: direct/orchestrator 入口と `campaign.*` driver の間で layout、WAL、provenance、report の root が分裂する。
- 修正方向: pin と lock を alias 非依存の process singletonへ移すか、二つの import identityを同一 moduleへ正規化する。両 identity を同時に使う負例を追加する。

### 4. pin の compare-and-set が thread-safe でない

- 種別: 競合・ドリフト（A-4 不一致）
- 深刻度: 高・must-fix
- 根拠: [layout.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:281)、[layout.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:311)、[test_campaign.py:3735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3735)
- 壊れ方: 二 thread が異なる env 値を取り込み、双方が line 311 で `None` を読んでから line 314 を実行できる。両方が異なる root を返し、最後の代入だけが pin として残る。新テストは逐次 drift しか撃っていない。
- 成果物影響: 同一 process の並行 campaign が別 root に台帳を生成し、最終 pin と既生成成果物の参照が一致しなくなる。
- 修正方向: module identityを跨いで共有する lock 内で env 再読・比較・pin を原子的に行い、barrier付き競合テストを追加する。

### 5. `ensure()` は全 materializer を支配していない

- 種別: gate 迂回
- 深刻度: 高・must-fix
- 根拠: [layout.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:425)、[layout.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:434)、[wal.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:301)、[wal.py:780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:780)
- 壊れ方: `exploration_campaign_layout(id)` の直後に `wal.write_lock(layout, ...)` または `wal.log(...)` を呼ぶと、WAL 側が `os.makedirs()` し、worktree gate を一度も通らない。`run_campaign()` は ensure を通るが、WAL 公開 API 自体には支配関係がない。
- 成果物影響: env 未設定の wave で campaign.lock/WAL を直接 repository 内へ生成でき、land が再び RC_DIRT になる。
- 修正方向: WALを含む全 materializerに layout admission を要求するか、未 ensure の ExplorationCampaignLayout を書込み API が拒否する契約を設ける。直接 WAL 負例を追加する。

### 6. 8c の env 未設定既定値は symlink 経由で bytes が変わる

- 種別: 後方互換（B-1 不一致）
- 深刻度: 中・must-fix
- 根拠: [layout.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:42)、[p3_autonomous_workload_trial.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:134)、[p3_autonomous_workload_trial.py:1761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1761)
- 壊れ方: 旧既定は `Path(__file__).resolve()` 由来の `ROOT/output`。新既定は `abspath(__file__)` 由来の `repo_output_root()`。例えば `/proc/self/cwd` や checkout symlink 経由の import では、旧値が real path、新値が symlink lexical pathになり、文字列が一致しない。
- 成果物影響: report.json の `attempt_journal`、journal の report pathなどの bytes が env 未設定でも変わる。
- 修正方向: resolverへ「caller固有の legacy default」を渡せるようにし、8c の未設定時だけ従来の `ROOT / "output"` を保持する。

### 7. `os.geteuid` の所有検査テストは process-global mutation

- 種別: テスト隔離
- 深刻度: nit
- 根拠: [test_campaign.py:3711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3711)
- 壊れ方: `layout_module.os` は共有 `os` moduleなので、line 3713 は全 module/thread の `os.geteuid` を変更する。通常例外では `finally` により復元されるが、in-process 並列実行中の漏れは防げない。
- 成果物影響: なし。並列テストの判定だけが非決定的になり得るため nit。
- 修正方向: layout-local `_effective_uid()` seam を設け、その bindingだけを差し替える。

## 裁定項目の照合

| 項目 | 判定 |
|---|---|
| A-1/A-2 | 通常の symlink・`.git`・owner 負例は実装済み。ただし所見1・2で実 path の受理集合が破れる。 |
| A-4 | 逐次単一 identityでは一致するが、所見3・4で process pinではない。 |
| A-5 | [test_dev_wave_land.py:2758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2758) で `_cwd(wave)` 内から両検査を呼んでおり破れなかった。 |
| B-1 | env時の path形と明示引数優先は一致。ただし所見2・6が残る。 |
| B-3 | [test_dev_wave_land.py:2742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2742) は実 `run_campaign()` を通し、marker・lock・WAL・cleanを確認。fake evaluatorは検査対象のlayout/run_campaignを置換していない。 |
| gate署名 | `ensure()` と8cの局所的な ValueError位置は一致。ただし所見5によりmaterialization全体のgateにはなっていない。 |

例外 typeだけを見る負例も攻撃したが、登録済み入力では受理された場合に `AssertionError` へ落ち、正例も別テストにあるため恒真ではなかった。worktree predicateも相対 path・trailing slash・`.`/`..` は `resolve()` 後に判定し、symlink inwardは拒否、outwardは実 materialize先がcontainer外なので署名どおりだった。8cの ValueError先行も裁定そのもので、CLIは両例外を捕捉していないため別のhandler退行はない。exploration factoryのenv未設定bytesは [layout.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:287) で無加工返却され、[test_campaign.py:3620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3620) も非正規形を固定しているため破れなかった。

## 総括

- real候補数: 7（must-fix 6、nit 1）
- must-fix数: 6
- 最深刻: 所見1。resolve前walkの早期終了により、A-1/A-2を通過したenv rootからrepository内へWALを書ける。
- pytest: 指示どおり未実走。