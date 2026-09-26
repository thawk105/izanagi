# [T-2273] [T-2560] 受入 shard-0 の候補 (a)「局所の写しを collection 中に作る」の効果 — repo に入れない対照診断の隣接 3 対で W_0 が 45.7〜81.3 秒 (中央値 18.0 %) 縮み、事前登録の基準を満たした (2026-09-26)

wave `dev-wave-t2273-shard0-precopy` (branch `t2273-shard0-precopy`)。依頼の逐語は `verbatim/T-2273-origin.md`、裁定は D2243 項 2。**repo の実装面の差分はゼロ** (D1936 項 35): probe 3 file は Codex author の子 branch にあり repo 外で実行し、repo には逐語 `verbatim/probe-source.md` だけを置く。
標本の時点 = 開始 gate 2026-09-26 20:05 JST (`verbatim/startup-gate.log`)。計測 tip = `265cce13c` (開始時の local main、3 job とも同じ)。記録時に local main `25655d808` へ ff-only で揃えたが、`git diff 265cce13c 25655d808 -- orchestrator/tests/test_s8b_oracle_driver.py orchestrator/tests/conftest.py tools/run_tests.py tools/acceptance_shards.py` は空。

## 結論 (最初に読む)

1. **事前登録の基準 (段 4 裁定 `verbatim/s4-ruling.md` §3.3) を満たす。** 有効 3 対の shard-0 W_0 の対差 Δ = W_0(A) − W_0(P) は +64.368 / +81.276 / +45.693 秒 (3 対すべて正)、対率は 18.0 / 22.1 / 12.7 %、中央値 18.0 % (基準 ≥ 10 %)。最大 worker 占有 O_max の対差は +65.087 / +86.546 / +45.635 秒。条件別中央値は W_0 が A 358.937 / P 293.343 秒、O_max が A 282.981 / P 217.318 秒。**推奨 = (a) の実装 wave** (land は実受入の隣接対で判定)。
2. **A (現行) は実受入に近い形で測れた。** 投入前に wave 木を login で 1 回温めた (bytecode を書く collect-only、`verbatim/warm-meta.txt`) ことで、A の pre は 65.171〜65.701 秒 (前回の実受入 64.3〜65.9 秒、第 4 回 replica 128.8〜130.2 秒)、A の W_0 は 357.711〜368.584 秒 (前回の実受入 A 344.8〜367.5 秒)。pre 倍増の原因を bytecode と断定はしない (温めで揃ったという観測まで)。
3. **P の形:** 既存の早期 memo prewarm と同じ点 (controller の `pytest_configure_node` 初回、D2061 / D2062) で背景 thread を起こし、実関数 `_copy_git_visible_output(ROOT, <写し>/output)` を session で 1 回呼んで計算ノード /tmp に写しを作る。builder は写しの完成を待ってから写しを局所複製する。**対照用の差し替えであって観測 wrapper ではない。** 8 builder (共有 7 key + 非共有 1 本) の複製結果は A・P の 3 対すべてで file の stat digest (path・size・mode・mtime_ns、30,701 件。出力欄 `stat_count` 33,805 は file と dir の合計)・dir の path 集合 (3,104 件)・可視集合 (30,707 件。複製対象はここから receipt 等の所定の除外 6 件を引いた 30,701 件) が一致した。
4. **効果の大小は写しの完成の遅れと逆順に並んだ。** 写しの生成は 83.6 / 80.8 / 103.3 秒かかり、collection (写し開始から最初の builder 開始まで 65.7〜70.7 秒) を越えた分、builder は 12.7 / 5.6 / 27.1 秒待った。対応する Δ は 64.4 / 81.3 / 45.7 秒。共有 builder の構築は A 195.2〜198.1 秒 → P 117.4〜146.1 秒。写しの生成時間の揺れの原因 (Lustre の状態・同時刻の他 job) は分解していない。3 点の並びであって回帰ではない。
5. **(a) の後の次の律速は発行 subprocess (b)。** 共有発行 key の builder で、発行 child の内訳 (両条件に同じ計測用 code 変換、A・P で差なし) は finalize_receipt 26.5 秒、draft_receipt 20.4 秒、validate_draft 19.8 秒、gate_check 13.2 秒、verify_receipt 6.6 秒、import 0.6 秒で計約 87 秒。どの phase も CPU 時間 ≈ 壁時間 (CPU 実行が支配)。P の共有発行 key の builder 117.4〜146.1 秒から、この約 87 秒と写し待ち 5.6〜27.1 秒を引いた残りは約 25〜31 秒 (orchestrator の複製・写しからの局所複製・git 等、差し引きの値で内訳は分けていない)。analyzer が名指した次の phase は finalize_receipt (key 別 P 中央値 26.6 秒)。
6. **5 分は replica の値からは言わない (段 4 裁定 B3)。** P の W_0 は 293.343 / 287.308 / 313.244 秒 (参考値、3 本中 2 本が 300 秒未満)。実受入での達成は (a) を実装した wave が隣接対で別判定する。写しの待ちが残る走では 300 秒を越えたので、達成を確実にするには (a) に加えて (b) か写しの短縮が要りうる。
7. **早期 memo prewarm との干渉は観測されなかった。** 早期 memo の待ち超過は A・P とも 0 件。controller の memo job の所要中央値は A 61.8 / P 64.2 秒。P の pre は 65.878 / 70.636 / 65.735 秒 (A との差 −0.7 / −5.2 / −0.03 秒)。

