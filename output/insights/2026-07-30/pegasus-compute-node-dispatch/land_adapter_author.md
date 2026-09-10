## 総括

1. `dev_wave_land.py` を module importし、`land(LandRequest)` を使用しました。lock、repository identity、history/config、audit closure、ff-only、既存 collision、control-plane、postcondition は既存経路のままです。
2. 唯一の緩和は `_status_records()` の結果から、main の固定 `?? output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md` を1件だけ除外する箇所です。他の dirt はそのまま helper に渡します。
3. 宣言 path は `O_NOFOLLOW`、通常ファイル判定、inode安定性を確認し、前後の SHA-256・`st_mode`・size・inode・時刻情報をJSONへ記録します。差異は非0終了です。
4. helper の exact audit closure 検証後、lock内で各監査commitを `git diff-tree --root -m --name-only -z` により列挙し、`_paths_overlap()` で宣言 pathとの接頭辞衝突を拒否します。`already-landed` にも適用されます。
5. scriptのland実行、pytest、buildは行っていません。`python3 -m py_compile` は成功し、静的collision確認も該当なしでした。

作成後、親側の予定された移動・実行と整合する外部変更が発生し、現在worktreeはclean、mainは `5e095d00f6711e10e42f7e12b4b2e1766cfa93d6` です。追跡ファイルの変更・commit・pushは行っていません。