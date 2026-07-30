指定資料はすべて読み取れました。read-only のため編集・pytest 実走はしていません。

結論として実装は可能ですが、親 brief の snapshot 前提と P1/P3/P5/P6 はそのまま採用できません。特に `9b26b3b` を checkout して fix2 を逆適用するだけでは、歴史 focus1 と同じ Git 状態になりません。

## 確認できた一次事実

- 歴史 focus1 の `session_meta` は HEAD `8c8dc5e0a337677e213b4ebabbeff5ea188111ae`。`9b26b3b` ではない。
- 当時は統合対象の6ファイルが unstaged dirty で、レビュー入力3ファイルが untracked だった。
- fix2 rollout には `response_item.payload.type=custom_tool_call`、`payload.name=apply_patch` がちょうど1件ある。
- fix2 patch SHA-256 は `19d21b9d78dd3abc4ae7d40e5ff9ed16b66437b3583aba8ddabb66ca080dd206`。
- 歴史 focus1 prompt は 2,000文字・2,706 bytes・末尾改行なし。SHA-256 は `511941738fd39a20ac9fb41ce2f4c3ed0039c35fca637ded0fa2fb6679667829`、旧 worktree root は9回出現する。
- 歴史 focus1 receipt の照合値は model calls 28、CLI reported token 320,640、task wall-clock 806,942 ms。歴史 max は scorer/receipt の oracle にのみ使い、実験 arm には数えない。

## 編集ファイルと予定行

実装子は次の2ファイルだけを所有します。既存 ledger/checker は変更しません。

| ファイル | 予定行 | 内容 |
|---|---:|---|
| `tools/codex_reasoning_ab.py` | 1–90 | T-181 immutable spec、source/patch/hash、arm、RC 定義 |
|  | 91–205 | JSONL streaming、prompt・fix2 patch の一意抽出 |
|  | 206–320 | fix2 の厳密な逆適用、snapshot materialization |
|  | 321–430 | snapshot oracle |
|  | 431–500 | prompt path rewrite と byte pin |
|  | 501–660 | thread ID による session 同定、ledger adapter、receipt |
|  | 661–820 | Markdown scorer、R-1 detector |
|  | 821–900 | aggregate、canonical JSON、CLI subcommands |
| `orchestrator/tests/test_codex_reasoning_ab.py` | 1–150 | 合成 JSONL/Git/Markdown fixture helper |
|  | 151–285 | source prompt・patch 抽出 |
|  | 286–430 | snapshot build/oracle |
|  | 431–525 | prompt rewrite |
|  | 526–690 | session 同定・receipt・token/wall-clock |
|  | 691–875 | score/R-1/曖昧出力 |
|  | 876–990 | RC、arm cardinality、deterministic output |

行番号は新規ファイル内の配置契約であり、実装時の最終差分で再確認します。

## 1. 凍結 snapshot

### 再構成手順

1. source commit を full hash `9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec` に固定し、その単一 parent が `8c8dc5e...` であることを assert する。
2. wave 専用 job directory 内に、`8c8dc5e...` を HEAD とする detached worktree を作る。
3. `git submodule update --init` を先に実行する。これは [DW-O08](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/dev-wave/operations.md:40) の停止条件。
4. `8c8dc5e..9b26b3b` の6ファイル分の diff を、index に入れず working tree へ適用する。これで内容は統合 commit 相当だが、Git 上は歴史どおり「parent HEAD + dirty files」になる。
5. sibling rollout 全体から fix2 `apply_patch` を一意抽出する。件数、rollout SHA、patch SHA、対象パス2件を検査する。
6. patch を fuzz なしでメモリ上で逆適用する。許可パスは次の2件だけとし、`Add/Delete/Move` やパストラバーサルを拒否する。

   - `tools/check_ai_provenance.py`
   - `orchestrator/tests/test_check_ai_provenance.py`

