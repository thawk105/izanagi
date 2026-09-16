---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2616-prewarm-configure-node
seq: 3
---

## 新規

### {{F:predicate-and-its-test-share-the-same-wrong-option-name}}. 述語と、その述語を検査する test が同じ誤った option 名を共有して恒真になった [恒真ゲート] [テスト代表性]

- 事象: 早期 prewarm の発火条件で「narrowing が無いこと」を判定する列挙に、pytest の実 parser と
  食い違う destination 名を書いた。`--ff` の destination は `failedfirst` だが `ff` と書き、
  `--sw` / `--sw-skip` (`stepwise` / `stepwise_skip`) と `-o` (`override_ini`) は列挙自体が無かった。
  **同じ wave が追加した test も同じ誤名 (`("ff", True)`) を使ったため、test は実装の誤りと
  自己整合して緑のまま通った。** 段 6 の敵対レビューが pytest 本体の `addoption` と突き合わせて
  初めて露見した。
- 根本原因: 述語が参照する名前空間 (pytest の parsed option destination) の権威が外部にあるのに、
  実装と test の両方が同じ手書きの列挙を根拠にした。**述語を、その述語が生成した候補集合で
  検査している**ため、列挙の誤りは構造的に検出できない。
- 影響: `--ff` や `-o python_files=...` を付けた焦点走で早期 prewarm が発火し、D518 が却下した
  「無条件 prewarm」が焦点走へ漏れる。consumer を含まない走行に解決 1 回分 (実測 28.3 秒) が
  丸乗りし、テスト時間規則を破る。
- 恒久対応: 実 `Parser` へ plugin の `addoption` を登録して destination を照合する対照 test を置き、
  **さらに独立した CLI 入力でも検査する**。前者は綴り誤りを、後者は列挙漏れを落とす。
  詳細は {{D:early-prewarm-fire-condition-parsed-option}}。
- 再発検知: 外部ライブラリの識別子 (option destination、hook 名、marker 名等) を手で列挙する
  述語を新設する wave が必ず踏む。**列挙の正しさを、その列挙から作った入力だけで検査していないか**を
  段 6 のレンズに入れる。

## 再発

### F945

- **再発: 2026-09-16** — receipt memo prewarm を collection 前へ移す wave の受入 attempt 2 で、
  `test_t1259_qsub_env_delivery_probe.py` の **28 件**が setup error になった
  (shard-0: 8851 tests / errors=28 / failures=0)。setup traceback の Git argv は既報と同一で、
  `git -C <wave worktree> ls-files --others --exclude-standard -z` と `git status` の
  30 秒 TimeoutExpired。**直近の再発 (2026-09-14) と件数まで同じ 28 件**である。
  同 tip・同 file の単独再走は **51 passed / 15.92 秒 / rc=0** で非再現 (投入時 load 6.75)。
  恒久対応は既報のまま変えず、timeout 拡大・stub 化・除外・gate 新設は行わなかった。
  **本 wave の走行は同時に 3 本の受入が走り、さらに終了しない job が資源を握っていた。**
  同じ shard の junit time は 602.867 秒で通常の倍であり、**赤の帰属判定だけでなく
  wall の測定としても無効**と判定して受入ごと投げ直した。

### F982

- **再発: 2026-09-16** — receipt memo prewarm の wave で、
  `test_real_repo_writers_do_not_materialize_oracle_environment_candidates` が
  同 file 単独走で決定的に赤になった (WAL lock の JSON 不一致、
  `test_p3_s4_loop.py:7079` の `wal.read_lock(lay) == build_v2_lock(ident.canonical_preimage(cfg))`)。
  既報どおり **`test_p3_s4_loop.py` を選択へ足すと緑になり** (503 passed / 1 skipped → fix 後 505)、
  選択形固有の偽赤と確定した。**変更面は conftest の prewarm 起動点と memo の cache 読み書きで、
  当該 wrapper・site 中立化 fixture・WAL・ident は触っていない。**
  本 wave は commit 前後の両方で再現することも確かめ、未 commit 由来の drift ではないと切り分けた。
