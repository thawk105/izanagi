# [T-109] クロスプロトコル対応 — 実装可能性の調査と「実装しない」裁定 (2026-07-26)

- **wave 種別:** `/dev-wave クロスプロトコル対応`。段 4 で **実装しない**と裁定し `4→7→8→9` を採った。
- **実装差分:** なし (コード 0 byte)。したがって変異 matrix と受入全走は**対象外**である (`DW-S04`)。
- **基準 commit:** `4825398`。branch `worktree-dev-wave-t091-093-hardening`
  (worktree `dev-wave-t088-floor-wrapper`)。
- **逐語:** `output/insights/2026-07-26_s1-cross-protocol-consultations.md`
  (段 2 プラン 1 本 + 段 3 敵対レンズ 2 本。計 3 本、いずれも codex `gpt-5.6-sol` / `reasoning=max` /
  `sandbox=read-only`)。
- **判定:** 段 2 プラン **NO-GO**、段 3 レンズ A **NO-GO**、レンズ B **NO-GO**。**3 本すべて NO-GO。**

---

## 1. 何を調べたか

引数「クロスプロトコル対応」を Phase 3 の次の 3 つの現行項目と同定した。

- 主実験 headline 2 = **クロスプロトコル stock 最良**との比較 (`docs/phase3-main-experiment.md`)
- **S1** = 別 protocol への trace-hook 移植 (`docs/phase3.md` must 表 S1 行)
- 後続段 7 = cross-protocol 最適化移植 + カタログ化

そのうえで「最安の生死実験を 1 本通す」(`DW-G01`) ことを狙い、mocc 1 protocol への trace-hook
移植を実装 scope とする brief を立てた。結論として、**本 wave が取りうる実装経路はすべて塞がっている**。

## 2. 現状の構造 (実測)

| 事実 | 根拠 |
|---|---|
| trace-hook を持つ protocol は **silo と si の 2 本のみ**。他 8 本 (cicada/d2pl/ermia/mocc/mvto/oze/ss2pl/tictoc) は 0 件 | grep 実測。`external/ccbench/cc/silo/transaction.cc`、`.../cc/si/transaction.cc` |
| verifier は機能的に protocol 非依存。入力は trace dir だけ | `orchestrator/verifier/core.py:2-19`。ただし `dsg.py:52` に `Silo` 言及コメントが 1 件ある (親の「出現 0 件」は字面では誤り) |
| verifier は版 ID 写像の誤りを fail-closed で捕まえる。要求は **9 カウンタ全 0** | `orchestrator/verifier/model.py:101-142` の `Integrity.clean()` |
| buildcache の target/cache key は protocol 汎用 | `orchestrator/campaign/buildcache.py:135,339,581` |
| `SPACES` / `space_for()` の消費者は `genome.py` とテスト以外に 0 件。`Genome` は protocol を検証しない | `orchestrator/campaign/genome.py:88-96`、`model.py:35-60` |

### 2.1 版 ID 写像コストは protocol で桁違い (本調査の中心的な技術的知見)

| protocol | 版 ID の表現 | 移植コスト |
|---|---|---|
| **mocc** | `Tidword{absent:1, tid:31, epoch:32}` (`cc/mocc/include/tuple.hh:14`) | bitfield 抽出は恒等。ただし **UPDATE-only に限る** — `absent` を落とすと tombstone read が false-green、INSERT/reinsert では同一キーの版順が native commit 順と一致しない (所見 A-2/A-3) |
| **tictoc** | `TsWord{lock:1, absent:1, delta:15, wts:47}` (`cc/tictoc/include/tuple.hh:13`) | **不安定**。validation の rts 拡張が delta overflow 時に `v2.wts = v2.wts + shift` で**新版を書かずに wts を前進させる** (`cc/tictoc/transaction.cc:425-440`)。ソース上の実在は確認済みだが「版 ID が不安定」は設計上の推論であって実測ではない |
| **ermia** | `cstamp<<1` (低ビット = SSN flag) | 既知の罠。`docs/ccbench-anatomy.md:211` |
| silo / si | 移植済み | si は `(epoch=1, tid=cstamp)` へ写像 (`cc/si/transaction.cc:526-553`、約 30 行) |

