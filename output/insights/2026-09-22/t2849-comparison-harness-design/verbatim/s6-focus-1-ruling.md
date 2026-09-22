# 段 6 焦点再レビュー 1 巡目 (`s6-focus-1.md`、09:49〜09:52:18、NO-GO、must 2 / should 1 / nit 1) への親の判定

親が根拠行を確認した (b5_generator_contrast.py:744-752 / :778-792 の LLM handshake 拒否と schema 不合格の `proposal-rejected`、:806-816 の機械故障で endpoint 選択前に終了する分岐、genome.py:124・:211・:217 の MOCC_SPACE と `space_for`、pin.py:31 の 7 桁 literal)。

| ID | 判定 | 採否 | 直し方 |
|---|---|---|---|
| F1 planner 出力の無い拒否を whiteboard に写せない | real | 採用 | R1 で入れた「iteration を提出機会の順にし投入前の拒否を rejected と写す」案を撤回する。whiteboard と継承照合は B-5 のまま (投入した評価だけ、iteration = b)。初期点と投入前の拒否 (提出機会の番号 a・拒否の分類だけ、値や自由文は入れない) を 1 つの閉じた兄弟 key で渡す。方向・大きさを架空に補わない |
| F2 機械欠測の優先 | real | 採用 | 初期点・探索の機械故障の retry 上限超え (または未解決) は endpoint の有無を問わず系列を終えて score 欠測 (B-5 §3.3、実装 :810-816)。品質欠測の規則 (endpoint 不在のときだけ score 欠測) と分ける。設計書 §4.6・§5.4、decisions fragment、worklog fragment を同期する |
| F3 MOCC_SPACE の「消費する driver は無い」 | real | 採用 | 直接参照は `genome.py` の定義と `SPACES` 登録だけ、`space_for("mocc")` を通す間接利用と driver の有無は未確認と書く |
| F4 CURRENT_PIN の表記 | real | 採用 | `CURRENT_PIN` は 7 桁 prefix `e9e477c`、gitlink と `CCBENCH_FULL_SHA` は完全 SHA と書く |

refuted 0 件。直した後に焦点再レビュー 2 巡目を投げる (DW-O16、上限 3 巡)。
