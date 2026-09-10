# 裁定パッケージ — [T-1505] 床値救出 attempt registry で閉じられなかった 5 点

本 wave (dev-wave-t1484-floor-restart-registry) は D672 に従って共通 core の抽出と
8c 互換 facade までを実装した。**下の 5 点は実装せず、ユーザー裁定へ返す。**
いずれも「受理集合を変える」か「床値の意味 (estimand) を変える」判断であり、
AI が既成事実にしてよい範囲を超えている。

command が「ユーザー裁定が要ると判明したらそこで返す」と指示していたため、これに従う。

各項は段 2 codex plan と段 3 敵対 2 レンズが独立に出し、親がコードで検算して real と裁定した。

---

## R-a. 死んだ process の attempt を誰がどう引き取るか

**事実 (検算済み):**

- terminal を registry へ書けるのは、分類を実行したのと**同じ process・同じ thread** だけである
  (`orchestrator/campaign/trial_registry.py:3366-3370`:
  `capability._classification_owner != (os.getpid(), threading.get_ident())` なら拒否)。
- 次の slot を開始できるのは、前の slot に terminal があり、それが `retryable-failure` で、
  かつ観測開始の記録が無い場合だけである (同 `:2367-2382`)。
- PBS の wall timeout・node 障害・SIGKILL は**計測 process ごと殺す**ので、
  その attempt には terminal が永久に付かない。

**結果:** 救出経路の中核 —「落ちた構成を測り直す」— が現行の状態機械では**原理的に成立しない**。
`docs/phase3-8b-descriptor-design.md` §10.5 にもこの引き取り経路の規定が無い。

**択一:**

1. **新しい「引き取り (recovery)」event を作る。** 別 process が、外部証拠
   (scheduler の accounting 記録) を根拠に、放棄された attempt を terminal 化できるようにする。
   未知 event は今日拒否されるので、この event を **8b profile にだけ**許せば
   **8c の受理集合は不変**のまま拡張できる。
   - 利点: 8c を 1 bit も変えずに済む。D672 の実装条件を守れる。
   - 代償: §10.5 の追記が要る。「誰が stale を宣言できるか」の fencing 設計が要る。
   - **訂正 (段 6 レビューが親の論証を反証):** 親は段 4 で「profile の event 表へ足すだけで
     拡張できる」と論じたが、これは**誤りだった**。段 6 の 2 レンズが独立に、
     core の replay が「start / seal / classification / observation-start 以外はすべて terminal」
     という `else` 分岐になっていることを示した。つまり event 表に名前を足すだけで
     **core が semantic を実装していない event に terminal の semantic が付いてしまう**。
     本 wave はこの穴を fail-closed へ直したが、**recovery の実装は profile だけでは足りず、
     core 側に明示的な semantic handler を足す必要がある**。
     この裁定を実装する wave は core 改修を見込むこと。
2. **terminal の owner 束縛を緩める。** — **推奨しない。** 8c の受理集合が変わり D672 に反する。
3. **引き取りを作らない。** — 落ちた構成は測り直せないままであり、D496 決定 3 の
   「行き止まりを作らない」に反する。

**親の推奨: 択一 1。** ただし §10.5 の追記と fencing 設計を伴う別 wave が要る。

---

## R-b. 観測開始後に落ちた反復をどう扱うか (estimand の問題)

**事実 (検算済み):**

- 欠測反復があると `s8b_floor_stats.py:288` (`valid = coord_consistent and n_valid == n_sessions`)
  が**その cell を丸ごと失格**にする。数値の床値は `null` になる (同 `:342-405`)。
- 一方、次の attempt の値を主値に昇格させると、「完了した attempt だけを見る」ことになり、
  完了の起こりやすさが性能と相関する場合 (wall timeout は遅い run ほど起きやすい)
  **床値の estimand が変わる**。方向はデータ依存であり、
  「楽観側へ偏る」と一般化することはできない (段 3 sol の指摘。親の初回主張は誤りだった)。
- 「同じ attempt の続きから再開する」案は現行実装では**不可能**。
  rep 単位の耐久記録が無く、`rep_observations` は session 終了時に初めて journal へ落ちる
  (`s8b_floor_campaign.py:5366`)。

**択一:**

1. **永久欠測**とし、その cell の床値を `null` にする。
   - 利点: 統計的に正直。値を捏造しない。
   - 代償: **その対比は行き止まりになる。** D496 決定 3 に正面から抵触する。
2. **次の attempt を主値へ昇格**させる。
   - 利点: 行き止まりを作らない。
   - 代償: estimand が「固定 timeout と外部障害条件のもとで完了した run の条件付き性能」へ変わる。
     元の床値と同一だと主張できなくなる。
3. **失敗理由で分ける。** 性能と相関しない外部要因 (node 障害・preemption・probe 競合) は
   昇格を許し、性能と相関しうる要因 (wall timeout) は許さない。
   - 利点: 行き止まりを大幅に減らしつつ、偏りの主因を断つ。
   - 代償: 「どの理由が性能と相関しないか」を宣言する責任が生じる。

**親の推奨: 択一 3。** ただしこれは**床値の意味に関わる**ため、ユーザーの明示裁定なしに実装しない。

---

## R-c. 8b の閉じた再走理由集合と、その正本証拠源

**事実:** §10.5 は「許可理由を exact な列挙として事前登録の凍結範囲へ書く」「分類は信頼側が
性能出力を読む**前**に確定する」と要求する。現行 8b は理由の多くを `measure_fn` 実行**後**に
決めており (`s8b_floor_campaign.py:5290-5322`)、要件を満たさない。

**閉じていない点:**

