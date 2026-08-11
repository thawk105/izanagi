---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t808-mutation-fanout
seq: 1
---

## {{D:mutation-fanout-contract}}. 変異本走の N-job fan-out は親 spec からの再導出で束縛し、shard 数は実測で頭打ちにする

**背景:** D289 決定 (3) が「第 3 の選択肢」として起票した N 本同時 fan-out を実装する。
D130 / D131 の未充足 4 条件は **harness を計算ノードへ束ねる**経路の条件であり、
harness がログインに残る `--runner-mode dispatch` には掛からない。

**決定 (1): 分割は「記録」でなく「再導出」で束縛する。**
spec schema は exact key (`_require_exact_keys`) なので shard spec に親への参照を書けず、
harness が束縛するのは shard spec の hash だけである。素朴に分割すると
**ID 集合が揃っていても中身が別 spec 由来**という経路が開く。よって併合器は親 spec と
assignment から shard spec を再導出し、bytes hash が ledger の `spec_sha256` と一致することを
要求する。**併合器は親 spec を入力に取る** — shard から親を再構成すると
「shard を 1 本渡し忘れる」攻撃が丸ごと通る。
`estimated_run_seconds` / `timeout_seconds` / `hang_timeout_seconds` は親の値をそのまま複製し、
変異集合も期待 node も 1 件も増減させない (D289 決定 5 / 絶対規律 4)。

**決定 (2): 併合の欄比較は「内容欄 exact 一致・path は manifest の期待値と照合」。**
`_runner_identity` / `_tool_identity` は絶対 path 欄を持ち、shard 間で実際に異なるのは
`entrypoint_path` / `dispatch_entrypoint_path` / tool の `path` の 3 欄である
(`executable_path` は素の名前が `shutil.which` で解決されるため shard 共通)。
よって `runner_sha256` / `tool_sha256` の一致要求は必ず落ちる。
**一方で「path は pairwise で異ならねばならない」も誤りである** — 同一 scratch root を
**逐次**再利用すれば 3 path は一致しうるが、それは内容上正しい成果物であり、
DIFFER 必須にすると正しい shard を誤拒否する。**gate は group manifest が期待する
exact path との比較とし、whole-object hash の異同は二次的 checksum に留める。**
未知欄は fail-closed (一致とも差異とも推定しない)。

**決定 (3): queue 待ちが `TIMEOUT` に化ける経路があるため、併合は TIMEOUT record を拒否する。**
`_run_tests` は dispatch subprocess **全体**に `timeout_seconds` を掛けるので、request が
`QUE` のまま超過すると**計算ノードで一度も走っていない変異が `TIMEOUT` = terminal として
記録され、`registered == recorded` が成立する。**
**これは fan-out が作った欠陥ではなく現行の逐次経路に既にある**もので、D130 決定 (3) 条件 4 の
`total_deadline` 欠陥と同族である。既存 semantics の修正は本 wave の scope 外とし、
**fan-out 側は併合器が TIMEOUT record を含む shard を拒否して fail-closed に閉じる。**
根治は {{T:mutation-timeout-semantics}} へ。

**決定 (4): 短縮には硬い上限があり、shard 数は「多いほど速い」ではない。**
過去 3 台帳から固定費 (collection + baseline) と変動費 (変異本体) を分離した。
**短縮の上限 = (固定費 + 変動費) / (固定費 + 最遅変異 1 本)** である。

| 台帳 | n | 固定費 | 変動費 | 上限 |
|---|---|---|---|---|
| 2026-08-04 t325 | 12 | 48.5 s | 378.4 s | 3.24x |
| 2026-08-09 t685 | 11 | 207.3 s | 2625.3 s | 6.03x |
| 2026-08-11 t787 | 14 | 48.6 s | 427.5 s | 4.71x |

t325 は N=8 でも N=4 と同じ 3.24x で頭打ちになり、増えた固定費だけ損をする。
**N > 変異数では空 shard が固定費を払って何もしない。**`duration_s` は
`_run_tests` の Popen〜communicate 全体なので**順番待ちを含む** (待ちも並列化される)。
spec は変異ごとの所要を持たない (`estimated_run_seconds` は全変異共通の 1 値) ため
**所要による均し込みは原理的にできない**が、t787 の N=4 では単純分割が LPT と実質同値
(2.87x 対 2.86x) であった。**既定 N を置かず明示入力必須とし、上限は変異数とする。**

**決定 (5): admission は per-process RSS を判定量にしない。**
runbook §7.0 の判定量は user slice の `memory.current` (cgroup 課金量) であり、
**規範値に N を掛ける外挿も禁じられている。**`--force-dispatch` は login admission を迂回し
(`tools/run_tests.py`)、`dispatch_compute.py` / `mutation_harness.py` / `mutation_worktree.py` は
`login_headroom` を一切参照しない (grep 0 hit)。**変異 dispatch 経路は丸ごと admission 台帳から
見えない。**よって driver が exact-N・同一 argv・同一入力規模の cgroup `memory.current` を
3 反復以上測った certified peak を要求し、measurement log の実在・symlink 拒否・hash 一致・
sample 時刻の単調増加を検査する。未測定・別 N・別 argv は `unknown` として**投入前に停止**する。
**N を黙って clip しない** — clip すると投入前に記録した期待集合が投入後に変わる。

**決定 (6): fan-out の merge index は偶発欠落への fail-closed であって、偽造への改竄検知ではない。**
敵対レビューは、同一 Unix user が偽 scope を立てて kernel peak を合わせる・既知 hash を
identity 欄へ複写する・同一 root 内で親 hash だけ差し替える等の**偽造**手順を構成できることを示した。
これらは real だが、**信頼境界が operator 自身の account である本 repo では
プロトタイプ基準 (防御的堅牢化は既定で見送り) に従い本 wave では閉じない。**
**docs と報告で「機械保証済み」と読める書き方をしない。**偽造耐性は {{T:fanout-tamper-evidence}} へ。

**却下した選択肢:**
- **merge 成果物へ shard ledger を verbatim 埋め込む** — hash index の方が
  「shard 台帳を書き換えない」を直接満たし、巨大な `artifact.stdout` の二重保存を避ける。
- **`runner_sha256` の一致を要求する** — 構造的に必ず落ちる (決定 2)。
- **履歴の所要で LPT 割付けする** — spec に所要が無く、N=4 では単純分割と実質同値 (決定 4)。
- **N の上限を固定値で規範化する** — 空きは他 wave の稼働で変動する。実測で動的に決める。
- **shell 背景化 + `.done` で N 本を回す** — rc の取りこぼし・`pgrep -f` の自己マッチ・
  孤児 process の 3 事故面を持ち込む。in-process の単一 driver ループにした。
