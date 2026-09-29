# 受入全走の最長経路の分解 — 9/26 以降の shard wall の約 1 分増は、受入門番の共有雛形が `PYTHONDONTWRITEBYTECODE=1` を立て、投入元 worktree の bytecode cache が冷えたままだったことによる。雛形から外した。台帳・割付の見直しは効果 0 秒 (2026-09-29〜30)

依頼: `/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_2.txt` (共通指示 `common.txt`)。受入全走の実 wall を、検査範囲 (受理集合) を 1 つも縮めずに縮める。
wave: `worktree-dev-wave-acceptance-critical-path`、base = local main `8fe87f852`。job dir `/work/1/SFC/tanab/dev-wave-jobs/acceptance-critical-path-20260929/` (brief・裁定・codex の入出力・対照の生記録)。
段構成は軽量版 (依頼が段 3 相談 1 本と段 6 review 1 本を残すと指定)。段 2 は brief が plan を兼ねた。逐語は `verbatim/`、集計は `data/`。

## 結論

1. **受入 1 走の外側 (投入意図 → 統合 junit) は、9/29 の緑 58 走で中央値 509.5 秒。各指標の中央値は、待ち行列 (3 shard の最大) 177.6 秒、shard wall の最大 W_max 337.9 秒、後処理 15.7 秒** (`data/runs.csv`、`data/agg.out`。中央値どうしなので和は分解式ではない)。依頼の「約 14 分」級 4 走 (804〜936 秒) は、W が通常範囲 (293〜429 秒) で、待ち行列が 458〜514 秒に伸びた走だった。待ち行列はこの wave の手段では縮められない。
2. **shard 内の最大の区間は、計算ノード上の collection (pre = session 開始 → collection 完了) で、中央値 112〜117 秒 (W の約 3 分の 1)。9/22〜23 の日別中央値は 64.8〜74.9 秒で、冷の走は少数だった。pre は走ごとに温 (65〜80 秒) と冷 (125〜140 秒) の二峰で、多くの走では同じ走の 3 shard がそろって同じ峰に入る (中間の走では shard ごとに割れる)。9/26 の午後以降は冷の走が多数派になった** (`data/pre_series.out`、`data/pre_step.out`)。二峰は既知の bytecode cache の温冷 (memory・T-2710: 温 65 / 冷 130、D2253 の replica: 温めで pre 65 に戻る) と一致する。
3. **冷の原因は、受入門番の共有雛形 `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` (9/26 作成、[T-2838]) 19 行目の `export PYTHONDONTWRITEBYTECODE=1` である。** 出自は 9/26 の t2273 系計測 wave 群の script (4 本とも同じ行を持つ)。この値は launcher → `tools/run_tests.py` → login collection (`_collect_login_universe`、`_dispatch_environment()` が `os.environ` を継承) と計算ノード worker に継承され、投入元 worktree の `orchestrator/tests/__pycache__` を誰も書かない。9/26〜29 の 124 走で、dispatch の `request.json` の env にこの値がある 73 走は冷 67 / 温 6、無い 51 走は温 37 / 中間 12 / 冷 2 (`data/pyc_crosstab_req.txt`)。各 worktree の初回受入に限っても、ある 60 走は冷 58、無い 35 走は温 23 / 中間 10 / 冷 2。9/29 の同じ日では温 19 走の W_max 中央値 297 秒、冷 28 走 357 秒 (別 wave・別の木の観測差で、全差を pyc に帰属はしない)。
4. **共有雛形から export 行を外した (repo 外。旧版 sha256 `b30be0fb…` → 新版 `25d25685…`、差分は export 1 行の削除とコメント 1 行)。** 受入自身の login collection (正規経路) が、post-claim merge 後の検査対象の木に pyc を書くようになる。受入の清浄性の指紋は `git status` 由来で、`__pycache__/` は .gitignore 済み (9/26 以前の常態に戻るだけ)。門番の閾値・周期・再投入は byte 不変。
5. **同時刻対照 (事前登録どおり 2 対、同 commit `4604b9fe4` の fresh 木 4 本) の判定は「判定不能」。** 2 対とも待ち行列が 22〜29 秒と短く、H の 6 shard すべてが login collection の完了前に始まったので、事前登録の適格 shard が 0 件になった。観測値は、H の pre が K より 6/6 shard で 24.7〜28.6 秒短い (K 135.96〜137.81 秒、H 108.26〜110.98 秒)、ΔW_max は +23.8 / −148.3 秒 (対 2 の H の shard-0 が最大占有 371 秒の外れ値)。終了後の tests の pyc は H が 440、K が 0 (`verbatim/pairs-aggregate.md`)。**したがって、待ち行列が短い初回受入での効果は部分的 (pre 約 −27 秒) で、約 65 秒の全効果は shard 開始前に pyc がそろっている場合 (待ち行列が login collection より長い初回、または同じ木の 2 回目以降) に限られる見込み**。全効果の側はこの wave の対照では測っておらず、根拠は結論 3 の観測と既往の対照 (T-2710、D2253) である。
6. **台帳の再生成・割付の変更は効果 0 秒。** 現行台帳での `allocate` の再計算は実走の割付と 3 shard 完全一致した。台帳を実測中央値に置換、`--refresh` で最新 1 走から再生成、5 走の中央値を合成、のどれでも、48 worker の list scheduling で予測した shard 間最大の makespan は 153.7 秒で差 0。shard-1 / 2 は単独で長い test 1 本 (151.6 / 153.7 秒) が律速で、総和は既に均衡している (`data/plan_summary.tsv`、`data/alloc_table.tsv`)。この結論は試算した台帳置換案に限る。fixture 共有で個々の所要が変わる案は評価していない。
7. **依頼の fixture 共有 (test_s8b_oracle_driver の T-080 群、test_s8b_floor_campaign の official 群) は実装していない。** 次の一手として下の §6 に数値つきで残す。所要台帳・`tools/acceptance_shards.py`・test file は変更していない (repo 内の実装面差分ゼロ)。

