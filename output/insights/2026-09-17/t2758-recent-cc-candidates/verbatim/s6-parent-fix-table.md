# 親の是正対応表 (段 6 レビュー所見 → 候補表 v2 / README v2)

| 所見 | 親の裁定 | 適用 | 親の自己判定 |
|---|---|---|---|
| 1 RR / Bamboo「単版」前提の誤り | real / must-fix | trace cell を「未 commit の複数版を読む、未確認」へ、`rr.txt` §5 と Bamboo §3.5 の逐語を cell に置いた。§6 項 1 を是正案 2 の内容へ。判定 c=? | closed |
| 2 Polaris `validate` の説明 | real / must-fix | 証明面 cell を是正案 3 の内容へ (write set 外 locked 拒否 + data_ver 一致、LOCK_ERR_PRIO は lock / try_lock)。trace cell は「低と見積る (推論)」+ `get_data_ver()` uint32_t と commit ID 未照合を明記。「費用最小」は「候補比較で費用が最も低いと見積る (推論)」へ | closed |
| 3 P3 の未確認の扱い | real / must-fix | P3 を是正案 1 の三値記録へ。判定を「優先調査候補 / 保留 / 棄却 / 母集合外」に分け、各 cell に a〜d の値を書いた。追加対象 (確定) は 0 件と明記。P1 母集合外の条件 (学習型・分散・engine 内・certifier・単一 protocol でない) を P3 の前段として分離 | closed |
| 4 dirty read と verifier の観測能力 | real / must-fix | §6 項 3 を是正案 2 後半の内容へ (G1a / G1b 観測不能を明記、Bamboo §3.1 の逐語)。Shirakami 証明面 cell の「G2 検出で扱える」を「対応は未照合」へ | closed |
| 5 Bamboo 対照の根拠 | real / must-fix | RR 実装可用性 cell と §4 項 2 を是正案 4 の内容へ (切替経路・対照の同一移植は未確認、費用共有・劣後は断定しない) | closed |
| 6 RW1 | real / must-fix | 「公開実装なし」→「未確認」+ 走査語を cell に記載 (Plor / CormCC / Tebaldi は検索 query を逐語で)、「唯一」は本表内の順位と明記、§1 項 3 の結論を是正案 5 の文へ、NeurCC license は root 一覧の実測 (LICENSE 系 file 不在) と API 分類を書き分け、ATCC / ESSN は「抽出要約に記述なし」+ 「原文の全件走査ではない」。README 追記は是正案 7 へ | closed |
| 7 §6 の設計指定 | real / must-fix | §6 を「確認課題」に改題し、field / event / reason / 採番 / 移植先 / workload API は決めないと冒頭に明記。項 2 / 5 / 6 を性質と確認課題の記述へ | closed |
| 8 P1 の系譜と除外記録 | real / must-fix | §1 項 2 を是正案 8 の文へ。項 3 に検索で拾った題名の扱い (決定論 / protocol でない / 環境対象外) を列挙、項 5 に一次資料の関連研究節の名前を列挙 | closed |
| 9 Plor の hit 数・節番号・限定 | real / nit | 是正案の逐語 (3 行、URL 1 行は concurrentqueue)、§5 実装 / §6.2.2 評価、「競合する trx 間で」を追加 | closed |
| 10 README の語彙・認可 | refuted | 是正案 7 は内容上の強さの是正として採用 (README 段落を置換) | — |

親が新たに足した事実 (レビュー後の追加照合、2026-09-17): neurdb/neurcc の root 一覧 (GitHub API contents) に LICENSE 系 file なし、gitzhqian/RebirthRetire の LICENSE raw = ISC (Bamboo-Public と同文)、luyi0619/aria の LICENSE raw = MIT。web-evidence.md には未追記 (この表が一次記録)。
