---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2392-genesis-cli-entry
seq: 1
title: [T-2392] 正式系列の起点入口を CLI へ足した — D1775 の停止条件は 4 項目中 2 項目が偽で発火せず、純増は provenance でなく入力構築の保証だった (コード + テスト + insight、branch worktree-dev-wave-t2392-genesis-cli-entry、変異 4 件すべて KILLED、初回 m02 は親の期待集合誤りで MISMATCH → probe として保存)
---

## 本文

- **D1775 の条件付き裁定を実行した。** 例外条項「既存経路で起点の commit・argv・入力・lifecycle が
  記録されるなら足さない」を read-only で実測した結果、**4 項目の連言は成立しない**ため例外は
  発火せず、主文どおり `genesis` subcommand を足した。判定は
  commit=偽 (厳密に読む場合) / argv=偽 / 入力=真 / lifecycle=真。
- **親の段 1 の読みは段 2・段 3 に否定された。** 親は当初「既存 2 入口も argv を記録しないから
  argv は数えない」と読んで「足さない」に傾いたが、これは裁定文に無い有効性条件を足していた。
  「既存 2 入口と同じ層」は追加先を指定する句であって記録項目の比較基準ではなく、
  D1775 は「記録されていない場合に足さない」を明示的に却下している。親はこの読みを取り下げた。
- **段 3 sol が P1 を壊した (親が現物で確認)。** 受入が束縛するのは「起点を導入した commit」ではなく
  「起点 1 行の blob を含む任意の commit」である。全史走査は blob が前 commit と同一のとき
  strict-prefix 検査を掛けないため、起点導入 commit G の後に registry を変えない無関係な commit K を
  作り、K を内容 commit `P` として使う履歴が正式な発行経路をそのまま通る。receipt に残るのは K である。
- **本 wave の純増は provenance ではなく入力構築の保証である。** 既存の生成関数は
  `manifest_sha256` を独立引数で受け形式検査しかせず、manifest 本体と照合しない。起点は create-only の
  不可逆な成果物なので、食い違う hash は受入まで残る。CLI は manifest bytes から digest を導出するため、
  これを作成時点で拒否できる。**追加した入口も schema を変えない限り actor・時刻・実行 code 版・
  argv・真の導入 commit は記録しない**ことを段 3 sol が明記し、裁定文へそのまま残した。
- **不在は repo 全体で実測した。** `git ls-files` を道具に、他セッションの worktree と submodule を
  構造的に除いて数え、8c facade の非テスト caller が 0 件であることを確定した。段 2・段 3 は
  いずれも「射影外は判定不能」と留保していたので、親がこれを閉じた。
- **段 6 レビュー 5 件の裁定:** refuted 1 (`load_trial_manifest` は既存 `register` 入口も使う同一 helper で
  あり裁定外の validator ではない)、scope 内 real 3 (本 wave が足したテスト自身の自己 oracle と
  過剰決定。fix 済み)、scope 外 real 1。段 3 sol の 5 件と合わせ scope 外 real は計 6 件で、
  新規 T として裁定へ返す。
- **変異の erratum:** 初回走行で m02 が MISMATCH。原因は**親の期待集合の誤り**で実装の欠陥ではない。
  fix で世代不一致テストの全 slot を一様に `3` へ揃えたため、変異が定数 `1` を渡しても先頭 slot で
  同じ食い違いメッセージが出て当該テストは緑のまま通る。初回を probe として保存し、
  期待 node を 2 件へ訂正して再走した。
- **新規 test file を作らなかった。** 既存 `test_trial_registry.py` が自走 harness と CLI テストを
  既に持つため、そこへ足すことで harness 登録も受入所要台帳の新規行も不要になり、
  main 取り込み時の台帳競合も避けた。
- 起点を作る**運用手順**は事前登録文書にも runbook にも無い (段 3 luna)。規範的要件はあるが手順ではない。
  本 wave で入口ができたので、手順を書く先は用意された。手順そのものは本 wave の scope 外。
- **受入は 3 attempt を要した。いずれも実装の赤ではない。** attempt 1 は `stage=postcheck rc=70`
  で、post-claim merge は成立したのに走行中に main が 6 commit 進んで branch が遅れ fail-closed
  (テスト子は未起動)。attempt 2 は完走して 21976 passed だが 3 赤。3 件とも `trial_registry` を
  1 箇所も参照しない file で、実行ノードの loadavg が 65 に達しており、内訳は launcher の timeout 1 件と
  `git ls-files --others --exclude-standard -z` が 30 秒 timeout する setup 失敗 2 件だった。
  同一 tip で 3 件を単独再走すると 9 秒で全部緑 (非再現) だったため環境由来と確定し、受入を再走した。

## 次の一手差分

### 完了

- [T-2392] 正式系列の起点入口を CLI へ足すかを決め、D1775 の停止条件が発火しないことを実測して
  `genesis` subcommand を足した。
  remaining: none
  base: 6b71313b7226fb5776b4007746de9e1550812b39b005ed41872b97d372ddbfa3

### 新規

- {{T:genesis-introduction-commit-binding}} **P2・新規 (段 3 sol、親が現物で確認)**:
  受入は「起点を導入した commit」を束縛していない。全史走査は blob 不変の commit で strict-prefix
  検査を掛けず、`_blob_at_commit` は P が導入 commit かを見ない。G → registry 不変の K → K を P に
  使う履歴が正式経路を通り、receipt には K が残る。束縛するかは受入契約の変更を伴う設計択一。
- {{T:create-only-partial-write-recovery}} **P2・新規 (段 6 レビュー sol)**:
  `_write_create_only` は `O_EXCL` で作成後、途中の `os.write` / `fsync` 失敗でも作りかけ file を
  消さない。壊れた正本が create-only path を占有し再試行を恒久的に塞ぐ。共有 writer で
  分類受領証経路も使うため、直すと既存 caller の挙動が変わる。
- {{T:standalone-verifier-effective-commit-checks}} **P3・新規 (段 3 sol)**:
  standalone の receipt verifier は `prereg_effective_commit` が実在するか・P の直子か・
  measurement HEAD の祖先かを検査しない。正式 issuer だけが検査しており、信頼面が二重になっている。
- {{T:standalone-verifier-lifecycle-rederivation}} **P3・新規 (段 3 sol)**:
  standalone verifier は lifecycle の意味を再導出しない。`_assert_git_history_append_only` は
  lifecycle JSON を parse せず、長さと hash を合わせた任意の非空 file を拒否できない。
- {{T:genesis-manifest-path-binding}} **P3・新規 (段 3 sol)**:
  standalone verifier は起点の `manifest_path` を受領証の `manifest_path` と比較しない
  (正式 issuer は比較する)。同じ bytes を別 path に置いても path 差では赤にならない。
- {{T:genesis-schema-actor-fields}} **P3・新規 (段 3 sol)**:
  起点 schema に作成時刻・実行者・実行 code 版の field が無く、exact-key 検査により追加もできない。
  追加した `genesis` subcommand もこれらを記録しない。記録するかは schema 変更を伴う設計択一。
- {{T:genesis-operational-procedure}} **P3・新規 (段 3 luna)**:
  起点を作る運用手順が事前登録文書にも runbook にも無い。コードが要求する順序は
  「manifest と slots を用意 → 起点を生成 → 起点を含めて P を commit → binding のみの C」だが、
  起点生成の工程が未文書化である。