7. `review-a.md`、`review-b.md`、`fix1.md` だけを frozen commit `08a7e5f2fc08d57309a86ef70d00e9b050ebec9c` から展開する。現在の artifact directory 全体は、未来の focus1/focus2 結果を含むためコピーしない。
8. 実走前の各回と全実走後に同一 oracle を再実行する。run output は snapshot の外に置く。

9b を HEAD のまま逆適用する案は不採用です。ファイル bytes が同じでも、レビュー対象の `git diff`、commit history、provenance checker の挙動が歴史 session と異なるためです。

### 機械 oracle

HEAD、index、dirty set、bytes、untracked closure を独立に検査します。

対象 bytes の SHA-256 は次で固定します。

| snapshot 内相対パス | fix1 SHA-256 |
|---|---|
| `docs/ai-provenance.md` | `f00a045ba8d7e4a655b5a5e18beec94972291fb4c416b9bfcae6aeab97a75059` |
| `docs/decisions.md` | `16bc9b74fce0548c42e21a5d5076c9694bf2115b7d2d561f4522768366b3330e` |
| `tools/check_ai_provenance.py` | `bc3f5f95f5c9c3f44955bbd1b2e3affbbafb6e62fda8e836173e1b9d5998c3af` |
| `tools/check_docs.py` | `707f8f369086fe80cec9d296be8e9b3fad26a82ea08b7cc69149ec662e533195` |
| `orchestrator/tests/test_check_ai_provenance.py` | `ed3f93d196e7c43c8ba61c83f91f065d3fc829f0d12bdc4d9ead31b2ec3d57ed` |
| `orchestrator/tests/test_check_docs.py` | `38675b065a56230f8998b653d5da7e14d1d505f1c289ca0e84d5b5b2103b3e83` |
| `.../review-a.md` | `beea33ee7bb10acc583db30ef32252683c41fa3fe0ac3626db426103f5f102cc` |
| `.../review-b.md` | `04bbe6fc8feedca29b67f7ea9c29587e60539538592f8b9efe6db3f46f770f8c` |
| `.../fix1.md` | `e581c63399f20dbda51f223b05fbf4dadcf5e38961c9650dad2aca3756a39997` |

追加 assert は以下です。

- `HEAD == 8c8dc5e...`、detached HEAD。
- staged diff は空。
- unstaged path は上表のtracked 6ファイルだけ。
- `git diff --numstat` は歴史値と完全一致。

```text
3   3  docs/ai-provenance.md
45  0  docs/decisions.md
693 0  orchestrator/tests/test_check_ai_provenance.py
37  0  orchestrator/tests/test_check_docs.py
123 10 tools/check_ai_provenance.py
9   1  tools/check_docs.py
```

- untracked file はレビュー入力3件だけ。未来の prompt、focus1/focus2、receipt、score は不在。
- 入力9件は regular file、非 symlink、`realpath` が snapshot 内。
- submodule status に `-`、`+`、`U` がない。
- fix2 を再適用すると、2ファイルが元の9b bytesへ戻ることも round-trip assert する。
- 上記を canonical JSON manifest にし、その SHA-256 を全 receipt に記録する。

逆適用成功だけでは、誤った base、欠落した4 dirty file、余計な artifact、fuzzy context、誤 HEAD、mode/symlink 差を検出できません。したがって oracle は patch 実装と独立した歴史 bytes を正本にします。

## 2. prompt の逐語復元

`event_msg` のうち `payload.type=user_message` を全走査し、ちょうど1件だけ許可します。JSONL の物理10行目という位置は sanity check に使いますが、抽出条件にはしません。

書換規則は単一です。

- 旧 root `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423`
- 新 root は全6 run 共通の snapshot 絶対パス
- 旧 root の完全一致 byte sequence だけを9回置換
- 正規化、相対化、改行変更、末尾空白変更はしない

保証は次の三層です。

1. source prompt の文字数、bytes、SHA、末尾改行なし、置換件数9を先に assert。
2. 旧/新 root を同じ sentinel に置換した path-neutral bytes が前後で一致することを assert。
3. 各置換先の suffix が上記9入力に一対一対応し、bytes manifest と一致することを assert。

