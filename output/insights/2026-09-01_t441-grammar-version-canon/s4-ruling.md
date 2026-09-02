# 段 4 裁定 (親) — [T-441] D901 条項 2・3

base: local main `265aa16e3ac2cb004ade3bbcb3fbf18775007c4f` (wave 中の docs-only 前進を ff-only で取り込み済み)
裁定 inbox 再走査: 新規 D1379〜D1394 を確認。backoff 文法に関わるものは無く、scope を覆さない。

## 親の前提の裁定

- **P1 (版は hole を持つ campaign に限定) — 採用。ただし実装形は変更する。**
  path 判定 (`include/backoff.hh` の dirty) では campaign 帰属を表せない。段 3 の 2 レンズが
  独立に、同 path を材料化する別 producer (`backoff_extended_sweep.py:54-64,193-225`、
  `b10_backoff_shape_sweep.py:83-89,674-746`) を名指しした。**campaign 由来の明示的な版を
  渡す**形に替える (下記 R-3)。
- **P2 (正準化は台帳記録側だけ) — 撤回。** プラン子と段 3 の両レンズが独立に、台帳併記だけでは
  source bytes が分かれたままで `src_token` / variant id / cache key の分裂が残ると指摘した。
  D901 条項 3 の理由 (「certified 選択の母集合を汚す重複」) を達成できない。
  **13 段の受理判定を全部通過した後に、材料化するソースを正準形へ書き換える**案 (プランの (c))
  を採用する。拒否された候補には触れないので受理集合は動かない。
- **P3 (版定数は文法 module に置き rule_id の `.v1` と独立) — 採用。** 異論なし。
- **P4 (新規 test file) — 撤回。** 実測で T-1999 の `test_p3_s4_loop.py` 側 hunk は 40-102 行
  (import と helper 1 個) に限られ、本 wave の編集は 212 行以降で衝突しない。既存 file を使う。
  ただし top-level import 群は T-1999 の面なので触らない (R-9)。

## 所見の裁定

### real・採用 (must-fix)

- **R-1 (sol F-03 / luna F-01 前半):** 正準化は受理後の材料化で行う。P2 撤回のとおり。
- **R-2 (sol F-05 / luna F-05):** 版の producer を 1 本にする。`cfg.search_config` の版と
  実行中 module 定数 `BACKOFF_GRAMMAR_VERSION` が一致することを build / WAL の前に exact に
  強制し、不一致は fail-closed で停止する。identity・WAL・source/cache がすべて同じ 1 つの値を
  読むこと。
- **R-3 (sol F-06 / luna F-02):** source/cache への版束縛を path 判定でやらない。
  `run_campaign(cfg, ...)` → `pipeline.evaluate(...)` → `source_digest.resolve_evidence()` /
  `resolve()` / `src_token()` へ **keyword-only・既定 `None` の追加引数**で campaign 由来の版を
  渡す。既定 `None` は現行と 1 byte も変えない。`run_campaign` の呼び出し 241 箇所、
  `resolve_evidence` の 35 箇所は既定により無改変で済む。呼び出し規約を変えるので、実装子は
  全呼び出しを数えて既定経路の bytes 不変を確認すること (DW-C01)。
- **R-4 (luna F-03):** 新しい WAL 版検査を `wal._validate_attempt_topology()` の中へ置き、
  全 caller を一度に閉じる。プランが列挙した 5 箇所への個別配線より**行数が少なく**、
  `artifact_admission._inspect_campaign()` 経由の正式 admission も同時に閉じる。
  個別配線案は採らない。
