/**
 * Tes pemilihan tingkat kerincian — FR-018.
 *
 * Yang paling penting diuji di sini bukan bahwa perangkat lemah diturunkan,
 * melainkan bahwa perangkat yang TIDAK MELAPORKAN apa-apa tidak ikut
 * diturunkan. Safari dan Firefox tidak melaporkan `deviceMemory` sama sekali;
 * menganggap diamnya sebagai perangkat lemah berarti mencabut bentang alam 3D
 * dari sebagian besar penggunanya tanpa sebab.
 */

import { describe, expect, it } from "vitest";

import { tingkatAwal } from "./kualitas";

function nav(keterangan: { deviceMemory?: number; hardwareConcurrency?: number }): Navigator {
  return keterangan as unknown as Navigator;
}

describe("tingkatAwal", () => {
  it("menurunkan kerincian saat ingatan perangkat di bawah 2 GB", () => {
    expect(tingkatAwal(nav({ deviceMemory: 1, hardwareConcurrency: 8 }))).toBe("ringan");
    expect(tingkatAwal(nav({ deviceMemory: 0.5, hardwareConcurrency: 8 }))).toBe("ringan");
  });

  it("menurunkan kerincian saat inti prosesor kurang dari empat", () => {
    expect(tingkatAwal(nav({ deviceMemory: 8, hardwareConcurrency: 2 }))).toBe("ringan");
  });

  it("membiarkan kerincian penuh pada perangkat yang sanggup", () => {
    expect(tingkatAwal(nav({ deviceMemory: 8, hardwareConcurrency: 8 }))).toBe("penuh");
    expect(tingkatAwal(nav({ deviceMemory: 2, hardwareConcurrency: 4 }))).toBe("penuh");
  });

  it("menganggap perangkat yang diam sebagai sanggup, bukan tidak sanggup", () => {
    expect(tingkatAwal(nav({}))).toBe("penuh");
    expect(tingkatAwal(nav({ hardwareConcurrency: 8 }))).toBe("penuh");
    expect(tingkatAwal(nav({ deviceMemory: 8 }))).toBe("penuh");
  });

  it("mengabaikan jumlah inti nol, yang berarti tidak diketahui", () => {
    expect(tingkatAwal(nav({ hardwareConcurrency: 0 }))).toBe("penuh");
  });
});
