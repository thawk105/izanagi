# Phase 3 タスク3 (H3 hooks) の実装と敵対検証

- **日付:** 2026-07-02
- **対象:** Phase 3 kickoff タスク3 — `hooks/guard_write.py` (Edit/Write 第二防壁) と
  `hooks/guard_bash.py` (Bash 経由書き込みの第二防壁) の実体化 + `.claude/settings.json` 配線。
  絶対規律1 (観測者効果の分離) / 規律2 (正しさゲートを緩めない) の書き込み時点執行。
- **方法:** 実装 → 多エージェント敵対検証 (4 レンズ = write 迂回 / bash 迂回 / 誤検出 / 仕様配線、
  各 finding を独立スケプティックが実機 repro で裁定) を **2 巡** + 実装者自身の independent probe。
- **位置づけ:** izanagi 内部の設計レビュー記録 (CCBench バグではない)。decisions D30。

---

## 中核的教訓: blocklist は原理的に穴だらけ → allowlist 反転

初版 `guard_bash.py` は「書き込みコマンドを列挙して拒否」する **blocklist** だった。1 巡目の
敵対検証は、この方式が**シェルの無限の書き込み経路を列挙しきれない**ことを 12 件の bash 迂回で
実証した。修正では **allowlist 反転** (防護対象に触れるセグメントの head が既知の読み取り専用で
なければ拒否 = 未知コマンドは fails-closed) を採用。読み取り専用コマンドの集合は小さく安定して
いるので、新種の writer は列挙せずとも自動的に落ちる。これが規律6 (fails-closed) の思想と一致する。

---

## 1 巡目で確定した 15 finding (全て実機 repro 済み)

### guard_write.py

- **GW-1 (critical):** `_strip_comments` がブロックコメント `/* */` を行コメント `//` より先に
  除去し、C++ レキサの左優先を反転。`// ... /*` の陰に `#include`/`__DATE__`/`TRACE` を隠すと
  実コード行が検査から消え、payload に任意の生指令・非決定 builtin・TRACE トークンを注入できた
  (hook2(b) の D23 道Y 執行 + 規律1 の第二防壁を無効化)。
- **F1 (high):** C++ digraph `%:` は g++ が `#` と解釈するが、行頭走査が `^\s*#` のみで
  `%:ifdef Linux` を素通し → digest 枝と実ビルド枝が乖離する identity 穴。

### guard_bash.py (blocklist の列挙漏れ群)

- **F-BASH-1 (critical):** `( rm ... )` / `{ cp ... ; }` / `if ...; then cp ...; fi` /
  `for ...; do cp ...; done` — サブシェル・グループ・制御構文がセグメント先頭に来ると head が
  シェル構文語になり writer 検査が発火しない **master bypass**。
- **F-BASH-3 (critical):** `awk -i inplace` / `perl -i -pe` が WRITERS・inline-interp いずれの
  検査にも掛からず WAL を in-place 改竄 (実ファイルで ABORT→COMMIT 偽造を実証)。
- **F-BASH-2/4/5, F2, F3, F4, BYP-parent (high〜medium):** `sed --in-place=SUFFIX` /
  `campaign"."lock` クォート分割 / `>&` リダイレクト / `find -delete` / `git mv` /
  `ex`・`ed`・`sponge`・`sort -o` / 親ディレクトリ削除 (`rm -rf output/campaigns/c`)。
- **F6 (low):** `chmod`/`chattr` による WAL 書込不可化 (DoS)。

### 誤検出 (allowlist 反転で解消すべき FP)

- **FP-quote-split (high):** 引用符を無視した正規表現分割で、`grep "a\|b" wal.jsonl` のような
  交替 grep が shlex ValueError → fails-closed で誤拒否。**セッション冒頭で実装者自身のコマンドを
  実際に止めた。**
- **FP-heredoc-commit (medium):** `git commit -m "$(cat <<EOF...)"` がメッセージに防護トークンを
  含むと `$()` 不透明判定で拒否。

