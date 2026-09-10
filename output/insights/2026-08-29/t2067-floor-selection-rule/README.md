# [T-2067] 床値の使用測定を事前登録した決定的な選択規則で固定する

authority: none
default_effect: no-state-change

D1243 の実装記録である。状態の正本は worklog、採用済み判断は decisions とする。
本 wave は署名・nonce・一回性台帳・汎用の選択規則 framework を実装していない。

## 何が閉じ、何が閉じていないか

**閉じたもの (land 後に安全に主張できること)**

1. 同一 `(env_tag, proto8)` namespace に、共有 admission 台帳から導出した適格性が真である
   より早い official floor run が存在するとき、それ以外を g1 candidate へ渡すと拒否される。
2. selected run の path 起動時刻は、その run の launch certificate の `started_utc` と秒一致する。
3. g1 の `generation.floor` は、記録された `floor_source` blob の `floors` 投影と一致する。

**閉じていないもの (D1241 の advisory / non-certifying 上限を維持する理由)**

1. 値を見た後に、より早い official run を削除してから g1 を作る経路。
   台帳・署名を禁じた条件では、消えた事実を後から証明できない。
2. g2 以降の選択・投影。`_launch_validate` は generation 1 だけを受理する一方、
   loader と s8c は g2 を受理する。
3. load-only consumer への選択強制。loader は historical 経路と両立させるため投影だけを検査する。
   `verify_floor_bytes` 経由の s8c publish metadata は選択規則を強制しない。
4. launch certificate の実時間性。整合する certificate / journal / admission を再構成する攻撃。
5. s8c official table の production final claim 配線 (公開関数の production callsite 0)。

## 規則

`earliest-eligible-official-run-id/v1`。同一 `(env_tag, proto8)` namespace の official floor
result のうち、path の起動時刻 `<TS>` が最小の**適格**な run だけを強い主張に使う。

- namespace の絞り込みは path の `proto8` だけで行い、earlier result の内容から
  `protocol_sha256` を読まない。`proto8` 衝突は過剰包含 (拒否側) に倒れるので安全側である。
- 起動時刻は launch certificate 発行時点で確定するため値盲である。

## 適格性の権威を自己申告に置かなかった理由

段 2 の初版は earlier result の `eligible_for_refreeze` を**自己申告のまま**読んで
競合集合から外していた。段 3 のレンズ A がこれを real と判定し、親も採用した。
選ばれなかった run の 1 field を後から書き換えるだけで required run が動くためである。

現行実装は `s8b_holdout_admission.inspect_floor_holdout_admission_evidence` が共有 admission
台帳から**再導出**する `derived_eligible_for_refreeze` を権威とする。既存機構の再利用であり、
新しい台帳は作っていない。

## 「最も早い result.json をそのまま必須にする」案を却下した理由

親は一度この単純化を検討したが却下した。**D1124 の再発だからである。**

`s8b_floor_campaign._derive_refreeze_eligibility` は
`official AND resume_dir is None AND 非既定 seam なし` を適格とする。すなわち
**resume した run は official path に result.json を書きつつ適格ではない**。
resume は D1124 が守った途中死からの復旧経路そのものであり、これを競合に数えると
「1 度落ちたらその protocol では二度と強い主張ができない」という、D1124 が撤廃した停止構造が
artifact 側で復活する。D1124 の逐語は、この型の厳密さが床値実測を 5 日完全停止させた実害を
記録している。

途中死そのものは D1124 の記述どおり成果物を残さないため、result.json 不在として
自然に競合集合から外れる。

この却下理由は正例変異 `treat-all-earlier-eligible` で機械的に守っている。

## 起動時刻の意味を閉じた経緯

段 3 のレンズ A が「candidate 経路は launch certificate を検証しない」と指摘し、親が現物で確認した。
`s8b_holdout_freeze` は path 文法の `parse_official_run_path` しか import せず、
既存 fixture は certificate に `b"{}"` を書いていた。したがって `<TS>` はただの名前であり、
検証せずに最小 run_id 規則だけを入れても規則は装飾にとどまる。

