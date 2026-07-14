# hooks — 機械的防壁 (Python)

絶対規律1・2 を書き込み時点で機械執行する最小限の hook。auditor の事後監査に加えた第二防壁。
ECC のように大量の hook は持たない。下記2本だけ (規律5「盛らない」)。

**実装ステータス: 実装済・配線済 (Phase 3 タスク3、方針 A)。** `.claude/settings.json` の PreToolUse に
両 hook を配線 (matcher = `Write|Edit|MultiEdit|NotebookEdit` / `Bash`)。方針 A (D30) で hook の責務を
「明白な直接書き込みを止める最小の第二防壁」に絞り、identity の正直さ (偽 cache hit / `#ifdef`) と
観測者効果の分離 (TRACE 混入) は**一次防壁 (source_digest)** に委譲した。

**Codex には未配線 (D54)。** Codex の `apply_patch` hook は `tool_input.command` に patch 全文を渡し、
Claude の Write/Edit の `file_path` 形とは異なる。既存 `guard_write` を設定だけ複製すると path 欠落を
管轄外として通すため、Codex adapter と parity test ができるまでは `.codex/hooks.json` を置かない。
これは新しい論理 hook の追加ではなく、既存 2 判定核の将来 adapter として扱う。

**3 巡の敵対検証で硬化 (2026-07-02 / 07-03 / 07-04)。** 各巡で Opus 赤チームが real finding を摘出し修正:
- 1・2 巡目 (旧 payload テキスト検査): critical GW2R-1 (コメント行連結でコメント除去器を騙し `#define TRACE`
  を素通し) 等 real 13。「テキスト検査で C++ 翻訳フェーズ・shell を完全再現するのは原理的に無理」を実証し、
  **方針 A = payload 検査を hook から削除し一次防壁へ委譲** (D30/D33)。
- 3 巡目 (方針 A 版 + 一次防壁): real 9 / known-limitation 6 / refuted 0。**critical = source_digest の
  builtin definedness (`#ifdef __x86_64__`) 偽 cache hit** — 方針 A の委譲先自身の穴 — を D34 (-undef 廃止) で
  封鎖。hook 側は絶対パス rm・改行セグメント・heredoc `<<`・symlink root fail-open・NotebookEdit decoy の
  bypass 5 件と、nm/du/tar backup の過剰拒否 3 件を修正。known-limitation 6 (docstring 明示の限界) は据え置き。

## hook 1: guard_write.py (PreToolUse: Write/Edit/MultiEdit/NotebookEdit)

成果物の proof chain を守り、coder の編集面を designated ソースに限定する (規律1・2)。**方針 A では
designated ソース内の内容は検査しない** — 何を書いても identity が正直に変わり (偽 cache hit しない)、
TRACE 混入は build 出口の一次防壁が捕える。

- **成果物への直接書き込み拒否 (規律2):** `output/campaigns/*/runs/` (WAL)・`campaign.lock`・
  `build-variants/` への Edit/Write を拒否。COMMIT/fitness を書く唯一の経路は `pipeline.evaluate()`。
  比較基盤は realpath で解決 (output/ が別ボリュームへの symlink でも fail-open しない, 3 巡目 fix)。
- **編集面の限定 (規律1・2, D23/D24):** `external/ccbench/` 内は EVOLVE-BLOCK ソース
  (`source_digest.EVOLVE_BLOCK_SOURCES`。現有の対象ファイルは同定数が正本 — 軸の追加で増えるため
  ここに値を再掲しない) だけ書き込み可。`Options.cmake` 等は
  人間 template 専有 — template 改訂は `patches/` + `git apply` (Bash) 経由。NotebookEdit は notebook_path を
  優先判定 (良性 file_path decoy で管轄を外せない, 3 巡目 fix)。
- **payload 検査は方針 A で削除 (D33):** `#ifdef`/生指令/TRACE 混入/偽 cache hit の担保は、テキスト検査の
  完全性 (原理的に破れる) ではなく一次防壁 = source_digest の preprocess 後ハッシュ + #include 行 HEAD 固定 +
  build 出口の diff-of-diffs (観測者効果) + TOCTOU 再照合が担う。意味的逸脱 (骨格破壊・領域外編集) の判定は
  auditor / 人間レビュー領域。

## hook 2: guard_bash.py (PreToolUse: Bash)

guard_write が見ない Bash 経由の成果物書き込み (`echo >> wal.jsonl` 等) を塞ぐ (規律2)。