（棄却 7 件: variants/ 書き込み・`$(nproc)` ビルド・scratch fixture・xargs 読み取り・cp 読み取り
方向・`git reset` unstage・`__builtin_expect` 一律禁止 — いずれも設計意図どおり or 実害なしと裁定）

---

## 修正 (1 巡目を受けて)

- **guard_write GW-1:** `_strip_comments` を C++ 左優先の単一パス状態機械に (`//` `/*` は先に
  現れた方が勝つ、文字列・文字リテラルは温存)。**F1:** 行頭走査を `^\s*(#|%:)` に拡張。
- **guard_bash 全面書き直し (allowlist 反転):** shlex punctuation_chars でクォート aware に
  トークン化 → 演算子・シェル構文語でセグメント分割 (head 隠し対策) → 末端に触れるセグメントは
  read-only allowlist 判定、リダイレクト先が末端なら head 不問で拒否、祖先ツリー破壊
  (`_overlaps_protected_tree`) は削除・移動・展開 head で判定。FP-quote-split はクォート解決で、
  F-BASH-4 (クォート分割) も同時に解消。

## 実装者 self-probe で追加発見

- **`rm -rf external` (穴, 修正):** `external` は `external/ccbench` の親だが `_MENTION_RE` に
  `external` 単独が無く fast-path 素通り → mention に `\bexternal\b` を追加。
- **`chmod -R 000 <campaign dir>` (穴, 既知限界):** 祖先 dir への再帰権限剥奪 DoS。tree-mutator に
  chmod を入れると reports の正当 chmod まで巻き込む FP を生むため、README に既知限界として明記
  (WAL 追記は pipeline が PermissionError で fails-closed、owner chmod で回復可能)。

全 finding は `orchestrator/tests/test_hooks.py` に回帰固定 (`test_bash_finding_bypasses_all_denied`
32+ ケース、`test_payload_comment_hiding_denied` / `test_payload_digraph_directive_denied`)。

## 残る既知限界 (第二防壁ゆえ一次防壁に委ねる)

テキスト検査であり sandbox ではない。変数展開でのパス組み立て・スクリプトファイル越し・
python 内書き込み・git commit heredoc の `$()` 拒否 (単一行 -m/-F で回避)・防護対象を名指さない
CWD 全削除・祖先 dir の chmod DoS。一次防壁 = `pipeline.evaluate` の fails-closed + WAL proof chain、
事後 = 規律6 監査。また **#ifdef 系は source_digest の `-Werror=undef` で捕まらず guard_write の
payload 検査が唯一の防壁**である (F1 検証で確認)。

## 2 巡目の敵対検証 (2026-07-03 完了)

修正版に対する 2 巡目 (Opus 4.8 Workflow、4 レンズ × 独立スケプティック裁定、Fable 最終裁定) を実施し、
**13 real を確定** (new-bypass 6・false-positive 4・spec-gap 3 / critical 1・high 6・medium 6)。1 巡目
fix 済み経路 (GW-1 コメント隠蔽・F1 digraph・F-BASH-1 サブシェル等) は回帰確認で今も DENY。

**結論: 「2 巡で硬化」は尚早。** 特に GW2R-1 (critical) は `_strip_comments` が C++ 翻訳フェーズ2 (行連結
= backslash-newline splice) を非モデル化する新種で、GW-1 が塞いだコメント隠蔽注入を別経路で再開し、上記
「#ifdef 系は guard_write の payload 検査が唯一の防壁」という**単一障害点**を突く (Fable が独立 repro で確定)。
SPEC-2 は同じ穴を Bash 経路 (`sed -i external/ccbench/...`) で示す。false-positive 4 件は allowlist 反転が
計測層を過剰拒否 (F-FP-1 = システム自身の repro コマンドを拒否)。hooks は現在 `.claude/settings.json={}` で
**未配線 = 実害ゼロ**。

**13 real の全機序・修正方向・未解決の設計判断 (hook 最小防壁化 + `#ifdef`/観測者効果の一次防壁委譲を推奨)・
working tree 状態・検証構成は、申し送り `2026-07-03_phase3-task3-h3-hooks-round2-handoff.md` に畳んだ。**
新セッションはそちらを起点にする。
