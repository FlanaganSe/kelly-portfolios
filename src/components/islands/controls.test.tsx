import { fireEvent, render } from "@solidjs/testing-library";
import { createSignal } from "solid-js";
import { describe, expect, it } from "vitest";
import { NumberField, RangeField } from "~/components/islands/controls";

describe("NumberField", () => {
  it("emits on every parseable keystroke", () => {
    const seen: number[] = [];
    const { getByLabelText } = render(() => (
      <NumberField label="Edge" value={1} onInput={(value) => seen.push(value)} step={0.01} />
    ));
    const field = getByLabelText("Edge") as HTMLInputElement;
    fireEvent.input(field, { target: { value: "0.5" } });
    fireEvent.input(field, { target: { value: "0.55" } });
    expect(seen).toEqual([0.5, 0.55]);
  });

  it("clamps on blur rather than while typing", () => {
    const seen: number[] = [];
    const [value, setValue] = createSignal(1);
    const { getByLabelText } = render(() => (
      <NumberField
        label="Edge"
        value={value()}
        onInput={(next) => {
          seen.push(next);
          setValue(next);
        }}
        min={0}
        max={10}
        step={0.1}
      />
    ));
    const field = getByLabelText("Edge") as HTMLInputElement;
    fireEvent.focus(field);
    fireEvent.input(field, { target: { value: "40" } });
    expect(seen).toEqual([40]);
    expect(field.value).toBe("40");
    fireEvent.blur(field);
    expect(seen).toEqual([40, 10]);
    expect(field.value).toBe("10.0");
  });

  it("leaves a half-typed entry alone", () => {
    const seen: number[] = [];
    const { getByLabelText } = render(() => (
      <NumberField label="Edge" value={1} onInput={(value) => seen.push(value)} step={0.01} />
    ));
    const field = getByLabelText("Edge") as HTMLInputElement;
    fireEvent.focus(field);
    fireEvent.input(field, { target: { value: "" } });
    expect(seen).toEqual([]);
    expect(field.value).toBe("");
  });

  /**
   * The defect this test exists for: choosing a preset while the cursor is still in the
   * field used to leave the old number in the box beside a recomputed answer.
   */
  it("takes a value set from outside even while it has focus", async () => {
    const [value, setValue] = createSignal(1);
    const { getByLabelText } = render(() => (
      <NumberField label="Edge" value={value()} onInput={setValue} step={0.01} />
    ));
    const field = getByLabelText("Edge") as HTMLInputElement;
    fireEvent.focus(field);
    fireEvent.input(field, { target: { value: "0.25" } });
    expect(field.value).toBe("0.25");
    setValue(0.92);
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(field.value).toBe("0.92");
  });

  it("puts the unit in the accessible name", () => {
    const { getByLabelText } = render(() => <NumberField label="Edge" value={1} onInput={() => {}} unit="% a year" />);
    expect(getByLabelText("Edge in % a year")).toBeInTheDocument();
  });
});

describe("RangeField", () => {
  it("is a native range control with a label and a readout", () => {
    const { getByLabelText } = render(() => (
      <RangeField label="Roth" value={33} onInput={() => {}} min={0} max={100} unit="%" />
    ));
    const field = getByLabelText("Roth") as HTMLInputElement;
    expect(field.type).toBe("range");
    expect(field.getAttribute("aria-valuetext")).toBe("33 %");
  });

  it("clamps whatever the track hands it", () => {
    const seen: number[] = [];
    const { getByLabelText } = render(() => (
      <RangeField label="Roth" value={33} onInput={(value) => seen.push(value)} min={0} max={50} />
    ));
    const field = getByLabelText("Roth") as HTMLInputElement;
    fireEvent.input(field, { target: { value: "80" } });
    expect(seen).toEqual([50]);
  });
});