**設計 = allowlist 反転。** 書き込み経路は事実上無限で列挙しきれない (敵対レビューで多数の迂回が実証)。
読み取り専用コマンドの集合は小さく安定なので反転: **防護対象に触れるセグメントは、その head が既知の
読み取り専用でなければ拒否 (未知コマンド = fails-closed)。** shlex (punctuation_chars) でクォートを解決して
トークン単位で判定する。祖先ツリー (campaign dir / ccbench root) を丸ごと削除・移動・展開する操作
(`rm -rf`/`mv`/`git clean` 等) も、対象パスが防護ツリーと重なれば拒否。3 巡目 fix:
- 絶対パス・`~` は repo_root で相対化してから照合 (`rm -rf /abs/.../output/campaigns/c` を塞ぐ)。
- 改行はセグメント境界にする (先頭行 read-only head が後続行 writer を隠蔽するのを防ぐ)。
- here-doc `<<` は不透明構文として fails-closed (bare interpreter への流し込みを塞ぐ)。
- 純読み取り (nm/objdump/readelf/ldd/size/du/zcat 系) を allowlist に追加 (規律1 の nm 手検証を止めない)。
- tar/rsync は read (backup) / write (展開・mirror INTO) を判別 (backup を巻き込まない)。

## 既知の限界 (正直に)

これは**テキスト検査の第二防壁であり sandbox ではない**。次は原理的に見えず、一次防壁
(`source_digest` の identity 核 + `pipeline.evaluate` の fails-closed + WAL proof chain) と事後監査 (規律6) に委ねる:
- **変数展開でパスを組み立てる** (`W=wal.jsonl; echo >> $W` / `$HOME/.../output/campaigns`)。シェルの実行時
  展開は hook から追えない。`~` は expanduser で解決するが `$VAR` は不能。
- **スクリプトファイル越しの書き込み** (`bash script.sh` の中身 / `python3 x.py` 内での open+write)。
  スクリプトファイルは監査可能な作業物として Bash 実行自体は許可。
- **部分 glob** (`rm -rf out*` / `output/campaign?`): メタ文字前のリテラル prefix でしか判定できない。
- **末端の tar/rsync backup** (`tar czf b.tgz .../build-variants`): archive 出力先の上書きリスクを厳密に
  判別できないため末端 (build-variants/WAL) を touch する形は拒否したまま (cp -r/nm で代替)。ツリー (campaign
  dir) の backup は通す。
- `git commit -m "$(...)"` の heredoc: メッセージに防護トークンが入ると不透明構文判定で拒否。単一行 `-m` か
  `git commit -F <file>` で回避。
- `chmod -R 000 <campaign dir>` の権限剥奪 DoS: 末端への chmod は末端層で拒否するが祖先 dir への再帰 chmod は
  通す。ただし WAL 追記は `pipeline.evaluate` が PermissionError で fails-closed に倒れ、owner の chmod で回復可能。
- **computed include** (`#if __has_include("x.hh")`): #include 行に現れず、-nostdinc で header 未発見なら
  digest 環境で dead 化 = identity に乗らない (実ビルドで header があれば別バイナリ)。auditor + 規律6 監査領域
  (git status に `?? x.hh` + `M backoff.hh` として露出)。builtin definedness (`#ifdef __x86_64__`) の方は
  D34 で digest に反映して封鎖済み。
- **ハーネス自身は防護対象外**: 防護ツリーは `output/campaigns` と `external/ccbench` のみで、一次防壁の
  コード・hook 自身・`.claude/settings.json` への書き込みはどの hook も守らない。緩和は規律6 の監査 + 人間の
  コミットレビュー (機械防壁を自己参照で増やすと規律5 と衝突)。

## テスト

`orchestrator/tests/test_hooks.py` が両 hook の判定核 (`decide()`) を直叩きし、3 巡の敵対レビューで確定した
全 finding を回帰固定する (`test_bash_finding_bypasses_all_denied` / `test_bash_round2_bypasses_denied` /
`test_bash_false_positive_fixes_allowed` / `test_symlinked_output_tree_still_protects` /
`test_notebookedit_decoy_file_path_denied` 等)。settings.json の配線 (4 tool matcher) と、subprocess として
stdin JSON → exit code で動く煙テストも含む。一次防壁 (source_digest) の網羅は `test_campaign.py`
(`test_source_digest_builtin_ifdef_not_aliased_to_stock` = D34 案A の critical 回帰 等)。
