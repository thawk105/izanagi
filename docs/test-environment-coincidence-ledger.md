# 受入 suite の「環境の偶然を assert する検査」台帳

守りたい性質ではなく、その回の実行環境がたまたまそうだったことを assert している検査の分類台帳。
発端と機序は `docs/failures.md` の F641 を正本とする。本文書は分類と処置の正本である。

この台帳は網羅を主張しない。**走査述語が拾える範囲**の候補を分類したものであり、
述語の外にある型は「述語の限界」節に明示する。

---

## 走査述語と母集合

対象は `orchestrator/tests/*.py` (298 file)。数値は base `b0c1a8bd` 時点。
grep ではなく AST で数える。同一行に 2 つの一致があれば 2 件と数える。

**述語 P1 (厳密):** call の `.join(<数値>)` / `.wait(<数値>)` の第 1 位置引数、または
キーワード `timeout=<数値>`。

**述語 P2 (拡張):** P1 に加えてキーワード `deadline_s=<数値>` と
`termination_grace_s=<数値>`。この 2 つは子 process の絶対締切であり、F641 が挙げた 4 型の
1 つに直接当たるが、P1 では拾えない。

数え方の細目: 真偽値リテラル (`True` / `False`) は数値として数えない。
Python では真偽値が整数型に含まれるため、これを数えると件数が水増しされる。

| 述語 | 件数 | file 数 |
|---|---:|---:|
| P1 | 243 | 66 |
| P2 | 260 | 66 |
| P2 のうち稼働 wave が編集中 | 54 | 13 |
| P2 のうち本 wave の対象 | 206 | 53 |

F641 が記録した 244 / 68 とは一致しない。F641 の走査述語は記録されていないので、
どちらが正しいかは比較できない。**本台帳の数値は上の述語でのみ再現できる。**

**上限値の分布 (P2):**
`0.02:1 0.04:1 0.05:17 0.1:1 0.2:1 1:15 2:20 3:6 5:58 10:56 12:1 15:6 20:18 30:20 45:1 60:10 120:18 180:4 240:1 300:5`

上限が 2 以下のものは 56 件。
elapsed の上限を assert する箇所は別途 12 件 / 9 file ある (P1 / P2 のどちらにも含まれない)。

**`time.sleep` について:** source text 上の `time.sleep(` の綴りは 108 だが、
これは実行される sleep の数ではない。AST 上の実 call で数値直値を渡すものは 46 件、
うち 0.05 秒以下が 38 件である。差分には子 process へ渡す source string が含まれる。

### 述語の限界 (拾えないもの)

1. **記号定数の上限。** `SUBPROCESS_TIMEOUT = 120`、`GIT_TIMEOUT_SECONDS = 180`、
   `_SERVE_CHILD_CEILING_S = 180` は実際の上限だが、call の AST は
   `timeout=SUBPROCESS_TIMEOUT` のままなので数値述語では拾えない。
   **定数の値を変えても述語は変化を検出しない。**
2. **hook・callback の実行順序。** 相対順序の `.index()` 比較や list 等値比較。
3. **識別子の再利用。** OS が割り当てた fd 番号・inode と literal の比較。
4. **周囲状態。** `/proc/self/fd` の件数、テストが所有しない directory の内容。
5. **別名束縛。** `LIMIT = 1; thread.join(LIMIT)`、`**{"timeout": 1}`、
   `getattr(thread, "join")(1)` はいずれも述語の外である。
6. **テストが自分で持つ実時計の締切。** `deadline = time.monotonic() + N` に続く poll ループは
   P1 / P2 のどちらでも構造的に見えない。`5d0c898c4` 時点で **29 site** ある。
   本台帳が引用している `test_dev_wave_wait.py` の `deadline = time.monotonic() + 30` が
   まさにこの形で、そこでは「30 秒待って waiter が終わらないこと」を assert している。
   分類でいえば **C (因果の代理観測)** の典型だが、候補一覧には 1 行も入っていない。
   **母集合は同族の site を少なくとも 29 件取りこぼしている。**

