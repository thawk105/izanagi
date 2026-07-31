# [T-181] 段4 裁定・plan v2・変異事前登録 (親)

段2 plan (rc=0)、段3 consult A / B (ともに rc=0、判定 NO-GO→条件付き GO) を親が裁定した。
`check_codex_output.py` は 3 本とも rc=0。

## 0. 親が独立に実測して確定した事実

| # | 事実 | 実測方法 |
|---|---|---|
| E1 | 歴史 focus1 の HEAD は `8c8dc5e0a337677e213b4ebabbeff5ea188111ae` (= `9b26b3b` の親)、branch は `codex/dev-wave-t153e-t15423` | rollout `session_meta.payload.git.commit_hash` |
| E2 | 歴史 focus1 は指定 9 入力**以外**に `CLAUDE.md`、`AGENTS.md`、`docs/dev-wave/{core,workers,operations,mutation}.md`、`docs/phase3.md`、`docs/worklog.md`、`docs/decisions.md`、`adjudication-plan-v2.md`、skill 定義 (`.agents/skills/dev-wave/SKILL.md` 等) を実際に読んだ | rollout の全 tool call 27 件を親が走査 |
| E3 | `8c8dc5e..9b26b3b` の numstat は 764/126 行。plan が示す fix1 期待値 693/123 との差は fix2 patch の追加量と整合 | `git diff --numstat` |
| E4 | `output/insights/2026-07-29_t153e-t15423-review-verbatim/` は `8c8dc5e` に**存在しない**。同 tree の `focus` 名 7 件はすべて先行 wave のもので R-1 を含まない | `git ls-tree -r` |
| E5 | `bwrap 0.6.1` + unprivileged userns が使える。`bwrap --tmpfs <repo> --tmpfs ~/.claude` + 新規 `CODEX_HOME` の下で `codex exec` は**完走し、auth も通り、`focus1.md` は到達不能** (`No such file or directory`) になる | 実 probe 2 本 (rc=0)。逐語は `probe.md` / `probe2.md` |
| E6 | 歴史 focus1.md の R-1 block には literal `check_cab` が**存在する** (1 hit) | `sed` + `grep -c` |
| E7 | 歴史 focus1.md の R-1 見出しは `### 残存finding R-1 — ...`、`real` 行は文字列 `refuted` を含む (`- real/refuted: **real**`) | `grep -n` |

## 1. 所見の real/refuted と採否

### 採用 (real、scope 内)

| ID | 出所 | 裁定 | 根拠 |
|---|---|---|---|
| A-1 | consult A F-1 / consult B 1 | **real・採用** | E2。歴史入力の byte 再現は不可能。「歴史再走」を撤回する |
| A-2 | consult A F-2 | **real・採用** | 正例 1 点では偽陽性能力が測れない。focus2 を負対照に入れる |
| A-3 | consult A F-3 | **real・採用** | R-1 は名指し済み = 確認実験。結論の射程を限定する |
| A-4 | consult A F-4 | **real・採用** | n=3 の判定規則を run 前に凍結する |
| A-5 | consult A F-5 / consult B 4 | **real・採用 (根拠は一部 refuted)** | E6 により「focus1 に `check_cab` が無い」は**refuted**。だが E7 の見出し形・`refuted` 語の混入は real で、素朴な regex は ground truth を落とす |
| A-6 | consult A F-6 | **real・採用** | 部分出力を分母から外すと arm 依存の劣化が消える。T-181 の主題そのもの |
| A-7 | consult A F-7 | **real・採用** | silent miss から runtime escalation は作れない。可観測失敗だけが gate になる |
| B-1 | consult B 1 | **real・採用** | mode/HEAD/untracked の pin 追加。逆適用 2 件は独立導出と突合 |
| B-2 | consult B 2 | **real・採用** | schedule manifest + fresh process envelope + set equality |
| B-3 | consult B 3 | **real・採用** | ledger issue 全件伝播、token/context 存在条件、effort 補完禁止 |
| B-5 | consult B 5 | **real・採用** | F54 型 join。run_id 主キーと逐件照合、row-swap 変異 |
| B-6 | consult B 6 | **real・採用** | 受入全走 (`orchestrator/tests` 既定収集) + 凍結 artifact の replay verifier |
| B-7 | consult B 7 | **real・採用** | 合成 fixture の自己追認回避。実 rollout slice を tracked golden に |
| B-8 | consult B 8 / consult A 漏洩 | **real・採用** | E5 により mount 隔離を**実装する**。transcript 監査は補助に降格 |

