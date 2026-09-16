---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2697-b4-binary-placement
seq: 3
---

## 新規

### {{F:transport-copy-repairs-missing-required-key}}. 移送用コピーへ必須 key を補うと、exact key 集合の検査が迂回されて欠損 record を受理した [恒真ゲート]

- 事象: B-4 binary の配置経路 `b4_binary_record.place_record` は、portable record のコピーの
  `binary` と `store_path` を絶対 path へ書き換えてから `store_binaries` へ渡す。実装は
  `placed["binary"] = str(source)` を元 record に `binary` key があるか確かめずに実行していた。
  `s8b_binary_admission.py:343-346` は portable record の exact key 集合を要求するので、
  `binary` を欠く record は本来拒否される。ところが下流の検査は**補修後のコピー**を見るため、
  欠損 record から配置物と成功 relpath が生まれた。段 6 の敵対レビュー (正しさ・受理集合レンズ) が
  実走前に見つけた。
- 根本原因: 形の検査 (exact key 集合) と、その検査へ渡す前の変形 (path の書き換え) が別の関数にある。
  変形側は「既存 key の値を差し替える」つもりで書いたが、dict への代入は key の追加も兼ねるので、
  **差し替えと補修の区別が消えた。** 他の必須 field は変形の前に読まれて欠落すれば `KeyError` に
  なっていたので、読まれずに代入だけされる `binary` の 1 つだけが穴になった。
- 恒久対応: 置換の前に元 record の `binary` を参照して欠落を `KeyError` にする
  (`orchestrator/campaign/b4_binary_record.py` の `place_record`)。負例テスト
  `orchestrator/tests/test_b4_binary_record.py::test_place_rejects_missing_binary_key` が
  store 未到達と配置物なしまで確かめ、変異 M8 (guard 行の削除) がそのテストだけを単一理由で殺すことを
  変異 matrix で確認した (`output/insights/2026-09-16/t2697-b4-binary-placement/mutation-final-result.json`)。
- 再発検知: 検査へ渡す前にコピーを変形する経路では、**変形で触る key ごとに「元に無い場合」の負例**を
  置く。敵対レビューのレンズに「変形が検査対象の形を補修していないか」を入れる。

### {{F:placed-artifact-breaks-ignore-removal-mutation}}. 実データ走で置いた ignored な配置物が、ignore 行を消す変異の下で untracked として現れ、変異走行全体を中止させた [手順漏れ] [計測汚染]

- 事象: 親が B-4 binary の実データ 1 走で 701KB の binary を `output/env/pegasus/binaries/<sha>` へ置いた。
  `.gitignore` の `output/env/*/binaries/` に当たるので `git status --porcelain --untracked-files=all` は
  空だった。その後の変異 probe 走は M1〜M6 を完了したが、M7 (その ignore 行を消す変異) を適用した時点で
  配置物が untracked として現れ、`mutation harness aborted: runner/test 実行前に untracked file を検出` で
  全体が中止した。配置物を退けて M7・M8 だけを再走し、本走を別に投入した。
- 根本原因: 変異 harness の走行前 clean-tree 検査は**変異適用後の木**を見る。ignore 規則そのものを
  変異させると、平時は不可視の ignored file が検査対象に入る。F134 の再発検知
  (投入前に porcelain が空であることを確かめる) は変異適用前の木を見るので、この経路をすり抜ける。
- 恒久対応: memory `mutation-discipline` に「ignore 規則を変異させる spec を走らせる前に、その規則に
  当たる実 file を worktree から退ける」を追記した。
- 再発検知: 変異 spec の replacement に `.gitignore` が含まれるとき、その規則に当たる実在 file を
  `git ls-files --others --ignored --exclude-standard` で数え、0 件でなければ投入前に退ける。

### {{F:existing-placement-rule-not-searched-in-stage1}}. 段 1 が「同種の物の既存の置き場」を production コードで引かず、plan が既存規約と二重化する新 namespace を提案した [手順漏れ]

- 事象: B-4 binary の配置規則を決める wave で、段 2 plan は新しい namespace `output/b4-binaries/<sha256>` を
  提案し「campaign 軸でも env 軸でもない実験補助 store」と位置づけた。ところが
  `s8b_floor_campaign.py:7669` は既に同じ種類の物を `env_scope_dir(env_tag)/binaries/<sha>` へ置いていた。
  親はこれを段 2 投入の**後**に見つけ、plan 子の prompt には間に合わなかった。段 3 レンズ B へ射影して
  突き合わせさせ、段 4 で既存規約側を採って回収した。採っていれば、依頼が禁じた一般化 (新分類の新設) と
  同種の物の置き場の二重化が起きていた。
- 根本原因: 段 1 の閉包は「依頼の対象 path を pin する台帳・test」(`DW-O09`) と「依頼の性質で
  decisions / failures / archive を検索する」(`DW-S01`) を課すが、**「依頼が作ろうとしている物と同じ種類の物を、
  既存 production コードがどこへ置いているか」を引く義務は無い。** 親は消費側 (`floor_pair_driver`) から
  辿ったので、producer 側の既存の置き場に後から当たった。
- 恒久対応: memory `stage1-search-existing-home-for-same-kind` に「配置・命名・置き場を決める依頼では、
  同種の物を既に置いている production の呼出し (`store_root` / `*_dir(` / `Path(...) /` の組み立て) を
  段 1 で引き、brief の実アンカー表へ入れる」を書いた。段 3 の敵対レンズへ親の後発実測を射影する既存手順
  (`DW-S03`) が本件を回収したことも併記する。
- 再発検知: 段 2 plan が新しい directory・namespace・分類を提案したら、親は段 4 の前に
  その置き場の同種の既存例を production で grep する。
