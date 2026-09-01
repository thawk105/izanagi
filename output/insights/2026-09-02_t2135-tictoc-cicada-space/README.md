# tictoc と cicada の genome 空間を SPACES へ登録する (T-2135、2026-09-02)

- **wave 種別:** `/dev-wave [T-2135] tictoc / cicada の genome 空間を SPACES へ登録する`。
- **基準 commit:** `c6a94ec998bba8c20c302105f28af3850f8134a6` (着手直前の local main)。
  branch `worktree-dev-wave-t2135-tictoc-cicada-space`。
- **実装 commit:** `727ca869f` (production 1 file + test 1 file、+208/-5)。
- **成果物:** 本 insight + worklog / decisions / failures fragment + 実装。
- **測定:** 本 wave は 1 件も行っていない。

---

## 1. 何を登録したか

| protocol | 軸 (すべて `[0,1]`) | 制約 | 生 | 有効 |
|---|---|---|---|---|
| tictoc | `BACK_OFF`, `NO_WAIT_LOCKING_IN_VALIDATION`, `NO_WAIT_OF_TICTOC`, `PREEMPTIVE_ABORTS`, `TIMESTAMP_HISTORY` | 両 no-wait の同時 1 を禁止 | 32 | 24 |
| cicada | `BACK_OFF`, `INLINE_VERSION_OPT`, `INLINE_VERSION_PROMOTION`, `REUSE_VERSION`, `WRITE_LATEST_ONLY` | `PROMOTION ⟹ OPT` | 32 | 24 |

`SPACES` は silo / mocc / tictoc / cicada の 4 protocol になった。
silo (8) と mocc (8) は不変である。

**導出できずに落とした軸は 0 本。** 依頼は「導出できない軸は無理に登録せず、できない理由を書いて
残す」だったが、段 2・段 3・段 6 のいずれの子も判定不能な軸を報告しなかった。
cicada の 5 flag は `SINGLE_EXEC` の除外を含めてすべて分類できた。

## 2. 除外した軸と理由

| protocol | flag | 理由 |
|---|---|---|
| tictoc | `PARTITION_TABLE` | 死にフラグ。`cc/tictoc/` 全体 (`include/` 部分木と 4 workload source を含む)・共通 header・`common/` の全件検索で live site 0 件。cicada / silo / oze では起動時 option 表示に現れるが、tictoc にはそれすら無い |
| tictoc | `SLEEP_READ_PHASE` | 計測撹乱ノブ。read の途中へ sleep を挿入する (規律 4) |
| cicada | `SINGLE_EXEC` | **測定対象そのものの変更。** 多版 MVCC を単版実行へ変える (裁定の正本は本 wave の decisions fragment 由来の D 番号エントリ) |
| cicada | `PARTITION_TABLE` | 死にフラグ。実コードは起動時 option 表示だけ。**README の説明と現行コードが食い違う** |
| cicada | `WORKER1_INSERT_DELAY_RPHASE` | 計測撹乱ノブ。特定 worker の commit 前へ delay を挿入する |
| cicada | `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS` | 計測撹乱ノブ。cicada の source には使用箇所が無く、CMakeLists にのみ現れる |
| 両方 | bare define | **該当なし。** 両 protocol の `OPTIONS` は全 entry が `NAME=${VAR}` 形式で、mocc の `RWLOCK` のような裸の名前は無い |

## 3. tictoc は silo の XOR ではない — 親の誤りを子が覆した

親は段 1 brief で「tictoc も silo と同じ no-wait XOR」を provisional 裁定 (P1) として置いた。
**段 2 プランが最初に否定し、段 3 レンズ A が行番号で裏取りした。**

- silo: 初回 load の後、内側 spin loop に lock word の再読込が**無い**。stale な `expected` を
  保持し続けるため両 0 は livelock する (実測 = `output/insights/2026-06-22_silo-both-no-wait-zero-livelock.md`)。
- tictoc: 外側は write-set を回る `retry` label 付きの loop、内側が spin loop で、
  `#endif` の後の `expected` 再読込は**内側 spin loop の内側**にある。
  したがって両 0 は空の分岐ではなく blocking spin になる。write-only 経路も非 write-only 経路も
  同じ再読込へ到達する。
- 両 1 は `#if` が選ばれ `#elif` が dead code になるため (1,0) と冗長。**除くのはこれだけ。**

**XOR を転用していれば、有効な (0,0) を過剰除外して探索空間を 24 から 16 へ誤って縮めていた。**
過剰除外は「探索しても見つからない」を静かに作るので、発見が遅れる型の誤りである。

