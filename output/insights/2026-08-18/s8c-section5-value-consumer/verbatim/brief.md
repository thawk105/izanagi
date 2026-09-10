# 段 1 brief — 8c 事前登録 §5「反復単位対比の判定パラメータ」欄の値を機械検証する consumer

## scope

- **実装面 (Codex author が書く)**
  - `orchestrator/campaign/s8c_preregistration.py`: §5 の欄別値制約を検証する経路を
    `_classify_section5_value` / `_parse_section5` の周辺へ足す。対象欄は
    `反復単位対比の判定パラメータ (H1 / H2: n・平均差の下限・差の標本 SD の上限)` ちょうど 1 欄。
    違反値は `FieldStatus.INVALID` と固有 `reason_code` を返し、`all_filled` が偽になることで
    `ActivationReport.effective` を偽 (= 本書は未発効) にする。
  - `orchestrator/tests/test_s8c_preregistration_core.py`: 正例・負例・production 経路の到達性。
  - 必要なら `orchestrator/tests/test_s8c_preregistration_invariant.py` に meta-test 1 本。
- **scope 外 (この wave では触らない)**
  - `docs/phase3-8c-preregistration.md` の本文・§5 の実値記入。
  - evidence contract JSON の `machine_checkable` 反転、条件凍結 record (世代 7 は t822 系が占有)。
  - 8b §10.1 の judge 本体・3 表の生成 (別 wave `t1352-c07-result-judge` の領分)。
  - §5 の他 8 欄の値制約 (累積ベンチ実時間欄は `t1363-c06-budget-consumer` の領分)。

## 確定済みユーザー裁定 (command 引数)

- 実装は Codex author (D95)。既存の「未記入は placeholder 語そのものだけ」「説明文や
  空でない container を値セルへ書かない」判定は緩めない。
- 規律 2 を緩める方向 (検証を素通しさせる既定値) は採らない。

## 親が測った事実 (brief の根拠。推測ではない)

1. 現行 `_classify_section5_value` は `` `{"n":"two"}` ``・`` `0` ``・`` `"anything"` `` を
   すべて `FILLED` にする (worktree で実行済み)。制約違反値が今日そのまま発効側へ通る。
2. 実 doc の当該欄は `UNFILLED / placeholder`。9 欄のうち `FILLED` は「検定 4 点」1 欄だけで、
   本書は現在も未発効である。
3. canonical JSON は key ソート必須。`{"H1":{"n":1,"delta_min":-5,...}}` は
   `noncanonical-json` で**先に**落ちる。テスト値は canonical 形 (key 昇順) で書くこと。
4. `_markdown(filled=True)` は全 9 欄へ同一値 `` `{"v":1}` `` を入れる。当該欄が INVALID に
   なるため、fixture を欄別値へ変える必要がある (呼び出しは 16 箇所すべて `_init_repo` 経由で
   `_markdown` 1 箇所に集約されている)。
5. `_classify_section5_value` / `_parse_section5` を名指しする pin は repo 内に無い
   (insight の過去記述のみ)。同 file を触る生存 branch も無い。t822 branch は main へ着地済みで
   `git diff --name-only main...worktree-dev-wave-t822-c02-receipt-v2` は空 (引数の重複検査に回答)。

## 不変条件

- `docs/phase3-8c-preregistration.md`、evidence contract JSON、generation record の bytes を
  1 byte も変えない (`protected_sha256` 不変)。
- 既存判定を緩めない。placeholder 判定・canonical JSON 要求・空 container / 空文字 / null の
  `UNFILLED`・非 code span の `INVALID` は現状維持。新経路は `FILLED` をさらに絞るだけで、
  現在 `INVALID`/`UNFILLED` の入力を `FILLED` へ昇格させない。
- 既定は fail-closed。未知 key・型不一致・数値でない値・欠落 block はすべて `INVALID`。
  「検証できない形だから通す」既定を作らない。
- subprocess を増やさない (`test_ccbench_spawn_sites.py:134` が `s8c_preregistration.py` の
  spawn site を `_git` 1 件で exact pin)。
- 新規 test file を作るなら `test_s8c_preregistration_invariant.py` の `WAVE_REQUIRED_PATHS` へ
  登録する。既定は既存 file への追記とする。

## 成果物影響 (DW-G05)

現行 checkout では本 wave 単独で certified 選択・レポート・台帳の値は 1 つも変わらない
(8c は未発効のままで、実走はまだ無い)。変わるのは**将来 §5 当該欄を記入したときの発効判定**で、
制約違反値のまま発効し不正な閾値で走った測定が本系列の試行に数えられる経路を塞ぐ。
8c §6 前提条件 7 は「§5 の判定パラメータの型・有限性・符号・単位・向きを検査する validator が
production 経路から到達可能でなければ本条件を充足しない」と名指しで要求しており、本 wave は
その validator の実体である (条件の充足判定を反転させるのは scope 外)。
実装しなければ、8b §10.2 の「現在の担保は欄が空であることだけ」という状態が続き、
当該欄は永久に記入不能のままになる。

## provisional 裁定 (P#。親の暫定であり段 3 の攻撃対象)

- **(P1) 受理形**: 値は object で exact 2 key `"H1"` / `"H2"`。各 block は
  `delta_min` / `direction` / `n` / `sd_max` / `unit` の exact key set。余剰・欠落は `INVALID`。
- **(P2) 制約**: `n` は bool でない int かつ 2 以上。`delta_min` は bool でない有限数かつ > 0。
  `sd_max` は bool でない有限数かつ >= 0。`unit` と `direction` は非空 (空白のみでない) 文字列で
  両方必須 (= 単位と向きの同時固定)。H1 と H2 で unit/direction の一致までは要求しない。
- **(P3) dispatch**: 欄名 exact 一致の table で validator を引く。当該欄以外の 8 欄は現行挙動のまま。
  table は将来の兄弟 wave が entry を足せる形にする (merge 面を 1 箇所へ寄せる)。
- **(P4) 欄名消失時の fail-open**: 欄名が変われば §5 欄名 hash が変わり凍結 chain が
  未発効へ倒すため production の追加署名は増やさない。代わりに meta-test 1 本で
  「validator の key が実 doc の §5 欄名集合に実在する」を pin する。
- **(P5) reason_code**: 違反種別ごとに固有コードを返す (規律 3: なぜ壊れたかを構造化して返す)。
  単一の総称コードには潰さない。

## 分割方針

編集面が 1 module + 1〜2 test file と小さいため、段 5 は Codex author 1 単位 (並列分割なし)。
段 3 は異なるレンズ 2 本、段 6 は敵対レビュー 2 本 + 焦点再レビュー 1 本。
本 wave は受理集合を変え正しさ防壁 (発効判定) に触るため、軽量版ではなく段 2・3・6 を省かない。
