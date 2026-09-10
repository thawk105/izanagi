# [T-817] verifier-policy epoch と witness なし COMMIT の再評価 — 逐語 (2026-08-11)

wave = `dev-wave-t817-verifier-epoch` / branch `worktree-dev-wave-t817-verifier-epoch`
base = main `276ab6cc` / **実装差分ゼロ** (段 4 で「実装しない」と裁定し、`4→7→8→9`)

## 何をしたか

裁定 [T-817] (a) 条件付きが自ら課した条件 —「実装 wave はまずログ残存率を実測してから設計する」—
を実行し、**残存率 0** を確定した。その過程で、裁定時点で未見だった事実が 4 件出た。

1. **突き合わせ対象は空** — 既存 WAL の 459 committed attempt (P2-2 は 24) のうち、対応する
   ccbench stdout が残っているものは 0 件。git 全史でも `output/campaigns` 配下に stdout 系 path は
   存在しない。pipeline は stdout をその場で parse して捨てる (保存経路が無い)。
2. **突き合わせは、ログが残っていても健全に作れない** — WAL と stdout を「同じ run」だと束縛する値
   (execution nonce) がどこにも記録されておらず、`trace_bin` は identity 検査に使うなと実装が明記する
   表示用 prefix。同伴 receipt を作っても別 run の counter が通る。[T-756] の blocker と同型で、
   作れば規律 2 に反する経路を自作することになる。
3. **除外の面が裁定の想定より広い** — 旧 certified / 旧 fitness を読んで winner や certified 集合を
   作る生きた経路が 8 つ以上ある (`p2_2_report` と `critic/digest` は `certified` を見ずに committed +
   median で winner を選ぶ)。**敵対レンズ 2 本が独立に同じ取り残しを発見した**。
4. **識別子が衝突する** — `verifier_policy_sha256` は未実装の設計語ではなく
   `reflux_origin_ledger.py` の実装済み field。ユーザーが本 wave に設定した停止条件に該当する。

副産物として、**epoch を入れる土台が既に存在する**ことも判明した — `campaign.lock` v2 の authority は
enforcement source closure 8 path の blob SHA-256 を記録しており、その中に witness gate 本体が住む
`pipeline.py` が含まれる。名前が付いていないだけである。

## 一次資料

| ファイル | 中身 |
|---|---|
| `verbatim/ruling-package.md` | **裁定パッケージ (本 wave の主成果物)。4 問と親の推奨** |
| `verbatim/brief.md` | 段 1 親 brief (実測 M1〜M11、新事実 N1/N2、provisional 裁定 P1〜P4) |
| `verbatim/s2-plan.md` | 段 2 プラン (file:line 粒度。`verifier_policy_sha256` を未実装と誤認) |
| `verbatim/s3-lens-a.md` | 段 3 レンズ A = 正しさ境界 (**NO-GO**。BLOCKER 1 + HIGH 4 + MEDIUM 2) |
| `verbatim/s3-lens-b.md` | 段 3 レンズ B = 全層被覆 (**NO-GO**。consumer 取り残し 8 経路、namespace 衝突) |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (13 所見すべて real、refuted ゼロ。実装しない理由) |
| `log-survival-scan.txt` | `output/` 全走査の生結果 (10,291 ファイル、実 stdout 193 件の一覧) |

## 親自身の誤りで、敵対検証が訂正したもの

- **(P1) 誤り** — 「現行 certified 選択 = replay/guided」は狭すぎた。8 経路が残る。
- **(P2) 誤り** — 「不在 = 歴史保存」は `screening_search_config` の局所的な性質で、campaign identity
  全体には成立しない。
- **(P3) 部分的に誤り** — 記録の形からの epoch 導出は payload 偽造に弱く、診断情報に留めるべき。
- **(P4) 未充足** — 「残存 0 件を恒真な検査にしない」と書いたが、提案された機構は実 corpus では
  永久に発火せず、synthetic fixture だけが非恒真性を装う形だった。
- **M5 が不正確** — 「凍結 producer は走らせない」は誤り。`test_s1_known_axes_freeze.py:85` が実 repo に
  対して `build_document()` を走らせる。bytes は不変でも検証は再構築を通る。
- **N1 の単位が誤り** — 除外の単位は verify 記録 571 ではなく committed attempt (459 / P2-2 は 24)。

## 変異

**免除。** 実装差分ゼロの「実装しない」裁定のため (DW-S04)。