### scope 外 (real だが本 wave で実装しない → 裁定パッケージ)

| ID | 内容 | 理由 |
|---|---|---|
| X-1 | 非名指しの held-out 正例 (blind discovery stratum) | 新しい ground truth の作成と裏取りが別 wave 規模。**外的妥当性の最大の限界**として insight に明記する |
| X-2 | 非劣性検定に足る n の再設計 (margin/power) | 本 wave は記述的 sentinel。統計的主張をしない |
| X-3 | runtime の silent-miss escalation | oracle 不在で原理的に不可能 (A-7)。可観測失敗のみ gate 化できることを insight に書く |
| X-4 | CI workflow 新設 | repo に CI 定義が無いことを確認済み。受入全走への結線までを本 wave の scope とする |
| X-5 | model identity (backend build ID) の attestation | 取得手段が無い。`recorded effective effort` 表記で限界を明記 |

### refuted

- consult B 4 の「ground truth focus1 に `check_cab` が無いので plan の必須語は既知真陽性を落とす」は
  **refuted** (E6)。ただし同所見の**結論**(採点器を歴史 max の文体へ過適合させるな、歴史 focus1.md を
  positive control にせよ) は採用する。理由が誤っていても是正内容は正しく、かつ E7 は real。
- consult B 3 の「effort 不明を max で補完する既定値がある」は plan に無く refuted。
  ただし「context 0 件を明示拒否していない」は real なので、補完禁止を明文で登録する。

## 2. plan v2 — 確定仕様

### 2.1 枠組みの訂正 (最重要)

本 wave は**歴史 focus1 の再走ではない**。歴史 prompt から導出した
**新規凍結 benchmark 上の限定 A/B** である。insight・worklog・commit message で
「歴史 focus1 と同一入力を再走した」と書いてはならない。

### 2.2 benchmark snapshot

- 位置: repo 外の専用 root (`~/.t181-bench/`)。worktree ではなく `git clone` 由来の**自己完結 repo**
  (bwrap 隔離下で `.git` が repo 外を指してはならないため)。
- **正例 snapshot (POS)**: HEAD = `8c8dc5e` (branch 名も `codex/dev-wave-t153e-t15423` を再現)、
  `8c8dc5e..9b26b3b` の 6 ファイル差分を index に入れず working tree へ適用し、
  そこから fix2 patch を逆適用する。untracked に `review-a.md` / `review-b.md` / `fix1.md` を
  `08a7e5f2` の blob から置く (E4 より当該 dir は `8c8dc5e` に不在)。
- **負例 snapshot (NEG)**: 同じ手順で fix2 逆適用を**行わない** (= 統合 commit 相当の working tree)。
  → 歴史 focus2 の prompt が要求した入力に対応する。**`focus2.md` は絶対に置かない**。

**[訂正 A1 — 2026-07-29 23:12、段5 実装子の報告により親が是正]**
初版は NEG untracked を `review-a / review-b / fix1 / fix2 / focus1` と書いたが、
歴史 focus2 prompt の実測 (13 パス指定) と一致しない。確定規則は次とする。

> **untracked allowlist = その case の prompt が要求するファイル集合と厳密に一致させる。過不足を許さない。**

- POS untracked = `review-a.md` / `review-b.md` / `fix1.md` (3 件)
- NEG untracked = `brief.md` / `adjudication-plan-v2.md` / `review-a.md` / `review-b.md` /
  `focus1.md` / `fix2.md` (6 件)。`fix1.md` は NEG prompt が要求しないので**置かない**。

すべて commit `08a7e5f2` の blob から展開する。NEG が `focus1.md` を含むのは仕様どおりである
(歴史 focus2 の任務が focus1 所見の再判定であるため)。NEG の正解が「R-1 は closed」である以上、
これは答えの漏洩ではなく入力である。`focus2.md` はいずれの case にも置かない。
T-153(e) の `brief.md` / `adjudication-plan-v2.md` は段4 時点の文書であり、
R-1 (段6 focus1 で初出) を含まないことを親が確認した。
- oracle は plan の HEAD/index/dirty/numstat/bytes/untracked closure に加えて
  **B-1 の `st_mode`・symbolic HEAD・許可 untracked 集合**を pin する。