**silo と si の hook は同型ではない。** si は `emit_commit` / `emit_read` / `emit_write` だけの最小形だが、
silo は lock 被覆 shadow (D38) と permutation 保存 assert (D41) を持つ。
`Integrity.clean()` の 9 項目のうち `lock_coverage_violations` と `permutation_violations` は
**silo の `#if TRACE` assert が emit する X 行 / P 行だけが検出源**である。
したがって si 型の最小 hook を mocc に移植すると、この 2 カウンタは**常に 0 になる恒真ゲート**になり、
同じ lockskip を silo は `indeterminate`、mocc は cycle が偶然出なければ `certified` とする
**protocol 間の受理集合の非対称**が生じる (所見 A-5)。

## 3. 実装を塞いでいるもの (すべてユーザー承認済みの決定)

### 3.1 D86(3) / D87 — AI は `qsub` しない

`docs/decisions.md:3789-3800`。「実 submit artifact ID の確認は人間の明示 `qsub` を待つ。
**AI は `qsub` しない**」と明記され、両敵対レンズが親の当初裁定を否定した経緯まで記録されている。
`docs/pegasus-runbook.md` §7 の「Pegasus はビルド・動作確認・デバッグ用」は**計算資源の用途**の話であり、
AI に qsub 権限を与える記述ではない。

→ **生死実験の実測 (計算ノードでの TRACE=1 ビルドと correctness run) を AI は実行できない。**
DW-G01 が要求する「最安の生死確認」の核心部分が、そもそも人間手番である。

### 3.2 D16 — trace-hook の out-of-tree patch は却下済みの選択肢

`docs/decisions.md:248-275`。D16 は改変の行き先を性質別に分岐させ、trace-hook を
submodule `izanagi-trace` branch と定めた。却下リストには「**D6 維持 (全て patch)**」があり、
却下理由は「trace-hook が protocol 横断で増えると patch rebase が破綻する」である。

親は「人間承認 gate 待ちの単発 hook を一時的に patch へ隔離するのは D16 の却下対象と別物」と主張したが、
両レンズが却下した。**「単発・一時」は D16 の分類軸ではない。**例外を採るならユーザー裁定と
decisions への記録が要る。

### 3.3 D32 — cross-protocol は主実験後の拡張予約 (ユーザー承認 2026-07-03)

`docs/decisions.md:709-729`。層2(b2) 移植を「主実験後の拡張予約」に降格し、
**着手時の一歩目をカタログ化の試作 1 枚**と定め、「cicada/oze への空間拡大 (**S1 移植を伴う**) と
束ねるのが自然」としている。主実験 (段 6) はまだ走っていない ([T-011] floor 実測が未了)。

→ 本 wave の scope は、承認済みの順序を反転させる。

### 3.4 [T-088] — 承認済み・未実行の human turn を、**ファイルを足すだけで**割る

これが最も重要な発見である。当初、親は「凍結 bytes を 1 byte も変えない回避路がある」と考えた
(`genome.py` を触らず、gitlink も前進させず、patch として置く)。**これは誤りだった。**

- floor launch certificate の `clean_scan_digest` は**実際の repository file 一覧を preimage に含む**
  (`orchestrator/campaign/s8b_floor_campaign.py:1597-1639`)。patch / driver / PBS script を commit すれば
  [T-088] receipt の `source_commit` と `clean_scan_digest` が承認時点から変わる。
- `tools/pegasus/submit_floor.sh:181-245` は tracked clean・`output/` 外の untracked・未 commit script を
  明示拒否する。PBS の stdout/stderr は `#PBS -o/-e` を指定しなければ投入ディレクトリへ戻るため、
  repo root から投入すると `.o<ID>` / `.e<ID>` が `output/` 外の untracked file になり submit が rc=2 になる。