- **R-5 (sol F-07 / luna F-04):** 固定 id を 2 種に分けて扱う。
  - **更新する (現行 `default_cfg()` から再導出される 4 件):**
    `test_p3_s4_loop.py:2964,2967` の `2cd75697` / `9f43a5b8`、
    `test_p3_b4_closed_critic.py:3070-3071` の `ad0444da` / `8700ee8e`。
    期待値は実装から自己導出せず literal で固定する。
  - **触らない (歴史記録・別 driver):**
    `test_artifact_admission.py:84-88,188-190` の `0b53a387` と `LEDGER_RAW_SHA256`、
    `test_critic.py:582-590`、`test_campaign.py:337-360,685-714` の backoff-sweep 群、
    `s1_expected_goldens.py:253-258,315,370,437-443`。
    絶対規律 7 と D942 の非遡及により、1 byte も動かしてはならない。
- **R-6 (sol F-02):** 正準化が文法判定より前へ動く変異を殺す注入点は、合成経路で
  `statement-count` に到達する候補 (`double now_backoff = 20; (void)0;`) を使う。
  `test_p3_s4_loop.py:4630-4686` は HOLE_ESCAPE / HOST_EFFECT までしか到達せず前段に隠れる。
- **R-7 (sol F-09):** helper 直接呼び出しで、**異なる 2 つの raw digest が同じ版でも異なる
  token になる**ことを固定する。これが無いと raw digest を pre-image から落とす変異が生き残り、
  別ソースが同一 cache key へ alias する。
- **R-8 (luna F-07):** 版導入前の非-stock cache が再利用されないことを固定する。
  unbound raw token と bound-v1 token が異なり、旧 key への fallback 探索が無いことを、
  legacy `cache_key()` と `_v2_identity()` の両方で検査する。
  「v1 は素通し、v2 以降だけ版付き」の誤実装が通る計画になっていたため必須。

### real・採用 (should-fix)

- **R-9 (luna F-09):** cache 検査に必要な `buildcache` は top-level import 群に足さず、
  当該テスト内で local import する。top-level は T-1999 の編集面である。
- **R-10 (luna F-08):** `_critic_view()` (`test_p3_s4_loop.py:159-166`) は record を書いた後に
  lock を書くため、`default_cfg()` が versioned になると既存 reject/critic テスト群の
  `BUILD_START` に版 field が無く新 validator が拒否する。fixture を
  「版あり lock を先に seed する production 形」と「版 key の無い legacy lock を明示する形」に
  分離する。**既存 WAL への backfill で直してはならない。**
- **R-11 (sol F-04):** `value=20` + raw `0x14` + canonical source `20` + `BACKOFF_FIXED=20` を
  **一続きに**固定するテストを 1 本置く。分割された検査では配線ミスを取り逃す。

### real だが scope 外 (実装しない・裁定パッケージへ)

- **R-12 (luna F-01 後半):** `diffq_variant_id()` は拒否候補の raw implementation を hash する
  ため、`20` と `0x14` の拒否は別 token のまま残る。**これは real な観察である。**
  しかし本 wave では実装しない。理由は 3 つ。
  1. D901 条項 3 の理由は「certified 選択の母集合を汚す」であり (`rulings-verbatim.md:33-39`)、
     拒否候補は母集合へ入らない。
  2. 拒否候補の literal を正準化するには、**文法に落ちた入力**に対して値抽出器を走らせることに
     なる。絶対規律 2 が守る面をわざわざ広げる方向であり、R-6 が塞ごうとしている
     「正準化が判定より前に来る」型と同じ危険を招く。
  3. DW-G05 の成果物影響を書くと、影響は critic への診断入力の重複だけで、certified 成果物の
     値・受理集合・参照を変えない。よって must-fix の条件を満たさない。
  版を `diffq_variant_id` の pre-image に足すこと (プラン項目 3) は採用する。これは束縛であって
  正準化ではない。

### 不採用

