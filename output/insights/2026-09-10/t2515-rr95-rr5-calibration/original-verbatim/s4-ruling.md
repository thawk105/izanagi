# 段 4 裁定 — [T-2515]

段 2 プラン 1 本、段 3 敵対相談 2 本 (レンズ A = 正しさ境界と受理集合、レンズ B = 整合と実効性)
の所見を裁定する。所見番号は各出力のもの。

## 親 brief の訂正 (real、親が誤っていた)

- **A4 の docs anchor は誤り。** pin されているのは `docs/pegasus-runbook.md` ではなく
  `tools/pegasus/README.md` (`test_pegasus_calibration_workload.py:22, 639-647` が読む)。
  親が実物で確認した (README:125-140 に例と whitelist 断定がある)。
- **A1 の行番号は 42-45 でなく 40-43。** 44 行以降は protocol gate である。
- **成果物契約が誤り。** `registered/` へ publish されるのは accepted JSON **だけ**で、
  `calibration.md` は attempt staging に残る (`cli.py:1012-1028`)。完了検査は JSON で行う。
- **P2 の根拠から D1488 を外す。** D1488 は study ごとの workload/cell shape と `--policy` path の
  exact map についての裁定で、calibration の rratio を扱っていない (A[12] real)。
  `{5,20,50,80,95}` に閉じる根拠は依頼そのもの (「本題の実装だけ、一般化は scope 外」) に置く。

## P1 の裁定

依頼の「A-6 はここで止まっている」は `docs/paper-story/2026-09-05.md` §8 と食い違う。§8 は
A-6 の停止原因を「計算ノードで `FetchContent_Populate(masstree)` が落ちる」と書いている。
**成果物は変えない** (rr95 / rr5 の accepted calibration を取る)。ただし本 wave の記録で
「A-6 を解除した」とは書かない。根拠は T-2515 原文の「B-4 の 3 workload セルが 2 件不足」に置く。

## 採用する real 所見 (実装する)

1. **A[3]: 非 canonical 字面の runtime 負例を足す。** 抽出 literal の静的 assert だけでは、
   gate の前に `${RRATIO#+}` や先頭 0 除去を挿し込む変異で恒真化する。submitter を実起動する
   負例に `05` / `+5` / ` 5` / `5 ` / 全角 `５` を含める。これは新設 gate ではなく、
   本 wave が書くテストの検出力の問題である。
2. **A[4] / B[3]: job body の rratio gate は移動しない。** プランの relocation 案を却下する。
   現位置は `write_failure` 準備後なので不正値が構造化 `failure.json` に残る。移動すると
   その provenance を失い、順序意味論も変わる。値と error 文字列だけを更新する。
3. **B[1]: README の旧 3 値断定を全部更新する。** 例 (126-127 行) の追記だけでは閉じない。
   132 行「20 / 50 / 80 の固定 whitelist」、137 行「rr80/rr20 の calibration」、
   169 行「`skew0p9_rr{20|50|80}_rmw0`」も 5 値へ揃える。
