# 段 1 brief — [T-786] docs 予算棚卸し wave

## scope

`docs/dev-wave/**` の L1 / L1.5 / L2 単節予算と `.claude/commands/*.md` の byte 予算に対し、
(A) 陳腐化節のテスト化・縮約で余白を作り、(B) 滞留 8 件の入庫可否を package で一括提示し、
(C) rulings command への 2 行を優先同梱し、(D) [T-773] 待ち手正本の結線を行う。

## 確定済みユーザー裁定

- [T-786] (a)。S9 (a) の独立審査認可を根拠に棚卸し wave を 1 本立てる。
- [T-127]。**予算値の上限は上げない。空けるが第一。** 入らない分だけ引き上げ可否を審査結果で返す。
- [T-773] (a)。待ち手正本 `tools/dev_wave_wait.py` を command 段 6/9 と `DW-O01` / `DW-C00`
  から機械参照させる。[T-738] (c) の再訪を含む。
- [T-784]。**予算のために安全義務を削除・弱化する案は採らない。**
- `docs/skill-self-improvement.md`: L2 節の削除を裁定パッケージへ送れるのは
  「発火実績なし × テスト/機械検査で義務代替済み」の両条件を満たす節だけ。実施はユーザー裁定に限る。

## 実測 (親、2026-08-11、worktree `dev-wave-t786-docs-budget`、base `0c336b8e`)

`tools/check_docs.py` の三層分類を repo 外 script で再現した実測値。

| 予算 | 現在値 | 上限 | 余白 |
|---|---|---|---|
| L1 unique footprint | 10,625 | 10,625 | **0** |
| L1.5 unique footprint | 9,554 | 9,566 | **12** |
| L2 最大節 `DW-O09` | 935 | 1,000 | 65 |
| `.claude/commands/rulings.md` | 4,991 | 5,000 | **9** |
| `.claude/commands/dev-wave.md` | 9,497 | 9,500 | **3** |

滞留 8 件の所要は L1 側 ~350 bytes、L1.5 側 ~510 bytes、`DW-O09` 単節 ~128 bytes、
rulings ~250 bytes、dev-wave command ~150 bytes と見積もる (各起票の実測超過値の合計)。
**現状の余白では 1 件も入らない。空ける作業が先行しなければ本 wave の入庫はゼロになる。**

## 不変条件

1. 予算定数 (`DEV_WAVE_L1_BYTES_MAX` / `DEV_WAVE_L1_5_BYTES_MAX` /
   `DEV_WAVE_L2_SECTION_BYTES_MAX` / `COMMAND_LIMITS`) を**引き上げない**。
2. 安全義務を削除・弱化しない。縮約は意味等価に限り、テスト化は
   「prose の義務を機械検査へ移す」だけで義務の外延を狭めない。
3. L2 節の削除は実施しない (ユーザー裁定事項)。削除候補は package で返す。
4. `DW-O09` pin 閉包: 本 wave が触る docs は SHA-256 whole-file pin の対象外だが
   (pin は cleanup-branches command と Codex skill のみ)、`tools/check_docs.py` の
   `REQUIRED_REFERENCE_SECTIONS` / `STAGE_UNCONDITIONAL_DISPATCH_CONTRACT` /
   各 literal 定数、`orchestrator/tests/test_check_docs.py`、
   `orchestrator/tests/test_dev_wave_launch_authority.py`、`.agents/skills/dev-wave/SKILL.md`
   が節 ID と逐語を pin する。編集時は同時同期する。
5. 実装面 (check_docs の新検査・テスト) は Codex `role=author` が書く。親は docs 本文のみ編集する。

## 成果物の形

- `docs/dev-wave/**` の縮約差分 + `.claude/commands/{dev-wave,rulings}.md` の差分。
- `tools/check_docs.py` の新規機械検査 + `orchestrator/tests/test_check_docs.py` の positive/negative。
- 入庫可否 package (worklog fragment + 裁定パッケージ) — 入った件・入らなかった件・
  引き上げ可否の審査結果を件ごとに書く。

## provisional 裁定 (親の暫定であり攻撃対象)

- **(P1) 待ち手正本の結線は L1 を増やす操作ではなく空ける操作にできる。**
  `DW-C00` の待ち手 3 義務 (1 条件 1 本 / 通知ごとに作り直さない / 生産者の死を待ち条件に含める)
  は `tools/dev_wave_wait.py` が既に実装しており、prose を canonical invocation の指示へ
  置換すれば L1 が縮む。同時に [T-738] (c) の pid 死判定禁止と [T-757] の mtime 停滞判定は
  「手書き待ち手を作らない」で構造的に不要化され、**追記せずに解決する**。
  純増検出力 = 現在 `tools/dev_wave_wait.py` を consumer へ束縛する機械検査は repo にゼロ
  (grep で runbook §7.3 の散文参照のみ)。本検査が初の束縛になる。
- **(P2) テスト化の対象は「機械検査が現に代替している prose」に限る。**
  代替の実在を検査 nodeid で示せない節は縮約対象にせず、意味等価な圧縮だけを試みる。
- **(P3) 滞留 8 件は同一予算を奪い合うため、入庫は費用対効果順とする。**
  優先度 = rulings 2 行 (ユーザー明示の優先同梱) > [T-773] 結線 (実害 2 例、F32 族) >
  [T-769]/[T-775](ii) (MISMATCH 4 例目の予防) > [T-775](i) > [T-765] > [T-784] >
  t657 候補 A/B。入らなかった件は引き上げ可否の審査結果を付けて返す。

## 成果物影響 (DW-G05)

- (A) を行わない場合: 滞留 8 件は入庫ゼロのまま滞留し続け、`DW-M08` の期待 node 誤りによる
  変異 matrix の MISMATCH が 4 例目以降も出て、wave あたり 1〜2 走が空費される。
- (D) を行わない場合: 手書き待ち手の自己マッチ死 (F32 族、独立 2 例) の再発経路が開いたままで、
  wave が無音死し受入結果が台帳へ入らない。

## 並列分割方針

段 2 は 1 本 (棚卸しは全体最適で、分割すると同じ予算を二重計上する)。
段 3 は 2 レンズ並列 — レンズ A = 安全義務の削除・弱化の検出 (縮約が意味等価でない箇所)、
レンズ B = 新設検査の恒真性・被覆漏れと、親の実測値・(P1)〜(P3) の一般化への攻撃。
段 5 は実装面 1 本 (check_docs + tests は同一ファイル群を触るため所有を分けられない)。
段 6 は敵対レビュー 2 本 (安全義務 / 検査実効性)。

## 受入・実測環境

Pegasus。受入全走は `tools/run_tests.py` の acceptance shape を余計な flag なしで、
受入 lease 取得後に背景投入する。実測は本 worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget`。