F641 が挙げた 4 型のうち、P1 が確実に拾うのは待ち上限の型だけである。

---

## 分類

判定は call の種別ではなく、**その数値・順序・識別子を変えたときに期待結果が変わるか**で行う。

| class | 意味 | 判定手続き |
|---|---|---|
| H | hang guard | 上限は診断と hang 回収のためだけにあり、期待結果は上限値を参照しない。完了しない実装を注入すると上限で赤になる |
| T | 時間が主題 | 数値が production の締切・猶予・poll へ到達し、その値が期待結果を決める |
| C | 因果の代理観測 | 「N 秒待って終わらないこと」で排他・先行関係を代理観測している。守るべき happens-before が別にある |
| O | 順序 | 保証されていない実行順序・出力順序に一致を要求している |
| I | 識別子 | OS や runtime が再利用する整数・名前 (fd 番号、pid、inode、一時 path) の一致を要求している |
| A | 周囲状態 | テストが所有しない process や host 全体の可変状態を一致・閾値比較している |
| F | 決定的な床 | 待つ対象が production 側の実 sleep / poll 間隔で下から押さえられており、上限との余裕がその床で決まっている。負荷は引き金にすぎない。H と誤分類しやすい |
| D | 確定的 | 実時計・実並行・OS 割当が関与しないか、比較関係が操作によって強制されている |

### 8 クラスは、判定手続きに次を必須化して初めて排他になる

[T-1901] の全数分類で、**現行の手続きでは同じ行が複数のクラスに一致する**ことが分かった。
「床あり → F」「wait の戻り値を assert → T」のような手続きだけで判定すると排他にならない。
排他にするには次を必須化する。

- **F には materiality。** 床が在るだけでは足りない。**上限との余裕がその床で決まっている**
  ことまで示す。床と上限の比を必ず計算する。
- **T には production への値伝播。** その数値が production の締切・猶予・poll へ**到達**
  しなければ T ではない。test-local な `threading.Event` の上限や、mock の `side_effect` 内の
  同期上限は production へ到達しない。
- **H には別 assertion の名指し。** 「上限は診断と hang 回収のためだけ」と言うなら、
  検査対象の性質は別の場所で assert されている。その `file:line` を挙げられなければ H ではない。
- **D は実際に待っていない場合。** 実時計・実 process・実 thread が関与せず、mock された
  呼び出しの引数一致を見ているだけなら D。**実 thread や実 process があるなら D ではない。**

`assert ev.wait(N)` のように**戻り値が assert されていることは、要反証の合図であって
自動的な非 H 条件ではない。** 上限が failure recovery だけを bound する fail-fast guard で、
性質が別の assertion にあることは実在する
(`orchestrator/tests/test_codex_worker_launch.py:5918-5932` はコメントに明記がある)。
逆に**戻り値を捨てていても非 H のことがある。** timeout 後に writer が残りを公開する、
lock が解放される、thread が先へ進む、といった副作用が期待結果を変えるなら T か C である。

### F の判定を H より先に置く

**上限の妥当性を論じる前に、待つ対象に決定的な床が無いかを確かめる。**
床がある site では上限は問題ではないので、「実負荷の artifact が無いから上限を変えない」と
裁定しても何も直らない。分類し直しが要る。

判定は次の 3 段で行う。**判定を担うのは段 1 と段 3 であり、段 2 は並べ替えにすぎない。**

1. その site が呼ぶ production 側の関数に、sleep / clock / poll 間隔の注入 seam があるか。
2. (安価だが不完全な優先順位付け) 同じ file 内で、多数派と違う呼び方をしている site を grep で出す。
   **file 内の全 site が seam を素通ししていれば多数派が存在せず 0 件を返す。**
   0 件を「F は無い」の根拠にしてはいけない。
3. seam があるのに、この site はそれを渡しているか。渡していなければ F の候補である。
4. **その床は上限との余裕を決めているか。** 床と上限の比を計算する。決めていなければ F ではない。