## 1. 区間分解 (9/29 の緑 58 走)

赤 21 走、成果物欠落 16 走を除いた。shard dir `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/` の dispatch-intents・junit・report から計算 (`data/runs.csv`)。receipt 側の claim / merge / 検査の区間は、対応する receipt を見つけられず未測定。

| 指標 (秒) | 中央値 | 最小 | 最大 |
|---|---:|---:|---:|
| 外側 (統合 junit mtime − 最早 intent) | 509.5 | 303 | 2161 |
| 投入前 (intent → 最後の confirm) | 4 | 3 | 6 |
| 待ち行列 (3 shard の最大) | 177.6 | 21 | 1789 |
| W_max | 337.9 | 250 | 481 |
| 後処理 (統合 junit − 最遅 shard 終了) | 15.7 | 13.4 | 18.8 |
| W (shard-0 / 1 / 2) | 328.3 / 292.5 / 287.3 | | |
| pre (shard-0 / 1 / 2) | 112.4 / 114.5 / 116.6 | 66 | 146 |

- 最遅 shard は shard-0 が 37 走、shard-2 が 11、shard-1 が 10。W 最大 shard は shard-0 が 51 走。
- 最新走 (86bd457c) の shard-0 は worker 占有の和 5,961 秒・平均 124 秒・最大 185 秒 (上位 5 worker が 158〜185 秒) で、1 本の長い test ではなく shard 全体の仕事量で決まる型。
- 重い 2 群はどちらも全走 shard-0: T-080 群 (test_s8b_oracle_driver の名前に t080 / stub_free / e2e を含む 44 nodeid) の合計は中央値 2,112 秒 (1,731〜3,786)、floor official 群 (test_s8b_floor_campaign の official_ / pilot_resume を含む 54 nodeid) は 1,097 秒 (805〜2,897)。依頼文の「T-080 群 約 3,566 秒」は遅い走の値で中央値とは合わない (`data/agg.out`)。
- 台帳値と実測中央値の対応は `data/ledger_vs_measured.txt` (T-080 の約 20 件は台帳 190〜230 秒に対し実測 84〜112 秒)。

## 2. pre の二峰と原因 (結論 2・3 の根拠)