- 逆適用 2 ファイルの golden は**独立 2 経路**で導出して突合する。
  (a) `9b26b3b` − fix2 patch、(b) `8c8dc5e` + author patch + fix1 patch
  (author/fix1 session の rollout に `apply_patch` が現存)。両者が byte 一致しなければ rc≠0。
  同一 patch engine の round-trip だけを根拠にしない。
- snapshot 内に `focus1.md` / `focus2.md` が存在しないことを oracle の必須 assert にする
  (NEG の `focus1.md` は入力として意図的に置くので、NEG では `focus2.md` 不在のみ)。

### 2.3 prompt

- POS prompt = 歴史 focus1 の `user_message` 逐語 + root path 置換 9 箇所のみ。
- NEG prompt = 歴史 focus2 の `user_message` 逐語 + 同規則の置換。
- 置換は完全一致 byte 列のみ。path-neutral 同一性 assert を置く。
- 各 prompt は**一度だけ**生成し、その SHA を全 run receipt に束縛する。arm 名・effort を prompt に書かない。

### 2.4 隔離 (E5 で live 確認済み)

各 run を次で包む。両 arm 同一。

- `bwrap --dev-bind / / --tmpfs <izanagi repo> --tmpfs ~/.claude --tmpfs ~/.codex
   --bind <run 専用 CODEX_HOME> <同> --bind <snapshot> <同> --chdir <snapshot>`
- run 専用 `CODEX_HOME` は `auth.json` と `config.toml` だけを持つ新規 dir。
  rollout はそこへ書かれ、他 run・歴史 rollout は不可視。
- transcript の外部参照監査は**補助**として残す (「明白な外部参照の検出であって非参照の証明ではない」
  と出力 schema に明記)。

### 2.5 run schedule

- 正例: `max` 3 / `high` 3。負例: `max` 2 / `high` 2。計 **10 run**。
- **pair 同時実行**: 各 pair は (max, high) を**同時**に起動し、pair 間は逐次。
  理由: serving window を arm 間で等化する。逐次交互では時刻交絡が arm へ入る。
  代償として wall-clock は共有負荷の影響を受けるため**二次指標**とし、その旨を結論に書く。
- schedule manifest を run 前に凍結: `run_id → case(POS/NEG) → arm → argv sha → 出力 path 群`。
- fresh envelope: run dir は非存在から作成、`events.jsonl` / `.done` は開始時 size=0・fresh inode、
  launch 時刻 envelope 内。予定 run ID 集合と生成 session ID 集合を **set equality** で照合。
- pilot は置かない (E5 で隔離の生死確認が済んでおり、pilot を replicate に数える adaptivity 論点が消える)。

### 2.6 採点 (二層、primary は盲検人手)

- 機械層: 妥当性 (validity)、候補抽出、receipt。`r1_candidate` は候補に留める。
- **primary endpoint = 親の盲検意味裁定**。arm・effort・token を伏せた `blind_id` で逐語を読み、
  次の 3 命題の充足で `r1_detected` を決める。
  1. pre-policy commit でも canonical CAB parser (相当) が実行されると指摘している
  2. その失敗が従来 rc=0 を rc=2 へ変える (受理集合が縮む) と述べている
  3. NO-GO ないし must-fix 相当として扱っている
  同義表現を許す。関数名・R 番号・citation 完全性は**二次の evidence-quality 指標**へ分離する。
- **採点器の必須 control**: 歴史 `focus1.md` を正例、`focus2.md` を負例として通すこと。
  どちらかを取り違える採点器は実装前に失格。
- fence は backtick / tilde 双方を除去。`## 総括` 節**自体**の UTF-8 byte 数 500 以上を検査する
  (既存 checker は成果物全体を測るため不足)。

### 2.7 失敗分類 (A-6)

| 種別 | 例 | 扱い |
|---|---|---|
| pre-treatment (technical-invalid) | snapshot/effort/model/cwd 不一致、launch 失敗、session 同定失敗 | 分母から外す。pair 単位で無効化し**固定上限 2 回**まで再実行。全 attempt を保存し削除しない |
| post-treatment (arm failure) | 部分出力、`## 総括` 欠落/500 bytes 未満、GO/NO-GO 曖昧、推論後 abort | **assigned arm の失敗**として `scheduled_n` 分母に算入する |

token・wall-clock は invalid run も含めて全件計上する。

### 2.8 事前登録した判定表 (run 前に凍結、事後変更禁止)