4. **B[4] / B[6] / B[7]: 投入は独立した 2 本の detached submit-tree から並行で行い、
   成果物を wave tree へ sha256 照合つきで取り込む (最終版)。**
   - **裁定は 2 度動いた。経緯を残す。** 初案は「別 tree で並行 + 取り込み」。次に job の実所要が
     3 分 25 秒と実測できたので「wave tree から直列」へ変えた。最後に `qstat` で
     **自分の job 6 本がすべて待ち行列にある**ことを実測し、初案へ戻した。
     決め手は job の実行時間ではなく**待ち行列の長さが予測できないこと**である。
   - wave worktree から投入すると、job が queue にいる間ずっと wave tree の `output/` へ
     書きうる主体が居続ける。`DW-M05` は変異走行中に worktree へ書きうる子を止めることを
     要求するので、待ち時間が伸びるほど段 6 が止まる。別 tree なら段 6 と並行できる。
   - job body は投入元 repo の CCBench submodule gitdir へ worktree を足すので、同一 tree からの
     並行投入は管理 metadata の writer を共有する (B[4] real)。tree を分ければ gitdir も分かれる。
   - `--repo-root` は `PBS_O_WORKDIR` を変えない。**投入時の cwd がそのまま job の REPO_ROOT
     になる** (B[7] real)。各 submit-tree へ `cd` してから投入し、成果物はその tree の
     `output/` に着地する (B[6] real)。
   - 取り込みは content-addressed 名 (`calibration-<sha256 先頭 16 桁>.json`) を使って
     **ファイル名と中身の sha256 が一致すること**を親が機械照合する。
     `output/env/pegasus/calibration/**` は tracked (757 file) なので、いずれにせよ親が commit する。
   - 条件を割って別ノードへ同時に流すというユーザーの既定方針とも一致する。
   - **参考実測 (撤回した中間案の根拠として残す):** 過去の certification job の実所要は
     3 分 25 秒 (`attempts/0_867876.nqsv/final-receipt.json` の会計 raw: Started 04:58:40 /
     Ended 05:02:05、queue 待ち 8 秒)。sweep は 3 点 (1M / 2M / 4M) x 3 rep で早期停止していた。
     2 時間は予約枠であって実所要ではない。rr95 / rr5 は working set が違うので点数が
     増えうるが、上限は 16M までの 5 点で 2 時間枠の内側である。

   (以下は撤回した中間案の記述)
   - `--repo-root` は `PBS_O_WORKDIR` を変えない。**投入時の cwd がそのまま job の REPO_ROOT
     になる** (B[7] real)。したがって成果物は投入した tree の `output/` に着地する (B[6] real)。
     投入の直前に wave worktree へ `cd` する。
   - job body は投入元 repo の CCBench submodule gitdir へ worktree を足すので、同一 tree からの
     並行投入は管理 metadata の writer を共有する (B[4] real)。直列ならこれが起きない。
   - **親は当初「別 submit-tree で並行 + 取り込み」と裁定したが、実測で撤回した。**
     過去の certification job の実所要は **3 分 25 秒**である
     (`attempts/0_867876.nqsv/final-receipt.json` の会計 raw: Started 04:58:40 /
     Ended 05:02:05、queue 待ち 8 秒)。sweep は 3 点 (1M / 2M / 4M) x 3 rep で早期停止しており、
     2 時間は予約枠であって実所要ではない。**2 本を直列にしても合計 10 分程度**なので、
     別 tree + 複写という余計な機構を持ち込む理由が無い。直列なら成果物は wave tree へ
     直接着地し、複写の照合段も不要になる。
   - ユーザーの既定方針「計測は条件を割って複数ノードへ同時投入する」は、1 ノード直列で
     何時間も流すことを却下したものである。数分の job 2 本はその射程外と判断する。
   - **rr95 / rr5 の sweep が balanced より多くの点を要する可能性は残る** (working set が
     workload で変わる)。その場合でも上限は 16M までの 5 点で、2 時間枠の内側である。
   - `output/env/pegasus/calibration/**` は tracked (757 file) なので、着地した成果物は親が commit する。
5. **B[8]: 投入直前に queue state を親が確認する。** `qstat -Q` の rc だけでは足りない。
   新 gate は作らず、親が本文を読んで `gen_S` が ENA/ACT であることを確かめる。
6. **A[9] / B[2]: 「95 を拒否」テストの置換は検出力を落とさない。** 95 を正例へ移し、
   未登録値の parameterized 負例 + 副作用不在 + 伝播検査を併置する。既定 rr50 の pin は残す
   (B の pin 閉包表が「段 2 に欠落」と指摘した項)。

## real だが scope 外 (実装しない・記録する)

- **A[1]: `orchestrator/calibrate.py --certify` 自体には rratio の allowlist が無い。**
  正しい receipt と binary を用意して CLI を直接叩けば、任意の rratio で accepted JSON を
  登録できる。**これは本 wave が作る穴ではなく、既存の設計である** (balanced 2 件も同じ経路で
  作られている)。CLI 側へ allowlist を新設することは、依頼が明示的に scope 外とした
  「仮想リスク向けの gate の追加」に当たる。**限界として insight と decisions に明記し、
  「受理集合が 5 値に閉じている」とは謳わない** — 閉じているのは sanctioned な 2 shell 経路だけである。
