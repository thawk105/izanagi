# Phase 3 タスク3 (H3 hooks) — 2巡目敵対検証の結果と新セッション申し送り

- **日付:** 2026-07-03
- **前提:** 前セッション (2026-07-02) が H3 hooks (`hooks/guard_write.py` / `hooks/guard_bash.py`)
  を実装し 1巡目敵対検証で 15 finding を摘出・修正。**その修正版に対する 2巡目敵対検証を本セッションで完走した。**
  前セッションの記録は insight `2026-07-02_phase3-task3-h3-hooks-adversarial-review.md`、その末尾
  「2巡目の敵対検証」節を本セッションの結果で埋めた。
- **位置づけ:** izanagi 内部の設計レビュー記録 (CCBench バグではない)。decisions D30 は未記入 (方針確定後)。
- **本セッションの結論:** 前セッションが phase3.md を「H3 hooks 完了・2巡で硬化」とマークしたのは**尚早**。
  2巡目で **new-bypass 6・false-positive 4・spec-gap 3 = 計 13 real** を確定 (critical 1・high 6・medium 6)。
  hooks は現在 `.claude/settings.json = {}` で**未配線 = 実害ゼロ**なので、**配線を戻す前に方針を決める**のが正しい順序。

---

## 0. 新セッションの最初の一手 = 未解決の設計判断

**この判断が全ての起点。コードを触る前にここを決める。** hooks は未配線なので急ぎではない。

2巡目 real の**質**が分岐を突きつけている:
- bypass 6件の多くは「テキスト検査が C++ 翻訳フェーズ (行連結・単独 CR 正規化) や shell (glob・here-string・
  pipe・`git config -f`) を**完全再現しないと防げない**」= いたちごっこ (軍拡競争)。
- 特に **GW2R-1 (critical)** は insight 自身が認めた「`#ifdef` 系は guard_write の payload 検査が**唯一の防壁**」
  という設計上の**単一障害点**を突く。**SPEC-2** も同じ穴 (Bash 経路の `sed -i external/ccbench/...` が
  payload 検査を丸ごと迂回) を別角度で示す。
- false-positive 4件は allowlist 反転が**計測層を過剰拒否** (F-FP-1 は「システム自身が生成する repro コマンドを拒否」)。

**3 択 (Fable の推奨 = A):**

| 案 | 内容 | トレードオフ |
|---|---|---|
| **A. 設計見直し (推奨)** | テキスト検査の完全性を諦める。hook は「明白な直接攻撃」だけ止める**最小防壁**に戻し、`#ifdef`/観測者効果の分離は**一次防壁**に委譲: (1) source_digest の **preprocess 後ハッシュ** (phase3.md に既にある「既定 inert を preprocess 後ハッシュ一致」) で `#ifdef`/build 時マクロ由来のバイナリ差を捕える、(2) phase3.md の別 must「**観測者効果の二重検査**」(trace/perf 両ビルドの preprocess 出力 or シンボル集合 diff) で TRACE 混入を捕える。roadmap/decisions 改訂を伴う。 | 規律5「盛らない/ECC 化しない」と整合。hook が「唯一の防壁」でなくなり GW2R-1/SPEC-2 の単一障害点が消える。ただし roadmap 大改訂 = **ユーザー確認必須** (CLAUDE.md の版管理規律)。一次防壁側の実装 (preprocess ハッシュ・二重検査) が別途必要。 |
| **B. 全 finding 修正 → 3巡目** | 13 real を Opus 下請けでコード修正し、3巡目検証を回す。hook を賢くし続ける。 | 軍拡競争: C++ レキサ/shell を完全再現する方向で、3巡目でまた新種が出るリスク。規律5 と緊張。 |
| **C. 記録して区切り** | over-claim を撤回し 2巡目結果を正直に記録するのみ。修正・再設計は先送り。 | 前進しないが、hooks 未配線ゆえ実害ゼロ。最小コミットで安全に区切れる。 |

