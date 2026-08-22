"""Penyandi nilai ke RGB, penulis PNG, pembungkus PMTiles.

Yang disimpan adalah nilai daya terima, bukan warna jadi. Skema warna hidup
sepenuhnya di etalase, sehingga bisa diganti tanpa menghitung ulang berjam-jam.

Kontrak penyandiannya di
specs/001-signal-prediction-map/contracts/tile-format.md — sisi TypeScript
membaca dengan rumus yang sama, dan kesepakatan itu punya tesnya sendiri.
"""