## 1. 依頼と不変条件

依頼 (逐語 `verbatim/T-2273-origin.md`): D2243 項 2 のとおり、候補 (a) の効果 = 実受入の shard-0 の最大 worker 占有と W_0 の短縮を、repo に入れない対照診断 (第 4 回と同じ型の probe) で先に測る。効果が乏しければ発行 subprocess の内訳を測って (b) を判断する。(c) は採らない。計算は job Elapse の実測単価で見積もり、検査込み 2 node 時間以上ならユーザー確認。5 分上限の超過は受容しない。

守ったこと: production・test・conftest・台帳・既存検査は 1 byte も変えていない。観測 wrapper は実物へ同じ引数を 1 回渡す。P の差し替えと発行 child の code 変換は、それぞれ「対照用の差し替え」「計測用 code 変換」と probe の docstring と span に明記した。計算ノードの job 走行中は wave 木へ書いていない。

## 2. 段 3 相談・段 4 裁定・段 6 レビュー

- 段 1 brief (`verbatim/s1-brief.md`) の前提 (P1)〜(P4)・(P2') を、段 3 の相談 2 本 (レンズ A 計測の妥当性、レンズ B 過剰・削除・費用、どちらも修正後 GO) が攻撃した。段 4 (`verbatim/s4-ruling.md`) で 16 件を裁定: pre 倍増の原因は仮説に下げる (A1)、写しは controller 所有の別 dir に置き join してから消す (A3)、同一性は stat digest を両条件同じ方法で採る (A5、bytes の hash は 910 MB × 8 本で W を膨らませるので採らない)、P での早期 memo 超過を自動的に P の失敗と数えない ((P2') 撤回、A6)、発行内訳は両条件に同じ計測用 code 変換で同じ走から採る (A8、別 job を足さない)、5 分は replica の絶対値から言わない (B3)、費用の停止点 7,200 秒を投入ごとに更新 (B6)、smoke は job 1 だけ (B5)。
- 段 6 (`verbatim/s6-ruling.md`): 敵対レビュー 2 本 (修正後 GO) の 8 件を全部 real とし fix1 で直した (P の env を run.json に記録していなかったため全対が無効になる欠陥、controller main thread での test module import、dir size を含む digest、3 対未満で (b) を名指しする出力など)。焦点再レビュー 1 本 (修正後 GO) の残り 2 件は判定の向きを変えない nit として fix しなかった。memo 超過の判定文は親が memo module の実出力と照合した。
- **erratum E1 (job 1 集計後):** fix1 の analyzer は job 1 を無効と判定した。原因は analyzer の登録外れで、builder を「key + その key を最初に要求した test の nodeid」で突き合わせていた (xdist の割付で A と P の初回要求 test が違った) ことと、第 4 回から既知の Lustre llite stats の読取り不能を必須観測の欠落に数えていたこと。8 builder の digest は全部一致していた。登録どおり key だけで突き合わせる形へ fix2 で戻し (判定式・閾値・他の有効性項目は不変)、3 job ともこの版で集計した。

## 3. 計測

