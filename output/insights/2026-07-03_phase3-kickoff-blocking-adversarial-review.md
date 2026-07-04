# Phase 3 kickoff blocking 実装 4 本 — 多視点敵対検証の結果と反映

- **日付:** 2026-07-03
- **位置づけ:** izanagi 内部の実装レビュー記録 (CCBench バグではない)。Phase 3 kickoff の残り blocking タスク
  (phase3.md) の実装直後、コミット前に独立コンテキストで敵対裏取り (規律6 の監査、Phase 境界・自作作業物の取り込み)。
- **対象実装 (未コミット時点):** (1) verify の abort 数を WAL に記録 (`pipeline.py`)、(2) apply/revert ハーネス
  (`campaign/patchharness.py` 新規)、(3) build 後の digest 再照合 = TOCTOU 遮断 (`buildcache._recheck_src_token`)、
  (4) #include 死角の閉塞 (当初 = 恒久案 `_source_parts` に include 行列を pre-image 織り込み)。
- **手法:** Workflow、30 エージェント (5 レンズ finder = 仕様突合 / identity 攻撃 [Opus] / ハーネス堅牢性 /
  consumer 追従 / テスト正直さ → 指摘ごとに独立裁定 real/refuted/known)。読み取りのみ・新規計測ゼロ。subagent
  tokens ≈ 1.90M。全 finding の証拠付き裁定は task output (session-scoped) に、要点を本ファイルに畳む。

## 総合判定

**real 22 (high 5 / medium 6 / low 11、重複統合後の本質 ~12 ベクタ)・known 2・refuted 1。** 最大の発見 =
**#include の恒久案が塞いだつもりの穴を塞げていない** (実機 probe で偽 cache hit 再現)。恒久案を撤回し **最小案**
(include 行集合を HEAD 固定 = include 追加自体を止める) に転換して解消。over-claim は git 履歴未固定の段階で撤回。

## real の統合 (ベクタごと・裁定後 severity・対応)

| # | ベクタ (統合) | sev | 検出 finder | 対応 |
|---|---|---|---|---|
| A | **#include 死角 = 恒久案の残穴**: include 行を identity に載せて「追加を許す」設計だが、include **先ファイルの中身**は identity 外 → 中身違いの新規 untracked header で variant 間 alias (probe: 中身 X/Y の synth_new.hh が同一 src_token → 既存バイナリに cache hit で Y が未コンパイルのまま certified)。`#if __has_include` (preprocess 環境と実ビルドで評価分岐) / #define computed include も同型 | high | spec, harness×2, identity-attack, consumer | **fixed (最小案化)**: 恒久案撤回 → `assert_includes_match_head` で include 行集合が HEAD と 1 行でも違えば resolve が abort。literal include の追加/差し替えを穴ごと停止。`__has_include`/#define は #include 行に現れず残る → **残存リスク化** (道Y 一般問題、guard_write payload 検査 + auditor 領域。完了条件 1 と両立して identity 核だけでは塞げない) |
| B | **apply/build/revert に排他が無い (ABA)**: 共有 working-tree の apply→(他セッションの build が汚染 tree を読む)→revert。TOCTOU 再照合は両端一致で見ない → 混合バイナリが共有キャッシュに永続 | high | harness | **fixed (緩和) + known 化**: `patchharness._tree_lock` (区間 flock) で single tree の並走 apply を直列化。**恒久解は段 5 の git worktree 隔離** (並列化)。※refuted 版 (骨格 inert で実害段が止まる) と両裁定 — flock は保守側の防壁として採用 |
| C | **revert 後 assert がタスク定義「porcelain 空」より弱い**: tracked のみ検査 (untracked skip) で、body 中に作られた patch 外 untracked 残骸が次 variant へ持ち越される | medium | spec | **部分対応 + 記録**: flock で並走 apply は排除。body 中の事故由来 untracked は tracked 検査では捕えない (docstring の「build 生成物は ignored」は正しいが porcelain 空より弱い) → 残存リスク。段 5 worktree で解消 |
| D | **非 ASCII パスの C-style quote 素通り**: `git apply --numstat` が非 ASCII を quote → 生文字列を FS 操作に使い残骸削除/leftovers 検査が両方素通り | medium | harness, test-honesty | **fixed (緩和)**: 全 git 呼び出しに `-c core.quotepath=false`。制御文字は残るが coder の非 ASCII ファイル追加は #include 死角 assert + EVOLVE-BLOCK 制約で手前で停止 |
| E | **revert の `git checkout -- .` が patch 外の並走変更を破壊** (fails-destructive) | medium | consumer | **緩和 + known 化**: flock で単一セッション内に patch 外変更が無いことを保証。並走は排他。恒久解は段 5 worktree |
| F | **テスト正直さ ×3**: build cache-miss 側 recheck 結線 / `_run_trace`→`_parse_abort_counts` 結線 / `applied()` enter の pinned-clean 駆動 — いずれも「実装を消しても suite 全緑」 | medium×3 | test-honesty | **fixed**: 回帰テスト 3 本追加 (`test_build_cache_miss_wires_recheck` / `test_run_trace_parses_abort_from_stdout` / `test_patchharness_applied_rejects_dirty_tree`) **※07-04 訂正: 実体は翌日追加** (下記) |
| G | **pin 照合が任意長 startswith で弱照合** (1 文字 pin でも通る) | low | spec, harness, consumer, test-honesty | **fixed**: `assert_pinned_clean` に 7 桁下限 (git 短縮 SHA 慣行未満を拒否) |
| H | **TOCTOU 破棄が rmtree(ignore_errors=True) で沈黙**: 破棄失敗した汚染バイナリが次 run の cache hit で再利用 | low | spec, harness | **fixed**: `_discard_build_dir` で破棄後の残存を検査し明示例外 |
| I | **applied() exit で HEAD==pin を再照合しない**: body 中に HEAD が動くと revert が新 HEAD 基準で clean 報告 | low | harness | **緩和 + 記録**: flock で単一セッション内は HEAD 不動。並走は排他。段 5 worktree で恒久 |
| J | **順序固定が docstring 規約のみ・駆動未配線** | low | spec | **仕様通り (記録)**: 配線は後続「coder.md + 全配線 1 周」タスク。未配線自体は仕様違反でない |
| K | **_recheck の transient rmtree が D25 と非対称**: resolve の一時障害でも新規ビルド成果を破棄 | low | consumer | **注記で正当化**: identity 不明バイナリを共有キャッシュに残さない (偽 hit 防止 > 再ビルド)。cache_key で再ビルドされ D25 の再評価可能性は保たれる。層が違う (WAL terminal vs キャッシュ清潔性) |
| L | **template patch 適用時の source_digest 実検査 3 件が skip 継続** | low | test-honesty | **既知 (記録)**: submodule に patch 未適用ゆえ (out-of-band 適用は評価時のみ)。実適用時のみ発火する検査。inert digest 検査の silent return は改善余地 |

