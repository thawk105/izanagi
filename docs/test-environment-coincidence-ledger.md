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
| D | 確定的 | 実時計・実並行・OS 割当が関与しないか、比較関係が操作によって強制されている |

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

各 site には、環境の偶然への依存が戻ったら落ちる検査を残した。

**検査する性質は 1 つも捨てていない。既存の待ち上限の数値は 1 つも変えていない。**
ただし文字どおりの意味で「assert を 1 行も消していない」わけではない。
fd 件数の一致 assert、0.2 秒の負の待ち、0.1 秒の負の待ちは削除し、
同じ性質をより強く主張する assert へ置き換えた。

---

## 直さないと判定したものと、その理由

**243 は候補の上限値であって、全部が欠陥ではない。** 処置しない判断の理由を型ごとに記す。

### 候補一覧の所在と、分類がどこまで進んだか

行単位の候補一覧は `output/insights/2026-08-26_t1848-env-coincidence-inventory.json` にある。
schema は `izanagi-env-coincidence-inventory/v1`。各行は file、行番号、種別、上限値、述語 (P1 / P2)、
本 wave の対象か次 wave 送りか、送りなら所有 wave、暫定 class を持つ。

**分類はまだ全件には届いていない。** 内訳は次のとおりである。

| 区分 | 件数 |
|---|---:|
| 候補 (P2) 全体 | 260 |
| うち本 wave の対象 | 206 |
| うち稼働 wave 所有で次 wave 送り | 54 |
| 暫定 class が付いた行 | 159 |
| class が付いていない行 | 101 |

対象内 206 行の暫定 class は H 145、C 2、T 2、D 1、未分類 56 である。

**暫定 class は段 2 プランの群分類を転記したものであり、確定ではない。**
敵対レビューが H 群から 5 件を抽出監査したところ、**3 件が非 H だった**。
つまり H の分類手続きには系統的な偏りがある。確認できた誤分類は次の 4 件である。

- `test_check_ai_provenance.py:6359` — `wait(1)` の戻り値が直接の期待値なので T
- `test_run_tests_preflight.py:2049` — 同型
- `test_dev_waves_receipt.py:220` — 2 秒が partial file を公開する時刻を決めるので C / T
- `test_env_contract_activation.py:2451` — `release.wait(20)` は lock を保持する因果 fixture なので C

したがって「H だから直さない」という判断は、**個々の site については追試を要する**。
全件の再監査 (判定基準は「値を変えると期待結果が変わるか」に統一する) は次 wave の作業である。
本台帳が確定的に主張できるのは、次の 2 つだけである。

1. 候補の母集合と、その走査述語 (再現可能)。
2. **実負荷の artifact が無い以上、どの上限値も本 wave では変えられない**という政策判断 (D249)。

### H — 待ち上限の値を本 wave では 1 つも変えない

理由は `docs/decisions.md` の D249 である。D249 は負荷依存フレークに対して
「テスト側の時間予算を広げる変更を先に入れない。まず計装を入れ、実負荷で 1 件でも artifact を
得てから、その値を根拠に予算を裁定する」と定める。

本 wave は H に該当する候補について**実負荷の artifact を 1 件も持っていない**。
したがって予算変更は D249 が却下した「根拠なき拡大」に当たる。

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