これは「参照対象と、それ以外の prompt bytes が変わらない」ことを保証します。異なる絶対パス文字列をモデルが潜在的に同じ意味として扱うことまでは数学的に保証できません。その残差を消すため、両 arm は同じ snapshot path と、同じ一度だけ生成した prompt file を使います。

render 後の prompt SHA を pin し、各 rollout 内の実 user message と byte 一致させます。arm 名や effort は prompt に書き込まず、CLI option だけで変えます。

## 3. run receipt

### ledger の再利用

token 定義は新規実装せず、[codex_worker_ledger.py:227](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:227) の `_stream_rollout`、[同:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:187) の `_billable`、[同:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:377) の終了分類を呼び出します。

CLI reported token は最後の有効な累積 `total_token_usage` について、

`input_tokens - cached_input_tokens + output_tokens`

です。28回の累積値を合算しません。reasoning token も output に再加算しません。

不足部分は新しい adapter が補います。

- [同:195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:195) の record に task timestamp、duration、prompt cardinality がない。
- [同:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:291) は最初の user message だけを保持し、一意性・byte identity を検査しない。
- [同:296](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:296) は task complete を bool に落とす。
- [同:727](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:727) の cwd substring filter は session identity には使えない。
- [同:773](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_worker_ledger.py:773) は process exit を unknown としている。
- requested/effective effort、model、output score、arm cardinality の gate がない。

### session 同定

各 `codex exec` に `--json` を追加し、stdout を arm-neutral な `run-01/events.jsonl` のような専用ファイルへ保存します。[DW-O01](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/dev-wave/operations.md:6) どおり `.done` の exit code が process completion の正本です。

1. CLI events から `thread.started.thread_id` をちょうど1件抽出。
2. session root の候補を走査し、`session_meta.payload.id == thread_id` の完全一致で検索。
3. 0件・複数件を拒否。cwd 部分一致は検索にも採用判定にも使わない。
4. filename suffix は候補削減にだけ使い、JSON 内 full ID を正本にする。
5. 六つの full session ID がすべて異なることを aggregate で検査。

さらに session/turn context の cwd は snapshot の完全一致、Git commit は `8c8...`、model は `gpt-5.6-sol`、CLI version は全runで同一、全 `turn_context.payload.effort` は要求 arm と一致させます。

### receipt 内容

run ごとに次を canonical JSON で保存します。

- requested/effective effort、model、CLI version
- thread/session/turn ID、rollout SHA、prompt SHA、snapshot manifest SHA
- `turn_count`。この実験では開始・完了の1対だけ
- `model_calls`。non-null `token_count.info` の件数
- raw input/cached/output/reasoning token と CLI reported token
- task start/complete の外側 RFC3339 timestamp
- wall-clock = 同じ turn ID の `task_started.timestamp` から `task_complete.timestamp`
- `task_complete.payload.duration_ms` は補助値。wall-clockとの差が1秒超なら malformed receipt
- process exit、aborted/incomplete/completed、output validation、score 状態
- transcript の snapshot 外参照監査

歴史 focus1 では外側 timestamp 差が 806,942 ms、payload duration が 806,975 msなので、この定義で既知値を再現できます。

## 4. 決定的 scorer

最初に [check_codex_output.py:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/check_codex_output.py:67) の `check_file()` を再利用し、[同:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/check_codex_output.py:37) と同じ fence 除外を適用します。`-o` の bytes と rollout の最終 agent message も完全一致させます。

抽出規則はコード commit 時点で固定します。

- fence 外に完全一致の `## 総括` がちょうど1件。
- 総括内に GO または NO-GO がちょうど1件。`NO-GO` を先に token 化し、その内部の `GO` を二重計上しない。
- 総括内の `must-fix` 行に `数字 + 件` がちょうど1件。
- GO iff 0件、NO-GO iff 1件以上。不整合は invalid。
- GFM table の ID/status header alias はコード内の有限集合だけ許可。
- ID は A1、A2、A3、A4、B1–B6 を各1回解決する。`A3/B1` は展開して双方に適用できる。
- status は強調記号を除去した完全一致 `closed|partial|regressed` のみ。
- reference mapping は以下。