- **R-13 (luna F-06 — 条項 2・3 を 2 つの論理 commit に分ける):** 不採用。
  1. ユーザー引数が「版束縛と数値正準化を同じ変更単位に含めること」と明示している。
  2. D942 が却下したのは **D836 の wave に**条項 2・3 を含めることであり、T-441 では
     両者が依頼そのものである。D1034 はそれを追認した。
  3. 両者は同じ `src_token` を動かすため、分割した中間 commit が赤になる。段 7 は commit 時点で
     テストが通ることを要求する。
  luna の成果物影響は「切り戻しの粒度」であり、値・受理集合・参照を変えない。DW-G05 により
  must-fix の条件を満たさないので nit へ落とす。

### 適合確認 (修正不要)

sol F-01・F-10・F-11・F-12・F-14・F-15、luna F-10・F-11。
sol F-15 の指摘どおり、親が brief に書いた「16 件」は不正確である。
`test_campaign.py` 全体で 16 行が該当し、`:337-360` の範囲には 15 literal がある。
sol F-12 の指摘どおり、親の実測は `validate_backoff_implementation()` の受理までしか示さず、
production の value/literal 一致検査は別経路である。scope の結論は変わらない。

## 変異事前登録 (DW-M01、実装前に凍結)

各変異は単一理由性を確認済みか、確認手順を添える。KILLED 期待の node は fix 後 (DW-M07) に
anchor を再検証して確定する。

| # | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M1 | `BACKOFF_GRAMMAR_VERSION` を定義するが `default_cfg()` の `search_config` に入れない | KILLED | exact key 検査 + campaign id 検査が前後に無い |
| M2 | campaign id にだけ版を入れ、source/cache へ渡さない | KILLED | R-8 の cache 検査が唯一の判定層 |
| M3 | cfg の版と module 定数の一致検査を外す | KILLED | R-2 の gate が唯一。意図的に版をずらした cfg を入力する |
| M4 | WAL writer が版 field を書かない | KILLED | versioned writer の E2E が唯一 |
| M5 | WAL reader が版欠落を許す (writer は正常) | KILLED | 手作りの欠落 record を replay と duplicate reader へ入れる |
| M6 | 正準化 helper を実装するが `quarantine()` の最終 `edited_text` に配線しない | KILLED | 返却 bytes と実 file bytes の検査が唯一 |
| M7 | 正準化を WAL 記録だけに留め raw source を残す | KILLED | canonical file bytes + source token の検査が唯一 |
| M8 | 版束縛 token の pre-image から raw digest を落とす | KILLED | **前段に隠れる。** helper へ 2 つの異なる digest を直接注入する (R-7) |
| M9 | 正準化を 13 段より前へ動かす | KILLED | **前段に隠れる。** `double now_backoff = 20; (void)0;` を合成経路で使う (R-6) |
| M10 | `STOCK` にも版を足す | KILLED | exact `STOCK` token / cache golden が唯一 |
| M11 | 版を上げたとき `backoff-grammar.*.v1` の rule id も変える | KILLED | 既存 rule corpus が固定値で捕える |
| M12 | 版なし旧 cache key への fallback 探索を残す | KILLED | R-8 の検査が唯一 |

冗長 gate と判明した変異は `DW-M03` に従い単独変異の証拠から外し、明記する。

## 承認外の過剰拒否の正例 (受理集合を動かさないことの正例)

受理集合を**広げも狭めもしない**ことを示すため、次を通る正例として登録する。

- `double now_backoff = 20;` / `20.0` / `1e2` / `001` / `0x14` / `024` / `0b10100` / `2'0` /
  `0x1.4p4` / `0xFF` — 全部これまでどおり受理され、材料化後の source は
  `double now_backoff = <10進整数>;` に収束する。
- `double now_backoff = 20; (void)0;` — これまでどおり `statement-count` で拒否され、
  正準化は呼ばれない。

## 段 5 の分割

実装子 1 本。版定数の producer と identity / WAL / source / cache の consumer が同じ契約を
跨ぐため分割しない (並行 fix は producer/consumer 契約を壊す)。

## 受入・実測環境

login node。性能測定も新規 C++ 実装も無い (luna F-11 が独立に確認)。
