# 裁定パッケージ — [T-798] / [T-799] fold transaction の窓

wave: `dev-wave-t798-t799-fold-window`
測定 checkout: `.claude/worktrees/dev-wave-t798-t799-fold-window` (HEAD `9abd23da` → `974207ae`)
一次資料: 同 wave dir の `findings.md`、probe と log は `probe/`、敵対レンズ 2 本は
`consult-sol.md` / `consult-luna.md`。**本番コードは 1 行も変えていない。**

両方の窓は**実在し、そのまま再現した。**

- [T-798]: 窓の内側で land を SIGKILL すると、canonical・`FOLDED.md`・fragment GC は反映済み、
  fold commit も transaction state も無い状態が残る。
  **正規の復旧 CLI (`python3 tools/spool_fold.py`) は rc=0 / `status=noop` を返す** — 何も言わない。
- [T-799]: state が束縛する field は 8 個で、HEAD・land 起源・base・tested tip はどれも入っていない。
  resume 経路は新規 apply が通る `_git_clean_preflight` を**通らない**。
  そして **state が hash で束縛するのは plan の *target* だけで、採番の入力は束縛されない** —
  archive worklog を変えてから resume させ、**重複した T 番号を実際に作った**。

**両者は独立ではない。** standalone resume は commit を作らないので、成功した瞬間の tree は
[T-798] の crash 残骸と 1 文字も違わず、次の land は rc=20 で止まる。

**敵対レンズ 2 本 (`consult-sol.md` / `consult-luna.md`) が親の主張を複数崩した。
親はそれを受けて追加実測を 3 本行い、当初の推奨と数値を大きく書き換えている。**
撤回・縮小した主張は次のとおりで、詳細は各問と `findings.md` にある。

| 当初の主張 | 判定 | 訂正後 |
|---|---|---|
| 窓は約 2.83 秒、96% が check_docs、land 1 回ごと | **撤回** | commit と postcondition を除いた **pre-commit の代替小計**。露出の分母は land 数でなく **non-noop fold 数** |
| (b) は新しい recovery 機構を要らない | **撤回** | (b) は窓を「commit 済み・state 残存」へ**移す**。その形から land は rc=10 `stale-main` で止まる (追加実測) |
| 新 field は省略可能として読めばよい | **撤回** | fail-open。厳格側を既定にし、旧 state の扱いを別問にした |
| (a) で proof chain が durable になる | **撤回** | state は成功時に消え、receipt は base/tip を持たない。durable な置き場が別に要る (Q3 を新設) |
| 発火条件は process 死に限る | **縮小** | 通常例外 + rollback 失敗の二重故障でも同じ残骸になる |
| [T-766] が増やす state と同じ形 | **撤回** | 測ったのは pre-mutation state。rollback 失敗で残る形は別 |
| C2 は帰属が壊れた欠陥 | **縮小** | 測った C2 は正常動作。実害は「採番入力の未束縛」で別に実測した |
| standalone resume は必ず残骸に着地 | **縮小** | 現行コードでは成立。(b) 採用後は健全な反例ができる |
| (b) が壊すテスト pin は 5 行 | **訂正** | **1 本だけ**。land 側だけ挙動を分けるなら 0 本 |

---

## Q1. [T-798] — apply_fold の state 削除から commit までの窓をどう塞ぐか

### 実測した現状 (c) のリスク

| 項目 | 実測値 |
|---|---|
| 窓の幅 | **pre-commit 部分だけの代替小計で約 2.83 秒**、その大半が `check_docs.py`。commit と postcondition は含まない (end-to-end は未測定)。露出の分母は **non-noop fold の回数** (fragment 0 件の land は窓へ入らない) |
| 発火条件 | **process 死** (SIGKILL / OOM / ノード障害 / 電源断) **または 通常例外 + rollback 失敗の二重故障**。`apply_fold` は返る前に state を消しているため、後者でも journal は無い |
| 残骸 | canonical 反映済み・fragment GC 済み・commit 無し・journal 無し (実測した plan では 3 path) |
| 正規復旧 CLI の応答 | **rc=0 / `noop`** (何も復旧せず、警告も出さない) |
| 次の land | rc=20 `main tracked/index/submodule dirt is forbidden` (fold を一言も指さない) |
| 実際の復旧 | `git checkout -- docs` → land 再投入。**適用済みの fold を捨てて作り直す**。捨てた事実は台帳に残らない |
| 最悪の分岐 | 運用者が手で commit すると、`verify_declared_fold_commit`・fold author・`AI-Agent:` trailer の どれも通らない commit が main に載る = [T-798] の言う帰属不能 |

