## 総括

[main_checker_history.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/main_checker_history.py) を作成し、指定 CLI で自己実走しました。

```bash
python3 build/probe/main_checker_history.py \
  --repo /work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe \
  --since 2026-09-15T00:00:00+09:00 \
  --commits 33c608726 55068f84e 4c532aa0b aa81e3c64 62ed683ab 00d781372 65966f4d8 6305f2d05 5733c0f08 \
  --out build/probe/out/main-checker-history-self.jsonl \
  > build/probe/out/main-checker-history-self.stdout.txt
```

指定期間の残存 entry は575件、checker 遷移は **5回**。`6305f2d05` の checker は **`65476dafe9c0`** でした。包含判定と版の一致判定は別列にしています。JSONL には残存する全3,279 entry の完全な SHA-256 も保存しました。

reflog は共有 git-dir の `/work/1/SFC/tanab/izanagi/.git/logs/refs/heads/main` です。worktree 固有の ref ではありません。

取得範囲は **2026-08-02 21:04:01 ～ 2026-09-21 08:26:37 JST**。連続性の断絶を10件検出し、下記に各範囲を記録しました。すべて指定期間より前ですが、expire・削除の理由や失われた内容は確定できません。未観測の版を「main が一度も指さなかった」とは断定しません。自己実走の終了コードは、この断絶を知らせる **1** です。出力は完了しており、実走中の reflog・main tip の変化、checker 読取失敗はありません。

tracked file 31,698件の実走前後の内容ハッシュと index を比較し、**変更0件・index不変**を確認しました。commit・既存テスト実行はしていません。実装上の未完了はありません。

自己実走 stdout 全文：

```text
COVERAGE	2026-08-02T21:04:01+09:00	2026-09-21T08:26:37+09:00
MAIN_REFLOG	/work/1/SFC/tanab/izanagi/.git/logs/refs/heads/main	shared=true
SNAPSHOT	stable=true	chain_gaps=10	monotonic=true
LIMIT	Retained reflog only; expiry/deletions before or within this range cannot be fully ruled out. No match is not never-on-main.
CHAIN_GAP	2026-08-02T21:52:29+09:00	2026-08-03T10:24:22+09:00	163ac0d804c17ed4a705800a712cabbf4868e172	e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e
CHAIN_GAP	2026-08-03T10:24:22+09:00	2026-08-03T13:48:14+09:00	163ac0d804c17ed4a705800a712cabbf4868e172	e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e
CHAIN_GAP	2026-08-03T13:48:14+09:00	2026-08-03T14:01:35+09:00	0fbe3361e1d6fe51added31667c47cb486c0a33a	e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e
CHAIN_GAP	2026-08-03T14:01:35+09:00	2026-08-03T14:05:16+09:00	a976d81e7ae773031d79ab2605bd0e26e3aa0807	e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e
CHAIN_GAP	2026-08-03T14:29:31+09:00	2026-08-03T16:50:04+09:00	9fbed42cae46741b3dedae2c25c5648892d0da5c	ea6ca433eb83d666ec64f3629cc35c769a2b5c19
CHAIN_GAP	2026-08-03T16:50:04+09:00	2026-08-03T16:50:38+09:00	7ccbfb96c8869357f35aa1e41f58cceaa8b2072f	ea6ca433eb83d666ec64f3629cc35c769a2b5c19
CHAIN_GAP	2026-08-03T16:57:57+09:00	2026-08-03T17:20:24+09:00	57848c4f7c3a82ebbddf5ad88edadc6e20ba8776	e805d69e7cba643664f67cc667dff26ccd6c852c
CHAIN_GAP	2026-08-03T21:00:55+09:00	2026-08-03T21:34:58+09:00	3b551c09a60f4276651ebb9c7e574b96732c7209	1a3604b126c853fc98426f0dbf67b7dde96fa3da
CHAIN_GAP	2026-08-03T21:46:30+09:00	2026-08-03T21:54:21+09:00	e222450e65e8b90dc83e0622c114b6dba8406216	fbad0260cc9c232f1b4e47ee1893cea40d527367
CHAIN_GAP	2026-08-03T21:54:21+09:00	2026-08-03T22:21:49+09:00	4aa6f9e9782bbb8e1e3576445267ad928fee8a14	fbad0260cc9c232f1b4e47ee1893cea40d527367
kind	reflog_time_JST	new_commit	old_sha256	new_sha256	subject
baseline	2026-09-14T18:05:14+09:00	6be7935b75e318019ce6262923370891b4873758	-	865df41c5c77	commit: Fold landed documentation fragments
transition	2026-09-15T19:56:18+09:00	c724ca8ade8302d006b388ff7543c42f01838e40	865df41c5c77	b2d209ef2989	merge c724ca8ade8302d006b388ff7543c42f01838e40: Fast-forward
transition	2026-09-16T11:08:46+09:00	c7a8b32c0f24c9754bb7bb8fad6f1629baf22866	b2d209ef2989	5cb709cbca5d	merge c7a8b32c0f24c9754bb7bb8fad6f1629baf22866: Fast-forward
transition	2026-09-20T10:30:23+09:00	79bfa157c7c44ab2f141a36b3b2bbcc33bfd6c0f	5cb709cbca5d	7c02fb2d5fec	merge 79bfa157c7c44ab2f141a36b3b2bbcc33bfd6c0f: Fast-forward
transition	2026-09-20T23:29:54+09:00	1e5fb5705d18711b347fac9a7581e35a4833a8d1	7c02fb2d5fec	65476dafe9c0	merge 1e5fb5705d18711b347fac9a7581e35a4833a8d1: Fast-forward
transition	2026-09-21T00:10:46+09:00	65966f4d8a9277a4e1496c65dd276718f26d718b	65476dafe9c0	e69764c1d885	merge 65966f4d8a9277a4e1496c65dd276718f26d718b: Fast-forward
commit	checker_sha256	d2192_lines	outer_deadline_lines	ancestor_of_main	version_seen_on_retained_main	matching_entries	first_match_JST
33c608726	5cb709cbca5d	0	0	True	True	395	2026-09-16T11:08:46+09:00
55068f84e	7c02fb2d5fec	0	0	True	True	96	2026-09-20T10:30:23+09:00
4c532aa0b	1acbb4961ca6	0	0	True	False	0	-
aa81e3c64	89a60a884088	0	3	True	False	0	-
62ed683ab	65476dafe9c0	0	3	True	True	2	2026-09-20T23:29:54+09:00
00d781372	2b72e1d543cd	2	0	True	False	0	-
65966f4d8	e69764c1d885	2	3	True	True	24	2026-09-21T00:10:46+09:00
6305f2d05	65476dafe9c0	0	3	True	True	2	2026-09-20T23:29:54+09:00
5733c0f08	e69764c1d885	2	3	True	True	24	2026-09-21T00:10:46+09:00
SUMMARY	retained_entries=3279	window_entries=575	baseline_entries=1	checker_transitions=5	unknown_transitions=0	queried_commits=9	matched_versions=6	unreadable_checker_entries=0
```