# [T-2265] cohort 2 の図のための観測長 6 秒 companion 測定

wave: `dev-wave-t2265-cohort2-perf6` (2026-09-09)

投入前に固定した設計は同ディレクトリの `measurement-design.md`
(commit `04a7e8cbe65d244a45a46abcdd9d273c6d106d0f`、
blob sha256 `e7d84627941b728881a9e9ba6099c4dbad83c690f7453a37903b3ad5ac67051d`)。

---

## 0. 結論を 2 行で

**測定は完了した。** 観測長 6 秒の performance 成果物 7 本を測り、7 本すべてが図の生成器の
受理条件 (168 点の完全格子・identity 一致) を満たすことを実測した。

**図は出せなかった。** 生成器の layout 検査が実データで落ちた。原因は cohort 2 の cell 名が
長いことで、**1 つの軸ラベルが図の右端を 5.85 px はみ出す**。生成器は本 wave の scope 外なので
触らず、裁定 §8 の停止規則どおり止めた (§5 に裁定パッケージ)。

## 1. この wave が主張すること・しないこと

**主張すること。** 観測長 6 秒・schema v3・legacy 7 腕 x 3 workload x 8 スレッドの
performance 成果物 7 本が存在し、cohort 2 の診断成果物と identity が完全一致する。

**主張しないこと。**

- **観測長 3 秒の凍結判定を置き換えない。再確認もしない。** 既存 7 本
  (`978014`〜`978020`、観測長 3 秒・schema v2) とそれに基づく H1–H7 の判定はそのまま残る。
- **cohort 2 の腕の trace 無効版ではない。** ここで測った 7 腕のうち `cw-as-dyn` は
  時間 cap が 10240 µs で、cohort 2 の 3 腕の cap 9223372036854775807 µs とは違う。
  **別の並行性制御設定である。** この測定値を、cohort 2 の局所 ITT の主判定
  (推奨方向の実用優越 +4.900%、95% CI [+3.316%, +6.509%]、worklog 1393) の性能側の裏づけとして
  読んではならない。段 3 の敵対レンズが指摘し、親が採用した最重要の限定である。
- **性能値は未認証である。** 直列性の検査を通していない (絶対規律 1・2)。variant の採用根拠にしない。
- **性能の数値を 1 つも記録していない。** 図が公開されなかったので、この集合から H1–H7 も
  系列値も出していない。図の失敗を見た後で手計算の解析を始めるのは、事前に固定した
  解析経路の外側であり、やらなかった。

## 2. なぜ測る必要があったか

`tools/plotting/plot_dynamic_backoff.py` は、cohort 2 の診断成果物 (schema
`izanagi-dynamic-backoff-trace/v4`) と組にする performance 成果物に観測長 6 秒を要求する
(`expected_extime_s = 6 if terminal_contract`)。既存 7 本は観測長 3 秒なので identity 検査で
拒否される。**図を描くためだけの要件であり、新しい問いを立てたのではない。**

直前の wave の insight (`output/insights/2026-09-08_t2265-cohort2/README.md` §9-2) が
「cohort 2 の図を実際に描くには、観測長 6 秒の performance 成果物が 6〜7 本要る。本 wave は
それを測っていない」と書いて残した項目である。

## 3. 測定