### 選択肢の評価 (実測込み)

**(a) land 専用 journal を分けて finalize protocol を新設する**
- 検出力: 高い。land が「apply 済み・未 commit」「commit 済み・未 finalize」を自分で宣言できる。
  Q2 (a) が欲しい起源 field を同じ file に載せられる。
- コスト: **中〜大**。ただし「**journal を 2 本にしない**」が条件である (レンズ B)。
  transaction state と land journal が同時に生きると、失敗経路の組合せが増え、
  どちらが正かを決める規則が新たに要る。

**(b) state 削除を land の postcondition 後へ移し `validate_spool_tree` を active-aware にする**
- **窓は消えず移動する (実測)。** 新しい残余窓は「fold commit 済み・state 未削除」で、
  この形から land を再投入すると **rc=10 `stale-main`** で止まる。次 wave が新しい `tested_main` で
  来る場合は rc=27 になる。**どちらにせよ land は finalize しない。**
  閉じられるのは standalone CLI だけで、それは Q2 (b) が封鎖したい経路である。
  → **親の当初の「(b) は新しい recovery 機構を要らない」は撤回する** (レンズ B 所見 1-B、実測で確認)。
- ただし残余窓の**幅は桁違いに小さい**。約 2.83 秒 (check_docs 込み) → `unlink` + `fsync` だけ。
  さらに残るのが**journal そのもの**なので、現状の「痕跡が git dirt しかない」状態と違って
  何が起きたかを機械的に言える。
- 追加で要るものは 1 つに特定できた: **land の active-plan 分岐が
  「main が tested_tip の子である fold commit で、plan が全 target after」を受理して finalize する経路**。
  必要な比較は land が既に `_rollback_fold` で書いている「現 HEAD の親が expected_tip か」と同型である。
- 冪等性は実測で確認した。ローテーション発火・failures の再発挿入・supersede 追記・見送り追記を
  含む plan でも、再適用は書込み 0 の `resumed` で全 target が byte 単位で不変、二重挿入ゼロ。
  機序は変換の再実行ではなく content-addressed な収束である。
- テストの churn は**当初見積りより小さい**。apply 成功後の state 削除を pin しているのは
  **1 本だけ** (`test_interrupted_transaction_resumes_before_and_after_targets`)。
  land 側だけ挙動を分ける実装なら **0 本**。
  (親の当初「5 行」は dry-run のテストを誤って数え、レンズ B の「9 行」は rollback と dry-run の
  pin を含んでいた。全部開いて分類した結果が上である。)
- `check_docs.py` へ抑止 flag を足す必要は無い (レンズ B も同意)。ただし `_discover` の
  active-aware 化は、**受理する形を表で固定して fail-closed に書く**必要がある
  (全 target after かつ全 GC 削除済みだけ受理、部分状態・第三状態・schema 不正は従来どおり拒否)。
  「state があれば内容を見て問題なければ通す」形にすると規律 2 に反する受理集合の拡大になる。

**(c) 現状維持**
- 成果物影響: 窓に落ちた 1 回について、canonical 3 台帳・`FOLDED.md`・fragment GC が反映済みなのに
  commit と journal が無い状態が残り、certified 選択・レポートの proof chain を main history へ
  帰属できない。**正規の復旧 CLI が rc=0 で「やることは無い」と答える**ため、
  運用者が窓に落ちたと気づく機械的な手掛かりが無い。

### 親の推奨: **(a) と (b) を別案として扱わず、単一 journal の finalize protocol にする。**

実測から見ると (a) と (b) は排他ではなく、**同じものの言い換えになりつつある**。
(b) を安全にするには land に finalize 経路が要る (= (a) の finalize protocol)。
(a) を安全にするには journal を 2 本にしない (= 既存 transaction state を使う = (b) の器)。
したがって推奨は次の 1 案である。

