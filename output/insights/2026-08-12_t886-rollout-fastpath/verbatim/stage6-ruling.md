# 段 6 裁定 — レビュー 2 本の採否 ([T-886])

統合 commit = `c691c8e7`。レビュー = `stage6-lensA.md` / `stage6-lensB.md` (両 rc=0)。
焦点走 = **190 passed / 0 failed / rc=0** (246.76s、計算ノード)。

## 採用 (6 件 → fix へ)

| # | 出所 | 深刻度 | 裁定 | 根拠 |
|---|---|---|---|---|
| F1 | lensA 2 / lensB 1 | BLOCKER | **real・採用 (独立 2 例)** | `PermissionError` は `OSError` 派生なので、狭い catch 変異が生き残る。段 4 A1/R2 の `MemoryError` 契約を検査できていない |
| F2 | lensB 2 / lensA 17,18 | BLOCKER | **real・採用 (独立 2 例)** | 既定経路だけ pin を外す変異が全新規テストを通り、**改善ゼロで全部緑**になる。配線テストが `False` しか渡していない |
| F3 | lensA 1 | BLOCKER | **real・採用 (親が実装方針を変更)** | fast attempt 全体の broad catch は**候補自身の例外まで飲んで再試行**する。これは段 4 が認可した「非候補 file を観測しない」拡大の**外側**。例外を 3 区画に分け、候補の内容照合だけ伝播させる |
| F4 | lensA 3 | MUST-FIX | **real・採用** | sentinel が毎回投げるため `except BaseException` 変異が fallback 2 回目で通ってしまう |
| F5 | lensA 4 | MUST-FIX | **real・採用** | pinless の「新コードに触れない」を結果でしか見ていない。rglob pattern を固定する |
| F6 | lensA 5 / lensB 2 後半 | MUST-FIX | **real・採用 (独立 2 例)** | 深さ固定なので `glob("*/*/*/*/*/"+p)` 変異が生存。異なる深さ 2 case にする |

## 記録のみ (fix しない)

- **lensB 4 — 機序の記述が誤り。採用し、記録の定型を訂正する。**
  親は段 4 R4 で「warm metadata walk の係数を約 270 倍下げる」と書いたが、これも不正確。
  narrow `rglob` も同じ tree を最後まで歩くので **walk の費用は before/after で同じ**である。
  消えているのは**無関係 rollout の open / stream / session_meta candidate parse**。
  → **正しい定型 = 「無関係 rollout の内容 scan を除去。directory walk の線形項は残る
  (実測 2,946 file で約 17ms、5.5µs/file)」。** cold cache 倍率は**未測定・効果不明**と明記する。
- **lensA 表 / lensB 表 — 新規テストは 17 本ではなく 18 関数 (26 parameterized case)。** 訂正する。
- **lensB 5 (NIT)** — fallback 時は候補の session_meta も二重に読む。段 4 A11 に追記して記録する。
  **正しさのために fallback を狭めない**方針は維持。
- **lensA 表 #9 / lensB 表 #9** — opaque-ID テストは親 matrix の kill 数 0 だが、
  pinless 互換性の回帰テストとして残す価値がある。F5 で検出力を足す。

## refuted (実装も記録もしない)

- **lensB 3 の一部 — 「並行 wave の `_filesystem_file_set` 改善が main に入っており before/after が
  混成になる」は誤り。** 親が実測: `be5018eb` / `dff79a0c` は先方 branch 上にあり、
  取り込み済みの本 worktree には**入っていない** (`parent_is_root_git` の grep が 0 件)。
  before/after は同一 checkout・同一 process・同一コードで測っており base 混在はない。
- **lensB 3 の残り (ABBA 多 block 要求)** — 部分 refuted。効果量が 200 倍で、
  逆順走でも before が 4.14s と変わらない以上、cache 順序では説明できない。
  **多 block は実施せず、「2 順序 2 走。ABBA 多 block は未実施」と限界を明記する**方針とする。
- **lensA 1 の代替案「親裁定を再試行まで拡張する」** — 採らない。F3 で拡大を閉じる方が安い。

## 変異 matrix の更新 (段 4 §4 を改訂)

- **M7 改訂:** 逐語 `rglob` → 非再帰 `glob` に限定。加えて **M7b = 固定深度 `glob("*/*/*/*/*/"+p)`** を追加
  (F6 の 2 深度 case が殺す)。
- **M10 改訂:** `except Exception` → `except (ValidationError, OSError, ValueError)`。
  F1 の `MemoryError` テストが殺す。
- **M11 新設 (kill 枠):** 候補の内容照合例外を握り潰す (F3 の逆)。F3 の訂正済みテストが殺す。
- **P4 新設 (diagnostic pin 枠):** 既定経路だけ pin を外す条件付き配線 (F2 の変異)。
  受理集合を変えないので kill に数えず diagnostic pin へ入れる。
- 既存 M1〜M6・M8・M9 と P1〜P3 は据え置き。既存 gate が先取りする 2 件は効力に数えない。

期待 node は **fix 後の最終 commit で完全集合を再導出する** (DW-M07)。
