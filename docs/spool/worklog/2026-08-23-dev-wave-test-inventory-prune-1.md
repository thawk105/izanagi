---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-test-inventory-prune
seq: 1
title: 構文木が完全一致する冗長テスト 5 件を退役させた。棚卸しは第 1 tranche であり成長曲線は退役では曲がらない (コード+docs、branch worktree-dev-wave-test-inventory-prune)
---

## 本文

- ユーザー依頼は「不要なテストの棚卸しと削除」で、動機は**件数と量が永遠に成長し続けうる**こと。
  親は「証明可能に冗長なものだけ」を scope とし、14467 件から **5 件**を退役させた。
  判定基準と権限の出所は {{D:test-retirement-ast-candidate-only}} と
  {{D:test-retirement-authority-is-user-instruction}}。

- **本 wave は棚卸しの完了ではない。** 退役 5 件が消すのは約 1.3 KB。一方 `orchestrator/tests` は
  直近 8 日で +33 file / +3.0 MB (1 日あたり約 4 file) 増えている。
  **曲線を決めているのは追加の速度であり、退役では曲がらない。**
  この対比を書かないと、後から読む人が「棚卸しは済んだ」と誤読する。

- **段 3 レンズ A が親の判定基準そのものを反証した (blocker)。** 親は
  「同一 module 内で args + decorator_list + body が構文木レベルで完全一致 = 同一実行」を
  構文的証明として brief に書いたが、`conftest.py` が関数名を node ID へ変換して
  `xdist_group` と skip を分岐し、`growth_test_holds.py` が名前指定で wrapper 化し、
  plain runner が名前順で走る。**実行は名前に依存する。**
  親は基準を候補抽出へ格下げし、安全根拠を実測へ移した。

- **変異 matrix を削除前 (`4cbaf041`) と削除後 (`640d35f6`) の両方で走らせ、集合として比較した。**
  これが反証された構文的論証を置き換える中心的な証拠である。両走とも baseline PASSED / rc=0 /
  失敗 node 0、SURVIVED 0 件。

  | 変異 | 削除前の失敗 node 数 | 削除後 | 差集合 (消えた node) | 想定外の消失・増加 |
  |---|---|---|---|---|
  | M1 backlog sink 認識 | 291 | 290 | 退役した 1 件 | 0 |
  | M2 DW-S05-A の xhigh pin | 309 | 307 | 退役した 2 件 | 0 |
  | M3 protected stderr 正例分岐 | 7 | 6 | 退役した 1 件 | 0 |
  | M4 FC09/FC04 の先取順序 | 2 | 1 | 退役した 1 件 | 0 |
  | M5 C12 required allocation call | 68 | 67 | 退役した 1 件 | 0 |

  **5 変異すべてで、失敗 node 集合の差は退役 node ちょうどであり、想定外の消失も増加も 0 だった。**
  検出力の変化は「退役した node が消えた」以外に何もない。M2 で 2 件消えているのは、
  `test_check_docs.py` から退役した 2 件が**どちらもこの変異を検出していた**ためで、
  退役 node の総数と整合する。
  なお M1・M2・M3・M5 は MISMATCH (過剰決定) である。変異箇所が多数のテストの共通経路にあり
  単一理由性を満たさない。`DW-M03` に従い**単一理由性は主張せず**、
  「対の両 node が検出しており、削除後も残存 node が検出する」ことだけを主張する。
  単一理由だったのは M4 のみ。

- **段 3 レンズ B が blocker 2 件を出した。** (1) D99 決定 4 の「別の人間裁定と commit」のうち
  人間裁定を、親は「別 commit である」だけで満たしたと書いていた。(2) 本 wave は
  certified 選択・proof chain・台帳の値を 1 bit も変えないため `DW-G05` では nit/backlog である。
  いずれも**ユーザー直接指示を権威として逐語記録し、override の事実を隠さない**ことで解消した。