## known 2 / refuted 1 (蒸し返さない)

- **known**: (1) `-undef` は標準 builtin (`__DATE__`/`__TIME__`/`__COUNTER__`) を除去しない → EVOLVE-BLOCK に混ざると
  digest 非決定化。既に phase3.md 残存リスク + guard_write の予約識別子 ban (方針 A) で対策予約済み。(2) revert の
  tree 全体 checkout が並走セッションの適用中 variant を巻き戻す (= E と同根)。flock + 段 5 worktree で解消方向。
- **refuted**: buildcache の TOCTOU 再照合が ABA を素通りする指摘のうち「patch 適用後 backoff.hh を読んだ混合バイナリが
  永続」の実害段は、patch 骨格が inert (BACKOFF_FIXED=-1 で #else=stock) ゆえ実行検証で停止を確認 → refuted。ただし
  ABA の理論核 (B) 自体は別 finder が real 裁定しており flock で対応済み。

## 反映後の状態

- 全 suite 緑 (174 passed, 5 skipped)。submodule は pin (dff0f1e) 不動・clean。
- phase3.md: blocking 4 タスクを `[x]` (実装済) に更新 + #include を最小案採用に書き換え + 残存リスク節に道Y 一般穴
  (`__has_include`/#define)・ABA の worktree 恒久解・transient rmtree 非対称を追記。
- **※ 2026-07-04 取り込み監査での訂正 (規律6、コミット前の突合で発見):** 本節と F 行の記述 2 点が
  未コミット差分の実体と食い違っていた — (1) suite は 174 でなく **170** passed だった (F の回帰テスト 3 本が
  「追加」と記録されたのみで実体が無かった)。07-04 セッションで 3 本を実装し、**変異検査 3/3** (各結線を消すと
  該当テストだけ赤 → 復元で全緑) で結線検査として機能することを実証。補完後 **173 passed, 5 skipped**。
  (2) phase3.md の `[x]` 化・最小案書き換え・残存リスク追記も**未実施**だった (同セッションで実施)。
  実装 4 本の本体 (pipeline / patchharness / buildcache / source_digest) は本表のベクタ対応と一致することを
  突合済みで、上記以外の食い違いは無い。
- **道Y 一般穴 (A の残) は後続段 4 (coder 自律期) で skeleton 検査として load-bearing にする** — kickoff (no-op /
  人間が値を与える純 timing) では coder が #if/#include/#define を発明しないので潜在。

## 成果物の場所

- 全 finding の証拠付き裁定 (JSON): task output `tasks/wjndhjerz.output` (session-scoped) + workflow journal。
- Workflow スクリプト: `~/.claude/projects/.../workflows/scripts/kickoff-blocking-adversarial-review-wf_73234b6e-5ff.js`
  (resume 可)。要点は本ファイルに畳んであるので JSON が消えても再開できる。