- **A[6]: `report.py` の "正当な selection" は D15 の数値関係を独立検証していない。**
  `lower_bound_selected` と `cache_floor_warning` しか見ておらず、`l3_multiple` と
  `working_set_ratio` が内部矛盾でも accepted になりうる。既存 producer を信頼する現行設計の
  弱点で、本 wave の allowlist 拡張が緩めたものではない。backlog。
- **B[12]: `local-ok` の evidence は `legacy-admitted (未実測)` である。**
  「安全性が実測済み」とは書かない。

## refuted 所見

A[2] (公式経路では非 canonical 字面は通らない — ただし A[3] の runtime 検査は入れる)、
A[5] (rr95/rr5 で accepted 条件が無効化される経路は無い)、A[7] / B[10]
(`cli.py:913` の `ratio in ("20","80")` は calibration observation capability の発行条件で、
quality / schema / publish のどの述語も参照しない。rr50 が capability 無しで accepted である
事実と整合する)、A[8] (env_contract は directory を探索せず path + sha256 で固定するので、
新 record が既存 lock の参照先を静かに変えない)、A[13] (P3 は一般化していない)、
A[14] (F660 は該当しない)、B[5] (`/scr` の直接衝突は無い)、B[9] (request ID 形式は現行で通る)。

## evidence gap の解消 (A[15] / B[11] — 親が実物で確認した)

`test_pegasus_calibration_workload.py:429-446` が `95` を rc=2 で拒否することを exact に要求する
こと、`tools/pegasus/README.md:125-140` の実在、`tools/pegasus/admission_registry.json:334` の
`submit_certify.sh` = `local-ok`、`output/env/pegasus/calibration/**` が git tracked (757 file)
であること、`cli.py:905-925` の capability 条件を、親が worktree の実物で確認した。

## 変異事前登録 (DW-M01)

実装前に登録する。期待 node は実装後の probe (全件 SURVIVED 登録) で確定し、
差異は erratum として台帳へ残す (DW-M08)。

| ID | 位置 | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `submit_certify.sh` の rratio 比較 | `"95"` の枝を削る | KILLED | 95 を拒否できる層は他に無い (job body は submitter を通った後) |
| M2 | 同上 | `"5"` の枝を削る | KILLED | 同上 |
| M3 | 同上 | 受理集合へ `"51"` を足す | KILLED | 未登録値の負例と exact 集合検査が同時に赤になる |
| M4 | `certify_calibration.sh` の rratio 比較 | `"95"` の枝を削る | KILLED | 両 shell 一致検査だけが片側拡張を捕まえる |
| M5 | `submit_certify.sh` の gate 直前 | `RRATIO=${RRATIO#+}` を挿入 | KILLED | `+5` の runtime 負例だけが捕まえる (静的 literal 抽出は緑のまま) |
| M6 | 同上 | `RRATIO=$((10#$RRATIO))` 相当の先頭 0 除去を挿入 | KILLED | `05` の runtime 負例だけが捕まえる |
| M7 | `README.md` の whitelist 記述 | 旧 3 値へ戻す | KILLED | docs pin 検査だけが捕まえる |

M5 / M6 は「テストの検出力そのもの」を対象とする変異である。SURVIVED なら A[3] の指摘が real で
あったことの証拠になるので、その場合は fix でテストを強化してから再走する。

## 段 5 の分割

実装子 1 本。実装子の編集面は `tools/pegasus/submit_certify.sh`、
`tools/pegasus/certify_calibration.sh`、`orchestrator/tests/test_pegasus_calibration_workload.py`
の 3 file。所有を割る利得が無いので単一単位とする。

`tools/pegasus/README.md` は **D95 決定 2 の実装面ではない** (`tools/` 配下だが Markdown)。
したがって親が直接編集する。ただしテストがこの file の字面を exact に pin するため、
**親が先に README を編集してから実装子を起動する**。そうしないと子が書くテストの期待値と
docs の実体が食い違い、DW-S05-C の「期待赤」を無用に作る。子には README の絶対 path を渡し、
brief の引用ではなく**実物から**逐語を取らせる。