参考までに、当初想定していた別経路も独立に塞がっている。

- `genome.py` への `SPACES` 登録 → 同ファイルは `output/s1-freeze/known_axes_freeze.json` と
  `output/s8b-freeze/holdout_freeze.json` に source sha256 で pin され**現在値と一致 (MATCH)**。
  編集すれば oracle gate に `known-axes-freeze-verify: source sha256 不一致` が増える。
- submodule への commit と gitlink 前進 → `ccbench_pin = d706650...` が
  `known_axes_freeze.json` と `output/s8b-freeze/floor_protocol.json` に刻まれ、同値が
  `orchestrator/campaign/s8b_approved.py:67` の `CCBENCH_FULL_SHA` = 承認定数
  (「定数の追認を許さない」)。`orchestrator/tests/test_s8b_approved.py:58-64` の
  `test_ccbench_full_sha_matches_real_gitlink` は「**submodule 前進の検出**」を目的に実 gitlink を
  照合し、基準で 10 passed の緑を実測した。`s8b_floor_campaign.py:393-396` も同様に fail-closed する。

### 3.5 buildcache の信頼境界は silo 形状である

`buildcache.build()` は configure 前に `source_digest.assert_worktree_within_allowlist()` を
**無条件実行**する (`orchestrator/campaign/buildcache.py:573-577`)。
`ALLOWLIST` は `{cmake/Options.cmake, include/backoff.hh, cc/silo/transaction.cc}` の 3 件のみ
(`orchestrator/campaign/source_digest.py:62-71`)。dirty な `cc/mocc/transaction.cc` は拒否される。

親は「`s5_permutation_coverage.py:125-132` が patched build に手動 cmake を使う先例がある」と反論したが、
**レンズ A に否定された**。s5 の手動 build は **trusted な HEAD 済み hook の上に broken 差分を重ねる**
ものであり、**新規 hook そのもの**を手動経路で作る本件とは非同型である。buildcache は build ごとに
観測者効果の diff-of-diffs と TRACE=0 の `nm` 検査を行う (`buildcache.py:592-620,659-675,713-735`) が、
手動 cmake 経路はこれを通らない。すなわち `#ifdef TRACE` の書き戻しや unguarded static を含む patch でも
smoke の受理集合に入りうる。**規律 1 の機械防壁が効かない経路で規律 1 を守る新規コードを書く**ことになる。

## 4. 段 4 裁定

**実装しない。** 理由は上記 3.1〜3.5 が独立に成立し、いずれも本 wave の権限内で解消できないため。
`DW-S04` に従い段 5・6 を飛ばし `4→7→8→9` とした。
`DW-S04` は「承認済み裁定を親が独断で失効させてはならない。止めてよいのは裁定時点で未見だった
新事実がある場合だけで、その場合も親が不採用にせずユーザー再裁定待ちへ戻す」と定めており、
本件はまさにその形である。

なお `DW-G04` (条件付き機能の発火 gate) の観点でも、本 wave は「発火条件を満たす既存 artifact path
または計測 ID を brief に書ける」状態になかった。

### 4.1 親 brief の誤り (すべて real と認めた)