| 観測 (正例) | 許される裁定 |
|---|---|
| max 3/3、high 3/3 | 「この 6 run で劣化を観測しなかった」。非劣性・同等・採用の証明にはしない |
| max 3/3、high 2/3 以下 | high は事前登録した zero-miss 安全条件を満たさない。統計的劣性とは言わない |
| max 2/3 以下、high 3/3 | benchmark または max 基準が不安定。high 優越とは言わない |
| 両方 2/3 以下 | 品質判断不能 |
| 負例で NO-GO / 偽 must-fix を観測 | 当該 arm の偽陽性 occurrence として記録。母集団 FPR とは言わない |
| technical-invalid 発生 | 2.7 の固定規則で処理し、全 attempt を保存 |

禁止表現 (insight・worklog・commit に書いてはならない): consult A の禁止リスト全 10 項目を採用する。

### 2.9 受入結線 (B-6)

- 新テストは `orchestrator/tests/` 配下に置き、既定全走に自然収集させる。`tools/run_tests.py` は変更しない。
- `codex_reasoning_ab.py verify --manifest <tracked manifest>` を実装し、
  凍結済み run artifact の replay 検査をテストから呼ぶ。live inference は受入全走に入れない。

### 2.10 所有

- 実装子 (Codex `role=author`) の編集集合 = `tools/codex_reasoning_ab.py`、
  `orchestrator/tests/test_codex_reasoning_ab.py` のみ。既存 ledger / checker / run_tests / docs は no-touch。
- 親: snapshot 構築の実行、隔離起動、10 run の実走、盲検裁定、変異、受入全走、記録、commit。

## 3. 変異事前登録 (DW-M01)

統合 commit 後に本走する (DW-O19)。各変異は「その位置より前に同じ入力を拒否する検査が無い」ことを
実装後に確認してから走らせる。確認できなければ登録を実効 gate へ再照準する (F28)。

| ID | 変異位置と内容 | 期待 kill 理由 (単一) |
|---|---|---|
| M1 | snapshot oracle の HEAD assert を任意 commit 許容へ | 誤 base の snapshot が受理される |
| M2 | 逆適用 golden の独立 2 経路突合を削除し (a) だけ採用 | 自己追認 snapshot が受理される |
| M3 | `st_mode` / symbolic HEAD / untracked allowlist の pin を削除 | mode 改変・余剰 untracked が受理される |
| M4 | session 同定で `id != session_id` を許容 | 二義化した session が受理される |
| M5 | schedule と生成 session の set equality を包含判定へ緩和 | 過去/別 wave session が枠を埋める |
| M6 | run 行の arm label を 2 行入れ替え (総数・合計は不変) | F54 型の誤帰属が逐件 oracle で殺されるか |
| M7 | ledger `issues` の failure reason 伝播を削除 | 0 token / 壊れ行の run が有効化される |
| M8 | `turn_context` 欠落時に requested effort で補完 | effort 不明 run が正しい arm と誤認される |
| M9 | post-treatment 失敗を technical-invalid へ再分類 | 部分出力が分母から外れ品質劣化が消える |
| M10 | 採点器の positive/negative control assert を削除 | ground truth を取り違える採点器が受理される |
| M11 | tilde fence 除去を削除 | fence 内の偽 `## 総括` が受理される |
| M12 | `## 総括` の 500 bytes 検査を削除 | 断片総括が有効 run になる |
| P1 (正例) | 完全に妥当な run 一式 | **緑のまま**であること (過剰拒否の検出) |

`DW-M08` に従い、受理集合を変えず構造化シグナルだけを pin する変異が出たら
kill 計上から外し diagnostic sensitivity pin として別枠に記録する。

## 3.5 段6 レビュー後の親裁定 (訂正 A2〜A6、2026-07-29 23:35)

段6 敵対レビュー A (must-fix 8) / B (must-fix 9) を受けた親の裁定。
実装面の是正は fix 子へ、仕様・運用の是正は以下で親が確定する。

### 訂正 A2 — Git object 閉包 (review B MF-2、**親が実測で確認**)

`git clone` した snapshot には 894 commit 全部が入り、
`git log --all -- .../focus1.md` から答えの commit `08a7e5f2` へ到達できることを親が実測した
(`git cat-file -e 9b26b3b` / `08a7e5f2` がともに成功、refs に main と全 remote branch)。
bwrap の path 遮断はこの経路を閉じない。E5 の probe が証明したのは
「その 1 path の ENOENT」だけであり、「歴史回答が不可視」への一般化は**取り消す**。

確定仕様: snapshot の object 閉包を `8c8dc5e` から到達可能な集合に限定する。
oracle の必須 assert は次とする。

