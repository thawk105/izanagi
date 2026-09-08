# 段 4 裁定 — [T-2396] A-1 受領証の公開を os.link() へ改める

親が段 2 プラン (`artifacts/s2-plan.md`) と段 3 相談 2 本
(`artifacts/s3-consult-sol.md` = 正しさ境界レンズ、`artifacts/s3-consult-luna.md` = 整合と実効性レンズ)
を読み、real/refuted と採否を裁定した。**プラン v2 は「段 2 プラン + 本裁定の採用項目」である。**

## A. 採用する所見 (scope 内、実装する)

### A-1 [sol 所見 7、致命的] cleanup が公開済み受領証の最後の link を消しうる — **採用**

hard link 公開では staging と宛先が**同じ inode** になる。公開後に第三者が
`unlink(staging); rename(destination, staging)` を行うと、cleanup の `(st_dev, st_ino)` 照合は
通ってしまい、`unlink(staging)` が受領証の最後の link を消す。**rename 公開には無かった破れで、
本 wave の機構変更が作り出す。** 成果物影響: 公開済みの group receipt が消え、bytes も回収できず、
3 job は受領証を見つけられず bench に入らない (attempt-0002 と同じ 0 点)。

**採用する修正:** cleanup へ宛先も渡す。`published=True` の経路では、staging を unlink する前に
**宛先が存在し、その `(st_dev, st_ino)` が staging identity と一致すること**を必須にする。
一致しない・宛先が無いなら **unlink せず** `PaperStoryError` で止める (公開状態不明として fail-closed)。
`published=False` の経路は現行どおり staging identity だけを見る。

### A-2 [luna 所見 9] 公開後 cleanup failure の終端 — **採用 (プラン案を維持し、意味を明示する)**

公開はどちらの経路でも**最後の手番**である (`_run_submit_v3` は `:3252` で `return 0`、
`_run_complete_v3` は `:4262` で `return 0`)。したがって cleanup failure 時点で受領証は既に
公開済みで、後続処理は無い。

- **rc は非ゼロのまま** (silent success にしない)。staging 撤去の不変条件が破れたことを黙らない。
- **`submission-failure.json` を書かない** (プラン案どおり)。公開済みなのに失敗台帳を作るのは虚偽。
- **追加要件:** `_PublishedReceiptCleanupError` の message は「受領証は公開済みである」ことを
  明示的に述べる。rc 非ゼロを「投入されなかった」と読み違えないようにするため。
- luna の代案 (cleanup failure を非致命の診断にする) は不採用。**受理集合を広げず、
  破れた不変条件を黙らせない側を採る。**

### A-3 [luna 所見 10 / sol 所見 13] completion の AST wiring test を挙動テストへ置き換える — **採用**

`_publish_completion_receipt` が呼ばれていることを数える AST 検査は、
completion だけを `lexists` + `os.replace` へ退化させた実装を通してしまう (sol が具体コードで実証)。
**AST wiring test は作らない。** 代わりに submission と同型の**挙動**テストを completion にも置く:
`os.link` 呼出し直前に staging が canonical bytes で完成しており宛先が不在であることを観測し、
本物の link へ委譲する境界テスト。

### A-4 [luna 所見 12] 宛先 directory の fsync 変異を殺す検査が無い — **採用**

cleanup 自身も同じ parent を fsync するため「1 回呼ばれた」検査では変異が生き残る。
**事象順** `link → 宛先 parent fsync → staging 撤去 → parent fsync` を観測する焦点テストを 1 本置く。

### A-5 [luna 所見 11] 変異の単独帰属 — **採用 (登録内容を組み替える)**

`os.replace` 置換・staging 撤去削除・`FileExistsError` 握り潰しは複数テストが同時に赤にする。
`DW-M01` に従い、**単独帰属が成立する gate へ再照準した集合**を下の C 節で事前登録する。
帰属は段 6 の probe で実測し、成立しない項は登録から外して再照準する。

### A-6 [luna 所見 18] 余分な実装 pin を作らない — **一部採用**

completion 側に**新しい exact 英語 message の pin を作らない**。負例は例外型と挙動
(宛先 bytes 不変・staging 不在) で判定する。submission 側の既存 prefix
`no-replace submission receipt publish failed: ...` は現行挙動なので維持する。

### A-7 [sol 所見 12 / luna 所見 17] probe の一般化 — **採用 (記録の書き方の制約)**

親の probe が証明したのは「2026-09-08 00:35 JST、durable base 直下の scratch directory で、
その 3 操作がその結果を返した」ことだけである。記録・insight では射程をその directory と時点に
限定して書き、「Lustre 一般で `os.link` が通る」とは書かない。実装への影響は無い。

## B. real だが scope 外 (実装しない。裁定パッケージとしてユーザーへ返す)