- **親の実測の誤りが 6 件、子と並行セッションに指摘された。すべて同じ型である** —
  道具が何を数えたかを確かめずに数値を出した。
  1. decorator を鍵から外したときの重複組数を「11 組・偽陽性 6」と書いた。正しくは
     **13 組・偽陽性 8**。親が本体長 300 文字の下限を掛けたまま数えていた (段 2 が指摘)。
  2. `output/insights/**` を「7936 file / 46.0 MB、テストの 4 倍」と書いた。正しくは
     **8928 file / 66.2 MB、5.4 倍**。`ruleops.py inventory` の絞り込み後の件数を総量として
     引用していた (レンズ B が指摘)。
  3. 重複の蓄積速度を「約 30 日で 5 件」と書いた。正しくは **11 日で 5 件**
     (08-11 / 08-12 / 08-12 / 08-19 / 08-21)。「重複が成立した commit」ではなく
     「古い側の関数の初出日」を見ていた (レンズ B が指摘)。
     この訂正は速度を約 3 倍にし、段 2 の「検出器は純増 +3 だから作らない」という
     算術の前提を変える。
  4. D666 を「冗長削減には negative control が要る」という一般則として引用し、
     そのうえで「構文木一致なので免除」と自分を例外にしていた。D666 は
     base/`--ff`/`--nf` の 3 variant 限定の裁定で、一般則ではない (レンズ B が指摘)。
  5. 「D689 は main に存在しない」と並行セッションへ通知した。**実在した** (27204 行)。
     使った抽出が `^## D689\..*?(?=^## D\d+\.)` で「次の見出し」を先読み要求するため、
     **D689 が最終節なので構造的に必ず落ちていた**。D688 は後ろに D689 があるので拾えていた。
     つまり親の検査は「末尾の 1 件だけを常に不在と報告する」道具だった。
  6. 変異結果の確認で存在しないキー `observed_nodes` を読み、全件「残存 node を含まない」と
     一度出力した。実キーは `failed_nodes`。

- **並行セッションとの相互訂正が機能した。** 裁定集約セッションは本日 7 件の誤りを
  自己申告・撤回しており、そのうち 3 件が本 wave へ届いた。逆に本 wave は
  同セッションの D689 と「削除と除外は別物」の一般化を撤回させた。
  **片方向の権威ではなく双方が一次資料へ戻る形**で、どちらの誤りも本番へ入らなかった。
  - 「削除と除外は別物、認められているのは実行対象から外すことだけ」という一般則の中継が
    届いたが、D679 の却下節の逐語は「既知赤を消す (テストを削除する)」、D681 の対象は
    「原因が理解された壊れたテストだけ」で、**どちらも赤いテストが対象**である。
    親が限定解釈を主張し、中継元が撤回した。
  - 「`test_growth_test_holds_contract.py` の 1 件が main 単独で決定的に赤」という周知も
    撤回された。実際は **Claude Code セッションの `FORCE_COLOR=3` / `COLORTERM=truecolor` が
    原因**で、dispatch 経由の受入全走は緑。親は自分のセッションに両変数が実在することを
    `env` で確認した。

- **証拠の届く範囲を決定文へ限定した。** 親の実測 (collect-only 差分・変異行列) は
  いずれも受入と同じ dispatch 環境で走る。色有効時だけ発火する差が対の両 node の間に
  あった場合、**この手順は構造的にそれを検出しない**。指摘が無ければ親は
  「実測が緑だから同値」と広く書いていた。受入受領証が固定する env は
  `PYTEST_ADDOPTS` / `PYTEST_PLUGINS` / `IZANAGI_TASK_RUN_ID` / `IZANAGI_TASK_RUNS_ROOT` の
  4 つで `FORCE_COLOR` を含まない (`tools/acceptance_launcher.py`)。

- **advisory 検出器は作らなかった。** 段 2 と段 3 レンズ B が独立に「作らない」を推奨した。
  D99 決定 1 が CLI を `inventory` / `inspect` / `check` の閉集合に限定しており、
  新 subcommand は D99 の改訂を要する。`tools/ruleops.py` と `test_ruleops.py` は無変更。

