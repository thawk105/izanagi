# [T-1128] — 床値の oracle 依存 root と build の source root を同一 tree へ揃える

wave: `dev-wave-t1128-floor-same-root` / 2026-08-15〜16 / branch
`worktree-dev-wave-t1128-floor-same-root`

## この材料が答えたこと

依頼は [T-1128]。2026-08-15 の /rulings 束で [T-1094] が「(a) 実装しない」と裁定され、
床値の残作業が本項へ集約された結果である。**実装した。**

前 wave (`output/insights/2026-08-15_t1094-fetchcontent-floor/`) が計算ノードで
`same_root = false` を実測し、oracle が実質要求しているのは pin された source ではなく
**build 済みの masstree** (`config.h` と archive) であることを確定していた (D413)。
本 wave はその構造欠陥を塞いだ。

## 何を変えたか

- job 一意な `$TMPDIR` 配下に canonical な FetchContent base を 1 個作り、
  依存の prebuild と `sort_best` cell の build が同じ `<base>/masstree-src` を使う。
  oracle の `dependency_root` はその root へ明示束縛する。
- **`FETCHCONTENT_SOURCE_DIR_*` は渡さない。** [T-1094] の裁定どおり、この配線は復活させていない。
  `FETCHCONTENT_BASE_DIR` は FetchContent の repository と SHA pin を迂回せず、
  source/build/subbuild の親だけを変える別の変数である。
- **同一性の権威を内容に置いた** — masstree HEAD + `config.h` sha256 + archive sha256。
  `st_dev` / `st_ino` は診断に留めた。内容が同じなら inode が変わっても通る。
- build が実際に使った masstree source root を **build 自身の成果物 (`CMakeCache.txt`) から
  読み取って照合する。** configure argv の文字列検査は補助へ降格した。
- 依存 receipt を v2 build identity の preimage へ入れ、
  別 masstree で作られた binary が cache hit する経路を閉じた。
- **completion を publish する前に、実効 root から内容を取り直して入力 receipt と比較する。**
  実効 root が期待 base の外なら publish しない。
- 失敗は段階別の閉じた detail code へ変換し、永続化してから
  `OracleStatus.UNAVAILABLE` で停止する。oracle 未実行・`build_fn` 未実行を保つ。
- 旧経路の共有 third-party cache を production から撤去した
  (submitter の必須検査と qsub export を含む)。放置すると「cache を指せば動く」入口が残り、
  F319 の再来を招くためである。

## 主張しないこと

- **pinned-clean な masstree で build したとは主張しない。** ignored 生成物の検査は [T-1129] の範囲。
- **build 中に依存を差し替えて元へ戻す (ABA) 攻撃への保護は主張しない。**
  前後 snapshot の同値検査では検出できない。publish 前の照合により観測窓は
  「build 完了から publish まで」から「build 中のみ」へ狭まったが、予防はしていない。
- **1 job の実測から床値全体・他 node・他 profile の可用性を一般化しない。**
- **床値が取れるようになったとは主張しない。** 本走 (12 cell・測定・report) は行っていない。
- 計算ノードで共有 base の再利用挙動 (2 本目の configure が再 fetch しないこと) は**未測定**である。
  静的根拠は CMake 3.22.1 の実ソースと、床値 job が `command -v cmake` で
  同じ実体を引くことだけである。設計は fail-closed なので、仮定が外れても偽の主張は出ず停止する。

## 測ったこと

すべて計算ノード (Pegasus `gen_S`) で実測。login node の bounded local は
`bounded scope の memory.max / memory.oom.group を走行中に attest できない` により
rc=16 になり使えなかった (テスト結果ではない)。

| 走行 | 結果 |
|---|---|
| `test_buildcache_v2.py` 単独 | 120 passed |
| `test_build_site_gate.py` 単独 | 23 passed |
| `test_pegasus_floor_tools.py` 単独 | 71 passed |
| `test_s8b_floor_campaign.py` 単独 | 301 passed, 2 skipped |
| 合同 4 file | 515 passed, 2 skipped |
| 制約 meta 4 file (`test_env_contract` / `test_sort_swo_oracle` / `test_s8b_oracle_manifest` / `test_s8b_oracle_report`) | 503 passed |

## 変異検査

固定 commit `341ea11cdabb3a16b66c8e8bf99896da0630d310` の使い捨て worktree で
`tools/mutation_worktree.py` を `--runner-mode dispatch` で走らせた。

### 初回走 (probe 巡) — `mutation-ledger-probe.json` / `mutation-spec-probe.json`

9 変異。baseline PASSED (515 passed, 2 skipped)。
**KILLED 7 / MISMATCH 2 / SURVIVED 0。**

MISMATCH は M3 と M5 の 2 件で、どちらも **観測が登録の上位集合**だった。
spec が 1 つ前の commit `5fcad04e` の時点で書かれ、その後の fix が
`test_buildcache_v2.py` へ test を追加したため期待 node が古くなったことによる。
検出力が登録より低かったのではない。**この巡は probe として残す** (`DW-M08`)。

### 再走 — `mutation-ledger.json` / `mutation-spec.json`

M3 と M5 を再登録して再走。baseline PASSED。**KILLED 2 / MISMATCH 0 / SURVIVED 0。**

