/**
 * Tes kesepakatan dua sisi.
 *
 * `contracts/tile-format.md` menyebut tes ini yang paling penting dari
 * ketiganya: tes pulang-pergi di masing-masing sisi bisa sama-sama lolos
 * sambil sama-sama salah, asal salahnya konsisten di sisi itu sendiri.
 *
 * Berkas contohnya dibuat oleh `dapur/tiles/encode.py`. Jadi yang diperiksa di
 * sini benar-benar: apakah TypeScript membaca angka yang sama dengan yang
 * ditulis Python.
 */

import { describe, expect, it } from "vitest";
import contoh from "./__fixtures__/sandi-python.json";
import { colorizeTile, decodeDbm } from "./tile";
import { NO_DATA_COLOR, SIGNAL_STEPS, signalLevel } from "./palette";

// Langkah penyandian 0,1 dB, jadi galat pembulatan paling besar separuh langkah.
const TOLERANSI_DB = 0.05;

describe("sandi nilai sinyal", () => {
  it("membaca angka yang sama dengan yang ditulis Python", () => {
    for (const { dbm, r, g } of contoh.contoh) {
      expect(decodeDbm(r, g)).toBeCloseTo(dbm, 1);
    }
  });

  it("tidak melenceng di seluruh jangkauan", () => {
    for (const { dbm, r, g } of contoh.contoh) {
      expect(Math.abs(decodeDbm(r, g) - dbm)).toBeLessThanOrEqual(TOLERANSI_DB);
    }
  });
});

function hexKeRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

describe("pewarnaan ubin", () => {
  it("membiarkan piksel di luar batas kota tetap tembus pandang", () => {
    const piksel = new Uint8ClampedArray([10, 20, 255, 0]);
    colorizeTile(piksel, 1);
    expect(piksel[3]).toBe(0);
  });

  it("memberi wilayah tanpa data warna dan arsirnya sendiri", () => {
    // Kanal biru nol berarti data tidak memadai, apa pun nilai sinyalnya.
    const piksel = new Uint8ClampedArray([255, 255, 0, 255]);
    colorizeTile(piksel, 1);
    expect([piksel[0], piksel[1], piksel[2]]).toEqual(hexKeRgb(NO_DATA_COLOR));
  });

  it("tidak menampilkan wilayah tanpa data sebagai sinyal lemah", () => {
    // Ini kesalahan yang paling merugikan: satu operator kehilangan 36% wilayah
    // Samarinda dari data, dan menampilkannya sebagai sinyal lemah adalah
    // tuduhan yang salah.
    const tanpaData = new Uint8ClampedArray([0, 0, 0, 255]);
    const sinyalLemah = new Uint8ClampedArray([0, 0, 255, 255]);
    colorizeTile(tanpaData, 1);
    colorizeTile(sinyalLemah, 1);
    expect([tanpaData[0], tanpaData[1], tanpaData[2]]).not.toEqual([
      sinyalLemah[0],
      sinyalLemah[1],
      sinyalLemah[2],
    ]);
  });

  it("memetakan nilai ke tingkat warna yang benar", () => {
    for (const { dbm, r, g } of contoh.contoh) {
      const piksel = new Uint8ClampedArray([r, g, 255, 255]);
      colorizeTile(piksel, 1);
      const tingkat = Math.min(signalLevel(dbm), SIGNAL_STEPS.length - 1);
      expect([piksel[0], piksel[1], piksel[2]]).toEqual(hexKeRgb(SIGNAL_STEPS[tingkat]!));
    }
  });
});
