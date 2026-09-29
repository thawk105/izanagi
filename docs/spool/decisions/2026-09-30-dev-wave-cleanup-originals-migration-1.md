---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-cleanup-originals-migration
seq: 1
---

## {{D:cleanup-originals-no-recovery}}. 原本を抱えた古い投入木と branch 91 本・11 本は回収せずに撤去し、D2242 決定 1 の「branch は残す」を解く

**決定:**

1. 2026-09-30 の棚卸しで、研究記録が原本の所在・固定 checkout・発効版として path を名指すために残していた worktree 91 本 (dev-wave-jobs 等の投入木 80 本と個別の木 11 本) と
   local branch 11 本を、**回収せずに撤去する**。回収 (repo 外の恒久置き場 `izanagi-repro-archive` への新しい写し) は 0 件。
   判定基準はユーザー方針 (2026-09-30、依頼 md_1) のとおり、(a) 論文の数値・図がその原本からしか得られない、(b) phase3 の現行タスクか worklog 末尾の次の一手が入力に取る、
   (c) 有効な事前登録・凍結が入力に取る、のいずれかを一次資料で示せた系列だけを回収する。名指しされているだけ (経緯・所在の記述) は回収理由にしない。
   調査の結果、(a)〜(c) に当たる系列は 0、コード・テストが木の path を読む箇所も 0 だった。T-2850 追補 3 が入力に取るのは main の祖先の commit `299aa022e` で、木ではない。
2. 記録の付け替えは集約 insight `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とし、名指していた insight README の末尾に日付付きの追記節を足す。
   結果稿・版・claim-evidence・receipt・MANIFEST・verbatim・raw (append-only の凍結物) は書き換えず、`docs/paper-story/README.md` の所在注記から訂正先を指す。
3. B-5 の発効 commit `6fce61d6e` (唯一の ref が branch `worktree-dev-wave-t2797-b5-main-run`) は tag を作らず、branch の bundle で保全する。
4. D2242 決定 1 の「branch `worktree-t2273-shard0-local-copy` は残す」を解き、bundle に退避してから削除する。

**理由:**

- 論文の主張は「どの仕組みで何が得られたか」と粗い時期で足り、bytes 級 provenance の保全は既定で最小側に倒す (ユーザー明言 2026-08-12)。数値・図はすべて repo 内の派生物 (insight・結果稿) にあり、
  K2 3 組・B-5 試走・MOCC 疎通 21 本・T-2850 試走 v2 18 本・T-2865 段階 F の campaign 原本は既に `izanagi-repro-archive` に sha256 照合つきで写してある。
- T-2871 生死確認の WAL 2 本は `output/insights/2026-09-29/gen-opt-evolution-design/README.md` §6.1 の内訳の生データとして名指されるが、同設計は未採用・本走未承認で、内訳値は同 README に転記済みなので (b) に当たらない
  (攻撃役の指摘を採用)。前日の退避 tar に入っている。
- tag は管理する ref を増やすだけで、論文稿の「branch にある」という所在の記述はどちらにしても注記で直す必要がある。発効 commit の差分は json 1 file・25 行で bundle から復元できる。
- D2242 が branch を残した趣旨は決定 3 (中立な整理としての land を別判断に残す) にあり、その判断は D2243 項 2 が候補 (c) として不採用にした。branch を入力に取るタスクは無い。
- 残し続ける費用は実測で重い: 2026-09-29 に worktree 216 本で `git worktree list` 7.2 秒・rescue gate が時間切れ・全 worktree の status 15 分超。

**却下した選択肢:**

- 名指しがある木を全部残す (前日の Codex 判断) — 経緯の記述を回収理由にすることになり、ユーザー方針に反する。
- T-2871 の WAL 2 本を恒久置き場へ回収する (決定役の案) — (a)〜(c) を満たさない。
- B-5 発効 commit に tag `archive/t2797-b5-effect` を作る (決定役の案) — 上記の理由で不要。
- git の登録だけ外して directory を残す — 施錠・checkout と HEAD の対応・submodule 接続が壊れ、残した directory も再現に使えない (前日の決定役の判断を維持)。
- 到達不能 object 台帳へ削除 commit を転記する — 人間の喪失受容を要する期限つき台帳で、`/cleanup-branches` §5 も別 wave への引き渡しとしている。bundle の所在を集約 insight に書くに留める。
