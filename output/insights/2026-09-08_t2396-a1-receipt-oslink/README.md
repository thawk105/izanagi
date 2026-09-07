# A-1 受領証の公開を os.link() の hard link へ改めた — 機構の差し替えが撤去処理へ受領証削除の経路を開きかけた (2026-09-08)

- `authority: none` / `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- 裁定の正本: `docs/decisions.md` の D1732 (2026-09-07、/rulings 全件 第 13 回、推奨どおり)。
- 一次資料: `output/insights/2026-09-07_a1-pilot-attempt-0002/README.md` §5・§7、`docs/failures.md` F870。
- 本 wave は **A-1 の測定を 1 点も行っていない。** 直した経路がこれで通るかは、次に pilot を投入するまで
  実機で確かめられていない (§7)。

## 1. 依頼と実施範囲

依頼は「group submission receipt の公開を `os.link()` へ改める。`complete` の completion receipt と
materialize 側も同族として棚卸しし、同じ変更単位で扱う。正例・負例を同じ commit へ入れる。
Codex `role=author` を守る。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。

実施したのは実装 1 単位、敵対相談 2 本、敵対レビュー 2 本、fix 2 本、焦点走 5 回、
変異 2 巡 (probe + 本走)、本記録である。

## 2. 着手前に測り直した裁定の前提

policy `execution.durable_measurement_base` が固定する directory の直下に scratch を作り、
production と同じ 3 操作を 1 回ずつ実行した (2026-09-08 00:35 JST、`stat -f` の fstype = `lustre`)。
probe は 80 行の使い捨て script で、repo の外 (wave の job directory) に置いたまま repo へ入れていない
— 実行可能資材は Codex `role=author` を要求し、probe-only は免除にならないためである。
再現には `ctypes` で `renameat2` を呼び、同じ scratch directory に対して空き先と既存先で
`os.link` を 1 回ずつ試せばよい。下表がその全出力である。

| 操作 | 結果 |
|---|---|
| `renameat2(RENAME_NOREPLACE)` → 空き先 | errno 22 EINVAL |
| `os.link()` → 空き先 | 成功、`nlink=2`、**staging は残る** |
| `os.link()` → 既存先 | errno 17 EEXIST、**宛先 bytes は不変** |
| staging を unlink した後の宛先 | bytes は不変 |

**この probe が証明したのは、その directory・その時点でこの 3 操作がこの結果を返したことだけである。**
別 OST、quota 逼迫、同時実行、nlink 上限、別 mount 点、計算ノード側から見た同じ path は測っていない。
「Lustre 一般で `os.link` が通る」とは主張しない。F870 の欠陥が現在も再現することは確かめた。

## 3. 実装した範囲

- 受領証 file の共通 publisher を新設し、完成した staging への
  `os.link(staging, path, follow_symlinks=False)` で公開する。既存先は `PaperStoryError` で拒否し、
  既存 bytes を 1 byte も変えない。
- staging basename を kind ごとに分ける (submission と completion)。
- rename と違い hard link は staging を消さないので、公開成功後に staging を撤去する経路を足した。
- `complete` の completion receipt (v2 / v3 の 2 経路) を同じ publisher へ揃えた。
  従来は完成名を `O_EXCL` で直接開いてから書いており、書込み途中の停止で千切れた bytes が
  create-only 名を占有し得た。
- 受領証 JSON の schema・field・canonical bytes は 1 byte も変えていない。

## 4. 実装しなかった範囲 (棚卸しの結果)

- **materialize の bundle 公開。** staging を `mkdir` で作る **directory** であり、通常の user process は
  directory の hard link を作れない。probe + `PUBLISH_EINVAL_FALLBACK`、`renameat2` helper、
  公開機構定数、materialization のテストはすべて無変更で残した。
  driver 自身が書いている「fallback は非協調な writer に対して atomic no-replace ではない」という
  限界もそのまま残る。
- **`receipts/submission-failure.json`。** D1732 が名指ししたのは group submission receipt、
  completion receipt、materialize の 3 つで、失敗台帳はその外にある。
- **file system probe・機構選択 evidence の新設。** `os.link` は Lustre でも tmpfs でも通るので
  選択肢が要らない。発火経路の無い条件付き機能を main へ入れることになる。

## 5. 段 3 が着地前に捕らえた致命的所見

段 2 プランは公開を `os.link` へ替えつつ、撤去側の `(st_dev, st_ino)` 照合を **rename 時代のまま**
据え置いていた。段 3 の相談 (正しさ境界レンズ) が次の並びを実証した。

1. `os.link` により staging と宛先が同じ inode I を指す。
2. 撤去の直前に第三者が `unlink(staging)` を行い、続けて `rename(destination, staging)` を行う。
   I の唯一の名前が staging になる。
3. 撤去処理の `staging.lstat()` は regular file かつ identity I なので照合を通る。
4. `unlink(staging)` が I の最後の link を消す。
5. 例外は出ず、publisher は成功を返す。宛先は存在せず、受領証 bytes も回収できない。

**rename 公開では公開後に staging 名が消えるため撤去処理そのものが無く、この破れは存在しなかった。**
本 wave の機構変更が新しく作る破れである。

対応は、撤去へ宛先も渡し、公開済み経路では **宛先が存在し identity が staging と一致すること**を
unlink の前提にすること。不成立なら unlink せず fail-closed で止める。
`docs/failures.md` の該当 F と `docs/decisions.md` の該当 D が正本。

## 6. 親が refuted と裁定した所見

| 所見 | 裁定 |
|---|---|
| 宛先確認と unlink の間に残る競走 | real。ただし非協調な同 uid writer を前提とし、その writer は受領証を直接消せるので file 操作では閉じられない。**threat model 自体の裁定へ返す。** |
| link 後の最初の fsync 失敗が生の `OSError` で抜ける | `_fsync_directory` は変更前から生の `OSError` を投げ、v3 submit の `except PaperStoryError` は捕まえない。**偽の failure receipt は書かれない。** 変更前後で挙動は同一 |
| `_exclusive_write_bytes` が write / fsync 失敗で partial staging を残す | real。本 wave が作った破れではなく変更前と同一。共有 helper なので全利用者を巻き込む。**裁定へ返す** |
| staging basename が PID だけで決まる TOCTOU | real。変更前と同一。命名規約の変更は freshness gate の予測可能性と表裏で別論点 |
| v3 `complete` の completion staging を不可逆成果物の作成前に予約・検査する | real。引き金は同一 PID の先行 crash が必要で極めて狭く、`complete` は現行でも result root 作成後の失敗から再開できない。**1 cycle 後へ送る** |
| `FileExistsError` 専用 catch が冗長 | create-only 契約を明示し、変異の単一行 target になる。防御コードの追加ではない。**残す** |
| `_fsync_directory` 内部の実 fsync 消失 / 波及列挙の精度 / duration 台帳の旧名 entry | 本 wave の変更面でない、または実装に影響しない |

## 7. 名乗らないこと

- **A-1 pilot が通るとは言えない。** 本 wave は測定を 1 点も行っていない。直した公開経路が実機の
  投入で通るかは、次に attempt を投入するまで確かめられていない。
- **Lustre 一般で `os.link` が使えるとは言えない** (§2)。
- **非協調な同 uid writer に対して受領証公開が安全とは言えない** (§5・§6)。閉じたのは
  決定的な順序だけで、宛先確認と unlink の間の競走は開いている。
- 受入全走の結果は本文書に含まれない。本記録 commit を基準に投入する。

## 8. 検査

- 焦点走・consumer 走 1462 passed / 0 failed / 4 skipped (login node、clean tree、72.65 秒)。
  対象は `test_paper_story_a1_job_contract.py` と、変更した production module を参照する
  consumer test 10 file、および制約 meta-test。
- 変異 probe (10 件、全件 SURVIVED 期待) で観測 node を集め、本走は **10/10 KILLED、
  期待 node 完全一致、SURVIVED 0 / MISMATCH 0**。baseline は PASSED (171 passed)。
  `repo_head` は `2c1127c94ea380ddaa3fcb7e63be52cc8058f094`。
  spec と台帳は `mutation-spec-final.json` / `mutation-ledger-final.json`、
  probe 巡は `mutation-spec-probe.json` / `mutation-ledger-probe.json`。
- 単独帰属が成立するのは 3 件 (`m01b`、`m02`、`m03`) で、残り 7 件は複数 node が同時に落ちる
  冗長 kill である。**単独帰属のために既存の正当な assertion を削っていない。**
- 実装の行数増で赤になった機械検査 2 件は実測して追随させた。deferred gate 台帳の行番号
  (7146 → 7209) と、受入 duration 台帳の被覆 (89.993511% → 90% 以上)。

## 9. 変異一覧

| ID | 変異 | 結果 |
|---|---|---|
| `m01a` | 公開済み撤去が宛先の不在を許す | KILLED (2 node) |
| `m01b` | 公開済み撤去が宛先 identity を見ない | KILLED (1 node) |
| `m02` | staging の identity 照合を落とす | KILLED (1 node) |
| `m03` | link 直後の宛先 parent fsync を落とす | KILLED (1 node) |
| `m04` | completion の staging kind を submission にする | KILLED (3 node) |
| `m05` | `os.link` を `os.replace` へ退化させる | KILLED (13 node) |
| `m06` | completion だけ `lexists` + `os.replace` へ退化させる | KILLED (3 node) |
| `m07` | `FileExistsError` を握り潰して成功扱いにする | KILLED (3 node) |
| `m08` | 公開成功後に staging を撤去しない | KILLED (11 node) |
| `m09` | 公開済み撤去失敗の専用例外型を落とす | KILLED (3 node) |

`m06` は段 3 の相談が「予定テストを生存しうる」と名指しした形である。段 6 のレビューが
**v3 の completion 公開点を実行するテストが repo 全体に 1 本も無い**ことを見つけ、fix で足した
挙動テストが `m04` と `m06` の owner に入った。

## 10. 偽装入力の判定

外部由来の内容 (子の出力、テスト出力、probe の実行結果) に、正しさゲートを緩めるよう促す指示は
見つからなかった。子の完了報告に含まれる `closed` の申告は証拠として数えず、
コードとテストの現物および親の実走だけを根拠にした。

## 11. 次の wave の出発点

- A-1 pilot の attempt-0003 を投入し、group receipt の公開が実機で通ることを初めて確かめる。
  §7 のとおり、それまで「直った」とは言えない。
- 裁定へ返した 4 件 (threat model、failure receipt、`_exclusive_write_bytes` の partial staging、
  v3 completion staging の事前検査) は worklog の次の一手に登録した。