> **既存の transaction state に phase (`applied` / `committed`) と起源 (Q2) を持たせ、
> 削除を land の postcondition 後へ移し、finalize は land だけが行う。**
> `validate_spool_tree` は phase から受理形を決め、受理表を fail-closed に固定する。

**当初の「無条件 (b)」からの変更点は、finalize 経路を必須の構成要素として明示したことである。**
文言上どれに当たるかを裁定していただきたい — 親の読みでは **(a) の趣旨を (b) の器で実装する**が、
選択肢の文言に忠実であることを優先するなら (a) を選ぶ形になる。

---

## Q2. [T-799] — fold state が land 起源・base・tested tip を束縛しない

### 実測した現状 (c) のリスク

| 項目 | 実測値 |
|---|---|
| state の field | 8 個。**HEAD・land 起源・base・tested tip は無し**。`transaction_id` にも入らない |
| 唯一効いている歯止め | `apply_fold` の before/after hash 照合 = **plan の target の bytes が同じか**だけ |
| **採番の入力が未束縛 (最重要、追加実測)** | `_max_task_number` は archive worklog・phase3 見送り台帳・worklog から最大 T を採るが、**archive は target ではないので state に現れない**。archive を変えてから resume させると、**古い採番を適用して重複 T 番号ができた** (`[T-052]` が worklog と archive の両方に存在。再計画なら `[T-053]`)。`WORKLOG_ROTATE_BYTES` (コード側) も同型の未束縛入力である |
| 下流で止まるか | `check_docs` の T 重複検査は **1 エントリ内**に閉じており archive を跨がない (静的確認、実 checker では未実測) |
| 誤った HEAD での standalone resume | canonical を変えない commit なら **rc=0 / `resumed` で成功**。ただしこの構成単体では**値は壊れていない** — 壊れるのは上の採番入力が変わったとき |
| resume と新規 apply の非対称 | resume は `_git_clean_preflight` を**通らない**。同じ dirty 条件で新規 apply は拒否、resume は通過 |
| land 側 | `locked_main == tested_tip` だけ。別 HEAD で計画された plan を resume して fold commit を作った (C2)。ただし**測った C2 自体は正常動作**であり、欠陥の実演ではない |
| wave 同一性 | `_verify_supervised_fragment_wave` は `refs/heads/dev-wave/dw-` 以外で no-op。`worktree-dev-wave-*` には束縛が無い |
| standalone resume の終端 | **commit を作らない。** 現行コードでは成功した瞬間の tree が [T-798] の crash 残骸と同一で、次の land は rc=20 |
| 排他 | **standalone は land lock を取らない** (静的確認)。land / standalone の同時実行は無排他 (競合は未実測) |

### 選択肢の評価 (実測込み)

**(a) state へ land 起源・base・tested tip・rollback ref を束縛し、mutation 前に HEAD と照合する**
- 検出力: 高い。「target bytes が同じか」から「この state を作った land と同じ位置にいるか」へ
  検査の意味が変わる。C2 の land 側 resume も B1 の standalone resume も止まる。
- **ただし HEAD の束縛だけでは重複 T 番号を止められない可能性がある。**
  実測した実害の直接原因は HEAD ではなく **plan 入力 closure の未束縛** である
  (archive worklog・phase3 見送り台帳・`WORKLOG_ROTATE_BYTES`)。
  HEAD を束縛すれば「archive を変える commit」も HEAD を動かすので**結果として**止まるが、
  同一 commit 内で archive を変えた場合や、HEAD を動かさない writer には効かない。
  **束縛すべきは「plan が読んだ入力の closure の hash」である。**
  選択肢 (a) の文言 (`land 起源・base・tested tip・rollback ref`) にこれを足すかどうかも裁定対象にしたい。
- **束縛先は申告値でなく観測値にする。** `tested_tip` は `_verify_heads` が実 wave HEAD と
  照合しているので無検証の文字列ではないが (レンズ B 5-A)、C2 は「今回の argv と実体が一致」を
  満たしたまま**別 wave 由来の state** を消費できた。要るのは
  「**state を作ったときの観測値と、今の実体が一致するか**」である。最低限:
  origin (`land` / `standalone`) / ff 前に lock 内で観測した `main_before` /
  plan source の実 `wave_ref` と実 `wave_head` / apply 開始時の main HEAD / `rollback_ref`。
  これらは **`transaction_id` にも含める** (JSON field だけだと後から書き換えられる)。