再登録した期待 node は観測から埋めたのではなく、**赤になる因果を実コードで説明できたものだけ**を
入れた (逐語 = `verbatim/` には収めていないが、因果の説明は本節に要約する)。

- M3 (依存 receipt を v2 identity preimage から外す) が
  `test_v2_cache_hit_reuses_same_content_receipt_across_distinct_bases` を赤にするのは、
  preimage から receipt が消えると cache hit 側の validator が
  `fetchcontent_dependency` を期待 field に加えず、実 manifest の余分な field で
  field 集合検査が落ちるためである。
- M5 (`-DFETCHCONTENT_BASE_DIR` を 2 個生成する) が
  `test_v2_wrong_effective_root_never_publishes_or_hits_same_key` を赤にするのは、
  exact-one gate が `_run(configure, ...)` より前に発火し、
  テストが用意した wrong-root の経路へ到達しないためである。

### 登録した変異

| ID | 変異 | 結果 |
|---|---|---|
| M1 | 実効 root 照合を削り argv 検査だけに戻す | KILLED |
| M2 | `config.h` sha256 比較を恒真化する | KILLED |
| M3 | 依存 receipt を v2 identity preimage から外す | KILLED (再走) |
| M4 | prebuild 失敗を握り潰して oracle へ進む | KILLED |
| M5 | `-DFETCHCONTENT_BASE_DIR` を 2 個生成する | KILLED (再走) |
| M6 | base 注入を非 sort cell にも広げる | KILLED |
| M7 | oracle dependency root を wave 前の形へ戻す | KILLED |
| M8 | cache receipt から archive sha256 を外す | KILLED |
| M9 | phase marker の archive sha256 記録を外す | KILLED |

**M8 が KILLED だったことが本 wave の検出力の要点である。** 段 6 の敵対レビュー B は
「cache identity の実 consumer から archive key だけを削る変異は、自己導出期待値と
寛い fake により生存する」と予測しており、fix の F6 (期待値を独立 literal 化し、
fake に exact 一致を要求する) がその穴を実際に塞いだことが確認できた。

### 変異台帳の限定

- M1 の期待 node のうち
  `test_floor_postflight_gate_rejects_effective_root_and_content_drift` の wrong-root parameter は、
  fixture が `masstree-src` 自体を作っていないため後段の source-missing gate に**過剰決定**されている。
  単一理由の kill 証拠には数えない (`DW-M03`)。M1 の単一理由 node は
  `test_floor_postflight_cache_hit_uses_content_receipt_not_prior_absolute_root` の fresh 部分である。
- `_v2_commands` と `prepare_masstree_fetchcontent` の内部にある
  「`FETCHCONTENT_SOURCE_DIR_*` が 0 個」「`FETCHCONTENT_BASE_DIR` がちょうど 1 個」の検査は、
  公開引数や `Genome.cmake_defines()` から発火させる具体的入力が無い。
  これらは**構成不変条件**であって、外部入力に対する実効 gate ではない。
  実効 gate は campaign 側の postflight である。

## 手順で起きたこと

- 段 3 の敵対 2 レンズが独立に NO-GO、段 6 の敵対レビュー 2 本も独立に NO-GO、
  段 6 の焦点再レビューも NO-GO。fix は 4 巡した。
- **第 1 巡の 79 件の赤は親の裁定文の誤りが原因**である。片方向の含意を「同値」と書いたため、
  実装子が忠実に双方向の同値を実装し、base を持たない正常な `sort_best` record を全部拒否した。
- **第 3 巡で偽の緑を 1 件是正した。** 失敗注入テストが `buildcache` を束縛しておらず、
  `NameError` が production の総括捕捉へ落ちて、期待値と偶然一致したパラメータだけ
  緑のまま通っていた。
- 第 4 巡は `DW-O16` の 3 巡上限を超えるが、**新しい所見への追加対応ではなく
  第 1 巡 fix 契約 F2 の未完了部分の完成**であり、成果物影響が重い
  (oracle が検証していない依存で作られた binary に certified の admission receipt が出る)
  ため実施した。判断と根拠は `verbatim/s6-fix4-ruling.md` §0 に書いた。
- 背景 job の待ち手 (`tools/dev_wave_wait.py producer`) が 3 回連続で、
  成果物・`.done` が無く生産者が生存している状態で rc=0 で終了した。
  3 点照合で未完了と判定し、最後は `.done` 出現までブロックする自前の待ちへ切り替えた。

## 裁定へ返した項目 (scope 外の real 所見)

1. SWO PASS receipt が durable record へ束縛されていない。
   `prepare_cell` が返す `oracle_attempt` を `s8b_floor_campaign` は一度も読まない。
2. oracle 後の再 fetch を禁止する手段 (`FETCHCONTENT_FULLY_DISCONNECTED` 等) は
   download 権威の変更なので別審査が要る。
3. 計算ノードでの 1 job probe (共有 base の再利用挙動の実測)。
4. build 中の依存差し替え (ABA) に対する予防。
5. 共有 base の所有権 lock (将来 cell build を並列化するときの再審査事項)。

## 逐語

- `verbatim/` に段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、
  段 6 敵対レビュー 2 本、段 6 焦点再レビュー、段 6 fix 契約 4 巡分を収めた。
- 実装子・fix 子の報告は job dir に残る。本 README はその結論だけを持つ。
