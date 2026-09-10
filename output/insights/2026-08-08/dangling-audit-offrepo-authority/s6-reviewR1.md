# 所見リスト

1. **real / blocker — landed 参照が substring 判定のため、別候補の hit を流用できる**

   [`_landed_reference_matches()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:454) は全 pattern を `git grep -F` へ渡した後、hit した全ファイルの内容をまとめ、各 pattern を単純な `encoded in content` で再判定しています（[同 483–490 行相当](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:483)）。

   例えば候補 A が `/jobs/wave/a.py`、候補 B が `/jobs/wave/a.py.backup` で、main が B だけを参照していても、A の pattern は B の文字列の prefix なので両方が `referenced` になります。祖先 pattern でも `/jobs/t574` と `/jobs/t574-old` のように同じ誤判定が生じます。これは条件 5 を満たさない A を抑止する、候補間の根拠流用です。

   **成果物影響:** A の `(commit,path)` がレポートの受理集合から消え、最後の finding なら rc が 1→0 になり、未 land の insight・fragment が certified cleanup 後に台帳から永久欠落し得ます。

   修正には、pattern ごとの完全な path 参照境界を検証し、少なくとも「一方の path が他方の prefix」という kill test で短い方が残ることを固定する必要があります。

2. **real / blocker — 読み取り中に同一 inode が更新されても bytes 一致として返せる**

   open 直後には inode・size・mode を検査していますが（[313–321 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:313)）、hash と逐次比較の後は metadata を再確認せず、そのまま `True` を返します（[323–348 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:323)）。

   外部ファイルが最初は一致しており、逐次比較の読み取り位置の後ろから writer が同一サイズの別内容へ上書きすると、reader は旧 bytes を最後まで読んで一致を返せますが、返却時点のファイルは既に不一致です。2 回読むことだけではこの writer-behind-reader race を閉じません。

   **成果物影響:** 不一致になった外部実体を根拠に finding が抑止され、rc・レポート受理集合・救出台帳が blocker 1 と同じ方向へ誤って縮みます。

   比較前後の `fstat` で size・mode・mtime/ctime 等の安定性を確認し、変化時は確認不能として抑止しない必要があります。

## Scope 外の real 所見（本 wave では実装禁止）

- **real / nit（scope 外）— [T-593] 1(c):** [`audit()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:521) は main に同名 path があれば内容違いの revision も除外する。  
  **成果物影響:** 同名別内容の失われた revision はレポート・救出台帳へ入らない。

- **real / nit（scope 外）— [T-593] 4:** 既存 3 条件は解決済み commit、landed 参照は後から可変の `main_ref` で確認するため（[504–508 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:504)、[576–578 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dangling-audit-offrepo-authority/tools/audit_dangling_commits.py:576)）、ref 移動時に異なる tree の証拠が混ざる。  
  **成果物影響:** race 時だけ抑止受理集合が増減する。

- **real / nit（scope 外）— [T-593] 6(a):** 合成 commit fixture の隔離は本変更では扱わない。  
  **成果物影響:** 受入結果の provenance 帰属が合成 commit と混ざり得る。

- **real / nit（scope 外）— hardlink/root symlink 交換:** 裁定済み残存 risk。  
  **成果物影響:** 意図的な inode/path 交換では repo 内実体を repo 外根拠として扱い、finding が消え得る。

- **real / nit（scope 外）— ack 台帳・即時 prune・10 倍規模実測:** いずれも裁定により不採用または先送り済みで、今回の修正要求にはしない。  
  **成果物影響:** 既知残骸は自然 GC までレポートに残り、10 倍規模での時間・メモリ受入証拠は未確立のままになる。

`audit()` の signature・戻り値・既存 3 条件は HEAD と一致しています。root 拒否、literal pathspec/NUL 解析、mode 対応、FIFO/device 除外、read-only、出力と rc には別の in-scope 所見はありません。pytest は実行しておらず、親提示の 37 passed を前提事実として扱いました。

## 総括

- **blocker: あり、2 件**
- 最も危険なのは **substring による別候補の landed hit 流用**。並行更新や filesystem race を必要とせず、通常の path 命名だけで条件 5 を破る。
- **NO-GO** — blocker 2 件を塞ぐまで land 不可。