**主張していないこと:** 両 0 が競合下で実際に完走すること、公平性、starvation の不在。
tictoc では未実測であり、判断は制御フローからの静的導出である。notes に逐語で書いた。

## 4. 多版 MVCC の軸を「最適化か測定対象の変更か」で分けた

段 3 レンズ B が全 site を照合して 2 flag の性格を判定した。

- **`SINGLE_EXEC` = 測定対象の変更。** timestamp に基づく version chain の探索、pending 待ち、
  aborted version のスキップを迂回して常に inline version を読む。version の生成と timestamp 順
  挿入も、abort / commit 後の多版 maintenance も省く。update payload の扱いも通常経路と異なる。
- **`WRITE_LATEST_ONLY` = 最適化軸。** 読み側の版の選択はこの flag を参照しない。有効時は
  blind write の latest が自分より新しければ保守側に abort する。**正しさを緩めて速く終える
  方向ではなく、余分に abort して許容スケジュールを狭める方向**である。作用点は blind write 側と
  validation 側の両方にある。

親は (P3) で 2 flag を一括して「最適化軸」と裁定していた。**前半だけが覆った。**
除外と採用の線引きに一貫性があることをレンズ B が独立に確認している。

## 5. 親が誤り、子が見つけた 5 件

| # | 親の誤り | 見つけた子 | 訂正 |
|---|---|---|---|
| 1 | tictoc に silo の XOR を転用した | 段 2 / 段 3 レンズ A | 「両 1 のみ禁止」へ。有効 24 |
| 2 | `PARTITION_TABLE` の検索範囲が `cc/tictoc/include/` 部分木と 4 workload source を落としていた | 段 3 レンズ A | 全件で測り直し。結論は維持、根拠を差し替え |
| 3 | 「`space_for` の caller 0」を正しさ境界の根拠にした | 段 3 レンズ A | `Genome` は登録簿を通さず直接構築できるため証明にならない。根拠を差し替え |
| 4 | 差し替え先で拒否機構を `BASELINES[protocol]` の `KeyError` と書いた | 段 6 レビュー B | 実際は `_parse_cli_args` の `ValueError`。添字参照へ到達しない |
| 5 | 変異 M4 の期待 pair 集合を 2 組と書いた | 段 6 レビュー A | 正しくは 3 組。有効数は 24 のままなので size test は落ちない |

誤り 2 は F717 の再発として台帳へ追記した。
誤り 5 は本走前に訂正できた (`mutation-erratum.md`)。訂正していなければ期待 node が過大になり、
MISMATCH と誤判定して変異検査そのものが信用できなくなっていた。

## 6. 段 6 レビュー B の must-fix 3 件はすべて本物だった

1. **notes の事実誤り。** 「genome に列挙しない flag は fresh configure で default 0 に落ちる」は
   一般化として成立しない。`INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS` の default は
   `0` ではなく空文字 (unset) である。`SINGLE_EXEC` へ限定した。
2. **射影不足で独立検証できない。** 方法論として正当な指摘。親が全件で確かめ、
   焦点再レビュー 2 巡目で不足 file を射影して closed にした。
3. **正しさ境界の機構名と例外型の誤り** (上表の 4)。

nit として `WRITE_LATEST_ONLY` の引用が blind write 側だけだったことも挙がった。
この軸は規律 2 に最も近い判断なので、判定は変えずに validation 側の作用点を notes へ足した。

## 7. 正しさ境界 — 登録は測定経路を開かない

**根拠は SPACES から独立の 2 層である** (親が実測)。

1. `orchestrator/campaign/between_run_floor.py` の `_parse_cli_args` 末尾が
   `protocol not in BASELINES` を `ValueError` で拒否する。親の実測:
   `tictoc -> ValueError: unknown protocol: 'tictoc' (選択肢: ['mocc', 'silo'])`、cicada も同じ。
   SPACES への登録はこの dict を変えない。
2. その先に D1373 の source 束縛 admission がある。親の実測:
   silo=True / mocc=False / tictoc=False / cicada=False。
   固定 allowlist ではなく、実際にコンパイルされる source を読んで判定する。

**新しい gate は足していない。** 依頼が scope 外とした範囲であり、既存 2 層で fail-closed である。

