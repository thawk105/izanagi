# [T-1259] 段 4 裁定 — プラン v2 と変異事前登録

段 3 は 2 レンズとも NO-GO。所見 21 件を real / refuted、採用 / 不採用、scope 内 / 外で裁定する。

## 0. 親 brief の自己訂正

段 3 が親 brief の誤りを 2 件出した。どちらも認める。

1. **brief §1-2 の「ambient 継承するなら承認束縛の前提そのものに関わる」は過大だった。**
   `submit_floor.sh` の実投入 guard は shell 内部変数 `CONFIRM_OFFICIAL_FLOOR_RUN` を見ており、
   これを 1 にするのは CLI 引数だけである (`tools/pegasus/submit_floor.sh:33,44-46,84-87`)。
   ambient の `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` は guard 判定に一切使われない。
   したがって ambient 継承が有っても**標準 submitter の引数必須性は不変**である。
   影響が及ぶのは raw `qsub` の非標準経路だけで、そこは runbook §8 と D926 が既に保証外と明記している。
   正しい書き方は「ambient 継承の有無は、raw `qsub` 経路で承認 env がどう運ばれうるかの事実であって、
   sanctioned 経路の承認束縛を弱めも強めもしない」である。
2. **brief §4 の「[T-2228] が 2 本目到達を被覆している」は根拠として不成立。**
   両レンズが独立に反証した。T-2228 の 2 本目必須化とその先の成果物実在は
   「2 本目の値が存在した」ことしか示さず、**その値が `-v` の 2 番目 field で運ばれたのか
   ambient 継承で届いたのかを識別できない** — ambient 継承の有無が未確定である以上、循環する。
   格を「当該 2 request における未検証の間接証拠」へ下げる。
   本 wave は 1・2・3 本目すべてを新規の直接観測として扱う。

## 1. (P1) の確定

| # | 段 1 の provisional | 確定 |
|---|---|---|
| P1-a | T-2228 が 2 本目を被覆 | **不成立。** 上記のとおり格下げ。専用 request は不要だが、理由は「新 probe が 1〜3 本目を exact 再観測するから」であって「証明済みだから」ではない |
| P1-b | 承認ありの実 driver argv は観測しない | **支持。** 両レンズ一致。`floor_campaign.sh` は §8 (`:547-566`) と argv 組立て (`:1216-1225`) の間に repo 内 staging・claim・依存 build を挟む |
| P1-c | 6 file で閉じる | **支持。** 両レンズが独立検索で追加の閉集合を見つけられなかった。`test_plain_runner_coverage.py` の自走 harness で 7 本目を回避する |
| P1-d | 固有名 sentinel で ambient を測る | **名前選択のみ支持、測定設計は不支持。** §2-2 と §2-4 で作り直す |
| P1-e | 未承認実 driver は state を変えない | **CLI control flow については支持。主張の範囲を狭めて採用** (§2-5) |

## 2. 所見の裁定

### 採用 (must-fix)

- **A-1 / B-1 受信値を送信値へ exact 束縛する。** real・採用。
  投入側が `-v` 文字列を組むのと**同じ shell 変数**から create-only の
  `submission-manifest.json` を evidence dir へ書き、job 側が 3 値すべてを exact 比較する。
  値の入替え・置換で緑にならなくする。**順序は job の `os.environ` から復元できない**ので、
  manifest に記録するのは「投入 argv に書いた順序」であって到着順序ではないと明記する。
- **A-2 承認 env 自身の ambient 継承を測る。** real・採用・**scope 内**。
  これはユーザー依頼文の後半 (「NQSV が -v 指定外の ambient env を継承するか」) そのものであり、
  固有名 sentinel だけでは `IZANAGI_` 名が個別に除外される可能性を排除できない。
  **request を 3 本にする** (§3)。ambient に置く承認値は**わざと nonce と一致しない literal** にし、
  万一届いても承認として成立しない形にする (規律 2 を緩めない)。
- **A-2 追記 / B-4 投入 subshell で対象名を全 unset する。** real・採用。
  意図的に ambient へ置く 1 名を除き、`IZANAGI_SUBMISSION_NONCE`・
  `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN`・`IZANAGI_FLOOR_JOB_EVIDENCE_ROOT`・probe 固有 2 名を
  qsub 直前に unset する。親環境と `-v` の混入を断つ。