- 集合の中身。段 2 plan は 5 個を提案したが、**受理集合を変えるので実装子判断で決めてはならない**。
- `scheduler_wall_timeout` / `node_failure` / `preemption` を何から読むか。
  PBS の accounting を読む authority は未設計である。
- SIGKILL・process 消失を retryable に含めるか。
  段 3 luna の推奨は「scheduler の accounting 受領証がある場合だけ retryable、
  単なる PID 消失は不可」。

**親の推奨:** R-b の裁定と同時に決める (どの理由を昇格可とするかが R-b の択一 3 と直結する)。

---

## R-d. §10.5「単一 registry の全履歴唯一性」をどう満たすか

**事実 (検算済み):** §10.5 は「同一 freeze に対する第二の root を全履歴走査で拒否する」と要求するが、
既存の共有 admission root は**削除・同一 bytes 再構成を検出できない**とコード自身が明記している
(`s8b_holdout_admission.py:4-11`, `:4054-4058`)。

**結果:** 共有 root を master にするだけでは §10.5 の唯一性要件を満たさない。
**満たしたと記録してはならない。**

**択一:** genesis の hash と canonical path を Git の content commit に pin する / 同等の
append-only authority を別に用意する / 唯一性要件を緩める (推奨しない)。

---

## R-e. 4 台帳の権威分担と crash cut

**事実:** 8b には既に 4 つの台帳が別々の意味を持って存在する。

| 成果物 | 現在の意味 |
|---|---|
| `claims/*.claim` | cell の一回性 master |
| run `journal.jsonl` の `session-start` | attempt authorization |
| `consumed/*.json` | ticket 消費の耐久事実 |
| `attempt-ledger.jsonl` | 消費の追記 log |

新 registry を足すと 5 つ目になる。**どれが権威で、どの順に書き、どの中断点から
どう復帰するか**の表が無い。段 3 luna は crash 形態 11 種のうち 6 種で復帰経路が
存在しないことを file:line で示した。

**併せて:** `session-start` (journal) と registry `start` の書き順に crash cut があり、
片側だけ残ると現行 resume がその session を永久に skip する
(`s8b_floor_campaign.py:5036-5039` の forward-only 契約)。

**親の推奨:** R-a の裁定後に、4 台帳 + registry の conflict truth table と recovery owner を
1 つの設計文書として起こす別 wave を立てる。

---

## 付録: 本 wave が見つけた既存 8c の穴 (別途の裁定候補)

**8c の attempt registry には、値を見た後に再走を得る経路が今日開いている。**

- `record_attempt_terminal` の明示 `failure_reason` は分類受領証の
  `pre_observation_failure_reason` を**上書きする** (`trial_registry.py:3385-3389`)。
- terminal 行は受領証の値を `pre_observation_failure_reason_echo` として持ち、
  echo が受領証と一致することは検査されるが (`:2504-2511`)、
  **`failure_reason` が echo と一致することは検査されない**。
- null matrix は `failure_reason` が retryable 集合に属することしか見ない (`:2253-2262`)。
- したがって「受領証の理由 = `None`」で封印した後、値を読み、
  `terminal_status="retryable-failure"` + `failure_reason="preempted"` を付ければ次の slot が取れる。
  観測開始を記録しなければ `:2367-2382` の拒否も通る。

**本 wave はこれを 8c 側で直していない。** D672 が「8c の受理集合を変えるな」と定めているため、
締めると受理集合が狭まって実装条件に反するからである。
代わりに、**この検査を profile の設定項目 (`require_terminal_reason_equals_classification`) にし、
8b profile では `True`、8c profile では今日どおり `False`** とした。

**裁定候補:** 8c 側をいつ締めるか。締めると 8c の受理集合が狭まるため、
凍結世代・事前登録との関係を含めた判断が要る。

---

## 付録 2: 段 8 の自己改善候補 (予算不足で実装できず)

**候補:** `docs/dev-wave/operations.md` の `DW-O09` (凍結 bytes の pin 閉包) は、
pin の探し方として `grep -rn "<成果物パス>" --include=*.py` を規定し、
「role 名を key に張る pin は key 側でも検索する」まで書いている。
しかし本 wave で 8c の受理集合を実際に決めていたのは、
`s8c_preregistration_evidence.py` の **AST 述語 probe** —
関数が `ast.FunctionDef` として実在すること、関数内の呼出し関係、live node の属性名と
文字列定数、到達性グラフ、top-level 名を key にする pin — だった。
これは path でも role 名でも引けない第三の型である。

**発火実績:** 本 wave。段 1 で親が独自に気づいたが、`DW-O09` の規定に従っただけでは見落とす。
実際、この pin を知らずに facade を再 export で書くと 8c の拒否理由が変わる。

**実装しなかった理由:** `DW-O09` は現に 996 bytes で、L2 単節予算は 1,000 bytes である。
余裕は 4 bytes しかない。既存文を意味等価に縮約しつつ probe 型を足す最小案でも
**+34 bytes** を要し、収まらなかった。
`docs/skill-self-improvement.md`「command 入口の編集条件」は
「予算のために安全義務を削除・弱化してはならない」「予算値を上げる変更は通常の自己改善に
含めず、理由付きの独立審査対象にする」と定めているため、実装せず裁定へ返す。

**択一:**

1. `DEV_WAVE_L2_SECTION_BYTES_MAX` を上げる (現行 1,000)。独立審査対象。
2. `DW-O09` の既存内容の一部を別 L2 節へ移して枠を作る。
3. 実装しない (この pin 型は各 wave が独力で気づくことに任せる)。

**親の推奨: 択一 1。** ただし予算値の変更は本 wave の権限外である。