**Fable の推奨は A。** 理由: 2巡目 real の質が「テキスト検査で C++/shell の完全性は原理的に無理」を実証しており、
GW2R-1 と SPEC-2 が同じ単一障害点 (「payload 検査が唯一の防壁」) を突いている。これは hook を賢くして塞ぐ問題ではなく、
**その責務を一次防壁 (identity=preprocess ハッシュ / 観測者効果=二重検査) に移す**設計問題。A なら hook は「うっかり
直接書き込み」を止める第二防壁に軽量化でき、規律5 とも合う。

---

## 1. working tree の状態 (未コミット・警告)

**本セッションはコミットを 1 件もしていない。** 全て未コミット。方針確定まで保留するのが正しい。

```
M  docs/phase3.md      ← ★over-claim (SPEC-1)。H3 hooks を [x]完了・「2巡で硬化」とマーク。撤回対象。コミットするな。
M  hooks/README.md     ← ★over-claim。「.claude/settings.json の PreToolUse に両 hook を配線済み」と断言。訂正対象。
?? .claude/settings.json  ← {} (空)。前セッションが配線を外した。hooks は未発火 = 第二防壁は現状ゼロ。
?? hooks/guard_write.py   ← 実装済みだが 2巡目で GW2R-1(critical)/GW2R-2 の穴あり。
?? hooks/guard_bash.py    ← 実装済み (allowlist 反転) だが GB2-1〜4 の穴 + F-FP-1〜4 の過剰拒否あり。
?? orchestrator/tests/test_hooks.py  ← 回帰テスト。現状 18 passed / 1 skipped / 1 failed。
                                        唯一の赤 = test_settings_json_wires_both_hooks (settings.json={} ゆえ KeyError)。配線を戻せば緑。
?? output/insights/2026-07-02_...adversarial-review.md  ← 1巡目記録 (2巡目節を本セッションで追記済み)。
?? output/insights/2026-07-03_...round2-handoff.md      ← 本ファイル。
```

**規律6 の注意:** phase3.md / README の over-claim は **git 履歴には未固定** (working tree のみ) なので、まだ汚れていない。
**コミット前に撤回すること。** 「謳うだけで裏付けない保証」を履歴に入れてはいけない。SPEC-1 がこれを独立検出した =
2巡目検証が規律6 の裏取りとして機能した好例。

---

## 2. 2巡目 REAL 13 (severity 順) — 機序と修正方向

修正方向は各 verifier の裁定から抽出した**参考**。**方針 A を採るなら bypass 系の多くは「hook で塞ぐ」でなく
「一次防壁へ委譲」になる**ので、下記 fix は方針 B を採る場合の指針として読む。

### bypass (規律1/2 を破る = 防壁の穴)