| ID | reference |
|---|---|
| A1 | closed |
| A2 | closed |
| A3 | partial |
| B1 | partial |
| A4 | closed |
| B2–B6 | closed |

mapping が reference と異なっても、形式が一意なら品質差であり invalid にはしません。

新規 finding は fence 外の `### R-<正整数>` block だけを authoritative ID とします。重複 ID、構造化 block と本文の矛盾、残 must-fix 数との不整合は invalid。機械 scorer は「候補 finding」までを出し、real/refuted の最終裁定は effort/token を伏せた親の人手判定に分離します。

### R-1 事前登録規則

`r1_detected=true` は、単なるキーワード共起ではなく、唯一の R-1 block が次をすべて満たす場合だけです。

- status `regressed`
- severity `HIGH`
- literal `must-fix`
- disposition `real` または `実在`、かつ `refuted` でない
- `check_cab` と `_has_co_authored_by_policy` の両方
- `validate_message` と、`_co_authored_by_findings` または `_parsed_trailers`
- policy 計算と canonical parser の前後関係を示す固定語彙
- `rc=2`
- `tools/check_ai_provenance.py` の parser 側 160–176 と caller 側 368–379 の双方への file:line citation

R-1 block がない、または因果証拠が足りない場合は、形式が他の点で完全なら「有効 run の R-1 miss」です。R-1 block が複数ある、status が衝突する、must-fix 数を一意に決められない場合だけ invalid とします。最初の live run 後に regex や line range を緩める場合は、pilot を含む六runすべてを破棄して再開します。

## 5. fail-closed RC

per-run と aggregate を分離します。

| RC | 条件 |
|---:|---|
| 0 | receipt・output・score がすべて有効 |
| 20 | snapshot oracle、source/patch hash、prompt identity の失敗 |
| 21 | `thread.started` または対応 rollout が0件/複数件 |
| 22 | requested/effective effort、model、cwd、commit、CLI routing の不一致 |
| 23 | `## 総括` 欠落、validator failure、曖昧なscore、output bytes不一致 |
| 25 | process非0、aborted、task timestamp不整合、禁止パス参照など他の malformed run |
| 24 | aggregate 時に各armの scheduled_nまたはvalid_nが3でない |

複数失敗は receipt の `failure_reasons` に全件残し、per-run の primary RC は `20 → 21 → 22 → 23 → 25` の順で決めます。session 0件なら run RC 21、最終 aggregate は valid_n不足としてRC 24にもなります。

無効 run は品質低下や R-1 miss の分母へ入れず、代替 run も追加しません。修正が必要なら仕様を再凍結して全六runをやり直します。

## 6. テスト境界

合成 fixture で固定する範囲は次です。

- JSONL の0/1/複数 prompt・patch・thread/session
- patch path allowlist、逆適用、round-trip、hash不一致
- 「逆適用成功だが HEAD が9b」「余計なdirty/untracked file」など oracle の負例
- exact root 9回置換、0回/10回、path-neutral identity
- 同じcwdを持つ decoy session を thread ID で排除
- effort/model mismatch
- compacted cumulative token と CLI reported token
- model calls、task timestamp、duration、exit/abort
- fence 内の偽 `## 総括`
- GO/NO-GO、must-fix、merged A3/B1、重複/欠落 ID
- R-1 の正例と、キーワード共起だけの近接負例
- RC precedence、各arm 3件、canonical JSON の byte determinism

live inference なしでは固定できないものは、実効 routing の実サービス挙動、モデルの確率的再現率、新規 finding の実在性、実 token/time、rate limit、時間順序効果、snapshot 外の読み取り可能性です。これらは親の実走・人手裁定範囲です。

親は repo root から以下を実走します。[DW-O18](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/dev-wave/operations.md:95) に従い checkout も記録します。

