# [T-1871] 段 1 brief + 親プラン v1 (2026-09-20、dev-wave `dev-wave-t1871-nonenum-addendum`)

worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-addendum`
(branch `worktree-dev-wave-t1871-nonenum-addendum`、base = local main `42096593893670a12e1483f17423a207de89dfa6`、clean、submodule 初期化済み、開始 gate rc=0)

## 研究前進 (1 行)

旧 headline 主張 (D52) の復活条件が使う語「非列挙」を、ユーザー裁定 D1441 の操作的定義
(「固定予算の下で操作的に列挙し尽くせない」) で**事前登録の層に**固定する。完了判定 = 追補が着地し、
B-5 事前登録 (`docs/b5-generator-contrast-preregistration.md` 68〜71 行) と論文ストーリーが「D1441 で改められた /
定義の置き直しは未裁定」と食い違って書いている箇所に、事前登録側の正本を与えられる状態になること。

## scope

- **docs-only。** 追補 1 file + `docs/README.md` の地図 1 entry + `docs/phase3.md` の分離節 (285〜294 行) への pointer 1 文。
- scope 外 (引数で明示): 論文ストーリー次版、軸の実体化、B-1 再測定、仮想リスク向け gate / 検査 / 台帳の追加。
- 本 wave で加えて scope 外とするもの: 凍結成果物 (`output/s1-freeze/*.json`、`output/s8b-freeze/*.json`) の bytes、
  `orchestrator/` `tools/` 配下の一切、`docs/phase3-main-experiment.md` の bytes。

## 確定済みユーザー裁定 (逐語は `primary-sources.md`)

- **D1441 (2026-09-02):** 復活条件の「非列挙」を「固定予算の下で操作的に列挙し尽くせない」へ定義し直す。
  骨格が新しい状態を持つ案はこの軸では追わない。レンズ本数の数え方は規則にしない。段階 A の人間 gate はやり直さない。
- 引数 (本 wave の依頼): 上記を日付付き追補として `docs/phase3-main-experiment.md` 2026-07-12 追記の
  「非列挙のコード片軸 … が実体化し偵察が floor 超地形を確認した場合にのみ検証可能」に対して置く。
  拘束力ある事前登録なので**本文 bytes を書き換えず**、同文書の更新契約に従う追補形式。

## 段 1 で実測した、依頼の前提を覆す新事実

1. `docs/phase3-main-experiment.md` の現 sha256 `e544de1969dd4df13dc42aa3d165e22b70fab2ab399dc011baa46359727bea45` は
   凍結成果物 5 本 (`output/s1-freeze/known_axes_freeze.json` 623 行、`measurement_freeze.json` 742 行、
   `output/s8b-freeze/holdout_freeze.json`、`holdout_freeze.v2.g1.json`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`)
   に source 記録として埋め込まれている (key `D52 2026-07-12追記: read-heavy sk_ad事前固定`)。
2. **実走 (DW-O19 一時変異、復元済み):** doc 末尾に 1 行足すと production の `s1_known_axes_freeze.verify()` が
   `FreezeError: source sha256 不一致: docs/phase3-main-experiment.md` で赤。この verify は
   `orchestrator/campaign/s8b_oracle_driver.py` 515 行 (8b oracle の refusal `known-axes-freeze-verify`) と
   `s1_verify_extime_calibration.validated_target` (235 行) が実 root に対して呼ぶ。test では
   `orchestrator/tests/test_s1_known_axes_freeze.py::test_historical_current_use_matches_real_reconstruction` (1055 行) が同経路。
   `_HISTORICAL_CODE_PATHS` (864 行) は code 6 path だけを歴史扱いし、docs path は含まない。
   → **同 doc へ 1 byte でも追記すると、8b oracle は変更後の木で refuse し、受入全走は赤になる。**
3. 先例 `e5dfa84c6` (2026-07-16 追記) は doc 追記と同 commit で s1-freeze JSON の sha を「追随」させたが、
   その後 T-080 (2026-08-02) が `known_axes_freeze.json` の raw bytes を `KNOWN_AXES_RAW_SHA256` として code に pin し、
   holdout v2 g1 も同 JSON の sha256 を束縛する。追随は凍結 chain 全体の再凍結になる。
4. **D1789 (2026-09-08、D1441 より後):** 発効後の事前登録は文面の瑕疵でも bytes を書き換えず erratum で訂正する。
   却下案として「文面だけ直して sha を貼り直す」を明示。同型の先例 = `docs/backoff-policy-performance-preregistration-erratum-1.md`
   (凍結 v1 の bytes を 1 byte も変えず、別 file の正誤表を `docs/README.md` 49 行に登録)。
5. `docs/phase3.md` 290〜291 行が同 doc の更新契約を「元の本文を消さず、既知結果を開示した日付付き改訂だけを append-only で
   重ねる契約」と書く。file 内 append は 1〜4 により不可能になったので、append-only 契約の履行形は別 file の追補になる。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 追補の置き場 = 別 file `docs/phase3-main-experiment-addendum-1.md`。** `docs/phase3-main-experiment.md` は 0 byte 変更。
  依頼の「同文書に置く」から逸脱するが、依頼自身の制約「本文 bytes を書き換えず」「同文書の更新契約に従う」を
  凍結 chain と D1789 の下で満たす唯一の形。追随 (sha 貼り直し) は D1789 却下案そのもの、
  `_HISTORICAL_CODE_PATHS` への docs 追加は verifier の弱体化 (DW-STOP) で採らない。
- **(P2) 追補の拘束力ある本文は D1441 の決定 4 点の逐語だけ。** 「固定予算」の額・生成器・判定主体などの新規則は書かない
  (insight §6 択 a の「事前登録した生成器の試行予算では到達 truth-vector を覆い尽くせない」は出所・意図として非拘束で引用)。
  D1441 が「定義し直す」と言った対象 = 2026-07-12 追記 170〜171 行「非列挙のコード片軸 … 検証可能」の「非列挙」1 語。
- **(P3) 追補は復活条件の語義を定めるだけで、旧 headline の復活・D1012 の休眠 (B-5 対照・(a)〜(e))・D52 の (c') を動かさない。**
  D1441 の残り 3 点 (新状態骨格は追わない / レンズ本数は規則にしない / 段階 A gate はやり直さない) は
  この軸の段階 B 以降の扱いとして同じ追補に書く。
- **(P4) 承認は D1441 のユーザー裁定 (2026-09-02) と本 wave の依頼で足り、追補は land 時点で発効。** D1012 が求める
  「ユーザー承認を伴う日付付き発火 commit」の承認を追加で待たない。
- **(P5) 凍結成果物側は一切触らない。** 追補 file は凍結 doc の sha256 を本文に明記し、「同 doc の bytes は不変」を自ら宣言する
  (b10 erratum-1 と同形)。

## 不変条件

- `docs/phase3-main-experiment.md` の sha256 = `e544de19…` を段 6・段 7 で再実測し commit に含めない。
- `orchestrator/` `tools/` `output/` `hooks/` に差分 0。`python3 tools/check_docs.py` 緑。
- 追補は D1441 を超える規則・数値・発火を新設しない (規律 5 盛らない、DW-G05)。

## 成果物の形 (親プラン v1、file:line)

1. `docs/phase3-main-experiment-addendum-1.md` (新規、60〜90 行): 冒頭に対象 doc の path + sha256 + 「bytes 不変」宣言、
   §0 いつ・何を根拠に (D1441、insight §6 裁定 1〜4、[T-1871] 段階 B、依頼)、§1 対象箇所の逐語引用 (170〜173 行)、
   §2 追補本文 (D1441 4 点、拘束力の範囲、動かさないもの)、§3 出所と限界 (壁 1 が定義変更の理由、壁 2 は未解決、
   本追補で発火するものは無い)、§4 束縛 (この追補は凍結成果物に pin されない living 文書ではなく、D1789 の erratum 系列と同じく append-only)。
2. `docs/README.md` 19 行の直後に 1 entry: `phase3-main-experiment-addendum-1.md — 上記事前登録の追補 1 (D1441 …)`。
3. `docs/phase3.md` 285〜294 行の分離節末尾に 1 文: 「2026-09-20 以降、同文書の bytes は凍結成果物に pin されるため、
   日付付き改訂は `docs/phase3-main-experiment-addendum-N.md` へ置く (追補 1 = D1441)」。

## 並列分割方針

実装面 0 → Codex author 不要。段 2 plan は省略 (本 file の v1 を plan とする)。段 3 = 敵対相談 2 本 (read-only、lane luna、
レンズ = A: 正しさ境界・整合 / B: 実効性と過剰・削除)。段 5 = 親が docs を書く。段 6 = 独立 read-only レビュー 1 本
(一次資料からの再抽出を含む docs-only、DW-C00) + 受入全走。変異 matrix は実装面 0 で対象外 (DW-S04)。
受入・実測環境: 受入全走は `tools/dev_wave_wait.py acceptance --lease-optional` (Pegasus 計算ノード dispatch)。