- **B-4 ambient 不在の陽性対照。** real・採用。attempt ごとに乱数 sentinel を生成し、
  `submission-manifest.json` に「qsub を呼ぶ process が実際に見た sentinel の存在・値・PID・時刻・
  `-v` の bytes」を記録する。これで job 側 absent が「継承しなかった」か
  「export し忘れた」かを分離する。
- **B-6 evidence 経路を PBS stdout に一次化する。** real・採用。**最も重い設計欠陥。**
  「job 実行中の `/proc/$$/fd/{1,2}` の親 directory が `qsub -o/-e` の最終 directory と同じ」は
  未実証の仮定であり、runbook §3 の「終了後に投入時 directory へ戻る」記述とも整合しない。
  observer は結果 JSON を**識別可能な単一行として stdout へ必ず出す**。
  `result.json` は補助へ格下げし、3 本目 (evidence root) が届かなくても結果が回収できるようにする。
  これで「届かなかった」と「evidence routing が壊れた」を分離できる。
- **A-6 / B-5 / B-10 repo への write 閉包を締める。** real・採用。
  PBS shell の冒頭から `GIT_OPTIONAL_LOCKS=0` と `ulimit -c 0` を効かせ、Python 起動前に
  cwd を job 専用 scratch へ移す。前後比較は tracked だけでなく **untracked path 集合**も取る。
  実 driver subprocess には**短い timeout** を付ける。
  不変条件の言い方を「repo working tree へ file を作らない・変えない。
  scheduler が持つ spool は閉包の外」へ狭める。「1 byte も」の literal 保証は主張しない。
- **B-3 焦点走に分類の実効性検査を足す。** real・採用。
  `test_bash_pegasus_registry_login_and_suspect_bits_are_pinned` と
  `test_bash_other_and_compute_keep_all_pegasus_entry_bits` を焦点走へ加える。
- **B-9 投入前に queue と非干渉を確認して記録する。** real・採用。
  `qstat -Q`・`pegasusinfo`・自分の稼働 request 一覧を投入直前に取り、外部 manifest へ残す。
- **A-9 result に権威区分を書く。** real・採用。
  `authority="diagnostic-only"`、probe schema、probe script の path と hash、
  `official_campaign_executed=false` を result に入れる。env 名は測定対象なので変更しない。
- **A-8 / B-12 緑でも言えないことを成果物に固定する。** real・採用。insight に専用節を作る。
- **親の独自所見 — 投入元を detached submit-tree にする。** real・採用。
  プランは wave worktree から `qsub` し job 側で HEAD 一致 + tracked-clean を要求していた。
  queue が詰まっている間 worktree を触れなくなり段 6 以降が止まる。
  **D1643 が既に「計測は wave worktree でなく固定 SHA の detached worktree (`submit-tree`) から
  投入する」と裁定済み**である。これに従う。

### 採用 (弱めて)

- **B-8 paired 完了判定。** 一部 real。**反復は増やさない** (queue を圧迫する)。
  投入 script が 3 request の ID・投入順・時刻・hostname・terminal state・result hash を
  外部 group manifest へ書き、1 本でも欠ければ全体を `indeterminate` と読む。
  **機械強制する新しい gate は作らない** — 読み方の規約として insight に書く。
- **A-5 / B-5 P1-e の主張範囲。** 「未承認 official argv は protocol loader・campaign core へ
  到達せず、repo の観測可能な内容を変えない」まで。**「process が何も書かない」とは書かない** —
  import closure 全体の副作用は 1 file の投影では証明できない。

### 不採用 / scope 外

- **B-11 §8 の汎用 4 分岐 evaluator と網羅 test を削る。** real・**採用** (削る側を採用)。
  実 job が作る条件は unset / exact-match / (3 本目 request の) ambient 値だけである。
  未観測の set-empty・mismatch を網羅する汎用関数とその test は、ユーザーが明示的に scope 外と
  した「仮想リスク向けの一般化」に当たる。**観測した条件についてだけ**現行 source の帰結を添える。
  false green を防ぐ負例 (env 欠落・repo 内 evidence path 拒否・create-only) は scope 内で残す。
