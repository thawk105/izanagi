# 段 6 裁定 (2 巡目) — 焦点再レビューの partial 11 + RG-1〜4 (2026-08-04)

closed 17 は採用。partial 11 と RG-1〜4 を以下のとおり裁定する。fix は 2 巡目 (上限 3 巡)。

## 親裁定 (コード変更なしで閉じるもの)

- **RA-4 / RB-15 の残余 (pre-head-commit の seal event 平文) = refuted-in-part。**
  開示点は「producer による seal 要求」であり、その crash 窓の raw bytes を読める観測者は
  平文を既に保有する producer 自身か trusted machine に限る。generator role は ledger file への
  経路を持たない (P2 の遮断は role projection 側)。API は未 commit event を可視化しない
  (M-N16 で検査済み)。**module docstring に「seal 要求 = 開示点。seal event の fsync 後・
  head commit 前の crash は、開示済みだが未 commit の event bytes を raw 観測者に残す」を明記する**
  (fix 子への指示 F-1)
- **RA-5 の残余 (salt の予測不能性) = leaf では強制不能。** 契約として docstring に
  「salt は producer が CSPRNG で生成する。leaf は長さ・一意性のみ強制する」を明記し (F-2)、
  テスト helper の決定的 salt は乱数由来へ置換する (F-3)
- **RG-4 (既存期待値 T:767 の変更) = 親が事後承認する。** Δ4 改訂 (clean base B での修復) に
  整合する期待値移行であり、設計上正しい。ただし fix 子が「止めて報告」する契約に反した点は
  手順違反として worklog fragment に記録する。snapshot に旧期待値が保存済み
- **M-N12 = diagnostic sensitivity pin へ降格** (`DW-M08` の別枠)。canonical-byte 検査が
  同じ入力を拒否する冗長層であり、受理集合 kill は成立しない。変異台帳に降格として記録
- **M-N11 (旧) = retire + erratum。** Δ4 改訂により登録 operator (「unrelated tail を truncate
  する誤実装」) の前提が反転した。旧 ID は erratum つきで退役させ、**M-N11r** (未完 tail
  truncate 修復を除去 → clean-base exact repair が失敗する) を新 ID として登録する
  (`DW-M02` の「初回結果は消さず erratum」に従う)

## fix 子への指示 (2 巡目)

- **F-1 / F-2:** 上記 2 件の docstring 契約追記
- **F-3:** テスト helper の salt を os.urandom 由来へ置換 (決定的 hash をやめる)
- **F-4 (RA-2 残余):** 未完 tail の検証つき truncate を store open / replay の全入口
  (read 経路含む) で行い、reopen 後の `read_origin()` が post-repair の clean commitment B を
  返すことをテストで固定する
- **F-5 (RA-8/RB-6/RB-13/RG-1):** 時間待ち (0.25 秒) を証拠にする判定をすべて排除し、
  決定論的な状態機械へ置換する — 待ち側は `flock(LOCK_EX|LOCK_NB)` の EWOULDBLOCK を
  「保持中は必ず失敗」として assert し、保持解放後に取得成功を assert する
  (file gate で順序を固定)。inode 差し替え vector も LOCK_NB probe で状態遷移を検査する
- **F-6 (RG-2, M-A2 の忠実な anchor):** 登録 operator どおり「global flock → per-origin flock」
  への退化を撃つ: 異なる 2 origin を file gate で同じ global base 読取点へ到達させ、
  global lock なら片方が EWOULDBLOCK/直列化、per-origin lock なら双方進行して global head
  chain の衝突が検出される、を状態ベースで assert する vector を追加
- **F-7 (M-N11r):** 新 operator に対応する負例 (truncate 除去 → clean-base repair 失敗) の
  帰属を確認し、既存 T:964–1020 が単一赤で撃つことを静的確認
- **F-8 (M-A5):** 両層変異として再登録する: L:2499–2504 (exact-continuation composite) と
  replay gate (L:1964–1977 相当) の**両方を同時に除去**したときだけ operation B が受理される
  ことを狙う。テストは B の拒否を**受理集合で** assert する (診断文字列 assert T:45–50 に
  依存しない) よう強化する
- **F-9 (RA-11):** feasibility を「実 serialize による構築的上限」へ置換 — admission 時に
  当該 authority の最大 frame (batch_min 個の dummy 64hex commitment、Kmax 個の class) を
  実際に構築・serialize して MAX_RECORD / MAX_LEDGER に収まることを検査。負例:
  `batch_min=qmax=floor` が envelope に収まらない authority の admission 拒否
- **F-10 (RA-12/RB-14):** file open を `O_RDONLY|O_NONBLOCK|O_NOFOLLOW` + `fstat` の
  type 判定に変え、FIFO で hang しない。FIFO 負例 (timeout 付き) を追加
- 契約は 1 巡目と同じ (S05 全文継承 + 既存期待値不変更。ただし F-4/F-5 での
  待ち時間 assert の置換と、RG-4 で親承認済みの T:1038 は現状維持でよい)

## 変異台帳の確定 (fix 2 巡目後、`DW-M07` anchor 再検証 → 本走)

KILLED 候補として本走: M-A1, M-A2(F-6 で忠実化), M-A3, M-A4(再照準), M-A6,
M-N1〜M-N10, M-N11r, M-N13〜M-N18。
両層登録: M-A5 (kill 期待を事前登録、`DW-M04`)。
diagnostic sensitivity pin: M-N12。
retire + erratum: M-N11(旧)。