- `git cat-file -e 9b26b3bd3acc…` と `git cat-file -e 08a7e5f2…` が**失敗**する
- ref は期待 branch 1 本だけ。remote / reflog / replace / alternates が空
- `git log --all -- <focus1.md path>` と `<focus2.md path>` が空
- untracked の答え隣接ファイルは plain file として書き、object store に入れない

### 訂正 A3 — 実行順を逐次 crossover へ変更 (review B MF-7)

初版の「pair 同時実行」を**撤回**する。共有 quota・rate limit・serving queue・host 資源を介して
相手 arm が primary 品質 (partial output・abort・retry) 自体を変えうるため、
wall-clock を二次指標と注記するだけでは足りない。

確定仕様: **事前乱数化した隣接逐次 crossover block**。1 block = 同一 case の (max, high) 2 run を
隣接して逐次実行し、block 内の先攻 arm を run 前に凍結した順序表で決める。同時実行はしない。
時刻傾向は block 番号と block 内順序で記録する。

### 訂正 A4 — primary の呼称と手続き (review B MF-5)

親が launcher 兼裁定者である以上、これを「盲検 primary」と名乗ってはならない。確定仕様:

- 名称は **label-masked adjudication** とする。「盲検」「blind」と書かない。
- 機械的に順序を強制する: 裁定 packet (乱数 ID・均一ファイル名・本文のみ、receipt/token/arm/順序なし)
  を生成 → 親が verdict を書く → verdict ファイルを hash で凍結 → **その後でしか** unblind map を
  出せない。凍結前に unblind した場合は rc≠0。
- 追加で、**独立した Codex read-only 裁定者 1 本**へ同じ packet と同じ codebook を渡し、
  第二読者として 3 命題判定を出させる。一致率を insight に記録する。不一致は親が保守側 (miss 扱い) で裁定する。
- 出力本文自体から effort が推測されうることは制御不能な残差として insight に明記する。

### 訂正 A5 — 「新規 finding」の定義 (review B MF-9)

実装に定義が無かった。確定定義:

> 新規 finding = (a) 事前凍結した既知 finding 集合 `{A-1, A-2, A-3, A-4, B-1〜B-6, R-1}` の
> いずれとも意味同値でなく、(b) label-masked 裁定で real と認定され、
> (c) root cause 単位で dedup されたもの。

R 番号や見出し件数を新規 finding 数にしてはならない。機械層は候補までを出す。

### 訂正 A6 — 判定表の全域化 (review B MF-8)

初版の表は全観測を覆わない。確定仕様として次の**優先順位付き決定関数**を run 前に凍結する。
aggregate は適用した row とその理由を機械出力する。

1. **experiment completeness**: retry 上限後も technical-invalid が残る slot が 1 つでもあれば
   `experiment_complete=false` とし、**品質裁定を行わない** (資源値のみ報告)。
2. **POS primary**: 3.5 の label-masked verdict で R-1 を検出した数 `k/3` を arm 別に取り、
   初版 2.8 の表を適用する。
3. **NEG adjudicated false finding**: 負例で real と裁定された must-fix が 1 件でもある arm は、
   その occurrence を記録し、POS が同点でも採用候補から外す。
4. **post-treatment reliability**: 部分出力・総括欠落・曖昧決定・推論後 abort の
   arm 別発生数を出す。これは **online の max escalation 候補**として別出力する
   (offline の不採用条件とは混ぜない)。
5. **resource report**: 全 attempt (invalid 含む) の token / model_calls / logical turn /
   wall-clock を報告する。品質裁定の入力にはしない。

silent miss は **offline の不採用条件**にのみ使う。runtime escalation の根拠にしてはならない (A-7)。

### 訂正 A7 — 禁止表現の統合

初版で採用した consult A の 10 項目に、review B の 15 項目を**加えて**採用する。
重複は統合し、insight・worklog・commit・裁定パッケージのいずれにも書かない。

## 4. 成果物影響 (DW-G05)

- 実装しない場合: reasoning routing の採用判断 (T-184) が逐語の目視だけになり、
  effort 配線事故・答え漏洩・run 誤帰属を検出できないまま stage matrix が確定しうる。
- 隔離を入れない場合: 新規 finding 数と結論強度が歴史回答の漏洩で水増しされ、
  reasoning 効果への帰属が崩れる。
- 負対照を入れない場合: 常に NO-GO を出す arm が「再現率 100%」に見え、採用方向が反転しうる。