- **B-7 sanctioned 経路への一般化禁止。** real・採用 (書き方の制約として)。実装追加はしない。
- **A-3 承認束縛を緩める提案の混入。** refuted (混入は無かった)。緩和は一切行わない。
- **A-7 追加の登録簿。** refuted。6 file を維持する。

## 3. プラン v2 — 3 request の設計

投入元は **detached submit-tree** (固定 SHA)。各 request の walltime は `00:10:00` を維持する。
これは上限であって占有量ではなく、実 driver subprocess に短い timeout を付けるので
実占有は 2 分程度になる。**過大な短縮で job が結果を書く前に殺される方が損失が大きい**。

| request | `-v` の中身 | 投入 shell の ambient | 何が分かるか |
|---|---|---|---|
| R1 承認あり | `IZANAGI_SUBMISSION_NONCE=<hexA>`, `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=<hexA>`, `IZANAGI_FLOOR_JOB_EVIDENCE_ROOT=<絶対 path>` | sentinel のみ (対象名は全 unset) | `submit_floor.sh` 最大構成と同じ 3 名・同じ値の形が exact に届くか |
| R2 承認なし | `IZANAGI_SUBMISSION_NONCE=<hexB>`, `T1259_QSUB_SECOND_HEX=<hexC>`, `IZANAGI_FLOOR_JOB_EVIDENCE_ROOT=<絶対 path>` | sentinel + `T1259_QSUB_SECOND_HEX=<hexD≠hexC>` | 3 本 exact 到達。**同名が `-v` と ambient の両方にあるときどちらが勝つか**。未承認の実 driver 拒否の実測 |
| R3 ambient のみ | `IZANAGI_SUBMISSION_NONCE=<hexE>`, `IZANAGI_FLOOR_JOB_EVIDENCE_ROOT=<絶対 path>` (2 本) | sentinel + `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=<nonce と一致しない固定 literal>` | **承認 env 名そのものが ambient 継承するか。** 2 本構成の到達 |

R3 の ambient 承認値は `t1259-ambient-approval-must-not-match` のような、32 桁 hex ではない
固定 literal にする。届いても `floor_campaign.sh:559` の exact 一致検査を通らない形である。

実 driver の未承認拒否観測は **R2 だけ**で行う。R1・R3 では起動しない。

## 4. 変異事前登録 (DW-M01)

実装後に「他層が先に拒否しないこと」を確認し、確認できないものは登録から外して実効 gate へ再照準する。

| ID | 変異位置 | 期待 kill | 単一理由性の見込み |
|---|---|---|---|
| M-1 | observer の受信値 exact 比較を存在検査へ緩める | 新 test の値入替え負例 | 単一 |
| M-2 | 対象 env 欠落時に `ok=true` を返す | 新 test の欠落負例 | 単一 |
| M-3 | evidence dir が repo 内でも受理する | 新 test の repo 内 path 負例 | 単一 |
| M-4 | result publish を上書き許可へ変える | 新 test の create-only 負例 | 単一 |
| M-5 | 未承認 driver の rc 期待を 2 から任意へ緩める | 新 test の rc 固定 | 単一 |
| M-6 | 未承認 driver argv から `--mode official` を落とす | 新 test の argv 完全一致 | 単一 |
| M-7 | 未承認 driver argv へ承認 flag を足す | 新 test の argv 完全一致 | 単一。**規律 2 の中心** |
| M-8 | stdout への結果 1 行出力を落とす | 新 test の stdout 契約 | 単一 |
| M-9 | PBS の compute-only hostname 検査を削る | 新 test の PBS 静的検査 | 単一 |
| M-10 | PBS の `ulimit -c 0` / `GIT_OPTIONAL_LOCKS=0` を削る | 新 test の PBS 静的検査 | 単一 |
| M-11 | registry の新 entry の class を `unknown` へ | `test_hooks.py` の class golden | **冗長あり** — runbook 投影検査も赤になる見込み。実装後に確認 |
| M-12 | 新 test の `pytest.main([__file__])` を削る | `test_plain_runner_coverage.py` | 単一 |

## 5. 成果物影響 (DW-G05)

放置すると、official 床値の投入が gen_S の 10 時間確保を消費したうえで driver の CLI 関門で拒否され、
床値が 1 件も出ない。certified 選択が使う床値入力が materialize しない。
本 wave が測るのはその輸送経路の実在であって、official 走行の認可ではない。