| # | 誤り | 訂正 |
|---|---|---|
| P4 | 「AI が PBS ジョブを投入してよい」 | **誤り**。D86(3)/D87 が明示禁止 |
| P5 | 「gate 待ちなら D16 の例外として patch に置ける」 | **誤り**。D16 に該当例外はない |
| P1/P2 | 「cross-protocol の一歩目は S1 移植」 | **不足**。D32 が一歩目をカタログ化試作と定め、主実験後へ降格済み |
| P6 | 「patches/ への追加は repo scan invariant に無害」 | **無条件命題としては誤り**。file 一覧は `clean_scan_digest` の preimage に入る |
| P7 | 「mocc の live 軸は 2 本」 | **誤り**。universal `BACK_OFF` を落としている。正しくは `BACK_OFF=1, KEY_SORT=0, TEMPERATURE_RESET_OPT=1` の 3 軸 |
| 実測2 | 「verifier に silo の出現 0 件」 | **字面では誤り** (`dsg.py:52` に `Silo`)。機能的 protocol 非依存性という主張自体は維持 |
| 実測3 | 「`IntegrityIssues.is_clean()` が 4 カウンタを要求」 | **誤り**。実体は `Integrity.clean()` で **9 カウンタ** |
| 実測6 | 「mocc は恒等写像」 | **UPDATE-only 限定**。`absent`・INSERT/reinsert・scan で前提が崩れる |
| R-1 | 「手動 cmake は gate 迂回でない」 | **限定採用にとどまる**。観測者効果 baseline を通らない点は未解決 |
| R-3.1 | 「si 型最小形でよい」 | **life/death に限り採用**。ただし恒真ゲート化を自覚した上での限定 |

## 5. ユーザーへ返す裁定パッケージ

1. **[T-109-a] D16 の prototype 例外の可否。** 一回限りの trace-hook patch を許すか。
   許すなら campaign/cache 非流入・期限・昇格先 (branch)・削除条件を decisions と
   `patches/README.md` に記録する。拒否なら trace-hook は branch にしか置けず、gitlink 前進を伴う。
2. **[T-109-b] [T-088] との順序。** 現在の承認済み source state で [T-088] を先に実行するか、
   新規ファイル追加後の `source_commit` / `clean_scan_digest` を再承認するか。
   **AI 推奨 = [T-088] を先に完了させる** (承認済み・未実行であり、後続の [T-011] が従属するため)。
3. **[T-109-c] 最小 trace-hook smoke の scope。** 実施するなら SI 型 C/R/W + 正例 +
   W-version mismatch の 2 ケースに限定し、driver が隔離 worktree を所有し、C 行数と
   `commit_counts_` の一致・pin/patch/binary hash を残す。**実測は人間 `qsub` 手番**である。
4. **[T-109-d] observer-effect baseline の protocol 拡張。** 手動 cmake 経路が規律 1 の機械防壁を
   通らない問題への恒久対応。`source_digest` の allowlist と trusted TRACE baseline を
   protocol-aware にするか、非 campaign build 専用の検査経路を作るか。
5. **[T-109-e] MOCC lock coverage package。** RWLOCK non-INSERT の入口/保持、lockskip/early-unlock を
   別 wave で扱う。INSERT・hot-read owner・MQLOCK はさらに別裁定。
   これを行わない限り mocc の `Integrity.clean()` は silo より構造的に弱い。
6. **[T-109-f] 本物の cross-protocol package の順序。** D32 に従うなら一歩目はカタログ化試作 1 枚。
   S1 移植は cicada/oze への空間拡大と束ねる。headline 2 を復活させるなら
   `docs/phase3.md` must 表 S1 行の択一 (S1 移植 vs stock 専用計測経路) を先に決める必要がある。

## 6. この wave が確定させた再利用可能な知見

- **移植順序は「protocol の系統」ではなく「版 ID の安定性」で決めるべきである。** OCC 同士の
  silo→tictoc は直感的に近いが、tictoc は新版なしに wts が前進する経路を持つ。
  mocc は hybrid だが bitfield は恒等。**直感的な近さと移植コストは相関しない。**
- **`Integrity.clean()` の 9 カウンタのうち 2 つは silo 専用の emitter に依存する。**
  protocol を増やすと、hook の装備差がそのまま**検出力の差**になる。
  「移植した」と「同じ強度で検証できる」は別である。
- **凍結基盤は bytes だけでなく「ファイル一覧」も preimage に持つ。**
  `clean_scan_digest` の存在により、**凍結ファイルを 1 byte も触らなくても**、新規ファイルを
  commit するだけで承認済み receipt の前提が変わる。`DW-O09` の pin 閉包列挙は
  「bytes を pin する台帳」を既定対象にしているが、**ファイル集合を pin する digest** が抜けている。