- 日別推移 (`data/pre_series.out`): 9/10〜9/22 は中央値 53〜67 秒、9/23 は 74.6、9/26 以降は 112〜133。9/26 の午前 (10:24〜12:52) の走は 64〜81、13:11 以降は多くの走が 131〜135 (14:38・14:49・15:14 の走は 65〜91) (`data/pre_step.out`)。9/23 にも shard-0 の pre が 129〜131 の走が 6 件ある。同じ universe 件数 (27,971) の走でも 67 と 133 が混在するので、コードの段差ではない。
- 最新走の投入元 worktree (`dev-wave-t2867-silo-contrast-impl`) の `orchestrator/tests/__pycache__` は 16 個 (test file 440 本) だった (親が実測)。
- 反例 8 走: request に値があるのに温 6 走は、同じ木の先行する (値の無い) 受入が pyc を書いていた可能性が高い (推測、6 走中 4 走は 2 回目以降)。値が無いのに冷 2 走 (vhash-cicada-baseline-tuning、t2853-r2-fig11、どちらも初回) は理由未確認。中間 12 走は全部値の無い側で、shard ごとに峰が割れる (login collection の完了前後で shard の開始が分かれたと読むのが対照 §4 と整合するが、走ごとには未照合)。
- 雛形の export は `tools/pegasus/dispatch_compute.py` が計算ノード子に `setdefault` で立てる値とは別物で、作用点は login 側の cache 作成だけ (段 3 相談 所見 3)。

## 3. 割付の机上試算 (結論 6 の根拠)

- 最新走の `observed_universe` (28,265 件、`{file, group, nodeid}`) を `tools.acceptance_shards.parse_records` → `allocate(recs, 3)` に渡し、実走の `selected` と 3 shard とも差 0 (4,304 / 11,599 / 12,362 件)。
- 「真の所要」は 58 走の junit testcase time の nodeid 別中央値 (48 worker 並行下の壁時計値)。予測 makespan は pre・固定費を含まない。
- モデルの検証: shard-1 / 2 の予測 (151.6 / 153.7) は実測の最大 worker 占有の中央値 (159.0 / 155.7) とほぼ一致。shard-0 は予測 115.1 に対し実測 207.3 で、模型が持たない lock 待ち・共有 base 構築待ちの分と推測 (未検証)。
- `tools/update_acceptance_duration_ledger.py` は複数 JUNIT に同じ nodeid があると rc=2 で拒否する (和・最大・最後を採らない)。

## 4. 同時刻対照 (結論 5 の根拠)

事前登録: `verbatim/s4-ruling.md`「対照の事前登録」(結果を見る前、9/29 23:45 に固定)。runner / 集計器は Codex author 製 (job dir `meas/run-pair.sh` sha256 `737503d8…`、`meas/aggregate.py` `dc74b89c…`)。

