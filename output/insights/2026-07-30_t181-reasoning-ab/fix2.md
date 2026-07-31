## 総括

RF-1〜RF-8の実装対応を、指定された2ファイルだけに反映しました。

- [codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py)
  - `create-launch-receipt` を廃止し、pair単位の `supervise-pair` に統合
  - supervisor自身がsnapshot前後検査、bwrap/Codex argv・環境生成、起動・wait、OS時刻、CLI/bwrap/config/auth SHAを記録
  - UUID run directory、唯一のrun root、append-only attempt ledger、pair世代retry、実時刻の非重複・順序・隣接・gap gate
  - root/submoduleのobjects、全refs、reflog、grafts、alternates、replace、`info/*`を再帰manifest化
  - ignored・余剰・欠落fileをfilesystem完全一致で拒否し、Codex環境から`GIT_*`を除去
  - packet外の乱数名mapping secret、metadata正規化、parent/second-readerの追記式verdict、保守側miss、一致率、`mask_strength: same-owner-advisory`
  - incompleteまたはverifier reason時の品質ledger null化、型付きNEG除外arm・採否可能性・decision row
  - 非空turn ID、event順序・timestamp、実process wall-clock、否定・未裁定・500-byte境界を強化

- [test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py)
  - 40 test nodeを定義
  - M1〜M12について新旧HEADの期待node名をmodule docstringへ明記
  - POS/NEG両向きのmode・ignored extra・missing・focus、prompt件数、実rollout slice、Git再注入、pair timing、片側retry、attempt=4、root外退避、post-treatment分母などを独立fixture化
  - fake Codexによる10 runのsupervisor→collector→packet→二読者→aggregate replay経路を追加

検査は `python3 -m py_compile` のみ成功しています。**pytest 未実行（ユーザー指示によりログインノードで走らせない）**であり、`tools/run_tests.py`、mutation、live Codex、bwrap実走、受入全走も実行していません。したがって緑は主張しません。

未達として残るのは親担当の計算ノードでのpytest、M1〜M12新旧matrix、焦点再レビュー、live 10 run、docs・記録・commitです。scope外のheld-out正例、非劣性設計、backend identity、runtime silent-miss検出も未実装です。

波及可能性として、repo内に所有外callerは静的には見つかりませんでしたが、親launcherは旧コマンドから`supervise-pair`へ移行し、`run_root`、attempt ledger、前後snapshot、二読者verdict log、revealed map、combined judgmentを持つ新manifestへ追随する必要があります。共有fixtureの変更はなく、consumer面は当該テスト、将来のtracked manifest、親launcher、既定の`orchestrator/tests`収集です。docs編集とcommitは行っていません。