7 job を同時に投入した。投入台帳は job dir の `submitted-jobs-2.tsv` (repo 外)。
投入元は commit `8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235` を指す detached worktree で、
canonical・tracked-clean・ccbench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` clean を
投入直前に実測した。qsub 7 回のそれぞれ直前にも HEAD と tracked-clean を再検査している。

| rep | job | host | 開始 | 終了 | wall (s) | 成果物 sha256 先頭 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `986850.nqsv` | bnode006 | 00:31:02Z | 00:51:23Z | 1220.9 | `f813dc37edf26b70` |
| 1 | `986851.nqsv` | bnode017 | 00:29:22Z | 00:49:40Z | 1218.6 | `717f1f2ac94072c6` |
| 2 | `986852.nqsv` | bnode007 | 00:29:20Z | 00:49:40Z | 1219.6 | `daac0bac61c9ebca` |
| 3 | `986853.nqsv` | bnode035 | 00:36:00Z | 00:56:21Z | 1220.8 | `59058e11af2785f0` |
| 4 | `986854.nqsv` | bnode002 | 00:30:46Z | 00:51:09Z | 1222.3 | `2e74242a752a7213` |
| 5 | `986855.nqsv` | bnode015 | 00:33:41Z | 00:54:02Z | 1220.8 | `71dd3567719f53bd` |
| 6 | `986857.nqsv` | bnode010 | 00:36:57Z | 00:57:19Z | 1222.4 | `6819eb7cbdb4fefb` |

- **7 job は 7 つの別ノードに載った。** 図の生成器は hostname の重複を拒否せず provenance に
  列挙するだけなので、これは保証ではなく実測結果である。
- 開始時刻は 00:29:20Z から 00:36:57Z までの 7 分 37 秒にばらけた。queue 待ちの差である。
- wall は 1218.6〜1222.4 秒。投入前の見積り (観測長 3 秒の実測 714〜731 秒 + 168 点 x 3 秒
  = 約 1245 秒) とほぼ一致した。walltime は 3600 秒を与えたので余裕は約 2.9 倍だった。
- 途中で落ちた job は無い。**結果を見てから job を足していない。**

## 4. 親が作図前に実測したこと

段 4 裁定 §5 のとおり、7 本すべてについて次を実測した。**全項目が緑である。**

1. `cells` の row 数が 168 であること — 7 本とも 168。
2. 座標集合が `CELLS x WORKLOADS x THREADS` の全体と一致すること — 7 本とも完全一致
   (部分集合ではない)。生成器の parser は 1〜168 row を許すので、file の実在だけでは
   完全な block の証拠にならない (段 3 レンズ A の指摘)。
3. `extime_s == 6`、`schema_version == izanagi-cicada-adaptive-3const-probe/v3` — 7 本とも一致。
4. `cell_order` が rep index の巡回順であること、`rep_index` が 0..6 で重複しないこと — 一致。
5. `pbs_jobid` が 7 本で相異なること — 相異なる。
6. **15 個の identity field** が cohort 2 診断 `stage1-rep0-0_985851.nqsv.json` と一致すること —
   7 本とも 15 個すべて一致。

生成器の `load_inputs` も 7 本 + 診断を受理した (`contract = cohort2`、`n_perf = 7`)。

## 5. 図が出なかったこと (裁定パッケージ)

`python3 tools/plotting/plot_dynamic_backoff.py <出力接頭辞> --trace-json <診断> <perf x7>` は
次で終了した。

```
[error] FigureLayoutError: text leaves figure: 'cw-as-dyn-c2-p2'
[plot rc=1]
```

親が図ごとに分けて測ったところ、**3 図のうち 2 図は layout 検査を通る**。

| 図 | layout 検査 |
| --- | --- |
| thread-axis | OK |
| contrasts | OK |
| diagnostic | **FAIL** — `text leaves figure: 'cw-as-dyn-c2-p2'` |

はみ出しの実測値は次のとおり。

- 図の大きさ 1452 x 891 px。
- **はみ出しているラベルは 1 つだけ**で、量は **5.85 px** (図幅の 0.40%)。
- 該当は右下パネルの右端の x 軸目盛ラベル `cw-as-dyn-c2-p2`。
  bbox は `x1 = 1457.8` で図の右端 `1452.0` を超える。

原因は `make_diagnostic_figure` の `fig.subplots_adjust(..., right=0.985, ...)` に対して
cohort 2 の cell 名が長いことである。cohort 1 の `cw-as-dyn-p2` と legacy の `cw-as-dyn` は
それぞれ 3 文字・7 文字短く、はみ出さない。

**test にこの穴がある。** `orchestrator/tests/test_plot_dynamic_backoff.py` で
`check_figure_layout` が現れるのは、それを monkeypatch で差し替える
`test_layout_failure_leaves_no_partial_outputs` だけである。cohort 2 の
`test_plot_accepts_exact_cohort2_grid_and_uses_artifact_cells_in_figure_loop` は
`make_diagnostic_figure` を実際に呼んで軸ラベルまで確認するが、**本物の layout 検査を通していない。**
`FIGURE_CONVENTIONS.md` §10 が「fixture が実寸でもテストは完了の証拠にならない。
実データで全モードを実走して 3 成果物を確かめるまで完了と申告しない」と書いている型の欠陥である。

**本 wave は生成器を触らなかった。** 理由は 3 つ。

1. 段 4 裁定 §8 が「bbox が実データで落ちたら生成器を触らずに停止する」を**結果を見る前に**
   固定していた。失敗を見た後で自分の停止規則を外すのは、規律 2・3 が防いでいる型そのものである。
2. `tools/plotting/plot_dynamic_backoff.py` は稼働中の別 wave
   (`dev-wave-t2417-policy-arm-perf`) が変更を保持しており、その worktree は
   `t2187_adaptive_const_probe.{py,pbs}` の未解決 merge 競合を抱えたままである。
3. `subplots_adjust` の定数は legacy・cohort 1・cohort 2 の 3 系統が共有する。
   変えると既発表の図 (`output/insights/2026-09-05_dynamic-backoff-mechanism/figures/`) の
   再生成結果も変わる。単独の wave が独断で動かす値ではない。

**ユーザーへ返す裁定。** 次のどちらかを選ぶ必要がある。

- (A) 生成器の `make_diagnostic_figure` の `right` を下げる (5.85 px = 0.40% なので
  `0.985` → `0.975` 程度で足りる)。同時に cohort 2 の layout 検査を test へ足す。
  **既発表図の再生成結果が変わることを承知したうえで**行う。
- (B) T-2417 の wave が同 file を持っているので、そちらの所有として直す。

どちらでも、**測定はやり直さなくてよい。** 7 本の成果物は残り、identity 束縛も成立している。

## 6. 段 3 と段 6 の敵対検証が見つけたもの

### 6.1 段 3 (投入前) — 名乗りが決まっていなかった

2 レンズが同じ根に当たった。**観測長 6 秒の 7 腕格子を「事前登録済みの確認的判定」と呼ぶのか
「未認証の記述的な別測定」と呼ぶのか**が決まっていなかった。親は後者に固定した。

これを固定すると、当初の provisional 裁定 (companion の新規事前登録文書を作る) が不要になる。
**作っても成果物へ束縛できない**からである — 成果物の `prereg_sha256` は driver が常に
`docs/dynamic-backoff-preregistration.md` の bytes から作り、図の provenance もその値しか出さない。
**発火しない保証を置くのは実装したふり**なので `DW-G04` で留め、代わりに本 insight の一部
(`measurement-design.md`) を投入前に commit する形へ縮めた。

他に採用した所見。

- **「投入は detached checkout からしか成立しない」は誤り** (段 1 brief の訂正)。
  正しくは「対象 commit を指す tracked-clean な checkout であればよい」。detached であることは
  `repo_head` に符号化されない。実務上 detached worktree を使ったのは他 session と干渉しない
  ためであって、必要条件ではない。
- **`clocks_per_us = 2100` はノード較正値ではなく Pegasus contract の固定値。**
  7 本が別ノードに散っても identity は落ちないが、**identity の一致は物理クロックの一致の
  証拠ではない。**
- **performance 経路に外側 watchdog は無い。** 1 点 180 秒 timeout だけで、build 7 本に
  deadline が無い。→ `elapstim_req` を 40 分から 1 時間へ上げた。
- **成果物 parser は 1〜168 row を許す。** → 親が作図前に完全格子を実測することにした (§4)。
- **図に使う診断の選択 (job ID 昇順の先頭) は事前凍結ではない。** 12 本は既に存在し主判定の
  解析も済んでいる。「結果非依存の規則を、診断図を 1 枚も描く前に固定した」が正確な表現である。

### 6.2 段 6 (実装後) — 実機に投げるまで誰も知らなかったこと

段 6 は投入・待機の script 2 本を対象にした。**3 巡の fix を要した欠陥は 4 件とも、
この計算機の scheduler が NQSV であって PBS Pro ではないことに由来する。**

1. **`qstat -f` の書式** (親が実測)。実機は `Request ID:` / `Current State = Running` を返し、
   `Job Id:` / `job_state =` / `Exit_status =` は出ない。終了 job は **rc=0 のまま**
   `does not exist` を返し、一覧からも消える。→ 生存判定を `qstat` 一覧の行頭 RequestID の
   完全一致へ作り直した。
2. **`qsub` の出力** (親が実機に 1 本投げて実測)。素の job ID ではなく
   `Request 986814.nqsv submitted to queue: gen_S.` という文を返す。最初の投入はこれで rc=3 で
   止まり、**job は queue に入ったのに台帳へ記録されなかった。** 段 6 で入れた
   「受理済み job を見失わせない」警告が発火して job ID が stderr に出たので `qdel` で取り消せた。
   実害なし。
3. **投入側の RequestID には sub-request 接頭辞が付かない** (親が既存成果物 20 件で実測)。
   job の中の `PBS_JOBID` は `0:<RequestID>` で、出力 file 名は
   `stage1-rep<N>-0_<RequestID>.json` になる。期待 file 名を投入側の RequestID から組み立てると
   7 本すべてが `missing` になる。
4. **NQSV の state 語彙検査が `qstat` の全行に掛かっていた** (親が発見)。`qstat` は同じ利用者の
   全 job を出すので、無関係な別 session の job が未知 state になった瞬間に監視が死ぬ。
   → 自分の 7 job の行だけに限定した。

**教訓: 実行環境に依存する実装は、レビュー通過を completion の証拠にできない** (`DW-O16`)。
子は 4 件すべてを「偽 `qstat` / 偽 `qsub`」で緑にしていた。実機の書式は親が測るまで
誰も知らなかった。親は fix 後の待ち手を**実機の `qstat` に対して 1 回走らせて**確かめている
(生存 4 本を `RUN`/`RUN`/`QUE`/`PRR` と判定し、不在 3 本を terminal + json missing とし、
timeout 経路で 7 行 inventory を出して rc=5)。

## 7. 限界 (正直に書く)

- **束縛が外付けである。** 成果物 JSON の `prereg_sha256` は既存の事前登録文書を指し、
  `measurement-design.md` の SHA は成果物にも図の provenance にも入らない。
  束縛は投入台帳と本 insight でしか辿れない。**成果物だけを見た第三者にはこの束縛が見えない。**
- **図単体では「置き換えない」と言えない。** 生成器は本 wave の scope 外なので、非置換の
  断り書きを図の中に入れられない。限定は本 insight にしかない (図が出た後も同じである)。
- **ノードの単独性は確認していない。** 7 job が 7 ノードに散ったことは実測したが、
  各ノードが専有だったかは測っていない。
- **A+B+C patch stack の legacy 7 腕の実行体は認証していない。** 直列性の検査を通していない。
- **生成器は入力どうしを比べるだけで実 repo と照合しない。** `repo_head` や `prereg_sha256` は
  入力 JSON から読んだ値を突き合わせるだけである。本 wave は自分で投入した成果物だけを
  入れたので実害は無いが、限界として書いておく。

## 8. 変異検査

**免除。** 本 wave の repo 差分は docs (本 insight と `measurement-design.md`) だけで、
D95 決定 2 の実装面 (`orchestrator/`・`tools/`・`hooks/`・場所を問わない Python/shell 等) の
差分が 0 である (`DW-S04`)。qsub launcher と待ち手の `.sh` 2 本は Codex の `role=author` /
fix 子が書いたが、親が job dir へ退避して実行し、**repo へ commit していない。**
受入全走は免除していない。

## 9. 工数

codex 子 9 本 (plan 1 / consult 2 / author 1 / review 2 / fix 3)。うち author 1 本が
`f43_fragment` で不受理となり、最終報告が途中で切れた。実装 file 2 本は残っていたので、
親が現物を読んで内容を確かめ、段 6 のレビューへ回した。fix は 3 巡で、いずれも §6.2 の
実機書式に起因する。`DW-O16` の 3 巡上限に収まっている。
