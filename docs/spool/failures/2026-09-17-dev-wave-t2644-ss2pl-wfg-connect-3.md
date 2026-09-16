---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2644-ss2pl-wfg-connect
seq: 3
---

## 新規

### {{F:gate-integrated-driver-never-run-live}}. condition gate を計測 driver の build 経路へ統合した後、その driver を一度も実走せず、gate の前提が patch の設計と合わないまま 3 週間残った [手順漏れ] [ドリフト]

- 事象: 2026-08-27 に `tools/pegasus/run_ss2pl_lock_study.py` の `build_target` へ condition gate
  (`_require_condition_gates`) が入った後、SS2PL runner は一度も計算ノードで build を実走していなかった。
  2026-09-17 に初めて走らせると、inert な arm は stock 木対照で `ycsb_ss2pl.exe` の owner TU が解決できず
  (`owner-tu-unresolved`、companion define の未使用警告で `configure-failed`)、非 inert な arm は軸ごとに header /
  marker define を切り替える patch の設計と「define 1 個だけの差」を要求する gate が合わず
  (`dependency-closure-drift` / `compile-command-drift`)、全 arm が拒否された。pristine な thirdparty staging では
  masstree の `config.h` 不在で gate の前処理も落ちる (永続 cache に残った生成物で T-2213 の実測は通っていた)。
  一次資料 `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md` §5。
- 根本原因: gate の統合 wave は unit test (合成 fixture) で緑を取り、統合先 driver の実走 (生死確認) を省いた。
  driver 側の test も `build_target` を stub する。runner の build 経路が「動く」と誰も確かめないまま docs と
  台帳は接続済みとして扱われた。
- 恒久対応: `DW-G01` (生死実験先行) を、新機構の実装前だけでなく**既存 driver への gate 統合時**にも適用する —
  統合先 driver の production 経路で 1 走を通すまで完成と扱わない。memory
  `gate-tools-need-parent-live-dogfood` (gate tool は親が実データで 1 回通すまで完成でない) と同じ規律。
  修正そのものは {{T:ss2pl-runner-build-gate-incompat}}。
- 再発検知: driver の build 経路を stub する test しか無い gate 統合 commit。段 1 で「その driver は統合後に
  実走したか」を worklog / insight で照合する。

### {{F:constructed-key-escapes-consumer-grep}}. 文字列連結で組まれる policy key の読み手が literal 検索の消費者列挙から漏れ、「読み手 0」の主張のまま launcher が壊れた [consumer 取り残し] [手順漏れ]

- 事象: T-548 (2026-09-17 entry 1578) は `gflags_source_path` / `glog_source_path` を policy から消し「読み手は 0」と
  記録したが、`tools/pegasus/ss2pl_lock_study.sh:207` は `policy[name + "_source_path"]` と key を連結で組んで
  読んでおり、`dependency_policy` 段で KeyError 相当で落ちる。同日の [T-2644] wave が launcher を読んで見つけた。
- 根本原因: 消費者列挙を `gflags_source_path` の literal 検索で行い、接尾辞 `_source_path` や `"_source_path"` の
  断片では検索しなかった。連結で組まれる key は literal 検索に現れない。
- 恒久対応: memory `closure-and-search-discipline` に「key 名を文字列連結で組む読み手は literal 検索から漏れる。
  接尾辞・断片 (`_source_path`) でも検索し、shell の heredoc 内 python も対象に含める」を追記した。
  修正は {{T:ss2pl-launcher-source-path-key}}。
- 再発検知: 「読み手 0」と書く前に、識別子の断片検索が 0 件であることも併記する。

## 再発

### F656

- **再発: 2026-09-17** — [T-2644] wave で、親が probe の generic dispatch を背景投入した直後に同一 worktree から
  焦点走を投げ、後発が `reason=orphan-hold` で子を起動せずに戻った (rc=16)。焦点走は別 worktree (実装子 A の
  worktree、同じ差分) から投げ直して実害なし。`DW-O26` の「同一 worktree からの dispatch は全種を直列にする」を
  親が投入直前に確かめなかった遵守の失敗。