- 木: commit `4604b9fe4` (投入時の local main、木作成から投入まで進み 0) の fresh worktree 4 本。作成直後の pyc 0・submodule 13 entry を記録 (`data/make-trees-summary.txt`)。
- K = `PYTHONDONTWRITEBYTECODE=1` (旧雛形相当)、H = unset (新雛形相当)。各対で `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を同時起動 (起動差 0.018 / 0.003 秒)。対 1 は 00:20〜00:35、対 2 は 00:35〜00:54 (JST 9/30)。全 12 shard が rc=0。
- 実効値の確認: K は 3 shard とも request env が "1"、終了後の tests pyc 0。H は request env に値なし、終了後の tests pyc 440。

| 対 | K pre (s0/s1/s2) | H pre (s0/s1/s2) | Δpre | K W_max | H W_max | ΔW_max | 待ち行列 |
|---|---|---|---|---:|---:|---:|---|
| p1 | 137.7 / 136.8 / 137.1 | 110.3 / 110.2 / 111.0 | 27.4 / 26.6 / 26.1 | 341.3 | 317.5 | +23.8 | 22〜25 秒 |
| p2 | 136.8 / 136.0 / 137.8 | 108.3 / 111.2 / 110.0 | 28.6 / 24.7 / 27.8 | 341.5 | 489.8 | −148.3 | 22〜29 秒 (K の s2 だけ 413 秒) |

- 判定 (事前登録どおり): 2 対とも H の全 shard が login collection 完了前に開始 → 適格 H shard 0 件 → 「判定不能」。W_max の縮みは 2 対そろわず観測なし。
- 計算: 対照 12 job の Elapse 合計 4,058 秒 = 1.13 node 時間 (`data/pairs-elapse.txt`)。「同じ木の 2 回目」の対を追加すると最終受入込みで 2 node 時間を超える見込みなので取っていない。

## 5. 相談・レビューの採否

- 段 3 相談 1 本 (所見 8、`verbatim/s3-consult-out.md`): 高 1 (login の温めを `python3 -m pytest` で直接起動する案は AGENTS.md:52 に反する) を採用し、明示の温めを撤回した。高 2 (温めた木と検査する木の不一致) は撤回で解消。中 3〜6・低 7〜8 も採用 (裁定は `verbatim/s4-ruling.md`)。
- 段 6 review 1 本 (`verbatim/s6-review-out.md`) は NO-GO、must 3 (shard 対応の部分一致、期待 commit の証跡、実効 env の記録) と should 4 を全部 real として fix 1 回 (`verbatim/s6-fix1-out.md`)。焦点再レビュー 1 巡 (`verbatim/s6-focus1-out.md`) は NO-GO: 新規 must 1 (K と H に同じ木を渡せる) は運用で閉じた (木 4 本の一意性・fresh・submodule・commit を木作成 log と record.json の path で親が照合)。partial 2 / 3 / 6 は木作成 log・終了後 pyc・request env・同時起動直前の ps 全行で足りると裁定。should (JSON 要素の一致) は要素の完全一致なので refuted。fix を重ねず閉じた (DW-O16)。

## 6. 次の一手 (残る律速)

1. **初回受入でも shard 開始前に pyc をそろえる。** 待ち行列が login collection より短いと効果は約 27 秒に留まる (§4)。正規経路 (`tools/run_tests.py`) の中で login collection の完了を shard の collection 開始の前に置くか、計算ノード worker に pyc を書かせるか、の設計択一。`tools/run_tests.py` の blob を変えると D987 により in-flight の全 wave が再受入になるので、並走 wave の少ない時間帯を選ぶ。見込みは待ち行列の短い初回受入で pre −約 38 秒 (65 − 27)。
2. **shard-0 の最忙 worker (実測中央値 207 秒 対 shard-1 / 2 の約 157 秒) を作る成分の削減。** 候補: T-080 共有 base の構築待ち (flock)、test_s8b_floor_campaign の `_real_output_snapshot()` 前後 2 回 (重い 10 関数 12 nodeid、各約 87 秒)、T-080 active-v2 系 9 node が `receipt_root` 付きで emitter memo を迂回して毎回実走する分。fixture の scope 引き上げは test 間の状態共有を生む (段 3 所見、コード地図は job dir の子の報告)。実装前に最忙 worker の item 列を実測する (worker 名つき junit の property が一部 testcase にしか付かない点の確認を含む)。
3. 待ち行列 (中央値 178 秒、最大 1,789 秒) は制御外。

## 7. 確かめたこと・確かめていないこと

- 確かめた: 区間分解と二峰 (58 走・124 走の生データ)、割付の再現と試算、雛形の差分 (diff)、対照 2 対での pre の短縮 (6/6 shard) と実効 env・pyc。
- 確かめていない: 雛形変更後に他 wave の受入で pre が温の峰へ戻ること (配置後の走は未観測)、約 65 秒の全効果の同時刻対照、receipt 側の claim / merge 区間、反例 2 走の冷の理由、shard-0 の模型の外れ (約 92 秒) の内訳。
- 呼出し側が自分で `PYTHONDONTWRITEBYTECODE` を export する wave、既に写した旧雛形の job dir script (t2273 系の 4 本など) には効かない。
- 撤去 tool は ignored file も証拠化するので、pyc が増えると撤去時の証拠量は増えうる (段 3 所見 8)。
