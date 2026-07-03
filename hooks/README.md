# hooks — 機械的防壁 (Python)

絶対規律1・2 を書き込み時点で機械執行する最小限の hook。auditor の事後監査に加えた第二防壁。
ECC のように大量の hook は持たない。下記2本だけ (規律5「盛らない」)。

**実装ステータス: 実装済・未配線 (Phase 3 タスク3、方針 A で再設計中)。** `.claude/settings.json = {}` で
**両 hook は未発火 = 第二防壁は現状ゼロ**。2 巡の敵対検証 (2026-07-02 / 2026-07-03) で real 13 件
(critical 1 = コメント行連結でコメント除去器を騙し `#define TRACE` を素通しさせる GW2R-1) を摘出し、
「テキスト検査で C++ 翻訳フェーズ・shell を完全再現するのは原理的に無理」を実証した。

→ **方針 A (ユーザー承認 2026-07-03, D30): hook の責務を一次防壁へ委譲する。** identity の honest さ
(偽 cache hit / `#ifdef`) は **source_digest の preprocess 後ハッシュ**、観測者効果の分離 (TRACE 混入) は
**観測者効果の二重検査** が一次防壁として担う。hook はテキスト検査の完全性に依存せず「明白な直接書き込み」
だけ止める最小の第二防壁に軽量化する (下記の記述は方針 A 反映後の目標形。実配線前に false-positive 4 件の
除去と単一障害点となっていた payload 検査の位置づけ変更を要する)。**「payload 検査が `#ifdef` の唯一の防壁」
という旧設計 (単一障害点) は放棄した** (GW2R-1/SPEC-2 が反証)。Phase 1-2 は variant がビルド時フラグの
組合せのみでコード変異が無く第二防壁は空でも実害が無かった (段階導入・規律5)。

## hook 1: guard_write.py (PreToolUse: Write/Edit/MultiEdit/NotebookEdit)

coder の編集面を EVOLVE-BLOCK に閉じ込め、成果物の proof chain を守る (規律1・2)。

- **成果物への直接書き込み拒否 (規律2):** `output/campaigns/*/runs/` (WAL)・`campaign.lock`・
  `build-variants/` への Edit/Write を拒否。COMMIT/fitness を書く唯一の経路は
  `pipeline.evaluate()` — verifier を迂回した性能数値の直接更新を塞ぐ。
- **編集面の限定 (規律1・2, D23/D24):** `external/ccbench/` 内は EVOLVE-BLOCK ソース
  (`source_digest.EVOLVE_BLOCK_SOURCES` = `include/backoff.hh`) だけ書き込み可。`Options.cmake`
  は source_digest 非被覆 = 偽 cache hit 源 (敵対レビュー F1) なので人間 template 専有 —
  template 改訂は `patches/` + `git apply` (Bash) 経由で行う。
- **payload 検査 (規律1・2):** 許可ソース内も、変更が EVOLVE-BLOCK の `#if` 枝 (payload) に
  閉じることを状態機械で検査 (マーカー・骨格・stock 枝 `#else`・領域外はバイト一致を要求)。
  payload 内の生プリプロセッサ指令 (行頭 `#` および digraph `%:`)・予約識別子 (`__*`/`_大文字*`)・
  `NDEBUG`/`GLOBAL_VALUE_DEFINE`・`TRACE`/`izanagi_trace` を拒否 (D23 道Y の機械執行 + 観測者
  効果の分離)。走査はコメント除去後の行頭アンカーで行い、in-comment の散文を誤検出しない。
- コメント除去は C++ 左優先の単一パス tokenizer (`//` 内の `/*` を誤ってブロック開始扱いせず、
  実コードを検査から消す攻撃を排除 = 敵対レビュー GW-1)。

## hook 2: guard_bash.py (PreToolUse: Bash)

guard_write が見ない Bash 経由の成果物書き込み (`echo >> wal.jsonl` 等) を塞ぐ (規律2)。

**設計 = allowlist 反転。** 初版は「書き込みコマンドを列挙して拒否」する blocklist だったが、
シェルの書き込み経路は事実上無限 (`find -delete`/`awk -i inplace`/`ex`/`ed`/`git mv`/サブシェルで
head を隠す/`>&` リダイレクト …) で列挙しきれず、敵対レビューで 12 件の迂回が実証された。
読み取り専用コマンドの集合は小さく安定しているので反転した: **防護対象に触れるセグメントは、
その head が既知の読み取り専用でなければ拒否 (未知コマンド = fails-closed)。** shlex
(punctuation_chars) でクォートを解決してからトークン単位で判定する。祖先ツリー (campaign dir /
ccbench root) を丸ごと削除・移動・展開する操作 (`rm -rf`/`mv`/`git clean`/`tar -C` 等) も、対象
パスが防護ツリーと重なれば拒否 (proof chain を配下ごと消させない)。

## 既知の限界 (正直に)

これは**テキスト検査の第二防壁であり sandbox ではない**。次は原理的に見えず、一次防壁
(`pipeline.evaluate` の fails-closed 設計 + WAL proof chain) と事後監査 (規律6) に委ねる:
- 変数展開でパスを組み立てる (`W=wal.jsonl; echo >> $W`)。
- スクリプトファイル越しの書き込み (`bash script.sh` の中身 / `python3 x.py` 内での open+write)。
  スクリプトファイルは監査可能な作業物として Bash 実行自体は許可する。
- `git commit -m "$(cat <<EOF ... EOF)"` の heredoc: メッセージに防護トークンが入ると不透明
  構文 (`$()`) 判定で拒否される。単一行 `-m` か `git commit -F <file>` で回避する。
- `rm -rf .` / `rm -rf ~` のような防護対象を名指さない CWD 全削除 (mention トリガに乗らない)。
- `chmod -R 000 <campaign dir>` のような権限剥奪 DoS: 末端ファイルへの chmod は末端層で拒否するが、
  祖先 dir への再帰 chmod は削除・移動でないため通す。ただし WAL 追記は `pipeline.evaluate` が
  PermissionError で fails-closed に倒れ (偽の成功記録は生まれない)、owner の chmod で回復可能。
- **ハーネス自身は防護対象外**: 防護ツリーは `output/campaigns` と `external/ccbench` のみで、
  一次防壁のコード (`orchestrator/campaign/pipeline.py`・`orchestrator/verifier/`)・hook 自身
  (`hooks/`)・`.claude/settings.json` への書き込みはどの hook も守らない。ここが汚染されると
  一次防壁ごと骨抜きになるが、緩和は規律6 の監査 + 人間のコミットレビューに委ねる (機械防壁を
  自己参照で増やすと規律5 と衝突する)。安価な補強候補: loop/pipeline の起動・終了時に
  `orchestrator/`・`hooks/`・`.claude/` の git 差分ゼロを assert し、差分があれば WAL に記録して停止する。

また guard_write の payload 禁止トークンは fails-closed 側に倒すため、決定的な `__builtin_expect`
等の正当な最適化も一律拒否する (hint を使わず書き直す)。

## テスト

`orchestrator/tests/test_hooks.py` が両 hook の判定核 (`decide()`) を直叩きし、敵対レビューで
確定した全 finding を回帰固定する (`test_bash_finding_bypasses_all_denied` 等)。settings.json の
配線と、subprocess として stdin JSON → exit code で動く煙テストも含む。
