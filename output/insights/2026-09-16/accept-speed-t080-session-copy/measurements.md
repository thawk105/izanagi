# 計測台帳 (dev-wave-t080-accept-speed)

時刻は `date` の出力 (JST)。junit の値は各 shard の `<testsuite time>`。

## 受入全走 pre (実装前 tip 51d4fec75 = 01bcdf239 + merge main)

| 走 | session | 開始 → 終了 | shard-0 | shard-1 | shard-2 | 赤 | shard-0 e2e (発行あり 10 node) | temp_roots / g7 |
|---|---|---|---|---|---|---|---|---|
| pre-1 | ee01fa2cf9ad7d6b2c4b550fa6ff1966 | 20:07:50 → 20:29:00 | **326.189** | 228.261 | 240.635 | 0 | 212.65〜235.41 (最長 ccbench-current 235.41) | 87.26 / 64.46 |
| pre-2 | e7d612187b8a10a854c72ff688c71ec8 | 20:29:41 → 20:42:27 | 336.855 | 278.166 | **355.655** | 0 | 241.80〜264.67 (最長 ccbench-current 264.67) | 104.66 / 72.98 |
| pre-3 (対照 worktree、非帰属赤 6) | c9e30be774f0847156afeec4fca9c913 | 20:49 → 21:1x | **491.348** | 228.252 | 256.057 | 6 error (setup の `git ls-files --others` 30 秒 timeout ×5、real-repo lock deadline ×1 = F945 型。同時刻に本 wave の変異走 12 job が lustre を使用) | (下記) | (下記) |

| pre-4 (対照 worktree、wave 名 control-…) | 62d2ca2a1c85bef165ad552f9579ab5d | 21:17:24 → 21:42:37 | **331.977** | 227.111 | 214.743 | 0 | 238.2〜261.2 | 104.6 / 65.1 |
| pre-5 (対照 worktree) | 41d1a03b384737e8bfde5950b8df3d5b | 21:44:46 → 22:10:22 | 333.317 | 229.748 | **410.232** | 0 | 240.4〜263.2 | 107.1 / 61.8 |

pre-3 の shard-0 e2e: 393.6〜416.7、temp_roots 222.8 / g7 79.5 (負荷下)。post-2 の shard-0 e2e: 435.8〜458.7、temp_roots 35.0 / g7 31.1 (負荷下、shard-0 は bnode050、pre-5 の shard-0 は bnode009)。

## 受入全走 post (実装 tip bdfa49950 + merge main、実装子 worktree から)

| 走 | session | 開始 → 終了 | shard-0 | shard-1 | shard-2 | 赤 | shard-0 e2e (発行あり 10 node) | temp_roots / g7 | 同時刻ペア |
|---|---|---|---|---|---|---|---|---|---|
| post-1 | ffbeb353240136e56657bb1f8e437b27 | 21:22:33 → 21:43:04 | **296.472** | 253.917 | 217.050 | 0 | 202.8〜225.5 | 23.6 / 19.4 | pre-4 (shard-0 332.0 → 296.5 = −35.5 秒、−10.7%) |
| post-2 (非帰属赤 30) | ed9cdcc564549a0fd9109abfaad725b1 | 21:44:46 → 22:07:45 | **573.210** | 236.044 | 222.782 | 30 error (setup の git subprocess 30 秒 timeout ×29、real-repo lock deadline ×1 = F945 型。同時刻に本 wave の変異 probe2/本走が dispatch 連続) | (下記) | (下記) | pre-5 (同時刻、下記) |

## 同時刻ペアの比較 (最遅 shard の junit time)

| ペア | pre (旧) | post (新) | 差 |
|---|---|---|---|
| 1 | pre-4 shard-0 331.977 | post-1 shard-0 296.472 | −35.5 秒 (−10.7%) |
| 2 (不成立) | pre-5 最遅 shard-2 410.232 (shard-0 333.317) | post-2 shard-0 573.210 (非帰属赤 30、git timeout) | 交絡: post-2 の shard-0 node だけ git subprocess が 30 秒 timeout を 29 回。同時刻の pre-5 shard-0 には無い |
| 3 (両側が F945 赤、負荷下) | pre-6 shard-0 474.446 (error 16) | post-3 shard-0 465.459 (error 17) | −9.0 秒 (−1.9%)。両側とも git subprocess timeout (11〜12) + git archive timeout (4) + real-repo lock (1) |
| 4 | pre-7 shard-0 326.709 | post-4 shard-0 308.071 | −18.6 秒 (−5.7%)。両側緑 |

pre-7: session 6c9b6facb1f1aaf0aa8f3eed3fe63fa3、22:42:33 → 22:52:13、shard-1 226.416 / shard-2 225.512、e2e 233.4〜256.3、temp_roots 100.0 / g7 70.2。
post-4: session 8ebafcc13209e40652ad3c626c8b0778、22:41:59 → 22:52:04、shard-1 225.286 / shard-2 230.089、e2e 217.1〜239.9、temp_roots 40.6 / g7 19.5。

**比較可能ペア (1・3・4) の中央値: −5.7%。** D357 / D1260 の 10% 基準の内側。

pre-6: session 30625ec08cf8a2390400e5f21a4362ee、22:29:37 → 22:41:15、shard-1 227.514 / shard-2 347.855。post-3: session f85a7794fad058aeaaa38f50faa7a51c、22:29:37 → 22:40:53、shard-1 228.007 / shard-2 265.379。

## 焦点走 (e2e 12 node + shared_base_builds_real_builder_once、xdist -n 12、1 node、generic dispatch)

| 走 | code | node | request | 所要 (pytest) | e2e 発行あり 10 node の範囲 | g7 / temp_roots / builds_real |
|---|---|---|---|---|---|---|
| new-1 | impl (proto 派生) | bnode067 | 1938 | **133.32** | 103.86〜126.55 | 54.13 / 17.49 / 42.11 |
| old-1 | control (旧 code 51d4fec75) | bnode067 | 1956 | **136.74** | 106.23〜129.05 | 56.37 / 20.37 / 42.90 |
| new-2 | impl (proto 派生) | bnode080 | 1982 | **133.09** | 〜126.28 | — |
| new-3 | impl (proto 派生) | bnode007 | (izdw、下記 file) | **150.16** | — | — |
| old-2 | control (旧 code) | bnode006 | (izdw、下記 file) | **136.25** | — | — |