- コスト: **中**。要点は schema 互換である。
  **当初の「省略可能 field として読み、有る場合だけ照合」は撤回する** — それは
  「新 code が旧 state を読めるが束縛検査が黙って無効になる」= fail-open であり、
  旧 code が書いた state を消費する瞬間こそが本件の想定状況である (レンズ B 4-A、妥当)。
  厳格版 (version 2 必須) は fail-closed だが、旧 v1 の in-flight state を復旧不能にする。
  **この扱いは独立の裁定が要る** (下の Q2-b)。
- **注意 (親の当初の主張の縮小):** 「(a) で proof chain が durable になる」は**過大だった**。
  state は成功時に削除され、`FOLDED.md` の receipt は `wave` / `seq` / `content_sha256` /
  allocation しか持たない。**束縛値を残したいなら、durable 側 (fold commit message か
  `FOLDED.md` の receipt) に書く必要がある。** → Q3 で独立に問う。

**(b) land 由来 state の standalone apply を拒否し、land recovery のみに限定する**
- 検出力: 高い。standalone resume には**成功しても正しい終端が無い** (commit を作らないので
  必ず [T-798] の残骸を作り、次の land を rc=20 で止める)。
- **ただし「閉じても失うものが無い」は撤回する** (レンズ B 6-A、妥当)。
  land が起動不能・lock が取れない・land の import や checker が壊れている・
  process 死後に state の内容だけ確定検査したい、といった場合、standalone が唯一の入口になる。
  実際 Q1 (b) の残余窓 (commit 済み・state 残存) を今**閉じられるのは standalone だけ**である。
  → **封鎖するなら、同等の lock-aware な finalize / inspect command を同時に用意する**必要がある。
- 「land 由来か」の判定には (a) の起源 field が要る。field を足さずにやるなら
  「引数なし apply を一律に閉じる」しかない。
- `validate_spool_tree` の理由語 `引数なし CLI で resume が必要` は**偽になる**ので同時に直す。

**(c) 現状維持**
- 成果物影響: wave commit と無関係な main HEAD 上で T/D/F 採番と receipt を確定でき、
  台帳・レポート・proof chain の帰属が分離する。

### 親の推奨: **(a) を採り、束縛対象に「plan 入力 closure」を足す。(b) は代替 command とセットでのみ採る。**

1. **重複 T 番号が実測できたので、[T-799] の優先度は「帰属」ではなく「値」で評価すべきである。**
   これが本 wave で一番効いた発見であり、敵対レンズ A の指摘から出た。
2. **(b) 単独では proof chain も値も直らない。** 依頼の動機に効くのは (a) の束縛である。
3. **(a) の schema 互換は fail-open にしない。** 厳格側を既定とし、旧 v1 state の扱いを Q2-b で裁定する。
4. **(b) の封鎖は代替 command が出来るまで保留する。** 実測上、standalone は
   Q1 (b) の残余窓 (commit 済み・state 残存) を**今唯一閉じられる経路**でもある。

### Q2-b. 旧 v1 in-flight state をどう扱うか (新規、レンズ B 4-B 由来)

厳格 schema にすると、旧 code が残した v1 state を新 code が読めない。
これは「復旧が必要なまさにその瞬間」に当たる。選択肢:
(i) 拒否して手動 quarantine (fail-closed、最も単純) /
(ii) 実 wave ref・HEAD・現 main から plan を再計算し、fragment・target・transaction ID の
完全一致を確認できたときだけ v2 へ変換する /
(iii) 外部の durable journal が起源を証明できる場合だけ変換する。
**親の推奨は (i)。** 移行 code は「使われないことを期待する復旧 code」になり、
テストしづらく、失敗すると台帳を壊す。**v1 state は 1 land の寿命しか持たないので、
新旧が交差する窓は実運用上ほとんど無い。**

---

## Q3. 束縛値をどの durable artifact に残すか (新規)

依頼の動機は「certified 選択の proof chain を main の履歴へ帰属させる」ことである。
実測すると、**現状その情報を残す durable な場所が無い。**

