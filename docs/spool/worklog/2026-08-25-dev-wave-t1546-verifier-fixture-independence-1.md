---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1546-verifier-fixture-independence
seq: 1
title: [T-1546] verifier fixture の独立性を 1 thread 自明直列 (g6) と broken-Silo 負例 (r8) で担保した (コード + docs、branch worktree-dev-wave-t1546-verifier-fixture-independence、変異 matrix = 新 HEAD 9/9 KILLED・旧 HEAD 6/7 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー裁定は 2026-08-23 の /rulings 全件で確定済みだった — **(a) 1 thread の自明直列 trace と
  (c) broken-Silo の負例を採り、(b) の独立 checker は見送り**。段 4 直前に裁定 inbox を再走査した
  ところ wave 開始後に main が 15 commit 進み新しい /rulings 記録 (`239cfc31` / `aee9201c`) が
  着地していたが、**どちらも T-1546 に触れていない** (持ち越し一覧の番号更新だけ) ことを確認した。
- 設計判断は {{D:verifier-fixture-independence-scope}}。
- **素材は再生成でなく再現できた。** `dev-wave-t756-fn2-trace-v2` の job dir に submodule pin と
  同一 commit (`511c9538`) の clone と gflags / glog の static install が現存し、trace build は
  17.92 秒で通った。1 thread 走行と broken-Silo 走行はどちらも login node で完結した。
- **壊しの効き目を対照実験で確かめた。** 同じ clone を複製し patch の有無だけを変えて、
  同じ機体・同じ日・同じ cmake 呼出し・同じ argv で走らせた。壊しあり 4/4 が
  `non-serializable` (巡回 4〜7 本)、壊しなし 4/4 が `serializable` (巡回 0 本)。
  **「唯一の原因」とは書かない** — 走行ごとのスケジュールと操作列は対応しておらず、
  patch 自体が abort と timing を変えるからである。
- **段 3 の敵対相談で親の主張が 5 件崩れた。** 最も重いのは
  「broken-Silo だから赤」は「非直列化可能な実行を*許しうる*」までしか言えず、
  **固定 bytes に閉路がある根拠まで verifier 由来だった**という指摘である。
  親は `fixtures/README.md` へ書く前に、**verifier を一切使わず生の行だけから巡回 {T3, T7} を
  再導出**した (wr は T3 の書いた版を T7 が読む、rw は T7 が読んだ genesis 版の直後版を T3 が書く、
  版の直後関係は 4 file 全行の悉皆走査で確かめた)。これは案 (b) ではない — repo へ checker を
  置かず 1 回限りの読み取りで、結論だけを docs の散文に残す。
- **親自身の誤りを 4 件記録する。** (1) brief の scope 1 で「緑 fixture が『常に緑と答える』退行を
  撃つ」と方向を逆に書いていた。(2) 「g5 と prefix 述語が完全一致」は誤りで、g5 は
  `tid <= 1000`、新 fixture は `tid <= 200` である。(3) fixture dir を「17」と数えていたが
  正しくは既存 16 + 新規 2 = **18 dir / 27 file** である。(4) 受入の verify 増分を約 26ms と
  見積もったが、閉じた framing node が各 dir を再検証するため g6 は 2 回・r8 は 3 回検証され、
  静的下限は **約 34.4ms** である。いずれも段 3 / 段 6 のレビューが指摘した。
- **段 6 で「変異が構造 assert の実効性を証明しない」構造が見つかった。** g6 node は
  先に `assert res.serializable` を置いていたため、逆向き辺を注入する変異はそこで停止し、
  裁定が「殺す本体」と定めた辺方向 assert は一度も評価されなかった。node は KILLED になるので
  受入は通るが、**死因の帰属が事実と違う**。構造解析を verdict 系より前へ移して直した。
- 失敗 2 件は {{F:parent-overconstrained-uniqueness-reddened-meta-test}} と
  {{F:frozen-pre-registration-diverged-from-own-spec}}。
- **変異は新旧両 HEAD で回した (`DW-M08`)。** 新 HEAD `0f70f46d` は baseline PASSED (32.205 秒)、
  registered 9 / KILLED 9 / SURVIVED 0 / MISMATCH 0。旧 HEAD `2ff5d8e4` は baseline PASSED
  (32.026 秒)、registered 7 / KILLED 1 / SURVIVED 6 / MISMATCH 0。
  **純増検出力は 6 本** — 「常に直列化可能と答える」「常に非直列化可能と答える」
  「グラフを見ずに認証する」「rw 辺を張らない」「壊れた理由を空にする」
  「外部 JSON の異常一覧を空にする」が、旧 HEAD では誰にも検出されなかった。
  理由から key を落とす変異だけは既存 `test_structured_report_has_edge_detail` も撃つため
  両 HEAD で KILLED になり、これは予測どおりである。
- **枠を分けて記録する** — kill 枠 4 本、diagnostic sensitivity pin 枠 3 本、bytes pin 枠 2 本。
  後 2 枠は受理集合を変えないので kill の点数へ合算しない (`DW-M08`)。
- **単一理由性は規模条件で作った。** census 実測で手製 fixture は最大 5 txn、g5 は 1,345 txn、
  g6 は 200 txn、r8 は 288 txn なので、`250 <= n <= 350` は r8 だけを選ぶ。
  g6 側は当初 `n == 200` だけにしていたが、任意入力 `output/runs/silo-sample` が
  200 txn で置かれた機体では期待 node 集合が変わるとレビューが指摘したため、
  `len(versions) == 131` を足した fingerprint へ強め、**g6 だけに一致し他 17 dir で外れる**ことを
  実測で確かめた。
- **段 8 の自己改善は 3 候補すべてを裁定し、dev-wave docs は 1 行も編集しなかった。**
  (1) `DW-O01` の「effort の caller 指定は不可」は実測と逆で、`dev_wave_codex.py` は
  plan / consult では `--reasoning` を必須にする (未指定は rc=2)。**是正は予算で入らない** —
  31 bytes の訂正を実際に当てて測ると `docs/dev-wave/**` の L1.5 unique footprint が
  9,596 > 9,566 bytes で赤になり、さらに `DW-O01` の dispatcher route 行の構造 pin も破れた
  (`DW-O19` に従い `git checkout --` で復元し、commit との一致を確認)。
  誤りの是正であって「あると親切」ではないので、D730 の原則落ちではなくユーザー裁定へ返す。
  (2) fix 子が実走できず親の直接実走だけが赤を捕まえた件と、(3) 親の指示文が過剰制約になった件は、
  failures 台帳へ routing した (恒久対応も同エントリに書いた)。(2) の「親が commit 前に焦点 node を
  最低 1 回実走する」という新義務は**実測 1 例**であり、D730 の基準 (独立 3 例) を満たさないので
  本 wave では実装しない。
- 子の工数: plan 1 / consult 2 / author 1 / review 2 / fix 2 の計 8 本、いずれも
  `gpt-5.6-sol` / effort xhigh。plan 初回は `--reasoning` 未指定で rc=2 になり 1 本無駄にした
  (`dev_wave_codex.py` は plan / consult では必須。`DW-O01` の文面は段によって逆である)。
  実装子と fix 子はいずれも焦点 pytest を実走できず、**親が素の Python で test 関数を直接呼ぶ
  焦点実走を行った** (login node では pytest が guard に拒否される)。

## 次の一手差分

### 完了

- [T-1546] (a) 1 thread の自明直列 fixture と (c) broken-Silo の負例を実 emitter の bytes で置き、
  独立に決まる述語と verifier 由来の golden を assert の節で分け、負例側の構造化出力を
  内部 object と外部 report の両方で exact に固定した。変異は新旧両 HEAD で回し、
  純増検出力 6 本を機械で示した。
  remaining: none
  base: b56541516e068522e07506bd479fabb4a9c9618c381b08f49bc4d09733d84b7d

### 新規

- {{T:devwave-o01-reasoning-wording}} **P3・ユーザー裁定待ち**: `DW-O01` の
  「effort は … caller 指定は不可」は plan / consult では実測と逆である
  (`dev_wave_codex.py` が `--reasoning` を必須にし、未指定は rc=2)。
  31 bytes の訂正で L1.5 予算 (9,566 bytes) を 30 bytes 超過し、
  `DW-O01` の dispatcher route 行の構造 pin も破れることを実測した。
  誤記の是正なので D730 の原則落ちには当たらないが、収容先を削らずには入らない。
  上限の扱いを含めてユーザー裁定を仰ぐ。