```text
pytest -q orchestrator/tests/test_codex_reasoning_ab.py \
  orchestrator/tests/test_codex_worker_ledger.py \
  orchestrator/tests/test_check_codex_output.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

これは予定コマンドであり、今回緑を確認したとは記録しません。

## 7. 所有と実走順

実装子の repo 編集集合は、

- `tools/codex_reasoning_ab.py`
- `orchestrator/tests/test_codex_reasoning_ab.py`

だけなので、一実装子単位では自明に素集合です。`codex_worker_ledger.py`、`check_codex_output.py`、既存test、docs、frozen artifact、policy は no-touch とします。

親が所有するのは snapshot、prompt、run別 log/output/receipt、aggregate、insight、worklog/phase doc、統合 commit、実走・記録です。一時的tracked変異は実装 commit 後の専用 worktree に限定し、[DW-O19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/dev-wave/operations.md:102) に従って明示6パスだけを復元・検証します。

実走順は事前固定した `high-01, max-01, high-02, max-02, high-03, max-03` の逐次交互実行を推奨します。high-01 を pilot と数えてよいのは、snapshot、prompt、scorer、run command、artifact visibility を一切変更しなかった場合だけです。

## 親 brief の P1–P6 への裁定

- P1: 一入力に絞ること自体は交絡を減らす。ただし「focused review 一般」や policy escalation の外的妥当性は得られない。結論を「明示されたR-1正例に対する確認実験」に限定すべき。可能なら focus2 を負の対照として別実験にする。
- P2: 賛成。歴史 max は時刻・path・環境が違うため arm に混ぜない。
- P3: `n=3/arm` は記述的 pilot にすぎない。`k/3`、各run値、median/range は出せるが、再現率一般や有意差は主張できない。
- P4: named hypothesis は妥当。ただし R-1 は「新規発見」ではなく「既知仮説の検証」。新規 finding は別指標に分離する。
- P5: extractor と人手裁定の分離には賛成。提示された3語の共起だけでは closed/refuted 言及も真陽性になるため反対し、上記の因果・severity・return code・citation 契約へ強化する。
- P6: pilot 中に一切適応しない場合のみ replicate として数えられる。pilot 後に parser、prompt、snapshot、実行方式を変えたなら数えてはならない。high 先行だけの連続実行も時間交絡があるため交互実行にする。

DW-O01 の既定 reasoning 値を変更するコードは一切含めません。本 wave は per-invocation の観測だけです。

## 総括

実装の骨子は、既存の token 正本を再利用する一つの read-only 集計ツールと合成 fixture test を新設し、親が統合後に専用 snapshot と六つの run artifact を作る構成です。snapshot は `9b26b3b` を HEAD にした単純な逆パッチではなく、歴史 focus1 と同じ parent `8c8dc5e` を HEAD にして統合6ファイルを unstaged 展開し、その上で唯一の fix2 patch を逆適用します。HEAD、dirty set、numstat、9入力の SHA、untracked allowlist、submodule、prompt bytes を独立 oracle で毎run前後に確認します。session は cwd ではなく `thread.started.thread_id` と `session_meta.payload.id` の完全一致で同定し、要求 effort と実効 `turn_context.payload.effort` の不一致を fail-closed にします。

最大のリスクは、同じ一入力を三回ずつ回す小標本よりさらに手前にある「結果漏洩」です。現在のホストには歴史 focus1/focus2 の答えが存在するため、snapshot 内から除外するだけでは read-only sandbox が別パスを読めないことを証明できません。run transcript の外部パス監査を必須にし、可能なら親側の mount namespace/container で snapshot 以外を不可視にしない限り、強い再現率主張は避けるべきです。親 brief には、9b逆適用だけで十分という前提、三語共起の R-1 判定、適応後pilotの流用、`n=3` から一般的 escalation 条件を導く点で反対します。成立する insight は「凍結した既知R-1正例における max/high の記述的比較」であり、既定 policy の変更根拠や focused review 全般の推定値ではありません。