- **子の工数:** codex 子 5 本 (plan 1 / consult 2 / author 1、うち consult sol は 1 回目が
  `evidence_status=invalid` で不採用となり再投入)。1 回目の不採用は成果物 11468 bytes を
  生成した後の provenance 束縛の一過性競合で、rollout 本体は健全だった
  (session_meta=1、turn_context=1、破損行 0)。`max_attempts: 1` のため再試行余地が無かった。
  **親は生成済み成果物を拾わず、新しい job-id で再投入した。**

- **変異 spec の `category` は自由文字列ではない。** `negative` / `positive` / `both-layers` の
  閉じた列挙で、機序名を書くと spec 解析で中止する。このとき使い捨て worktree の container が
  残り、`git worktree list` に登録されたままになる。放置すると全 wave の land を止めるため、
  `git worktree remove --force` → `prune` → `rm -rf` まで行った。

## 次の一手差分

### 新規

- {{T:test-retirement-semantic-subsumption}} **P2・新規**: 意味的包含による退役候補を扱う。
  `orchestrator/tests/test_s8c_preregistration_predicates.py` の全 C01-C12 reason snapshot が
  同 file の C12 個別テスト 2 件を包含しうる (段 3 レンズ B)。採ると退役は 5 → 7 件、
  所要は追加で約 24 秒消える。**構文木一致では証明できず variant 固有の negative control が要る**
  ため {{D:test-retirement-ast-candidate-only}} の証拠水準を超える。
  ユーザー裁定を得てから着手する。

- {{T:test-duplicate-add-time-gate}} **P2・新規**: 追加時点で重複を弾く gate を裁定する。
  変更された test file だけを解析し、新規・変更関数を同一 module 内の既存関数と照合する形なら
  母集合が repo 成長に比例しない。**D99 決定 1 の閉じた CLI 集合の改訂が要る。**
  発火導線・docs 登録・`.claude/commands/dev-wave.md` (9,497/9,500 bytes) と
  `tools/README.md` (2,985/3,000 bytes) の予算逼迫まで一変更単位で設計する必要がある。
  蓄積速度の実測 (11 日で 5 件、うち 1 組は同一 commit で最初から重複して生まれた) が
  必要性の根拠。ユーザー裁定待ち。

- {{T:mutation-doc-budget-blocks-two-measured-fixes}} **P3・新規**: 段 8 で実測した
  `docs/dev-wave/mutation.md` への追記 2 件が byte 予算に入らないため裁定へ返す。
  内容は (a) spec の `category` は `negative` / `positive` / `both-layers` の閉集合で
  機序名を書くと解析で中止する、(b) spec 解析や実行の中止は使い捨て worktree を
  `git worktree list` へ登録したまま残し、残骸は全 wave の land を止めるので
  `git worktree remove --force` → `prune` → scratch 削除まで行う。
  親は追記を試みたが **L1 が予算 10625 に対し 10948、L1.5 が 9566 に対し 9796** で
  `check_docs` が赤になったため撤回した。既存文の圧縮で捻出するのは
  「予算のために安全義務を削除・弱化してはならない」に触れうるので行っていない。
  予算値の引き上げは自己改善の範囲外 (独立審査対象) であり、ユーザー裁定が要る。

- {{T:insights-corpus-retention-inventory}} **P2・新規**: `output/insights/**` の棚卸しを裁定する。
  8928 file / 66.2 MB でテスト資産の 5.4 倍あり、**成長の主質量はテストではなくこちらである**。
  D99 決定 2 は insights も inventory 対象に含めるが、D361 は論文・現状把握に使う証拠を
  tracked で残すことを求めるため一括削除はできない。
  「test 成長だけ」「D361 を守る retention-aware な insights 棚卸し」「両方」の
  択一をユーザーへ返す。
