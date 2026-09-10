# 段 4 裁定 — plan v2 と変異事前登録 (dangling-audit-offrepo-authority)

段 3 は 2 レンズとも **NO-GO** (lensA blocker 4 / lensB blocker 1)。親は下記のとおり裁定し、
**設計を 1 点で作り直した**。作り直しの根拠は段 4 で新たに取った実測 2 件である。

## 段 4 の新規実測 (裁定の根拠)

- **実測 A**: 現状の findings は **8 commit / 28 (commit,path) 対**。段 1 brief の「24 対」は誤りで、
  24 は失われた **basename の異なり数**だった。lensA-4 の指摘は real。brief は訂正済み。
- **実測 B**: `git grep -F -l <repo 外 path> main` を実行した結果、
  **[T-574] の `/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py` は
  main の landed 文書 3 本 (`output/insights/2026-08-06_t574-historical-resolver/brief.md`,
  `s3-lensA.md`, `s3-lensB.md`) から参照されている。**一方
  **[T-409] の `/work/1/SFC/tanab/dev-wave-jobs/t409-impl-trigger-grammar/` を参照する landed 文書は
  0 件**である。

## 設計の作り直し — 抑止条件に「landed 参照」を連言として足す

段 2 プランは「basename 一致 + bytes 一致」で抑止する。lensA-1 (一時的な写しを永続的な保全と誤認) と
lensA-2 (無関係な同名同内容による masking) はこの述語に対する real な反証であり、親も real と認める。

**しかし修正は (a) ack 台帳でも (d) prune でもなく、裁定文自身の分類の中にある。**
裁定は 3 群を明確に分けている — [T-574] は **(b) で消す構造的偽陽性**、[T-409] と [T-213] は
**(c) で gc に任せる裁定済み残骸**である。段 2 プランの述語は [T-409] の 11 対まで (b) で消してしまい、
**裁定の分類を踏み越えている**。実測 B が示すとおり、2 群を分ける観測可能な差は
「**main に land 済みの文書が、その repo 外 path を一次資料として参照しているか**」である。
[T-574] の起票根拠そのもの (裁定文 19〜21 行「landed 側の brief.md / s3-lensA.md / s3-lensB.md が
repo 外の絶対パスで参照している」) がこの差であり、bytes 一致は起票者が付けた**裏取り**にすぎない。

したがって抑止述語を次の連言に確定する。**裁定 (b) の範囲内で、抑止する集合は真に小さくなる方向にしか
動かない** (13 対 → 2 対)。安全側であり、承認済み裁定を緩めない。

1. 到達不能側が **regular blob** (mode 100644 / 100755) であること。削除・symlink・gitlink は不可。
2. repo 外候補が **regular file** で、**basename が一致**すること。
3. **実行 mode が一致**すること (100755 ↔ owner 実行ビット)。lensA-2 の「非 executable が
   executable script を抑止する」を閉じる。
4. **bytes が完全一致**すること (size prefilter → sha256 → 逐次 bytes 比較)。
5. **main の tree から、その候補の絶対 path、または探索根より真に下位の祖先 directory path が
   参照されている**こと (`git grep -F` を候補分まとめて 1 回)。

条件 5 が lensA-1 への実質的な回答である。landed 文書は main の履歴に永続する。repo 外実体が後で
消えても、**「この成果物の所在はここである」という記録は main に残り続ける**。「たまたま写しがある」
と「所在が台帳に記録されている」の差がここにある。**探索根そのものへの参照 (runbook §7.2 が書いている
`/work/1/SFC/tanab/dev-wave-jobs/`) は根拠にしない** — 全件を一撃で抑止してしまうため。

**bytes は一致するが landed 参照が無い候補は抑止しない。**findings に残したうえで、その行に
「repo 外に同一 bytes の実体あり (landed 参照なし): \<絶対 path\>」と注記する。救出判断の材料は
渡しつつ、rc は 1 のままにする。

**この設計での実 repo 期待値: 8 commit / 28 対 → 6 commit / 26 対 (抑止 2 対)、注記 11 対。**
commit 数の減り方は段 2 プラン (6 commit) と同じである — [T-409] の 2 commit は
`README.md` が bytes 不一致で残るため、どちらの述語でも消えない。