**段 1〜3 だけでは F を過剰に判定する。** D1055 の 2 段手続きは class 定義にある
materiality 条項を落としているため、定義に入らない site でも発火する。[T-1901] の全数分類で
実測した ([T-1901] の節を見よ)。段 4 を落としてはならない。

**F の処置は 3 段に分ける。**

- **呼び手 (テスト) に既存の seam を渡させて床を消す。** これはテスト側だけの変更である。
  seam が無い場合だけ production の変更を検討する。**後者は production 挙動を変える判断なので、
  裁定の重さが違う。**
- **watchdog の上限は残す。** 用途を「hang 回収であって合否の latency 予算ではない」と明記する。
  床が消えると上限と実所要の比が桁で開くので、上限を残しても負荷依存にはならない。
  F の処置は「上限を消す」ではなく **「上限を判定から降ろす」** である。
- **降格が回帰しないことを守る control を足す。** 注入した sleeper の呼出しと偽 clock の進みを
  観測する。**この control で実時間を測ってはいけない。** 測れば、消したはずの負荷依存が戻る。

最後の段を落とすと、`sleep=` を外して床が戻っても watchdog の内側なので
**性質の assertion は全部通ってしまう。** 修理が黙って蒸発する。

このクラスと手続きは、並行 wave `dev-wave-flaky-holds-20260826` の実測に基づく。
同 wave は「並列負荷で落ちるフレーク」に見えた 2 件を計装し、`-n 32` / `-n 48` で
10.015 / 10.014 / 10.015 秒 (ばらつき 1 ミリ秒) を観測した。正体は production 側の
`DEFAULT_POLL_INTERVAL_S = 5.0` の実 sleep 2 回による決定的な床で、`join(10)` の余裕は
15 ミリ秒だった。production は 1 byte も変えず、テスト側が既に存在した seam を
渡していなかっただけである。同 wave は降格を守る control を最初は忘れ、
焦点再レビューの指摘で変異 3 件 (`sleep=` 削除 / `clock=` 削除 / latch 側の `clock=` 削除) を
足して守った。

