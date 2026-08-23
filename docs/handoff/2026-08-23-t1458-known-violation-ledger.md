# [T-1458] known-violation台帳への2件登録
- 目的: `94815c57` と `3a5e5feb` の missing-codex-author を provenance 台帳へ登録し、逐語ミラーを同期する
- 状態: 中断
- 最終更新: 2026-08-23
- 基準コミット: 3a5e5feb5f5c65e5e91752f847c623ce37e9b14d (作業ツリー clean で開始)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)
- 対象SHAを確定: `94815c57976806da56a3f067ade91c0041b2e2d1`、`3a5e5feb5f5c65e5e91752f847c623ce37e9b14d`。
- 既存の末尾台帳エントリ `25614f868c1a1b562a68072233fdf55b0be93cd1` と、テストの逐語比較箇所を確認済み。
- 台帳件数は `51`、直接呼出しの逐語アサーションは passed、`check_docs.py` と `check_codex_agents.py` は成功。
- 公式の全史 provenance 走と焦点走は、Pegasus `qstat -Q` の `API EACCTAUTH: Unknown user-id` により子未起動。

## 未完の作業と次の一手 (具体的に)
1. 追加済みの2件について、Pegasus認証復旧後に指定の provenance 全史監査と焦点テストを再実行する。
2. commitは作成せず、親セッションが対象2ファイルの差分を引き取る。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)
- テストは `expected_finding_value` の空文字列を含む5要素タプルで、ruling/note の文字列は台帳と一字一句一致させる必要がある。
