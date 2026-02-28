import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Input } from "../input";

describe("Input", () => {
  // ─── Render ────────────────────────────────────────────────

  it("input elementi olarak render edilir", () => {
    render(<Input />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("placeholder gösterilir", () => {
    render(<Input placeholder="E-posta adresiniz" />);
    expect(screen.getByPlaceholderText("E-posta adresiniz")).toBeInTheDocument();
  });

  // ─── Label ─────────────────────────────────────────────────

  it("label prop verildiğinde label gösterilir", () => {
    render(<Input label="Ad Soyad" />);
    expect(screen.getByText("Ad Soyad")).toBeInTheDocument();
  });

  it("label verilmediğinde label gösterilmez", () => {
    render(<Input placeholder="test" />);
    const labels = document.querySelectorAll("label");
    expect(labels).toHaveLength(0);
  });

  // ─── Value & onChange ──────────────────────────────────────

  it("kullanıcı yazarken onChange tetiklenir", async () => {
    const onChange = vi.fn();
    render(<Input onChange={onChange} />);

    const input = screen.getByRole("textbox");
    await userEvent.type(input, "Beşiktaş");

    // Her karakter için bir onChange tetiklenmeli
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls.length).toBeGreaterThanOrEqual(1);
  });

  it("value prop ile kontrollü input çalışır", () => {
    render(<Input value="test değer" onChange={() => {}} />);
    const input = screen.getByRole("textbox") as HTMLInputElement;
    expect(input.value).toBe("test değer");
  });

  // ─── Disabled ──────────────────────────────────────────────

  it("disabled olduğunda input devre dışı kalır", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("disabled olduğunda disabled variant sınıfları uygulanır", () => {
    render(<Input disabled />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("cursor-not-allowed");
  });

  // ─── Helper Text ───────────────────────────────────────────

  it("helperText verildiğinde yardımcı metin gösterilir", () => {
    render(<Input helperText="En az 8 karakter" />);
    expect(screen.getByText("En az 8 karakter")).toBeInTheDocument();
  });

  it("errorMessage varken helperText gösterilmez", () => {
    render(
      <Input
        helperText="Yardımcı metin"
        errorMessage="Bu alan zorunludur"
      />
    );
    expect(screen.queryByText("Yardımcı metin")).not.toBeInTheDocument();
    expect(screen.getByText("Bu alan zorunludur")).toBeInTheDocument();
  });

  // ─── Error ─────────────────────────────────────────────────

  it("errorMessage verildiğinde hata mesajı gösterilir", () => {
    render(<Input errorMessage="Geçersiz e-posta" />);
    expect(screen.getByText("Geçersiz e-posta")).toBeInTheDocument();
  });

  it("errorMessage verildiğinde kırmızı border uygulanır", () => {
    render(<Input errorMessage="Hata" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("border-red-500");
  });

  // ─── Type ──────────────────────────────────────────────────

  it("type prop ile input tipi belirlenir", () => {
    render(<Input type="email" placeholder="Email" />);
    const input = document.querySelector('input[type="email"]');
    expect(input).not.toBeNull();
  });

  // ─── Custom className ──────────────────────────────────────

  it("ek className ile özel sınıf eklenebilir", () => {
    render(<Input className="custom-input" />);
    const input = screen.getByRole("textbox");
    expect(input.className).toContain("custom-input");
  });
});