- transaction state は成功時に削除される。
- `FOLDED.md` の receipt が持つのは `wave` / `seq` / `content_sha256` / allocation だけである。
- fold commit の message は固定文言 (`_FOLD_MESSAGE`) である。

したがって Q2 (a) を入れても、**実行時の受理集合は狭まるが、後から「この fold commit は
どの main 状態に対して採番されたか」を台帳から言えるようにはならない。**

選択肢 = (a) `FOLDED.md` の receipt へ base / tested tip / wave ref を足す /
(b) fold commit message へ構造化 trailer で書く / (c) 両方 / (d) 何もしない (実行時検査だけで足りるとする)。
**親の推奨は (a)。** receipt は既に fold だけが追記する耐久記録で、機械可読の JSON 行であり、
`_receipt_records` という consumer が既にある。commit message は provenance checker と
`verify_declared_fold_commit` の固定 message 契約に触れるので、より広い面へ波及する。

## Q4. Q1 / Q2 を 1 つの変更として扱うか

- Q1 の器 (state の寿命延長) と Q2 の field は**同じ file** に載る。別々に land すると
  同じ schema を 2 回変え、互換判断を 2 回やる。
- **Q1 を先に出す順序は拒否すべきである** (レンズ B 8、親も同意)。state の寿命だけ先に延び、
  誤った HEAD での resume の窓を先に広げる。

**親の推奨: 1 つの変更として扱う。** 分割するなら Q2 を先に限る。

## Q5. 付随所見を起票するか

`_load_rotate_limit` (`tools/spool_fold.py`) は `tools/check_docs.py` を
**land process 内で `exec_module`** する。`except Exception` で囲っているが `SystemExit` は
`BaseException` なので抜ける。本 wave の probe で、`check_docs.py` が module 直下に
`raise SystemExit(0)` を持つと **land process が出力ゼロ・rc=0 で静かに消えた**ことを実測した。
実物は `if __name__ == "__main__":` で囲っているので現状は発火しない。

**親の推奨: P3 で起票する** (本 wave の fragment で起票済み)。
「fail-closed に囲ったつもりの `except Exception` が `SystemExit` を取り逃がし、
しかも rc=0 = 成功に見える」形は、規律 2 が一番嫌う形である。同型が他にあるかは未測定。

## Q6. 裁定の前に追加測定を要求するか (新規、両レンズ由来)

本 wave が**測っていない**ものを正直に列挙する。どれかが裁定を左右するなら、
実装 wave の前に測定 wave を 1 本挟むのが安全である。

1. commit 成功後・postcondition 中の crash (post-commit 相の残骸と復旧)
2. [T-766] の rollback 失敗で残る各形 (ref CAS / read-tree / path 復元) からの resume
3. `WORKLOG_ROTATE_BYTES` や phase3 を変えた場合の rotation 差 (archive は実測済み)
4. land / standalone の同時実行競合 (standalone は land lock を取らない)
5. commit と postcondition を含む end-to-end の窓幅
6. 実 checker が §D の重複 T を止めるか (現状は静的確認のみ)
7. supervised branch での C2 相当の受理差

**親の推奨: (1) と (6) だけを実装 wave の段 1 前提実測に含め、残りは実装 wave の中で
テストとして書く。** 独立の測定 wave は要らないと考える — (1) は選択肢 (b) の可否に直結するので
先に要るが、(2)〜(5)(7) は「実装した gate が効くか」の検査であり、実装と同じ wave で
テストとして書くほうが安い。ここは判断が割れうるので裁定に含めた。

## 参考 — 近傍の未着手項

[T-800] (`_rollback_fold` の state 型検査が復元と同じ `try` の末尾にある) と
[T-801] (rollback lifecycle の 3 細部) は**同じ関数群**を触る。Q1/Q2 を実装する wave が
同じ file を開くので、まとめる方が安いかもしれない。ただし本 wave はこの 2 件を実測していないので、
束ねる判断の材料は持っていない。

レンズ B は長期案として「temporary index/tree で folded tree を構築し、gate を通した commit object と
phase journal を作り、ref を CAS 更新する commit-first 方式」を挙げている
(未 commit canonical の窓を大きく縮められるが、別設計の規模)。
**本 wave は測っていないので、選択肢として提示するに留める。**