レンズ A の処方 (主張を下げる) は採らなかった。同じ束縛は
`s8b_ratified_freeze.py` の equality chain に
`("official-path.run_id.ts", "cert.started_utc(second)")` として既に宣言され、
full launch validation で強制されている。**その述語を candidate へ再利用した。**

## 層の配置と、loader を H-pure に保った理由

| 層 | 置いた検査 |
|---|---|
| candidate (`build_v2_g1_candidate`) | 選択 identity + 起動証明書 / path 起動時刻の秒一致 |
| loader (`_verify_generation_semantics`) | 投影 equality のみ (H-pure) |
| `_launch_validate` の current 分岐 | 選択 identity |

loader に選択 identity を置くと、`_validate_floor_inputs` が current build admission policy を
無条件に使うため、`reverify_published_freeze` が historical semantics を選ぶ前に落ちる。
これは規律 7 と D1245 に反する。したがって loader は H-pure に保ち、選択強制は
`LaunchValidatedFreeze` 分岐にだけ置いた。`ReverifiedFreeze` には課さない —
過去の g1 は規則制定前の成果物であり、現行コードとの差だけを無効化理由にしない。

candidate 側の投影 equality は構造上恒真 (candidate の `floor` は検証関数の戻り値そのもの) なので
置いていない。

## 実装しなかったもの

- generation document への `floor_selection_rule` field。単一 legal 値で dispatch を伴わなければ
  文字列存在検査にすぎず (D1242 が否定した型)、dispatch を伴えば汎用 framework への第一歩になる。
- frozen generator blob の版文字列 exact 1 回 scan。同じ理由。
- namespace 全体の H tree / worktree exact 一致。selected より**後**の未追跡 run 1 件で
  既存 consumer を止める過剰拒否であり、成果物の値も参照も変わらない。
- 未追跡 earlier run の HEAD 不在は、既存の `_measurement_closure` が captured HEAD blob を
  要求することで既に閉じている。新しい commit barrier は作っていない。

## 段 6 で見つかった実装欠陥

- **nofollow が check-then-use だった** (レンズ A、must-fix)。各 component を `lstat` してから
  後で path で開き直すため、検査と使用の間に親 directory を symlink へ差し替えられた。
  同 module に既にあった dirfd 走査 (`_write_v2_candidate_create_only` の
  `os.open(component, O_NOFOLLOW|O_DIRECTORY, dir_fd=parent_fd)`) を再利用して閉じた。
- **最重要の正例が stub だった** (レンズ B、must-fix)。`positive-resumed-earlier` が
  `_derive_floor_selection_eligibility` を monkeypatch で False に差し替えており、機構を
  通っていなかった。earlier run の manifest / journal / admission 台帳を実 producer で作り、
  stub なしで production の candidate builder を通す形へ直した。
- **選択層と導出層をつなぐ引数配線が未検証だった** (親の所見)。earlier の導出へ selected 由来の
  値を渡す取り違えが生存した。selected と earlier で run id / run path / manifest hash を
  別値にする検査を足した。
- launch 側が選択関連の全例外を `floor-selection-rule-mismatch` へ潰していた (レンズ A、should-fix)。
  mismatch / underivable / それ以外の 3 分類へ分けた。
- 親が **refuted** としたもの: `_validate_floor_inputs` の 6 tuple → 7 tuple が契約違反という所見。
  module private で caller は 1 件、返す `path_info` は関数内で既に計算済みの同一オブジェクトであり、
  再 parse を足すと run-id の解釈が 2 か所に増える。段 2 プランが明示的に避けた形なので据え置いた。

## 焦点走が捕まえた既存の内部矛盾

新設した投影 equality により、oracle の g1 fixture 24 件が落ちた。原因は
`s8b_v2_freeze_fixture.per_pair_floor()` の**合成定数 (0.01)** で `document["floor"]` を上書きし、
同じ文書が記録する `floor_source` の result の `floors` と無関係にしていたことである。
これらの g1 は元から内部矛盾しており、新検査が初めて可視化した。
fixture 側を正規形へ直した (合成 floor の上書きをやめ、必要な budget だけを足す)。
**期待値の緩和ではない。**