一次資料は同 wave の branch `worktree-dev-wave-flaky-holds-20260826` 上の
`output/insights/2026-08-26_flaky-holds-removal/` と、job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/` にある。
**同 wave は本台帳の記録時点で land していないため、新規の F / D 番号と worklog entry 番号は
確定していない。番号ではなく path で引くこと。** land 後に番号へ差し替えるのが安全である。
既存番号の F480 (族分類の訂正の追記先) と F24 (待ち手の偽完了) だけは安定して引ける。

`assert not event.wait(0.1)` は T ではなく C である。遅い環境では赤にならず、
むしろ排他の回帰を見逃す方向へ働くからである。
`dup2` 直後の fd 一致比較は I ではなく D である。関係が操作で強制されているからである。

---

## 本 wave で是正した site

いずれも**既存の待ち上限の値を変えずに環境依存を除去する書き換え**である。

| class | file | 是正 |
|---|---|---|
| I | `orchestrator/tests/test_sort_swo_oracle.py` | parent 側で target fd を予約し、`dup2` と予約によって番号差を強制する |
| I | `orchestrator/tests/test_wave_land_window.py` | 旧 lease fd を開いたまま reacquire し、旧 inode を live に保って再利用を不能にする |
| A | `orchestrator/tests/test_buildcache_v2.py` | clean な子 process 内で測り、開始前後の全 fd identity 差分を比較する |
| C | `orchestrator/tests/test_codex_worker_launch.py` | lock-attempt event と非 blocking lock probe、critical hook の前後関係で排他を証明する |
| C | `orchestrator/tests/test_trial_registry.py` | writer の lock-attempt hook と critical section の因果 trace を同期 event で検査する |
| C | `orchestrator/tests/test_mutation_harness.py` | signal 前後の段階遷移を実時間でなく因果 event で検査する |
| T | `orchestrator/tests/test_codex_worker_launch.py` | 子 process の pid 登録を 2 秒の絶対期限で待つのをやめ、launcher 終了後に判定する。証拠は終了後も残る |

各 site には、環境の偶然への依存が戻ったら落ちる検査を残した。

最後の 1 件は受入全走で実際に落ちたものである。2 回連続で同じ node だけが落ち (いずれも 17,390 passed / 1 failed)、単独走は緑だった。台帳の F57 に同じ node・同じ assertion 逐語で非帰属として 2 度記録されている型で、**本族の実例が受入で発火した**。
hold で隠す道もあったが、`orchestrator/tests/flaky_test_holds.py` は稼働 wave の所有であり、同 wave は受入済みの tip で凍結していた。そこへ書けば相手に受入の再走を強いる。
対象 file は本 wave の所有なので、隠さずに直した。

**検査する性質は 1 つも捨てていない。既存の待ち上限の数値は 1 つも変えていない。**
ただし文字どおりの意味で「assert を 1 行も消していない」わけではない。
fd 件数の一致 assert、0.2 秒の負の待ち、0.1 秒の負の待ちは削除し、
同じ性質をより強く主張する assert へ置き換えた。

---

## 直さないと判定したものと、その理由

**243 は候補の上限値であって、全部が欠陥ではない。** 処置しない判断の理由を型ごとに記す。

### 候補一覧の所在 — v1 と v2

行単位の候補一覧は 2 つある。

- `output/insights/2026-08-26_t1848-env-coincidence-inventory.json`
  (schema `izanagi-env-coincidence-inventory/v1`、base `b0c1a8bd`、260 行)。**歴史記録として残す。**
- `output/insights/2026-08-27_t1901-env-coincidence-classification.json`
  (schema `izanagi-env-coincidence-classification/v2`、observed `5d0c898c4`、250 行)。**現行の正本。**

**走査述語は commit 済みのコードになった。** `tools/scan_env_coincidence.py` が P1 / P2 を AST で
実装する。**行番号規則は `ast.Call.lineno` (call の開始行) である。** 引数値の `lineno` ではない。
v1 の base `b0c1a8bd` で走らせると `Call.lineno` 規則は **260/260 を完全再現**し、引数値 `lineno`
規則は **163/260** しか一致しない。本台帳の数値を生んだ規則は、散文の解釈ではなくこの再現性で
同定できる。

**候補一覧は commit を跨ぐと陳腐化する。** v1 の `(file, line)` anchor は記録の翌日に 100/260 が
外れていた。[T-1901] の作業中にも local main が 40 commit 進み、8 anchor が移動した。
v2 は各行を観測対象の commit と source blob OID で束縛する。**これは将来の expected pin ではない。**
再走査は走査器を当て直して行う。

### 分類は全数に届いた

`5d0c898c4` 時点の母集合は **250 行 / 66 file** (直下 Python file 303、P1 233、P2 追加 17)。
全 250 行を分類した。

| class | 件数 |
|---|---:|
| H | 206 |
| D | 16 |
| C | 14 |
| T | 14 |
| F | 0 |
| 判定不能 | 0 |

前 wave の暫定 class があった 155 行のうち **17 行 (11.0%) を覆した**。暫定 H は 153 行あり、
**うち 16 行 (10.5%) が非 H へ動いた** (H→C 8、H→T 5、H→D 3)。未分類だった 95 行は
H 69、D 11、T 9、C 6 に分かれた。

**前 wave の抽出監査は H 群 5 件中 3 件 (60%) が非 H だったが、全数では 10.5% だった。**
系統的な偏りは実在するが、規模は標本からの外挿の 6 分の 1 である。
**5 件の標本から族全体の誤分類率を外挿してはならない。**

稼働 wave が所有する 5 行は `observation_only` とした。分類はしたが source は今後変わりうる。
**[T-1902] はこの 5 行について開いたままである。**

### F は不在だった

**候補 10 行を検分した結果、`5d0c898c4` 時点の母集合に F は 1 件も無い。**
「見つからなかった」ではなく「調べた上で不在」である。

10 行はいずれも production 側の実 sleep / poll 床を持つ。しかし F の class 定義は
**「上限との余裕がその床で決まっている」**ことを要求する。床と上限の比は最小でも 100 倍だった。

| site | 上限 | 床 | 比 |
|---|---:|---:|---:|
| `_dev_waves_serve_child.py:122` | 120 | 0.01 | 12000x |
| `test_check_ai_provenance.py:6359` | 1 | 0.005 | 200x |
| `test_codex_worker_launch.py:1132` | 10 | 0.01 | 1000x |
| `test_codex_worker_launch.py:1159` | 10 | 0.01 | 1000x |
| `test_codex_worker_launch.py:1214` | 10 | 0.01 | 1000x |
| `test_codex_worker_launch.py:2202` | 30 | 0.01 | 3000x |
| `test_codex_worker_launch.py:2261` | 30 | 0.01 | 3000x |
| `test_real_repo_serialization.py:1728` | 5 | 0.05 | 100x |
| `test_run_tests_preflight.py:2049` | 1 | 0.005 | 200x |
| `test_t126_qualification_driver.py:850` | 10 | 0.05 x 2 | 100x |

D1055 が根拠にした実例は床 10.015 秒に対し上限 10 秒で、**比 1.0015、余裕 15 ミリ秒**だった。
上表とは桁が違う。

一次分類は D1055 の 2 段手続きを正確に実行した結果この 10 行を F とし、独立した 3 系統の検査
(床と上限の比の実測、逐行レビュー、class を隠した盲検再分類) がいずれも過剰発火と判定した。
**手続きへ materiality を足す必要がある。** 完全な機械判定は現状の文言ではできない。
「余裕を決める」の数値境界が未定義だからである。次までは機械化できる。

```text
B = site の上限
L = 期待結果へ至る全 path で必ず通る production sleep の総下限
candidate = L > 0 かつ seam で L が無効化されていない
F_R = candidate かつ B / L <= R
```

条件付き loop は、最低反復回数を静的に証明できない限り `L` に入れない。`R` (または許容 jitter
`J` を使う `B - L <= J`) は裁定された定数でなければならない。**D1055 の実例 1 件では `R` も `J` も
決められない。** 現状は candidate と比率までを機械で出し、materiality は未確定として止めるのが
正しい。

### 前 wave が記録した「確認できた誤分類 4 件」のうち 2 件は、訂正自体が誤りだった

| site | 前 wave の記録 | 全数分類の判定 | 理由 |
|---|---|---|---|
| `test_check_ai_provenance.py:6359` | T | **H** | `wait(1)` は mock の `side_effect` 内の test-local `Event` で、`1` は production へ到達しない。T の定義を満たさない。性質は `:6406` の cap OOM 検査が担う |
| `test_run_tests_preflight.py:2049` | T | **H** | 同型。性質は `:2088` が担う |
| `test_dev_waves_receipt.py:220` | C / T | **C** | timeout 後に writer が残りを公開するので、値が公開時刻を決める |
| `test_env_contract_activation.py:2451` | C | **C** | lock を保持する因果 fixture |

前 wave の敵対レビューは H 偏りを直そうとして**逆方向へ振れていた**。
偏りの是正は、H を疑うことと同じ強さで**非 H の主張も疑う**ことでしか達成できない。

### H — 待ち上限の値を本 wave では 1 つも変えない

理由は `docs/decisions.md` の D249 である。D249 は負荷依存フレークに対して
「テスト側の時間予算を広げる変更を先に入れない。まず計装を入れ、実負荷で 1 件でも artifact を
得てから、その値を根拠に予算を裁定する」と定める。

本 wave は H に該当する候補について**実負荷の artifact を 1 件も持っていない**。
したがって予算変更は D249 が却下した「根拠なき拡大」に当たる。

**ただしこの裁定は、その site が H であることを前提にしている。**
決定的な床を持つ site (クラス F) では上限そのものが問題ではないので、
「上限を変えない」と裁定しても何も直らない。**H と裁定する前に F の判定を通すこと。**
手続きは「分類」節の「F の判定を H より先に置く」に従う。

H の上限拡大が受理集合を実際に広げることは、具体的な回帰で確認した。

- 20 秒の join を 60 秒へ広げると、worker が 30 秒かかる性能回帰が通る。
- 1 秒の wait を 10 秒へ広げると、sampler の観測が 5 秒後になる回帰が通る。
- 60 秒の subprocess watchdog を 120 秒へ広げると、probe が 90 秒停止してから
  同じ出力を返す回帰が通る。

F641 が行った `join(10)` から `join(60)` への拡大も、値の根拠は静穏な単独走 13.94 秒の
4 倍超という外挿であり、実負荷の分布ではない。**D249 適合例として引用してはならない。**

### T — 値が主題のものは、そもそも環境の偶然ではない

上限値が仕様そのものである検査は、環境が変わっても意味が変わらない。
論理時計へ寄せる余地はあるが、**実 OS 上の応答上限を置換すると検出力が落ちる**。
たとえば「遅れて正しい error を返す」回帰は、実 integration の狭い上限だけが捕まえる。
論理検査は追加にとどめ、実上限を置換・削除しない設計が確定するまで着手しない。

### D — 比較関係が操作で強制されているもの

`dup2` 直後の fd 一致、同時に存在する 2 file の inode 不一致、単一 thread での逐次呼出し、
mock が渡された値で例外を送出する検査などは、環境が変わっても結果が変わらない。是正不要である。

### 稼働 wave と重なったため次 wave へ送る

次の file は、本 wave の稼働中に別の wave が編集していた。編集面が重なるため対象から外した。
稼働 wave の land 後に再走査して同じ分類手続きへ戻す。

| 所有 wave | file |
|---|---|
| dev-wave-b10-overthrottle-grid | `test_backoff_extended_sweep.py`, `test_backoff_extended_sweep_report.py`, `test_backoff_overthrottle.py`, `test_p3_build_authority_cli.py`, `test_s1_known_axes_freeze.py`, `conftest.py`, `test_s1_9pair_figure_provenance.py` |
| dev-wave-b10-backoff-shape-orthogonal | `test_b10_backoff_shape_sweep.py`, `test_ccbench_spawn_sites.py`, `test_campaign.py`, `test_hooks.py`, `test_official_perf_closure.py` |
| dev-wave-b4-prereg-enactment | `test_p3_b4_closed_critic.py`, `test_p3_exploration_namespace.py`, `test_p3_s4_loop.py`, `test_p3_s4_loop_sort.py`, `test_p3_s4_loop_trigger_gating.py` |
| dev-wave-flaky-holds-20260826 | `flaky_test_holds.py`, `output_snapshot_ignores.py`, `test_flaky_test_holds_contract.py`, `test_pegasus_dispatch_compute.py`, `test_real_repo_serialization.py`, `test_s8b_floor_campaign.py`, `test_s8b_oracle_driver.py` |
| dev-wave-t1629-ratification-broker | `test_artifact_admission.py`, `test_ed25519_verify.py`, `test_enforcement_source_ratification_receipt.py`, `test_ratification_broker.py`, `test_t671_source_binding.py` |
| dev-wave-t1732-condition18-two-points | `test_check_docs.py` |
| dev-wave-t1889-worktree-registration-race | `test_dev_wave_land.py`, `test_t810_coordinator.py` |

---

## 是正の順序について

本 wave は**確実性順**で是正した。機序が確定している I / A / C を先に処置し、
確率的にしか現れない H は計装なしには順位づけできないと判定した。

「実測フレーク率への寄与が大きい順」を確定するには、site ごとの発火率の推定が要る。
既知の全体率 15%/走を出発点に必要な走行数を見積もると次のようになる。

- 全体率 15% の事象を 95% の確率で 1 回でも観測する: 最低 19 走。
- 候補 9 site が均等かつ独立と仮定すると各 site は約 1.79%/走。
  指定した 1 site を 95% の確率で 1 回観測するのに 166 走。
  9 site すべてを全体 95% で観測するのに約 287 走。
- 287 走でも各 site の期待観測は約 5 件で、順位差の比較には足りない。

これは絶対規律 4 (実験スケールを無造作に大きくしない) に反する規模である。
必要本数は、各 site の発火率と判別したい最小差を先に定めない限り決まらない。
**したがって寄与順の確定は、本台帳の射程外である。**

上限値の小ささは落ちやすさと同じではない。待つ対象の仕事量が小さければ、
小さい上限でも余裕は大きい。実際、cleanup 経路にしか現れない 2 秒の待ちより、
常時走る 45 秒・60 秒の elapsed 上限のほうが発火面は広い。

---

## 実測

飽和条件 (計算ノード、全コア並列、17,391 件) での全走を 3 本取った。

| 走 | 結果 | 所要 |
|---|---|---|
| 1 (fresh worktree の初回) | 3 failed | 343.42 秒 |
| 2 | 全緑 | 383.85 秒 |
| 3 | 全緑 | 427.76 秒 |

走 1 で落ちた 3 件はいずれも `assert "runs" in ignored_prefixes` で、
`git ls-files -o -i --directory -- output/` が**中身のある** ignore 対象 directory しか
返さないことに起因する。fresh worktree では `output/runs/` が空なので prefix に現れない。
走 1 自身がそこへ中身を作ったため、走 2 以降は緑になった。
**「その checkout にたまたま `output/runs/` の中身が在ること」への依存**であり、本族の実例である。
該当 file は稼働 wave が是正中のため、本 wave の対象外とした。

負荷起因のフレークは 3 走とも 0 件だった。これは既知の 15%/走と矛盾しない
(3 走すべて 0 件になる確率は約 61%)。**3 走の緑から率が下がったとは言えない。**

所要は 343 秒から 428 秒へ単調に伸びた。原因は未特定である。

### 変異 matrix

是正が本物かを、production 側へ変異を注入して確かめた。baseline PASSED、
**3/3 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0**。期待 node は完全集合で一致した。

| id | 注入した回帰 | 捕まえた検査 |
|---|---|---|
| M01 | attempt registry の共有ロックを取り除く | `test_trial_registry.py::test_formal_acceptance_shared_lock_blocks_compat_writer_through_receipt` |
| M02 | manifest ロックを排他から共有へ落とす | `test_codex_worker_launch.py::test_manifest_lock_covers_load_replace_critical_section` |
| M03 | fd の close を最初の失敗で中断する | `test_buildcache_v2.py::test_close_fds_best_effort_closes_all_and_reraises_first_error`, `::test_copied_binary_close_error_does_not_leak_later_fds` |

**erratum:** M02 は初回 probe で SURVIVED だった。等価変異ではなく照準の誤りで、
テストが撃っているのは manifest ロックなのに receipt ロックを変異させていた。
実効 gate へ再照準して本走した。初回結果は本欄に残す。

なお、42 走すべての緑を要求したときの到達確率は「0.1% 未満」ではなく約 0.1% である
(5/33 で 0.1007%、15% で 0.108%)。これは独立同分布を仮定した推定であって観測値ではない。

---

## 却下した設計 — repo 全体の静的 gate

新しい検査が小さい絶対上限・保証されない順序・識別子の一致を持ち込んだら落ちる、
repo 全体の静的 gate を検討したが採らなかった。理由は次のとおりである。

- **登録 gate にしかならない。** 候補集合を台帳へ固定して一致を要求する設計では、
  source と台帳を同じ変更で更新すれば通る。分類が正しいかを gate 自身は判断できない。
- **迂回が容易である。** 「述語の限界」に挙げた別名束縛はいずれも述語の外に出る。
  既存の記号定数を 120 から 300 へ変えても call の AST は変わらない。
- **信頼の根が循環する。** 同じ走査器が候補を作り、同じ実装が台帳と分類を作り、
  同じ走査器の正負例で自分を検査する構造になる。根拠欄は自己申告になる。
- **除外規則と両立しない。** 全 file を走査すれば稼働 wave の未登録候補で baseline が赤になり、
  除外 file を走査から外せば land 後も盲点が残る。

代わりに、是正した各 site へ再発検知を置く方式を採った。
gate の設計は今後の裁定に委ねる。