## 所見の裁定表

| # | レンズ | 判定 | 採否 | 成果物影響 (直さない場合に何が変わるか) |
|---|---|---|---|---|
| A-1 | 一時的な写しを永続的保全と誤認 | **real / blocker** | **採用** (条件 5 を新設) | 抑止した (commit,path) が写し削除 + gc で二度と報告されず、未 land の insight・fragment が台帳から永久欠落する |
| A-2 | basename+bytes は同一成果物の証明でない (空 file、mode) | **real / blocker** | **採用** (条件 3・5) | 無関係な同名同内容や非 executable 同名により、救出すべき path が報告から消える |
| A-3 | root 検査の迂回 (祖先 root、`/`、hardlink、symlink race) | **real / blocker** | **一部採用** | 祖先 root 拒否を**必須化**。repo 内 untracked copy を根拠にすると自作自演 masking になる。hardlink と root symlink 交換は、単独運用者環境で意図的操作を要するため**残存 risk として明記**し実装しない (敵対者モデルを置かない) |
| A-4 | 件数 oracle の不整合 (24 vs 13 vs 15) | **real / blocker** | **採用** | brief の 24 は basename 数の誤記。実測 A で 28 対に訂正。件数は**固定 HEAD での 1 点観測として worklog に書くだけ**とし、テストの oracle にしない (dangling object は gc と wave 進行で変わる) |
| A-5 | rc=0 が caller で silent になる | **real / must-fix** | **採用** | 抑止分が cleanup の救出判断へ渡らない。module docstring の rc 契約、0 件時出力、caller の 3 分岐記述を更新する |
| A-6 | 新規テストが危険な述語を殺せない | **real / must-fix** | **採用** | 下記の変異事前登録で被覆する |
| A-7 | 第三条件は内容違いの revision を見逃す | real / **scope 外** | **不採用** ([T-593] 事項 1(c)) | 裁定パッケージへ返す |
| A-8 | refs の非 snapshot race | real / **scope 外** | **不採用** ([T-593] 事項 4) | 裁定パッケージへ返す |
| B-1 | 実際の caller で発火しない (恒真機構) | **real / blocker** | **採用** | `DW-G04` により、発火条件を満たす経路を書けない条件付き機能は実装してはならない。`.claude/commands/cleanup-branches.md` の監査呼び出しへ環境変数を渡す形を親が書く |
| B-2 | 祖先 root 拒否が未確定 | **real / must-fix** | **採用** (A-3 と同一) | 同上 |
| B-3 | `--include-fold-trees` の CLI 回帰 | **real / must-fix** | **採用** | 明示した `--include-fold-trees` が黙って無視され、spool/archive の調査契約が退行する |
| B-4 | env 名がテストで独立に固定されていない | **real / must-fix** | **採用** | 定数を誤記した実装が緑になり、実運用で 1 度も発火しない |
| B-5 | CLI precedence の positive test が弱い | **real / must-fix** | **採用** | CLI 指定時に env 側を混ぜる誤実装が緑になる |
| B-6 | スケール・メモリの根拠が 1 点 | **real / must-fix** | **一部採用** | 候補 blob に **32 MiB の上限**を設け、超過は抑止せず理由を表示する。逐次 chunk 比較で候補ファイル全体をメモリへ載せない。10 倍規模の実測は**行わない** (`DW-G02`: 1 cycle 後へ送る) |
| B-7 | FIFO テストが hang しうる / root onerror 未被覆 | **real / must-fix** | **採用** | 回帰が赤でなく hang・無言 skip になる。FIFO は lstat 段階の拒否を単体で固定し、`open()` しない。読めない root の control を足す |
| B-8 | 「正本 / authority」の語が既存 trust semantics と衝突 | real / nit (scope 外) | **採用** (安いので今やる) | 出力・識別子から「正本 / authority」を外し「repo 外の同一実体 (external copy)」に統一する |
| B-9 | lease env との関係が曖昧 | 疑い / nit | **採用** | runbook §7.2 に、新 env は `dev-wave-jobs/` 親を指し `IZANAGI_WAVE_LEASE_DIR` (その下の `land-lease/`) とは別であると書く |

## plan v2 (段 2 プランからの差分だけを書く。他は段 2 プランのとおり)

