#!/usr/bin/env python3
"""Incrementally merge shard results into rank.csv and rank/rank-latest.csv.

Unlike merge_shards.py, this keeps the existing full table and only replaces
rows for relays that were re-tested. It does not prune candidates or remove
existing clean rows when an incremental run is temporarily bad.
"""
import csv
import glob
import os
import sys

HDR = ["中继", "出口IP", "延迟秒", "Google状态码", "Google跳转", "并发", "带宽MB/s",
       "风控值", "纯净度", "是否家宽", "是否原生", "国家", "城市", "运营商", "AS",
       "代理标记", "机房标记", "判定"]


def read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return [row for row in csv.reader(handle) if row and row[0] not in ("中继", "relay")]


def bandwidth(row):
    try:
        return float(row[6])
    except (IndexError, TypeError, ValueError):
        return 0.0


def main():
    shard_dir, rank_path, clean_path = sys.argv[1], sys.argv[2], sys.argv[3]
    rank = {}
    for row in read_rows(rank_path):
        if len(row) >= 18:
            rank[row[0]] = row
    clean = {}
    for row in read_rows(clean_path):
        if len(row) >= 18:
            clean[row[0]] = row

    new_rank = {}
    for path in sorted(glob.glob(os.path.join(shard_dir, "rank-*.csv"))):
        for row in read_rows(path):
            if len(row) >= 18:
                new_rank[row[0]] = row

    new_clean = {}
    for path in sorted(glob.glob(os.path.join(shard_dir, "clean-*.csv"))):
        for row in read_rows(path):
            if len(row) >= 18:
                new_clean[row[0]] = row

    rank.update(new_rank)
    clean.update(new_clean)

    with open(rank_path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(HDR)
        writer.writerows(rank.values())

    clean_rows = sorted(clean.values(), key=bandwidth, reverse=True)
    with open(clean_path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(HDR)
        writer.writerows(clean_rows)

    print(f"incremental merge: tested={len(new_rank)}, rank={len(rank)}, clean={len(clean_rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