- **GW2R-1 [critical / write-bypass] — Fable が独立 repro で確定 (§6)。**
  `_strip_comments` が C++ 翻訳フェーズ2 (行連結 = backslash-newline splice) を非モデル化。ブロックコメントを閉じる
  `*/` を `*` `\` `<改行>` `/` と綴ると、g++ はフェーズ2 で `\<改行>` を除去して `*/` に綴じコメントを閉じるが、
  hook は 2 文字窓で `*\` (≠`*/`) を見て BLOCK 状態を継続し後続を「コメント内」として食い潰す。結果 splice 後の
  `#define TRACE`/`#include`/`__DATE__`/`__builtin_*`/`NDEBUG`/`GLOBAL_VALUE_DEFINE`/`izanagi_trace` が
  strip 出力から消え `_payload_violations` は空 (ALLOW) だが g++ では active。規律1 (TRACE の perf ビルド混入)・
  規律2/D23 (生指令禁止)・digest 非被覆 (__DATE__ 非決定) を一括で破る。GW-1/F1 が塞いだコメント隠蔽注入の再開。
  **fix (B案):** `_strip_comments` の前段でフェーズ2 splice (行末 `\`+改行の除去) を先に適用してから状態機械を回す。

- **GW2R-2 [high / write-bypass].** `_strip_comments` の LINE 状態が `c=='\n'` でしか抜けない。g++ (libcpp) は
  **単独 CR (0x0D、後続 LF 無し)** も行末に正規化するので、`// c<CR>#define TRACE 1<CR>...` の CR で g++ は `//` を
  閉じ `#define`/`__DATE__` を active 化するが hook は CR を食い次の `\n` まで消す → ALLOW。CRLF は LF が双方で行末に
  なるので穴は**単独 CR に限る**。live 到達性は上流ハーネスが tool_input の単独 CR を正規化するかに依存 (未配線の
  本環境では未観測)。**fix (B案):** LINE 抜けを `c in ('\n','\r')` に + `_payload_violations` 側でも `\r`→`\n` 正規化してから `splitlines`。

- **GB2-1 [high / bash-bypass].** `_overlaps_protected_tree` はリテラル比較のみで shell glob を展開しない。防護ツリー
  root 以上に glob を置くと、(a) `rm -rf out*` は 'output' を字面に含まず `_MENTION_RE` を素通り (fast-path escape)、
  (b) `rm -rf output/*` は mention 発火しても `'output/*'` が `'output/campaigns'` と prefix 一致せず overlap=False。
  実機で `rm -rf out*` が output/ ごと消滅を確認。対照 `rm -rf output/campaigns/*` と `rm -rf output` は正しく DENY。
  **fix (B案):** 破壊 head + glob メタ文字を含むトークンは、防護ツリー root と字面が重なりうる時点で fails-closed。

- **GB2-2 [high / bash-bypass].** here-string `<<<` が `_OPAQUE_RE` (`<(` `>(` のみ)・`_REDIR_OPS` (出力系のみ)・
  `_SEG_OPS` のどれにも当たらず、`head=bash/python3` は `-c/-e` が無いと `_is_read_only=True`。よって
  `bash <<< 'rm -rf output/campaigns'` / `python3 - <<< 'code'` で任意コマンドを素通し。`bash -c '...'` は
  fails-closed なのに `-c` を `<<<` に替えるだけで迂回。実機で campaigns 消滅を確認。
  **fix (B案):** `_OPAQUE_RE` に `<<<` を含める (inline 実行同様 opaque=fails-closed)。

- **GB2-3 [medium / bash-bypass].** `echo "<leaf を含む python コード>" | python3` — `|` で `_segments` が分割し、
  leaf リテラルは echo (PURE_READER) 側に入るので leaf-touch 枝が発火せず、python3 側に leaf が無いので何も発火せず ALLOW。
  実機で WAL 内容を 'orig'→'FORGED' に改竄成功。`python3 -c "<leaf>"` は DENY できるのに、echo→bare interpreter への
  書き換えで leaf を洗浄しその明示防御を破る。**fix (B案):** パイプ終端が script-file 引数無しの bare interpreter なら fails-closed。

- **GB2-4 [medium / bash-bypass].** `_GIT_READ_SUBS` に `config` があり、`git config -f <protected> k v` (書き込み
  invocation) を read-only 誤判定。runtime 緩和あり: 既存の有効 JSONL WAL は git の INI parser が `bad config line` で
  改竄を止めるので、被害は**新規防護パス生成 / config 互換内容の書き込み**に限定。だが decide の read-only 誤分類自体は real。
  **fix (B案):** `_is_read_only` の git 分岐で `config -f`/`--file` を非 read-only に。

### false-positive (allowlist 反転の過剰拒否)

- **F-FP-1 [high / false-positive].** `_LEAF_RE` に `build-variants` が無アンカーで入り、末端層が「build-variants を
  含むトークン + head が read-only でない = 拒否」する。ベンチ binary は build-variants 配下なので、それを**実行するだけ**の
  計測コマンド (`perf stat -- .../build-variants/.../ycsb_silo.exe` / bare run) も拒否される。書き込み保護のつもりが
  **実行 (read/execute) まで潰す**。reports が `## 実験の再現` として自ら埋め込む cmake configure/build 手再現コマンドも全滅。
  自動ループは python ラッパ + subprocess list 形式で hook を通らず無傷なので、実害は手動/対話的な計測・プロファイル・再現に限局。
  **fix (B案):** build-variants は「書き込み (`>`/`tee`/`cp` 先/`sed -i`)」だけ拒否し、実行 (path が引数に出るだけ) は許可。

- **F-FP-2 [medium / false-positive].** `_overlaps_protected_tree` の `p.startswith(tree+'/')` が campaign dir の
  任意の子孫にマッチ。`_TREE_MUTATORS` (rm/mv/tar/rsync/install) が overlap を無条件拒否するので、proof-chain でない
  `output/campaigns/c/reports/` の散文・プロット・バックアップの mv/rm/tar/rsync まで拒否。`cp` は許可されるのに `mv` は
  拒否 = 非対称 (test_bash_reports_write_allowed が cp を ALLOW と固定)。**fix (B案):** tree-destroy 判定を proof-chain
  末端 (runs/wal/lock/build-variants) に触れる場合に限定し、reports/ 配下は除外。

- **F-FP-3 [medium / false-positive].** `_head_and_args` の wrapper skip は「`-`始まり / `\d+[smhd]?` 裸整数 / `-c`」しか
  読み飛ばさない。`taskset -c 0-47` の CPU リスト `0-47`、`taskset 0xff` のマスク、`numactl -C 0-47` の `0-47` は
  該当せず、実 head (grep/cat) を見失い `0-47` を head と誤認 → read-only 判定 False で WAL の純読みを拒否。
  **fix (B案):** taskset/numactl の値引数 (CPU リスト・マスク) を skip 対象に追加。

- **F-FP-4 [medium / false-positive].** `_MENTION_RE` が祖先削除まで拾うため `\boutput\b`/`\bexternal\b`/`\bccbench\b`/
  `\bcampaigns\b` の裸単語を含む。これが `--output=` フラグや 'external deps' 等に当たり、精査冒頭の `_OPAQUE_RE` 短絡拒否
  (厳密パス検査より**前**に走る) と組んで、防護対象パスが皆無でも「mention 語 + `$()`」で拒否。しかも拒否理由が「防護対象と
  不透明構文の同居」と**虚偽の存在を主張**。`perf stat --output=/tmp/... -t $(nproc)` が該当。
  **fix (B案):** `_OPAQUE_RE` 短絡を厳密パス検査の後段に回す、または mention 語を絞る。

### spec-gap (記述と実装の乖離)

- **SPEC-1 [high / spec-gap] — ★over-claim。** settings.json={} で両 hook は未発火 = 第二防壁は現状ゼロ。だが
  phase3.md:63 は「H3 hooks 2 本 + settings.json (完了)」、README:6-7 は「PreToolUse に両 hook を配線済み」と断言。
  さらに配線検査テストは `cfg['hooks']` で KeyError を吐き赤。**→ §1 の撤回対象。方針 A/B/C いずれでも先に撤回する。**

- **SPEC-2 [high / spec-gap] — ★責務帰属の誤り (GW2R-1 と同根)。** phase3.md:65 は「(hook2 guard_bash) designated
  ソース以外への Write 拒否」、:67 は「hook2 が source_digest の 2 被覆ギャップを編集面側で塞ぐ責務」、:85-86 は
  「payload 検査が #ifdef への唯一の防壁」と明示するが、実装はこれらを**全て guard_write (Edit/Write ツール) 側にしか
  置いていない**。guard_bash の防護対象は末端 (WAL/lock/runs/build-variants) とツリー破壊のみで、**Bash 経由の ccbench
  ソース内容書き込みは対象外**。よって `sed -i s/4/8/ external/ccbench/cmake/Options.cmake` (偽 cache hit)、
  `sed -i .../backoff.hh` / `printf '#ifdef ...' >> backoff.hh` (payload 検査迂回) が全て ALLOW。**方針 A の核心証拠:**
  「payload 検査が唯一の防壁」という設計自体が穴。identity は preprocess ハッシュに委譲すべき。

- **SPEC-3 [medium / spec-gap].** test_settings_json_wires_both_hooks の matcher assert が
  `any('Write' in m and 'Edit' in m ...)` の substring 検査のみ。matcher が `'Write|Edit'` だけ (MultiEdit/NotebookEdit
  欠落) でも PASS = 恒真寄り。だが guard_write.decide は MultiEdit/NotebookEdit を DENY する実装 = 実配線が必要。
  正しい matcher は `'Write|Edit|MultiEdit|NotebookEdit'`。**fix:** テストで 4 tool 全部を要求する assert に。
  **配線を戻す (方針 B/C) 際は、この matcher を使うこと。**

---

## 3. REFUTED 4 (蒸し返し防止 — 新セッションで再提起しない)

- **GW2R-3 [low].** `//...\<NL>#include` を hook が生指令として DENY する過剰遮断。だが payload の行頭 `#` は規律1/D23 で
  一律禁止ゆえ**正当作業を止めない** (splice で inert 化した指令は g++ で死コード)。→ refuted。
- **GW2R-4 [low].** 非正準位置 (`<campaign>/wal.jsonl`、深い階層の campaign.lock) への Write が ALLOW。だが pipeline は
  正準位置 (`<campaign>/runs/wal.jsonl`・`<campaign>/campaign.lock`) しか読まないので proof-chain 非該当。→ refuted。
- **F-FP-5 [low].** cp WAL バックアップ拒否・`$()` 純読み拒否。だが意図された許容限界 (cp は write 能力ありで allowlist 非搭載)
  で回避策あり (`cat WAL > file` / 変数事前計算)、1巡目で棄却済みの再浮上。→ refuted。
- **SPEC-4 [low].** main() の fails-OPEN。だが json.loads 例外時のみ到達し、ハーネスは整形 JSON を渡すので malformed
  stdin は敵対的にも運用的にも到達不能。保護 Write は必ず decide() が rc=2 を返す。→ refuted。

---

## 4. 検証の構成 (2巡目 = 本セッション)

- **手法:** Opus 4.8 の Workflow (`hooks-round2-adversarial`)。4 レンズ (write 突破 / bash 突破 / 過剰拒否 / 仕様配線) の
  finder が修正版 hooks を importlib で直叩き攻撃 → 各 finding を独立 Opus スケプティックが実機 repro で real/refuted 裁定
  → **Fable (メインループ) が最終裁定**。21 エージェント / subagent_tokens ≈ 1.38M / 17 candidate → 13 real。
- **なぜ Opus:** 攻撃 probe は cybersecurity 形状で Fable5 の safety classifier に flag される (§7)。かつ攻撃 repro は
  「下請け」に適する。設計・裁定は Fable が担う分業 (§7)。

---

## 5. GW2R-1 (critical) の Fable 独立確認

Opus 裁定を鵜呑みにせず、最重要の critical だけ Fable が guard_write を実機ロードして確認 (probe = 当時の scratchpad
`spot_gw2r1.py`)。攻撃 payload = `    double now_backoff = 5.0; /* hide *\<NL>/<NL>#define TRACE 1<NL>    double leak = __DATE__[0];<NL>`:

```
decide(Write) = (True, '')          ← ALLOW (bypass 成立)
decide(Edit)  = (True, '')          ← ALLOW
_strip_comments(攻撃) = '    double now_backoff = 5.0; \n\n\n\n'   ← payload 全消滅
_payload_violations(攻撃) = []       ← 空 = すり抜けの機序
g++ -E 同一バイト列 → double leak = "Jul  3 2026"[0];  (__DATE__ 展開)
                      double t = 1 + now_backoff;      (TRACE=1 が active)
#error probe rc=1 → splice が *\<NL>/ を */ に綴じコメント終了を実証
```

→ Opus 裁定は正しい。critical 妥当。**13 real を信頼する。**

---

## 6. 成果物の場所

- **2巡目の全結果 (JSON):** 前セッション tmp の `tasks/wj9jfq1cm.output` (session-scoped、新セッションからは
  パスが変わる/消える可能性)。**本 handoff §2-3 に全 finding を畳んであるので、JSON が無くても再開できる。**
- **Workflow スクリプト:** `~/.claude/projects/.../workflows/scripts/hooks-round2-adversarial-wf_dd90887e-b93.js`
  (resume 可、ただし攻撃プロンプト内蔵)。
- **hook 実装・テスト:** リポジトリ内 (§1 の working tree)。

---

## 7. セッション運用知見: モデル自動降格と 2 レーン分業

**事実 (Anthropic のポップアップで確定):** セッションモデルを Fable 5 にしても、izanagi の作業 (hook bypass・injection・
WAL 偽造の探索、CLAUDE.md の「攻撃/exploit/reward hacking」語彙、セーフガード議論そのもの) が **Fable 5 の safety
classifier に content-based で flag** され、その turn だけ **Opus 4.8 に自動切り替え**される。ポップアップ文面が
「intentionally broad ... may flag safe and routine coding, **cybersecurity** ... work」と明言。rate limit でもバグでもない。

**混同しやすい 3 つの別物:**
1. **「Allow this command?」権限プロンプト** = Claude Code 本体 (ハーネス) が未許可コマンド実行前に出す確認。危険判定ではない。
2. **guard_bash/guard_write hooks** = izanagi の第二防壁。**未配線で発火せず** (§1)。
3. **モデル降格** = Anthropic の safety classifier。上記のこれ。

**分業の指針 (このプロジェクトで有効):**
- **Opus 4.8 (サブエージェントに `model:'opus'` 明示):** 攻撃 probe・exploit repro・敵対検証。分類器 flag 対象 & 適材。
  ※本セッションで検証済み: Workflow サブエージェントは実測 338 対 1 で確かに Opus で走った (指定は効く)。
- **Fable 5 (メインループ):** 設計判断・最終裁定・文書・config・テスト・コミット。ただし攻撃要約を読む turn は分類器で
  Opus に落ちうる (害なし。Opus 4.8 で続行)。**分業しても、攻撃内容がメインループのコンテキストに載る限り私の turn は
  落ちうる** — これはコンテキスト由来で分業では消せない。
- 黙って切り替わるのが嫌なら `/config` →「Switch models when a message is flagged」をオフで選択制にできる。

**関連メモリ:** [[model-downgrade-fable5-classifier]] (本セッションで作成)。

---

## 8. 本セッションで確定した事実 (再検証不要)

- **decisions.md は無傷。** 前セッション末尾の「decisions.md 590 行以降が破損 (『省略された本文』等のメタ文言)」疑いは
  **tool 出力レイヤの一時的異常で、実ファイルは正常**。生バイト (od)・sha256 (working tree と HEAD が完全一致
  `71c468aa…`)・repo 全域 grep で、疑わしいメタ文言はどこにも存在せず、D29 の正しい本文が入っている。前セッションが
  規律6 として手を止めた判断は妥当だったが、実害は無かった。**decisions.md は触ってよい (D30 追記の対象)。**
- **hooks は `.claude/settings.json = {}` で未配線。** ユーザー/repo-local/repo いずれの settings にも PreToolUse
  エントリ無し。第二防壁は現状ゼロ。

---

## 9. 方針確定後の残タスク (順序)

1. **over-claim 撤回** (方針 A/B/C 共通・最優先): phase3.md の「完了/2巡で硬化」を実態 (2巡目で 13 real・未配線・未硬化) に、
   README の「配線済み」を訂正。**これをやってからでないと何もコミットしない。**
2. **方針 A なら:** roadmap/decisions 改訂案をユーザーに提示 (版管理セレモニー) → hook 軽量化 + 一次防壁 (preprocess
   ハッシュ・観測者効果二重検査) の設計。**方針 B なら:** 13 real を Opus 下請けで修正 → 3巡目検証。**方針 C なら:** 記録のみ。
3. **D30 追記** (decisions.md): 内容は方針次第 (A=責務の一次防壁委譲 / B=allowlist 反転 + 2巡の硬化)。
4. **worklog エントリ + MEMORY 更新** (モデル降格知見は §7・別メモリで済)。
5. **settings.json 配線** (B/C で hook を活かすなら。matcher は `Write|Edit|MultiEdit|NotebookEdit` / `Bash`。SPEC-3)。
6. **テスト全緑確認 → 論理単位ごとにコミット** ([[commit-granularity-and-progress-log]])。