**主張していないこと:** システム全体について「正しさ検証前の測定が存在しない」こと。
段 6 の 2 レンズが独立に、`measure_point_floor()` の直接呼出しが admission を通らないこと、
floor CLI が通過後 `trace=False` build を測るだけで verifier を実行しないこと、
screening が verifier より先に bench を実行できることを挙げた。
**これは本 wave が作った欠陥ではなく既存の状態**であり、official commit writer は certified
判定後に閉じている。本 wave の worklog fragment が新規に起票した「正しさ検証を経ない測定面の閉包確認」の項へ送った。

## 8. 凍結成果物との関係

`genome.py` の SHA は `known_axes_freeze.json` / `measurement_freeze.json` / `holdout_freeze.json` の
3 つに source record として `8e8abd7f…` で記録されている。**base commit の時点で live は
`10e91790…` で既に stale** であり (先行 wave T-2115 の mocc 追加による)、本 wave の変更で新たに
赤になる gate は無い。live bytes を `8e8abd7f…` と比べる pin は `.py` に 0 件、
`freeze_verification_hold.HELD = True` (21 件)。規律 7 に従い、当時の bytes という歴史的事実は
変わらず、現行コードとの差はそれだけでは何かを無効にする理由にならない。

## 9. 変異 matrix

固定 commit `727ca869f` の使い捨て worktree、`--runner-mode dispatch`。
baseline PASSED・**KILLED 7 / SURVIVED 0 / MISMATCH 0**・期待 node 完全一致 7/7。
走行後に作業木が commit と byte 一致することを確認した。

| id | 変異 | 期待赤 node 数 |
|---|---|---|
| M1 | tictoc の制約を外す | 2 |
| M2 | tictoc の制約を silo XOR に差し替える (**親が実際に犯した誤りの正例**) | 2 |
| M3 | cicada の制約を外す | 2 |
| M4 | cicada の制約を逆向きにする | 1 |
| M5 | cicada へ `SINGLE_EXEC` 軸を足す | 2 |
| M6 | tictoc へ `PARTITION_TABLE` 軸を足す | 2 |
| M7 | `SPACES` から 2 protocol を落とす | 7 |

## 10. 見なかったことにしていない前提

- 本 wave は測定を 1 件も行っていない。tictoc / cicada の floor も較正も実測していない。
  実測は人間の qsub 手番であり続ける。
- `space_for()` に production caller は無い。登録は探索空間の宣言であって、
  certified な tictoc / cicada campaign を成立させるものではない。
- `docs/phase3.md` 段 6 dormant (b) は**閉じていない**。protocol 別 calibration と
  between-run floor の対象別再実測が残る。本 wave はこの項目を編集していない。
- notes の語句を検査する test は、notes にその語句が書かれているかだけを見る。
  C++ 側の事実そのものは検査しない。この限界は test の docstring に書いてある。

## 11. 段 8 自己改善の裁定 — dev-wave 文書の変更は 0 件

`docs/skill-self-improvement.md` の発火 gate・routing を一度だけ適用した。候補 3 件、採用 0 件。

| 候補 | 裁定 | 理由 |
|---|---|---|
| wave 引数が「t441 が p3_b4_wiring_probe.py 経由で SPACES を参照している」と述べたが、実測では probe は `campaign.model` を import するだけで SPACES を参照しない (`_VIEW_WORKSPACES` への substring 一致による偽陽性) | **不採用** | 起票側の事実誤りであって dev-wave 手順の欠落・曖昧ではない。親は起動時の編集面重複検査で実測し、重複 0 を確認して進めた。手順は意図どおり働いた |
| 変異 runner の argv へ `-k` の式を渡したとき語に分かれた (harness は shell expansion を行わない) | **不採用** | harness が fail-closed で明示的な error を返し、1 手で node 明示指定へ切り替えられた。実害なし。3 層とも byte 予算が満杯であり、自明な argv の事実を手順書へ足す価値より予算圧迫の害が大きい |
| 不在の主張を子に独立検証させるとき、射影が build 対象の閉包を覆っていないと検証が成立しない (焦点再レビュー 1 巡目が partial を返した) | **failures へ routing 済み・dev-wave 文書は変更しない** | F717 の同型再発として台帳へ追記した (routing 規則 1)。F717 の恒久対応は既に主張側の義務を書いており、再発検知も段 3 レンズでの確認を要求している。射影側の義務はその自然な延長なので、同じ内容を dev-wave 入口・reference へ複製しない (routing 規則 5) |

**入口 (`.claude/commands/dev-wave.md`) と `docs/dev-wave/` の reference は 1 byte も変更していない。**

