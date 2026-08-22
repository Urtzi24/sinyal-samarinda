/**
 * Pemilih operator.
 *
 * Tombol berjajar mendatar yang semuanya terlihat sekaligus, bukan menu gulung.
 * Perbandingan harus satu ketukan — itu inti kegunaan peta ini, dan satu-satunya
 * bagian panel lama yang tidak bisa dihilangkan tanpa membuat petanya berhenti
 * menjawab pertanyaannya sendiri.
 */

import { OPERATOR_NAMES, OPERATORS, type OperatorId } from "./map";

/** Nama pendek untuk layar sempit; nama panjangnya tetap dibaca pembaca layar. */
const NAMA_PENDEK: Record<OperatorId, string> = {
  telkomsel: "Telkomsel",
  ioh: "Indosat",
  xlsmart: "XLSmart",
};

export function renderOperators(
  target: HTMLElement,
  aktif: OperatorId,
  onPilih: (operator: OperatorId) => void,
): void {
  target.innerHTML = `
    <div class="operator__baris" role="radiogroup" aria-label="Pilih operator">
      ${OPERATORS.map(
        (id) => `
        <button type="button"
                class="operator__tombol"
                role="radio"
                data-operator="${id}"
                aria-checked="${id === aktif}"
                aria-label="${OPERATOR_NAMES[id]}">
          ${NAMA_PENDEK[id]}
        </button>`,
      ).join("")}
    </div>`;

  target.querySelectorAll<HTMLButtonElement>("[data-operator]").forEach((tombol) => {
    tombol.addEventListener("click", () => {
      target.querySelectorAll("[data-operator]").forEach((lain) => {
        lain.setAttribute("aria-checked", String(lain === tombol));
      });
      onPilih(tombol.dataset.operator as OperatorId);
    });
  });
}
