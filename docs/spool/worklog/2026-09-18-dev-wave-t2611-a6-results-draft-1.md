---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2611-a6-results-draft
seq: 1
title: [T-2611] A-6 read-heavy 認証 (attempt a6-20260908b、outer reject −5.7841%) の単独 results 稿を一次資料全体から書き、README の results 表へ 1 行足した — 段 6 の敵対レビュー 2 本の所見 9 件を全件採用し焦点再レビューで closed (docs のみ、branch worktree-dev-wave-t2611-a6-results-draft、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2611] (P3、entry 1488) A-6 read-heavy 認証 (attempt a6-20260908b、request 982234.nqsv、outer reject
  −5.7841%、2 cell とも source_binding_status=bound で correctness certified) の単独 results 稿を docs/paper-story/results/
  系列の規則どおり書く (docs のみ) — 一次資料全体から作り直し、横断稿で補完しない。性能判定 reject と正しさ証拠の取得を
  混同せず、当時の判定を保持する (規律 7)。−5.78% が B-10 近接条件 3 block と同符号・同程度であること ([T-2430])、反復
  attempt は行わないこと、実行基盤測定の −4.876% は attempt に数えないこと (D1870)、限定 (v) (D1993 + [T-2630]) を限定に
  書く。README の results 表へ 1 行足す。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の
  統制稿だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 成果物は `docs/paper-story/results/2026-09-18-a6-certification-reject.md` (§0 位置づけと主判定文 / §1 何を
  測ったか / §2 結果 / §3 他の記録との関係 / §4 限定 12 項 / §5 一次資料、commit 582cf60c0) と `docs/paper-story/README.md`
  results 表の 1 行。一次資料は `output/insights/2026-09-18/t2611-a6-results-draft/README.md` (レビュー逐語 3 本を
  `verbatim/` に同梱)。新しい測定は 1 件も行っていない。凍結物の bytes は変えていない。図は作っていない (A-6 の凍結図は無い)。
- 着手前実測 (段 1): tracked 6 file と durable authority 11 file の SHA-256 が manifest / 受領証と全件一致。派生統計
  (mean・標本 sd・cv・95% CI 半幅) を raw 5 標本から計算し、cv は campaign の書込み台帳の `bench_done.cv` と 4 桁一致。
  走行時 policy (8969a7e4…) と公開 policy (96ed47d0…) の JSON 差は `tracked_destination` 1 key で `protocol_sha256` は同一、
  現行 policy (main 302b94796) との差も `scheduler.nodes` 1 → 5 で preimage 外 (実関数で計算)。B-10 3 block の効果
  −6.609 / −5.377 / −5.317% を record から再計算し [T-2430] insight と一致。abort 率は走行時 source の runner が採る
  「throughput の中央値に最も近い rep」の 1 点。scheduler stdout には条件関門 8 record の本文が各 1 回出ているが、
  schema 化された保存ではないので限定 (iv) は維持した。
- 稿を書きながら親が直した誤り 3 件: §3.4「判定式も違う」(実際は同じ合成規則で workload 集合が違う)、§3.5 の D1506 の根拠
  (旧環境ではなく 2026-09-02 の非認証較正)、§4 (v) の「A-6 の src_token は新旧で同じ」の断定 (再計算していないので撤回、
  [T-2752] は D2120 項 7 で裁定済み)。
- **段 6 の敵対レビュー 2 本 (read-only codex、`gpt-6-astra`、両本 `accepted` / `completed`) はいずれも NO-GO を返し、
  親が全 9 件を real と裁定して採用した。** A (一次資料照合): must-fix 2 (`high_variance` / `rounds` の出所は raw JSON でなく
  campaign の書込み台帳、§3.4 の A-2 status / genome を支える一次資料が §5 に無い)、nit 2 (台帳の行数内訳、「canonical
  policy bytes」の語)。B (規律・限定・表現): must-fix 2 (§2.2 の引用可能文が性能と別走行の正しさを 1 文に畳む、§5.4 の D1506
  括弧が §3.5 修正前の旧記述)、should 2 (B-10 との「protocol」一致が測定契約の同一性に読める、trace 側 abort 比率の範囲が
  performance 条件 5 回だけであることの未明記)、nit 1 (表の単位)。B が提案した §0 の主判定文 (3 文に分けた引用形) も採用。
  A は掲載した全数値・hash 18 件・識別子・policy 比較を現物から再計算して「一致」を列挙、B は論点 11 件を「所見なし」と列挙。
- **焦点再レビュー 1 本 (fix 後): GO、10 件すべて closed、新規所見なし。** A-2 権威 bytes (SHA-256 e74d0f87…) の値、
  raw JSON / 台帳の field 実在、復号 policy の `legacy_correctness`、README 行の「限定 12 件」、派生統計の再計算を確認。
- 実装面 (コード・テスト・script・機械設定) の差分は 0。変異 matrix は `DW-S04` の免除。受入全走は land 経路で 1 走
  (結果は land の受領証)。`check_docs.py` 違反なし (段 5 後・fix 後・commit 後)、三軸語走査 hit 0、`git diff --check` rc=0。
- 工数: codex 子 3 本 (review 2 / focus 1、全件 `outcome=accepted` / `stop_reason=completed`、model_calls 13 / 10 / 8)。
  親の実測: SHA-256 全件照合、派生統計・policy 差分・protocol hash・B-10 record の再計算、台帳 20 行の全読、stdout の
  record_id 計数、走行時 source の runner 規則の照合、check_docs 直接 3 回、三軸語走査 1 回、全史 provenance 監査。

## 次の一手差分

### 完了

- [T-2611] A-6 read-heavy 認証 (attempt `a6-20260908b`) の単独 results 稿 `docs/paper-story/results/2026-09-18-a6-certification-reject.md`
  を一次資料全体から書き、README の results 表へ 1 行足した (docs のみ、commit 582cf60c0)。
  remaining: none
  base: 73b0af7c7afc5acb6c51324140c805f11f5691ff07a5b2495561b4af53127c68