| # | 所見 | 裁定理由 |
|---|---|---|
| B-1 | [sol 6] `_exclusive_write_bytes` が staging 作成後の write/fsync 失敗で partial staging を残す | **本 wave が作る破れではない** (現行コードも同じ)。共有 helper `:796-814` の改修は他の全利用者 (intent、barrier、WAL 等) を巻き込む。D1732 の射程外 |
| B-2 | [sol 8] staging basename が PID だけで決まる (旧 PID 残留・check 後注入の TOCTOU) | 同上。現行と同一で本 wave は変えない。命名規約の変更は freshness gate の予測可能性と表裏で別論点 |
| B-3 | [sol 2/3] 非協調な同 uid writer による parent 差し替え・staging 差し替え | rename 公開でも同じく成立し、**本 wave が作る破れではない**。threat model 自体の裁定が要る |
| B-4 | [sol 9] v3 `complete` の completion staging を不可逆成果物の作成前に予約・検査する | 新しい失敗の引き金は極めて狭い (同一 PID の先行 crash が必要)。かつ `complete` は result_root 作成後に失敗すれば**現行でも**再開できない。`DW-G02`/`DW-G04` により 1 cycle 後へ送る |
| B-5 | [luna 15 / sol 10] `receipts/submission-failure.json` も staging + no-replace 公開にする | **D1732 の射程外** (group submission / completion / materialize の 3 つを名指し)。失敗台帳の意味と retry policy が別論点 |
| B-6 | [sol 11] materialize の fallback が排他性を落としたまま残る | D1732 が「materialize 側も同族として棚卸し」とした結論そのもの。directory 公開に `os.link` は使えない (`:8266` が `mkdir` で staging を作る)。設計変更は別裁定 |

## C. 変異事前登録 (DW-M01、実装前)

対象は `orchestrator/campaign/paper_story_a1_paired.py` の新 `_publish_receipt` / `_remove_receipt_staging`
とその caller。**段 6 の probe で単独帰属を実測し、成立しない項は登録から外して再照準する。**

| ID | 変異 | 想定 owner (単独で赤にするテスト) |
|---|---|---|
| M-01 | cleanup の**宛先 identity 要求**を削除する (A-1 の防壁) | 同一 inode 移動の負例 |
| M-02 | `_remove_receipt_staging` の `(st_dev, st_ino)` 照合を削除する | 差し替え staging 保存テスト |
| M-03 | link 直後の**宛先 parent の `_fsync_directory` を削除**する | 事象順テスト (A-4) |
| M-04 | 事象順を入れ替え、staging 撤去を宛先 fsync より**先**に行う | 事象順テスト (A-4) |
| M-05 | `os.link(...)` を `os.replace(...)` へ意味的に置換する (keyword を外す) | 既存先 負例 (submission) |
| M-06 | **completion だけ** `lexists` + `os.replace` の check-then-replace へ退化させる | completion 境界テスト (A-3) |
| M-07 | `FileExistsError` を握り潰して成功として返す | 既存先 負例 (completion) |
| M-08 | 公開成功後の staging 撤去を行わない | 正例 (staging 不在) |
| M-09 | `_PublishedReceiptCleanupError` を素の `PaperStoryError` にする | v3 の「公開済みなら failure receipt を書かない」テスト |

## D. プラン v2 で実装するもの (確定)

段 2 プランの production 変更を基礎とし、次を加える。

1. `_publish_receipt(path, value, *, receipt_kind)` を新設し、`os.link(staging, path, follow_symlinks=False)`
   で公開。`_publish_submission_receipt` / `_publish_completion_receipt` は薄い wrapper。
2. `_receipt_staging_path(path, *, receipt_kind)` / `_remove_receipt_staging(...)` へ改名。
   staging suffix は submission `.s-<pid hex>`、completion `.c-<pid hex>`。
3. **A-1:** cleanup へ宛先を渡し、`published=True` では宛先が同一 identity で存在することを
   unlink の前提にする。不成立なら unlink せず fail-closed。
4. **A-2:** `_PublishedReceiptCleanupError` を維持し、message で「公開済み」を明示。
   `_run_submit_v3` は本例外で failure receipt を書かない。
5. completion の 2 caller (`_run_complete_v3` `:4260`、`run_complete` `:4350`) を共通 publisher へ。
6. materialize 経路・`_renameat2_directory`・公開機構定数・`submission-failure.json` は**無変更**。
7. 受領証 JSON の schema・field・canonical bytes は 1 byte も変えない。
8. テスト: 既存 7 本を弱めずに機構へ追随させ、A-3 / A-4 / A-1 の負例と completion の正例・負例を足す。
   **AST wiring test は作らない。**

## E. 不変条件 (段 6 まで不変)

- create-only の排他性を落とさない。既存先への公開は必ず失敗し、既存 bytes を 1 byte も変えない。
- 完成した staging への hard link 以外で完成名を作らない (部分公開の窓を作らない)。
- 公開済みの完成名を、cleanup も含めどの経路でも消さない。
- 規律 2: correctness gate・verifier・受理集合を緩めない。既存テストの期待値を反転・緩和・skip しない。
- 要求外の gate・検査・台帳・互換層・一般化を足さない。
