# 段 4 (再走) 裁定 — plan v3 確定

段 3 再走のレンズ C (移設完全性) / D (新 gate 実効性) はともに NO-GO。所見 15 件を裁定した。
**refuted はゼロ。** C-02 と D-01 は独立に同じ穴 (dispatch の発火条件が機械束縛されていない) へ収束した。

## 1. 裁定表

| ID | 判定 | 採否 | plan v3 での対応 |
|---|---|---|---|
| C-01 (BLOCKER) | real | 採用 | 入口に**通常列**を 1 行残す — 「message file → `--message-file` rc=0 → `commit -F` → 既定 full-history 監査」。reference へ移すのは別 range・legacy・任意の確認例だけにする。これがないと入口だけの読者が preflight 義務を発見できない |
| C-02 / D-01 (BLOCKER) | real | 採用 | dispatch 契約に**条件列を含める**。表は 3 列固定、path/節 ID の解析は第 3 列だけから行う。空条件・常時化・条件入替・第 2 列への token 密輸を独立の負例で拒否する |
| D-02 (BLOCKER) | real | 採用 | provenance の表・H2 解析は **HTML コメント / code fence を除外した可視行**だけを対象にする。`check_docs.py` に既存の可視行 scanner があるのでそれを使う。隠し heading / 隠し row の負例を置く。既存 dev-wave parser 側の同種問題は **scope 外 (裁定パッケージ)** |
| C-03 (HIGH) | real | 採用 | O7 の量化子を復元 — 「raw 候補数と canonical parser 認識数が**一致しなければ拒否する**」を本文へ書く (D98 決定 1 の逐語) |
| C-04 (HIGH) | real | 採用 | phase 1 の**完成全文を実体化**し、O1〜O45 と must-fix をその実体に対して再監査する。差分指示のままにしない |
| C-05 (MEDIUM) | real | 採用 | 「世代や内部モデルを推測しない」を復元。`unknown``  の余分な backtick を除去 |
| C-06 / D-07 (HIGH) | real | 採用 (親の主張を訂正) | 「correction は消費済みだから条件付き」は**担い手作成**についてのみ真。監査面では live なので、入口に「既定 full-history を権威とする」を残し、詳細だけ reference にする。削減率は単一値でなく**4 指標を分けて実測**する — (a) 入口 bytes、(b) 全 commit = 入口 + `PR-A02`、(c) dev-wave 通常 commit = 入口 + `PR-A01` + `PR-A02`、(d) family 総量。「上限不増」と「schema 受理集合変更」も分けて記録する |
| C-07 (HIGH) | real | 採用 | D105 の waiver 運用義務 (免除の**実発火件数と理由**を checker が stdout に出す / 件数と経緯を worklog に残す) を入口の waiver 節へ 1 行で入れる。family 上限は「**登録三文書の合計**」と限定して称する。分割で新設される義務 (入口を全 commit で読む、reference 不在なら停止、新規 carrier 禁止、preflight rc=0 後だけ commit) も移設マップへ逆方向に登録する |
| C-08 (MEDIUM) | real | 採用 | 「3 つの exactly-once 逐語 + 1 つの出現数依存 anchor (`scope=`)」と記述を正す |
| D-03 (HIGH) | real | 採用 | **registry 三面 (予算 path 集合 / 節 registry path 集合 / dispatch 契約 path 集合) の集合一致**を checker 自身が強制する。pair が複数 key に属することも拒否。「登録済みだが入口から到達不能な reference」の負例を追加 |
| D-04 (MEDIUM) | real | 採用 | 3 逐語は**入口で各 1 件・各 reference で各 0 件**を別々に pin し、`POLICY_PATH == PROVENANCE_ENTRY` も独立に固定する |
| D-05 (HIGH) | real | 採用 | family 全 path の `_ENUMERATED_DOCS` 所属を機械固定する。`all_limits` 経由で継承される dev-wave 固有 lint (land-helper 制約) の適用可否を明示し、境界テストと D に記録する |
| D-06 (HIGH) | real | 採用 | D-01〜D-05 の各穴に**独立した負例**を置く。変異は対象 gate だけを無効化し、第一失敗が当該 gate に帰属する形にする (registry key 削除のような二理由変異は分解する。F28/F60 の再発防止) |
| D-08 (HIGH) | real | 採用 | D は**修正後の実際の accepted/rejected 境界**と継承 lint を列挙し、その負例を同じ commit へ置く。実装しない保証を書かない |
| B-01 (再掲) | real | scope 外 | `_scope_policy_commit` / `_implementation_policy_commit` の per-lineage 化は裁定パッケージ |

## 2. 受入条件の erratum (親の事前登録の訂正)

段 1 brief の「phase 1 は 7,200 bytes 以下」は、段 3 が**追記を要求する must-fix** (C-01 通常列、C-03 拒否条項、
C-05 世代、C-07 waiver 運用、A-01 waiver 排他、B-02 reason 文法、B-03 `.rst`) を織り込む前の値だった。
これらは削除ではなく**欠落の是正**であり、削って目標を守るのは規律 2 に反する。よって受入条件を
**「phase 1 実ファイル ≤ 7,600 bytes かつ must-fix 全反映」**へ訂正する (現行 8,942 比 -15% 以上)。
phase 2 の受入は「入口 ≤ 6,300 / 各 reference ≤ 1,600 / 登録三文書合計 ≤ 9,000」を機械 gate とする。

## 3. commit 構成 (変更なし)

- commit 1 = docs-only。縮約 + 欠落是正の入口全文。親が書く。
- commit 2 = docs (入口 dispatch 化 + reference 2 本) + `tools/check_docs.py` + 境界テスト + D 記録。
  実装面は Codex `role=author` が書き、親は docs と D と統合だけを行う (D95)。

## 4. 変異事前登録 (plan v2 の 15 件を D-06 に従って分解・追加)

phase 2 統合 commit 後に `DW-O19` で本走する。各変異は**単一の gate だけ**を無効化する。

1. 入口の Codex author 逐語を 0 件化 → implementation exactly-once test
2. 入口の CAB 逐語を 0 件化 → CAB exactly-once test
3. 入口の waiver 逐語を 0 件化 → waiver exactly-once test
4. 入口の `scope=` を 0 件化 → 新規 `scope=` 出現数 test
5. reference 側へ 3 逐語のいずれかを複製 → reference 0 件 pin test
6. `docs/provenance/extra.md` を追加 (registry 非登録) → 未登録実体 test
7. 登録済み reference の実体を削除 → 欠落 member test
8. reference へ孤児 H2 を追加 → 孤児 H2 test
9. 入口 dispatch から 1 行削除 → dispatch 欠落 test
10. dispatch の**条件セルだけ**を恒偽の文言へ変更 → 条件束縛 test (C-02/D-01)
11. 条件セルへ path/節 token を密輸し第 3 列を空に → 列固定 test (D-01)
12. dispatch 表を HTML コメントで囲む → 可視行 scanner test (D-02)
13. reference の H2 を code fence 内へ移す → 可視行 scanner test (D-02)
14. 予算 registry にだけ第 3 member を足す (dispatch 未登録) → registry 三面一致 test (D-03)
15. family の 1 member を個別 cap 内のまま合計 9,001 bytes にする → family cap test
16. family cap の比較を到達不能条件へ変える → 9,001 拒否 test が緑になれば恒真化を検出
17. 孤児 H2 の差集合計算を空集合へ変える → 孤児 H2 test
18. family path のいずれかを `LIVING_DOCS` から外す → `_ENUMERATED_DOCS` 所属 pin test (D-05)
