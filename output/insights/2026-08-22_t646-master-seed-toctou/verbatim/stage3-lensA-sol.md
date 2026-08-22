## 1. P1 再検証

攻撃したが崩せなかった。

`run_campaign` の前処理は `s8b_floor_campaign.py:5638-5670` に閉じており、型・seam・pilot承認の検査だけで、ファイル書込みや測定を行わない。成功経路は必ず `s8b_floor_campaign.py:5672-5675` の `_require_supplied_protocol_authority` を通過し、その直後の唯一の戻り先が `_run_campaign_core` (`:5676-5688`) である。

CLI も通常 campaign 経路では、読込み・検証 (`:7080-7088`) の後に必ず `run_campaign` (`:7090-7097`) を呼ぶ。authority failure は `:7100-7104` で失敗終了し、core へ進まない。

- `--mode official` の早期拒否 (`:7067-7073`) は成功経路ではない。
- `reseal-protocol` 等の別サブコマンド (`:7006-7062`) は campaign 実行経路ではない。
- `_run_campaign_core` の直接呼出しは production caller ではなく、private core/test 用の別境界である。

## 2. fix の順序と TOCTOU

攻撃したが崩せなかった。

`head` は `s8b_holdout_freeze.py:1687-1689` で先に捕捉され、`_validate_floor_inputs` の呼出しは `:1714-1718` である。比較を `protocol_raw` 捕捉 (`:1362-1365`) の直後、canonical parse より前に置けば、`build_schedule` (`:1440-1448`) より確実に前になる。

HEAD がその間に変わる場合も、旧 `head` の blob と新 working tree bytes が不一致なら fail-closed になる。protocol bytes が同一なら受理されるが、master_seed を含む bytes も同一なので安全側である。candidate 書込みは `:1854-1860` まで発生しない。

ただし、実装時に `_validate_floor_inputs` 内で HEAD を再捕捉してはいけない。既存の `head` を必須 keyword として渡す必要がある。

## 3. シグネチャと既存テスト契約

攻撃したが崩せなかった。

`_validate_floor_inputs` の production caller は `s8b_holdout_freeze.py:1716` の一箇所だけで、テストは private helper を直接呼ばず `build_v2_g1_candidate` (`test_s8b_holdout_freeze.py:1602, 1680, 1756` 等) を呼んでいる。したがって、`head` を必須 keyword-only 引数にして caller を更新しても、確認できる既存 test contract は壊れない。

ただし新しい不変条件を検査するテストは不足している。少なくとも次を追加すべきである。

- working tree の protocol だけを変更した場合に `FreezeError` になること。
- reseal commit 後の HEAD blob と working tree が一致する場合に通ること。
- non-commit HEAD、HEAD tree entry の symlink/非 `100644` を拒否すること。

## 4. 実際に残る穴

### 4.1 HEAD が commit である保証がない — real

`s8b_holdout_freeze.py:1687-1689` は `git rev-parse HEAD` の結果が40桁hexかしか検査していない。`_blob_at_head` (`:319-326`) も object type が `blob` かしか見ていない。

失敗シナリオ:

1. Git ref の `HEAD` を commit ではなく tree object に向ける。
2. その tree に `output/s8b-freeze/floor_protocol.json` を置く。
3. working tree に同じ bytes の regular fileを置く。
4. `rev-parse` は40桁hexを返し、`cat-file HEAD:path` も blob を返すため比較を通過する。
5. commit ではないOIDが `frozen_at_head` (`:1737`) に記録される。

`git rev-parse --verify HEAD^{commit}` を使い、HEAD が commit であることを明示すべきである。

### 4.2 HEAD tree の mode を検査していない — real

Git では symlink (`120000`) も `cat-file -t` では `blob` である。したがって、HEAD 側が symlink または `100755` でも `_blob_at_head` は受理する。

失敗シナリオ:

- HEAD の対象 entry を `120000` または `100755` にする。
- working tree 側を同じ bytes の通常ファイルへ置換する。
- `_capture_regular_nofollow` (`:264-277`) は通常ファイルとして通り、`_blob_at_head` も blob として通る。

既存の floor campaign の `_head_blob_100644` (`s8b_floor_campaign.py:735-762`) と同様、`git ls-tree` で exact `100644 blob` を検査すべきである。

なお、working tree の対象ファイル自体が symlink の場合は `O_NOFOLLOW` により `:271-277` で拒否される。この部分は攻撃したが崩せなかった。

### 4.3 Git replace object を無効化していない — real

`s8b_holdout_freeze.py:292-316` の Git 呼出しは ambient Git authority を使い、`_blob_at_head` (`:323-326`) も `--no-replace-objects` を付けていない。

失敗シナリオ:

1. `:1687` で実際のHEAD OID `H` を捕捉する。
2. `refs/replace/H` が別 commit `H'` を指す状態にする。
3. `git cat-file H:output/...` が `H'` 側の protocol blob を返す。
4. working tree を `H'` の bytes に合わせる。
5. 比較は通るが、実際の commit `H` の blob ではない。

`git --no-replace-objects` を HEAD捕捉・tree検査・blob読込みの全Git操作に適用し、可能なら floor campaign と同じ環境衛生化も共有すべきである。

## 5. 正例と成果物 bytes

攻撃したが崩せなかった。

正当な reseal 直後は、新しい commit を `:1687` で捕捉し、その commit の `floor_protocol.json` blob と working tree bytes が一致するため通過する。detached HEAD でも、HEAD が通常の commit なら問題ない。

shallow clone も、現在の HEAD の tree/blob が存在すれば通過し、欠落していれば Git 読込み失敗で fail-closed になる。unborn HEAD は `rev-parse` 失敗となる。

比較案は `protocol_raw` を置換せず、単に HEAD blob と比較するだけである。candidate の bytes は従来どおり `document["floor_protocol"]["sha256"]` (`:1749-1751`) に同じ `protocol_raw` の hash を使うため、DW-O09 相当の成果物 bytes 変更はない。

## 総括

| 指摘 | 暫定判定 |
|---|---|
| `run_campaign` の成功経路で authority gate を回避できる | refuted |
| head捕捉→working tree読込みの順序 | refuted（再捕捉しないことが条件） |
| `_validate_floor_inputs` の既存caller/test契約破壊 | refuted |
| 新しいprotocol dirty-stateの回帰テスト不足 | real |
| HEAD が commit である保証不足 | real |
| HEAD tree entry の mode/symlink 検査不足 | real |
| Git replace object による blob authority 迂回 | real |
| shallow/detached/unborn HEAD の通常ケース | refuted |
| reseal 正例の破壊 | refuted |
| 凍結成果物 bytes の変更 | refuted |