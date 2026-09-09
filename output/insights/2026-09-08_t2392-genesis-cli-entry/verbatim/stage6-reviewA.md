## must-fix

1. **must-fix — `orchestrator/campaign/trial_registry.py:6545`**  
   `load_trial_manifest` は digest 導出だけでなく、schema・exact keys・6 trial universe まで検証する。確定 plan が許可したのは manifest bytes の読取りと SHA-256 導出であり、これは D1769 が禁じる裁定外 validator になっている。  
   **成果物影響:** 既存 creator の path＋digest 契約では作成可能な入力が拒否され、正本 attempt-registry 台帳が作られないため、`genesis` の受理集合が裁定より狭くなる。

2. **must-fix — `orchestrator/campaign/trial_registry.py:2448`**  
   新分岐が到達する `_write_create_only` は正本 file を `O_EXCL` で先に作り、その後直接書き込む。`os.write` または `fsync` が途中で失敗しても、`2449–2467` に作成済み file の回収処理がなく、部分的な正本が残る。  
   **成果物影響:** 壊れた `attempt-registry.jsonl` が正本 path を占有して再試行を create-only で拒否し、formal receipt を以後生成不能にする。

## nit

なし。

## 壊せなかった点

- digest 自体は `load_trial_manifest` が読んだ raw bytes を `hashlib.sha256` へ渡しており、引数由来ではない (`trial_registry.py:806–823`, `6562`)。
- `genesis` の引数は指定された5個だけで、`--manifest-sha256`、`--registry`、retry 理由指定は追加されていない (`6522–6529`)。
- 正本 path は creator と receipt verifier の双方で固定されている (`trial_registry.py:2425–2430`, `s8c_acceptance_receipt.py:1864–1865`)。
- 世代一致は外側と core の双方、retry 理由は core の閉集合比較で維持される (`trial_registry.py:2497–2512`, `attempt_registry_core.py:689–701`, `733–750`)。
- `register` / `accept` の parser、出力構築、分岐本体に `genesis` 由来の意味変更は見つからなかった。
- 通常の入力拒否は `TrialRegistryError` から `parser.error`、argparse 不備は `SystemExit(2)` に揃っている (`trial_registry.py:6530–6531`, `6609–6610`)。

## 総括

must-fix は2件。受理防壁の緩和や偽 digest は確認できなかったが、裁定外の manifest validator と、失敗時に正本を不可逆に汚染する create-only 書込み経路が残っている。静的レビューのみで、実走は行っていない。