## 12. 受入 1 回目は `owned-path-overlap` で終端拒否された — 親の判定と根拠

受入 1 回目 (`--owned-path orchestrator/campaign/genome.py --owned-path
orchestrator/tests/test_campaign.py`) は `classification=owned-path-overlap` /
`reason=terminal-owned-path-overlap` / `retry=false` で rc=70 終了した。
claimed main は `66e6e9f2b9676243fbcbd57677ac7f3d7c2554d4`。

**これはテストの赤ではない。** `_owned_path_overlap()` は
`git diff --name-only HEAD...main` を file 単位で見るため、宣言した所有 file に main が
1 行でも触れていれば terminal になる。ガードの目的は、並行 wave が同じ file を変えたときに
親へ注意を強制することである。**ガードは正しく発火した。**

親が現物を測った結果は次のとおり。

- main が触れたのは `orchestrator/tests/test_campaign.py` の 1 file だけで、
  `orchestrator/campaign/genome.py` には触れていない。
- その変更は `@@ -49,0 +50` と `@@ -51 +52,2` の import 2 行 (`holdout_observation` と
  `s8b_ratified_freeze` の追加) と、`@@ -13520,0 +13523,181` の**末尾への純粋な追加 181 行**である。
- 本 wave の編集面は同 file の 245〜350 行付近であり、**入ってくる hunk と完全に離れている**。
- 追加された test は `ratified_enforcement_source` fixture と holdout / ratified-freeze 系を使い、
  本 wave が触れた `TICTOC_SPACE` / `CICADA_SPACE` / genome 空間には触れない。逆も同じ。

**判定:** 所有面の意味的衝突は無い。ガードが求めた「親の注意」は上記の実測で払った。
2 回目は `--owned-path` を外して投入し、main の取り込みは acceptance の post-claim merge に任せる
(`DW-O20`)。ただし**競合が無く全走が緑でも合成が保証されるわけではない**ため、
land 前に Codex `role=author` による合成監査を別に行う。

`--owned-path` を外すのは、tool 自身が「未指定のため所有実装面 overlap 判定を省略します」と
明示して受理する運用であり、検査の迂回ではない。省略した判定の中身は上に逐語で記録した。

## 13. 受入 3 回目の赤 1 件は本 wave の差分に帰属しない — F273 の手順で実測した

受入 3 回目は merge を作ったうえで全走し、**19518 passed / 92 skipped / 1 failed** で返した。
tested tip は merge commit `728853f9b`、claimed main は `dbd263c15`。

赤は 1 件のみ:
`orchestrator/tests/test_codex_worker_launch.py::test_failure_class_enum_and_receipt_recomputation_are_closed`。

**本 wave の差分から到達できない。** 本 wave が触れたのは `orchestrator/campaign/genome.py` と
`orchestrator/tests/test_campaign.py` の 2 file であり、当該 test は
`tools/codex_worker_launch.py` を実 subprocess として起動し wall-clock 上限つきで挙動を測る
(`max_wall="10"`、`evidence_grace="3"`、`subprocess.run(..., timeout=10)`)。

`docs/failures.md` の **F273** が同型を既に記録している
(「`test_codex_worker_launch.py` が並行 codex launcher の負荷で受入全走のときだけ落ちる」、
2026-08-23 に再発追記あり)。同 F の再発検知手順に従って親が実測した。

| 手順 | 実測値 |
|---|---|
| 単独再走 (当該 node のみ、`--force-dispatch`) | **1 passed / 5.85 秒 / rc=0** |
| 単独走 (file 全体、`--force-dispatch`) | **211 passed / 8.55 秒 / rc=0** |
| `pgrep -c -f "codex_worker_launch.py run"` (事後) | 1 |
| login node の load average (事後、02:26) | 21.16 / 14.37 / 14.18 |

**判定: 実装差分へ帰属させない。** F273 の恒久対応が定める基準
(「差分が到達しえない file で出た赤は、単独再走で再現性を実測してから扱う。
再現しなければ実装差分へ帰属せず、フレークとして扱う」) を満たす。

`orchestrator/tests/flaky_test_holds.py` への登録は**行わない**。`DW-O18` が登録を求めるのは
再赤または決定的赤の場合であり、今回は 1 回の赤が単独走で再現しなかった。
再走で同じ node が再び赤になった場合に限り、F273 を証拠として Codex `role=author` が登録する。

`DW-O18` に従い、同一 tip で単独再走 1 回・受入再走 1 回だけを行う。
