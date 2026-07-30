# T-146 段 4 裁定と plan v2

## 裁定

- 段 2 plan v1 は NO-GO。段 3 の2本はいずれも形式 gate を通過し、real finding を反映した plan v2 へ差し替える。
- real / 採用: preexisting `.s` と ownership 観測不能を capability `False` に潰すと、
  long-path node が SKIP へ逃げる。これらは cleanup / ownership invariant 違反として送出する。
- real / 採用: fault test は helper の bool と nofollow の pathname 状態を recovery より前に直接観測する。
  test finalizer は assertion の外側で、patch 復元後または保存済み real syscall を使う。
- real / 採用: bind 部分成功の mandatory test を AF_UNIX 実 bind と偽らず、
  pathname materialization + bound-address state を持つ test double として固定する。
- real / 採用: `FileNotFoundError` は pathname 不在を再確認できた場合だけ冪等成功とする。
  `PermissionError` / `EIO` は cleanup invariant 違反として元の型と errno を送出する。
- real / 採用: unlink が成功を返しても pathname 不在を postcondition として再確認し、
  no-op unlink の偽緑を拒否する。
- real / 採用: mutation は exception branch の所有回収、FNF-only 分類、post-unlink absence の
  一意 anchor に分け、既存 T-138 gate が先に kill しないことを別走で確認する。
- real / 採用: targeted pytest は `-rf -rs` を使い、新規 fault node の SKIP を一件も許さない。
- refuted: production `tools/dev_waves/` または isolation meta-test の変更が必須。
  現 consumer と語彙の推移閉包は既に存在し、scope は integration test file 1枚で閉じる。
- refuted: `FileNotFoundError` の抑止が必ず偽緑。実 pathname の不在再確認を load-bearing にすれば
  既に消えている entry は cleanup postcondition を満たす。
- scope 外: hostile concurrent writer に対する stat/unlink の原子 ownership。
  現 caller は専用 TemporaryDirectory 内で serve thread 開始前に1回だけ呼ばれる single-writer である。
- scope 外: socket close / dirfd close の全複合例外族、production helper の同型 partial-bind fault。
  T-146 の独立再現は test helper の bind 後例外と unlink 異常だけで、族一般化の独立2例がない。
- brief の「全 FD close」は「通常経路と対象 fault 経路で close を試行し、既存 real-socket test を保つ」
  へ限定する。arbitrary close fault の完全保証は主張しない。

## plan v2

1. `orchestrator/tests/test_dev_waves_integration.py` の
   `_sandbox_permits_short_alias_bind()` だけを実装変更し、production / meta-test は no-touch にする。
2. dirfd を開いた後、literal `.s` を `follow_symlinks=False` で事前観測する。
   FNF のみ absent。entry 実在は `FileExistsError`、その他の観測 error はそのまま送出する。
3. capability の core subsequence `socket → bind → chmod → capability-stat → listen` と literal `.s`
   を維持する。ownership / cleanup の観測は追加列であり、core の代替にしない。
4. bind が投げた場合は socket の bound address を直接観測する。alias に bound 済みなら pathname を
   helper-owned として finally で回収し、未 bound なら capability `False` として回収しない。
   bound-address 観測不能は `False` に潰さず送出する。
5. helper-owned pathname は socket close 試行後に unlink する。FNF は nofollow の不在確認後だけ抑止し、
   それ以外の unlink error は送出する。unlink 成功後も nofollow の不在を確認する。
6. 新規 test は2関数へ縮退する。
   - fault policy parameter: partial-bind / FNF-after-real-unlink / EPERM / EIO / no-op-unlink。
   - preexisting entry parameter: regular file / broken symlink。両方とも例外送出と identity 保存を確認する。
7. 全新規 node に既存 `dev-waves-runtime` marker を1個だけ付ける。新規 node は skip 不可。
8. 既存正負 gate、long-path node、isolation exactness、2 test file 全体、repository 全走を親が実走する。
   product artifact 値・参照不変と test acceptance hardening を記録上も分離する。

## 変異事前登録

- pre-fix control: 新規 tests と変更前 helper の組合せで partial-bind、FNF-after-real-unlink、
  no-op-unlink の対象 parameter が FAILし、既存 T-138 正負 gate は PASSする。
- M-T146-A: bind exception branch の bound-address ownership 回収だけを無効化する。
  既存正負 gate PASS、新 partial-bind parameter FAIL、SKIP 0 を期待する。
- M-T146-B: cleanup の `except FileNotFoundError` を `except OSError` へ広げる。
  FNF parameter PASS、EPERM / EIO parameter FAIL、既存正負 gate PASS、SKIP 0 を期待する。
- M-T146-C: unlink 後の pathname absence postcondition だけを無効化する。
  no-op-unlink parameter FAIL、既存正負 gate PASS、SKIP 0 を期待する。
- 各 anchor は fix 後 source で exact 1箇所を要求する。rc、FAILED node、SKIPPED node / reason、
  mutated diff を記録し、復元は対象ファイル bytes の一致で確認する。
- 同一理由性が崩れた変異は kill に数えず、実効 gate へ再照準する。変異は対象 test subset に隔離し、
  repository 全走の代用にしない。

## 段 5 への裁定

GO。実装面は単一 workspace-write Codex author に限定し、コードとテストだけを編集させる。
manager は実装面を直接編集しない。