1. 抑止述語を上記 5 連言にする。条件 5 の実装は
   `git -C <repo> grep -F -l -e <path1> -e <path2> ... <main-ref> --` を **bytes 一致した候補についてだけ
   1 回**呼ぶ。rc=1 (hit 0) は正常系、rc≥2 は「参照確認不能」として**抑止しない**側へ倒す。
2. 探索根の検査を必須にする。root == worktree、root が worktree の子孫、**root が worktree の祖先**、
   root == `/` はすべて拒否し、拒否理由を出力する。拒否は監査を止めない。
3. `audit_with_offrepo()` は `excluded_prefixes` を `audit()` へそのまま渡す。CLI の
   `--include-fold-trees` が wrapper 経由で効くことを CLI レベルのテストで固定する。
4. 抑止は `AuditReport.suppressions`、注記は findings 側に持たせる。CLI 出力は
   「抑止」節と findings 行の注記の両方を出す。**rc=0 のときも抑止節を出す。**
5. 命名から「正本 / authority」を外す。`external_copy_path`、「repo 外の同一実体」で統一する。
6. 候補 blob は 32 MiB 上限。超過は抑止せず `oversize` として表示する。bytes 比較は chunk 単位。
7. module docstring の `exit code: 0 = 取り残しなし` を、抑止分を除いた意味へ書き換える。
8. `LIMITATION_NOTICE` は既存検出範囲の記述なので変えない。新条件は専用の出力行で開示する。

## 変異事前登録 (DW-M01、実装前に確定)

各変異は「同じ入力を拒否する層が前後に無い」ことを実装後に確認してから走らせる。
harness は `tools/mutation_harness.py --runner-mode dispatch`、runner argv に `--force-dispatch` を付ける。

| ID | 変異 (実装の逐語置換) | 期待 kill node (受理集合が変わる) |
|---|---|---|
| M01 | 条件 5 (landed 参照) の連言を落とし bytes 一致だけで抑止する | `test_negative_offrepo_copy_without_landed_reference_is_reported_with_note` |
| M02 | bytes 比較を落とし basename + size 一致で抑止する | `test_negative_offrepo_same_size_different_bytes_is_reported` |
| M03 | mode 一致検査を落とす | `test_negative_offrepo_mode_mismatch_is_reported` |
| M04 | 探索根が worktree の祖先でも受理する | `test_negative_offrepo_root_containing_worktree_is_rejected` |
| M05 | CLI root 指定時にも env root を併合する | `test_positive_cli_roots_override_environment` |
| M06 | wrapper が `excluded_prefixes` を既定へ握り潰す | `test_cli_include_fold_trees_reaches_audit_through_wrapper` |
| M07 | 抑止節の出力を消す (findings からは外したまま) | `test_positive_suppression_is_disclosed_at_rc0` |
| M08 | 到達不能側の mode 検査を外し symlink / gitlink も blob 扱いする | `test_negative_unreachable_symlink_is_not_suppressed` |
| M09 | 探索根未指定時の「未実施」表示を消す | `test_negative_root_unspecified_discloses_skip` |
| M10 | 抑止述語を恒偽にする (過剰拒否 = 承認外の過剰報告の正例) | `test_positive_landed_referenced_offrepo_copy_is_suppressed` |

M10 は `DW-M01` が要求する「受理集合を縮小する wave における、承認外の過剰拒否を検出する正例」である
(ここでの過剰拒否 = 抑止すべき既知の [T-574] 型を抑止できないこと)。

## scope 外として裁定パッケージへ返すもの (実装しない)

- [T-593] 事項 1(c) = path 一致・blob 不一致の第 2 警告カテゴリ (A-7)。
- [T-593] 事項 4 = refs snapshot 比較と再試行 (A-8)。
- [T-593] 事項 6(a) = `test_s8c_preregistration_invariant.py` の合成 commit 隔離。
- ack 台帳 (a)、即時 prune (d) — ユーザーが明示的に不採用にした。
- hardlink と root symlink 交換への防壁 (A-3 の残り)。単独運用者環境では意図的操作を要し、
  実装コストが便益を上回る。**残存 risk として worklog に明記する。**
- 10 倍規模のスケール実測 (B-6)。`DW-G02` により 1 cycle 後へ送る。