| job | request | node | 順序 | Elapse | 結果 |
|---|---|---|---|---:|---|
| j1 | 29983.nqsv | bnode005 | smoke A/P → A → P | 931 秒 | 有効 (smoke A 61.4 秒・P 66.3 秒、rc 0) |
| j2 | 30000.nqsv | bnode117 | P → A | 780 秒 | 有効 |
| j3 | 30021.nqsv | bnode006 | A → P | 796 秒 | 有効 |

- 3 job は逐次 (自分の他の計算ノード job を同時に走らせていない、D357)。j3 の投入時には別 session の変異走行の job が 1 本走っていた (対は同一 job 内で隣接なので、共有 Lustre の外乱は両条件にかかる)。
- 共通条件: 受入 shard-0 と同じ argv (`tools/run_tests.py orchestrator/tests -n 48 --dist loadgroup --junitxml=... -p tools.acceptance_shards -p no:cacheprovider` + 観測 plugin)、`acceptance_shards.create_session(repo, 3)` の shard 0/3、TMPDIR は dispatch 環境から継承、`PYTHONDONTWRITEBYTECODE=1`。**replica であり受入ではない。**
- 有効性 (s4-ruling §3.1): rc 0、outcome 集合一致、builder key ごとの複製結果の digest 一致、P の写しの可視集合が A の実関数の戻り値と一致、clean、HEAD 不変、others 0、record-error 0、ready marker あり、早期 memo 超過なし、必須観測の欠落なし。3 対とも全 20 項目が真。
- 対ごとの値と中央値は親が各 job の analyzer 出力から独立に再計算して照合した (`analysis/recompute.txt`)。

## 4. 限界・言わないこと

- replica の値から実受入の秒数や 5 分達成は言わない。温めで pre と A の W_0 は実受入の値域に入ったが、login collection の並行、受入の外側 dispatch、shard-1 / 2 は再現していない。
- 順序は A が後走 1 回、P が後走 2 回 (j2 は P が先)。順序別対差は AP が 64.4 / 45.7、PA が 81.3 秒で、後走の warm が P を有利にしたとは読めないが、3 対で順序効果を分離はできない。
- 写しの生成時間 (80.8〜103.3 秒) の揺れと、それが collection の終わりを越えるかどうかは実装の効果を左右する。原因は分解していない。
- 同一性は stat 水準 (size・mode・mtime_ns) で、bytes の hash は採っていない。
- 発行内訳は計測用 code 変換を入れた child の値で、変換の費用は両条件に同じだけ乗る (phase 境界の関数呼出しだけ)。
- 有意差判定ではない (3 対、事前登録の基準の成否だけ)。

## 5. 計算量

見積り (s4-ruling §4): 約 4,050 秒 (受入全走を含む)。実績: 3 job の Elapse 合計 2,507 秒 ≈ 0.70 node 時間。記録前の受入全走は別に加わる (worklog に記す)。取り直し 0。

## 6. この dir の中身

- `verbatim/`: 依頼、段 1 brief、段 3 相談の prompt と出力 (a / b)、段 4 裁定、段 5 実装子の prompt と報告、段 6 レビュー (a / b)・fix1・焦点再レビュー・fix2 の prompt と出力、段 6 裁定 (追補・erratum E1 を含む)、開始 gate、温めの記録、probe の逐語。
- `analysis/analysis-compact.json`: 3 job 系列集計の要約 (対ごとの有効性・判定量・時刻・builder 別の構築時間と digest、key 別中央値、発行 phase の key 別中央値、基準の成否)。全文 (系列 5.1 MB、job 別 1.5 MB) と生 span は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/` (`job-out-j{1,2,3}/`、`analysis/`) にある (repo 外)。
- `analysis/recompute.txt`: 親の独立再計算。
- `runs/submissions.txt`: 投入・終了時刻、request、Elapse、tip。

## 7. 再現手順

1. probe を Codex author の branch (`author-t2273pc-probe-fix2` の `f168a8ba6`) から repo 外の dir へ取り出す (逐語は `verbatim/probe-source.md`)。
2. 計測する clean な木を login で 1 回温める: `python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` (`PYTHONDONTWRITEBYTECODE` なし)。
3. `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:50:00 -- python3.10 <probe>/t2273_replica_runner.py ab --order AP|PA --smoke both|none --repo-root <木> --probe-dir <probe> --out-root <out> --job-tag <tag>` を逐次 3 本。
4. `python3.10 <probe>/t2273_replica_analyze.py --ab-series <out1> <out2> <out3> --json <json> --markdown <md>` (1 対は `--ab-dir <out>`)。
