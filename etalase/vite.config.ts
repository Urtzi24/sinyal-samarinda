import { createReadStream, statSync } from "node:fs";
import { resolve } from "node:path";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

// Arsip ubin ada di ../data/keluaran/, di luar folder etalase, dan tidak masuk
// git. Menyalinnya ke public/ berarti menggandakan belasan megabita tiap kali
// dapur dijalankan ulang, jadi disajikan langsung dari tempatnya.
//
// Permintaan sebagian (HTTP range) WAJIB dilayani. Tanpa itu PMTiles tidak ada
// gunanya: peramban akan menarik seluruh arsip alih-alih potongan yang sedang
// dilihat, dan seluruh alasan memilih format ini hilang.
const TILE_DIR = resolve(import.meta.dirname, "../data/keluaran");

/**
 * Sajikan ubin vektor sebagai berkas HTTP biasa di `/vt/{z}/{x}/{y}.mvt`.
 *
 * Ubin vektor diurai MapLibre di pekerja latar, bukan di utas utama seperti
 * raster. Protokol khusus `pmtiles://` tidak sampai ke sana dengan utuh —
 * lapisannya terpasang, tidak ada galat, tapi nol fitur termuat.
 *
 * Alamat HTTP biasa tidak punya masalah itu: pekerja latar mengambilnya
 * sendiri seperti ubin mana pun.
 */
function sajikanUbinVektor(): Plugin {
  return {
    name: "sajikan-ubin-vektor",
    async configureServer(server) {
      const { PMTiles, FetchSource } = await import("pmtiles");
      const { readFile } = await import("node:fs/promises");

      // Sumber sederhana yang membaca arsip dari cakram, bukan lewat jaringan.
      const jalurArsip = resolve(TILE_DIR, "kota.pmtiles");
      const arsip = new PMTiles({
        getKey: () => jalurArsip,
        getBytes: async (offset: number, length: number) => {
          const isi = await readFile(jalurArsip);
          return { data: isi.buffer.slice(offset, offset + length) as ArrayBuffer };
        },
      } as unknown as InstanceType<typeof FetchSource>);

      server.middlewares.use("/vt", async (req, res, next) => {
        const cocok = /^\/(\d+)\/(\d+)\/(\d+)\.mvt/.exec((req.url ?? "").split("?")[0]);
        if (!cocok) return next();
        try {
          const ubin = await arsip.getZxy(+cocok[1], +cocok[2], +cocok[3]);
          if (!ubin?.data) {
            res.statusCode = 204;
            res.end();
            return;
          }
          res.setHeader("Content-Type", "application/vnd.mapbox-vector-tile");
          res.setHeader("Cache-Control", "no-store");
          res.end(Buffer.from(ubin.data));
        } catch (galat) {
          res.statusCode = 500;
          res.end(String(galat));
        }
      });
    },
  };
}

function sajikanUbin(): Plugin {
  return {
    name: "sajikan-ubin",
    configureServer(server) {
      server.middlewares.use("/ubin", (req, res, next) => {
        const nama = (req.url ?? "").split("?")[0].replace(/^\//, "");
        if (!/^[\w.-]+\.(pmtiles|json|geojson)$/.test(nama)) return next();

        const jalur = resolve(TILE_DIR, nama);
        let ukuran: number;
        try {
          ukuran = statSync(jalur).size;
        } catch {
          res.statusCode = 404;
          res.end(`${nama} belum ada. Jalankan dapur lebih dulu.`);
          return;
        }

        res.setHeader(
          "Content-Type",
          nama.endsWith(".json") || nama.endsWith(".geojson")
            ? "application/json"
            : "application/octet-stream",
        );
        res.setHeader("Accept-Ranges", "bytes");

        // Jangan disinggah selama pengembangan.
        //
        // Nama arsipnya tetap sama setiap dapur dijalankan ulang, jadi peramban
        // tidak punya cara tahu isinya sudah berganti. Tanpa baris ini, hasil
        // hitung baru tidak muncul dan yang terlihat tetap ubin lama - gejala
        // yang menyesatkan, karena tampak seperti perhitungannya yang gagal.
        res.setHeader("Cache-Control", "no-store");

        const range = req.headers.range;
        if (!range) {
          res.setHeader("Content-Length", ukuran);
          createReadStream(jalur).pipe(res);
          return;
        }

        const cocok = /bytes=(\d*)-(\d*)/.exec(range);
        const awal = cocok?.[1] ? Number(cocok[1]) : 0;
        const akhir = cocok?.[2] ? Number(cocok[2]) : ukuran - 1;

        res.statusCode = 206;
        res.setHeader("Content-Range", `bytes ${awal}-${akhir}/${ukuran}`);
        res.setHeader("Content-Length", akhir - awal + 1);
        createReadStream(jalur, { start: awal, end: akhir }).pipe(res);
      });
    },
  };
}

export default defineConfig({
  plugins: [sajikanUbinVektor(), sajikanUbin()],

  // MapLibre WAJIB ikut dioptimalkan Vite, jangan dikecualikan.
  //
  // Bangunan ESM-nya terpecah jadi tiga berkas: modul utama, potongan bersama,
  // dan pekerja latar. Kalau dikecualikan, pekerja latarnya dibuat dari blob
  // dan gagal menemukan potongan bersamanya — MapLibre lalu menggantung tanpa
  // satu pun pesan galat, dan seluruh peta tampil kosong.
  //
  // Log server sempat menyarankan sebaliknya lewat peringatan soal
  // `maplibre-gl-worker.mjs` yang tidak ada. Peringatan itu tidak berbahaya;
  // menurutinya justru yang merusak.
  optimizeDeps: { include: ["maplibre-gl"] },

  build: { target: "es2022" },
  test: { environment: "node" },
});