この 24 件は「変更した test file」だけの焦点走では出ない。`DW-O26` に従って変更した
production file の consumer test を参照関係で引いたために出た。

## 実測

- 焦点走 (13 file、`python3 tools/run_tests.py`): **1185 passed / 17 skipped / 赤 0**、106.58 秒、rc=0。
  対象は変更した 8 file と、変更 production file の consumer test
  (oracle driver / manifest / report、holdout admission、floor stats)、および一覧走査系
  (official perf closure、frozen artifacts、protocol builder、campaign import invariant、
  repo scan invariant)。
- 変異 matrix: `tools/mutation_harness.py`、`--runner-mode dispatch`、HEAD `31426fb9a` 束縛。
  **baseline PASSED、9/9 KILLED、期待 node 完全一致、SURVIVED / MISMATCH / TIMEOUT 0。**
  期待 node は 2 回の probe 走 (全件 SURVIVED 登録) で観測した完全集合を再登録した。

| 変異 id | 種別 | 期待 node 数 |
|---|---|---:|
| `min-to-max` | negative | 6 |
| `drop-candidate-selection` | negative | 10 |
| `drop-cert-time-binding` | negative | 2 |
| `use-reported-eligible` | negative | 3 |
| `underivable-to-skip` | negative | 1 |
| `drop-loader-projection` | negative | 1 |
| `drop-launch-selection` | negative | 2 |
| `historical-policy-leak` | negative | 1 |
| `treat-all-earlier-eligible` | **positive** | 1 |

`treat-all-earlier-eligible` は受理集合を縮小する wave の過剰拒否検出用正例である
(`DW-M01`)。落とすのは `test_v2_candidate_accepts_later_run_after_derived_ineligible_resume`
ちょうど 1 件で、D1124 の却下理由を機械で守る。

- `check_docs.py` rc=0、`check_codex_agents.py` rc=0、`git diff --check` rc=0、
  全史 provenance rc=0。
- 凍結 artifact は不変。`output/s8b-freeze/floor_protocol.json` =
  `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`、
  `output/s8b-freeze/holdout_freeze.json` =
  `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`。

## 未実走・実装していないもの

- floor 本走、oracle / 8c 本走、性能測定、qsub は 0 件。未実走を緑と扱っていない。
- official floor run は現 repo に 0 件である
  (`output/env/pegasus/calibration/s8b-floor-official/` が不在)。
  T-1942 の実測によれば、床値実測の投入の主経路は D1192 未実装により無条件で赤であり
  (job 952631 で再現、`output/insights/2026-08-29_t1942-floor-gate-compiler-input/`)、
  これが 0 件である理由を与える。したがって本 wave の正例・負例はすべて合成 fixture である。

## 動機の射程についての訂正

本項の優先度を上げた動機は 2026-08-28 の A-2 実走 (rr5 -46.3902%、rr50 -65.9080%、
outer status `reject`、`output/insights/2026-08-28_t2022-a2-certification-run/`) だが、
**その実走は s8b holdout floor を消費していない。** 同 README の「floor」は A4 noise floor で
別概念である。動機 (どの床値をどの規則で使ったかが論文の主張に直結する) は妥当だが、
A-2 実走を s8b floor の消費例として引いてはならない。

## scope 外 (ユーザー裁定へ返す)

上記「閉じていないもの」の 5 項目。とくに次の 2 つは設計択一である。

1. 削除された earlier official run を集合へ戻す authority を作るか、削除攻撃を残余として
   D1241 を維持するか。台帳・署名の禁止と両立する案は本 wave では見つかっていない。
2. g2 以降にも同じ規則と投影を課すか、g2 以降を non-certifying のままにするか。

## 逐語

段 2 プラン、段 3 敵対相談 2 本、段 6 敵対レビュー 2 本、段 5 実装子と fix 子 3 巡の報告は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2067-floor-selection-rule/` にある。
`verbatim/` に主要な 5 本を複製する。
